#!/usr/bin/env python3
"""
Missing Chunks Processing Daemon
===============================

Dr. Sarah Chen (陈雪芳) PostgreSQL-First Architecture
Continuously processes books that are missing chunks until all are complete.

Features:
- Runs continuously until all books have chunks
- Processes books in batches to prevent database overload
- Automatic restart and error recovery
- Complete logging and progress tracking
- PostgreSQL-First approach with no hardcoded SQL
"""

import os
import sys
import time
import signal
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append('/Users/weixiangzhang/Local_Dev/LibraryOfBabel/scripts')
from process_missing_chunks import MissingChunkProcessor

class MissingChunksDaemon:
    """Daemon for continuous missing chunks processing"""
    
    def __init__(self):
        self.processor = None
        self.running = True
        self.daemon_name = "missing_chunks_daemon"
        self.batch_size = 25  # Process 25 books at a time
        
        # Setup logging
        log_file = f'/Users/weixiangzhang/Local_Dev/LibraryOfBabel/logs/{self.daemon_name}.log'
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.daemon_name)
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        
    def count_books_without_chunks(self) -> int:
        """Count books that still need chunks"""
        try:
            if not self.processor:
                self.processor = MissingChunkProcessor()
            
            books = self.processor.get_books_without_chunks()
            return len(books)
            
        except Exception as e:
            self.logger.error(f"Error counting books without chunks: {e}")
            return 0
    
    def run_processing_batch(self) -> dict:
        """Run one batch of chunk processing"""
        try:
            if not self.processor:
                self.processor = MissingChunkProcessor()
            
            # Get books without chunks
            books = self.processor.get_books_without_chunks()
            
            if not books:
                return {'success': True, 'books_processed': 0, 'message': 'No books need processing'}
            
            # Process batch
            batch_books = books[:self.batch_size]
            initial_stats = dict(self.processor.stats)
            
            self.logger.info(f"📦 Processing batch of {len(batch_books)} books...")
            
            for i, book in enumerate(batch_books, 1):
                book_title = book['title'][:30] + "..." if len(book['title']) > 30 else book['title']
                self.logger.info(f"📖 [{i}/{len(batch_books)}] Processing: {book_title}")
                
                if self.processor.generate_chunks_for_book(book):
                    self.processor.stats['books_processed'] += 1
                
                # Small delay to prevent database overload
                time.sleep(0.1)
            
            # Calculate batch statistics
            books_processed = self.processor.stats['books_processed'] - initial_stats['books_processed']
            chunks_created = self.processor.stats['chunks_created'] - initial_stats['chunks_created']
            
            return {
                'success': True, 
                'books_processed': books_processed,
                'chunks_created': chunks_created,
                'message': f'Processed {books_processed} books, created {chunks_created} chunks'
            }
            
        except Exception as e:
            self.logger.error(f"Batch processing error: {e}")
            return {'success': False, 'error': str(e)}
    
    def run(self):
        """Main daemon loop"""
        self.logger.info(f"🚀 Starting {self.daemon_name}")
        self.logger.info(f"🏛️  Architecture: Dr. Sarah Chen PostgreSQL-First")
        self.logger.info(f"📦 Batch Size: {self.batch_size} books per cycle")
        
        total_processed = 0
        total_chunks_created = 0
        error_count = 0
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                remaining_books = self.count_books_without_chunks()
                
                if remaining_books == 0:
                    self.logger.info("🎉 SUCCESS: All books now have chunks!")
                    self.logger.info(f"📊 Total processed by daemon: {total_processed} books")
                    self.logger.info(f"📄 Total chunks created: {total_chunks_created}")
                    break
                
                self.logger.info(f"🔄 Cycle {cycle_count}: {remaining_books} books remaining")
                
                # Run processing batch
                result = self.run_processing_batch()
                
                if result['success']:
                    books_processed = result['books_processed']
                    chunks_created = result.get('chunks_created', 0)
                    
                    total_processed += books_processed
                    total_chunks_created += chunks_created
                    error_count = 0  # Reset error count on success
                    
                    self.logger.info(f"✅ Batch complete: {result['message']}")
                    self.logger.info(f"📈 Daemon totals: {total_processed} books, {total_chunks_created} chunks")
                    
                    if books_processed == 0:
                        # No new books processed, wait longer
                        self.logger.info("⏳ No processable books in batch, waiting 30 seconds...")
                        time.sleep(30)
                    else:
                        # Brief pause between successful batches
                        self.logger.info("⏸️  Pausing 10 seconds before next batch...")
                        time.sleep(10)
                        
                else:
                    error_count += 1
                    self.logger.error(f"❌ Batch failed: {result.get('error', 'Unknown error')}")
                    
                    if error_count >= 5:
                        self.logger.error("💥 Too many consecutive errors, stopping daemon")
                        break
                    
                    # Wait before retrying
                    wait_time = min(60, 10 * error_count)  # Exponential backoff, max 60s
                    self.logger.info(f"⏳ Retrying in {wait_time} seconds... (attempt {error_count}/5)")
                    time.sleep(wait_time)
                    
            except KeyboardInterrupt:
                self.logger.info("⌨️  Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                self.logger.error(f"💥 Unexpected error in daemon loop: {e}")
                time.sleep(30)
        
        # Final statistics
        self.logger.info("=" * 60)
        self.logger.info(f"🎯 {self.daemon_name.upper()} FINAL REPORT")
        self.logger.info("=" * 60)
        self.logger.info(f"🔄 Total Cycles: {cycle_count}")
        self.logger.info(f"📚 Books Processed: {total_processed}")
        self.logger.info(f"📄 Chunks Created: {total_chunks_created}")
        self.logger.info(f"❌ Final Error Count: {error_count}")
        
        remaining = self.count_books_without_chunks()
        if remaining == 0:
            self.logger.info("🎉 STATUS: ALL BOOKS NOW HAVE CHUNKS - MISSION ACCOMPLISHED!")
        else:
            self.logger.info(f"⚠️  STATUS: {remaining} books still need processing")
        
        self.logger.info("🏛️  Dr. Sarah Chen PostgreSQL-First Architecture Maintained")
        self.logger.info("=" * 60)

def main():
    """Main entry point"""
    daemon = MissingChunksDaemon()
    
    # Create PID file
    pid_file = f'/Users/weixiangzhang/Local_Dev/LibraryOfBabel/pids/{daemon.daemon_name}.pid'
    os.makedirs(os.path.dirname(pid_file), exist_ok=True)
    
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    
    print(f"🚀 Starting Missing Chunks Processing Daemon (PID: {os.getpid()})")
    print(f"📝 Logs: /Users/weixiangzhang/Local_Dev/LibraryOfBabel/logs/missing_chunks_daemon.log")
    print(f"🛑 Stop with: kill {os.getpid()}")
    
    try:
        daemon.run()
    finally:
        # Clean up PID file
        try:
            os.remove(pid_file)
        except OSError:
            pass

if __name__ == "__main__":
    main()