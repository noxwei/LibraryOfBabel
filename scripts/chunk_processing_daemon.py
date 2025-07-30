#!/usr/bin/env python3
"""
Chunk Processing Daemon - Dr. Sarah Chen (陈雪芳) PostgreSQL-First Architecture
===============================================================================

Background daemon to safely process books without chunks using the established
read-only/admin connection security architecture. Processes the remaining 117
books without chunks from the LibraryOfBabel system health check.

Features:
- Read-only connections for querying which books need processing
- Admin connections only for actual chunk creation/insertion
- Resumable processing with progress tracking
- Proper error handling and logging
- Batch processing with configurable batch sizes
- Signal handling for graceful shutdown
"""

import os
import sys
import time
import signal
import json
import logging
from datetime import datetime
from contextlib import contextmanager

# Add src to path to import our database module
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from api.modules.database import (
    get_readonly_db, 
    get_admin_db, 
    execute_pg_function,
    ConnectionType
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/chunk_processing_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
PROGRESS_FILE = '/tmp/chunk_processing_progress.json'
PID_FILE = '/tmp/chunk_processing_daemon.pid'
DEFAULT_BATCH_SIZE = 5  # Process 5 books at a time to avoid overwhelming the system
DELAY_BETWEEN_BATCHES = 2  # Seconds between batches


class ChunkProcessingDaemon:
    """
    Background daemon for processing books without chunks
    Implements Dr. Chen's PostgreSQL-First architecture with proper security
    """
    
    def __init__(self, batch_size=DEFAULT_BATCH_SIZE):
        self.running = True
        self.batch_size = batch_size
        self.progress = self.load_progress()
        self.start_time = time.time()
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
        
        logger.info("Chunk Processing Daemon initialized")
        logger.info(f"Batch size: {batch_size}")
    
    def load_progress(self):
        """Load previous progress if exists"""
        try:
            if os.path.exists(PROGRESS_FILE):
                with open(PROGRESS_FILE, 'r') as f:
                    progress = json.load(f)
                    logger.info(f"Loaded existing progress: {progress['processed']}/{progress['total']} books processed")
                    return progress
        except Exception as e:
            logger.warning(f"Could not load progress file: {e}")
        
        return {
            'processed': 0,
            'total': 0,
            'current_batch': 0,
            'started_at': None,
            'last_updated': None,
            'status': 'not_started',
            'processed_books': [],  # Keep track of processed book_ids
            'failed_books': [],     # Keep track of failed book_ids
            'errors': []
        }
    
    def save_progress(self):
        """Save current progress to file"""
        self.progress['last_updated'] = datetime.now().isoformat()
        try:
            with open(PROGRESS_FILE, 'w') as f:
                json.dump(self.progress, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save progress: {e}")
    
    def create_pid_file(self):
        """Create PID file for daemon management"""
        try:
            with open(PID_FILE, 'w') as f:
                f.write(str(os.getpid()))
            logger.info(f"Daemon started with PID {os.getpid()}")
            return True
        except Exception as e:
            logger.error(f"Could not create PID file: {e}")
            return False
    
    def remove_pid_file(self):
        """Remove PID file on shutdown"""
        try:
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
        except:
            pass
    
    def shutdown(self, signum, frame):
        """Graceful shutdown handler"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        self.save_progress()
        self.remove_pid_file()
    
    def get_books_without_chunks(self):
        """
        Query books that don't have chunks using read-only connection
        Returns list of (book_id, title) tuples
        """
        try:
            with get_readonly_db() as conn:
                with conn.cursor() as cur:
                    # Query books that have content but no chunks
                    # This uses the existing book_contents table and checks chunk_count
                    query = """
                    SELECT DISTINCT b.book_id, b.title
                    FROM books b
                    INNER JOIN book_contents bc ON b.book_id = bc.book_id
                    WHERE (b.chunk_count IS NULL OR b.chunk_count = 0)
                    AND b.book_id NOT IN %s
                    ORDER BY b.book_id
                    LIMIT %s
                    """
                    
                    # Exclude already processed books
                    processed_books = tuple(self.progress.get('processed_books', []))
                    if not processed_books:
                        processed_books = (0,)  # Dummy value to avoid SQL syntax error
                    
                    cur.execute(query, (processed_books, self.batch_size * 10))  # Get more than batch size for buffer
                    results = cur.fetchall()
                    
                    logger.info(f"Found {len(results)} books without chunks (excluding {len(self.progress.get('processed_books', []))} already processed)")
                    return results
                    
        except Exception as e:
            logger.error(f"Error querying books without chunks: {e}")
            raise
    
    def get_book_content(self, book_id):
        """
        Get book content for processing using read-only connection
        Returns (title, content) tuple or None if not found
        """
        try:
            with get_readonly_db() as conn:
                with conn.cursor() as cur:
                    query = """
                    SELECT b.title, bc.content
                    FROM books b
                    INNER JOIN book_contents bc ON b.book_id = bc.book_id
                    WHERE b.book_id = %s
                    """
                    cur.execute(query, (book_id,))
                    result = cur.fetchone()
                    
                    if result:
                        title, content = result
                        logger.debug(f"Retrieved content for book {book_id}: '{title}' ({len(content)} characters)")
                        return title, content
                    else:
                        logger.warning(f"No content found for book_id {book_id}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error retrieving content for book {book_id}: {e}")
            raise
    
    def process_book_chunks(self, book_id, title, content):
        """
        Process book content into chunks using admin connection
        Uses the existing api_process_book_content PostgreSQL function
        Returns number of chunks created
        """
        try:
            with get_admin_db() as conn:
                with conn.cursor() as cur:
                    # Use the existing PostgreSQL function for chunk processing
                    cur.execute(
                        "SELECT api_process_book_content(%s, %s, %s)",
                        (book_id, title, content)
                    )
                    chunks_created = cur.fetchone()[0]
                    
                    if chunks_created > 0:
                        logger.info(f"Successfully created {chunks_created} chunks for book {book_id}: '{title}'")
                    else:
                        logger.warning(f"No chunks created for book {book_id}: '{title}' - content may be too short")
                    
                    return chunks_created
                    
        except Exception as e:
            logger.error(f"Error processing chunks for book {book_id}: {e}")
            raise
    
    def process_batch(self, books_batch):
        """
        Process a batch of books
        Returns (success_count, error_count)
        """
        success_count = 0
        error_count = 0
        
        for book_id, title in books_batch:
            if not self.running:
                logger.info("Shutdown requested, stopping batch processing")
                break
                
            try:
                logger.info(f"Processing book {book_id}: '{title}'")
                
                # Get book content
                content_result = self.get_book_content(book_id)
                if not content_result:
                    logger.warning(f"Skipping book {book_id} - no content available")
                    self.progress['failed_books'].append({
                        'book_id': book_id,
                        'title': title,
                        'error': 'No content available',
                        'timestamp': datetime.now().isoformat()
                    })
                    error_count += 1
                    continue
                
                book_title, content = content_result
                
                # Validate content length
                if len(content) < 100:
                    logger.warning(f"Skipping book {book_id} - content too short ({len(content)} characters)")
                    self.progress['failed_books'].append({
                        'book_id': book_id,
                        'title': title,
                        'error': f'Content too short ({len(content)} characters)',
                        'timestamp': datetime.now().isoformat()
                    })
                    error_count += 1
                    continue
                
                # Process chunks
                chunks_created = self.process_book_chunks(book_id, book_title, content)
                
                if chunks_created > 0:
                    success_count += 1
                    self.progress['processed_books'].append({
                        'book_id': book_id,
                        'title': title,
                        'chunks_created': chunks_created,
                        'timestamp': datetime.now().isoformat()
                    })
                    logger.info(f"✓ Successfully processed book {book_id} - {chunks_created} chunks created")
                else:
                    error_count += 1
                    self.progress['failed_books'].append({
                        'book_id': book_id,
                        'title': title,
                        'error': 'No chunks created - content validation failed',
                        'timestamp': datetime.now().isoformat()
                    })
                    logger.warning(f"✗ Failed to create chunks for book {book_id}")
                
                # Brief pause between books to avoid overwhelming the database
                time.sleep(0.5)
                
            except Exception as e:
                error_count += 1
                error_msg = str(e)
                logger.error(f"✗ Error processing book {book_id}: {error_msg}")
                
                self.progress['failed_books'].append({
                    'book_id': book_id,
                    'title': title,
                    'error': error_msg,
                    'timestamp': datetime.now().isoformat()
                })
                self.progress['errors'].append({
                    'book_id': book_id,
                    'error': error_msg,
                    'timestamp': datetime.now().isoformat()
                })
        
        return success_count, error_count
    
    def run_health_check(self):
        """Run initial health check to get total count"""
        try:
            logger.info("Running initial health check...")
            
            with get_readonly_db() as conn:
                with conn.cursor() as cur:
                    # Get total books and books without chunks
                    cur.execute("""
                        SELECT 
                            COUNT(*) as total_books,
                            COUNT(*) FILTER (WHERE chunk_count IS NULL OR chunk_count = 0) as books_without_chunks
                        FROM books b
                        INNER JOIN book_contents bc ON b.book_id = bc.book_id
                    """)
                    
                    total_books_with_content, books_without_chunks = cur.fetchone()
                    
                    logger.info(f"Health check results:")
                    logger.info(f"  Total books with content: {total_books_with_content}")
                    logger.info(f"  Books without chunks: {books_without_chunks}")
                    logger.info(f"  Previously processed: {len(self.progress.get('processed_books', []))}")
                    logger.info(f"  Previously failed: {len(self.progress.get('failed_books', []))}")
                    
                    return books_without_chunks
                    
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise
    
    def run(self):
        """Main daemon loop"""
        if not self.create_pid_file():
            return False
        
        try:
            logger.info("Starting Chunk Processing Daemon")
            logger.info("Following Dr. Chen's PostgreSQL-First Architecture")
            logger.info("Using read-only connections for queries, admin connections for chunk creation")
            
            # Run initial health check
            total_without_chunks = self.run_health_check()
            
            if self.progress['status'] == 'not_started':
                self.progress['started_at'] = datetime.now().isoformat()
                self.progress['total'] = total_without_chunks
                self.progress['status'] = 'running'
            
            processed_this_session = 0
            
            while self.running:
                # Get books that need processing
                books_to_process = self.get_books_without_chunks()
                
                if not books_to_process:
                    logger.info("No more books to process!")
                    self.progress['status'] = 'completed'
                    break
                
                # Process in batches
                for i in range(0, len(books_to_process), self.batch_size):
                    if not self.running:
                        break
                        
                    batch = books_to_process[i:i + self.batch_size]
                    self.progress['current_batch'] += 1
                    
                    logger.info(f"Processing batch {self.progress['current_batch']} ({len(batch)} books)")
                    
                    success_count, error_count = self.process_batch(batch)
                    
                    self.progress['processed'] += success_count
                    processed_this_session += success_count
                    
                    logger.info(f"Batch {self.progress['current_batch']} complete: {success_count} success, {error_count} errors")
                    logger.info(f"Total progress: {self.progress['processed']}/{self.progress['total']} books processed")
                    
                    # Save progress after each batch
                    self.save_progress()
                    
                    # Delay between batches to avoid overwhelming the system
                    if self.running and i + self.batch_size < len(books_to_process):
                        logger.debug(f"Waiting {DELAY_BETWEEN_BATCHES} seconds before next batch...")
                        time.sleep(DELAY_BETWEEN_BATCHES)
            
            # Final status
            if self.progress['status'] != 'completed':
                self.progress['status'] = 'stopped'
            
            elapsed_time = time.time() - self.start_time
            logger.info(f"Session complete!")
            logger.info(f"  Books processed this session: {processed_this_session}")
            logger.info(f"  Total books processed: {len(self.progress.get('processed_books', []))}")
            logger.info(f"  Total books failed: {len(self.progress.get('failed_books', []))}")
            logger.info(f"  Session duration: {elapsed_time:.1f} seconds")
            
            self.save_progress()
            return True
            
        except Exception as e:
            logger.error(f"Daemon error: {e}")
            self.progress['status'] = 'error'
            self.progress['errors'].append({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            self.save_progress()
            return False
            
        finally:
            self.remove_pid_file()
            logger.info("Chunk Processing Daemon stopped")


def show_progress():
    """Show current progress from progress file"""
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r') as f:
                progress = json.load(f)
            
            print("\n=== Chunk Processing Daemon Progress ===")
            print(f"Status: {progress.get('status', 'unknown')}")
            print(f"Progress: {progress.get('processed', 0)}/{progress.get('total', 0)} books processed")
            print(f"Current batch: {progress.get('current_batch', 0)}")
            print(f"Started: {progress.get('started_at', 'Not started')}")
            print(f"Last updated: {progress.get('last_updated', 'Never')}")
            print(f"Successfully processed: {len(progress.get('processed_books', []))} books")
            print(f"Failed: {len(progress.get('failed_books', []))} books")
            print(f"Errors: {len(progress.get('errors', []))} errors")
            
            if progress.get('failed_books'):
                print("\nRecent failures:")
                for failure in progress['failed_books'][-5:]:  # Show last 5 failures
                    print(f"  Book {failure['book_id']}: {failure['error']}")
            
        else:
            print("No progress file found - daemon has not been run yet")
            
    except Exception as e:
        print(f"Error reading progress: {e}")


def stop_daemon():
    """Stop running daemon"""
    try:
        if os.path.exists(PID_FILE):
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"Sent shutdown signal to daemon (PID {pid})")
                
                # Wait a bit for graceful shutdown
                time.sleep(2)
                
                # Check if process is still running
                try:
                    os.kill(pid, 0)  # Test if process exists
                    print("Daemon is still running, sending SIGKILL...")
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    print("Daemon stopped successfully")
                    
            except ProcessLookupError:
                print(f"Process {pid} not found - daemon may have already stopped")
                os.remove(PID_FILE)
                
        else:
            print("No PID file found - daemon is not running")
            
    except Exception as e:
        print(f"Error stopping daemon: {e}")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python chunk_processing_daemon.py start [batch_size]  - Start daemon")
        print("  python chunk_processing_daemon.py stop               - Stop daemon")
        print("  python chunk_processing_daemon.py status             - Show progress")
        print("  python chunk_processing_daemon.py reset              - Reset progress")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'start':
        batch_size = DEFAULT_BATCH_SIZE
        if len(sys.argv) > 2:
            try:
                batch_size = int(sys.argv[2])
                if batch_size < 1 or batch_size > 20:
                    print("Batch size must be between 1 and 20")
                    sys.exit(1)
            except ValueError:
                print("Invalid batch size - must be a number")
                sys.exit(1)
        
        # Check if daemon is already running
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0)  # Test if process exists
                print(f"Daemon is already running with PID {pid}")
                sys.exit(1)
            except (ProcessLookupError, ValueError):
                # Process doesn't exist, remove stale PID file
                os.remove(PID_FILE)
        
        daemon = ChunkProcessingDaemon(batch_size)
        success = daemon.run()
        sys.exit(0 if success else 1)
        
    elif command == 'stop':
        stop_daemon()
        
    elif command == 'status':
        show_progress()
        
    elif command == 'reset':
        try:
            if os.path.exists(PROGRESS_FILE):
                os.remove(PROGRESS_FILE)
                print("Progress file reset")
            else:
                print("No progress file to reset")
        except Exception as e:
            print(f"Error resetting progress: {e}")
            
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()