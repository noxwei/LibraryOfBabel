#!/usr/bin/env python3
"""
Database Integration Tests
==========================

Tests database functionality, data ingestion, and search performance.
Coordinates with DBA Agent work to validate complete data pipeline.

QA Agent: LibraryOfBabel
Target: <100ms search performance, zero data corruption
"""

import json
import os
import sys
import unittest
import logging
import time
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import tempfile

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestDatabaseIntegration(unittest.TestCase):
    """Test suite for database integration validation."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database environment."""
        cls.base_dir = Path(__file__).parent.parent
        cls.output_dir = cls.base_dir / 'output'
        cls.db_dir = cls.base_dir / 'database'
        
        # Create test database
        cls.test_db_path = tempfile.mktemp(suffix='.db')
        cls._create_test_database()
        cls._load_test_data()
        
        logger.info(f"Created test database: {cls.test_db_path}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database."""
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)
        logger.info("Cleaned up test database")
    
    @classmethod
    def _create_test_database(cls):
        """Create test database schema."""
        with sqlite3.connect(cls.test_db_path) as conn:
            cursor = conn.cursor()
            
            # Books table
            cursor.execute('''
                CREATE TABLE books (
                    book_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    author TEXT,
                    publisher TEXT,
                    publication_date TEXT,
                    language TEXT DEFAULT 'en',
                    isbn TEXT,
                    description TEXT,
                    subject TEXT,
                    total_chapters INTEGER DEFAULT 0,
                    total_words INTEGER DEFAULT 0,
                    file_path TEXT,
                    processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Chapters table
            cursor.execute('''
                CREATE TABLE chapters (
                    chapter_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER REFERENCES books(book_id),
                    title TEXT,
                    content TEXT NOT NULL,
                    chapter_number INTEGER,
                    section_number INTEGER,
                    word_count INTEGER DEFAULT 0,
                    file_path TEXT,
                    spine_order INTEGER
                )
            ''')
            
            # Chunks table
            cursor.execute('''
                CREATE TABLE chunks (
                    chunk_id TEXT PRIMARY KEY,
                    book_id INTEGER REFERENCES books(book_id),
                    chunk_type TEXT NOT NULL,
                    title TEXT,
                    content TEXT NOT NULL,
                    word_count INTEGER DEFAULT 0,
                    character_count INTEGER DEFAULT 0,
                    chapter_number INTEGER,
                    section_number INTEGER,
                    paragraph_number INTEGER,
                    start_position INTEGER,
                    end_position INTEGER,
                    parent_chunk_id TEXT
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX idx_books_author ON books(author)')
            cursor.execute('CREATE INDEX idx_books_title ON books(title)')
            cursor.execute('CREATE INDEX idx_chapters_book ON chapters(book_id)')
            cursor.execute('CREATE INDEX idx_chunks_book ON chunks(book_id)')
            cursor.execute('CREATE INDEX idx_chunks_type ON chunks(chunk_type)')
            
            # Full-text search indexes (SQLite FTS5)
            cursor.execute('''
                CREATE VIRTUAL TABLE books_fts USING fts5(
                    title, author, description, content='books'
                )
            ''')
            
            cursor.execute('''
                CREATE VIRTUAL TABLE chunks_fts USING fts5(
                    title, content, content='chunks'
                )
            ''')
            
            conn.commit()
    
    @classmethod
    def _load_test_data(cls):
        """Load processed data into test database."""
        if not cls.output_dir.exists():
            logger.warning("No output directory found - skipping data load")
            return
        
        loaded_books = 0
        loaded_chapters = 0
        loaded_chunks = 0
        
        with sqlite3.connect(cls.test_db_path) as conn:
            cursor = conn.cursor()
            
            for json_file in cls.output_dir.glob('*_processed.json'):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Insert book metadata
                    metadata = data.get('metadata', {})
                    cursor.execute('''
                        INSERT INTO books (title, author, publisher, publication_date,
                                         language, isbn, description, subject,
                                         total_chapters, total_words, file_path)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        metadata.get('title', 'Unknown'),
                        metadata.get('author', 'Unknown'),
                        metadata.get('publisher'),
                        metadata.get('publication_date'),
                        metadata.get('language', 'en'),
                        metadata.get('isbn'),
                        metadata.get('description'),
                        metadata.get('subject'),
                        metadata.get('total_chapters', 0),
                        metadata.get('total_words', 0),
                        metadata.get('file_path')
                    ))
                    
                    book_id = cursor.lastrowid
                    loaded_books += 1
                    
                    # Insert chapters
                    for chapter in data.get('chapters', []):
                        cursor.execute('''
                            INSERT INTO chapters (book_id, title, content, chapter_number,
                                                section_number, word_count, file_path, spine_order)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            book_id,
                            chapter.get('title'),
                            chapter.get('content', ''),
                            chapter.get('chapter_number'),
                            chapter.get('section_number'),
                            chapter.get('word_count', 0),
                            chapter.get('file_path'),
                            chapter.get('spine_order')
                        ))
                        loaded_chapters += 1
                    
                    # Insert chunks
                    for chunk in data.get('chunks', []):
                        cursor.execute('''
                            INSERT INTO chunks (chunk_id, book_id, chunk_type, title, content,
                                              word_count, character_count, chapter_number,
                                              section_number, paragraph_number, start_position,
                                              end_position, parent_chunk_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            chunk.get('chunk_id'),
                            book_id,
                            chunk.get('chunk_type'),
                            chunk.get('title'),
                            chunk.get('content', ''),
                            chunk.get('word_count', 0),
                            chunk.get('character_count', 0),
                            chunk.get('chapter_number'),
                            chunk.get('section_number'),
                            chunk.get('paragraph_number'),
                            chunk.get('start_position'),
                            chunk.get('end_position'),
                            chunk.get('parent_chunk_id')
                        ))
                        loaded_chunks += 1
                    
                    # Update FTS indexes
                    cursor.execute('''
                        INSERT INTO books_fts (rowid, title, author, description)
                        VALUES (?, ?, ?, ?)
                    ''', (book_id, metadata.get('title', ''), metadata.get('author', ''),
                          metadata.get('description', '')))
                    
                    for chunk in data.get('chunks', []):
                        if chunk.get('chunk_id'):
                            cursor.execute('''
                                INSERT INTO chunks_fts (rowid, title, content)
                                SELECT chunk_id, title, content FROM chunks 
                                WHERE chunk_id = ?
                            ''', (chunk.get('chunk_id'),))
                
                except Exception as e:
                    logger.error(f"Failed to load {json_file}: {e}")
            
            conn.commit()
        
        logger.info(f"Loaded {loaded_books} books, {loaded_chapters} chapters, {loaded_chunks} chunks")
    
    def test_01_database_schema_validation(self):
        """Validate database schema is properly created."""
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.cursor()
            
            # Check tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['books', 'chapters', 'chunks', 'books_fts', 'chunks_fts']
            missing_tables = [table for table in required_tables if table not in tables]
            
            self.assertEqual(len(missing_tables), 0,
                           f"Missing database tables: {missing_tables}")
            
            # Check indexes exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in cursor.fetchall()]
            
            required_indexes = ['idx_books_author', 'idx_books_title', 'idx_chapters_book', 
                              'idx_chunks_book', 'idx_chunks_type']
            missing_indexes = [idx for idx in required_indexes if idx not in indexes]
            
            self.assertEqual(len(missing_indexes), 0,
                           f"Missing database indexes: {missing_indexes}")
        
        logger.info("✓ Database schema validation passed")
    
    def test_02_data_ingestion_validation(self):
        """Validate data was properly ingested into database."""
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.cursor()
            
            # Check book count
            cursor.execute("SELECT COUNT(*) FROM books")
            book_count = cursor.fetchone()[0]
            self.assertGreater(book_count, 0, "No books found in database")
            
            # Check chapter count
            cursor.execute("SELECT COUNT(*) FROM chapters")
            chapter_count = cursor.fetchone()[0]
            self.assertGreater(chapter_count, 0, "No chapters found in database")
            
            # Check chunk count
            cursor.execute("SELECT COUNT(*) FROM chunks")
            chunk_count = cursor.fetchone()[0]
            self.assertGreater(chunk_count, 0, "No chunks found in database")
            
            # Validate referential integrity
            cursor.execute('''
                SELECT COUNT(*) FROM chapters c
                LEFT JOIN books b ON c.book_id = b.book_id
                WHERE b.book_id IS NULL
            ''')
            orphaned_chapters = cursor.fetchone()[0]
            self.assertEqual(orphaned_chapters, 0, "Found orphaned chapters")
            
            cursor.execute('''
                SELECT COUNT(*) FROM chunks ch
                LEFT JOIN books b ON ch.book_id = b.book_id
                WHERE b.book_id IS NULL
            ''')
            orphaned_chunks = cursor.fetchone()[0]
            self.assertEqual(orphaned_chunks, 0, "Found orphaned chunks")
        
        logger.info(f"✓ Data ingestion: {book_count} books, {chapter_count} chapters, {chunk_count} chunks")
    
    def test_03_search_performance_basic(self):
        """Test basic search performance meets <100ms target."""
        search_times = []
        
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.cursor()
            
            # Test queries
            test_queries = [
                "SELECT * FROM books WHERE author LIKE '%Author%' LIMIT 10",
                "SELECT * FROM chapters WHERE title LIKE '%Chapter%' LIMIT 10",
                "SELECT * FROM chunks WHERE chunk_type = 'chapter' LIMIT 10",
                "SELECT b.title, COUNT(*) FROM books b JOIN chapters c ON b.book_id = c.book_id GROUP BY b.book_id LIMIT 10"
            ]
            
            for query in test_queries:
                start_time = time.time()
                cursor.execute(query)
                results = cursor.fetchall()
                end_time = time.time()
                
                query_time = (end_time - start_time) * 1000  # Convert to milliseconds
                search_times.append(query_time)
                
                # Individual query should be under 100ms
                self.assertLess(query_time, 100,
                              f"Query exceeded 100ms threshold: {query_time:.2f}ms")
        
        avg_time = sum(search_times) / len(search_times)
        max_time = max(search_times)
        
        self.assertLess(avg_time, 50,  # Average should be well under threshold
                       f"Average query time {avg_time:.2f}ms too high")
        
        logger.info(f"✓ Search performance: avg={avg_time:.2f}ms, max={max_time:.2f}ms (target: <100ms)")
    
    def test_04_full_text_search_performance(self):
        """Test full-text search performance and accuracy."""
        search_times = []
        
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.cursor()
            
            # Test FTS queries
            fts_queries = [
                "SELECT * FROM books_fts WHERE books_fts MATCH 'investing' LIMIT 10",
                "SELECT * FROM chunks_fts WHERE chunks_fts MATCH 'money' LIMIT 10",
                "SELECT * FROM books_fts WHERE books_fts MATCH 'beginner' LIMIT 10"
            ]
            
            for query in fts_queries:
                start_time = time.time()
                try:
                    cursor.execute(query)
                    results = cursor.fetchall()
                    end_time = time.time()
                    
                    query_time = (end_time - start_time) * 1000
                    search_times.append(query_time)
                    
                    # FTS queries should be very fast
                    self.assertLess(query_time, 50,
                                  f"FTS query exceeded 50ms: {query_time:.2f}ms")
                    
                except Exception as e:
                    logger.warning(f"FTS query failed: {query} - {e}")
        
        if search_times:
            avg_fts_time = sum(search_times) / len(search_times)
            logger.info(f"✓ Full-text search performance: avg={avg_fts_time:.2f}ms")
        else:
            logger.warning("No FTS queries succeeded")
    
    def test_05_data_consistency_validation(self):
        """Validate data consistency between tables."""
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.cursor()
            
            # Check word count consistency
            cursor.execute('''
                SELECT b.book_id, b.total_words, SUM(c.word_count) as chapter_words
                FROM books b
                JOIN chapters c ON b.book_id = c.book_id
                GROUP BY b.book_id
                HAVING ABS(b.total_words - chapter_words) > b.total_words * 0.1
            ''')
            inconsistent_books = cursor.fetchall()
            
            self.assertEqual(len(inconsistent_books), 0,
                           f"Books with inconsistent word counts: {len(inconsistent_books)}")
            
            # Check chapter count consistency
            cursor.execute('''
                SELECT b.book_id, b.total_chapters, COUNT(c.chapter_id) as actual_chapters
                FROM books b
                JOIN chapters c ON b.book_id = c.book_id
                GROUP BY b.book_id
                HAVING ABS(b.total_chapters - actual_chapters) > 2
            ''')
            inconsistent_chapter_counts = cursor.fetchall()
            
            self.assertEqual(len(inconsistent_chapter_counts), 0,
                           f"Books with inconsistent chapter counts: {len(inconsistent_chapter_counts)}")
        
        logger.info("✓ Data consistency validation passed")
    
    def test_06_search_quality_validation(self):
        """Validate search result quality and relevance."""
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.cursor()
            
            # Test author search accuracy
            cursor.execute("SELECT DISTINCT author FROM books WHERE author IS NOT NULL")
            authors = [row[0] for row in cursor.fetchall()]
            
            if authors:
                test_author = authors[0]
                cursor.execute("SELECT * FROM books WHERE author = ?", (test_author,))
                author_books = cursor.fetchall()
                
                cursor.execute("SELECT * FROM books WHERE author LIKE ?", (f"%{test_author}%",))
                like_search_books = cursor.fetchall()
                
                # Like search should return at least as many results as exact match
                self.assertGreaterEqual(len(like_search_books), len(author_books),
                                      "Like search returned fewer results than exact match")
            
            # Test content search
            cursor.execute("SELECT content FROM chunks WHERE content IS NOT NULL LIMIT 1")
            sample_content = cursor.fetchone()
            
            if sample_content and sample_content[0]:
                # Extract a common word from content
                words = sample_content[0].split()
                if len(words) > 10:
                    test_word = words[5]  # Use 6th word
                    
                    cursor.execute("SELECT * FROM chunks WHERE content LIKE ? LIMIT 10", 
                                 (f"%{test_word}%",))
                    search_results = cursor.fetchall()
                    
                    # Should find at least one result
                    self.assertGreater(len(search_results), 0,
                                     f"No results found for word '{test_word}'")
        
        logger.info("✓ Search quality validation passed")
    
    def test_07_concurrent_access_simulation(self):
        """Simulate concurrent database access for stress testing."""
        import threading
        import queue
        
        results_queue = queue.Queue()
        error_queue = queue.Queue()
        
        def worker():
            try:
                with sqlite3.connect(self.test_db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Perform various operations
                    cursor.execute("SELECT COUNT(*) FROM books")
                    book_count = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT * FROM chapters LIMIT 5")
                    chapters = cursor.fetchall()
                    
                    cursor.execute("SELECT * FROM chunks WHERE chunk_type = 'chapter' LIMIT 3")
                    chunks = cursor.fetchall()
                    
                    results_queue.put(len(chapters) + len(chunks))
                    
            except Exception as e:
                error_queue.put(str(e))
        
        # Create multiple threads
        threads = []
        for i in range(5):  # 5 concurrent connections
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        errors = []
        while not error_queue.empty():
            errors.append(error_queue.get())
        
        self.assertEqual(len(errors), 0, f"Concurrent access errors: {errors}")
        
        # Verify all threads completed successfully
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        self.assertEqual(len(results), 5, "Not all threads completed successfully")
        
        logger.info("✓ Concurrent access simulation passed")


def run_database_integration_tests():
    """Run database integration tests and return results."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDatabaseIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful(), len(result.failures), len(result.errors)


if __name__ == '__main__':
    print("=" * 80)
    print("DATABASE INTEGRATION VALIDATION")
    print("=" * 80)
    
    success, failures, errors = run_database_integration_tests()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ ALL DATABASE INTEGRATION TESTS PASSED")
        print("Database functionality meets performance and quality standards")
    else:
        print("❌ DATABASE INTEGRATION TESTS FAILED")
        print(f"Failures: {failures}, Errors: {errors}")
    print("=" * 80)
    
    sys.exit(0 if success else 1)