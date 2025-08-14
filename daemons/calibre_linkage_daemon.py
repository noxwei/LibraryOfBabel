#!/usr/bin/env python3
"""
Calibre Linkage Background Daemon
==================================

Continuously processes all books in the Calibre library and creates
PostgreSQL-Calibre linkages for download endpoints.

Author: Dr. Sarah Chen (陈雪芳) - PostgreSQL-First Architecture
Integration: Dr. Marcus Wong (王志明) - Calibre EPUB Library Architect
Purpose: Automatically expand download-ready book collection
"""

import time
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import subprocess
from pathlib import Path
import json
from datetime import datetime
import signal
import sys
import os

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from calibre_path_resolver import CalibrePathResolver

# Setup daemon logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - CALIBRE_DAEMON - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/weixiangzhang/Local_Dev/LibraryOfBabel/logs/calibre_linkage_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CalibreLinkageDaemon:
    """Background daemon for PostgreSQL-Calibre linkage processing"""
    
    def __init__(self, calibre_library_path="/Users/weixiangzhang/Calibre Library"):
        self.calibre_library_path = calibre_library_path
        self.calibredb_path = "/Applications/calibre.app/Contents/MacOS/calibredb"
        self.path_resolver = CalibrePathResolver(calibre_library_path)
        self.running = True
        self.batch_size = 20
        self.sleep_interval = 5  # seconds between batches (faster for monitoring)
        self.detailed_monitoring_limit = 500  # Enhanced monitoring for first 500
        
        # Statistics
        self.stats = {
            "daemon_start_time": datetime.now(),
            "total_calibre_books_found": 0,
            "linkages_created": 0,
            "linkages_updated": 0,
            "processing_errors": 0,
            "batches_completed": 0,
            "last_batch_time": None
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"📡 Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def _safe_get_nested(self, data, key1, key2):
        """Safely get nested value from dict, handling string values"""
        if not isinstance(data, dict):
            return None
        
        value1 = data.get(key1)
        if not isinstance(value1, dict):
            return None
        
        return value1.get(key2)
        
    def connect_database(self):
        """Connect to PostgreSQL database"""
        return psycopg2.connect(
            host='localhost',
            database='knowledge_base',
            user='weixiangzhang',
            password=os.environ.get('DB_PASSWORD')
        )
    
    def get_all_calibre_books(self):
        """Get all books from Calibre library"""
        try:
            cmd = [self.calibredb_path, "list", "--library-path", self.calibre_library_path,
                   "--fields", "id,title,authors", "--for-machine"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            books = json.loads(result.stdout)
            
            logger.info(f"📚 Found {len(books)} books in Calibre library")
            self.stats["total_calibre_books_found"] = len(books)
            
            return books
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to get Calibre book list: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse Calibre JSON output: {e}")
            return []
    
    def find_matching_postgres_book(self, calibre_book):
        """Find matching PostgreSQL book for a Calibre book"""
        try:
            calibre_title = calibre_book.get('title', '').strip()
            calibre_authors = calibre_book.get('authors', '').strip()
            
            if not calibre_title:
                return None
                
            with self.connect_database() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Try exact title match first
                    cur.execute("""
                        SELECT book_id, title, author 
                        FROM books 
                        WHERE LOWER(title) = LOWER(%s)
                        LIMIT 1
                    """, (calibre_title,))
                    
                    match = cur.fetchone()
                    if match:
                        return match
                    
                    # Try partial title match
                    cur.execute("""
                        SELECT book_id, title, author 
                        FROM books 
                        WHERE title ILIKE %s
                        ORDER BY similarity(title, %s) DESC
                        LIMIT 1
                    """, (f"%{calibre_title[:30]}%", calibre_title))
                    
                    match = cur.fetchone()
                    if match:
                        return match
                    
                    # Try author-based search if we have authors
                    if calibre_authors:
                        first_author = calibre_authors.split(',')[0].strip()
                        cur.execute("""
                            SELECT book_id, title, author 
                            FROM books 
                            WHERE author ILIKE %s AND title ILIKE %s
                            LIMIT 1
                        """, (f"%{first_author}%", f"%{calibre_title[:20]}%"))
                        
                        match = cur.fetchone()
                        return match
                    
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error finding PostgreSQL match for '{calibre_title}': {e}")
            return None
    
    def create_calibre_linkage(self, postgres_book_id, calibre_book):
        """Create PostgreSQL-Calibre linkage"""
        try:
            calibre_id = calibre_book['id']
            
            # Get Calibre file path
            calibre_path = self.path_resolver.resolve_calibre_file_path(calibre_id)
            if not calibre_path:
                logger.warning(f"⚠️ Could not resolve file path for Calibre book {calibre_id}")
                return False, "File path not found"
            
            # Get enhanced Calibre metadata
            calibre_metadata = self.path_resolver.get_book_metadata(calibre_id)
            
            # Ensure calibre_metadata is a dict, not a string
            if isinstance(calibre_metadata, str):
                try:
                    calibre_metadata = json.loads(calibre_metadata)
                except (json.JSONDecodeError, TypeError):
                    calibre_metadata = {}
            
            # Get file info
            file_info = self.path_resolver.get_file_info(calibre_path) if calibre_path else None
            file_size = file_info['size_bytes'] if file_info else None
            
            with self.connect_database() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Use Dr. Sarah Chen's PostgreSQL function
                    cur.execute("""
                        SELECT api_link_calibre_book(
                            %s::BIGINT,          -- postgres_book_id
                            %s::INTEGER,         -- calibre_id
                            %s::TEXT,           -- calibre_path
                            %s::TEXT,           -- calibre_title
                            %s::TEXT,           -- calibre_author
                            %s::TEXT,           -- calibre_isbn
                            %s::TEXT,           -- calibre_description
                            %s::VARCHAR(64),    -- file_hash
                            %s::BIGINT          -- file_size_bytes
                        ) as result
                    """, (
                        postgres_book_id,
                        int(calibre_id),
                        calibre_path,
                        calibre_metadata.get('Title') if calibre_metadata else None,
                        calibre_metadata.get('Author(s)') if calibre_metadata else None,
                        self._safe_get_nested(calibre_metadata, 'Identifiers', 'isbn') if calibre_metadata else None,
                        calibre_metadata.get('Comments') if calibre_metadata else None,
                        None,  # file_hash - could compute if needed
                        file_size
                    ))
                    
                    result = cur.fetchone()['result']
                    
                    # Parse JSON result if it's a string
                    if isinstance(result, str):
                        result = json.loads(result)
                    
                    if result.get('success'):
                        action = result.get('action', 'unknown')
                        if action == 'created':
                            self.stats["linkages_created"] += 1
                        elif action == 'updated':
                            self.stats["linkages_updated"] += 1
                        return True, f"Linkage {action}"
                    else:
                        error_msg = result.get('error', 'Unknown error')
                        return False, f"Linkage failed: {error_msg}"
                        
        except Exception as e:
            logger.error(f"❌ Error creating linkage for Calibre book {calibre_book.get('id')}: {e}")
            return False, f"Exception: {str(e)}"
    
    def process_calibre_book(self, calibre_book):
        """Process a single Calibre book"""
        calibre_id = calibre_book.get('id')
        calibre_title = calibre_book.get('title', 'Unknown')
        
        logger.info(f"🔄 Processing Calibre book {calibre_id}: {calibre_title[:50]}...")
        
        # Check if already linked
        try:
            with self.connect_database() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM calibre_books WHERE calibre_id = %s", (calibre_id,))
                    if cur.fetchone():
                        logger.debug(f"⏭️ Book {calibre_id} already linked, skipping")
                        return True, "Already linked"
        except Exception as e:
            logger.error(f"❌ Error checking existing linkage: {e}")
        
        # Find matching PostgreSQL book
        postgres_book = self.find_matching_postgres_book(calibre_book)
        if not postgres_book:
            logger.debug(f"⚠️ No PostgreSQL match found for '{calibre_title}'")
            return False, "No PostgreSQL match"
        
        # Create linkage
        success, message = self.create_calibre_linkage(postgres_book['book_id'], calibre_book)
        if success:
            logger.info(f"✅ {message} for book {postgres_book['book_id']} -> Calibre {calibre_id}")
            return True, message
        else:
            logger.warning(f"⚠️ {message}")
            self.stats["processing_errors"] += 1
            return False, message
    
    def process_batch(self, calibre_books, batch_num, total_processed):
        """Process a batch of Calibre books with enhanced monitoring"""
        successful = 0
        failed = 0
        
        for calibre_book in calibre_books:
            if not self.running:
                break
                
            success, message = self.process_calibre_book(calibre_book)
            if success:
                successful += 1
            else:
                failed += 1
        
        self.stats["batches_completed"] += 1
        self.stats["last_batch_time"] = datetime.now()
        
        batch_success_rate = (successful/len(calibre_books)*100) if calibre_books else 0
        logger.info(f"📊 Batch {batch_num} completed: {successful}/{len(calibre_books)} successful ({batch_success_rate:.1f}%)")
        
        # Enhanced monitoring for first 500 books
        if total_processed <= self.detailed_monitoring_limit:
            if total_processed % 100 == 0 or total_processed == self.detailed_monitoring_limit:
                self.print_detailed_checkpoint(total_processed)
        
        return successful, failed
    
    def print_detailed_checkpoint(self, books_processed):
        """Print detailed checkpoint for monitoring first 500 books"""
        runtime = datetime.now() - self.stats["daemon_start_time"]
        total_success = self.stats["linkages_created"] + self.stats["linkages_updated"]
        
        logger.info("🔍" + "="*50)
        logger.info(f"📋 CHECKPOINT - {books_processed:,} BOOKS PROCESSED")
        logger.info("🔍" + "="*50)
        logger.info(f"✅ Download Links Created: {total_success:,}")
        logger.info(f"🔄 New Linkages: {self.stats['linkages_created']:,}")
        logger.info(f"📝 Updated Linkages: {self.stats['linkages_updated']:,}")
        logger.info(f"❌ Processing Errors: {self.stats['processing_errors']:,}")
        logger.info(f"⏱️ Runtime: {runtime}")
        
        if books_processed > 0:
            success_rate = (total_success / books_processed) * 100
            books_per_minute = books_processed / (runtime.total_seconds() / 60) if runtime.total_seconds() > 0 else 0
            estimated_completion = (self.stats["total_calibre_books_found"] - books_processed) / books_per_minute if books_per_minute > 0 else 0
            
            logger.info(f"📈 Success Rate: {success_rate:.1f}%")
            logger.info(f"⚡ Processing Speed: {books_per_minute:.1f} books/minute")
            logger.info(f"🕐 Estimated Time Remaining: {estimated_completion:.1f} minutes")
        
        logger.info("🔍" + "="*50)
        
        # Also save checkpoint to file
        checkpoint_data = {
            "checkpoint_time": datetime.now().isoformat(),
            "books_processed": books_processed,
            "download_links_ready": total_success,
            "success_rate_percent": (total_success / books_processed) * 100 if books_processed > 0 else 0,
            "runtime_minutes": runtime.total_seconds() / 60
        }
        
        with open(f"calibre_checkpoint_{books_processed}.json", "w") as f:
            json.dump(checkpoint_data, f, indent=2)
        
        logger.info(f"💾 Checkpoint saved to: calibre_checkpoint_{books_processed}.json")
    
    def save_progress(self):
        """Save current progress to file"""
        progress_data = {
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats.copy(),
            "runtime_minutes": (datetime.now() - self.stats["daemon_start_time"]).total_seconds() / 60
        }
        
        # Convert datetime to string for JSON serialization
        for key, value in progress_data["stats"].items():
            if isinstance(value, datetime):
                progress_data["stats"][key] = value.isoformat()
        
        with open("calibre_linkage_daemon_progress.json", "w") as f:
            json.dump(progress_data, f, indent=2)
    
    def print_status(self):
        """Print current daemon status"""
        runtime = datetime.now() - self.stats["daemon_start_time"]
        
        logger.info("=" * 60)
        logger.info("📊 CALIBRE LINKAGE DAEMON STATUS")
        logger.info("=" * 60)
        logger.info(f"📚 Total Calibre Books Found: {self.stats['total_calibre_books_found']}")
        logger.info(f"✅ Linkages Created: {self.stats['linkages_created']}")
        logger.info(f"🔄 Linkages Updated: {self.stats['linkages_updated']}")
        logger.info(f"❌ Processing Errors: {self.stats['processing_errors']}")
        logger.info(f"📦 Batches Completed: {self.stats['batches_completed']}")
        logger.info(f"⏱️ Runtime: {runtime}")
        logger.info(f"🔗 Total Download Links Ready: {self.stats['linkages_created'] + self.stats['linkages_updated']}")
        
        if self.stats['total_calibre_books_found'] > 0:
            completion_rate = ((self.stats['linkages_created'] + self.stats['linkages_updated']) / 
                              self.stats['total_calibre_books_found']) * 100
            logger.info(f"📈 Completion Rate: {completion_rate:.1f}%")
    
    def run(self):
        """Main daemon loop"""
        logger.info("🚀 Starting Calibre Linkage Daemon")
        logger.info(f"📍 Calibre Library: {self.calibre_library_path}")
        logger.info(f"📦 Batch Size: {self.batch_size}")
        logger.info(f"⏱️ Sleep Interval: {self.sleep_interval} seconds")
        
        try:
            # Get all Calibre books
            calibre_books = self.get_all_calibre_books()
            if not calibre_books:
                logger.error("❌ No books found in Calibre library, exiting")
                return
            
            # Process in batches
            total_batches = (len(calibre_books) + self.batch_size - 1) // self.batch_size
            
            for batch_num in range(total_batches):
                if not self.running:
                    break
                    
                start_idx = batch_num * self.batch_size
                end_idx = min(start_idx + self.batch_size, len(calibre_books))
                batch = calibre_books[start_idx:end_idx]
                total_processed = end_idx
                
                logger.info(f"📦 Processing batch {batch_num + 1}/{total_batches} (Books {start_idx + 1}-{end_idx})")
                
                successful, failed = self.process_batch(batch, batch_num + 1, total_processed)
                
                # Save progress
                self.save_progress()
                
                # Print status every 10 batches (unless in detailed monitoring mode)
                if total_processed > self.detailed_monitoring_limit and (batch_num + 1) % 10 == 0:
                    self.print_status()
                
                # Sleep between batches (unless it's the last batch)
                if batch_num < total_batches - 1 and self.running:
                    if total_processed <= self.detailed_monitoring_limit:
                        logger.info(f"😴 Brief pause for {self.sleep_interval} seconds...")
                    else:
                        logger.info(f"😴 Sleeping for {self.sleep_interval} seconds...")
                    time.sleep(self.sleep_interval)
            
            # Final status
            self.print_status()
            logger.info("🎉 Calibre Linkage Daemon completed successfully!")
            
        except KeyboardInterrupt:
            logger.info("⚠️ Daemon interrupted by user")
        except Exception as e:
            logger.error(f"❌ Daemon error: {e}")
        finally:
            self.save_progress()
            logger.info("💾 Progress saved, daemon shutting down")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Calibre Linkage Background Daemon")
    parser.add_argument("--batch-size", type=int, default=20, help="Books to process per batch")
    parser.add_argument("--sleep-interval", type=int, default=10, help="Seconds to sleep between batches")
    parser.add_argument("--calibre-path", default="/Users/weixiangzhang/Calibre Library", help="Path to Calibre library")
    
    args = parser.parse_args()
    
    daemon = CalibreLinkageDaemon(args.calibre_path)
    daemon.batch_size = args.batch_size
    daemon.sleep_interval = args.sleep_interval
    
    daemon.run()