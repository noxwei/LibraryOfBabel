#!/usr/bin/env python3
"""
🔄 BACKFILL EMBEDDINGS AND MD5 HASHES
====================================

Backfill existing books in database with:
1. MD5 content hashes for deduplication
2. Vector embeddings for semantic search

Team coordination:
- Linda Zhang: Workforce coordination and progress tracking  
- Lexi: Content strategy and embedding quality oversight
- DBA Team: Database integrity and optimization
- Dr. Sarah Chen: MD5 hash generation and storage
- Dr. Elena Rodriguez: Vector embedding pipeline optimization
"""

import os
import sys
import time
import logging
import psycopg2
import psycopg2.extras
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import hashlib

# Import processing components
sys.path.append('src')
try:
    from epub_processor import ChapterInfo
    from deduplication_layer import DeduplicationLayer
    from ollama_vector_embedder import OllamaVectorEmbedder
except ImportError:
    from src.epub_processor import ChapterInfo
    from src.deduplication_layer import DeduplicationLayer
    from src.ollama_vector_embedder import OllamaVectorEmbedder

class BackfillProcessor:
    """Backfill processor for existing books"""
    
    def __init__(self):
        """Initialize backfill processor"""
        # Database configuration
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': 5432
        }
        
        # Initialize components
        self.deduplication_layer = DeduplicationLayer(self.db_config)
        self.vector_embedder = OllamaVectorEmbedder(self.db_config)
        
        # Statistics
        self.stats = {
            'books_processed': 0,
            'md5_hashes_generated': 0,
            'embeddings_generated': 0,
            'books_skipped': 0,
            'errors': 0
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("BackfillProcessor")
        
        self.logger.info("🔄 Backfill Processor initialized")
        self.logger.info("📚 Ready to process existing books with MD5 and embeddings")
    
    def get_db_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(**self.db_config)
        except psycopg2.Error as e:
            self.logger.error(f"💔 Database connection failed: {e}")
            return None
    
    def get_books_needing_backfill(self) -> List[Dict]:
        """Get books that need MD5 hashes or embeddings"""
        books_to_process = []
        
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return books_to_process
                
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    # Get books missing MD5 hashes
                    cur.execute("""
                        SELECT book_id, title, author, word_count
                        FROM books 
                        WHERE md5_hash IS NULL 
                        ORDER BY book_id
                    """)
                    
                    md5_missing = cur.fetchall()
                    self.logger.info(f"📋 Books missing MD5 hashes: {len(md5_missing)}")
                    
                    # Get books missing embeddings
                    cur.execute("""
                        SELECT b.book_id, b.title, b.author, b.word_count
                        FROM books b
                        LEFT JOIN chunk_embeddings ce ON b.book_id = ce.book_id
                        WHERE ce.book_id IS NULL
                        ORDER BY b.book_id
                    """)
                    
                    embeddings_missing = cur.fetchall()
                    self.logger.info(f"🧠 Books missing embeddings: {len(embeddings_missing)}")
                    
                    # Combine and deduplicate
                    all_book_ids = set()
                    for book in md5_missing + embeddings_missing:
                        if book['book_id'] not in all_book_ids:
                            books_to_process.append({
                                'book_id': book['book_id'],
                                'title': book['title'],
                                'author': book['author'],
                                'word_count': book['word_count'],
                                'needs_md5': book in md5_missing,
                                'needs_embeddings': book in embeddings_missing
                            })
                            all_book_ids.add(book['book_id'])
                    
                    self.logger.info(f"🎯 Total books to process: {len(books_to_process)}")
                    
        except Exception as e:
            self.logger.error(f"❌ Error getting books to process: {e}")
        
        return books_to_process
    
    def get_book_chunks(self, book_id: int) -> List[ChapterInfo]:
        """Get chunks for a book and convert to ChapterInfo objects"""
        chunks = []
        
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return chunks
                
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    cur.execute("""
                        SELECT chunk_id, title, content, word_count, chapter_number
                        FROM chunks 
                        WHERE book_id = %s 
                        ORDER BY chapter_number, chunk_id
                    """, (book_id,))
                    
                    db_chunks = cur.fetchall()
                    
                    for i, chunk in enumerate(db_chunks):
                        chapter_info = ChapterInfo(
                            title=chunk['title'] or f"Chapter {i+1}",
                            content=chunk['content'] or "",
                            chapter_number=chunk['chapter_number'] or i+1,
                            section_number=None,
                            word_count=chunk['word_count'] or 0,
                            file_path=f"chunk_{chunk['chunk_id']}",
                            spine_order=i
                        )
                        chunks.append(chapter_info)
                    
                    self.logger.debug(f"📚 Retrieved {len(chunks)} chunks for book {book_id}")
                    
        except Exception as e:
            self.logger.error(f"❌ Error getting chunks for book {book_id}: {e}")
        
        return chunks
    
    def update_book_md5(self, book_id: int, chapters: List[ChapterInfo]) -> bool:
        """Generate and update MD5 hash for a book"""
        try:
            # Generate MD5 hash
            md5_hash = self.deduplication_layer.generate_content_md5(chapters)
            
            if not md5_hash:
                self.logger.warning(f"⚠️ Could not generate MD5 for book {book_id}")
                return False
            
            # Update database
            with self.get_db_connection() as conn:
                if not conn:
                    return False
                
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE books 
                        SET md5_hash = %s 
                        WHERE book_id = %s
                    """, (md5_hash, book_id))
                    
                    conn.commit()
                    
                    self.logger.debug(f"💾 Updated MD5 hash for book {book_id}: {md5_hash}")
                    self.stats['md5_hashes_generated'] += 1
                    return True
                    
        except Exception as e:
            self.logger.error(f"❌ Error updating MD5 for book {book_id}: {e}")
            return False
    
    def generate_book_embeddings(self, book_id: int, chapters: List[ChapterInfo]) -> bool:
        """Generate vector embeddings for a book"""
        try:
            # Use vector embedder to process the book
            success = self.vector_embedder.process_book_with_embeddings(book_id, chapters)
            
            if success:
                # Get embedding stats
                embedding_stats = self.vector_embedder.get_embedding_stats()
                self.stats['embeddings_generated'] += embedding_stats['embeddings_generated']
                self.logger.debug(f"🧠 Generated embeddings for book {book_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error generating embeddings for book {book_id}: {e}")
            return False
    
    def process_single_book(self, book_info: Dict) -> bool:
        """Process a single book for backfill"""
        book_id = book_info['book_id']
        title = book_info['title']
        
        self.logger.info(f"📖 Processing book {book_id}: \"{title}\"")
        
        try:
            # Get book chunks
            chapters = self.get_book_chunks(book_id)
            
            if not chapters:
                self.logger.warning(f"⚠️ No chunks found for book {book_id}")
                self.stats['books_skipped'] += 1
                return False
            
            success = True
            
            # Update MD5 hash if needed
            if book_info['needs_md5']:
                self.logger.info(f"    🔐 Generating MD5 hash...")
                md5_success = self.update_book_md5(book_id, chapters)
                if not md5_success:
                    success = False
                    self.logger.warning(f"    ❌ MD5 generation failed")
                else:
                    self.logger.info(f"    ✅ MD5 hash generated")
            
            # Generate embeddings if needed
            if book_info['needs_embeddings']:
                self.logger.info(f"    🧠 Generating vector embeddings...")
                embedding_success = self.generate_book_embeddings(book_id, chapters)
                if not embedding_success:
                    success = False
                    self.logger.warning(f"    ❌ Embedding generation failed")
                else:
                    self.logger.info(f"    ✅ Vector embeddings generated")
            
            if success:
                self.stats['books_processed'] += 1
                self.logger.info(f"    ✅ Book {book_id} backfill complete")
            else:
                self.stats['errors'] += 1
                self.logger.error(f"    ❌ Book {book_id} backfill failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error processing book {book_id}: {e}")
            self.stats['errors'] += 1
            return False
    
    def run_backfill(self, batch_size: int = 10):
        """Run the complete backfill process"""
        self.logger.info("🚀 Starting backfill process for existing books...")
        
        # Get books that need processing
        books_to_process = self.get_books_needing_backfill()
        
        if not books_to_process:
            self.logger.info("✅ No books need backfill - all up to date!")
            return
        
        self.logger.info(f"📋 Processing {len(books_to_process)} books in batches of {batch_size}")
        
        start_time = time.time()
        
        # Process books in batches
        for i, book_info in enumerate(books_to_process[:batch_size], 1):
            self.logger.info(f"[{i}/{min(batch_size, len(books_to_process))}] Processing...")
            
            self.process_single_book(book_info)
            
            # Small delay between books
            time.sleep(0.5)
        
        # Calculate total time
        total_time = time.time() - start_time
        
        # Print final statistics
        self.print_final_stats(total_time)
    
    def print_final_stats(self, total_time: float):
        """Print final processing statistics"""
        print("\n📊 BACKFILL PROCESSING COMPLETE")
        print("=" * 50)
        print(f"✅ Books processed: {self.stats['books_processed']}")
        print(f"🔐 MD5 hashes generated: {self.stats['md5_hashes_generated']}")
        print(f"🧠 Embeddings generated: {self.stats['embeddings_generated']}")
        print(f"⏭️ Books skipped: {self.stats['books_skipped']}")
        print(f"❌ Errors: {self.stats['errors']}")
        print(f"⏱️ Total time: {total_time:.1f}s")
        
        if self.stats['books_processed'] > 0:
            avg_time = total_time / self.stats['books_processed']
            print(f"📈 Average time per book: {avg_time:.1f}s")
        
        print("\n🎯 Backfill Summary:")
        if self.stats['errors'] == 0:
            print("🎉 All books processed successfully!")
        else:
            print(f"⚠️ {self.stats['errors']} books had errors")

def main():
    """Main execution function"""
    print("🔄 BACKFILL PROCESSOR - MD5 HASHES & VECTOR EMBEDDINGS")
    print("=" * 65)
    print("👔 Linda Zhang: Coordinating backfill operation")
    print("🤖 Lexi: Monitoring embedding quality")
    print("📚 DBA Team: Ensuring database integrity")
    print()
    
    try:
        processor = BackfillProcessor()
        
        # Run backfill on first 5 books as test
        processor.run_backfill(batch_size=5)
        
    except Exception as e:
        print(f"❌ Backfill failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()