#!/usr/bin/env python3
"""
Optimized Vector Embeddings for Large-Scale Libraries (100x+ current size)
High-performance batch processing with caching and parallel optimization
"""

import psycopg2
import psycopg2.extras
import requests
import json
import logging
import time
import numpy as np
from typing import List, Dict, Optional, Tuple
import os
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
import threading
import asyncio
import aiohttp
import aiopg
from dataclasses import dataclass
import pickle
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EmbeddingBatch:
    """Batch of embeddings for processing"""
    chunk_ids: List[str]
    texts: List[str]
    embeddings: List[Optional[List[float]]] = None

class OptimizedVectorGenerator:
    def __init__(self, ollama_host: str = "localhost", ollama_port: int = 11434):
        self.ollama_url = f"http://{ollama_host}:{ollama_port}/api/embeddings"
        self.model_name = "nomic-embed-text"
        
        # Database configuration
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': 5432
        }
        
        # Performance optimizations
        self.cache_dir = "/tmp/embedding_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # High-performance settings for 100x scale
        self.max_workers = 20  # Parallel embedding requests
        self.db_batch_size = 100  # Database batch insertions
        self.embedding_cache = {}  # In-memory cache
        self.cache_hits = 0
        self.cache_misses = 0
        
    def get_text_hash(self, text: str) -> str:
        """Generate hash for text caching"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def cache_embedding(self, text: str, embedding: List[float]):
        """Cache embedding to disk and memory"""
        text_hash = self.get_text_hash(text)
        
        # Memory cache
        self.embedding_cache[text_hash] = embedding
        
        # Disk cache for persistence
        cache_file = os.path.join(self.cache_dir, f"{text_hash}.pkl")
        with open(cache_file, 'wb') as f:
            pickle.dump(embedding, f)
    
    def get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Retrieve embedding from cache"""
        text_hash = self.get_text_hash(text)
        
        # Check memory cache first
        if text_hash in self.embedding_cache:
            self.cache_hits += 1
            return self.embedding_cache[text_hash]
        
        # Check disk cache
        cache_file = os.path.join(self.cache_dir, f"{text_hash}.pkl")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    embedding = pickle.load(f)
                    self.embedding_cache[text_hash] = embedding  # Load to memory
                    self.cache_hits += 1
                    return embedding
            except:
                pass
        
        self.cache_misses += 1
        return None
    
    async def generate_embedding_async(self, session: aiohttp.ClientSession, text: str) -> Optional[List[float]]:
        """Async embedding generation with caching"""
        # Check cache first
        cached = self.get_cached_embedding(text)
        if cached:
            return cached
        
        try:
            payload = {
                "model": self.model_name,
                "prompt": text[:8000]  # Truncate for API limits
            }
            
            async with session.post(self.ollama_url, json=payload, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    embedding = result.get('embedding', [])
                    if embedding:
                        self.cache_embedding(text, embedding)
                    return embedding
                else:
                    logger.error(f"Ollama API error: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Async embedding error: {e}")
            return None
    
    async def batch_generate_embeddings_async(self, texts: List[str]) -> List[Optional[List[float]]]:
        """High-performance async batch embedding generation"""
        connector = aiohttp.TCPConnector(limit=self.max_workers)
        timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes for large batches
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = [self.generate_embedding_async(session, text) for text in texts]
            return await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_large_batch_chunks(self, batch_size: int = 1000) -> List[Dict]:
        """Get large batches for high-throughput processing"""
        conn = psycopg2.connect(**self.db_config)
        conn.autocommit = True
        
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("""
                SELECT chunk_id, content, book_id, chunk_type, chapter_number
                FROM chunks 
                WHERE embedding_array IS NULL 
                ORDER BY chunk_id 
                LIMIT %s
            """, (batch_size,))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except psycopg2.Error as e:
            logger.error(f"Error fetching chunks: {e}")
            return []
        finally:
            conn.close()
    
    def batch_update_embeddings(self, chunk_embeddings: List[Tuple[str, List[float]]]):
        """High-performance batch database updates"""
        conn = psycopg2.connect(**self.db_config)
        conn.autocommit = False  # Use transactions for batch updates
        
        try:
            cursor = conn.cursor()
            
            # Prepare batch update
            update_data = [(embedding, chunk_id) for chunk_id, embedding in chunk_embeddings]
            
            cursor.executemany("""
                UPDATE chunks 
                SET embedding_array = %s 
                WHERE chunk_id = %s
            """, update_data)
            
            conn.commit()
            logger.info(f"Batch updated {len(update_data)} embeddings")
            return len(update_data)
            
        except psycopg2.Error as e:
            conn.rollback()
            logger.error(f"Batch update error: {e}")
            return 0
        finally:
            conn.close()
    
    def process_large_scale_embeddings(self, mega_batch_size: int = 1000) -> Dict[str, int]:
        """Optimized processing for 100x+ scale libraries"""
        total_processed = 0
        total_errors = 0
        batch_count = 0
        start_time = time.time()
        
        logger.info(f"🚀 Starting LARGE-SCALE embedding generation (batch size: {mega_batch_size})")
        
        while True:
            batch_count += 1
            batch_start = time.time()
            
            # Get large batch of chunks
            chunks = self.get_large_batch_chunks(mega_batch_size)
            if not chunks:
                logger.info("✅ No more chunks to process")
                break
            
            logger.info(f"📦 Processing mega-batch {batch_count} ({len(chunks)} chunks)")
            
            # Extract texts and chunk IDs
            texts = [chunk['content'] for chunk in chunks]
            chunk_ids = [chunk['chunk_id'] for chunk in chunks]
            
            # Generate embeddings asynchronously
            try:
                embeddings = asyncio.run(self.batch_generate_embeddings_async(texts))
            except Exception as e:
                logger.error(f"Async batch processing failed: {e}")
                total_errors += len(chunks)
                continue
            
            # Prepare successful embeddings for batch update
            successful_embeddings = []
            for chunk_id, embedding in zip(chunk_ids, embeddings):
                if embedding and isinstance(embedding, list) and len(embedding) > 0:
                    successful_embeddings.append((chunk_id, embedding))
                else:
                    total_errors += 1
            
            # Batch update database
            if successful_embeddings:
                updated = self.batch_update_embeddings(successful_embeddings)
                total_processed += updated
            
            batch_time = time.time() - batch_start
            rate = len(chunks) / batch_time if batch_time > 0 else 0
            
            logger.info(f"⚡ Batch {batch_count}: {len(successful_embeddings)}/{len(chunks)} success, "
                       f"{rate:.1f} chunks/sec, cache hit rate: {self.cache_hits/(self.cache_hits+self.cache_misses)*100:.1f}%")
            
            # Brief pause to prevent system overload
            time.sleep(1)
        
        total_time = time.time() - start_time
        
        logger.info(f"🎉 LARGE-SCALE embedding generation complete!")
        logger.info(f"📊 Total processed: {total_processed:,}")
        logger.info(f"❌ Total errors: {total_errors:,}")
        logger.info(f"⏱️  Total time: {total_time/3600:.2f} hours")
        logger.info(f"⚡ Average rate: {total_processed/total_time:.1f} chunks/second")
        logger.info(f"💾 Cache efficiency: {self.cache_hits/(self.cache_hits+self.cache_misses)*100:.1f}% hit rate")
        
        return {
            "total_processed": total_processed,
            "total_errors": total_errors,
            "total_time": total_time,
            "batches": batch_count - 1,
            "avg_rate": total_processed/total_time if total_time > 0 else 0
        }
    
    def estimate_completion_time(self) -> Dict:
        """Estimate completion time for remaining chunks"""
        conn = psycopg2.connect(**self.db_config)
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM chunks WHERE embedding_array IS NULL")
            remaining = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM chunks")
            total = cursor.fetchone()[0]
            
            # Estimate rate (optimistic with optimizations)
            estimated_rate = 25  # chunks/second with optimizations
            
            remaining_time = remaining / estimated_rate
            hours = remaining_time / 3600
            
            return {
                "remaining_chunks": remaining,
                "total_chunks": total,
                "estimated_rate": estimated_rate,
                "estimated_hours": round(hours, 2),
                "estimated_days": round(hours / 24, 2) if hours > 24 else 0
            }
            
        except psycopg2.Error as e:
            logger.error(f"Error estimating completion: {e}")
            return {}
        finally:
            conn.close()


def main():
    """Optimized main function for large-scale processing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LibraryOfBabel Optimized Vector Embeddings (100x Scale)")
    parser.add_argument("--generate-optimized", action="store_true", help="Generate embeddings with optimizations")
    parser.add_argument("--estimate", action="store_true", help="Estimate completion time")
    parser.add_argument("--batch-size", type=int, default=1000, help="Mega-batch size for processing")
    parser.add_argument("--clear-cache", action="store_true", help="Clear embedding cache")
    
    args = parser.parse_args()
    
    generator = OptimizedVectorGenerator()
    
    if args.clear_cache:
        import shutil
        shutil.rmtree(generator.cache_dir, ignore_errors=True)
        os.makedirs(generator.cache_dir, exist_ok=True)
        print("🗑️  Embedding cache cleared")
    
    elif args.estimate:
        estimate = generator.estimate_completion_time()
        print(f"📊 Completion Estimate:")
        print(f"   Remaining chunks: {estimate.get('remaining_chunks', 0):,}")
        print(f"   Estimated rate: {estimate.get('estimated_rate', 0)} chunks/sec")
        print(f"   Estimated time: {estimate.get('estimated_hours', 0)} hours")
        if estimate.get('estimated_days', 0) > 0:
            print(f"   Estimated days: {estimate.get('estimated_days', 0)} days")
    
    elif args.generate_optimized:
        print("🚀 Starting OPTIMIZED large-scale embedding generation...")
        results = generator.process_large_scale_embeddings(args.batch_size)
        print(f"✅ Complete! Processed {results['total_processed']:,} chunks")
        print(f"⚡ Average rate: {results['avg_rate']:.1f} chunks/second")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()