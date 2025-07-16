#!/usr/bin/env python3
"""
Full Library Reclassification Daemon
====================================
Reprocess ALL 1,243 books with llama3.2:3b for maximum accuracy
Fast, comprehensive, and autonomous
"""

import sys
import json
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import re
import time
import signal
import atexit
import os
from datetime import datetime
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config.api_config import get_database_config

class FullLibraryReclassificationDaemon:
    def __init__(self):
        self.db_config = get_database_config()
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = "llama3.2:3b"  # Fast, accurate model
        
        # State file for persistence
        self.state_file = project_root / "daemons" / "full_library_state.json"
        self.log_file = project_root / "daemons" / "full_library.log"
        self.pid_file = project_root / "daemons" / "full_library.pid"
        
        # Initialize state
        self.state = {
            "processed_books": [],
            "processed_count": 0,
            "reclassified_count": 0,
            "confirmed_count": 0,
            "failed_count": 0,
            "current_batch": 0,
            "total_books": 0,
            "start_time": None,
            "last_update": None,
            "status": "initializing",
            "genre_changes": {},
            "errors": [],
            "accuracy_stats": {}
        }
        
        # Load existing state if available
        self.load_state()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Valid genres with enhanced list
        self.valid_genres = [
            "Romance", "Literary Fiction", "Science Fiction", "Fantasy",
            "Mystery & Thriller", "Historical Fiction", "Contemporary Fiction",
            "Self-Help", "Biography & Memoir", "Psychology", "Philosophy",
            "Business & Economics", "History", "Science & Nature",
            "Programming & Technology", "Data Science & Analytics",
            "Religion & Spirituality", "Political Science", "Academic & Research",
            "Health & Medicine", "True Crime", "Travel", "Art & Design"
        ]
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        atexit.register(self.cleanup)
        
        # Write PID file
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))
    
    def load_state(self):
        """Load previous state if exists"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    saved_state = json.load(f)
                    self.state.update(saved_state)
                    print(f"📂 Loaded previous state: {self.state['processed_count']} books processed")
            except Exception as e:
                print(f"⚠️  Could not load previous state: {e}")
    
    def save_state(self):
        """Save current state"""
        self.state["last_update"] = datetime.now().isoformat()
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.state["status"] = "stopping"
        self.save_state()
        sys.exit(0)
    
    def cleanup(self):
        """Cleanup on exit"""
        if self.pid_file.exists():
            self.pid_file.unlink()
        self.save_state()
    
    def get_all_books_to_process(self):
        """Get ALL books in the library for comprehensive reclassification"""
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        
        try:
            with conn.cursor() as cur:
                # Get all books not yet processed
                if self.state["processed_books"]:
                    processed_ids = tuple(self.state["processed_books"])
                    if len(processed_ids) == 1:
                        processed_condition = f"AND b.book_id != {processed_ids[0]}"
                    else:
                        processed_condition = f"AND b.book_id NOT IN {processed_ids}"
                else:
                    processed_condition = ""
                
                cur.execute(f"""
                    SELECT b.book_id, b.title, b.author, b.genre
                    FROM books b
                    WHERE EXISTS (
                        SELECT 1 FROM chunks c 
                        WHERE c.book_id = b.book_id 
                        AND c.content IS NOT NULL 
                        AND LENGTH(c.content) > 100
                    )
                    {processed_condition}
                    ORDER BY b.book_id
                """)
                
                return cur.fetchall()
        finally:
            conn.close()
    
    def get_book_content_sample(self, book_id):
        """Get representative content sample from book"""
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        
        try:
            with conn.cursor() as cur:
                # Get diverse chunks from the book
                cur.execute("""
                    WITH numbered_chunks AS (
                        SELECT content,
                               ROW_NUMBER() OVER (ORDER BY chunk_id) as rn,
                               COUNT(*) OVER () as total_chunks
                        FROM chunks
                        WHERE book_id = %s
                        AND content IS NOT NULL
                        AND LENGTH(content) > 100
                    )
                    SELECT content
                    FROM numbered_chunks
                    WHERE rn IN (1, GREATEST(total_chunks/3, 1), GREATEST(total_chunks*2/3, 1))
                    ORDER BY rn
                    LIMIT 3
                """, (book_id,))
                
                chunks = cur.fetchall()
                
                # Create sample
                if chunks:
                    sample = " ... ".join([
                        re.sub(r'<[^>]+>|\\s+', ' ', chunk['content']).strip()[:200]
                        for chunk in chunks
                    ])
                    return sample[:600]  # Reasonable size for classification
                return ""
        finally:
            conn.close()
    
    def classify_with_llama(self, book_data, content):
        """Fast classification with llama3.2:3b"""
        
        prompt = f"""Classify this book by genre based on actual content analysis.

BOOK: "{book_data['title']}" by {book_data['author']}
CONTENT SAMPLE: {content}

AVAILABLE GENRES:
Romance, Literary Fiction, Science Fiction, Fantasy, Mystery & Thriller, Historical Fiction, Contemporary Fiction, Self-Help, Biography & Memoir, Psychology, Philosophy, Business & Economics, History, Science & Nature, Programming & Technology, Academic & Research

INSTRUCTIONS:
- Analyze the ACTUAL CONTENT, not just the title
- Fiction = characters, dialogue, narrative plot
- Non-fiction = facts, analysis, instruction, theory
- Choose the most specific and accurate genre

