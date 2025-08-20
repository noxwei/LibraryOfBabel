#!/usr/bin/env python3
"""
Multi-Ollama BGE-M3 Load Balanced Daemon
========================================

Load balances across multiple Ollama instances for maximum throughput.
Uses round-robin distribution across ports 11434, 11435, 11436.

Dr. Sarah Chen (陈雪芳) - PostgreSQL-First Architecture
"""

import sys
import json
import time
import signal
import requests
import psycopg2
import psycopg2.extras
import threading
import queue
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import os
import itertools

class MultiOllamaEmbeddingDaemon:
    def __init__(self, initial_workers: int = 36):
        self.db_config = {
            'host': 'localhost',
            'database': 'knowledge_base',
            'user': 'weixiangzhang', 
            'port': 5432
        }
        
        # Multiple Ollama instances for load balancing
        self.ollama_urls = [
            "http://localhost:11434",
            "http://localhost:11435", 
            "http://localhost:11436"
        ]
        self.url_pool = itertools.cycle(self.ollama_urls)
        self.model_name = "bge-m3"
        
        # Threading configuration
        self.initial_workers = initial_workers
        self.current_workers = initial_workers
        self.max_workers = 50  # Higher with multiple Ollama instances
        self.worker_executor = None
        
        # Performance monitoring
        self.max_content_length = 8000
        self.batch_queue = queue.Queue(maxsize=2000)
        self.results_queue = queue.Queue()
        
        # Statistics tracking
        self.start_time = datetime.now()
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
        self.total_processing_time = 0
        self.last_stats_time = time.time()
        self.last_processed_count = 0
        
        # Load balancing stats
        self.url_stats = {url: {'requests': 0, 'successes': 0, 'errors': 0, 'avg_time': 0} 
                         for url in self.ollama_urls}
        
        # Control flags
        self.should_stop = False
        self.pause_processing = False
        
        # System monitoring
        self.cpu_threshold = 95  # Higher threshold with multiple instances
        self.memory_threshold = 90
        
        # Daemon management
        self.pid_file = "multi_ollama_bge_daemon.pid"
        self.stats_file = "multi_ollama_bge_stats.json"
        
        # Signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        self.should_stop = True
    
    def write_pid_file(self):
        """Write daemon PID to file"""
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
        except Exception as e:
            print(f"⚠️  Warning: Could not write PID file: {e}")
    
    def get_next_ollama_url(self) -> str:
        """Get next Ollama URL using round-robin"""
        return next(self.url_pool)
    
    def get_db_connection(self):
        """Get database connection with proper isolation"""
        return psycopg2.connect(**self.db_config)
    
    def get_passage_chunks_batch(self, batch_size: int = 100) -> List[Tuple[str, int, str]]:
        """Get batch of passage-level chunks missing BGE embeddings"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    
                    cur.execute("""
                        SELECT c.chunk_id, c.book_id, c.content
                        FROM chunks c
                        LEFT JOIN chunk_embeddings ce ON c.chunk_id = ce.chunk_id 
                            AND ce.embedding_model = 'bge-m3'
                        WHERE ce.chunk_id IS NULL
                            AND c.content IS NOT NULL
                            AND c.chunk_type IN ('paragraph', 'section')
                            AND LENGTH(c.content) BETWEEN 100 AND %s
                            AND c.word_count BETWEEN 50 AND 2000
                        ORDER BY c.word_count ASC, c.chunk_id
                        LIMIT %s
                    """, (self.max_content_length, batch_size))
                    
                    results = cur.fetchall()
                    return [(row['chunk_id'], row['book_id'], row['content']) for row in results]
                    
        except Exception as e:
            print(f"❌ Database batch error: {e}")
            return []
    
    def worker_process_chunk(self, chunk_data: Tuple[str, int, str]) -> Dict:
        """Worker function to process a single chunk with load balancing"""
        chunk_id, book_id, content = chunk_data
        worker_id = threading.current_thread().name
        
        # Get next Ollama URL for load balancing
        ollama_url = self.get_next_ollama_url()
        
        try:
            # Truncate content if needed
            if len(content) > self.max_content_length:
                content = content[:self.max_content_length]
            
            start_time = time.time()
            
            # Generate embedding with selected Ollama instance
            response = requests.post(
                f"{ollama_url}/api/embeddings",
                json={
                    "model": self.model_name,
                    "prompt": content
                },
                timeout=30
            )
            
            processing_time = time.time() - start_time
            
            # Update URL stats
            self.url_stats[ollama_url]['requests'] += 1
            
            if response.status_code == 200:
                result = response.json()
                embedding = result.get('embedding', [])
                
                if embedding:
                    # Save to database
                    if self.save_embedding(chunk_id, book_id, embedding):
                        self.url_stats[ollama_url]['successes'] += 1
                        self.url_stats[ollama_url]['avg_time'] = (
                            (self.url_stats[ollama_url]['avg_time'] * 
                             (self.url_stats[ollama_url]['successes'] - 1) + processing_time) /
                            self.url_stats[ollama_url]['successes']
                        )
                        
                        return {
                            'success': True,
                            'chunk_id': chunk_id,
                            'book_id': book_id,
                            'processing_time': processing_time,
                            'embedding_dims': len(embedding),
                            'worker_id': worker_id,
                            'ollama_url': ollama_url
                        }
                    else:
                        self.url_stats[ollama_url]['errors'] += 1
                        return {
                            'success': False,
                            'error': 'Database save failed',
                            'chunk_id': chunk_id,
                            'processing_time': processing_time,
                            'worker_id': worker_id,
                            'ollama_url': ollama_url
                        }
                else:
                    self.url_stats[ollama_url]['errors'] += 1
                    return {
                        'success': False,
                        'error': 'Empty embedding returned',
                        'chunk_id': chunk_id,
                        'processing_time': processing_time,
                        'worker_id': worker_id,
                        'ollama_url': ollama_url
                    }
            else:
                self.url_stats[ollama_url]['errors'] += 1
                return {
                    'success': False,
                    'error': f'Ollama error: {response.status_code}',
                    'chunk_id': chunk_id,
                    'processing_time': processing_time,
                    'worker_id': worker_id,
                    'ollama_url': ollama_url
                }
                
        except Exception as e:
            self.url_stats[ollama_url]['errors'] += 1
            return {
                'success': False,
                'error': str(e),
                'chunk_id': chunk_id,
                'processing_time': 0,
                'worker_id': worker_id,
                'ollama_url': ollama_url
            }
    
    def save_embedding(self, chunk_id: str, book_id: int, embedding: List[float]) -> bool:
        """Save embedding to database with proper error handling"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    
                    vector_str = f"[{','.join(map(str, embedding))}]"
                    
                    cur.execute("""
                        INSERT INTO chunk_embeddings 
                        (chunk_id, book_id, embedding_model, embedding_dimension, embedding_vector_bge)
                        VALUES (%s, %s, %s, %s, %s::vector)
                        ON CONFLICT (chunk_id, embedding_model) 
                        DO UPDATE SET 
                            embedding_vector_bge = EXCLUDED.embedding_vector_bge,
                            embedding_dimension = EXCLUDED.embedding_dimension,
                            created_at = NOW()
                    """, (chunk_id, book_id, 'bge-m3', len(embedding), vector_str))
                    
                conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ Save error for {chunk_id}: {e}")
            return False
    
    def print_status_update(self):
        """Print comprehensive status update with load balancing stats"""
        current_time = time.time()
        elapsed_time = current_time - time.mktime(self.start_time.timetuple())
        
        current_rate = (self.processed_count / elapsed_time * 3600) if elapsed_time > 0 else 0
        success_rate = (self.success_count / self.processed_count * 100) if self.processed_count > 0 else 0
        
        print(f"\n🚀 MULTI-OLLAMA BGE-M3 DAEMON STATUS")
        print(f"{'='*70}")
        print(f"⏱️  Uptime: {elapsed_time:.1f}s")
        print(f"👥 Workers: {self.current_workers}/{self.max_workers}")
        print(f"📈 Processed: {self.processed_count:,} ({self.success_count:,} success, {self.error_count:,} failed)")
        print(f"✅ Success Rate: {success_rate:.1f}%")
        print(f"🔥 Current Rate: {current_rate:.0f}/hour")
        
        print(f"\n🔄 Load Balancer Stats:")
        for url, stats in self.url_stats.items():
            port = url.split(':')[-1]
            success_rate = (stats['successes'] / stats['requests'] * 100) if stats['requests'] > 0 else 0
            print(f"   Port {port}: {stats['requests']} reqs | {success_rate:.1f}% success | {stats['avg_time']:.2f}s avg")
        
        print(f"{'='*70}")
    
    def run_daemon(self):
        """Main daemon loop with load balancing"""
        print("🚀 MULTI-OLLAMA BGE-M3 LOAD BALANCED DAEMON STARTING")
        print("=" * 80)
        print(f"🎯 Target: Passage-level chunks (paragraphs + sections)")
        print(f"🔄 Ollama Instances: {len(self.ollama_urls)} ({', '.join([url.split('://')[-1] for url in self.ollama_urls])})")
        print(f"👥 Initial Workers: {self.initial_workers}")
        print(f"📏 Max Workers: {self.max_workers}")
        print()
        
        self.write_pid_file()
        
        # Initialize worker pool
        self.worker_executor = ThreadPoolExecutor(max_workers=self.current_workers, thread_name_prefix="BGE-LB-Worker")
        
        last_status_update = time.time()
        status_interval = 30  # seconds
        
        try:
            while not self.should_stop:
                # Get larger batch since we have multiple Ollama instances
                chunk_batch = self.get_passage_chunks_batch(self.current_workers * 6)
                
                if not chunk_batch:
                    print("🎉 No more passage chunks to process! Daemon completed successfully.")
                    break
                
                # Submit work to thread pool
                if not self.worker_executor:
                    print("❌ Worker executor not initialized")
                    break
                
                future_to_chunk = {}
                for chunk_data in chunk_batch:
                    if self.should_stop:
                        break
                    
                    future = self.worker_executor.submit(self.worker_process_chunk, chunk_data)
                    future_to_chunk[future] = chunk_data[0]  # chunk_id
                
                # Process completed work
                for future in as_completed(future_to_chunk):
                    if self.should_stop:
                        break
                    
                    chunk_id = future_to_chunk[future]
                    try:
                        result = future.result()
                        
                        self.processed_count += 1
                        
                        if result['success']:
                            self.success_count += 1
                        else:
                            self.error_count += 1
                            print(f"❌ {chunk_id} [{result.get('ollama_url', 'unknown')}]: {result.get('error', 'Unknown error')}")
                        
                        self.total_processing_time += result.get('processing_time', 0)
                        
                    except Exception as e:
                        self.error_count += 1
                        print(f"❌ {chunk_id}: Future exception: {e}")
                
                # Status updates
                current_time = time.time()
                if current_time - last_status_update >= status_interval:
                    self.print_status_update()
                    last_status_update = current_time
                
                # Brief pause to prevent overwhelming
                time.sleep(0.05)  # Shorter pause with multiple instances
        
        except KeyboardInterrupt:
            print("\n🛑 Keyboard interrupt received")
        except Exception as e:
            print(f"\n❌ Daemon error: {e}")
        finally:
            # Cleanup
            print("\n🔄 Shutting down daemon...")
            if self.worker_executor:
                self.worker_executor.shutdown(wait=True)
            
            self.print_status_update()
            
            try:
                os.remove(self.pid_file)
            except:
                pass
            
            print("✅ Multi-Ollama BGE-M3 daemon shutdown complete")

def main():
    if len(sys.argv) > 1:
        try:
            initial_workers = int(sys.argv[1])
            if initial_workers < 1 or initial_workers > 50:
                raise ValueError("Workers must be between 1 and 50")
        except ValueError as e:
            print(f"❌ Invalid worker count: {e}")
            print("Usage: python3 multi_ollama_bge_daemon.py [initial_workers]")
            sys.exit(1)
    else:
        initial_workers = 36
    
    daemon = MultiOllamaEmbeddingDaemon(initial_workers)
    daemon.run_daemon()

if __name__ == "__main__":
    main()