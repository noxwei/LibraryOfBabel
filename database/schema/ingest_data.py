#!/usr/bin/env python3
"""
LibraryOfBabel Data Ingestion Script
Loads processed JSON files into PostgreSQL database

This script:
1. Connects to the knowledge_base PostgreSQL database
2. Loads all processed JSON files from the output directory
3. Ingests book metadata and chunk content into the database
4. Tracks performance and provides detailed logging
5. Handles duplicate detection and error recovery
"""

import json
import os
import sys
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import psycopg2.extras

# Configuration
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'knowledge_base'),
    'user': os.getenv('POSTGRES_USER', os.getenv('USER')),  # Use system user as default
    'password': os.getenv('POSTGRES_PASSWORD', ''),  # No password for local development
    'port': 5432
}

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else PROJECT_ROOT / 'database' / 'data'
LOG_FILE = PROJECT_ROOT / 'database' / 'ingestion.log'

class DatabaseIngester:
    """Handles ingestion of processed book data into PostgreSQL"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.stats = {
            'files_processed': 0,
            'books_inserted': 0,
            'chunks_inserted': 0,
            'duplicates_skipped': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        
    def connect_database(self) -> bool:
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(**DATABASE_CONFIG)
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            # Test connection
            self.cursor.execute("SELECT version();")
            version = self.cursor.fetchone()
            self.log(f"Connected to PostgreSQL: {version['version']}")
            return True
            
        except psycopg2.Error as e:
            self.log(f"Database connection failed: {e}", level='ERROR')
            return False
            
    def log(self, message: str, level: str = 'INFO'):
        """Log message to console and file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {level}: {message}"
        
        print(log_entry)
        
        # Write to log file
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
        except Exception:
            pass  # Don't fail if logging fails
            
    def get_book_hash(self, book_data: Dict) -> str:
        """Generate unique hash for book to detect duplicates"""
        # Use file path and title for uniqueness
        unique_string = f"{book_data['metadata']['file_path']}:{book_data['metadata']['title']}"
        return hashlib.sha256(unique_string.encode()).hexdigest()
        
    def book_exists(self, file_path: str, title: str) -> Optional[int]:
        """Check if book already exists in database"""
        try:
            self.cursor.execute("""
                SELECT book_id FROM books 
                WHERE file_path = %s AND title = %s
            """, (file_path, title))
            
            result = self.cursor.fetchone()
            return result['book_id'] if result else None
            
        except psycopg2.Error as e:
            self.log(f"Error checking book existence: {e}", level='ERROR')
            return None
            
    def insert_book(self, metadata: Dict) -> Optional[int]:
        """Insert book metadata into database"""
        try:
            # Parse publication date
            pub_date = None
            if metadata.get('publication_date'):
                try:
                    # Handle ISO format dates
                    pub_date = datetime.fromisoformat(
                        metadata['publication_date'].replace('Z', '+00:00')
                    ).date()
                except (ValueError, TypeError):
                    self.log(f"Could not parse publication date: {metadata.get('publication_date')}")
            
            # Prepare book data - match actual database schema
            book_data = {
                'title': metadata['title'][:500],  # Truncate if too long
                'author': metadata.get('author', '')[:255] if metadata.get('author') else None,
                'publisher': metadata.get('publisher', '')[:255] if metadata.get('publisher') else None,
                'publication_date': metadata.get('publication_date', '')[:100] if metadata.get('publication_date') else None,
                'language': metadata.get('language', 'english')[:50],
                'isbn': metadata.get('isbn', '')[:50] if metadata.get('isbn') else None,
                'description': metadata.get('description'),
                'genre': metadata.get('subject', '')[:100] if metadata.get('subject') else None,  # Map subject to genre
                'word_count': metadata.get('total_words', 0),
                'file_path': metadata['file_path'][:1000],
                'processed_date': datetime.now()
            }
            
            # Insert book
            insert_query = """
                INSERT INTO books (
                    title, author, publisher, publication_date, language, isbn,
                    description, genre, word_count, file_path, processed_date
                ) VALUES (
                    %(title)s, %(author)s, %(publisher)s, %(publication_date)s, 
                    %(language)s, %(isbn)s, %(description)s, %(genre)s,
                    %(word_count)s, %(file_path)s, %(processed_date)s
                ) RETURNING book_id
            """
            
            self.cursor.execute(insert_query, book_data)
            book_id = self.cursor.fetchone()['book_id']
            
            self.log(f"Inserted book: {book_data['title']} (ID: {book_id})")
            return book_id
            
        except psycopg2.Error as e:
            self.log(f"Error inserting book: {e}", level='ERROR')
            return None
            
    def insert_chunks(self, book_id: int, chapters: List[Dict]) -> int:
        """Insert book chunks into database"""
        chunks_inserted = 0
        
        try:
            for i, chapter in enumerate(chapters):
                # Generate unique chunk_id 
                chunk_id = f"{book_id}_{i+1:04d}"
                
                # Prepare chunk data - match actual database schema
                chunk_data = {
                    'chunk_id': chunk_id,
                    'book_id': book_id,
                    'chunk_type': 'chapter',  # Default type
                    'title': chapter.get('title', '')[:500] if chapter.get('title') else None,
                    'chapter_number': chapter.get('chapter_number'),
                    'section_number': chapter.get('section_number'),
                    'content': chapter['content'],
                    'word_count': chapter.get('word_count', 0),
                    'character_count': len(chapter['content']) if 'content' in chapter else 0
                }
                
                # Insert chunk
                insert_query = """
                    INSERT INTO chunks (
                        chunk_id, book_id, chunk_type, title, chapter_number, section_number,
                        content, word_count, character_count
                    ) VALUES (
                        %(chunk_id)s, %(book_id)s, %(chunk_type)s, %(title)s, %(chapter_number)s,
                        %(section_number)s, %(content)s, %(word_count)s, %(character_count)s
                    ) RETURNING chunk_id
                """
                
                self.cursor.execute(insert_query, chunk_data)
                chunks_inserted += 1
                
                if chunks_inserted % 50 == 0:  # Progress update every 50 chunks
                    self.log(f"Inserted {chunks_inserted} chunks for book {book_id}")
                    
        except psycopg2.Error as e:
            self.log(f"Error inserting chunks: {e}", level='ERROR')
            
        return chunks_inserted
        
    def process_json_file(self, json_file_path: Path) -> bool:
        """Process a single JSON file and insert into database"""
        try:
            self.log(f"Processing: {json_file_path.name}")
            
            # Load JSON data
            with open(json_file_path, 'r', encoding='utf-8') as f:
                book_data = json.load(f)
                
            metadata = book_data['metadata']
            chapters = book_data.get('chapters', [])
            
            # Check if book already exists
            existing_book_id = self.book_exists(metadata['file_path'], metadata['title'])
            if existing_book_id:
                self.log(f"Book already exists (ID: {existing_book_id}): {metadata['title']}")
                self.stats['duplicates_skipped'] += 1
                return True
                
            # Insert book
            book_id = self.insert_book(metadata)
            if not book_id:
                self.stats['errors'] += 1
                return False
                
            self.stats['books_inserted'] += 1
            
            # Insert chunks
            chunks_count = self.insert_chunks(book_id, chapters)
            self.stats['chunks_inserted'] += chunks_count
            
            # Commit transaction
            self.connection.commit()
            
            self.log(f"Successfully processed: {metadata['title']} ({chunks_count} chunks)")
            return True
            
        except Exception as e:
            self.log(f"Error processing {json_file_path.name}: {e}", level='ERROR')
            self.connection.rollback()
            self.stats['errors'] += 1
            return False
            
    def get_json_files(self) -> List[Path]:
        """Get all JSON files from output directory"""
        if not OUTPUT_DIR.exists():
            self.log(f"Output directory not found: {OUTPUT_DIR}", level='ERROR')
            return []
            
        json_files = list(OUTPUT_DIR.glob('*_processed.json'))
        self.log(f"Found {len(json_files)} JSON files to process")
        return json_files
        
    def log_processing_stats(self):
        """Log processing statistics"""
        try:
            # Insert processing log entry
            self.cursor.execute("""
                INSERT INTO processing_log (operation, status, message, execution_time_ms, context)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                'data_ingestion',
                'completed' if self.stats['errors'] == 0 else 'failed',
                f"Processed {self.stats['files_processed']} files, "
                f"inserted {self.stats['books_inserted']} books, "
                f"{self.stats['chunks_inserted']} chunks",
                int((self.stats['end_time'] - self.stats['start_time']) * 1000),
                json.dumps(self.stats, default=str)
            ))
            self.connection.commit()
            
        except Exception as e:
            self.log(f"Error logging processing stats: {e}", level='ERROR')
            
    def get_database_stats(self) -> Dict:
        """Get current database statistics"""
        try:
            self.cursor.execute("SELECT * FROM database_stats")
            stats = self.cursor.fetchall()
            return {row['table_name']: dict(row) for row in stats}
        except Exception as e:
            self.log(f"Error getting database stats: {e}", level='ERROR')
            return {}
            
    def run_ingestion(self) -> bool:
        """Main ingestion process"""
        self.stats['start_time'] = time.time()
        
        self.log("=" * 80)
        self.log("LibraryOfBabel Data Ingestion Started")
        self.log("=" * 80)
        
        # Connect to database
        if not self.connect_database():
            return False
            
        # Get JSON files
        json_files = self.get_json_files()
        if not json_files:
            self.log("No JSON files found to process", level='ERROR')
            return False
            
        # Process each file
        for json_file in json_files:
            if self.process_json_file(json_file):
                self.stats['files_processed'] += 1
                
        self.stats['end_time'] = time.time()
        
        # Log final statistics
        self.log("=" * 80)
        self.log("Data Ingestion Complete")
        self.log("=" * 80)
        self.log(f"Files processed: {self.stats['files_processed']}")
        self.log(f"Books inserted: {self.stats['books_inserted']}")
        self.log(f"Chunks inserted: {self.stats['chunks_inserted']}")
        self.log(f"Duplicates skipped: {self.stats['duplicates_skipped']}")
        self.log(f"Errors: {self.stats['errors']}")
        self.log(f"Processing time: {self.stats['end_time'] - self.stats['start_time']:.2f} seconds")
        
        # Get database statistics
        db_stats = self.get_database_stats()
        if db_stats:
            self.log("\nDatabase Statistics:")
            for table, stats in db_stats.items():
                self.log(f"  {table}: {stats['record_count']} records, "
                        f"{stats['total_words']:,} total words")
                
        # Log to processing_log table
        self.log_processing_stats()
        
        # Close database connection
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            
        success = self.stats['errors'] == 0
        self.log(f"Ingestion {'completed successfully' if success else 'completed with errors'}")
        return success


def main():
    """Main entry point"""
    # Create log file directory if it doesn't exist
    LOG_FILE.parent.mkdir(exist_ok=True)
    
    # Initialize and run ingester
    ingester = DatabaseIngester()
    success = ingester.run_ingestion()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()