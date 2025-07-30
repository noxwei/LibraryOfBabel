#!/usr/bin/env python3
"""
Phonetic Processing Daemon - Dr. Rodriguez & Dr. Chen
====================================================

Background daemon to process phonetic columns without blocking other work.
Runs safely in background with progress tracking and resume capability.
"""

import psycopg2
import psycopg2.extras
import time
import os
import signal
import json
import sys
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/phonetic_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'knowledge_base', 
    'user': 'weixiangzhang',
    'port': 5432
}

# Progress tracking file
PROGRESS_FILE = '/tmp/phonetic_processing_progress.json'
PID_FILE = '/tmp/phonetic_daemon.pid'

class PhoneticDaemon:
    """Background phonetic processing daemon"""
    
    def __init__(self):
        self.running = True
        self.conn = None
        self.progress = self.load_progress()
        self.start_time = time.time()
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
    
    def load_progress(self):
        """Load previous progress if exists"""
        try:
            if os.path.exists(PROGRESS_FILE):
                with open(PROGRESS_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        
        return {
            'processed': 0,
            'total': 0,
            'current_batch': 0,
            'started_at': None,
            'last_updated': None,
            'status': 'not_started'
        }
    
    def save_progress(self):
        """Save current progress"""
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
    
    def connect_db(self):
        """Connect to database with retry logic"""
        for attempt in range(3):
            try:
                self.conn = psycopg2.connect(**DB_CONFIG)
                logger.info("✅ Database connected")
                return True
            except Exception as e:
                logger.warning(f"DB connection attempt {attempt+1} failed: {e}")
                if attempt < 2:
                    time.sleep(5)
        
        logger.error("❌ Could not connect to database")
        return False
    
    def setup_phonetic_infrastructure(self):
        """Set up phonetic columns and extensions if needed"""
        try:
            with self.conn.cursor() as cur:
                # Install fuzzystrmatch if needed
                cur.execute("CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;")
                
                # Add phonetic columns if needed
                cur.execute("""
                    ALTER TABLE chunks 
                    ADD COLUMN IF NOT EXISTS content_soundex TEXT,
                    ADD COLUMN IF NOT EXISTS content_metaphone TEXT,
                    ADD COLUMN IF NOT EXISTS content_audiobook_normalized TEXT;
                """)
                
                self.conn.commit()
                logger.info("✅ Phonetic infrastructure ready")
                return True
                
        except Exception as e:
            logger.error(f"❌ Infrastructure setup failed: {e}")
            return False
    
    def get_total_work(self):
        """Get total chunks that need processing"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM chunks 
                    WHERE content_soundex IS NULL 
                       OR content_metaphone IS NULL 
                       OR content_audiobook_normalized IS NULL
                """)
                total = cur.fetchone()[0]
                self.progress['total'] = total
                return total
        except Exception as e:
            logger.error(f"Could not get total work: {e}")
            return 0
    
    def process_batch(self, batch_size=500):
        """Process a batch of chunks"""
        try:
            with self.conn.cursor() as cur:
                # Get batch to process
                cur.execute("""
                    SELECT chunk_id, content 
                    FROM chunks 
                    WHERE content_soundex IS NULL 
                       OR content_metaphone IS NULL
                       OR content_audiobook_normalized IS NULL
                    LIMIT %s
                """, (batch_size,))
                
                batch = cur.fetchall()
                if not batch:
                    return 0  # No more work
                
                processed_count = 0
                
                for chunk_id, content in batch:
                    if not self.running:
                        break
                    
                    if content:
                        # Process content for phonetic matching
                        text_sample = content[:1000]  # First 1000 chars
                        
                        # Normalize for audiobook search
                        normalized = self.normalize_for_audiobook(text_sample)
                        
                        # Generate phonetic codes for first 30 words
                        words = text_sample.split()[:30]
                        soundex_codes = []
                        metaphone_codes = []
                        
                        for word in words:
                            clean_word = ''.join(c for c in word if c.isalpha())
                            if len(clean_word) >= 3:
                                try:
                                    # Soundex
                                    cur.execute("SELECT soundex(%s);", (clean_word,))
                                    soundex_result = cur.fetchone()
                                    if soundex_result and soundex_result[0]:
                                        soundex_codes.append(soundex_result[0])
                                    
                                    # Metaphone
                                    cur.execute("SELECT metaphone(%s, 4);", (clean_word,))
                                    metaphone_result = cur.fetchone()
                                    if metaphone_result and metaphone_result[0]:
                                        metaphone_codes.append(metaphone_result[0])
                                except:
                                    continue
                        
                        # Update chunk
                        cur.execute("""
                            UPDATE chunks 
                            SET content_soundex = %s,
                                content_metaphone = %s,
                                content_audiobook_normalized = %s
                            WHERE chunk_id = %s
                        """, (
                            ' '.join(soundex_codes)[:500],
                            ' '.join(metaphone_codes)[:500],
                            normalized[:500],
                            chunk_id
                        ))
                        
                        processed_count += 1
                
                self.conn.commit()
                return processed_count
                
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            return 0
    
    def normalize_for_audiobook(self, text):
        """Normalize text for audiobook search"""
        import re
        
        if not text:
            return ""
        
        # Convert to lowercase
        normalized = text.lower()
        
        # Common audiobook homophones
        replacements = {
            r'\btheir\b': 'there',
            r'\bthere\b': 'their',
            r'\byour\b': 'youre',
            r'\byoure\b': 'your',
            r'\bits\b': 'its',
            r'\bthan\b': 'then',
            r'\bthen\b': 'than',
        }
        
        for pattern, replacement in replacements.items():
            normalized = re.sub(pattern, replacement, normalized)
        
        # Remove punctuation
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def print_status(self):
        """Print current status"""
        if self.progress['total'] > 0:
            percent = (self.progress['processed'] / self.progress['total']) * 100
            elapsed = time.time() - self.start_time
            
            if self.progress['processed'] > 0:
                rate = self.progress['processed'] / elapsed
                eta_seconds = (self.progress['total'] - self.progress['processed']) / rate
                eta_minutes = eta_seconds / 60
                
                logger.info(f"📊 Progress: {self.progress['processed']:,}/{self.progress['total']:,} "
                          f"({percent:.1f}%) - ETA: {eta_minutes:.1f} minutes")
            else:
                logger.info(f"📊 Progress: {self.progress['processed']:,}/{self.progress['total']:,} ({percent:.1f}%)")
    
    def run(self):
        """Main daemon loop"""
        logger.info("🚀 Phonetic Processing Daemon - Dr. Rodriguez & Dr. Chen")
        logger.info("=" * 60)
        
        if not self.create_pid_file():
            return False
        
        try:
            # Connect to database
            if not self.connect_db():
                return False
            
            # Setup infrastructure
            if not self.setup_phonetic_infrastructure():
                return False
            
            # Get total work
            total = self.get_total_work()
            if total == 0:
                logger.info("✅ No phonetic processing needed - all chunks already processed!")
                return True
            
            logger.info(f"📋 Processing {total:,} chunks in background...")
            logger.info(f"💾 Storage increase: ~{total/1000:.0f}MB (very reasonable)")
            
            self.progress['started_at'] = datetime.now().isoformat()
            self.progress['status'] = 'running'
            
            batch_count = 0
            last_status_time = time.time()
            
            while self.running and self.progress['processed'] < total:
                # Process batch
                processed = self.process_batch(batch_size=500)
                
                if processed == 0:
                    logger.info("✅ All chunks processed!")
                    break
                
                self.progress['processed'] += processed
                batch_count += 1
                
                # Save progress every 5 batches
                if batch_count % 5 == 0:
                    self.save_progress()
                
                # Print status every 2 minutes
                if time.time() - last_status_time > 120:
                    self.print_status()
                    last_status_time = time.time()
                
                # Small delay to not overwhelm system
                time.sleep(0.1)
            
            if self.running:
                self.progress['status'] = 'completed'
                logger.info("🎉 PHONETIC PROCESSING COMPLETE!")
                logger.info(f"✅ Processed {self.progress['processed']:,} chunks")
                logger.info("🎧 Audiobook search enhanced with phonetic matching!")
            else:
                self.progress['status'] = 'interrupted'
                logger.info("⏸️ Processing interrupted - progress saved")
            
            self.save_progress()
            return True
            
        except Exception as e:
            logger.error(f"❌ Daemon error: {e}")
            return False
        
        finally:
            self.remove_pid_file()
            if self.conn:
                self.conn.close()
    
    def shutdown(self, signum, frame):
        """Graceful shutdown handler"""
        logger.info(f"📥 Received signal {signum} - shutting down gracefully...")
        self.running = False

