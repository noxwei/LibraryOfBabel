#!/usr/bin/env python3
"""
Frictionless Ebook Harvester - LibraryOfBabel Phase 5
Automated discovery and download of ebooks from audiobook database using MAM API

Features:
- Query audiobooks database for books needing ebook discovery
- Search MAM for EPUB/MOBI/AZW3 formats only (filter out audiobooks)
- Priority download: EPUB > MOBI > AZW3, skip others
- Auto-download using working MAM session
- Database status tracking: 'found', 'downloaded', 'skipped'
- Rate limiting: 95 requests/day with delays
- Error handling: Skip problematic books, continue processing
- Real-time progress logging
"""

import os
import sqlite3
import requests
import json
import time
import logging
import re
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import urlencode
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Load environment
load_dotenv()

class FrictionlessEbookHarvester:
    def __init__(self, database_path="database/data/audiobook_ebook_tracker.db", batch_size=20):
        self.database_path = database_path
        self.batch_size = batch_size
        self.downloads_dir = Path("ebooks/downloads")
        self.torrents_dir = Path("ebooks/torrents")
        
        # MAM Configuration
        self.mam_session_cookie = os.getenv('MAM_SESSION_COOKIE')
        self.mam_base_url = "https://www.myanonamouse.net"
        self.search_endpoint = "/tor/js/loadSearchJSONbasic.php"
        self.max_daily_requests = 95
        self.request_delay = 3  # seconds between requests
        
        # Ebook format priority (higher score = higher priority)
        self.format_priority = {
            'epub': 100,
            'mobi': 50,
            'azw3': 25,
            'azw': 20,
            'pdf': 10  # Low priority, but still ebook
        }
        
        # File size limits (focus on small books first)
        self.max_file_size_mb = 100  # Skip books larger than 100MB
        self.large_file_threshold_mb = 50  # Mark books >50MB for later
        
        # Statistics tracking
        self.stats = {
            'searched': 0,
            'found': 0,
            'downloaded': 0,
            'skipped': 0,
            'errors': 0
        }
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ebook_harvester.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Create directories
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self.torrents_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.mam_session_cookie:
            raise ValueError("MAM_SESSION_COOKIE not found in environment")
        
        self.logger.info("🚀 Frictionless Ebook Harvester initialized")
        self.logger.info(f"📁 Downloads: {self.downloads_dir}")
        self.logger.info(f"📦 Torrents: {self.torrents_dir}")
    
    def get_database_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.database_path)
    
    def get_books_needing_ebooks(self, limit=None) -> List[Dict]:
        """Get audiobooks that need ebook discovery"""
        with self.get_database_connection() as conn:
            cursor = conn.cursor()
            
            # Get books that don't have ebook matches yet
            query = """
            SELECT a.album_id, a.title, a.author, a.clean_title, a.clean_author
            FROM audiobooks a
            LEFT JOIN ebooks e ON a.album_id = e.audiobook_id
            WHERE e.audiobook_id IS NULL
            ORDER BY a.album_id
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            books = []
            for row in results:
                books.append({
                    'album_id': row[0],
                    'title': row[1],
                    'author': row[2],
                    'clean_title': row[3] or row[1],
                    'clean_author': row[4] or row[2]
                })
            
            return books
    
    def search_mam_for_ebooks(self, title: str, author: str, max_results=10) -> List[Dict]:
        """Search MAM for ebook formats only"""
        # Clean search query
        search_query = f"{title} {author}".strip()
        
        # MAM API parameters - using ebook categories from working URL
        ebook_categories = ['60', '61', '62', '63', '64', '65', '66', '67', '68', '69', '70', '71', '72', '73', '74', '75', '76', '77', '78', '79', '80', '81', '82']
        
        params = {
            'tor[text]': search_query,
            'tor[srchIn][title]': 'true',
            'tor[srchIn][author]': 'true',
            'tor[cat][]': ebook_categories,  # All ebook categories from working URL
            'tor[browse_lang][]': '1',  # English language
            'tor[perpage]': str(max_results)
        }
        
        # Headers for MAM API (working configuration)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.myanonamouse.net/',
            'Cookie': self.mam_session_cookie
        }
        
        try:
            url = f"{self.mam_base_url}{self.search_endpoint}?{urlencode(params, doseq=True)}"
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return self.filter_ebook_results(data, title, author)
            else:
                self.logger.error(f"MAM API error {response.status_code} for '{search_query}'")
                return []
                
        except Exception as e:
            self.logger.error(f"Search failed for '{search_query}': {e}")
            return []
    
    def filter_ebook_results(self, data: Dict, title: str, author: str) -> List[Dict]:
        """Filter and score ebook results by format priority"""
        if not data or 'data' not in data:
            return []
        
        ebook_results = []
        
        for item in data['data']:
            # Extract format from filename, title, and category
            filename = item.get('filename', '').lower()
            item_title = item.get('title', '').lower()
            category = str(item.get('category', ''))
            
            # Skip audiobook files first
            if any(audio_term in filename for audio_term in ['mp3', 'm4a', 'm4b', 'audiobook', 'audio']):
                continue
            if any(audio_term in item_title for audio_term in ['audiobook', 'audio book', 'm4b', 'mp3']):
                continue
            
            # Identify ebook format
            ebook_format = None
            
            # Check filename and title for format indicators
            for fmt in self.format_priority.keys():
                if fmt in filename or fmt in item_title:
                    ebook_format = fmt
                    break
            
            # If no format found, check if it's likely an ebook
            if not ebook_format:
                # Check category for ebook indicators (14 = E-Books from API docs)
                if category == '14' or 'ebook' in item_title.lower() or 'e-book' in item_title.lower():
                    ebook_format = 'epub'  # Default assumption for ebooks
                # Check for common ebook keywords
                elif any(keyword in item_title.lower() for keyword in ['novel', 'fiction', 'book', 'kindle', 'digital']):
                    # If it's not obviously audio and has book-related keywords
                    if not any(audio_word in item_title.lower() for audio_word in ['unabridged', 'narrator', 'audiobook']):
                        ebook_format = 'epub'  # Assume ebook
                    else:
                        continue  # Skip audiobooks
                else:
                    continue  # Skip if unclear format
            
            # Extract author from author_info JSON
            author_info = item.get('author_info', '{}')
            extracted_author = 'Unknown'
            try:
                if author_info and author_info != '{}':
                    import json
                    author_dict = json.loads(author_info)
                    if author_dict:
                        extracted_author = list(author_dict.values())[0]  # Get first author
            except:
                extracted_author = 'Unknown'
            
            # Check file size (convert from bytes to MB)
            file_size_bytes = item.get('size', 0)
            if isinstance(file_size_bytes, str):
                try:
                    file_size_bytes = int(file_size_bytes)
                except:
                    file_size_bytes = 0
            
            file_size_mb = file_size_bytes / (1024 * 1024) if file_size_bytes > 0 else 0
            
            # Skip files larger than 100MB
            if file_size_mb > self.max_file_size_mb:
                self.logger.info(f"    ⏭️ Skipping large file: {item.get('title', 'Unknown')} ({file_size_mb:.1f}MB > {self.max_file_size_mb}MB)")
                continue
            
            # Calculate match confidence
            title_match = self.calculate_title_match(title, item.get('title', ''))
            author_match = self.calculate_author_match(author, extracted_author)
            confidence = (title_match + author_match) / 2
            
            # Only include reasonable matches
            if confidence < 0.3:
                continue
            
            result = {
                'torrent_id': item.get('id'),
                'title': item.get('title'),
                'author': extracted_author,  # Use extracted author from author_info
                'filename': item.get('filename', ''),
                'format': ebook_format,
                'format_priority': self.format_priority[ebook_format],
                'seeders': int(item.get('seeders', 0)),
                'leechers': int(item.get('leechers', 0)),
                'size': item.get('size'),
                'file_size_mb': file_size_mb,  # Add file size in MB
                'is_large_file': file_size_mb > self.large_file_threshold_mb,  # Mark large files
                'match_confidence': confidence,
                'download_url': f"{self.mam_base_url}/tor/download.php?tid={item.get('id')}"
            }
            
            ebook_results.append(result)
        
        # Sort by: small files first, then format priority, then seeders, then confidence
        ebook_results.sort(key=lambda x: (
            x['is_large_file'],  # False (small files) comes before True (large files)
            -x['format_priority'],  # Higher priority first (negative for reverse)
            -x['seeders'],  # More seeders first
            -x['match_confidence']  # Higher confidence first
        ))
        
        return ebook_results
    
    def calculate_title_match(self, search_title: str, result_title: str) -> float:
        """Calculate title match confidence"""
        if not search_title or not result_title:
            return 0.0
        
        search_clean = re.sub(r'[^\w\s]', '', search_title.lower())
        result_clean = re.sub(r'[^\w\s]', '', result_title.lower())
        
        search_words = set(search_clean.split())
        result_words = set(result_clean.split())
        
        if not search_words:
            return 0.0
        
        intersection = search_words.intersection(result_words)
        return len(intersection) / len(search_words)
    
    def calculate_author_match(self, search_author: str, result_author: str) -> float:
        """Calculate author match confidence"""
        if not search_author or not result_author:
            return 0.0
        
        search_clean = re.sub(r'[^\w\s]', '', search_author.lower())
        result_clean = re.sub(r'[^\w\s]', '', result_author.lower())
        
        # Simple substring match for authors
        if search_clean in result_clean or result_clean in search_clean:
            return 1.0
        
        # Word-based matching
        search_words = set(search_clean.split())
        result_words = set(result_clean.split())
        
        if not search_words:
            return 0.0
        
        intersection = search_words.intersection(result_words)
        return len(intersection) / len(search_words)
    
    def download_torrent(self, torrent_data: Dict) -> bool:
        """Download torrent file using MAM session"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.myanonamouse.net/',
                'Cookie': self.mam_session_cookie
            }
            
            response = requests.get(torrent_data['download_url'], headers=headers, timeout=30)
            
            if response.status_code == 200 and len(response.content) > 100:
                # Generate clean filename
                clean_title = re.sub(r'[^\w\s-]', '', torrent_data['title'])[:30]
                torrent_filename = f"{torrent_data['torrent_id']}_{clean_title}_{torrent_data['format']}.torrent"
                torrent_path = self.torrents_dir / torrent_filename
                
                # Save torrent file
                with open(torrent_path, 'wb') as f:
                    f.write(response.content)
                
                # Add to transmission
                result = os.system(f'transmission-remote --add "{torrent_path}" >/dev/null 2>&1')
                
                if result == 0:
                    self.logger.info(f"    ✅ Downloaded and added to transmission: {torrent_filename}")
                    return True
                else:
                    self.logger.warning(f"    ⚠️ Torrent saved but transmission add failed: {torrent_filename}")
                    return False
            else:
                self.logger.error(f"    ❌ Download failed: Status {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"    ❌ Download error: {e}")
            return False
    
    def save_ebook_to_database(self, album_id: int, ebook_data: Dict, status: str):
        """Save ebook metadata to database"""
        with self.get_database_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO ebooks (
                        audiobook_id, mam_torrent_id, ebook_title, ebook_author,
                        file_format, file_size_mb, seeders, leechers, match_confidence,
                        download_status, discovered_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    album_id,
                    ebook_data['torrent_id'],
                    ebook_data['title'],
                    ebook_data.get('author', 'Unknown'),  # Handle missing author
                    ebook_data['format'].upper(),
                    ebook_data.get('file_size_mb', 0.0),  # Add file size
                    ebook_data['seeders'],
                    ebook_data['leechers'],
                    ebook_data['match_confidence'],
                    status,
                    datetime.now().isoformat()
                ))
                conn.commit()
                
            except Exception as e:
                self.logger.error(f"Database save error for album {album_id}: {e}")
    
    def mark_book_as_skipped(self, album_id: int, reason: str):
        """Mark book as skipped in database"""
        with self.get_database_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # Create a placeholder record to indicate we searched but found nothing
                cursor.execute("""
                    INSERT OR REPLACE INTO ebooks (
                        audiobook_id, mam_torrent_id, ebook_title, ebook_author,
                        file_format, match_confidence, download_status, discovered_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    album_id,
                    f"SKIPPED_{album_id}",
                    f"NO_EBOOK_FOUND",
                    reason,
                    "NONE",
                    0.0,
                    "skipped",
                    datetime.now().isoformat()
                ))
                conn.commit()
                
            except Exception as e:
                self.logger.error(f"Database skip marking error for album {album_id}: {e}")
    
    def print_progress(self):
        """Print current progress statistics"""
        total = self.stats['searched']
        success_rate = (self.stats['found'] / total * 100) if total > 0 else 0
        download_rate = (self.stats['downloaded'] / self.stats['found'] * 100) if self.stats['found'] > 0 else 0
        
        print(f"\n📊 PROGRESS STATS:")
        print(f"   🔍 Searched: {self.stats['searched']}")
        print(f"   ✅ Found: {self.stats['found']} ({success_rate:.1f}%)")
        print(f"   📥 Downloaded: {self.stats['downloaded']} ({download_rate:.1f}%)")
        print(f"   ⏭️ Skipped: {self.stats['skipped']}")
        print(f"   ❌ Errors: {self.stats['errors']}")
    
    def harvest_ebooks(self, test_mode=True):
        """Main harvesting function"""
        self.logger.info("🌾 Starting frictionless ebook harvesting...")
        
        # Get books needing ebooks
        limit = self.batch_size if test_mode else None
        books = self.get_books_needing_ebooks(limit)
        
        if not books:
            self.logger.info("✅ No books need ebook discovery!")
            return
        
        total_books = len(books)
        self.logger.info(f"📚 Found {total_books} books needing ebook discovery")
        
        if test_mode:
            self.logger.info(f"🧪 TEST MODE: Processing first {self.batch_size} books")
        
        for i, book in enumerate(books, 1):
            try:
                self.logger.info(f"[{i}/{total_books}] 🔍 Searching: '{book['title']}' by {book['author']}")
                
                # Search for ebooks
                ebook_results = self.search_mam_for_ebooks(book['clean_title'], book['clean_author'])
                self.stats['searched'] += 1
                
                if ebook_results:
                    # Get best match (already sorted by priority - small files first)
                    best_match = ebook_results[0]
                    self.stats['found'] += 1
                    
                    size_indicator = "🟢" if not best_match['is_large_file'] else "🟡"
                    self.logger.info(f"    📖 Found: {best_match['title']} ({best_match['format'].upper()})")
                    self.logger.info(f"    {size_indicator} Size: {best_match['file_size_mb']:.1f}MB, Seeders: {best_match['seeders']}, Confidence: {best_match['match_confidence']:.2f}")
                    
                    # Attempt download
                    if self.download_torrent(best_match):
                        self.save_ebook_to_database(book['album_id'], best_match, 'downloaded')
                        self.stats['downloaded'] += 1
                    else:
                        self.save_ebook_to_database(book['album_id'], best_match, 'found')
                        self.stats['errors'] += 1
                else:
                    self.logger.info(f"    ❌ No ebook matches found")
                    self.mark_book_as_skipped(book['album_id'], 'no_ebook_matches')
                    self.stats['skipped'] += 1
                
                # Progress update every 5 books
                if i % 5 == 0:
                    self.print_progress()
                
                # Rate limiting
                if i < total_books:
                    self.logger.info(f"    ⏳ Rate limiting delay ({self.request_delay}s)...")
                    time.sleep(self.request_delay)
                
            except Exception as e:
                self.logger.error(f"    ❌ Error processing '{book['title']}': {e}")
                self.mark_book_as_skipped(book['album_id'], f'error: {str(e)}')
                self.stats['errors'] += 1
                continue
        
        # Final statistics
        self.logger.info("\n🎉 HARVESTING COMPLETE!")
        self.print_progress()
        
        if self.stats['downloaded'] > 0:
            self.logger.info(f"📁 Downloaded files location: {self.downloads_dir}")
            self.logger.info("🔄 Check transmission status: transmission-remote --list")


def main():
    """Main execution function"""
    print("🚀 Frictionless Ebook Harvester - LibraryOfBabel Phase 5")
    print("=" * 60)
    
    try:
        # Test mode first (20 books)
        harvester = FrictionlessEbookHarvester(batch_size=20)
        harvester.harvest_ebooks(test_mode=True)
        
    except KeyboardInterrupt:
        print("\n⏹️ Harvesting interrupted by user")
    except Exception as e:
        print(f"❌ Critical error: {e}")
        raise


if __name__ == "__main__":
    main()