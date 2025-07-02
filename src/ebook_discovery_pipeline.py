#!/usr/bin/env python3
"""
Ebook Discovery Pipeline - Find ebook counterparts for audiobooks using MAM API

🎊 BREAKTHROUGH: Now using direct MAM API access (no more Playwright!)
Discovers ebook versions of 5,839 audiobooks for LibraryOfBabel expansion.
"""

import os
import sqlite3
import requests
import json
import time
import logging
from dotenv import load_dotenv
from urllib.parse import urlencode, quote
from datetime import datetime

# Load environment variables
load_dotenv()

class EbookDiscoveryPipeline:
    def __init__(self, database_path="database/data/audiobook_ebook_tracker.db"):
        self.database_path = database_path
        self.mam_session_cookie = os.getenv('MAM_SESSION_COOKIE')
        self.max_daily_downloads = int(os.getenv('MAX_DAILY_DOWNLOADS', 95))
        self.request_delay = 3  # 3 seconds between requests for rate limiting
        
        # MAM API configuration
        self.mam_base_url = "https://www.myanonamouse.net"
        self.search_endpoint = "/tor/js/loadSearchJSONbasic.php"
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        if not self.mam_session_cookie:
            raise ValueError("MAM_SESSION_COOKIE not found in environment")
    
    def get_database_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.database_path)
    
    def search_mam_for_ebook(self, title, author, max_results=5):
        """
        Search MAM for ebook using the working API
        """
        # Clean search query
        search_query = f"{title} {author}".strip()
        
        # MAM API parameters
        params = {
            'tor[text]': search_query,
            'tor[srchIn][title]': 'true',
            'tor[srchIn][author]': 'true',
            'tor[searchType]': 'all',
            'tor[cat][]': '0',  # All categories to start broad
            'tor[sortType]': 'seedersDesc',
            'tor[startNumber]': '0',
            'tor[perpage]': str(max_results)
        }
        
        # Headers for MAM API
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.myanonamouse.net/',
            'Cookie': self.mam_session_cookie
        }
        
        try:
            url = f"{self.mam_base_url}{self.search_endpoint}?{urlencode(params)}"
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
    
    def parse_file_size(self, size_str):
        """
        Parse human-readable file size to bytes
        """
        if not size_str:
            return 0
        
        # Handle sizes like "95.9 MiB", "1.2 GiB", "433.5 KiB"
        import re
        
        size_str = str(size_str).strip()
        
        # First try to parse as integer (raw bytes)
        try:
            return int(size_str)
        except ValueError:
            pass
        
        # Parse human-readable format
        match = re.match(r'([0-9,\.]+)\s*([KMGT]?i?B)', size_str, re.IGNORECASE)
        if not match:
            return 0
        
        size_num = float(match.group(1).replace(',', ''))
        unit = match.group(2).upper()
        
        multipliers = {
            'B': 1,
            'KB': 1024, 'KIB': 1024,
            'MB': 1024**2, 'MIB': 1024**2,
            'GB': 1024**3, 'GIB': 1024**3,
            'TB': 1024**4, 'TIB': 1024**4
        }
        
        return int(size_num * multipliers.get(unit, 1))
    
    def filter_ebook_results(self, api_response, original_title, original_author):
        """
        Filter MAM results to find likely ebook matches
        """
        if not api_response.get('data'):
            return []
        
        ebook_results = []
        
        for result in api_response['data']:
            # Check if it's an ebook category
            category = result.get('catname', '').lower()
            if 'ebook' not in category and 'book' not in category:
                continue
            
            # Parse author info
            author_info = result.get('author_info', '{}')
            try:
                authors = json.loads(author_info) if author_info else {}
                author_names = list(authors.values()) if isinstance(authors, dict) else []
                author_str = ', '.join(author_names) if author_names else 'Unknown'
            except:
                author_str = 'Unknown'
            
            # Calculate match confidence
            confidence = self.calculate_match_confidence(
                result.get('title', ''), author_str,
                original_title, original_author
            )
            
            if confidence > 0.3:  # Only include reasonable matches
                # Parse file size properly
                size_bytes = self.parse_file_size(result.get('size', 0))
                size_mb = round(size_bytes / (1024 * 1024), 2) if size_bytes else 0
                
                ebook_results.append({
                    'mam_id': result.get('id'),
                    'title': result.get('title', ''),
                    'author': author_str,
                    'category': category,
                    'size_bytes': size_bytes,
                    'size_mb': size_mb,
                    'seeders': int(result.get('seeders', 0)),
                    'leechers': int(result.get('leechers', 0)),
                    'confidence': confidence,
                    'download_url': f"{self.mam_base_url}/tor/download.php?tid={result.get('id')}"
                })
        
        # Sort by confidence and seeders
        ebook_results.sort(key=lambda x: (x['confidence'], x['seeders']), reverse=True)
        return ebook_results[:3]  # Return top 3 matches
    
    def calculate_match_confidence(self, result_title, result_author, original_title, original_author):
        """
        Calculate confidence score for title/author match
        """
        # Simple string similarity (can be enhanced with fuzzy matching)
        title_lower = original_title.lower()
        author_lower = original_author.lower()
        result_title_lower = result_title.lower()
        result_author_lower = result_author.lower()
        
        confidence = 0.0
        
        # Title matching
        if title_lower in result_title_lower or result_title_lower in title_lower:
            confidence += 0.6
        elif any(word in result_title_lower for word in title_lower.split() if len(word) > 3):
            confidence += 0.3
        
        # Author matching
        if author_lower in result_author_lower or result_author_lower in author_lower:
            confidence += 0.4
        elif any(word in result_author_lower for word in author_lower.split() if len(word) > 2):
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def save_ebook_results(self, audiobook_id, search_query, ebook_results):
        """
        Save discovered ebooks to database
        """
        conn = self.get_database_connection()
        cursor = conn.cursor()
        
        try:
            # Record search attempt
            cursor.execute("""
                INSERT INTO search_attempts (audiobook_id, search_query, results_found, search_engine)
                VALUES (?, ?, ?, 'MAM_API')
            """, (audiobook_id, search_query, len(ebook_results)))
            
            # Save ebook results
            for ebook in ebook_results:
                cursor.execute("""
                    INSERT OR REPLACE INTO ebooks (
                        audiobook_id, mam_torrent_id, ebook_title, ebook_author,
                        file_format, file_size_mb, seeders, leechers, match_confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    audiobook_id, ebook['mam_id'], ebook['title'], ebook['author'],
                    'EPUB/PDF', ebook['size_mb'], ebook['seeders'], ebook['leechers'],
                    ebook['confidence']
                ))
            
            conn.commit()
            self.logger.info(f"Saved {len(ebook_results)} ebooks for audiobook {audiobook_id}")
            
        except Exception as e:
            self.logger.error(f"Database error: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_audiobooks_without_ebooks(self, limit=None):
        """
        Get audiobooks that don't have ebook matches yet
        """
        conn = self.get_database_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT a.album_id, a.title, a.author, a.clean_title, a.clean_author
            FROM audiobooks a
            LEFT JOIN ebooks e ON a.album_id = e.audiobook_id
            WHERE e.audiobook_id IS NULL
            ORDER BY a.title
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'audiobook_id': row[0],
                'title': row[1],
                'author': row[2],
                'clean_title': row[3],
                'clean_author': row[4]
            }
            for row in results
        ]
    
    def run_discovery_batch(self, batch_size=20):
        """
        Run ebook discovery for a batch of audiobooks
        """
        self.logger.info(f"🚀 Starting ebook discovery batch (size: {batch_size})")
        
        # Get audiobooks without ebooks
        audiobooks = self.get_audiobooks_without_ebooks(limit=batch_size)
        
        if not audiobooks:
            self.logger.info("✅ All audiobooks already have ebook searches completed!")
            return
        
        self.logger.info(f"📚 Processing {len(audiobooks)} audiobooks")
        
        discoveries = 0
        
        for i, audiobook in enumerate(audiobooks, 1):
            self.logger.info(f"[{i}/{len(audiobooks)}] Searching: '{audiobook['title']}' by {audiobook['author']}")
            
            # Search MAM for ebooks
            ebook_results = self.search_mam_for_ebook(
                audiobook['clean_title'], 
                audiobook['clean_author']
            )
            
            if ebook_results:
                discoveries += len(ebook_results)
                self.logger.info(f"✅ Found {len(ebook_results)} ebook matches!")
                for ebook in ebook_results:
                    self.logger.info(f"   📖 {ebook['title']} (confidence: {ebook['confidence']:.2f}, seeders: {ebook['seeders']})")
            else:
                self.logger.info("❌ No ebook matches found")
            
            # Save results to database
            search_query = f"{audiobook['clean_title']} {audiobook['clean_author']}"
            self.save_ebook_results(audiobook['audiobook_id'], search_query, ebook_results)
            
            # Rate limiting delay
            if i < len(audiobooks):  # Don't delay after the last item
                self.logger.info(f"⏳ Rate limiting delay ({self.request_delay}s)...")
                time.sleep(self.request_delay)
        
        self.logger.info(f"🎉 Batch complete! Discovered {discoveries} ebooks total")
        self.print_statistics()
    
    def print_statistics(self):
        """
        Print current discovery statistics
        """
        conn = self.get_database_connection()
        cursor = conn.cursor()
        
        # Get stats
        cursor.execute("SELECT COUNT(*) FROM audiobooks")
        total_audiobooks = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT audiobook_id) FROM ebooks")
        audiobooks_with_ebooks = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ebooks")
        total_ebooks = cursor.fetchone()[0]
        
        coverage = (audiobooks_with_ebooks / total_audiobooks * 100) if total_audiobooks > 0 else 0
        
        conn.close()
        
        print("\n" + "="*60)
        print("📊 EBOOK DISCOVERY STATISTICS")
        print("="*60)
        print(f"📚 Total Audiobooks: {total_audiobooks:,}")
        print(f"✅ Audiobooks with Ebooks Found: {audiobooks_with_ebooks:,}")
        print(f"📖 Total Ebooks Discovered: {total_ebooks:,}")
        print(f"📈 Coverage: {coverage:.1f}%")
        print(f"🎯 Remaining: {total_audiobooks - audiobooks_with_ebooks:,}")
        print("="*60)

def main():
    """
    Main function to run ebook discovery
    """
    print("🎊 LibraryOfBabel Ebook Discovery Pipeline")
    print("Using MAM API Direct Access - No Playwright needed!")
    print("="*60)
    
    try:
        pipeline = EbookDiscoveryPipeline()
        
        # Run discovery batch
        batch_size = 5  # Start with very small batch for testing
        pipeline.run_discovery_batch(batch_size)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())