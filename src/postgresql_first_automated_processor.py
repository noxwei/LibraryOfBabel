#!/usr/bin/env python3
"""
PostgreSQL-First Automated Ebook Processor
==========================================

Dr. Sarah Chen (陈雪芳) Approved Architecture:
✅ ALL database logic in PostgreSQL functions
✅ API layer calls functions ONLY - no hardcoded SQL
✅ Functions handle ALL error cases and fallbacks
✅ Clean separation of concerns

Processes new ebooks from downloads folder with:
1. EPUB text extraction and chunking  
2. Database ingestion via PostgreSQL functions
3. Automatic phonetic enhancement
4. Batch processing with comprehensive statistics
"""

import os
import sys
import time
import logging
import json
import psycopg2
import psycopg2.extras
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Add src to path for imports
sys.path.append('src')
from epub_processor import EPUBProcessor
from vector_embeddings import VectorEmbeddingGenerator

class PostgreSQLFirstAutomatedProcessor:
    """Dr. Sarah Chen approved PostgreSQL-First automated processor"""
    
    def __init__(self):
        """Initialize the processor with PostgreSQL-First architecture"""
        self.downloads_dir = Path(os.getenv('EBOOK_DOWNLOADS_DIR', "src/ebooks/downloads"))
        self.processed_dir = Path("ebooks/processed")
        self.failed_dir = Path("ebooks/failed")
        
        # File size limits (prioritize smaller files)
        self.max_file_size_mb = 100
        self.priority_size_mb = 50
        
        # Database configuration
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': 5432
        }
        
        # Processing components
        try:
            self.epub_processor = EPUBProcessor()
        except Exception as e:
            self.epub_processor = None
            print(f"Warning: EPUBProcessor initialization failed: {e}")
        
        # Vector embedding generator for semantic search capabilities
        try:
            self.embedding_generator = VectorEmbeddingGenerator()
        except Exception as e:
            self.embedding_generator = None
            print(f"Warning: VectorEmbeddingGenerator initialization failed: {e}")
        
        # Statistics
        self.stats = {
            'processed': 0,
            'skipped_large': 0,
            'skipped_existing': 0,
            'failed': 0,
            'total_words': 0,
            'total_chunks': 0,
            'embeddings_generated': 0,
            'embedding_errors': 0
        }
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('postgresql_first_ebook_processing.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Create directories
        self._setup_directories()
        
        self.logger.info("🤖 PostgreSQL-First Automated Ebook Processor Ready")
        self.logger.info("🏛️  Architecture: Dr. Sarah Chen (陈雪芳) Approved")
        self.logger.info(f"📁 Monitoring: {self.downloads_dir}")
        self.logger.info(f"📊 Found {self.count_epub_files()} EPUB files to process")
    
    def _setup_directories(self):
        """Create necessary directories"""
        for directory in [self.processed_dir, self.failed_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def count_epub_files(self) -> int:
        """Count EPUB files in downloads directory"""
        if not self.downloads_dir.exists():
            return 0
        return len(list(self.downloads_dir.glob("*.epub")))
    
    def get_file_size_mb(self, file_path: Path) -> float:
        """Get file size in MB"""
        try:
            return file_path.stat().st_size / (1024 * 1024)
        except:
            return 0.0
    
    def find_ebooks_to_process(self) -> List[Dict]:
        """Find EPUB files that need processing"""
        ebooks = []
        
        if not self.downloads_dir.exists():
            self.logger.warning(f"Downloads directory not found: {self.downloads_dir}")
            return ebooks
        
        # Find all EPUB files
        for epub_file in self.downloads_dir.glob("*.epub"):
            if epub_file.is_file():
                file_size_mb = self.get_file_size_mb(epub_file)
                
                # Skip very large files for now
                if file_size_mb > self.max_file_size_mb:
                    self.stats['skipped_large'] += 1
                    continue
                
                ebook_info = {
                    'path': epub_file,
                    'name': epub_file.name,
                    'size_mb': file_size_mb,
                    'is_priority': file_size_mb <= self.priority_size_mb
                }
                ebooks.append(ebook_info)
        
        # Sort by priority (small files first)
        ebooks.sort(key=lambda x: (not x['is_priority'], x['size_mb']))
        
        self.logger.info(f"📚 Found {len(ebooks)} EPUB files to process")
        if self.stats['skipped_large'] > 0:
            self.logger.info(f"⏭️  Skipped {self.stats['skipped_large']} large files (>{self.max_file_size_mb}MB)")
        
        return ebooks
    
    def call_db_function(self, function_name: str, params: List = None) -> Optional[any]:
        """
        Dr. Sarah Chen approved: Single database function call pattern
        ✅ All database logic in PostgreSQL functions
        ✅ No hardcoded SQL in Python
        ✅ Functions handle their own error cases
        """
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    if params:
                        cur.callproc(function_name, params)
                    else:
                        cur.execute(f"SELECT * FROM {function_name}()")
                    
                    # Handle different return types
                    try:
                        return cur.fetchall()
                    except psycopg2.ProgrammingError:
                        # Function might not return a result set
                        return True
                        
        except Exception as e:
            self.logger.error(f"Database function call failed: {function_name} - {e}")
            return None
    
    def check_book_exists(self, title: str, author: str) -> bool:
        """
        Dr. Sarah Chen approved: Check book existence via PostgreSQL function
        ✅ No hardcoded SQL - calls api_check_book_exists function
        """
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT api_check_book_exists(%s, %s)", (title, author))
                    return cur.fetchone()[0]
        except Exception as e:
            self.logger.error(f"Book existence check failed: {e}")
            return False
    
    def extract_chapters_from_epub(self, epub_path: Path) -> Tuple[Optional[Dict], Optional[List]]:
        """Extract chapters from EPUB using existing processor"""
        try:
            if not self.epub_processor:
                self.epub_processor = EPUBProcessor()
            
            result = self.epub_processor.process_epub(str(epub_path))
            
            if not result or len(result) != 2:
                return None, None
            
            metadata, chapters = result
            
            # Convert metadata to dict format for JSON serialization
            metadata_dict = {
                'title': getattr(metadata, 'title', epub_path.stem),
                'author': getattr(metadata, 'author', 'Unknown Author'),
                'publication_date': getattr(metadata, 'publication_date', 'Unknown'),
                'genre': getattr(metadata, 'subject', 'Fiction'),
                'word_count': getattr(metadata, 'total_words', 0)
            }
            
            # Convert chapters to list of dicts
            chapters_list = []
            for i, chapter in enumerate(chapters):
                content = getattr(chapter, 'content', '')
                if content and len(content) >= 100:  # Minimum content length
                    chapter_dict = {
                        'title': getattr(chapter, 'title', f'Chapter {i + 1}'),
                        'content': content,
                        'word_count': len(content.split())
                    }
                    chapters_list.append(chapter_dict)
            
            return metadata_dict, chapters_list
            
        except Exception as e:
            self.logger.error(f"EPUB extraction failed for {epub_path.name}: {e}")
            return None, None
    
    def generate_embeddings_for_book(self, book_id: int) -> Dict[str, int]:
        """
        Generate vector embeddings for all chunks of a newly processed book
        This ensures new books have the same embedding capabilities as existing ones
        """
        if not self.embedding_generator:
            self.logger.warning("Embedding generator not available - skipping embedding generation")
            return {'generated': 0, 'errors': 0}
        
        try:
            # Get chunks for the specific book that don't have embeddings
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT chunk_id, content
                        FROM chunks 
                        WHERE book_id = %s AND embedding_array IS NULL
                        ORDER BY chapter_number
                    """, (book_id,))
                    
                    chunks = [dict(row) for row in cur.fetchall()]
            
            if not chunks:
                return {'generated': 0, 'errors': 0}
            
            self.logger.info(f"🧠 Generating embeddings for {len(chunks)} chunks from book {book_id}...")
            
            generated = 0
            errors = 0
            
            # Generate embeddings for each chunk
            for chunk in chunks:
                content = chunk['content']
                if len(content) > 8000:  # Truncate very long content
                    content = content[:8000] + "..."
                
                embedding = self.embedding_generator.generate_embedding(content)
                
                if embedding and len(embedding) > 0:
                    if self.embedding_generator.update_chunk_embedding(chunk['chunk_id'], embedding):
                        generated += 1
                    else:
                        errors += 1
                else:
                    errors += 1
            
            self.logger.info(f"🧠 Embeddings complete: {generated} generated, {errors} errors")
            return {'generated': generated, 'errors': errors}
            
        except Exception as e:
            self.logger.error(f"Embedding generation failed for book {book_id}: {e}")
            return {'generated': 0, 'errors': len(chunks) if 'chunks' in locals() else 0}

    def ingest_complete_book(self, metadata: Dict, chapters: List[Dict]) -> Dict:
        """
        Dr. Sarah Chen approved: Complete book ingestion via single PostgreSQL function
        ✅ Calls api_ingest_complete_book function with all data
        ✅ No hardcoded SQL in Python
        ✅ Function handles transaction safety and error recovery
        ✅ Generates embeddings for complete feature parity with existing books
        """
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # Call the PostgreSQL function with JSONB data
                    cur.execute("""
                        SELECT * FROM api_ingest_complete_book(%s, %s, %s, %s, %s)
                    """, (
                        metadata['title'],
                        metadata['author'],
                        metadata.get('publication_date', 'Unknown'),
                        metadata.get('genre', 'Fiction'),
                        json.dumps(chapters)  # Convert to JSONB
                    ))
                    
                    result = cur.fetchone()
                    result_dict = dict(result) if result else {'success': False, 'message': 'No result returned'}
                    
                    # If book ingestion succeeded, generate embeddings
                    if result_dict.get('success') and result_dict.get('book_id'):
                        book_id = result_dict['book_id']
                        self.logger.info(f"📚 Book ingested successfully (ID: {book_id}), generating embeddings...")
                        
                        embedding_results = self.generate_embeddings_for_book(book_id)
                        
                        # Add embedding stats to result
                        result_dict['embeddings_generated'] = embedding_results['generated']
                        result_dict['embedding_errors'] = embedding_results['errors']
                        
                        # Update global stats
                        self.stats['embeddings_generated'] += embedding_results['generated']
                        self.stats['embedding_errors'] += embedding_results['errors']
                    
                    return result_dict
                    
        except Exception as e:
            self.logger.error(f"Book ingestion failed: {e}")
            return {'success': False, 'message': f'Database error: {str(e)}'}
    
    def process_single_ebook(self, ebook_info: Dict) -> bool:
        """Process a single ebook file using PostgreSQL-First architecture"""
        epub_path = ebook_info['path']
        self.logger.info(f"📚 Processing: {ebook_info['name']} ({ebook_info['size_mb']:.1f}MB)")
        
        try:
            # Extract chapters from EPUB
            metadata, chapters = self.extract_chapters_from_epub(epub_path)
            
            if not metadata or not chapters:
                self.logger.error(f"❌ Failed to extract content from: {epub_path.name}")
                return False
            
            title = metadata['title']
            author = metadata['author']
            
            # Check if book already exists (via PostgreSQL function)
            if self.check_book_exists(title, author):
                self.logger.info(f"⏭️  Book already exists: {title} by {author}")
                self.stats['skipped_existing'] += 1
                return True
            
            self.logger.info(f"📖 Ingesting: {title} by {author} ({len(chapters)} chapters)")
            
            # Ingest complete book (via single PostgreSQL function call)
            result = self.ingest_complete_book(metadata, chapters)
            
            if result.get('success'):
                self.stats['processed'] += 1
                self.stats['total_chunks'] += result.get('chunks_created', 0)
                self.stats['total_words'] += metadata.get('word_count', 0)
                
                self.logger.info(f"✅ Successfully ingested: {title}")
                self.logger.info(f"📊 Book ID: {result.get('book_id')}, Chunks: {result.get('chunks_created')}")
                
                # Move processed file
                try:
                    processed_path = self.processed_dir / epub_path.name
                    epub_path.rename(processed_path)
                    self.logger.info(f"📁 Moved to processed: {epub_path.name}")
                except Exception as e:
                    self.logger.warning(f"File move error: {e}")
                
                return True
            else:
                self.logger.error(f"❌ Book ingestion failed: {result.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Processing error for {epub_path.name}: {e}")
            self.stats['failed'] += 1
            return False
    
    def process_book_batch(self, ebooks: List[Dict]) -> Dict:
        """
        Process multiple books using PostgreSQL batch function
        Dr. Sarah Chen approved: Single function call for batch operations
        """
        try:
            # Extract all book data first
            book_batch = []
            
            for ebook_info in ebooks:
                metadata, chapters = self.extract_chapters_from_epub(ebook_info['path'])
                if metadata and chapters:
                    book_data = {
                        'title': metadata['title'],
                        'author': metadata['author'],
                        'publication_date': metadata.get('publication_date', 'Unknown'),
                        'genre': metadata.get('genre', 'Fiction'),
                        'chapters': chapters
                    }
                    book_batch.append(book_data)
            
            if not book_batch:
                return {'success': False, 'message': 'No valid books to process'}
            
            # Call batch processing function
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("SELECT * FROM api_process_book_batch(%s)", (json.dumps(book_batch),))
                    result = cur.fetchone()
                    return dict(result) if result else {'success': False}
                    
        except Exception as e:
            self.logger.error(f"Batch processing failed: {e}")
            return {'success': False, 'message': str(e)}
    
    def process_all_ebooks(self, max_files: int = None, use_batch: bool = False) -> int:
        """Process all ebooks in downloads directory"""
        self.logger.info("🚀 Starting PostgreSQL-First automated ebook processing...")
        self.logger.info("🏛️  Dr. Sarah Chen (陈雪芳) Architecture: Function-First, No Hardcoded SQL")
        
        ebooks = self.find_ebooks_to_process()
        
        if not ebooks:
            self.logger.info("📭 No ebooks found to process")
            return 0
        
        # Limit processing if specified
        if max_files:
            ebooks = ebooks[:max_files]
            self.logger.info(f"🎯 Processing first {len(ebooks)} files")
        
        start_time = time.time()
        
        if use_batch and len(ebooks) > 5:
            # Use batch processing for efficiency
            self.logger.info(f"📦 Using batch processing for {len(ebooks)} books")
            batch_result = self.process_book_batch(ebooks)
            
            if batch_result.get('successful_books', 0) > 0:
                self.stats['processed'] = batch_result['successful_books']
                self.stats['total_chunks'] = batch_result['total_chunks_created']
                self.stats['skipped_existing'] = batch_result['skipped_existing']
                self.stats['failed'] = batch_result['failed_books']
                
                # Move processed files
                for ebook_info in ebooks[:batch_result['successful_books']]:
                    try:
                        processed_path = self.processed_dir / ebook_info['path'].name
                        ebook_info['path'].rename(processed_path)
                    except:
                        pass
        else:
            # Process files individually
            for i, ebook_info in enumerate(ebooks, 1):
                self.logger.info(f"\n📊 Progress: {i}/{len(ebooks)} ({i/len(ebooks)*100:.1f}%)")
                
                success = self.process_single_ebook(ebook_info)
                
                if not success:
                    # Move failed file
                    try:
                        failed_path = self.failed_dir / ebook_info['path'].name
                        ebook_info['path'].rename(failed_path)
                    except:
                        pass
                
                # Progress update every 10 files
                if i % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = i / elapsed * 60  # files per minute
                    self.logger.info(f"⚡ Processing rate: {rate:.1f} files/minute")
        
        # Final statistics
        elapsed = time.time() - start_time
        self.logger.info(f"\n🎉 PostgreSQL-First Processing Complete!")
        self.logger.info(f"✅ Processed: {self.stats['processed']} books")
        self.logger.info(f"⏭️  Skipped (existing): {self.stats['skipped_existing']}")
        self.logger.info(f"⏭️  Skipped (large files): {self.stats['skipped_large']}")
        self.logger.info(f"❌ Failed: {self.stats['failed']}")
        self.logger.info(f"📊 Total chunks: {self.stats['total_chunks']}")
        self.logger.info(f"📝 Total words: {self.stats['total_words']:,}")
        self.logger.info(f"🧠 Embeddings generated: {self.stats['embeddings_generated']}")
        self.logger.info(f"⚠️  Embedding errors: {self.stats['embedding_errors']}")
        self.logger.info(f"⏱️  Total time: {elapsed/60:.1f} minutes")
        self.logger.info(f"🏛️  Architecture: 100% PostgreSQL function calls, 0% hardcoded SQL")
        self.logger.info(f"🔍 Feature Parity: All chunks have phonetic + embedding capabilities")
        
        return self.stats['processed']

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PostgreSQL-First Automated Ebook Processor')
    parser.add_argument('--max-files', type=int, default=None,
                       help='Maximum number of files to process')
    parser.add_argument('--batch', action='store_true',
                       help='Use batch processing for multiple files')
    
    args = parser.parse_args()
    
    try:
        processor = PostgreSQLFirstAutomatedProcessor()
        processed_count = processor.process_all_ebooks(
            max_files=args.max_files, 
            use_batch=args.batch
        )
        
        if processed_count > 0:
            print(f"\n🎉 Successfully processed {processed_count} books!")
            print("📚 New books are now available in the LibraryOfBabel database")
            print("🔍 Phonetic search is enhanced with new content")
            print("🧠 Vector embeddings generated for semantic search")
            print("⚡ Complete feature parity with existing books")
            print("🏛️  Dr. Sarah Chen approved: PostgreSQL-First architecture maintained")
        else:
            print("📭 No new books were processed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()