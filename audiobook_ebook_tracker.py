#!/usr/bin/env python3
"""
Audiobook-Ebook Tracker Database
Tracks which audiobooks have corresponding ebooks available/downloaded
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

@dataclass
class AudiobookRecord:
    """Audiobook metadata from Plex database"""
    album_id: int
    title: str
    author: str
    release_date: str
    summary: str
    duration_hours: float
    file_path: str
    file_size_mb: float
    
    @property
    def clean_title(self) -> str:
        """Clean title for searching"""
        import re
        title = self.title
        title = re.sub(r'\s*\(Unabridged\)', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*\(Abridged\)', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*Audiobook.*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*\[.*?\]', '', title)
        return re.sub(r'\s+', ' ', title).strip()

@dataclass
class EbookRecord:
    """Ebook availability and download status"""
    audiobook_id: int
    mam_torrent_id: str
    ebook_title: str
    ebook_author: str
    file_format: str  # epub, pdf, mobi, etc.
    file_size_mb: float
    seeders: int
    leechers: int
    match_confidence: float
    discovered_date: str
    download_status: str  # 'available', 'downloading', 'completed', 'failed'
    download_date: Optional[str] = None
    local_file_path: Optional[str] = None
    torrent_file_path: Optional[str] = None

class AudiobookEbookTracker:
    """Database to track audiobook-ebook relationships and download status"""
    
    def __init__(self, db_path: str = "audiobook_ebook_tracker.db"):
        self.db_path = db_path
        self.init_database()
        self.logger = logging.getLogger(__name__)
    
    def init_database(self):
        """Initialize database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                -- Audiobooks table (from Plex database)
                CREATE TABLE IF NOT EXISTS audiobooks (
                    album_id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    release_date TEXT,
                    summary TEXT,
                    duration_hours REAL,
                    file_path TEXT,
                    file_size_mb REAL,
                    clean_title TEXT,
                    clean_author TEXT,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Ebooks table (MAM search results and downloads)
                CREATE TABLE IF NOT EXISTS ebooks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    audiobook_id INTEGER,
                    mam_torrent_id TEXT UNIQUE,
                    ebook_title TEXT NOT NULL,
                    ebook_author TEXT NOT NULL,
                    file_format TEXT,
                    file_size_mb REAL,
                    seeders INTEGER,
                    leechers INTEGER,
                    match_confidence REAL,
                    discovered_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    download_status TEXT DEFAULT 'available',
                    download_date DATETIME,
                    local_file_path TEXT,
                    torrent_file_path TEXT,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (audiobook_id) REFERENCES audiobooks (album_id)
                );
                
                -- Search attempts log
                CREATE TABLE IF NOT EXISTS search_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    audiobook_id INTEGER,
                    search_query TEXT,
                    results_found INTEGER,
                    search_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    search_engine TEXT DEFAULT 'MAM',
                    FOREIGN KEY (audiobook_id) REFERENCES audiobooks (album_id)
                );
                
                -- Download queue
                CREATE TABLE IF NOT EXISTS download_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ebook_id INTEGER,
                    priority INTEGER DEFAULT 5,
                    added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    started_date DATETIME,
                    completed_date DATETIME,
                    status TEXT DEFAULT 'queued',
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    FOREIGN KEY (ebook_id) REFERENCES ebooks (id)
                );
                
                -- Collection statistics
                CREATE TABLE IF NOT EXISTS collection_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    total_audiobooks INTEGER,
                    audiobooks_with_ebooks INTEGER,
                    audiobooks_without_ebooks INTEGER,
                    total_ebooks_available INTEGER,
                    total_ebooks_downloaded INTEGER,
                    coverage_percentage REAL,
                    last_calculated DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Indexes for performance
                CREATE INDEX IF NOT EXISTS idx_audiobooks_title ON audiobooks (clean_title);
                CREATE INDEX IF NOT EXISTS idx_audiobooks_author ON audiobooks (clean_author);
                CREATE INDEX IF NOT EXISTS idx_ebooks_audiobook ON ebooks (audiobook_id);
                CREATE INDEX IF NOT EXISTS idx_ebooks_status ON ebooks (download_status);
                CREATE INDEX IF NOT EXISTS idx_search_attempts_audiobook ON search_attempts (audiobook_id);
                CREATE INDEX IF NOT EXISTS idx_download_queue_status ON download_queue (status);
            """)
    
    def import_audiobooks_from_plex(self, plex_db_path: str) -> int:
        """Import audiobook metadata from Plex database"""
        import re
        
        plex_query = """
        SELECT 
            ROW_NUMBER() OVER (ORDER BY albumTitle, albumArtistName) as unique_id,
            albumTitle,
            albumArtistName, 
            albumDateReleased,
            albumSummary,
            SUM(duration) as total_duration,
            MIN(path) as sample_path,
            SUM(fileSize) as total_file_size
        FROM item 
        WHERE albumTitle IS NOT NULL 
        AND albumArtistName IS NOT NULL
        AND albumTitle != ''
        AND albumArtistName != ''
        GROUP BY albumTitle, albumArtistName
        ORDER BY albumTitle, albumArtistName
        """
        
        imported_count = 0
        
        try:
            # Connect to Plex database
            with sqlite3.connect(plex_db_path) as plex_conn:
                plex_cursor = plex_conn.cursor()
                plex_cursor.execute(plex_query)
                
                # Connect to tracker database
                with sqlite3.connect(self.db_path) as tracker_conn:
                    for row in plex_cursor.fetchall():
                        # Clean title and author for better matching
                        clean_title = row[1] or ''
                        clean_title = re.sub(r'\s*\(Unabridged\)', '', clean_title, flags=re.IGNORECASE)
                        clean_title = re.sub(r'\s*\(Abridged\)', '', clean_title, flags=re.IGNORECASE)
                        clean_title = re.sub(r'\s*Audiobook.*$', '', clean_title, flags=re.IGNORECASE)
                        clean_title = re.sub(r'\s*\[.*?\]', '', clean_title)
                        clean_title = re.sub(r'\s+', ' ', clean_title).strip()
                        
                        clean_author = row[2] or ''
                        clean_author = re.sub(r'\s*\(.*narrat.*\)', '', clean_author, flags=re.IGNORECASE)
                        clean_author = re.sub(r'\s*narrat.*by.*$', '', clean_author, flags=re.IGNORECASE)
                        clean_author = re.sub(r'\s*read\s*by.*$', '', clean_author, flags=re.IGNORECASE)
                        clean_author = re.sub(r'\s+', ' ', clean_author).strip()
                        
                        # Convert duration to hours
                        duration_seconds = row[5] or 0
                        duration_hours = duration_seconds / 3600
                        
                        # Convert file size to MB
                        file_size_bytes = row[7] or 0
                        file_size_mb = file_size_bytes / (1024 * 1024)
                        
                        # Insert into tracker database
                        tracker_conn.execute("""
                            INSERT OR REPLACE INTO audiobooks (
                                album_id, title, author, release_date, summary,
                                duration_hours, file_path, file_size_mb,
                                clean_title, clean_author, last_updated
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """, (
                            row[0],  # unique_id
                            row[1],  # title
                            row[2],  # author
                            row[3],  # release_date
                            row[4],  # summary
                            duration_hours,
                            row[6],  # sample_path
                            file_size_mb,
                            clean_title,
                            clean_author
                        ))
                        
                        imported_count += 1
                    
                    tracker_conn.commit()
            
            self.logger.info(f"Imported {imported_count} audiobooks from Plex database")
            return imported_count
            
        except sqlite3.Error as e:
            self.logger.error(f"Database error importing audiobooks: {e}")
            return 0
    
    def add_ebook_result(self, ebook: EbookRecord) -> bool:
        """Add ebook search result to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO ebooks (
                        audiobook_id, mam_torrent_id, ebook_title, ebook_author,
                        file_format, file_size_mb, seeders, leechers,
                        match_confidence, download_status, torrent_file_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ebook.audiobook_id,
                    ebook.mam_torrent_id,
                    ebook.ebook_title,
                    ebook.ebook_author,
                    ebook.file_format,
                    ebook.file_size_mb,
                    ebook.seeders,
                    ebook.leechers,
                    ebook.match_confidence,
                    ebook.download_status,
                    ebook.torrent_file_path
                ))
                conn.commit()
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Error adding ebook result: {e}")
            return False
    
    def log_search_attempt(self, audiobook_id: int, search_query: str, results_found: int):
        """Log search attempt for audiobook"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO search_attempts (audiobook_id, search_query, results_found)
                    VALUES (?, ?, ?)
                """, (audiobook_id, search_query, results_found))
                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Error logging search attempt: {e}")
    
    def get_audiobooks_without_ebooks(self, limit: Optional[int] = None) -> List[Dict]:
        """Get audiobooks that don't have corresponding ebooks yet"""
        query = """
        SELECT a.album_id, a.title, a.author, a.clean_title, a.clean_author,
               a.duration_hours, a.file_size_mb
        FROM audiobooks a
        LEFT JOIN ebooks e ON a.album_id = e.audiobook_id
        WHERE e.audiobook_id IS NULL
        ORDER BY a.title
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
                return results
                
        except sqlite3.Error as e:
            self.logger.error(f"Error getting audiobooks without ebooks: {e}")
            return []
    
    def get_audiobooks_with_ebooks(self) -> List[Dict]:
        """Get audiobooks that have corresponding ebooks"""
        query = """
        SELECT a.album_id, a.title, a.author, a.duration_hours,
               e.ebook_title, e.ebook_author, e.file_format,
               e.download_status, e.match_confidence, e.seeders
        FROM audiobooks a
        INNER JOIN ebooks e ON a.album_id = e.audiobook_id
        ORDER BY a.title
        """
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
                return results
                
        except sqlite3.Error as e:
            self.logger.error(f"Error getting audiobooks with ebooks: {e}")
            return []
    
    def update_download_status(self, torrent_id: str, status: str, local_file_path: Optional[str] = None):
        """Update download status for ebook"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if status == 'completed' and local_file_path:
                    conn.execute("""
                        UPDATE ebooks 
                        SET download_status = ?, download_date = CURRENT_TIMESTAMP,
                            local_file_path = ?, last_updated = CURRENT_TIMESTAMP
                        WHERE mam_torrent_id = ?
                    """, (status, local_file_path, torrent_id))
                else:
                    conn.execute("""
                        UPDATE ebooks 
                        SET download_status = ?, last_updated = CURRENT_TIMESTAMP
                        WHERE mam_torrent_id = ?
                    """, (status, torrent_id))
                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Error updating download status: {e}")
    
    def calculate_collection_stats(self) -> Dict:
        """Calculate and store collection statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total audiobooks
                cursor.execute("SELECT COUNT(*) FROM audiobooks")
                total_audiobooks = cursor.fetchone()[0]
                
                # Audiobooks with ebooks
                cursor.execute("""
                    SELECT COUNT(DISTINCT a.album_id) 
                    FROM audiobooks a 
                    INNER JOIN ebooks e ON a.album_id = e.audiobook_id
                """)
                audiobooks_with_ebooks = cursor.fetchone()[0]
                
                # Audiobooks without ebooks
                audiobooks_without_ebooks = total_audiobooks - audiobooks_with_ebooks
                
                # Total ebooks available
                cursor.execute("SELECT COUNT(*) FROM ebooks")
                total_ebooks_available = cursor.fetchone()[0]
                
                # Total ebooks downloaded
                cursor.execute("SELECT COUNT(*) FROM ebooks WHERE download_status = 'completed'")
                total_ebooks_downloaded = cursor.fetchone()[0]
                
                # Coverage percentage
                coverage_percentage = (audiobooks_with_ebooks / total_audiobooks * 100) if total_audiobooks > 0 else 0
                
                stats = {
                    'total_audiobooks': total_audiobooks,
                    'audiobooks_with_ebooks': audiobooks_with_ebooks,
                    'audiobooks_without_ebooks': audiobooks_without_ebooks,
                    'total_ebooks_available': total_ebooks_available,
                    'total_ebooks_downloaded': total_ebooks_downloaded,
                    'coverage_percentage': round(coverage_percentage, 2)
                }
                
                # Store in database
                conn.execute("""
                    INSERT INTO collection_stats (
                        total_audiobooks, audiobooks_with_ebooks, audiobooks_without_ebooks,
                        total_ebooks_available, total_ebooks_downloaded, coverage_percentage
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    total_audiobooks, audiobooks_with_ebooks, audiobooks_without_ebooks,
                    total_ebooks_available, total_ebooks_downloaded, coverage_percentage
                ))
                conn.commit()
                
                return stats
                
        except sqlite3.Error as e:
            self.logger.error(f"Error calculating collection stats: {e}")
            return {}
    
    def export_missing_books_list(self, output_file: str = "missing_ebooks.json"):
        """Export list of audiobooks without ebooks to JSON"""
        missing_books = self.get_audiobooks_without_ebooks()
        
        with open(output_file, 'w') as f:
            json.dump(missing_books, f, indent=2, default=str)
        
        return len(missing_books)

