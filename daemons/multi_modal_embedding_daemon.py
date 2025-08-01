#!/usr/bin/env python3
"""
🧠 MULTI-MODAL EMBEDDING DAEMON - Dr. Sarah Chen's PostgreSQL-First Architecture
===============================================================================

Intelligent content routing daemon that continuously processes chunks with optimal AI models:
- Technical/Academic: snowflake-arctic-embed (1024d) - Precise factual embedding
- Creative/Narrative: bge-m3 (1024d) - Rich semantic understanding  
- Cultural/Multilingual: mxbai-embed-large (1024d) - Cross-linguistic preservation
- General: nomic-embed-text (768d) - Broad coverage fallback

Features:
- Continuous processing with restart capability
- Intelligent content classification and model routing
- Progress tracking and performance analytics
- Database-first architecture with ACID compliance
- Resource management and error handling
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
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import threading

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))
sys.path.append(str(project_root))

@dataclass
class DaemonStats:
    """Daemon performance statistics"""
    start_time: datetime
    chunks_processed: int = 0
    chunks_successful: int = 0
    chunks_failed: int = 0
    books_processed: int = 0
    model_usage: Dict[str, int] = None
    total_processing_time: float = 0.0
    average_chunk_time: float = 0.0
    
    def __post_init__(self):
        if self.model_usage is None:
            self.model_usage = {"nomic": 0, "mxbai": 0, "bge": 0, "arctic": 0}

class MultiModalEmbeddingDaemon:
    """
    🚀 Dr. Sarah Chen's Multi-Modal Embedding Daemon
    
    Continuously processes book chunks with intelligent AI model routing
    based on content classification for optimal semantic understanding.
    """
    
    def __init__(self):
        self.daemon_dir = project_root / "logs" / "multi_modal_daemon"
        self.daemon_dir.mkdir(parents=True, exist_ok=True)
        
        self.state_file = self.daemon_dir / "daemon_state.json"
        self.log_file = self.daemon_dir / "daemon.log"
        self.pid_file = project_root / "pids" / "multi_modal_daemon.pid"
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("MultiModalDaemon")
        
        # Database configuration
        self.db_config = {
            'host': 'localhost',
            'database': 'knowledge_base', 
            'user': os.environ.get('DB_USER', 'postgres'),
            'password': os.environ.get('DB_PASSWORD')
        }
        
        # Ollama configuration
        self.ollama_base_url = "http://localhost:11434"
        
        # Multi-modal AI model configuration (4 specialized models)
        self.embedding_models = {
            "nomic": {
                "ollama_name": "nomic-embed-text:latest", 
                "dimensions": 768,
                "specialization": "general",
                "description": "General content - broad coverage fallback model",
                "keywords": ["general", "reference", "guide", "manual", "overview", "introduction", 
                           "basic", "fundamental", "essential", "practical", "everyday", "common"]
            },
            "bge": {
                "ollama_name": "bge-m3:latest",
                "dimensions": 1024, 
                "specialization": "semantic_narrative",
                "description": "Creative/narrative content with rich semantic understanding",
                "keywords": ["story", "novel", "fiction", "fantasy", "adventure", "romance", "character", 
                           "plot", "narrative", "tale", "saga", "epic", "literary", "drama", "thriller"]
            },
            "mxbai": {
                "ollama_name": "mxbai-embed-large:latest",
                "dimensions": 1024,
                "specialization": "multilingual",
                "description": "Cultural/multilingual content with cross-linguistic preservation",
                "keywords": ["culture", "cultural", "international", "global", "world", "foreign", 
                           "translation", "history", "memoir", "biography", "travel", "ethnography"]
            },
            "arctic": {
                "ollama_name": "snowflake-arctic-embed:latest",
                "dimensions": 1024,
                "specialization": "technical_academic", 
                "description": "Technical/academic content - Arctic embedding model",
                "keywords": ["technology", "science", "research", "analysis", "theory", "methodology", 
                           "academic", "scholarly", "technical", "engineering", "mathematics", "physics", 
                           "chemistry", "biology", "computer", "algorithm", "philosophy", "business", "economics"]
            }
        }
        
        # Processing parameters
        self.batch_size = 25  # Chunks per batch
        self.delay_between_batches = 2  # Seconds
        self.delay_between_chunks = 0.1  # Seconds  
        self.retry_attempts = 3
        
        # Daemon control
        self.running = False
        self.stats = DaemonStats(start_time=datetime.now())
        
        # Load previous state
        self.load_state()
        
        self.logger.info("🧠 Multi-Modal Embedding Daemon initialized")
        self.logger.info(f"📊 Models available: {list(self.embedding_models.keys())}")
        
    def load_state(self):
        """Load daemon state from previous session"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.stats.chunks_processed = state.get('chunks_processed', 0)
                    self.stats.chunks_successful = state.get('chunks_successful', 0)
                    self.stats.chunks_failed = state.get('chunks_failed', 0) 
                    self.stats.books_processed = state.get('books_processed', 0)
                    self.stats.model_usage = state.get('model_usage', {"nomic": 0, "mxbai": 0, "bge": 0, "arctic": 0})
                    self.stats.total_processing_time = state.get('total_processing_time', 0.0)
                    
                    self.logger.info(f"📁 Loaded state: {self.stats.chunks_processed} chunks processed")
            except Exception as e:
                self.logger.error(f"Failed to load state: {e}")
                
    def save_state(self):
        """Save current daemon state"""
        try:
            runtime = (datetime.now() - self.stats.start_time).total_seconds()
            self.stats.average_chunk_time = (self.stats.total_processing_time / 
                                           self.stats.chunks_processed if self.stats.chunks_processed > 0 else 0)
            
            state = {
                "session_start": self.stats.start_time.isoformat(),
                "last_updated": datetime.now().isoformat(),
                "runtime_seconds": runtime,
                "chunks_processed": self.stats.chunks_processed,
                "chunks_successful": self.stats.chunks_successful,
                "chunks_failed": self.stats.chunks_failed,
                "books_processed": self.stats.books_processed,
                "model_usage": self.stats.model_usage,
                "total_processing_time": self.stats.total_processing_time,
                "average_chunk_time": self.stats.average_chunk_time,
                "success_rate": (self.stats.chunks_successful / self.stats.chunks_processed * 100 
                               if self.stats.chunks_processed > 0 else 0)
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
            
    def get_db_connection(self):
        """Get PostgreSQL connection with retry logic"""
        for attempt in range(3):
            try:
                return psycopg2.connect(**self.db_config)
            except psycopg2.Error as e:
                self.logger.warning(f"DB connection attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(5)
        return None
        
    def classify_content_type(self, chunk_content: str, book_title: str = "", book_genre: str = "") -> str:
        """
        Dr. Sarah Chen's intelligent content classification system
        
        Analyzes content and metadata to determine optimal embedding model:
        - technical_academic: Philosophy, science, technology, business → snowflake-arctic-embed
        - semantic_narrative: Fiction, fantasy, romance, literature → bge-m3  
        - multilingual: History, biography, travel, cultural studies → mxbai-embed-large
        - general: Reference, self-help, mystery, psychology → nomic-embed-text
        """
        
        # Combine text for analysis
        combined_text = f"{book_title} {book_genre} {chunk_content}".lower()
        
        # Count keyword matches for each specialization
        scores = {}
        for model_key, config in self.embedding_models.items():
            score = sum(1 for keyword in config["keywords"] if keyword in combined_text)
            scores[model_key] = score
            
        # Find best match
        best_model = max(scores, key=scores.get)
        best_score = scores[best_model]
        
        # If no clear match, use content length and complexity heuristics
        if best_score == 0:
            if len(chunk_content) > 2000 and any(word in combined_text for word in ["theory", "analysis", "research"]):
                return "technical_academic"
            elif any(word in combined_text for word in ["story", "character", "novel"]):
                return "semantic_narrative" 
            else:
                return "general"
                
        # Map model to specialization (4 specialized models)
        model_mapping = {
            "nomic": "general",
            "bge": "semantic_narrative", 
            "mxbai": "multilingual",
            "arctic": "technical_academic"
        }
        
        return model_mapping.get(best_model, "general")
        
    def select_optimal_model(self, content_type: str) -> str:
        """Select optimal embedding model based on content classification with balanced distribution"""
        
        # Primary model mapping based on content type
        model_mapping = {
            "technical_academic": "arctic",
            "semantic_narrative": "bge",
            "multilingual": "mxbai", 
            "general": "nomic"
        }
        
        optimal_model = model_mapping.get(content_type, "nomic")
        
        # Balanced distribution check - if one model is over-utilized, use alternatives
        total_processed = sum(self.stats.model_usage.values())
        if total_processed > 100:  # Only balance after processing some chunks
            current_usage = self.stats.model_usage.get(optimal_model, 0)
            usage_percentage = current_usage / total_processed
            
            # If a model is over 35% of usage, prefer alternatives
            if usage_percentage > 0.35:
                alternative_models = [m for m in self.embedding_models.keys() if m != optimal_model]
                # Pick model with lowest usage
                alternative_model = min(alternative_models, key=lambda x: self.stats.model_usage.get(x, 0))
                self.logger.info(f"🔄 Balancing: Using {alternative_model} instead of {optimal_model} (usage: {usage_percentage:.1%})")
                return alternative_model
        
        return optimal_model
        
    def generate_embedding(self, text: str, model_key: str) -> Optional[List[float]]:
        """Generate embedding using specified Ollama model"""
        
        model_config = self.embedding_models[model_key]
        
        for attempt in range(self.retry_attempts):
            try:
                response = requests.post(
                    f"{self.ollama_base_url}/api/embeddings",
                    json={
                        "model": model_config["ollama_name"],
                        "prompt": text
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    embedding = response.json().get('embedding')
                    if embedding and len(embedding) == model_config["dimensions"]:
                        return embedding
                    else:
                        self.logger.warning(f"Invalid embedding dimensions from {model_key}")
                else:
                    self.logger.warning(f"API error from {model_key}: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout from {model_key}, attempt {attempt + 1}")
            except Exception as e:
                self.logger.warning(f"Error from {model_key}: {e}, attempt {attempt + 1}")
                
            if attempt < self.retry_attempts - 1:
                time.sleep(5)
                
        return None
        
    def process_chunk_batch(self) -> int:
        """Process a batch of chunks with optimal model routing"""
        
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return 0
                    
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # Get chunks that need multi-modal embedding (any missing embedding)
                    cur.execute("""
                        SELECT c.chunk_id, c.content, c.book_id, b.title, b.genre
                        FROM chunks c
                        JOIN books b ON c.book_id = b.book_id  
                        WHERE c.content IS NOT NULL 
                        AND (c.embedding_nomic IS NULL 
                             OR c.embedding_mxbai IS NULL 
                             OR c.embedding_bge IS NULL 
                             OR c.embedding_arctic IS NULL)
                        ORDER BY RANDOM()  -- Randomize for balanced processing
                        LIMIT %s
                    """, (self.batch_size,))
                    
                    chunks = cur.fetchall()
                    if not chunks:
                        return 0
                        
                    self.logger.info(f"📦 Processing batch of {len(chunks)} chunks")
                    
                    processed_count = 0
                    for chunk in chunks:
                        if not self.running:
                            break
                            
                        start_time = time.time()
                        
                        # Classify content type
                        content_type = self.classify_content_type(
                            chunk['content'], 
                            chunk.get('title', ''),
                            chunk.get('genre', '')
                        )
                        
                        # Select optimal model
                        optimal_model = self.select_optimal_model(content_type)
                        
                        # Generate embedding
                        embedding = self.generate_embedding(chunk['content'], optimal_model)
                        
                        if embedding:
                            # Update chunk with new embedding
                            model_config = self.embedding_models[optimal_model]
                            column_name = f"embedding_{optimal_model}"
                            
                            cur.execute(f"""
                                UPDATE chunks SET 
                                    {column_name} = %s,
                                    content_type = %s,
                                    routing_reason = %s,
                                    embedding_model_used = %s
                                WHERE chunk_id = %s
                            """, (
                                embedding,
                                content_type,
                                f"Phase3-{optimal_model}-{model_config['specialization']}",
                                optimal_model,
                                chunk['chunk_id']
                            ))
                            
                            self.stats.chunks_successful += 1
                            self.stats.model_usage[optimal_model] += 1
                            processed_count += 1
                            
                        else:
                            self.stats.chunks_failed += 1
                            self.logger.error(f"Failed embedding for chunk {chunk['chunk_id']}")
                            
                        # Update timing stats
                        processing_time = time.time() - start_time
                        self.stats.total_processing_time += processing_time
                        self.stats.chunks_processed += 1
                        
                        # Throttle between chunks
                        time.sleep(self.delay_between_chunks)
                        
                    conn.commit()
                    return processed_count
                    
        except Exception as e:
            self.logger.error(f"Batch processing error: {e}")
            return 0
            
    def run_daemon(self):
        """Main daemon processing loop"""
        
        self.logger.info("🚀 Starting Multi-Modal Embedding Daemon")
        self.logger.info(f"📊 Previous session: {self.stats.chunks_processed} chunks processed")
        
        # Write PID file
        self.pid_file.parent.mkdir(exist_ok=True)
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))
            
        self.running = True
        batch_count = 0
        
        try:
            while self.running:
                batch_count += 1
                
                # Process batch
                processed = self.process_chunk_batch()
                
                if processed == 0:
                    self.logger.info("✅ No more chunks to process - daemon complete!")
                    break
                    
                # Log progress every 10 batches
                if batch_count % 10 == 0:
                    success_rate = (self.stats.chunks_successful / self.stats.chunks_processed * 100 
                                  if self.stats.chunks_processed > 0 else 0)
                    
                    self.logger.info(f"📈 Progress: {self.stats.chunks_processed} chunks, {success_rate:.1f}% success")
                    self.logger.info(f"🎯 Model distribution: {dict(self.stats.model_usage)}")
                    
                    # Save state periodically
                    self.save_state()
                    
                # Delay between batches
                time.sleep(self.delay_between_batches)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Daemon interrupted by user")
        except Exception as e:
            self.logger.error(f"💥 Daemon error: {e}")
        finally:
            self.running = False
            self.save_state()
            self.cleanup()
            
    def cleanup(self):
        """Cleanup daemon resources"""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
            self.logger.info("🧹 Daemon cleanup complete")
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
            
    def print_final_report(self):
        """Print comprehensive final processing report"""
        
        runtime = (datetime.now() - self.stats.start_time).total_seconds()
        
        print("\n" + "="*80)
        print("🧠 MULTI-MODAL EMBEDDING DAEMON - FINAL REPORT")
        print("="*80)
        print(f"📊 Total Chunks Processed: {self.stats.chunks_processed:,}")
        print(f"✅ Successful Embeddings: {self.stats.chunks_successful:,}")
        print(f"❌ Failed Embeddings: {self.stats.chunks_failed:,}")
        print(f"📈 Success Rate: {self.stats.chunks_successful/self.stats.chunks_processed*100:.1f}%" 
              if self.stats.chunks_processed > 0 else "📈 Success Rate: 0%")
        print(f"⏱️  Total Runtime: {runtime:.1f} seconds ({runtime/3600:.1f} hours)")
        print(f"⚡ Average Time/Chunk: {self.stats.total_processing_time/self.stats.chunks_processed:.2f}s"
              if self.stats.chunks_processed > 0 else "⚡ Average Time/Chunk: 0s")
        
        print(f"\n🎯 AI MODEL USAGE DISTRIBUTION:")
        for model, count in self.stats.model_usage.items():
            if count > 0:
                config = self.embedding_models[model]
                percentage = (count / self.stats.chunks_successful * 100 if self.stats.chunks_successful > 0 else 0)
                print(f"  {model:>7s}: {count:>6,d} chunks ({percentage:>5.1f}%) - {config['specialization']}")
        
        print(f"\n📁 State File: {self.state_file}")
        print(f"📋 Log File: {self.log_file}")
        print("="*80)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print("\n🛑 Received shutdown signal - stopping daemon...")
    if hasattr(signal_handler, 'daemon'):
        signal_handler.daemon.running = False

def main():
    """Main daemon entry point"""
    
    daemon = MultiModalEmbeddingDaemon()
    signal_handler.daemon = daemon
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        daemon.run_daemon()
        daemon.print_final_report()
    except Exception as e:
        daemon.logger.error(f"💥 Fatal daemon error: {e}")
        raise

if __name__ == "__main__":
    main()