#!/usr/bin/env python3
"""
🏛️ Multi-Modal Embedding Pipeline - Dr. Sarah Chen Implementation
=================================================================

Advanced multi-modal embedding system for LibraryOfBabel that creates
specialized embeddings for different semantic aspects:

1. Semantic Embeddings: General meaning and context
2. Factual Embeddings: Facts, data, specific information  
3. Topical Embeddings: Subject areas and themes
4. Stylistic Embeddings: Writing style and genre
5. Temporal Embeddings: Time periods and historical context

Lead: Dr. Sarah Chen (陈雪芳) - Lead Data Engineer
Philosophy: "多维度向量表示提供最佳搜索体验"
(Multi-dimensional vector representation provides optimal search experience)
"""

import os
import json
import time
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import logging
from pathlib import Path
import hashlib
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Simulated embedding service (replace with actual service)
class EmbeddingService:
    """
    Dr. Chen's embedding service interface.
    In production, this would connect to OpenAI, Cohere, or local models.
    """
    
    def __init__(self):
        self.embedding_dim = 1536  # Standard dimension
        
    def generate_semantic_embedding(self, text: str) -> List[float]:
        """Generate semantic embedding focused on meaning and context"""
        # Simulate embedding generation with consistent hash-based vectors
        hash_obj = hashlib.md5(f"semantic_{text}".encode())
        seed = int(hash_obj.hexdigest()[:8], 16)
        np.random.seed(seed)
        embedding = np.random.normal(0, 1, self.embedding_dim)
        return embedding / np.linalg.norm(embedding)  # Normalize
    
    def generate_factual_embedding(self, text: str) -> List[float]:
        """Generate factual embedding focused on facts and specific information"""
        hash_obj = hashlib.md5(f"factual_{text}".encode())
        seed = int(hash_obj.hexdigest()[:8], 16)
        np.random.seed(seed)
        embedding = np.random.normal(0, 1, self.embedding_dim)
        return embedding / np.linalg.norm(embedding)
    
    def generate_topical_embedding(self, text: str) -> List[float]:
        """Generate topical embedding focused on subject areas and themes"""
        hash_obj = hashlib.md5(f"topical_{text}".encode())
        seed = int(hash_obj.hexdigest()[:8], 16)
        np.random.seed(seed)
        embedding = np.random.normal(0, 1, self.embedding_dim)
        return embedding / np.linalg.norm(embedding)
    
    def generate_stylistic_embedding(self, text: str) -> List[float]:
        """Generate stylistic embedding focused on writing style and genre"""
        hash_obj = hashlib.md5(f"stylistic_{text}".encode())
        seed = int(hash_obj.hexdigest()[:8], 16)
        np.random.seed(seed)
        embedding = np.random.normal(0, 1, self.embedding_dim)
        return embedding / np.linalg.norm(embedding)
    
    def generate_temporal_embedding(self, text: str) -> List[float]:
        """Generate temporal embedding focused on time periods and historical context"""
        hash_obj = hashlib.md5(f"temporal_{text}".encode())
        seed = int(hash_obj.hexdigest()[:8], 16)
        np.random.seed(seed)
        embedding = np.random.normal(0, 1, self.embedding_dim)
        return embedding / np.linalg.norm(embedding)

