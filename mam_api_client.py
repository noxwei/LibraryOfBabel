#!/usr/bin/env python3
"""
MAM API Client for LibraryOfBabel
Converts audiobook metadata to ebook downloads with 100/day rate limiting
"""

import sqlite3
import requests
import time
import json
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import os
from urllib.parse import quote_plus

@dataclass
class AudiobookMetadata:
    """Structured audiobook metadata from Plex database"""
    album_id: int
    title: str
    author: str
    release_date: str
    summary: str
    duration: float
    file_path: str
    
    @property
    def clean_title(self) -> str:
        """Clean title for MAM search"""
        # Remove common audiobook artifacts
        title = self.title
        title = re.sub(r'\s*\(Unabridged\)', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*\(Abridged\)', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*Audiobook.*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*Audio\s*Book.*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*\[.*?\]', '', title)  # Remove brackets
        title = re.sub(r'\s+', ' ', title).strip()
        return title
    
    @property
    def clean_author(self) -> str:
        """Clean author name for search"""
        author = self.author
        # Remove narrator information
        author = re.sub(r'\s*\(.*narrat.*\)', '', author, flags=re.IGNORECASE)
        author = re.sub(r'\s*narrat.*by.*$', '', author, flags=re.IGNORECASE)
        author = re.sub(r'\s*read\s*by.*$', '', author, flags=re.IGNORECASE)
        author = re.sub(r'\s+', ' ', author).strip()
        return author

@dataclass
class MAMSearchResult:
    """MAM torrent search result"""
    torrent_id: str
    title: str
    author: str
    size_mb: float
    seeders: int
    leechers: int
    category: str
    download_url: str
    upload_date: str
    match_confidence: float

class MAMRateLimiter:
    """Rate limiter for MAM API (100 requests per day)"""
    
    def __init__(self, max_daily_requests: int = 95):  # Leave buffer for manual searches
        self.max_daily_requests = max_daily_requests
        self.request_log_file = Path("mam_request_log.json")
        self.load_request_log()
    
    def load_request_log(self):
        """Load request log from disk"""
        if self.request_log_file.exists():
            with open(self.request_log_file, 'r') as f:
                self.request_log = json.load(f)
        else:
            self.request_log = []
    
    def save_request_log(self):
        """Save request log to disk"""
        with open(self.request_log_file, 'w') as f:
            json.dump(self.request_log, f, indent=2)
    
    def can_make_request(self) -> bool:
        """Check if we can make another request today"""
        today = datetime.now().strftime('%Y-%m-%d')
        today_requests = [r for r in self.request_log if r['date'] == today]
        return len(today_requests) < self.max_daily_requests
    
    def log_request(self):
        """Log a successful request"""
        self.request_log.append({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'timestamp': datetime.now().isoformat()
        })
        # Keep only last 7 days
        cutoff = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        self.request_log = [r for r in self.request_log if r['date'] >= cutoff]
        self.save_request_log()
    
    def requests_remaining_today(self) -> int:
        """Get remaining requests for today"""
        today = datetime.now().strftime('%Y-%m-%d')
        today_requests = [r for r in self.request_log if r['date'] == today]
        return self.max_daily_requests - len(today_requests)

