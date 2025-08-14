#!/usr/bin/env python3
"""
🚀 NOMIC-ONLY EMBEDDING DAEMON - Maximum Throughput Focus
=========================================================

Single-model embedding daemon using only nomic-embed-text for maximum speed.
No model switching, no Arctic failures, pure throughput.
"""

import os
import sys
import json
import time
import signal
import logging
import psycopg2
import psycopg2.extras
import requests
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))
sys.path.append(str(project_root))

class NomicOnlyDaemon:
    """
    🚀 Single-model embedding daemon for maximum throughput
    """
    
    def __init__(self, name="nomic_daemon"):
        self.name = name
        self.daemon_dir = project_root / "logs" / "nomic_daemon"
        self.daemon_dir.mkdir(parents=True, exist_ok=True)
        
        self.state_file = self.daemon_dir / f"{name}_state.json"
        self.log_file = self.daemon_dir / f"{name}.log"
        self.pid_file = project_root / "pids" / f"{name}.pid"
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(f"NomicDaemon-{name}")
        
        # Database configuration
        self.db_config = {
            'host': 'localhost',
            'database': 'knowledge_base', 
            'user': os.environ.get('DB_USER', 'weixiangzhang'),
            'password': os.environ.get('DB_PASSWORD')
        }
        
        # Ollama configuration - NOMIC ONLY
        self.ollama_base_url = "http://localhost:11434"
        self.model_name = "nomic-embed-text:latest"
        self.dimensions = 768
        
        # Processing parameters - OPTIMIZED FOR SPEED
        self.batch_size = 50  # Larger batches
        self.delay_between_batches = 0.5  # Faster batching
        self.retry_attempts = 2  # Fewer retries
        
        # Statistics
        self.chunks_processed = 0
        self.start_time = datetime.now()
        
        # Load state
        self.load_state()
        
        self.logger.info(f"🚀 {name} - Nomic-only daemon initialized")
        self.logger.info(f"📊 Model: {self.model_name} ({self.dimensions}d)")
    
    def load_state(self):
        """Load daemon state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.chunks_processed = state.get('chunks_processed', 0)
                self.logger.info(f"📁 Loaded state: {self.chunks_processed} chunks processed")
            except Exception as e:
                self.logger.warning(f"Could not load state: {e}")
    
    def save_state(self):
        """Save daemon state to file"""
        try:
            state = {
                'chunks_processed': self.chunks_processed,
                'last_save': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Could not save state: {e}")
    
    def get_db_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            return None
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding from Nomic model"""
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/embeddings",
                json={
                    "model": self.model_name,
                    "prompt": text
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('embedding')
            else:
                self.logger.warning(f"Embedding request failed: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Embedding error: {e}")
            return None
    
    def process_chunk_batch(self) -> int:
        """Process a batch of chunks"""
        processed_count = 0
        
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return 0
                    
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # Get chapters without embeddings
                    cur.execute("""
                        SELECT chunk_id, content, book_id
                        FROM chunks 
                        WHERE chunk_type = 'chapter' 
                        AND embedding_vector IS NULL
                        AND LENGTH(content) > 100
                        ORDER BY book_id
                        LIMIT %s
                    """, (self.batch_size,))
                    
                    chunks = cur.fetchall()
                    
                    if not chunks:
                        self.logger.info("✅ No more chapters to process!")
                        return 0
                    
                    self.logger.info(f"📦 Processing batch: {len(chunks)} chapters")
                    
                    for chunk in chunks:
                        try:
                            # Get embedding
                            embedding = self.get_embedding(chunk['content'])
                            
                            if embedding and len(embedding) == self.dimensions:
                                # Update chunk with embedding
                                cur.execute("""
                                    UPDATE chunks 
                                    SET embedding_vector = %s, 
                                        created_at = NOW()
                                    WHERE chunk_id = %s
                                """, (embedding, chunk['chunk_id']))
                                
                                processed_count += 1
                                self.chunks_processed += 1
                                
                                if processed_count % 10 == 0:
                                    self.logger.info(f"⚡ Processed {processed_count}/{len(chunks)} in batch")
                                
                            else:
                                self.logger.warning(f"Invalid embedding for {chunk['chunk_id']}")
                                
                        except Exception as e:
                            self.logger.error(f"Error processing {chunk['chunk_id']}: {e}")
                    
                    # Commit all changes
                    conn.commit()
                    
                    if processed_count > 0:
                        self.logger.info(f"✅ Batch complete: {processed_count} chapters embedded")
                        
        except Exception as e:
            self.logger.error(f"Batch processing error: {e}")
        
        return processed_count
    
    def run(self):
        """Main daemon loop"""
        self.logger.info(f"🚀 Starting {self.name} daemon")
        
        # Write PID file
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))
        
        try:
            while True:
                processed = self.process_chunk_batch()
                
                if processed > 0:
                    # Calculate rate
                    elapsed = (datetime.now() - self.start_time).total_seconds() / 3600
                    rate = self.chunks_processed / elapsed if elapsed > 0 else 0
                    self.logger.info(f"📊 Total: {self.chunks_processed:,} | Rate: {rate:.1f}/hour")
                    
                    # Save state periodically
                    if self.chunks_processed % 100 == 0:
                        self.save_state()
                else:
                    self.logger.info("😴 No work available, sleeping...")
                    time.sleep(30)
                    continue
                
                # Brief pause between batches
                time.sleep(self.delay_between_batches)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Daemon stopped by user")
        except Exception as e:
            self.logger.error(f"Daemon error: {e}")
        finally:
            self.save_state()
            if self.pid_file.exists():
                self.pid_file.unlink()

def main():
    parser = argparse.ArgumentParser(description="Nomic-only embedding daemon")
    parser.add_argument("--name", default="nomic_daemon", help="Daemon name")
    args = parser.parse_args()
    
    daemon = NomicOnlyDaemon(name=args.name)
    daemon.run()

if __name__ == "__main__":
    main()