def check_daemon_status():
    """Check if daemon is running and show progress"""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process is actually running
            try:
                os.kill(pid, 0)  # Doesn't kill, just checks if process exists
                print(f"✅ Phonetic daemon running (PID: {pid})")
                
                # Show progress if available
                if os.path.exists(PROGRESS_FILE):
                    with open(PROGRESS_FILE, 'r') as f:
                        progress = json.load(f)
                    
                    if progress['total'] > 0:
                        percent = (progress['processed'] / progress['total']) * 100
                        print(f"📊 Progress: {progress['processed']:,}/{progress['total']:,} ({percent:.1f}%)")
                        print(f"📝 Status: {progress['status']}")
                        print(f"⏱️ Last updated: {progress.get('last_updated', 'Unknown')}")
                
                return True
                
            except OSError:
                print("❌ Daemon PID file exists but process not running")
                os.remove(PID_FILE)
                return False
                
        except Exception as e:
            print(f"❌ Error checking daemon: {e}")
            return False
    else:
        print("📴 Phonetic daemon not running")
        return False

def stop_daemon():
    """Stop the running daemon"""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            
            os.kill(pid, signal.SIGTERM)
            print(f"🛑 Sent stop signal to daemon (PID: {pid})")
            
            # Wait a moment and check if it stopped
            time.sleep(2)
            if not check_daemon_status():
                print("✅ Daemon stopped successfully")
            else:
                print("⚠️ Daemon may still be running")
                
        except Exception as e:
            print(f"❌ Error stopping daemon: {e}")
    else:
        print("📴 No daemon running to stop")

def main():
    """Main function with command line options"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'status':
            check_daemon_status()
        elif command == 'stop':
            stop_daemon()
        elif command == 'start':
            if check_daemon_status():
                print("⚠️ Daemon already running")
            else:
                daemon = PhoneticDaemon()
                daemon.run()
        else:
            print("Usage: python3 phonetic_daemon.py [start|stop|status]")
    else:
        # Default: start daemon
        if check_daemon_status():
            print("⚠️ Daemon already running")
        else:
            daemon = PhoneticDaemon()
            daemon.run()

if __name__ == "__main__":
    main()