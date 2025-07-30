#!/usr/bin/env python3
"""
Simplified Automated Ebook Processor - Works with Current Environment
====================================================================

Processes new ebooks from downloads folder with:
1. EPUB text extraction and chunking  
2. Database ingestion with duplicate detection
3. Phonetic enhancement for search optimization
4. Works without complex dependencies like spacy

Optimized for the current LibraryOfBabel system.
"""

import os
import sys
import time
import logging
import json
import re
import hashlib
import psycopg2
import psycopg2.extras
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Add src to path for imports
sys.path.append('src')
from epub_processor import EPUBProcessor

class SimplifiedAutomatedProcessor:
    """Simplified automated processor that works with current environment"""
    
    def __init__(self):
        """Initialize the processor"""
        self.downloads_dir = Path("src/ebooks/downloads")
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
        except:
            # Fallback initialization
            self.epub_processor = None
        
        # Statistics
        self.stats = {
            'processed': 0,
            'skipped_large': 0,
            'skipped_existing': 0,
            'failed': 0,
            'total_words': 0,
            'total_chunks': 0
        }
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('automated_ebook_processing.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Create directories
        self._setup_directories()
        
        self.logger.info("🤖 Simplified Automated Ebook Processor Ready")
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
        return ebooks
    
    def check_book_exists(self, title: str, author: str) -> bool:
        """Check if book already exists in database"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COUNT(*) FROM books 
                        WHERE LOWER(title) = LOWER(%s) AND LOWER(author) = LOWER(%s)
                    """, (title, author))
                    return cur.fetchone()[0] > 0
        except Exception as e:
            self.logger.error(f"Database check error: {e}")
            return False
    
    def create_chapter_chunks(self, chapters: List, title: str) -> List[Dict]:
        """Create chapter-level chunks matching existing database structure"""  
        if not chapters:
            return []
        
        chunks = []
        
        for i, chapter in enumerate(chapters):
            # Chapters are also dataclass objects, not dicts
            content = getattr(chapter, 'content', '')
            if not content or len(content) < 100:
                continue
            
            # Create chunk matching existing database structure
            chunk_data = {
                'content': content,
                'chapter_number': i + 1,
                'word_count': len(content.split()),
                'title': getattr(chapter, 'title', f'Chapter {i + 1}')
            }
            
            # Only include chunks with substantial content (matching existing pattern)
            if chunk_data['word_count'] >= 100:  # Match existing minimum size
                chunks.append(chunk_data)
        
        self.logger.info(f"📑 Created {len(chunks)} chapter chunks for: {title}")
        return chunks
    
    def add_phonetic_enhancement(self, content: str) -> Dict[str, str]:
        """Add phonetic enhancement to content"""
        try:
            # Generate soundex and metaphone representations
            # Using simple approximation since we don't have full phonetic libraries
            words = re.findall(r'\b[a-zA-Z]+\b', content.lower())
            
            # Simple soundex approximation (first letter + remove vowels)
            soundex_words = []
            for word in words[:20]:  # Limit to first 20 words for performance
                if len(word) > 2:
                    soundex = word[0] + re.sub(r'[aeiou]', '', word[1:])
                    soundex_words.append(soundex[:4])  # Limit to 4 chars
            
            # Audio-book normalized (remove common homophones)
            audiobook_normalized = content.lower()
            homophones = {
                'there': 'their', 'to': 'too', 'your': 'youre',
                'its': 'it\'s', 'than': 'then'
            }
            for orig, repl in homophones.items():
                audiobook_normalized = audiobook_normalized.replace(orig, repl)
            
            return {
                'content_soundex': ' '.join(soundex_words),
                'content_metaphone': ' '.join(words[:15]),  # Simple approximation
                'content_audiobook_normalized': audiobook_normalized[:500]  # Limit length
            }
        except Exception as e:
            self.logger.error(f"Phonetic enhancement error: {e}")
            return {
                'content_soundex': '',
                'content_metaphone': '',
                'content_audiobook_normalized': content[:500]
            }
    
    def insert_book_and_chunks(self, book_data: Dict, chunks: List[Dict]) -> bool:
        """Insert book and chunks into database with phonetic enhancement"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    # Insert book
                    cur.execute("""
                        INSERT INTO books (title, author, publication_date, genre, word_count, processed_date)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING book_id
                    """, (
                        book_data['title'][:500],  # Limit title length
                        book_data['author'][:255],  # Limit author length  
                        book_data.get('publication_date', 'Unknown')[:100],
                        book_data.get('genre', 'Fiction')[:100],
                        book_data.get('word_count', 0),
                        datetime.now()
                    ))
                    
                    book_id = cur.fetchone()[0]
                    self.logger.info(f"📖 Inserted book: {book_data['title']} (ID: {book_id})")
                    
                    # Insert chunks with phonetic enhancement
                    chunk_count = 0
                    for chunk_data in chunks:
                        chunk_content = chunk_data['content']
                        chapter_num = chunk_data['chapter_number']
                        
                        if len(chunk_content) < 100:  # Skip very short chunks
                            continue
                        
                        # Generate phonetic enhancements
                        phonetic_data = self.add_phonetic_enhancement(chunk_content)
                        
                        chunk_id = f"{book_id}_chapter_{chapter_num}"
                        
                        cur.execute("""
                            INSERT INTO chunks (
                                chunk_id, book_id, title, author, content, word_count,
                                content_soundex, content_metaphone, content_audiobook_normalized
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            chunk_id,
                            book_id,
                            book_data['title'][:500],
                            book_data['author'][:255],
                            chunk_content,
                            chunk_data['word_count'],
                            phonetic_data['content_soundex'],
                            phonetic_data['content_metaphone'], 
                            phonetic_data['content_audiobook_normalized']
                        ))
                        chunk_count += 1
                    
                    conn.commit()
                    self.logger.info(f"✅ Added {chunk_count} chunks with phonetic enhancement")
                    self.stats['total_chunks'] += chunk_count
                    return True
                    
        except Exception as e:
            self.logger.error(f"Database insertion error: {e}")
            return False
    
    def process_single_ebook(self, ebook_info: Dict) -> bool:
        """Process a single ebook file"""
        epub_path = ebook_info['path']
        self.logger.info(f"📚 Processing: {ebook_info['name']} ({ebook_info['size_mb']:.1f}MB)")
        
        try:
            # Initialize EPUB processor if needed
            if not self.epub_processor:
                self.epub_processor = EPUBProcessor()
            
            # Process EPUB file
            result = self.epub_processor.process_epub(str(epub_path))
            
            if not result or len(result) != 2:
                self.logger.error(f"❌ Failed to process EPUB: {epub_path.name}")
                return False
            
            metadata, chapters = result
            
            # Extract basic information (metadata is a dataclass, not dict)
            title = getattr(metadata, 'title', epub_path.stem)
            author = getattr(metadata, 'author', 'Unknown Author')
            
            # Check if book already exists
            if self.check_book_exists(title, author):
                self.logger.info(f"⏭️  Book already exists: {title} by {author}")
                self.stats['skipped_existing'] += 1
                return True
            
            # Create chapter-level chunks matching existing database structure
            chunks = self.create_chapter_chunks(chapters, title)
            
            if not chunks:
                self.logger.warning(f"⚠️ No valid chunks created for: {title}")
                self.logger.info(f"📝 Found {len(chapters)} chapters from EPUB processor")
                return False
            
            # Prepare book data
            book_data = {
                'title': title,
                'author': author,
                'publication_date': getattr(metadata, 'publication_date', 'Unknown'),
                'genre': getattr(metadata, 'subject', 'Fiction'),
                'word_count': getattr(metadata, 'total_words', 0)
            }
            
            # Insert into database
            if self.insert_book_and_chunks(book_data, chunks):
                self.stats['processed'] += 1
                self.stats['total_words'] += book_data['word_count']
                
                # Move processed file
                try:
                    processed_path = self.processed_dir / epub_path.name
                    epub_path.rename(processed_path) 
                    self.logger.info(f"📁 Moved to processed: {epub_path.name}")
                except Exception as e:
                    self.logger.warning(f"File move error: {e}")
                
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Processing error for {epub_path.name}: {e}")
            self.stats['failed'] += 1
            return False
    
    def process_all_ebooks(self, max_files: int = None) -> int:
        """Process all ebooks in downloads directory"""
        self.logger.info("🚀 Starting automated ebook processing...")
        
        ebooks = self.find_ebooks_to_process()
        
        if not ebooks:
            self.logger.info("📭 No ebooks found to process")
            return 0
        
        # Limit processing if specified
        if max_files:
            ebooks = ebooks[:max_files]
            self.logger.info(f"🎯 Processing first {len(ebooks)} files")
        
        start_time = time.time()
        
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
        self.logger.info(f"\n🎉 Processing Complete!")
        self.logger.info(f"✅ Processed: {self.stats['processed']} books")
        self.logger.info(f"⏭️  Skipped (existing): {self.stats['skipped_existing']}")
        self.logger.info(f"❌ Failed: {self.stats['failed']}")
        self.logger.info(f"📊 Total chunks: {self.stats['total_chunks']}")
        self.logger.info(f"📝 Total words: {self.stats['total_words']:,}")
        self.logger.info(f"⏱️  Total time: {elapsed/60:.1f} minutes")
        
        return self.stats['processed']

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Simplified Automated Ebook Processor')
    parser.add_argument('--max-files', type=int, default=None,
                       help='Maximum number of files to process')
    
    args = parser.parse_args()
    
    try:
        processor = SimplifiedAutomatedProcessor()
        processed_count = processor.process_all_ebooks(max_files=args.max_files)
        
        if processed_count > 0:
            print(f"\n🎉 Successfully processed {processed_count} books!")
            print("📚 New books are now available in the LibraryOfBabel database")
            print("🔍 Phonetic search is enhanced with new content")
        else:
            print("📭 No new books were processed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()