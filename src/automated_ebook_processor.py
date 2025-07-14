#!/usr/bin/env python3
"""
Automated Ebook Processing Agent - LibraryOfBabel Phase 5
=========================================================

Complete automation pipeline that:
1. Monitors downloads folder for new ebooks
2. Processes them through existing EPUB pipeline
3. Ingests into PostgreSQL database
4. Updates tracking status
5. Focuses on small files first (<50MB priority, <100MB max)

Leverages existing proven infrastructure:
- EPUBProcessor for text extraction
- BatchProcessor for scalable processing  
- DatabaseIngestor for PostgreSQL integration
- File size filtering for optimal processing
"""

import os
import sys
import time
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import psycopg2

# Import existing processing components
sys.path.append('src')
from epub_processor import EPUBProcessor
from batch_processor import BatchProcessor
from database_ingestion import DatabaseIngestor
from deduplication_layer import DeduplicationLayer  # DBA Team deduplication system
from ollama_vector_embedder import OllamaVectorEmbedder  # Vector embedding integration
# from frictionless_ebook_harvester import FrictionlessEbookHarvester  # Removed MAM dependency

class AutomatedEbookProcessor:
    """Automated agent for processing downloaded ebooks into database"""
    
    def __init__(self):
        """Initialize the automated processor"""
        self.downloads_dir = Path("ebooks/downloads")
        self.processed_dir = Path("ebooks/processed")
        self.large_files_dir = Path("ebooks/large_files")
        self.failed_dir = Path("ebooks/failed")
        
        # File size limits (matching harvester)
        self.max_file_size_mb = 100
        self.large_file_threshold_mb = 50
        
        # Processing components
        self.epub_processor = EPUBProcessor("config/system_configs/processing_config.json")
        self.batch_processor = BatchProcessor("config/system_configs/processing_config.json")
        
        # Database configuration (matching working search API)
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': 5432
        }
        
        # DBA Team deduplication system
        self.deduplication_layer = DeduplicationLayer(self.db_config)
        
        # Vector embedding system (Lexi + Dr. Elena integration)
        self.vector_embedder = OllamaVectorEmbedder(self.db_config)
        
        # Statistics
        self.stats = {
            'processed': 0,
            'skipped_large': 0,
            'skipped_format': 0,
            'failed': 0,
            'total_words': 0
        }
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ebook_processor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Create directories
        self._setup_directories()
        
        self.logger.info("🤖 Automated Ebook Processor initialized")
        self.logger.info(f"📁 Monitoring: {self.downloads_dir}")
        self.logger.info(f"📏 Size limits: <{self.large_file_threshold_mb}MB priority, <{self.max_file_size_mb}MB max")
    
    def _setup_directories(self):
        """Create necessary directories"""
        for directory in [self.processed_dir, self.large_files_dir, self.failed_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_file_size_mb(self, file_path: Path) -> float:
        """Get file size in MB"""
        try:
            size_bytes = file_path.stat().st_size
            return size_bytes / (1024 * 1024)
        except:
            return 0.0
    
    def find_ebooks_to_process(self) -> List[Dict]:
        """Find ebooks in downloads directory that need processing"""
        ebooks = []
        
        if not self.downloads_dir.exists():
            return ebooks
        
        # Supported formats
        ebook_formats = ['.epub', '.mobi', '.azw3', '.azw']
        
        # Scan downloads directory
        for item in self.downloads_dir.rglob('*'):
            if item.is_file() and item.suffix.lower() in ebook_formats:
                file_size_mb = self.get_file_size_mb(item)
                
                ebook_info = {
                    'path': item,
                    'name': item.name,
                    'format': item.suffix.lower().replace('.', ''),
                    'size_mb': file_size_mb,
                    'is_large': file_size_mb > self.large_file_threshold_mb,
                    'is_too_large': file_size_mb > self.max_file_size_mb
                }
                
                ebooks.append(ebook_info)
        
        # Sort by size (small files first), then format priority
        format_priority = {'epub': 3, 'mobi': 2, 'azw3': 1, 'azw': 1}
        
        ebooks.sort(key=lambda x: (
            x['is_large'],  # Small files first
            -format_priority.get(x['format'], 0),  # Better formats first
            x['size_mb']  # Smaller files first
        ))
        
        return ebooks
    
    def check_already_processed(self, ebook_path: Path) -> bool:
        """Check if this ebook has already been processed (improved by DBA team)"""
        # Check if file exists in processed directory
        processed_file = self.processed_dir / ebook_path.name
        if processed_file.exists():
            return True
        
        # Check database for existing book by file path (Dr. Sarah's enhancement)
        try:
            import psycopg2
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Check if book already exists in database by file path
            cursor.execute("""
                SELECT book_id FROM books 
                WHERE file_path = %s OR file_path LIKE %s
            """, (str(ebook_path), f"%{ebook_path.name}%"))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                self.logger.debug(f"    📋 Book already in database: ID {result[0]}")
                return True
                
        except Exception as e:
            self.logger.debug(f"    ⚠️ Database check failed: {e}")
        
        return False
    
    def process_single_ebook(self, ebook_info: Dict) -> bool:
        """Process a single ebook through the complete pipeline"""
        ebook_path = ebook_info['path']
        
        try:
            self.logger.info(f"📖 Processing: {ebook_path.name}")
            self.logger.info(f"    📏 Size: {ebook_info['size_mb']:.1f}MB ({ebook_info['format'].upper()})")
            
            # Skip files that are too large
            if ebook_info['is_too_large']:
                self.logger.info(f"    ⏭️ Skipping: File too large ({ebook_info['size_mb']:.1f}MB > {self.max_file_size_mb}MB)")
                # Move to large files directory
                large_file_path = self.large_files_dir / ebook_path.name
                shutil.move(str(ebook_path), str(large_file_path))
                self.stats['skipped_large'] += 1
                return False
            
            # Mark large files but still process
            if ebook_info['is_large']:
                self.logger.info(f"    🟡 Large file warning: {ebook_info['size_mb']:.1f}MB > {self.large_file_threshold_mb}MB")
            
            # Convert non-EPUB formats to EPUB if needed
            if ebook_info['format'] != 'epub':
                epub_path = self._convert_to_epub(ebook_path)
                if not epub_path:
                    self.logger.error(f"    ❌ Format conversion failed")
                    self._move_to_failed(ebook_path)
                    self.stats['failed'] += 1
                    return False
                processing_path = epub_path
            else:
                processing_path = ebook_path
            
            # Process EPUB through existing pipeline
            metadata, chapters = self.epub_processor.process_epub(str(processing_path))
            
            if not chapters:
                self.logger.warning(f"    ⚠️ No chapters extracted")
                self._move_to_failed(ebook_path)
                self.stats['failed'] += 1
                return False
            
            # DBA Team deduplication check
            self.logger.info(f"    🔍 DBA Team: Checking for duplicates...")
            is_safe, duplicates = self.deduplication_layer.is_safe_to_ingest(metadata, chapters)
            
            if not is_safe:
                self.logger.warning(f"    🚫 DUPLICATE DETECTED - Skipping ingestion")
                for dup in duplicates:
                    if dup.confidence >= 0.75:
                        self.logger.warning(f"       📚 {dup.match_type}: {dup.confidence:.2f} - {dup.match_details}")
                
                # Log the duplicate prevention
                self.deduplication_layer.log_duplicate_prevention(metadata, duplicates, "BLOCKED_DUPLICATE")
                
                # Move to processed directory (don't try again)
                processed_path = self.processed_dir / ebook_path.name
                shutil.move(str(ebook_path), str(processed_path))
                self.stats['skipped_format'] += 1  # Track as skipped
                return False
            
            self.logger.info(f"    ✅ DBA Team: No duplicates found - proceeding with ingestion")
            
            # Ingest into PostgreSQL database with MD5 hash
            success = self._ingest_into_database(metadata, chapters)
            
            if success:
                self.logger.info(f"    ✅ Successfully processed: {len(chapters)} chapters, {metadata.total_words:,} words")
                
                # Move to processed directory
                processed_path = self.processed_dir / ebook_path.name
                shutil.move(str(ebook_path), str(processed_path))
                
                # Clean up converted file if it exists
                if ebook_info['format'] != 'epub' and epub_path and epub_path != ebook_path:
                    try:
                        epub_path.unlink()
                    except:
                        pass
                
                self.stats['processed'] += 1
                self.stats['total_words'] += metadata.total_words
                return True
            else:
                self.logger.error(f"    ❌ Database ingestion failed")
                self._move_to_failed(ebook_path)
                self.stats['failed'] += 1
                return False
                
        except Exception as e:
            self.logger.error(f"    ❌ Processing error: {e}")
            self._move_to_failed(ebook_path)
            self.stats['failed'] += 1
            return False
    
    def _convert_to_epub(self, file_path: Path) -> Optional[Path]:
        """Convert MOBI/AZW to EPUB using calibre"""
        try:
            # Check if calibre is available
            import subprocess
            result = subprocess.run(['which', 'ebook-convert'], capture_output=True)
            if result.returncode != 0:
                self.logger.warning("    ⚠️ Calibre not found - skipping format conversion")
                return None
            
            # Convert to EPUB
            epub_path = file_path.with_suffix('.epub')
            cmd = ['ebook-convert', str(file_path), str(epub_path)]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and epub_path.exists():
                self.logger.info(f"    🔄 Converted to EPUB: {epub_path.name}")
                return epub_path
            else:
                self.logger.error(f"    ❌ Conversion failed: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"    ❌ Conversion error: {e}")
            return None
    
    def _ingest_into_database(self, metadata, chapters) -> bool:
        """Ingest processed book into PostgreSQL database with MD5 hash"""
        try:
            import psycopg2
            
            # Generate MD5 hash for this book (Dr. Sarah Chen's requirement)
            content_md5 = self.deduplication_layer.generate_content_md5(chapters)
            
            # Direct database connection
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Insert book metadata with MD5 hash
            cursor.execute("""
                INSERT INTO books (
                    title, author, publisher, publication_date, language,
                    isbn, description, word_count, file_path, processed_date, md5_hash
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
                RETURNING book_id
            """, (
                metadata.title,
                metadata.author,
                metadata.publisher,
                metadata.publication_date,
                metadata.language,
                metadata.isbn,
                metadata.description,
                metadata.total_words,
                metadata.file_path,
                content_md5
            ))
            
            book_id = cursor.fetchone()[0]
            
            # Insert chunks
            chunks_inserted = 0
            for i, chapter in enumerate(chapters):
                chunk_id = f"{book_id}_chapter_{i+1}"
                
                cursor.execute("""
                    INSERT INTO chunks (
                        chunk_id, book_id, chunk_type, title, content,
                        word_count, character_count, chapter_number
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    chunk_id,
                    book_id,
                    'chapter',
                    chapter.title,
                    chapter.content,
                    chapter.word_count,
                    len(chapter.content),
                    chapter.chapter_number
                ))
                chunks_inserted += 1
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.logger.info(f"    ✅ Database: {chunks_inserted} chunks inserted for book ID {book_id}")
            
            # Generate vector embeddings (Lexi + DBA team integration)
            self.logger.info(f"    🧠 Generating vector embeddings...")
            embedding_success = self.vector_embedder.process_book_with_embeddings(book_id, chapters)
            
            if embedding_success:
                self.logger.info(f"    ✅ Vector embeddings generated and stored")
            else:
                self.logger.warning(f"    ⚠️ Vector embedding generation failed (book still processed)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Database ingestion error: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return False
    
    def _move_to_failed(self, file_path: Path):
        """Move failed file to failed directory"""
        try:
            failed_path = self.failed_dir / file_path.name
            shutil.move(str(file_path), str(failed_path))
        except Exception as e:
            self.logger.error(f"Failed to move file to failed directory: {e}")
    
    def update_tracking_database(self, processed_count: int):
        """Update the ebook tracking database with processing status"""
        try:
            # This would update the tracking database to mark books as processed
            # For now, just log the status
            self.logger.info(f"📊 Processing session complete: {processed_count} books processed")
            
        except Exception as e:
            self.logger.error(f"Tracking database update error: {e}")
    
    def print_statistics(self):
        """Print processing statistics"""
        total = sum(self.stats.values()) - self.stats['total_words']  # Exclude word count
        
        print(f"\n📊 PROCESSING STATISTICS:")
        print(f"   ✅ Processed: {self.stats['processed']}")
        print(f"   ⏭️ Skipped (large): {self.stats['skipped_large']}")
        print(f"   ⏭️ Skipped (format): {self.stats['skipped_format']}")
        print(f"   ❌ Failed: {self.stats['failed']}")
        print(f"   📝 Total words: {self.stats['total_words']:,}")
        
        if total > 0:
            success_rate = (self.stats['processed'] / total) * 100
            print(f"   📈 Success rate: {success_rate:.1f}%")
    
    def process_all_ebooks(self, batch_size: int = 10) -> int:
        """Process all ebooks in downloads directory"""
        self.logger.info("🚀 Starting automated ebook processing...")
        
        # Find ebooks to process
        ebooks = self.find_ebooks_to_process()
        
        if not ebooks:
            self.logger.info("📭 No ebooks found to process")
            return 0
        
        self.logger.info(f"📚 Found {len(ebooks)} ebooks to process")
        
        # Process in batches
        processed_count = 0
        
        for i, ebook_info in enumerate(ebooks[:batch_size], 1):
            # Skip if already processed
            if self.check_already_processed(ebook_info['path']):
                self.logger.info(f"[{i}/{min(batch_size, len(ebooks))}] ⏭️ Already processed: {ebook_info['name']}")
                continue
            
            self.logger.info(f"[{i}/{min(batch_size, len(ebooks))}] 🔄 Processing: {ebook_info['name']}")
            
            if self.process_single_ebook(ebook_info):
                processed_count += 1
            
            # Small delay between files
            time.sleep(1)
        
        # Update tracking
        self.update_tracking_database(processed_count)
        
        # Print statistics
        self.print_statistics()
        
        self.logger.info(f"🎉 Processing complete: {processed_count} books successfully processed")
        
        return processed_count
    
    def run_continuous_monitoring(self, check_interval: int = 300):
        """Run continuous monitoring of downloads directory"""
        self.logger.info(f"🔄 Starting continuous monitoring (checking every {check_interval}s)")
        
        try:
            while True:
                processed = self.process_all_ebooks(batch_size=5)
                
                if processed > 0:
                    self.logger.info(f"✅ Processed {processed} new ebooks")
                else:
                    self.logger.info("😴 No new ebooks to process")
                
                self.logger.info(f"⏰ Waiting {check_interval}s before next check...")
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            self.logger.info("⏹️ Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"❌ Monitoring error: {e}")


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated Ebook Processor")
    parser.add_argument('--mode', choices=['batch', 'continuous'], default='batch',
                       help='Processing mode: batch (process once) or continuous (monitor)')
    parser.add_argument('--batch-size', type=int, default=10,
                       help='Number of books to process in batch mode')
    parser.add_argument('--interval', type=int, default=300,
                       help='Check interval in seconds for continuous mode')
    
    args = parser.parse_args()
    
    try:
        processor = AutomatedEbookProcessor()
        
        if args.mode == 'batch':
            processor.process_all_ebooks(batch_size=args.batch_size)
        else:
            processor.run_continuous_monitoring(check_interval=args.interval)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()