GENRE:"""

        try:
            start_time = time.time()
            
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1}
                },
                timeout=20  # Fast model
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                classification = result['response'].strip()
                
                # Extract clean genre
                for genre in self.valid_genres:
                    if genre.lower() in classification.lower():
                        return genre, duration
                
                # Fallback - return raw classification for manual review
                return classification, duration
            else:
                return None, duration
                
        except Exception as e:
            self.logger.error(f"Classification error: {e}")
            return None, 20
    
    def update_book_genre(self, book_id, new_genre):
        """Update book genre in database"""
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE books SET genre = %s WHERE book_id = %s", (new_genre, book_id))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Database error: {e}")
            return False
        finally:
            conn.close()
    
    def process_book(self, book):
        """Process a single book"""
        try:
            self.logger.info(f"Processing: \"{book['title'][:60]}...\" by {book['author']}")
            
            # Get content
            content = self.get_book_content_sample(book['book_id'])
            if not content or len(content) < 50:
                self.logger.warning(f"Insufficient content for {book['title']}")
                return "insufficient_content"
            
            # Classify
            new_genre, duration = self.classify_with_llama(book, content)
            if not new_genre:
                self.logger.warning(f"Classification failed for {book['title']}")
                return "classification_failed"
            
            self.logger.info(f"Classification: {new_genre} ({duration:.1f}s)")
            
            # Update if different
            if new_genre != book['genre']:
                if self.update_book_genre(book['book_id'], new_genre):
                    self.logger.info(f"UPDATED: {book['genre']} → {new_genre}")
                    
                    # Track changes
                    old_genre = book['genre']
                    if old_genre not in self.state['genre_changes']:
                        self.state['genre_changes'][old_genre] = {}
                    if new_genre not in self.state['genre_changes'][old_genre]:
                        self.state['genre_changes'][old_genre][new_genre] = 0
                    self.state['genre_changes'][old_genre][new_genre] += 1
                    
                    return "reclassified"
                else:
                    return "update_failed"
            else:
                self.logger.info(f"CONFIRMED: {new_genre}")
                return "confirmed"
                
        except Exception as e:
            self.logger.error(f"Error processing {book['title']}: {e}")
            return "error"
    
    def run(self):
        """Main daemon loop"""
        self.logger.info("🚀 FULL LIBRARY RECLASSIFICATION DAEMON STARTING")
        self.logger.info("📚 Reprocessing ALL books with llama3.2:3b for maximum accuracy")
        self.logger.info("=" * 80)
        
        # Initialize
        if not self.state["start_time"]:
            self.state["start_time"] = datetime.now().isoformat()
        
        self.state["status"] = "running"
        
        # Get all books
        books_to_process = self.get_all_books_to_process()
        self.state["total_books"] = len(books_to_process) + len(self.state["processed_books"])
        
        self.logger.info(f"📚 Found {len(books_to_process)} books to process")
        self.logger.info(f"📊 Progress: {len(self.state['processed_books'])}/{self.state['total_books']} completed")
        
        if not books_to_process:
            self.logger.info("✅ ALL BOOKS PROCESSED - DAEMON COMPLETE!")
            self.state["status"] = "completed"
            self.save_state()
            return
        
        # Estimate completion time
        estimated_seconds = len(books_to_process) * 1.2  # ~1.2s per book
        estimated_minutes = estimated_seconds / 60
        self.logger.info(f"⏱️  Estimated completion: {estimated_minutes:.1f} minutes")
        
        # Process books in batches
        batch_size = 20
        for i in range(0, len(books_to_process), batch_size):
            batch = books_to_process[i:i + batch_size]
            self.state["current_batch"] += 1
            
            self.logger.info(f"📦 Processing batch {self.state['current_batch']} ({len(batch)} books)")
            
            for book in batch:
                result = self.process_book(book)
                
                # Update counters
                self.state["processed_books"].append(book['book_id'])
                self.state["processed_count"] += 1
                
                if result == "reclassified":
                    self.state["reclassified_count"] += 1
                elif result == "confirmed":
                    self.state["confirmed_count"] += 1
                elif result in ["error", "classification_failed", "update_failed"]:
                    self.state["failed_count"] += 1
                    self.state["errors"].append({
                        "book_id": book['book_id'],
                        "title": book['title'],
                        "error": result,
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Progress update
                progress_pct = (self.state["processed_count"] / self.state["total_books"]) * 100
                self.logger.info(f"📊 Progress: {self.state['processed_count']}/{self.state['total_books']} ({progress_pct:.1f}%)")
                
                # Save state every 10 books
                if self.state["processed_count"] % 10 == 0:
                    self.save_state()
                
                time.sleep(0.5)  # Very fast processing
            
            # Batch complete
            self.logger.info(f"✅ Batch {self.state['current_batch']} complete")
            self.save_state()
        
        # Final completion
        self.logger.info("🎉 FULL LIBRARY RECLASSIFICATION COMPLETE!")
        self.logger.info(f"📊 Final Stats:")
        self.logger.info(f"   • Total processed: {self.state['processed_count']}")
        self.logger.info(f"   • Reclassified: {self.state['reclassified_count']}")
        self.logger.info(f"   • Confirmed accurate: {self.state['confirmed_count']}")
        self.logger.info(f"   • Failed: {self.state['failed_count']}")
        
        accuracy_rate = ((self.state['reclassified_count'] + self.state['confirmed_count']) / 
                        self.state['processed_count']) * 100
        self.logger.info(f"   • Accuracy rate: {accuracy_rate:.1f}%")
        
        self.state["status"] = "completed"
        self.state["completion_time"] = datetime.now().isoformat()
        self.save_state()

def main():
    """Start the daemon"""
    daemon = FullLibraryReclassificationDaemon()
    
    try:
        daemon.run()
    except KeyboardInterrupt:
        daemon.logger.info("🛑 Daemon stopped by user")
    except Exception as e:
        daemon.logger.error(f"💥 Daemon crashed: {e}")
        daemon.state["status"] = "crashed"
        daemon.save_state()
    finally:
        daemon.cleanup()

if __name__ == '__main__':
    main()