class MultiModalEmbeddingPipeline:
    """
    Dr. Sarah Chen's Multi-Modal Embedding Pipeline.
    
    Creates specialized embeddings for different semantic aspects
    to enable ultra-precise search and retrieval.
    """
    
    def __init__(self, db_config: Dict[str, Any] = None):
        # Database configuration
        self.db_config = db_config or {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': int(os.getenv('DB_PORT', 5432))
        }
        
        # Initialize embedding service
        self.embedding_service = EmbeddingService()
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - 陈雪芳 - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.stats = {
            'chunks_processed': 0,
            'embeddings_generated': 0,
            'start_time': None,
            'errors': 0
        }
        
        self.logger.info("🏛️ Dr. Sarah Chen's Multi-Modal Embedding Pipeline initialized")
        self.logger.info("多维度向量表示提供最佳搜索体验")
    
    def setup_multimodal_tables(self) -> bool:
        """Create specialized embedding tables for each modality"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    
                    self.logger.info("🗂️ Creating multi-modal embedding tables...")
                    
                    # Create specialized embedding tables
                    embedding_tables = [
                        'semantic_embeddings',
                        'factual_embeddings', 
                        'topical_embeddings',
                        'stylistic_embeddings',
                        'temporal_embeddings'
                    ]
                    
                    for table_name in embedding_tables:
                        cur.execute(f"""
                            CREATE TABLE IF NOT EXISTS {table_name} (
                                chunk_id VARCHAR(255) PRIMARY KEY,
                                book_id INTEGER,
                                chunk_level VARCHAR(20),
                                embedding vector(1536),
                                confidence_score FLOAT DEFAULT 1.0,
                                processing_timestamp TIMESTAMP DEFAULT NOW(),
                                
                                FOREIGN KEY (chunk_id) REFERENCES semantic_chunks(chunk_id)
                            );
                            
                            -- High-performance HNSW index for vector similarity
                            CREATE INDEX IF NOT EXISTS idx_{table_name}_hnsw 
                                ON {table_name} USING hnsw (embedding vector_cosine_ops)
                                WITH (m = 16, ef_construction = 64);
                                
                            -- Additional indexes
                            CREATE INDEX IF NOT EXISTS idx_{table_name}_book_id 
                                ON {table_name}(book_id);
                            CREATE INDEX IF NOT EXISTS idx_{table_name}_chunk_level 
                                ON {table_name}(chunk_level);
                        """)
                    
                    # Create multi-modal search function
                    cur.execute("""
                        CREATE OR REPLACE FUNCTION multimodal_search(
                            query_semantic vector(1536),
                            query_factual vector(1536),
                            query_topical vector(1536),
                            query_stylistic vector(1536),
                            query_temporal vector(1536),
                            semantic_weight FLOAT DEFAULT 0.4,
                            factual_weight FLOAT DEFAULT 0.25,
                            topical_weight FLOAT DEFAULT 0.15,
                            stylistic_weight FLOAT DEFAULT 0.1,
                            temporal_weight FLOAT DEFAULT 0.1,
                            result_limit INTEGER DEFAULT 10
                        ) RETURNS TABLE (
                            chunk_id VARCHAR(255),
                            book_id INTEGER,
                            chunk_level VARCHAR(20),
                            combined_score FLOAT,
                            semantic_score FLOAT,
                            factual_score FLOAT,
                            topical_score FLOAT,
                            stylistic_score FLOAT,
                            temporal_score FLOAT
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT 
                                sc.chunk_id,
                                sc.book_id,
                                sc.chunk_level,
                                (
                                    semantic_weight * (1 - (se.embedding <=> query_semantic)) +
                                    factual_weight * (1 - (fe.embedding <=> query_factual)) +
                                    topical_weight * (1 - (te.embedding <=> query_topical)) +
                                    stylistic_weight * (1 - (stle.embedding <=> query_stylistic)) +
                                    temporal_weight * (1 - (tmpe.embedding <=> query_temporal))
                                ) as combined_score,
                                (1 - (se.embedding <=> query_semantic)) as semantic_score,
                                (1 - (fe.embedding <=> query_factual)) as factual_score,
                                (1 - (te.embedding <=> query_topical)) as topical_score,
                                (1 - (stle.embedding <=> query_stylistic)) as stylistic_score,
                                (1 - (tmpe.embedding <=> query_temporal)) as temporal_score
                            FROM semantic_chunks sc
                            JOIN semantic_embeddings se ON sc.chunk_id = se.chunk_id
                            JOIN factual_embeddings fe ON sc.chunk_id = fe.chunk_id
                            JOIN topical_embeddings te ON sc.chunk_id = te.chunk_id
                            JOIN stylistic_embeddings stle ON sc.chunk_id = stle.chunk_id
                            JOIN temporal_embeddings tmpe ON sc.chunk_id = tmpe.chunk_id
                            ORDER BY combined_score DESC
                            LIMIT result_limit;
                        END;
                        $$ LANGUAGE plpgsql;
                    """)
                    
                    conn.commit()
                    self.logger.info("✅ Multi-modal embedding infrastructure ready!")
                    return True
                    
        except Exception as e:
            self.logger.error(f"❌ Failed to setup multi-modal tables: {e}")
            return False
    
    def process_chunk_multimodal_embeddings(self, chunk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single chunk to generate all embedding modalities"""
        
        chunk_id = chunk_data['chunk_id']
        content = chunk_data['content']
        
        try:
            # Generate all embedding modalities
            embeddings = {
                'semantic': self.embedding_service.generate_semantic_embedding(content),
                'factual': self.embedding_service.generate_factual_embedding(content),
                'topical': self.embedding_service.generate_topical_embedding(content),
                'stylistic': self.embedding_service.generate_stylistic_embedding(content),
                'temporal': self.embedding_service.generate_temporal_embedding(content)
            }
            
            with self.lock:
                self.stats['chunks_processed'] += 1
                self.stats['embeddings_generated'] += len(embeddings)
            
            return {
                'chunk_id': chunk_id,
                'book_id': chunk_data['book_id'],
                'chunk_level': chunk_data['chunk_level'],
                'embeddings': embeddings,
                'status': 'success'
            }
            
        except Exception as e:
            with self.lock:
                self.stats['errors'] += 1
            
            self.logger.error(f"❌ Failed to process chunk {chunk_id}: {e}")
            return {
                'chunk_id': chunk_id,
                'status': 'error',
                'error': str(e)
            }
    
    def save_multimodal_embeddings(self, embedding_results: List[Dict[str, Any]]) -> bool:
        """Save multi-modal embeddings to specialized tables"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    
                    successful_saves = 0
                    
                    for result in embedding_results:
                        if result['status'] != 'success':
                            continue
                        
                        chunk_id = result['chunk_id']
                        book_id = result['book_id']
                        chunk_level = result['chunk_level']
                        embeddings = result['embeddings']
                        
                        # Save each embedding modality
                        for modality, embedding_vector in embeddings.items():
                            table_name = f"{modality}_embeddings"
                            
                            cur.execute(f"""
                                INSERT INTO {table_name} 
                                (chunk_id, book_id, chunk_level, embedding)
                                VALUES (%s, %s, %s, %s)
                                ON CONFLICT (chunk_id) DO UPDATE SET
                                embedding = EXCLUDED.embedding,
                                processing_timestamp = NOW()
                            """, (
                                chunk_id, book_id, chunk_level, 
                                embedding_vector.tolist()
                            ))
                        
                        successful_saves += 1
                    
                    conn.commit()
                    self.logger.info(f"✅ Saved multi-modal embeddings for {successful_saves} chunks")
                    return True
                    
        except Exception as e:
            self.logger.error(f"❌ Failed to save multi-modal embeddings: {e}")
            return False
    
    def process_book_multimodal_pipeline(self, book_id: int, 
                                       chunk_level: str = 'medium',
                                       max_workers: int = 4) -> Dict[str, Any]:
        """Process all chunks of a book through the multi-modal pipeline"""
        
        self.logger.info(f"🏛️ Starting multi-modal processing for book {book_id}")
        self.stats['start_time'] = time.time()
        
        # Get semantic chunks for the book
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT chunk_id, book_id, content, chunk_level, char_count
                        FROM semantic_chunks 
                        WHERE book_id = %s AND chunk_level = %s
                        ORDER BY chunk_index
                    """, (book_id, chunk_level))
                    
                    chunks = cur.fetchall()
                    
                    if not chunks:
                        return {
                            'status': 'error',
                            'message': f'No {chunk_level} chunks found for book {book_id}'
                        }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Database error: {e}'
            }
        
        self.logger.info(f"📊 Processing {len(chunks)} {chunk_level} chunks with {max_workers} workers")
        
        # Process chunks in parallel
        embedding_results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all chunks for processing
            future_to_chunk = {
                executor.submit(self.process_chunk_multimodal_embeddings, dict(chunk)): chunk
                for chunk in chunks
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_chunk):
                chunk = future_to_chunk[future]
                try:
                    result = future.result()
                    embedding_results.append(result)
                    
                    # Progress logging
                    if len(embedding_results) % 100 == 0:
                        elapsed = time.time() - self.stats['start_time']
                        rate = len(embedding_results) / elapsed
                        self.logger.info(f"📈 Processed {len(embedding_results)}/{len(chunks)} chunks ({rate:.1f} chunks/sec)")
                        
                except Exception as e:
                    self.logger.error(f"❌ Chunk processing failed: {e}")
                    embedding_results.append({
                        'chunk_id': chunk['chunk_id'],
                        'status': 'error',
                        'error': str(e)
                    })
        
        # Save all embeddings to database
        save_success = self.save_multimodal_embeddings(embedding_results)
        
        # Generate final report
        processing_time = time.time() - self.stats['start_time']
        successful_chunks = sum(1 for r in embedding_results if r['status'] == 'success')
        
        report = {
            'book_id': book_id,
            'chunk_level': chunk_level,
            'total_chunks': len(chunks),
            'successful_chunks': successful_chunks,
            'failed_chunks': len(chunks) - successful_chunks,
            'processing_time_seconds': processing_time,
            'chunks_per_second': len(chunks) / processing_time,
            'embeddings_generated': successful_chunks * 5,  # 5 modalities per chunk
            'database_save_success': save_success,
            'status': 'completed' if save_success else 'completed_with_save_errors'
        }
        
        self.logger.info(f"🎉 Multi-modal processing complete for book {book_id}")
        self.logger.info(f"📊 {successful_chunks}/{len(chunks)} chunks processed successfully")
        self.logger.info(f"⚡ Processing rate: {report['chunks_per_second']:.1f} chunks/second")
        
        return report

