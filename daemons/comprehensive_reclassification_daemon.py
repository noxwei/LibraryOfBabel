#!/usr/bin/env python3
"""
Comprehensive Reclassification Daemon
=====================================
Autonomous daemon to reprocess all 407 books without descriptions
- Self-stopping when complete
- Progress tracking and resumption
- Error recovery
- Status monitoring
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

class ReclassificationDaemon:
    def __init__(self):
        self.db_config = get_database_config()
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = "llama3.2:3b"  # Fast, accurate model
        
        # State file for persistence
        self.state_file = project_root / "daemons" / "reclassification_state.json"
        self.log_file = project_root / "daemons" / "reclassification.log"
        self.pid_file = project_root / "daemons" / "reclassification.pid"
        
        # Initialize state
        self.state = {
            "processed_books": [],
            "processed_count": 0,
            "reclassified_count": 0,
            "failed_count": 0,
            "current_batch": 0,
            "total_books": 0,
            "start_time": None,
            "last_update": None,
            "status": "initializing",
            "genre_changes": {},
            "errors": []
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
        
        # Valid genres
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
    
    def get_books_to_process(self):
        """Get all books without descriptions that haven't been processed"""
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        
        try:
            with conn.cursor() as cur:
                # Get books not yet processed
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
                        AND LENGTH(c.content) > 150
                    )
                    AND (b.description IS NULL OR b.description = '')
                    {processed_condition}
                    ORDER BY b.book_id
                """)
                
                return cur.fetchall()
        finally:
            conn.close()
    
    def get_book_content(self, book_id):
        """Get representative content from book"""
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        
        try:
            with conn.cursor() as cur:
                # Get chunks from different parts of the book
                cur.execute("""
                    WITH numbered_chunks AS (
                        SELECT content,
                               ROW_NUMBER() OVER (ORDER BY chunk_id) as rn,
                               COUNT(*) OVER () as total_chunks
                        FROM chunks
                        WHERE book_id = %s
                        AND content IS NOT NULL
                        AND LENGTH(content) > 150
                    )
                    SELECT content
                    FROM numbered_chunks
                    WHERE rn IN (1, GREATEST(total_chunks/4, 1), GREATEST(total_chunks/2, 1), total_chunks)
                    ORDER BY rn
                    LIMIT 4
                """, (book_id,))
                
                chunks = cur.fetchall()
                
                # Clean and combine content
                content_samples = []
                for i, chunk in enumerate(chunks, 1):
                    clean_content = re.sub(r'<[^>]+>', '', chunk['content'])
                    clean_content = re.sub(r'\s+', ' ', clean_content).strip()
                    
                    if len(clean_content) > 300:
                        sample = clean_content[:300]
                    else:
                        sample = clean_content
                    
                    content_samples.append(f"[Sample {i}] {sample}")
                
                return "\n\n".join(content_samples)
        finally:
            conn.close()
    
    def classify_content(self, book_data, content):
        """Use Magistral to classify based on content"""
        
        prompt = f"""You are an expert book classifier. Analyze the actual content to determine the correct genre.

BOOK:
Title: "{book_data['title']}"
Author: {book_data['author']}"
Current: {book_data['genre']}

CONTENT:
{content[:1500]}

GENRES: Romance, Literary Fiction, Science Fiction, Fantasy, Mystery & Thriller, Historical Fiction, Contemporary Fiction, Self-Help, Biography & Memoir, Psychology, Philosophy, Business & Economics, History, Science & Nature, Programming & Technology, Data Science & Analytics, Religion & Spirituality, Political Science, Academic & Research, Health & Medicine

RULES:
1. Base on CONTENT only, not title
2. Fiction: Has characters, dialogue, narrative
3. Non-fiction: Facts, analysis, instruction
4. Choose most specific genre

What genre best fits this content?

Respond with ONLY the genre name."""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.05}
                },
                timeout=30  # Fast model - 30 seconds is plenty
            )
            
            if response.status_code == 200:
                result = response.json()
                classification = result['response'].strip()
                
                # Extract clean classification
                if "\\boxed{" in classification:
                    match = re.search(r'\\boxed\{([^}]+)\}', classification)
                    if match:
                        classification = match.group(1)
                else:
                    lines = [line.strip() for line in classification.split('\n') if line.strip()]
                    if lines:
                        for line in reversed(lines):
                            for genre in self.valid_genres:
                                if genre.lower() in line.lower():
                                    classification = genre
                                    break
                            if classification in self.valid_genres:
                                break
                        else:
                            classification = lines[-1]
                
                # Clean and validate
                classification = re.sub(r'^["\']|["\']$', '', classification).strip()
                
                if classification in self.valid_genres:
                    return classification
                else:
                    # Try partial matching
                    for valid_genre in self.valid_genres:
                        if valid_genre.lower() in classification.lower():
                            return valid_genre
                    return None
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Classification error: {e}")
            return None
    
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
            self.logger.info(f"Processing: \"{book['title']}\" by {book['author']}")
            
            # Get content
            content = self.get_book_content(book['book_id'])
            if not content or len(content) < 100:
                self.logger.warning(f"Insufficient content for {book['title']}")
                return "insufficient_content"
            
            # Classify
            new_genre = self.classify_content(book, content)
            if not new_genre:
                self.logger.warning(f"Classification failed for {book['title']}")
                return "classification_failed"
            
            self.logger.info(f"Content classification: {new_genre}")
            
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
        self.logger.info("🚀 COMPREHENSIVE RECLASSIFICATION DAEMON STARTING")
        self.logger.info("=" * 60)
        
        # Initialize
        if not self.state["start_time"]:
            self.state["start_time"] = datetime.now().isoformat()
        
        self.state["status"] = "running"
        
        # Get books to process
        books_to_process = self.get_books_to_process()
        self.state["total_books"] = len(books_to_process) + len(self.state["processed_books"])
        
        self.logger.info(f"📚 Found {len(books_to_process)} books to process")
        self.logger.info(f"📊 Progress: {len(self.state['processed_books'])}/{self.state['total_books']} completed")
        
        if not books_to_process:
            self.logger.info("✅ ALL BOOKS PROCESSED - DAEMON COMPLETE!")
            self.state["status"] = "completed"
            self.save_state()
            return
        
        # Process books in batches
        batch_size = 10
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
                
                # Save state every 5 books
                if self.state["processed_count"] % 5 == 0:
                    self.save_state()
                
                time.sleep(1)  # Reduced rate limiting for fast model
            
            # Batch complete
            self.logger.info(f"✅ Batch {self.state['current_batch']} complete")
            self.save_state()
        
        # Final completion
        self.logger.info("🎉 COMPREHENSIVE RECLASSIFICATION COMPLETE!")
        self.logger.info(f"📊 Final Stats:")
        self.logger.info(f"   • Total processed: {self.state['processed_count']}")
        self.logger.info(f"   • Reclassified: {self.state['reclassified_count']}")
        self.logger.info(f"   • Failed: {self.state['failed_count']}")
        
        self.state["status"] = "completed"
        self.state["completion_time"] = datetime.now().isoformat()
        self.save_state()

def main():
    """Start the daemon"""
    daemon = ReclassificationDaemon()
    
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