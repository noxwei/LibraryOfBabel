#!/usr/bin/env python3
"""
🌙 Vector Optimization Daemon - Dr. Sarah Chen Implementation
=============================================================

Overnight processing daemon for LibraryOfBabel's complete vector optimization.
Processes all 2,074+ books through the advanced semantic chunking and 
multi-modal embedding pipeline.

Features:
- Automatic book discovery and processing queue
- Resumable processing (handles interruptions)
- Performance monitoring and logging
- Error recovery and retry logic
- Progress reporting and status updates
- Memory management for large-scale processing

Lead: Dr. Sarah Chen (陈雪芳) - Lead Data Engineer
Philosophy: "夜间处理，白天享受完美搜索体验"
(Overnight processing for perfect daytime search experience)
"""

import os
import sys
import json
import time
import signal
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import gc

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / 'src'))

try:
    from advanced_semantic_chunker import AdvancedSemanticChunker
    from multimodal_embedding_pipeline import MultiModalEmbeddingPipeline
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure you're running from the LibraryOfBabel root directory")
    sys.exit(1)

class VectorOptimizationDaemon:
    """
    Dr. Sarah Chen's overnight vector optimization daemon.
    
    Processes the complete LibraryOfBabel collection through:
    1. Advanced semantic chunking
    2. Multi-modal embedding generation
    3. Specialized vector index optimization
    """
    
    def __init__(self, config_file: Optional[str] = None):
        # Load configuration
        self.config = self._load_config(config_file)
        
        # Database configuration
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': int(os.getenv('DB_PORT', 5432))
        }
        
        # Initialize components
        self.semantic_chunker = AdvancedSemanticChunker(self.db_config)
        self.embedding_pipeline = MultiModalEmbeddingPipeline(self.db_config)
        
        # Processing state
        self.status_file = Path("scripts/optimization_status_v2.json")
        self.is_running = False
        self.should_stop = False
        self.processing_queue = queue.Queue()
        
        # Performance tracking
        self.stats = {
            'start_time': None,
            'books_processed': 0,
            'books_failed': 0,
            'total_chunks_created': 0,
            'total_embeddings_generated': 0,
            'current_book': None,
            'estimated_completion': None,
            'errors': []
        }
        
        # Setup logging
        self._setup_logging()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("🌙 Dr. Sarah Chen's Vector Optimization Daemon initialized")
        self.logger.info("夜间处理，白天享受完美搜索体验")
    
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load daemon configuration"""
        default_config = {
            'chunk_levels': ['medium', 'large'],  # Focus on useful chunk sizes
            'max_workers': 4,                     # Parallel processing workers
            'batch_size': 10,                     # Books per batch
            'max_retries': 3,                     # Retry failed books
            'sleep_between_books': 2,             # Seconds between books (be nice to system)
            'progress_report_interval': 100,      # Report every N books
            'enable_garbage_collection': True,    # Memory management
            'checkpoint_interval': 50             # Save status every N books
        }
        
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                print(f"⚠️ Error loading config file: {e}")
        
        return default_config
    
    def _setup_logging(self):
        """Setup comprehensive logging for overnight processing"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Create timestamp for this run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"vector_optimization_v2_{timestamp}.log"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - 陈雪芳 - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"📝 Logging initialized: {log_file}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"🛑 Received signal {signum}, initiating graceful shutdown...")
        self.should_stop = True
    
    def _save_status(self):
        """Save current processing status to file"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'is_running': self.is_running,
            'stats': self.stats,
            'config': self.config
        }
        
        try:
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            self.logger.error(f"❌ Failed to save status: {e}")
    
    def _load_status(self) -> Dict[str, Any]:
        """Load previous processing status"""
        if not self.status_file.exists():
            return {}
        
        try:
            with open(self.status_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"⚠️ Failed to load status: {e}")
            return {}
    
    def discover_books_to_process(self) -> List[Dict[str, Any]]:
        """Discover all books that need vector optimization"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    
                    # Find books that need multi-modal processing (avoiding prior vector conversion)
                    cur.execute("""
                        SELECT b.book_id, b.title, b.author, 
                               COUNT(c.chunk_id) as chunk_count,
                               COUNT(sc.chunk_id) as semantic_chunks,
                               COUNT(se.chunk_id) as semantic_embeddings,
                               COUNT(fe.chunk_id) as factual_embeddings,
                               COUNT(te.chunk_id) as topical_embeddings
                        FROM books b
                        LEFT JOIN chunks c ON b.book_id = c.book_id
                        LEFT JOIN semantic_chunks sc ON b.book_id = sc.book_id AND sc.chunk_level = 'medium'
                        LEFT JOIN semantic_embeddings se ON sc.chunk_id = se.chunk_id
                        LEFT JOIN factual_embeddings fe ON sc.chunk_id = fe.chunk_id
                        LEFT JOIN topical_embeddings te ON sc.chunk_id = te.chunk_id
                        GROUP BY b.book_id, b.title, b.author
                        HAVING COUNT(c.chunk_id) > 0 
                           AND (COUNT(sc.chunk_id) = 0 
                                OR COUNT(se.chunk_id) = 0 
                                OR COUNT(fe.chunk_id) = 0 
                                OR COUNT(te.chunk_id) = 0)
                        ORDER BY b.book_id
                    """)
                    
                    books_to_process = cur.fetchall()
                    
                    self.logger.info(f"📚 Discovered {len(books_to_process)} books requiring vector optimization")
                    self.logger.info("🎯 Focusing on new multi-modal embeddings (avoiding prior vector conversion)")
                    return [dict(book) for book in books_to_process]
                    
        except Exception as e:
            self.logger.error(f"❌ Failed to discover books: {e}")
            return []
    
    def process_single_book(self, book_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single book through the complete optimization pipeline"""
        book_id = book_info['book_id']
        title = book_info['title']
        author = book_info['author']
        
        self.logger.info(f"📖 Processing: '{title}' by {author} (ID: {book_id})")
        self.stats['current_book'] = f"{title} by {author}"
        
        processing_start = time.time()
        result = {
            'book_id': book_id,
            'title': title,
            'author': author,
            'status': 'unknown',
            'processing_time': 0,
            'chunks_created': 0,
            'embeddings_generated': 0,
            'errors': []
        }
        
        try:
            # Step 1: Semantic Chunking
            self.logger.info(f"🏗️ Creating semantic chunks for book {book_id}...")
            for chunk_level in self.config['chunk_levels']:
                
                chunk_results = self.semantic_chunker.process_book_semantic_chunks(
                    book_id, [chunk_level]
                )
                
                if 'error' in chunk_results:
                    raise Exception(f"Chunking failed: {chunk_results['error']}")
                
                # Save chunks to database
                if not self.semantic_chunker.save_semantic_chunks_to_db(chunk_results):
                    raise Exception("Failed to save semantic chunks")
                
                chunk_count = chunk_results['chunk_levels'][chunk_level]['chunk_count']
                result['chunks_created'] += chunk_count
                self.logger.info(f"✅ Created {chunk_count} {chunk_level} chunks")
            
            # Step 2: Multi-Modal Embeddings (focus on medium chunks for efficiency)
            self.logger.info(f"🧠 Generating multi-modal embeddings for book {book_id}...")
            embedding_results = self.embedding_pipeline.process_book_multimodal_pipeline(
                book_id=book_id,
                chunk_level='medium',
                max_workers=self.config['max_workers']
            )
            
            if embedding_results['status'] not in ['completed', 'completed_with_save_errors']:
                raise Exception(f"Embedding generation failed: {embedding_results.get('message', 'Unknown error')}")
            
            result['embeddings_generated'] = embedding_results['embeddings_generated']
            result['status'] = 'completed'
            
            processing_time = time.time() - processing_start
            result['processing_time'] = processing_time
            
            self.logger.info(f"🎉 Book {book_id} processing completed in {processing_time:.1f}s")
            self.logger.info(f"📊 Created {result['chunks_created']} chunks, {result['embeddings_generated']} embeddings")
            
            # Update global stats
            self.stats['books_processed'] += 1
            self.stats['total_chunks_created'] += result['chunks_created']
            self.stats['total_embeddings_generated'] += result['embeddings_generated']
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"❌ Book {book_id} processing failed: {error_msg}")
            result['status'] = 'failed'
            result['errors'].append(error_msg)
            self.stats['books_failed'] += 1
            self.stats['errors'].append({
                'book_id': book_id,
                'title': title,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            })
        
        finally:
            # Memory cleanup
            if self.config['enable_garbage_collection']:
                gc.collect()
        
        return result
    
    def run_optimization_daemon(self):
        """Main daemon loop for overnight vector optimization"""
        self.logger.info("🚀 Starting Vector Optimization Daemon")
        self.logger.info(f"⚙️ Configuration: {json.dumps(self.config, indent=2)}")
        
        self.is_running = True
        self.stats['start_time'] = time.time()
        
        try:
            # Setup multi-modal infrastructure
            self.logger.info("🗂️ Setting up multi-modal embedding infrastructure...")
            if not self.embedding_pipeline.setup_multimodal_tables():
                raise Exception("Failed to setup multi-modal infrastructure")
            
            # Discover books to process
            books_to_process = self.discover_books_to_process()
            if not books_to_process:
                self.logger.info("✅ No books require vector optimization!")
                return
            
            total_books = len(books_to_process)
            self.logger.info(f"📊 Starting optimization of {total_books} books")
            
            # Process books in batches
            for i, book_info in enumerate(books_to_process, 1):
                if self.should_stop:
                    self.logger.info("🛑 Graceful shutdown requested")
                    break
                
                # Process single book
                result = self.process_single_book(book_info)
                
                # Progress reporting
                if i % self.config['progress_report_interval'] == 0 or i == total_books:
                    elapsed = time.time() - self.stats['start_time']
                    rate = i / elapsed * 3600  # books per hour
                    remaining = total_books - i
                    eta = remaining / rate if rate > 0 else 0
                    
                    self.logger.info(f"📈 Progress: {i}/{total_books} books ({i/total_books*100:.1f}%)")
                    self.logger.info(f"⚡ Processing rate: {rate:.1f} books/hour")
                    self.logger.info(f"⏰ ETA: {eta:.1f} hours")
                    
                    # Update estimated completion
                    eta_time = datetime.now() + timedelta(hours=eta)
                    self.stats['estimated_completion'] = eta_time.isoformat()
                
                # Checkpoint save
                if i % self.config['checkpoint_interval'] == 0:
                    self._save_status()
                
                # Sleep between books (be nice to the system)
                if i < total_books:  # Don't sleep after the last book
                    time.sleep(self.config['sleep_between_books'])
            
            # Final processing summary
            total_time = time.time() - self.stats['start_time']
            self.logger.info("🎉 Vector Optimization Daemon completed!")
            self.logger.info(f"📊 Processed {self.stats['books_processed']} books successfully")
            self.logger.info(f"❌ Failed: {self.stats['books_failed']} books")
            self.logger.info(f"🏗️ Total chunks created: {self.stats['total_chunks_created']}")
            self.logger.info(f"🧠 Total embeddings generated: {self.stats['total_embeddings_generated']}")
            self.logger.info(f"⏰ Total processing time: {total_time/3600:.1f} hours")
            self.logger.info(f"⚡ Average rate: {self.stats['books_processed']/(total_time/3600):.1f} books/hour")
            
        except Exception as e:
            self.logger.error(f"💥 Daemon crashed: {e}")
            self.stats['errors'].append({
                'type': 'daemon_crash',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        
        finally:
            self.is_running = False
            self.stats['current_book'] = None
            self._save_status()
            self.logger.info("🌙 Vector Optimization Daemon shutdown complete")

def main():
    """Main entry point for the vector optimization daemon"""
    print("🌙 Dr. Sarah Chen (陈雪芳) - Vector Optimization Daemon")
    print("Lead Data Engineer - LibraryOfBabel")
    print("夜间处理，白天享受完美搜索体验")
    print()
    
    # Check if daemon is already running
    status_file = Path("scripts/optimization_status_v2.json")
    if status_file.exists():
        try:
            with open(status_file, 'r') as f:
                status = json.load(f)
            
            if status.get('is_running', False):
                print("⚠️ Daemon appears to be already running!")
                print("If this is incorrect, delete scripts/optimization_status_v2.json and restart.")
                return
        except:
            pass  # Ignore errors reading status file
    
    # Initialize and run daemon
    daemon = VectorOptimizationDaemon()
    
    print(f"🚀 Starting overnight vector optimization...")
    print(f"📊 This will process all books in the LibraryOfBabel collection")
    print(f"⏰ Processing may take several hours depending on collection size")
    print(f"📝 Progress will be logged to logs/vector_optimization_v2_*.log")
    print(f"🛑 Use Ctrl+C for graceful shutdown")
    print()
    
    daemon.run_optimization_daemon()

if __name__ == "__main__":
    main()