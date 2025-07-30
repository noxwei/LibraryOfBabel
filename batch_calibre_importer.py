#!/usr/bin/env python3
"""
Batch Calibre Importer
======================

Imports 3,513 unique books from external drive to Calibre in safe batches
with comprehensive progress tracking and error handling.

Author: Dr. Marcus Wong (王志明) - Calibre EPUB Library Architect
Purpose: Triple LibraryOfBabel collection size for The North Star project
"""

import os
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
import logging
import signal
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - CALIBRE_IMPORTER - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/calibre_batch_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BatchCalibreImporter:
    def __init__(self, scan_results_file="external_drive_scan_results.json"):
        self.calibre_library_path = "/Users/weixiangzhang/Calibre Library"
        self.calibredb_path = "/Applications/calibre.app/Contents/MacOS/calibredb"
        self.scan_results_file = scan_results_file
        self.batch_size = 25  # Safe batch size to avoid overwhelming Calibre
        self.batch_delay = 10  # seconds between batches
        self.running = True
        
        # Statistics
        self.stats = {
            "import_start_time": datetime.now(),
            "total_books_to_import": 0,
            "books_imported": 0,
            "import_errors": 0,
            "batches_completed": 0,
            "current_batch": 0,
            "estimated_completion": None
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"📡 Received signal {signum}, finishing current batch then shutting down...")
        self.running = False
        
    def load_scan_results(self):
        """Load the scan results with unique books to import"""
        try:
            with open(self.scan_results_file, 'r') as f:
                results = json.load(f)
            
            # Load the full unique books list
            with open("external_drive_scan_results.json", 'r') as f:
                full_results = json.load(f)
                
            # Get ALL unique books, not just the preview
            unique_books = []
            external_path = Path(full_results["external_drive_path"])
            calibre_prefixes = self.get_calibre_prefixes()
            
            # Re-scan to get complete list
            logger.info("🔍 Loading complete list of unique books...")
            external_epubs = list(external_path.rglob("*.epub"))
            external_prefixes = set()
            
            for epub_path in external_epubs:
                prefix = epub_path.stem[:15].lower()
                if prefix not in calibre_prefixes and prefix not in external_prefixes:
                    unique_books.append(str(epub_path))
                    external_prefixes.add(prefix)
            
            self.stats["total_books_to_import"] = len(unique_books)
            logger.info(f"📚 Loaded {len(unique_books):,} unique books for import")
            
            return unique_books
            
        except FileNotFoundError:
            logger.error(f"❌ Scan results file not found: {self.scan_results_file}")
            logger.error("Please run external_drive_duplicate_scanner.py first")
            return []
            
    def get_calibre_prefixes(self):
        """Get current Calibre library prefixes to avoid re-scanning"""
        calibre_path = Path(self.calibre_library_path)
        calibre_prefixes = set()
        
        calibre_epubs = list(calibre_path.rglob("*.epub"))
        for epub_path in calibre_epubs:
            prefix = epub_path.stem[:15].lower()
            calibre_prefixes.add(prefix)
            
        return calibre_prefixes
        
    def import_book_to_calibre(self, book_path):
        """Import a single book to Calibre"""
        try:
            cmd = [
                self.calibredb_path, "add",
                "--library-path", self.calibre_library_path,
                "--duplicates",  # Handle duplicates gracefully
                str(book_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, f"Imported successfully"
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            return False, error_msg
        except Exception as e:
            return False, str(e)
            
    def import_batch(self, batch_books, batch_num):
        """Import a batch of books"""
        logger.info(f"📦 Processing batch {batch_num} ({len(batch_books)} books)")
        
        successful = 0
        failed = 0
        
        for i, book_path in enumerate(batch_books, 1):
            if not self.running:
                logger.info("⏹️  Batch interrupted by shutdown signal")
                break
                
            book_name = Path(book_path).stem
            logger.info(f"📖 [{batch_num}.{i:02d}] Importing: {book_name[:60]}...")
            
            success, message = self.import_book_to_calibre(book_path)
            
            if success:
                successful += 1
                self.stats["books_imported"] += 1
                logger.info(f"✅ Imported successfully")
            else:
                failed += 1
                self.stats["import_errors"] += 1
                logger.warning(f"❌ Import failed: {message}")
                
        self.stats["batches_completed"] += 1
        self.stats["current_batch"] = batch_num
        
        success_rate = (successful / len(batch_books)) * 100 if batch_books else 0
        logger.info(f"📊 Batch {batch_num} completed: {successful}/{len(batch_books)} successful ({success_rate:.1f}%)")
        
        return successful, failed
        
    def save_progress(self):
        """Save current import progress"""
        runtime = datetime.now() - self.stats["import_start_time"]
        
        progress_data = {
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats.copy(),
            "runtime_minutes": runtime.total_seconds() / 60
        }
        
        # Convert datetime for JSON serialization
        for key, value in progress_data["stats"].items():
            if isinstance(value, datetime):
                progress_data["stats"][key] = value.isoformat()
        
        with open("calibre_batch_import_progress.json", "w") as f:
            json.dump(progress_data, f, indent=2)
            
    def print_status(self):
        """Print current import status"""
        runtime = datetime.now() - self.stats["import_start_time"]
        
        logger.info("=" * 70)
        logger.info("📊 CALIBRE BATCH IMPORT STATUS")
        logger.info("=" * 70)
        logger.info(f"📚 Total books to import: {self.stats['total_books_to_import']:,}")
        logger.info(f"✅ Books imported: {self.stats['books_imported']:,}")
        logger.info(f"❌ Import errors: {self.stats['import_errors']:,}")
        logger.info(f"📦 Batches completed: {self.stats['batches_completed']}")
        logger.info(f"⏱️  Runtime: {runtime}")
        
        if self.stats['total_books_to_import'] > 0:
            completion_rate = (self.stats['books_imported'] / self.stats['total_books_to_import']) * 100
            logger.info(f"📈 Progress: {completion_rate:.1f}%")
            
            # Estimate remaining time
            if self.stats['books_imported'] > 0:
                books_per_minute = self.stats['books_imported'] / (runtime.total_seconds() / 60)
                remaining_books = self.stats['total_books_to_import'] - self.stats['books_imported']
                eta_minutes = remaining_books / books_per_minute if books_per_minute > 0 else 0
                logger.info(f"⚡ Import speed: {books_per_minute:.1f} books/minute")
                logger.info(f"🕐 Estimated completion: {eta_minutes:.0f} minutes")
        
        logger.info("=" * 70)
        
    def run(self):
        """Main import process"""
        logger.info("🚀 Starting Calibre Batch Import")
        logger.info(f"📍 Calibre Library: {self.calibre_library_path}")
        logger.info(f"📦 Batch Size: {self.batch_size}")
        logger.info(f"⏱️  Batch Delay: {self.batch_delay} seconds")
        
        # Load books to import
        unique_books = self.load_scan_results()
        if not unique_books:
            logger.error("❌ No books to import, exiting")
            return
            
        logger.info(f"🎯 Starting import of {len(unique_books):,} unique books...")
        
        try:
            # Process in batches
            total_batches = (len(unique_books) + self.batch_size - 1) // self.batch_size
            
            for batch_num in range(1, total_batches + 1):
                if not self.running:
                    break
                    
                start_idx = (batch_num - 1) * self.batch_size
                end_idx = min(start_idx + self.batch_size, len(unique_books))
                batch = unique_books[start_idx:end_idx]
                
                logger.info(f"📦 Starting batch {batch_num}/{total_batches} (Books {start_idx + 1}-{end_idx})")
                
                successful, failed = self.import_batch(batch, batch_num)
                
                # Save progress
                self.save_progress()
                
                # Print status every 10 batches
                if batch_num % 10 == 0:
                    self.print_status()
                    
                # Sleep between batches (unless it's the last batch)
                if batch_num < total_batches and self.running:
                    logger.info(f"😴 Resting for {self.batch_delay} seconds...")
                    time.sleep(self.batch_delay)
            
            # Final status
            self.print_status()
            logger.info("🎉 Calibre Batch Import completed successfully!")
            logger.info(f"📚 Total imported: {self.stats['books_imported']:,} books")
            logger.info(f"🔗 Ready for daemon linkage creation!")
            
        except KeyboardInterrupt:
            logger.info("⚠️ Import interrupted by user")
        except Exception as e:
            logger.error(f"❌ Import error: {e}")
        finally:
            self.save_progress()
            logger.info("💾 Progress saved, importer shutting down")

if __name__ == "__main__":
    importer = BatchCalibreImporter()
    importer.run()