class MAMClient:
    """MyAnonamouse API client for ebook searching and downloading"""
    
    def __init__(self, session_cookie: str):
        self.session_cookie = session_cookie
        self.base_url = "https://www.myanonamouse.net"
        self.rate_limiter = MAMRateLimiter()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Cookie': f'mam_id={session_cookie}'
        })
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('mam_client.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def search_ebooks(self, audiobook: AudiobookMetadata) -> List[MAMSearchResult]:
        """Search MAM for ebook versions of audiobook"""
        
        if not self.rate_limiter.can_make_request():
            remaining = self.rate_limiter.requests_remaining_today()
            self.logger.warning(f"Rate limit reached. {remaining} requests remaining today.")
            return []
        
        # Build search query
        search_params = {
            'tor[text]': f"{audiobook.clean_title} {audiobook.clean_author}",
            'tor[srchIn][title]': True,
            'tor[srchIn][author]': True,
            'tor[cat][]': 14,  # E-Books category
            'tor[browseFlagsHideVsShow]': 0,
            'tor[sortType]': 'seeders',  # Sort by seeders desc
            'tor[perpage]': 25
        }
        
        try:
            # Make API request
            url = f"{self.base_url}/tor/js/loadSearchJSONbasic.php"
            response = self.session.get(url, params=search_params, timeout=30)
            response.raise_for_status()
            
            self.rate_limiter.log_request()
            
            data = response.json()
            results = []
            
            if 'data' in data:
                for item in data['data']:
                    result = MAMSearchResult(
                        torrent_id=item.get('id', ''),
                        title=item.get('title', ''),
                        author=item.get('author', ''),
                        size_mb=float(item.get('size', 0)) / (1024 * 1024),
                        seeders=int(item.get('seeders', 0)),
                        leechers=int(item.get('leechers', 0)),
                        category=item.get('cat_name', ''),
                        download_url=f"{self.base_url}/tor/download.php?tid={item.get('id', '')}",
                        upload_date=item.get('added', ''),
                        match_confidence=self._calculate_match_confidence(audiobook, item)
                    )
                    results.append(result)
            
            # Sort by match confidence, then by seeders
            results.sort(key=lambda x: (x.match_confidence, x.seeders), reverse=True)
            
            self.logger.info(f"Found {len(results)} results for '{audiobook.clean_title}'")
            return results
            
        except requests.RequestException as e:
            self.logger.error(f"MAM API request failed: {e}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse MAM response: {e}")
            return []
    
    def _calculate_match_confidence(self, audiobook: AudiobookMetadata, mam_result: Dict) -> float:
        """Calculate confidence score for audiobook-ebook match"""
        
        title_similarity = self._string_similarity(
            audiobook.clean_title.lower(),
            mam_result.get('title', '').lower()
        )
        
        author_similarity = self._string_similarity(
            audiobook.clean_author.lower(),
            mam_result.get('author', '').lower()
        )
        
        # Weight factors
        base_score = (title_similarity * 0.7) + (author_similarity * 0.3)
        
        # Bonus for good seeders
        if int(mam_result.get('seeders', 0)) >= 5:
            base_score += 0.1
        
        # Penalty for very large files (likely scans/poor quality)
        size_mb = float(mam_result.get('size', 0)) / (1024 * 1024)
        if size_mb > 100:
            base_score -= 0.1
        
        return min(1.0, max(0.0, base_score))
    
    def _string_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using simple token matching"""
        tokens1 = set(re.findall(r'\w+', str1.lower()))
        tokens2 = set(re.findall(r'\w+', str2.lower()))
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        return len(intersection) / len(union) if union else 0.0

class AudiobookExtractor:
    """Extract audiobook metadata from Plex database"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
    
    def get_audiobooks(self, limit: Optional[int] = None) -> List[AudiobookMetadata]:
        """Extract audiobook metadata from database"""
        
        query = """
        SELECT DISTINCT
            albumId,
            albumTitle,
            albumArtistName, 
            albumDateReleased,
            albumSummary,
            albumDuration,
            path
        FROM item 
        WHERE trackNumber = 1
        AND albumTitle IS NOT NULL 
        AND albumArtistName IS NOT NULL
        ORDER BY albumTitle
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        audiobooks = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                
                for row in cursor.fetchall():
                    audiobook = AudiobookMetadata(
                        album_id=row[0],
                        title=row[1] or '',
                        author=row[2] or '',
                        release_date=row[3] or '',
                        summary=row[4] or '',
                        duration=row[5] or 0.0,
                        file_path=row[6] or ''
                    )
                    audiobooks.append(audiobook)
                    
            self.logger.info(f"Extracted {len(audiobooks)} audiobooks from database")
            return audiobooks
            
        except sqlite3.Error as e:
            self.logger.error(f"Database error: {e}")
            return []

class EbookDownloadManager:
    """Manage ebook downloads with progress tracking"""
    
    def __init__(self, download_dir: str):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.progress_file = self.download_dir / "download_progress.json"
        self.load_progress()
        self.logger = logging.getLogger(__name__)
    
    def load_progress(self):
        """Load download progress from disk"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                self.progress = json.load(f)
        else:
            self.progress = {
                'downloaded': [],
                'failed': [],
                'skipped': []
            }
    
    def save_progress(self):
        """Save download progress to disk"""
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)
    
    def download_torrent(self, result: MAMSearchResult, audiobook: AudiobookMetadata) -> bool:
        """Download torrent file for ebook"""
        
        # Check if already downloaded
        if result.torrent_id in self.progress['downloaded']:
            self.logger.info(f"Already downloaded: {result.title}")
            return True
        
        try:
            # Create safe filename
            safe_filename = re.sub(r'[^\w\s-]', '', result.title)
            safe_filename = re.sub(r'[-\s]+', '-', safe_filename)
            torrent_file = self.download_dir / f"{safe_filename}_{result.torrent_id}.torrent"
            
            # Download torrent file
            response = requests.get(result.download_url, timeout=30)
            response.raise_for_status()
            
            with open(torrent_file, 'wb') as f:
                f.write(response.content)
            
            # Log successful download
            self.progress['downloaded'].append(result.torrent_id)
            self.save_progress()
            
            self.logger.info(f"Downloaded: {result.title} -> {torrent_file.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Download failed for {result.title}: {e}")
            self.progress['failed'].append({
                'torrent_id': result.torrent_id,
                'title': result.title,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            self.save_progress()
            return False

def main():
    """Main execution function"""
    
    # Configuration
    DB_PATH = "/Users/weixiangzhang/Local Dev/audiobook-metadata-extractor/library_1750488304.db"
    DOWNLOAD_DIR = "/Users/weixiangzhang/Local Dev/LibraryOfBabel/mam_downloads"
    SESSION_COOKIE = os.getenv('MAM_SESSION_COOKIE', '')
    
    if not SESSION_COOKIE:
        print("Error: MAM_SESSION_COOKIE environment variable not set")
        return
    
    # Initialize components
    extractor = AudiobookExtractor(DB_PATH)
    mam_client = MAMClient(SESSION_COOKIE)
    download_manager = EbookDownloadManager(DOWNLOAD_DIR)
    
    # Check rate limit status
    remaining = mam_client.rate_limiter.requests_remaining_today()
    print(f"MAM requests remaining today: {remaining}")
    
    if remaining <= 0:
        print("Rate limit reached for today. Try again tomorrow.")
        return
    
    # Get audiobooks (limit to available requests)
    audiobooks = extractor.get_audiobooks(limit=min(remaining, 20))
    
    print(f"Processing {len(audiobooks)} audiobooks...")
    
    successful_matches = 0
    total_downloads = 0
    
    for i, audiobook in enumerate(audiobooks, 1):
        print(f"\n[{i}/{len(audiobooks)}] Searching: {audiobook.clean_title} by {audiobook.clean_author}")
        
        # Search for ebook versions
        results = mam_client.search_ebooks(audiobook)
        
        if not results:
            print("  No results found")
            continue
        
        # Take best match if confidence > 0.6
        best_match = results[0]
        if best_match.match_confidence > 0.6:
            print(f"  Found match: {best_match.title} (confidence: {best_match.match_confidence:.2f})")
            print(f"  Author: {best_match.author}, Seeders: {best_match.seeders}")
            
            # Download torrent
            if download_manager.download_torrent(best_match, audiobook):
                successful_matches += 1
                total_downloads += 1
            
        else:
            print(f"  Low confidence match: {best_match.title} (confidence: {best_match.match_confidence:.2f})")
        
        # Rate limiting delay
        time.sleep(2)
        
        # Check if we're approaching limit
        if mam_client.rate_limiter.requests_remaining_today() <= 5:
            print("\nApproaching daily rate limit. Stopping.")
            break
    
    # Summary
    print(f"\n=== MAM Download Summary ===")
    print(f"Audiobooks processed: {len(audiobooks)}")
    print(f"Successful matches: {successful_matches}")
    print(f"Torrents downloaded: {total_downloads}")
    print(f"Requests remaining: {mam_client.rate_limiter.requests_remaining_today()}")
    print(f"Download directory: {DOWNLOAD_DIR}")

if __name__ == "__main__":
    main()