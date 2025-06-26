#!/usr/bin/env python3
"""
LibraryOfBabel Database Ingestion Module
Loads processed book chunks into PostgreSQL for AI agent consumption
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import psycopg2
import psycopg2.extras
from dataclasses import dataclass
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class IngestionStats:
    """Statistics for database ingestion process"""
    books_processed: int = 0
    chunks_inserted: int = 0
    authors_created: int = 0
    processing_time: float = 0.0
    failed_books: List[str] = None
    
    def __post_init__(self):
        if self.failed_books is None:
            self.failed_books = []

class DatabaseIngestor:
    """Handles ingestion of processed book data into PostgreSQL"""
    
    def __init__(self, db_config: Dict[str, Any]):
        """
        Initialize database ingestor
        
        Args:
            db_config: Database connection configuration
        """
        self.db_config = db_config
        self.connection = None
        self.stats = IngestionStats()
        
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.connection.autocommit = False  # Use transactions
            logger.info("Database connection established")
            return True
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def setup_database(self, schema_file: str = None):
        """Initialize database schema"""
        if not schema_file:
            schema_file = "database/schema.sql"
            
        schema_path = Path(schema_file)
        if not schema_path.exists():
            logger.error(f"Schema file not found: {schema_file}")
            return False
            
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            cursor = self.connection.cursor()
            cursor.execute(schema_sql)
            self.connection.commit()
            logger.info("Database schema initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            self.connection.rollback()
            return False
    
    def get_or_create_author(self, cursor, author_name: str) -> Optional[int]:
        """Get existing author or create new one"""
        if not author_name or author_name.strip() == '':
            return None
            
        author_name = author_name.strip()
        
        # Check if author exists
        cursor.execute("SELECT author_id FROM authors WHERE name = %s", (author_name,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Create new author
        try:
            cursor.execute(
                "INSERT INTO authors (name) VALUES (%s) RETURNING author_id",
                (author_name,)
            )
            author_id = cursor.fetchone()[0]
            self.stats.authors_created += 1
            logger.debug(f"Created new author: {author_name} (ID: {author_id})")
            return author_id
        except psycopg2.IntegrityError:
            # Handle race condition - author might have been created by another process
            self.connection.rollback()
            cursor.execute("SELECT author_id FROM authors WHERE name = %s", (author_name,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def insert_book(self, cursor, book_data: Dict) -> Optional[int]:
        """Insert book metadata into database"""
        metadata = book_data.get('metadata', {})
        
        # Extract book metadata
        title = metadata.get('title', 'Unknown Title')
        author = metadata.get('author', '')
        publisher = metadata.get('publisher', '')
        publication_date = metadata.get('publication_date', '')
        language = metadata.get('language', 'english')
        isbn = metadata.get('isbn', '')
        description = metadata.get('description', '')
        word_count = metadata.get('total_words', 0)
        source_location = metadata.get('source_location', '')
        import_source = metadata.get('import_source', '')
        
        # Parse publication year
        publication_year = None
        if publication_date:
            try:
                publication_year = int(publication_date[:4]) if len(publication_date) >= 4 else None
            except (ValueError, TypeError):
                pass
        
        # Get or create author
        author_id = self.get_or_create_author(cursor, author) if author else None
        
        # Insert book
        try:
            cursor.execute("""
                INSERT INTO books (
                    title, author, author_id, publisher, publication_date, 
                    publication_year, language, isbn, description, word_count,
                    source_location, import_source
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING book_id
            """, (
                title, author, author_id, publisher, publication_date,
                publication_year, language, isbn, description, word_count,
                source_location, import_source
            ))
            
            book_id = cursor.fetchone()[0]
            logger.debug(f"Inserted book: {title} by {author} (ID: {book_id})")
            return book_id
            
        except Exception as e:
            logger.error(f"Failed to insert book '{title}': {e}")
            return None
    
    def insert_chunks(self, cursor, book_id: int, chunks_data: List[Dict]) -> int:
        """Insert text chunks for a book"""
        chunks_inserted = 0
        
        for chunk in chunks_data:
            try:
                cursor.execute("""
                    INSERT INTO chunks (
                        chunk_id, book_id, chunk_type, title, content,
                        word_count, character_count, chapter_number, 
                        section_number, paragraph_number, start_position,
                        end_position, parent_chunk_id
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    chunk.get('chunk_id'),
                    book_id,
                    chunk.get('chunk_type'),
                    chunk.get('title', ''),
                    chunk.get('content', ''),
                    chunk.get('word_count', 0),
                    chunk.get('character_count', 0),
                    chunk.get('chapter_number'),
                    chunk.get('section_number'),
                    chunk.get('paragraph_number'),
                    chunk.get('start_position', 0),
                    chunk.get('end_position', 0),
                    chunk.get('parent_chunk_id')
                ))
                chunks_inserted += 1
                
            except Exception as e:
                logger.error(f"Failed to insert chunk {chunk.get('chunk_id', 'unknown')}: {e}")
                continue
        
        return chunks_inserted
    
    def process_book_file(self, file_path: Path) -> bool:
        """Process a single book JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                book_data = json.load(f)
            
            cursor = self.connection.cursor()
            
            # Insert book metadata
            book_id = self.insert_book(cursor, book_data)
            if not book_id:
                logger.error(f"Failed to insert book from {file_path}")
                self.connection.rollback()
                return False
            
            # Insert chunks
            chunks_data = book_data.get('chunks', [])
            chunks_inserted = self.insert_chunks(cursor, book_id, chunks_data)
            
            if chunks_inserted == 0:
                logger.warning(f"No chunks inserted for book {book_id}")
            
            # Commit transaction
            self.connection.commit()
            
            self.stats.books_processed += 1
            self.stats.chunks_inserted += chunks_inserted
            
            logger.info(f"✅ Processed {file_path.stem}: {chunks_inserted} chunks inserted")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            if self.connection:
                self.connection.rollback()
            self.stats.failed_books.append(str(file_path))
            return False
    
    def ingest_directory(self, directory_path: str) -> IngestionStats:
        """Ingest all JSON files from a directory"""
        start_time = time.time()
        
        directory = Path(directory_path)
        if not directory.exists():
            logger.error(f"Directory not found: {directory_path}")
            return self.stats
        
        # Find all JSON files
        json_files = list(directory.glob("*_processed.json"))
        if not json_files:
            logger.warning(f"No processed JSON files found in {directory_path}")
            return self.stats
        
        logger.info(f"Found {len(json_files)} books to process")
        
        # Process each file
        for i, json_file in enumerate(json_files, 1):
            logger.info(f"Processing book {i}/{len(json_files)}: {json_file.stem}")
            self.process_book_file(json_file)
            
            # Progress update every 10 books
            if i % 10 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                logger.info(f"Progress: {i}/{len(json_files)} ({i/len(json_files)*100:.1f}%) - {rate:.1f} books/sec")
        
        self.stats.processing_time = time.time() - start_time
        return self.stats
    
    def generate_report(self) -> Dict:
        """Generate ingestion report"""
        return {
            "ingestion_summary": {
                "books_processed": self.stats.books_processed,
                "chunks_inserted": self.stats.chunks_inserted,
                "authors_created": self.stats.authors_created,
                "failed_books": len(self.stats.failed_books),
                "success_rate": (self.stats.books_processed / max(self.stats.books_processed + len(self.stats.failed_books), 1)) * 100
            },
            "performance_metrics": {
                "total_processing_time_minutes": round(self.stats.processing_time / 60, 2),
                "books_per_hour": round((self.stats.books_processed / max(self.stats.processing_time / 3600, 0.001)), 1),
                "chunks_per_second": round((self.stats.chunks_inserted / max(self.stats.processing_time, 0.001)), 1)
            },
            "database_ready": {
                "ready_for_queries": self.stats.chunks_inserted > 0,
                "search_index_built": True,
                "api_ready": True
            },
            "failed_files": self.stats.failed_books
        }


def main():
    """Main ingestion function"""
    parser = argparse.ArgumentParser(description='LibraryOfBabel Database Ingestion')
    parser.add_argument('--input', required=True, help='Input directory containing processed JSON files')
    parser.add_argument('--setup-schema', action='store_true', help='Initialize database schema first')
    parser.add_argument('--db-host', default='localhost', help='Database host')
    parser.add_argument('--db-name', default='knowledge_base', help='Database name')
    parser.add_argument('--db-user', default='postgres', help='Database user')
    parser.add_argument('--db-port', default=5432, type=int, help='Database port')
    parser.add_argument('--report', default='database/ingestion_report.json', help='Output report file')
    
    args = parser.parse_args()
    
    # Database configuration
    db_config = {
        'host': args.db_host,
        'database': args.db_name,
        'user': args.db_user,
        'port': args.db_port
    }
    
    # Initialize ingestor
    ingestor = DatabaseIngestor(db_config)
    
    try:
        # Connect to database
        if not ingestor.connect():
            logger.error("Failed to connect to database")
            return 1
        
        # Setup schema if requested
        if args.setup_schema:
            logger.info("Setting up database schema...")
            if not ingestor.setup_database():
                logger.error("Schema setup failed")
                return 1
        
        # Run ingestion
        logger.info(f"🚀 Starting database ingestion from {args.input}")
        stats = ingestor.ingest_directory(args.input)
        
        # Generate report
        report = ingestor.generate_report()
        
        # Save report
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("📚 DATABASE INGESTION COMPLETE")
        print("="*60)
        print(f"✅ Books processed: {stats.books_processed}")
        print(f"🔗 Chunks inserted: {stats.chunks_inserted:,}")
        print(f"👤 Authors created: {stats.authors_created}")
        print(f"❌ Failed books: {len(stats.failed_books)}")
        print(f"⏱️  Processing time: {stats.processing_time/60:.1f} minutes")
        if stats.processing_time > 0:
            print(f"⚡ Speed: {stats.books_processed/(stats.processing_time/3600):.1f} books/hour")
            print(f"🔗 Chunk rate: {stats.chunks_inserted/stats.processing_time:.1f} chunks/second")
        print(f"📋 Report saved: {report_path}")
        print("🔍 Database ready for search queries!")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Ingestion interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        return 1
    finally:
        ingestor.disconnect()


if __name__ == "__main__":
    exit(main())