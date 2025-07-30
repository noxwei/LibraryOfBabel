#!/usr/bin/env python3
"""
Calibre Migration Daemon
========================

Runs continuous Calibre migration until all books are processed.
Includes monitoring, progress tracking, and automatic restart capabilities.
"""

import psycopg2
import subprocess
from pathlib import Path
import logging
import time
import json
import os
import signal
import sys
from datetime import datetime
import argparse

# Setup daemon logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - CALIBRE_DAEMON - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('calibre_migration_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CalibreMigrationDaemon:
    def __init__(self, batch_size=100, max_consecutive_failures=5):
        self.batch_size = batch_size
        self.max_consecutive_failures = max_consecutive_failures
        self.running = True
        self.total_processed = 0
        self.total_successful = 0
        self.total_failed = 0
        self.consecutive_failures = 0
        self.start_time = datetime.now()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("🤖 Calibre Migration Daemon initialized")
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"📡 Received signal {signum}, shutting down gracefully...")
        self.running = False
        
    def get_total_books_to_process(self):
        """Get total number of EPUB files to process"""
        epub_files = list(Path("ebooks/processed").glob("*.epub"))
        return len(epub_files)
        
    def get_enhanced_books_count(self):
        """Get count of already enhanced books"""
        try:
            conn = psycopg2.connect(host='localhost', database='knowledge_base', user='weixiangzhang')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM books WHERE metadata->>'metadata_source' = 'calibre_enhanced'")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"❌ Failed to get enhanced books count: {e}")
            return 0
            
    def calculate_progress(self):
        """Calculate overall progress"""
        total_books = self.get_total_books_to_process()
        enhanced_books = self.get_enhanced_books_count()
        
        if total_books == 0:
            return 100.0
            
        progress_percent = (enhanced_books / total_books) * 100
        return progress_percent, enhanced_books, total_books
        
    def run_migration_batch(self):
        """Run a single migration batch"""
        try:
            logger.info(f"🚀 Starting migration batch (size: {self.batch_size})")
            
            # Get current progress to determine start position
            _, enhanced_count, total_count = self.calculate_progress()
            
            if enhanced_count >= total_count:
                logger.info("🎉 All books have been processed!")
                return True, "completed"
                
            # Run the production migrator
            cmd = [
                'python3', 'production_calibre_migrator.py',
                '--batch-size', str(self.batch_size),
                '--max-books', str(self.batch_size),
                '--start-from', str(enhanced_count)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                # Parse the output for success/failure counts
                output = result.stdout
                
                # Look for final stats in output
                success_rate = 0
                batch_successful = 0
                batch_failed = 0
                
                for line in output.split('\n'):
                    if 'successful' in line and '/' in line:
                        try:
                            # Extract numbers like "178/200 successful"
                            parts = line.split()
                            for part in parts:
                                if '/' in part and 'successful' in line:
                                    successful, total = part.split('/')
                                    batch_successful = int(successful)
                                    batch_failed = int(total) - int(successful)
                                    success_rate = (int(successful) / int(total)) * 100
                                    break
                        except:
                            pass
                            
                self.total_processed += (batch_successful + batch_failed)
                self.total_successful += batch_successful
                self.total_failed += batch_failed
                self.consecutive_failures = 0
                
                logger.info(f"✅ Batch completed: {batch_successful}/{batch_successful + batch_failed} successful ({success_rate:.1f}%)")
                logger.info(f"📊 Overall: {self.total_successful}/{self.total_processed} successful")
                
                return True, "success"
                
            else:
                logger.error(f"❌ Migration batch failed: {result.stderr}")
                self.consecutive_failures += 1
                return False, "failed"
                
        except subprocess.TimeoutExpired:
            logger.error("⏰ Migration batch timed out (10 minutes)")
            self.consecutive_failures += 1
            return False, "timeout"
        except Exception as e:
            logger.error(f"❌ Migration batch error: {e}")
            self.consecutive_failures += 1
            return False, "error"
            
    def log_progress(self):
        """Log current progress and statistics"""
        progress_percent, enhanced_count, total_count = self.calculate_progress()
        remaining = total_count - enhanced_count
        
        runtime = datetime.now() - self.start_time
        runtime_hours = runtime.total_seconds() / 3600
        
        if runtime_hours > 0 and self.total_processed > 0:
            books_per_hour = self.total_processed / runtime_hours
            estimated_remaining_hours = remaining / books_per_hour if books_per_hour > 0 else 0
        else:
            books_per_hour = 0
            estimated_remaining_hours = 0
            
        logger.info(f"📈 Progress: {enhanced_count}/{total_count} books ({progress_percent:.1f}%)")
        logger.info(f"⏱️  Runtime: {runtime}")
        logger.info(f"⚡ Processing rate: {books_per_hour:.1f} books/hour")
        logger.info(f"🔮 Estimated remaining: {estimated_remaining_hours:.1f} hours")
        
        # Save progress to file
        progress_data = {
            "timestamp": datetime.now().isoformat(),
            "enhanced_books": enhanced_count,
            "total_books": total_count,
            "progress_percent": progress_percent,
            "books_processed_this_session": self.total_processed,
            "successful_this_session": self.total_successful,
            "failed_this_session": self.total_failed,
            "books_per_hour": books_per_hour,
            "estimated_remaining_hours": estimated_remaining_hours,
            "runtime_hours": runtime_hours
        }
        
        with open('daemon_progress.json', 'w') as f:
            json.dump(progress_data, f, indent=2)
            
    def run(self):
        """Main daemon loop"""
        logger.info("🤖 Starting Calibre Migration Daemon")
        logger.info(f"📋 Batch size: {self.batch_size}")
        logger.info(f"⚠️  Max consecutive failures: {self.max_consecutive_failures}")
        
        # Initial progress check
        self.log_progress()
        
        while self.running:
            try:
                # Check if we should continue
                progress_percent, enhanced_count, total_count = self.calculate_progress()
                
                if enhanced_count >= total_count:
                    logger.info("🎉 All books have been processed! Daemon shutting down.")
                    break
                    
                # Check consecutive failures
                if self.consecutive_failures >= self.max_consecutive_failures:
                    logger.error(f"💥 Too many consecutive failures ({self.consecutive_failures}). Stopping daemon.")
                    break
                    
                # Run migration batch
                success, status = self.run_migration_batch()
                
                # Log progress after each batch
                self.log_progress()
                
                if status == "completed":
                    logger.info("🏁 Migration completed successfully!")
                    break
                    
                # Wait a bit between batches to avoid overwhelming the system
                if self.running:
                    logger.info("💤 Waiting 10 seconds before next batch...")
                    time.sleep(10)
                    
            except KeyboardInterrupt:
                logger.info("⌨️  Keyboard interrupt received, shutting down...")
                break
            except Exception as e:
                logger.error(f"❌ Daemon error: {e}")
                self.consecutive_failures += 1
                time.sleep(30)  # Wait longer after errors
                
        # Final statistics
        runtime = datetime.now() - self.start_time
        logger.info("📊 Final Daemon Statistics:")
        logger.info(f"   • Total runtime: {runtime}")
        logger.info(f"   • Books processed this session: {self.total_processed}")
        logger.info(f"   • Successful: {self.total_successful}")
        logger.info(f"   • Failed: {self.total_failed}")
        
        # Final progress
        self.log_progress()
        logger.info("🤖 Calibre Migration Daemon shutdown complete")
        
def main():
    parser = argparse.ArgumentParser(description='Calibre Migration Daemon')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for migration')
    parser.add_argument('--max-failures', type=int, default=5, help='Max consecutive failures before stopping')
    
    args = parser.parse_args()
    
    daemon = CalibreMigrationDaemon(
        batch_size=args.batch_size,
        max_consecutive_failures=args.max_failures
    )
    
    try:
        daemon.run()
    except Exception as e:
        logger.error(f"💥 Daemon crashed: {e}")
        sys.exit(1)
        
if __name__ == "__main__":
    main() 