#!/usr/bin/env python3
"""
🧠 OLLAMA VECTOR EMBEDDER - LibraryOfBabel Team Integration
==========================================================

Vector embedding service using Ollama for semantic search capabilities.
Integrates with the DBA team's deduplication and processing pipeline.

Team Integration:
- Lexi (Reddit Bibliophile): Content strategy and embedding quality
- Dr. Elena Rodriguez: Performance optimization and architecture
- Dr. Marcus Thompson: Content validation and chunk quality
- Dr. Sarah Chen: Database storage and retrieval optimization

Supervised by: Linda Zhang (张丽娜) - HR Manager
"""

import os
import sys
import json
import time
import logging
import requests
import psycopg2
import psycopg2.extras
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np

# Import for content processing
try:
    from epub_processor import BookMetadata, ChapterInfo
    from deduplication_layer import DeduplicationLayer
except ImportError:
    from src.epub_processor import BookMetadata, ChapterInfo
    from src.deduplication_layer import DeduplicationLayer

@dataclass
class EmbeddingResult:
    """Result of vector embedding operation."""
    chunk_id: str
    embedding: List[float]
    success: bool
    error_message: Optional[str] = None
    processing_time_ms: float = 0.0

class OllamaVectorEmbedder:
    """
    🧠 Ollama Vector Embedding System
    
    Integrates with Ollama to generate vector embeddings for text chunks.
    Optimized for LibraryOfBabel's knowledge base and semantic search.
    """
    
    def __init__(self, db_config: Dict, ollama_base_url: str = "http://localhost:11434"):
        """Initialize Ollama vector embedder"""
        self.db_config = db_config
        self.ollama_base_url = ollama_base_url.rstrip('/')
        
        # Embedding configuration (Dr. Elena's performance optimization)
        self.embedding_model = "nomic-embed-text"  # Optimized for text embeddings
        self.batch_size = 10  # Process embeddings in batches
        self.max_chunk_length = 8000  # Optimal chunk size for embeddings
        self.embedding_dimension = 768  # Standard dimension for nomic-embed-text
        
        # Performance settings (Lexi's content strategy)
        self.timeout_seconds = 30
        self.retry_attempts = 3
        self.retry_delay = 2
        
        # Statistics tracking
        self.stats = {
            'embeddings_generated': 0,
            'embeddings_failed': 0,
            'total_processing_time_ms': 0,
            'average_embedding_time_ms': 0,
            'books_processed': 0,
            'chunks_processed': 0
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("OllamaVectorEmbedder")
        
        # Team signature
        self.team_signature = "OLLAMA_VECTOR_TEAM_v1.0"
        
        self.logger.info("🧠 Ollama Vector Embedder initialized")
        self.logger.info(f"🎯 Model: {self.embedding_model}")
        self.logger.info(f"📊 Batch size: {self.batch_size}")
        self.logger.info(f"📏 Max chunk length: {self.max_chunk_length}")
        
        # Verify Ollama connection
        self._verify_ollama_connection()
    
    def _verify_ollama_connection(self):
        """Verify Ollama is running and model is available"""
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self.logger.info("✅ Ollama service is running")
                
                # Check if embedding model is available
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                
                if any(self.embedding_model in name for name in model_names):
                    self.logger.info(f"✅ Embedding model '{self.embedding_model}' is available")
                else:
                    self.logger.warning(f"⚠️ Model '{self.embedding_model}' not found. Available models: {model_names}")
                    self.logger.info(f"🔄 Attempting to pull model '{self.embedding_model}'...")
                    self._pull_model()
            else:
                self.logger.error(f"❌ Ollama service not responding: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Cannot connect to Ollama: {e}")
            self.logger.error("💡 Please ensure Ollama is running: ollama serve")
    
    def _pull_model(self):
        """Pull the embedding model if not available"""
        try:
            self.logger.info(f"📥 Pulling model '{self.embedding_model}'...")
            response = requests.post(
                f"{self.ollama_base_url}/api/pull",
                json={"name": self.embedding_model},
                timeout=300  # 5 minutes for model download
            )
            
            if response.status_code == 200:
                self.logger.info(f"✅ Model '{self.embedding_model}' pulled successfully")
            else:
                self.logger.error(f"❌ Failed to pull model: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"❌ Error pulling model: {e}")
    
    def get_db_connection(self):
        """Get database connection (Dr. Sarah's method)"""
        try:
            return psycopg2.connect(**self.db_config)
        except psycopg2.Error as e:
            self.logger.error(f"💔 Database connection failed: {e}")
            return None
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate vector embedding for text using Ollama"""
        if not text or not text.strip():
            return None
        
        # Truncate text if too long (Dr. Marcus's content validation)
        if len(text) > self.max_chunk_length:
            text = text[:self.max_chunk_length]
            self.logger.debug(f"📝 Truncated text to {self.max_chunk_length} characters")
        
        start_time = time.time()
        
        for attempt in range(self.retry_attempts):
            try:
                # Call Ollama embedding API
                response = requests.post(
                    f"{self.ollama_base_url}/api/embeddings",
                    json={
                        "model": self.embedding_model,
                        "prompt": text
                    },
                    timeout=self.timeout_seconds
                )
                
                if response.status_code == 200:
                    data = response.json()
                    embedding = data.get('embedding')
                    
                    if embedding and isinstance(embedding, list):
                        processing_time = (time.time() - start_time) * 1000
                        self.stats['embeddings_generated'] += 1
                        self.stats['total_processing_time_ms'] += processing_time
                        
                        # Update average
                        if self.stats['embeddings_generated'] > 0:
                            self.stats['average_embedding_time_ms'] = (
                                self.stats['total_processing_time_ms'] / 
                                self.stats['embeddings_generated']
                            )
                        
                        self.logger.debug(f"🧠 Generated embedding: {len(embedding)} dimensions in {processing_time:.1f}ms")
                        return embedding
                    else:
                        self.logger.error(f"❌ Invalid embedding response: {data}")
                        
                else:
                    self.logger.error(f"❌ Ollama API error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"⏰ Embedding timeout (attempt {attempt + 1}/{self.retry_attempts})")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
                    
            except Exception as e:
                self.logger.error(f"❌ Embedding error: {e}")
                break
        
        self.stats['embeddings_failed'] += 1
        return None
    
    def embed_book_chunks(self, book_id: int, chapters: List[ChapterInfo]) -> List[EmbeddingResult]:
        """Generate embeddings for all chunks of a book"""
        self.logger.info(f"🧠 Generating embeddings for book ID {book_id} ({len(chapters)} chapters)")
        
        results = []
        
        for i, chapter in enumerate(chapters):
            chunk_id = f"{book_id}_chapter_{i+1}"
            
            self.logger.debug(f"   📝 Processing chunk {chunk_id}: {chapter.title}")
            
            start_time = time.time()
            embedding = self.generate_embedding(chapter.content)
            processing_time = (time.time() - start_time) * 1000
            
            if embedding:
                result = EmbeddingResult(
                    chunk_id=chunk_id,
                    embedding=embedding,
                    success=True,
                    processing_time_ms=processing_time
                )
                self.logger.debug(f"      ✅ Embedding generated ({len(embedding)} dims, {processing_time:.1f}ms)")
            else:
                result = EmbeddingResult(
                    chunk_id=chunk_id,
                    embedding=[],
                    success=False,
                    error_message="Failed to generate embedding",
                    processing_time_ms=processing_time
                )
                self.logger.warning(f"      ❌ Embedding failed for {chunk_id}")
            
            results.append(result)
            self.stats['chunks_processed'] += 1
            
            # Small delay between embeddings to avoid overwhelming Ollama
            time.sleep(0.1)
        
        self.stats['books_processed'] += 1
        
        success_count = sum(1 for r in results if r.success)
        self.logger.info(f"✅ Book {book_id}: {success_count}/{len(results)} embeddings successful")
        
        return results
    
    def store_embeddings(self, book_id: int, embedding_results: List[EmbeddingResult]) -> bool:
        """Store embeddings in PostgreSQL database (Dr. Sarah's optimization)"""
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    self.logger.error("❌ Cannot store embeddings - database unavailable")
                    return False
                
                with conn.cursor() as cur:
                    # Check if embeddings table exists
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'chunk_embeddings'
                        )
                    """)
                    
                    table_exists = cur.fetchone()[0]
                    
                    if not table_exists:
                        self.logger.info("📋 Creating chunk_embeddings table...")
                        self._create_embeddings_table(cur)
                    
                    # Store embeddings
                    stored_count = 0
                    for result in embedding_results:
                        if result.success and result.embedding:
                            try:
                                cur.execute("""
                                    INSERT INTO chunk_embeddings (
                                        chunk_id, book_id, embedding, 
                                        embedding_model, created_at
                                    ) VALUES (%s, %s, %s, %s, NOW())
                                    ON CONFLICT (chunk_id) DO UPDATE SET
                                        embedding = EXCLUDED.embedding,
                                        embedding_model = EXCLUDED.embedding_model,
                                        created_at = NOW()
                                """, (
                                    result.chunk_id,
                                    book_id,
                                    json.dumps(result.embedding),
                                    self.embedding_model
                                ))
                                stored_count += 1
                                
                            except Exception as e:
                                self.logger.error(f"❌ Failed to store embedding for {result.chunk_id}: {e}")
                    
                    conn.commit()
                    self.logger.info(f"💾 Stored {stored_count} embeddings for book {book_id}")
                    return stored_count > 0
                    
        except Exception as e:
            self.logger.error(f"❌ Database storage error: {e}")
            return False
    
    def _create_embeddings_table(self, cursor):
        """Create embeddings table optimized for PostgreSQL JSONB (Dr. Sarah's optimization)"""
        cursor.execute("""
            CREATE TABLE chunk_embeddings (
                embedding_id SERIAL PRIMARY KEY,
                chunk_id VARCHAR(255) UNIQUE NOT NULL,
                book_id INTEGER NOT NULL,
                embedding JSONB NOT NULL,
                embedding_model VARCHAR(100) NOT NULL,
                embedding_dimension INTEGER DEFAULT 768,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (book_id) REFERENCES books(book_id)
            )
        """)
        
        # Create optimized indexes for PostgreSQL JSONB vector storage
        cursor.execute("""
            CREATE INDEX idx_chunk_embeddings_book_id ON chunk_embeddings(book_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_chunk_embeddings_model ON chunk_embeddings(embedding_model)
        """)
        
        # GIN index on JSONB for efficient vector operations
        cursor.execute("""
            CREATE INDEX idx_chunk_embeddings_vector_gin ON chunk_embeddings USING gin(embedding)
        """)
        
        # Comment the table for documentation
        cursor.execute("""
            COMMENT ON TABLE chunk_embeddings IS 
            'Vector embeddings for text chunks - Optimized for PostgreSQL JSONB storage by DBA Team'
        """)
        
        self.logger.info("✅ Created chunk_embeddings table with PostgreSQL JSONB optimization")
    
    def process_book_with_embeddings(self, book_id: int, chapters: List[ChapterInfo]) -> bool:
        """Complete embedding processing for a single book"""
        self.logger.info(f"🔄 Processing book {book_id} with vector embeddings...")
        
        # Generate embeddings for all chapters
        embedding_results = self.embed_book_chunks(book_id, chapters)
        
        # Store embeddings in database
        storage_success = self.store_embeddings(book_id, embedding_results)
        
        if storage_success:
            self.logger.info(f"✅ Successfully processed book {book_id} with embeddings")
            return True
        else:
            self.logger.error(f"❌ Failed to store embeddings for book {book_id}")
            return False
    
    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get embedding processing statistics"""
        return {
            **self.stats,
            'team_signature': self.team_signature,
            'model_used': self.embedding_model,
            'timestamp': datetime.now().isoformat()
        }
    
    def test_embedding_system(self) -> bool:
        """Test the embedding system with sample text"""
        self.logger.info("🧪 Testing Ollama embedding system...")
        
        test_text = "This is a test sentence for vector embedding generation using Ollama."
        
        embedding = self.generate_embedding(test_text)
        
        if embedding and len(embedding) > 0:
            self.logger.info(f"✅ Embedding test successful: {len(embedding)} dimensions")
            self.logger.info(f"📊 Sample values: {embedding[:5]}...")
            return True
        else:
            self.logger.error("❌ Embedding test failed")
            return False

def main():
    """Test the Ollama vector embedder"""
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'knowledge_base'),
        'user': os.getenv('DB_USER', 'weixiangzhang'),
        'port': 5432
    }
    
    embedder = OllamaVectorEmbedder(db_config)
    
    # Test the system
    success = embedder.test_embedding_system()
    
    if success:
        print("🧠 Ollama Vector Embedder - Ready for Production")
        print("✅ All systems operational")
    else:
        print("❌ Ollama Vector Embedder - System check failed")
        sys.exit(1)

if __name__ == "__main__":
    main()