def main():
    """
    Dr. Sarah Chen's multi-modal embedding pipeline demonstration
    """
    print("🏛️ Dr. Sarah Chen (陈雪芳) - Multi-Modal Embedding Pipeline")
    print("Lead Data Engineer - LibraryOfBabel")
    print("多维度向量表示提供最佳搜索体验")
    print()
    
    pipeline = MultiModalEmbeddingPipeline()
    
    # Setup infrastructure
    print("🗂️ Setting up multi-modal embedding infrastructure...")
    if not pipeline.setup_multimodal_tables():
        print("❌ Failed to setup infrastructure")
        return
    
    # Test with the same book we used for semantic chunking
    test_book_id = 1099
    
    print(f"🧠 Processing multi-modal embeddings for book {test_book_id}...")
    result = pipeline.process_book_multimodal_pipeline(
        book_id=test_book_id,
        chunk_level='medium',  # Use medium chunks for reasonable processing time
        max_workers=4
    )
    
    if result['status'] in ['completed', 'completed_with_save_errors']:
        print(f"✅ Multi-modal processing completed!")
        print(f"📊 Book {test_book_id}: {result['successful_chunks']} chunks processed")
        print(f"🧠 Generated {result['embeddings_generated']} specialized embeddings")
        print(f"⚡ Processing rate: {result['chunks_per_second']:.1f} chunks/second")
        print(f"⏱️ Total time: {result['processing_time_seconds']:.1f} seconds")
        
        if result['database_save_success']:
            print("✅ All embeddings saved to database successfully")
        else:
            print("⚠️ Some database save errors occurred")
    else:
        print(f"❌ Processing failed: {result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    main()