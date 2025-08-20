#!/usr/bin/env python3
"""
Database Manager for BabelProcessorDb Testing
============================================

Handles database operations for the containerized pipeline testing.
Supports books, chunks, and chunk_embeddings tables.

Based on LibraryOfBabel standardized API schema.
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
import psycopg2
import psycopg2.extras
from epub_processor import BookMetadata, TextChunk

# Configure logging
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database operations for BabelProcessorDb testing"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'BabelProcessorDb'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'password': os.getenv('DB_PASSWORD', ''),
            'connect_timeout': 15,
            'application_name': 'BabelProcessor_Test'
        }
        logger.info(f"Database config: {self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}")
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper cleanup"""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    logger.info("Database connection successful")
                    return result[0] == 1
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def insert_book(self, metadata: BookMetadata, file_path: str) -> int:
        """
        Insert book metadata and return book_id
        
        Args:
            metadata: Book metadata
            file_path: Path to EPUB file
            
        Returns:
            book_id of inserted book
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # First check if book already exists by title and author
                    cur.execute("""
                        SELECT book_id FROM books 
                        WHERE title = %s AND author = %s
                    """, (metadata.title, metadata.author))
                    
                    existing = cur.fetchone()
                    if existing:
                        logger.info(f"Book already exists: {metadata.title} (ID: {existing[0]})")
                        return existing[0]
                    
                    # Insert new book
                    cur.execute("""
                        INSERT INTO books (
                            title, author, publisher, publication_date, 
                            language, isbn, description, genre, word_count, file_path
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING book_id
                    """, (
                        metadata.title,
                        metadata.author,
                        metadata.publisher,
                        metadata.publication_date,
                        metadata.language,
                        metadata.isbn,
                        metadata.description,
                        'Unknown',  # genre - will be classified later
                        metadata.word_count,
                        file_path
                    ))
                    
                    book_id = cur.fetchone()[0]
                    conn.commit()
                    
                    logger.info(f"Inserted book: {metadata.title} (ID: {book_id})")
                    return book_id
                    
        except Exception as e:
            logger.error(f"Error inserting book {metadata.title}: {e}")
            raise
    
    def insert_chunks(self, chunks: List[TextChunk]) -> int:
        """
        Insert text chunks in batch
        
        Args:
            chunks: List of text chunks
            
        Returns:
            Number of chunks inserted
        """
        if not chunks:
            return 0
            
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Prepare batch insert
                    chunk_data = [
                        (
                            chunk.chunk_id,
                            chunk.book_id,
                            chunk.chunk_type,
                            chunk.title,
                            chunk.content,
                            chunk.word_count,
                            chunk.chapter_number,
                            chunk.section_number,
                            chunk.paragraph_number
                        )
                        for chunk in chunks
                    ]
                    
                    # Batch insert
                    cur.executemany("""
                        INSERT INTO chunks (
                            chunk_id, book_id, chunk_type, title, content, 
                            word_count, chapter_number, section_number, paragraph_number
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) ON CONFLICT (chunk_id) DO NOTHING
                    """, chunk_data)
                    
                    inserted_count = cur.rowcount
                    conn.commit()
                    
                    logger.info(f"Inserted {inserted_count} chunks")
                    return inserted_count
                    
        except Exception as e:
            logger.error(f"Error inserting chunks: {e}")
            raise
    
    def insert_embeddings(self, embeddings: List[Dict]) -> int:
        """
        Insert embeddings in batch
        
        Args:
            embeddings: List of embedding dictionaries with keys:
                       chunk_id, embedding_model, embedding_vector
                       
        Returns:
            Number of embeddings inserted
        """
        if not embeddings:
            return 0
            
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Prepare batch insert
                    embedding_data = [
                        (
                            emb['chunk_id'],
                            emb['embedding_model'],
                            emb['embedding_vector']
                        )
                        for emb in embeddings
                    ]
                    
                    # Batch insert
                    cur.executemany("""
                        INSERT INTO chunk_embeddings (
                            chunk_id, embedding_model, embedding_vector
                        ) VALUES (
                            %s, %s, %s
                        ) ON CONFLICT (chunk_id, embedding_model) DO NOTHING
                    """, embedding_data)
                    
                    inserted_count = cur.rowcount
                    conn.commit()
                    
                    logger.info(f"Inserted {inserted_count} embeddings")
                    return inserted_count
                    
        except Exception as e:
            logger.error(f"Error inserting embeddings: {e}")
            raise
    
    def get_chunks_without_embeddings(self, model_name: str, limit: int = 100) -> List[Dict]:
        """
        Get chunks that don't have embeddings for specified model
        
        Args:
            model_name: Embedding model name
            limit: Maximum number of chunks to return
            
        Returns:
            List of chunk dictionaries
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT c.chunk_id, c.content, c.book_id, c.chapter_number
                        FROM chunks c
                        LEFT JOIN chunk_embeddings ce ON c.chunk_id = ce.chunk_id 
                            AND ce.embedding_model = %s
                        WHERE ce.chunk_id IS NULL
                        LIMIT %s
                    """, (model_name, limit))
                    
                    chunks = [dict(row) for row in cur.fetchall()]
                    logger.info(f"Found {len(chunks)} chunks without {model_name} embeddings")
                    return chunks
                    
        except Exception as e:
            logger.error(f"Error getting chunks without embeddings: {e}")
            raise
    
    def get_processing_stats(self) -> Dict:
        """Get processing statistics"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM get_processing_progress()")
                    row = cur.fetchone()
                    
                    if row:
                        return {
                            'total_books': row[0],
                            'total_chunks': row[1],
                            'chunks_with_nomic': row[2],
                            'chunks_with_bge': row[3],
                            'completion_percent_nomic': float(row[4]),
                            'completion_percent_bge': float(row[5])
                        }
                    else:
                        return {
                            'total_books': 0,
                            'total_chunks': 0,
                            'chunks_with_nomic': 0,
                            'chunks_with_bge': 0,
                            'completion_percent_nomic': 0.0,
                            'completion_percent_bge': 0.0
                        }
                        
        except Exception as e:
            logger.error(f"Error getting processing stats: {e}")
            return {}
    
    def get_embedding_stats(self) -> Dict:
        """Get embedding statistics"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM get_embedding_stats()")
                    rows = cur.fetchall()
                    
                    stats = {}
                    for row in rows:
                        model_name = row[0]
                        stats[model_name] = {
                            'total_embeddings': row[1],
                            'unique_chunks': row[2]
                        }
                    
                    return stats
                    
        except Exception as e:
            logger.error(f"Error getting embedding stats: {e}")
            return {}
    
    def cleanup_test_data(self) -> bool:
        """Clean up test data (books with ID > 1000)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Delete test data
                    cur.execute("DELETE FROM chunk_embeddings WHERE chunk_id IN (SELECT chunk_id FROM chunks WHERE book_id > 1000)")
                    embeddings_deleted = cur.rowcount
                    
                    cur.execute("DELETE FROM chunks WHERE book_id > 1000")
                    chunks_deleted = cur.rowcount
                    
                    cur.execute("DELETE FROM books WHERE book_id > 1000")
                    books_deleted = cur.rowcount
                    
                    conn.commit()
                    
                    logger.info(f"Cleanup completed: {books_deleted} books, {chunks_deleted} chunks, {embeddings_deleted} embeddings")
                    return True
                    
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return False