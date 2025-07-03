#!/usr/bin/env python3
"""
Vector Embeddings Generator for LibraryOfBabel
Uses Ollama's nomic-embed-text model for semantic search capabilities
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
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorEmbeddingGenerator:
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
        
        # Threading lock for database operations
        self.db_lock = threading.Lock()
        
    def get_db_connection(self):
        """Create database connection"""
        try:
            conn = psycopg2.connect(**self.db_config)
            conn.autocommit = True
            return conn
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using Ollama's nomic-embed-text model"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": text
            }
            
            response = requests.post(
                self.ollama_url,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('embedding', [])
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to Ollama failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return None
    
    def batch_generate_embeddings(self, texts: List[str], max_workers: int = 3) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts concurrently"""
        embeddings = [None] * len(texts)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {
                executor.submit(self.generate_embedding, text): i 
                for i, text in enumerate(texts)
            }
            
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    embeddings[index] = future.result()
                except Exception as e:
                    logger.error(f"Error generating embedding for text {index}: {e}")
                    embeddings[index] = None
        
        return embeddings
    
    def get_chunks_without_embeddings(self, limit: int = 100) -> List[Dict]:
        """Get chunks that don't have embeddings yet"""
        conn = self.get_db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("""
                SELECT chunk_id, content, book_id, chunk_type, chapter_number
                FROM chunks 
                WHERE embedding_array IS NULL 
                ORDER BY chunk_id 
                LIMIT %s
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except psycopg2.Error as e:
            logger.error(f"Error fetching chunks: {e}")
            return []
        finally:
            conn.close()
    
    def update_chunk_embedding(self, chunk_id: str, embedding: List[float]) -> bool:
        """Update a chunk with its embedding"""
        with self.db_lock:
            conn = self.get_db_connection()
            if not conn:
                return False
            
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE chunks 
                    SET embedding_array = %s 
                    WHERE chunk_id = %s
                """, (embedding, chunk_id))
                
                return cursor.rowcount > 0
                
            except psycopg2.Error as e:
                logger.error(f"Error updating chunk {chunk_id}: {e}")
                return False
            finally:
                conn.close()
    
    def process_chunks_batch(self, batch_size: int = 20) -> Dict[str, int]:
        """Process a batch of chunks for embedding generation"""
        chunks = self.get_chunks_without_embeddings(batch_size)
        if not chunks:
            return {"processed": 0, "errors": 0}
        
        logger.info(f"Processing batch of {len(chunks)} chunks...")
        
        # Extract text content
        texts = []
        for chunk in chunks:
            content = chunk['content']
            # Truncate very long content to avoid API limits
            if len(content) > 8000:
                content = content[:8000] + "..."
            texts.append(content)
        
        # Generate embeddings
        embeddings = self.batch_generate_embeddings(texts, max_workers=3)
        
        # Update database
        processed = 0
        errors = 0
        
        for chunk, embedding in zip(chunks, embeddings):
            if embedding and len(embedding) > 0:
                if self.update_chunk_embedding(chunk['chunk_id'], embedding):
                    processed += 1
                else:
                    errors += 1
            else:
                errors += 1
        
        logger.info(f"Batch complete: {processed} processed, {errors} errors")
        return {"processed": processed, "errors": errors}
    
    def process_all_chunks(self, batch_size: int = 20) -> Dict[str, int]:
        """Process all chunks without embeddings"""
        total_processed = 0
        total_errors = 0
        batch_count = 0
        
        logger.info("Starting vector embedding generation for all chunks...")
        start_time = time.time()
        
        while True:
            batch_count += 1
            logger.info(f"Processing batch {batch_count}...")
            
            results = self.process_chunks_batch(batch_size)
            processed = results["processed"]
            errors = results["errors"]
            
            total_processed += processed
            total_errors += errors
            
            if processed == 0:
                logger.info("No more chunks to process")
                break
            
            # Small delay between batches to avoid overwhelming Ollama
            time.sleep(1)
        
        total_time = time.time() - start_time
        
        logger.info(f"Embedding generation complete!")
        logger.info(f"Total processed: {total_processed}")
        logger.info(f"Total errors: {total_errors}")
        logger.info(f"Total time: {total_time:.2f} seconds")
        logger.info(f"Average time per chunk: {total_time/max(total_processed, 1):.2f} seconds")
        
        return {
            "total_processed": total_processed,
            "total_errors": total_errors,
            "total_time": total_time,
            "batches": batch_count - 1
        }
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm_vec1 = np.linalg.norm(vec1)
            norm_vec2 = np.linalg.norm(vec2)
            
            if norm_vec1 == 0 or norm_vec2 == 0:
                return 0.0
            
            return dot_product / (norm_vec1 * norm_vec2)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def semantic_search(self, query: str, limit: int = 10, similarity_threshold: float = 0.1) -> List[Dict]:
        """Perform semantic search using vector embeddings"""
        # Generate embedding for query
        query_embedding = self.generate_embedding(query)
        if not query_embedding:
            logger.error("Failed to generate embedding for query")
            return []
        
        # Get all chunks with embeddings
        conn = self.get_db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("""
                SELECT 
                    c.chunk_id, c.content, c.embedding_array, c.chunk_type, c.chapter_number,
                    b.title, b.author, b.publication_year
                FROM chunks c
                JOIN books b ON c.book_id = b.book_id
                WHERE c.embedding_array IS NOT NULL
            """)
            
            chunks = cursor.fetchall()
            logger.info(f"Found {len(chunks)} chunks with embeddings")
            
            # Calculate similarities
            results = []
            for chunk in chunks:
                similarity = self.cosine_similarity(query_embedding, chunk['embedding_array'])
                
                if similarity >= similarity_threshold:
                    result = {
                        'chunk_id': chunk['chunk_id'],
                        'title': chunk['title'],
                        'author': chunk['author'],
                        'publication_year': chunk['publication_year'],
                        'chunk_type': chunk['chunk_type'],
                        'chapter_number': chunk['chapter_number'],
                        'content_preview': chunk['content'][:300] + "..." if len(chunk['content']) > 300 else chunk['content'],
                        'similarity_score': round(similarity, 4)
                    }
                    results.append(result)
            
            # Sort by similarity score (highest first)
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return results[:limit]
            
        except psycopg2.Error as e:
            logger.error(f"Error performing semantic search: {e}")
            return []
        finally:
            conn.close()
    
    def get_embedding_stats(self) -> Dict:
        """Get statistics about embeddings in the database"""
        conn = self.get_db_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM chunks")
            total_chunks = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM chunks WHERE embedding_array IS NOT NULL")
            embedded_chunks = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM chunks WHERE embedding_array IS NULL")
            pending_chunks = cursor.fetchone()[0]
            
            return {
                "total_chunks": total_chunks,
                "embedded_chunks": embedded_chunks,
                "pending_chunks": pending_chunks,
                "completion_percentage": round((embedded_chunks / max(total_chunks, 1)) * 100, 2)
            }
            
        except psycopg2.Error as e:
            logger.error(f"Error getting embedding stats: {e}")
            return {}
        finally:
            conn.close()


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LibraryOfBabel Vector Embeddings Generator")
    parser.add_argument("--generate", action="store_true", help="Generate embeddings for all chunks")
    parser.add_argument("--search", type=str, help="Perform semantic search with query")
    parser.add_argument("--stats", action="store_true", help="Show embedding statistics")
    parser.add_argument("--batch-size", type=int, default=20, help="Batch size for processing")
    parser.add_argument("--limit", type=int, default=10, help="Number of search results")
    
    args = parser.parse_args()
    
    generator = VectorEmbeddingGenerator()
    
    if args.stats:
        stats = generator.get_embedding_stats()
        print(f"📊 Embedding Statistics:")
        print(f"   Total chunks: {stats.get('total_chunks', 0)}")
        print(f"   Embedded: {stats.get('embedded_chunks', 0)}")
        print(f"   Pending: {stats.get('pending_chunks', 0)}")
        print(f"   Completion: {stats.get('completion_percentage', 0)}%")
    
    elif args.generate:
        print("🚀 Starting embedding generation...")
        results = generator.process_all_chunks(args.batch_size)
        print(f"✅ Complete! Processed {results['total_processed']} chunks in {results['total_time']:.2f}s")
    
    elif args.search:
        print(f"🔍 Searching for: {args.search}")
        results = generator.semantic_search(args.search, args.limit)
        
        if results:
            print(f"\n📚 Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result['title']} by {result['author']}")
                print(f"   Similarity: {result['similarity_score']}")
                print(f"   Type: {result['chunk_type']}")
                print(f"   Preview: {result['content_preview'][:200]}...")
        else:
            print("No results found")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()