def main():
    """Initialize tracker and import audiobooks"""
    # Configuration
    PLEX_DB_PATH = "/Users/weixiangzhang/Local Dev/audiobook-metadata-extractor/library_1750488304.db"
    TRACKER_DB_PATH = "/Users/weixiangzhang/Local Dev/LibraryOfBabel/audiobook_ebook_tracker.db"
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize tracker
    tracker = AudiobookEbookTracker(TRACKER_DB_PATH)
    
    # Import audiobooks from Plex
    print("Importing audiobooks from Plex database...")
    imported_count = tracker.import_audiobooks_from_plex(PLEX_DB_PATH)
    print(f"Imported {imported_count} audiobooks")
    
    # Calculate initial stats
    print("\nCalculating collection statistics...")
    stats = tracker.calculate_collection_stats()
    
    print(f"""
    === Collection Statistics ===
    Total Audiobooks: {stats.get('total_audiobooks', 0)}
    Audiobooks with Ebooks: {stats.get('audiobooks_with_ebooks', 0)}
    Audiobooks without Ebooks: {stats.get('audiobooks_without_ebooks', 0)}
    Coverage: {stats.get('coverage_percentage', 0)}%
    """)
    
    # Export missing books list
    missing_count = tracker.export_missing_books_list()
    print(f"Exported {missing_count} missing ebooks to missing_ebooks.json")
    
    # Show sample of books without ebooks
    print("\nSample audiobooks without ebooks:")
    missing_books = tracker.get_audiobooks_without_ebooks(limit=10)
    for book in missing_books:
        print(f"  - {book['title']} by {book['author']}")

if __name__ == "__main__":
    main()