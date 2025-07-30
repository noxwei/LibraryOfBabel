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
import requests
import re
import json

# Import existing processing components
sys.path.append('src')
from epub_processor import EPUBProcessor
from batch_processor import BatchProcessor
from database_ingestion import DatabaseIngestor
from deduplication_layer import DeduplicationLayer  # DBA Team deduplication system
# from advanced_semantic_chunker import AdvancedSemanticChunker  # Dr. Sarah Chen's semantic chunker - disabled due to spacy dependency
# from multimodal_embedding_pipeline import MultiModalEmbeddingPipeline  # Dr. Sarah Chen's multi-modal embeddings - disabled
# from advanced_genre_classifier import AdvancedGenreClassifier  # Enhanced classification with HTML cleaning - disabled
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
        
        # Dr. Sarah Chen's advanced processing systems - disabled due to dependencies
        # self.semantic_chunker = AdvancedSemanticChunker(self.db_config)
        # self.embedding_pipeline = MultiModalEmbeddingPipeline(self.db_config)
        
        # Enhanced genre classification with HTML cleaning and description enhancement - disabled
        # self.genre_classifier = AdvancedGenreClassifier(self.db_config)
        
        # Enhanced classification system
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = "llama3.2:3b"  # Fast, accurate model
        
        # Valid genres with enhanced list
        self.valid_genres = [
            "Romance", "Literary Fiction", "Science Fiction", "Fantasy",
            "Mystery & Thriller", "Historical Fiction", "Contemporary Fiction",
            "Self-Help", "Biography & Memoir", "Psychology", "Philosophy",
            "Business & Economics", "History", "Science & Nature",
            "Programming & Technology", "Data Science & Analytics",
            "Religion & Spirituality", "Political Science", "Academic & Research",
            "Health & Medicine", "True Crime", "Travel", "Art & Design"
        ]
        
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
        
        # Setup Dr. Sarah Chen's multi-modal infrastructure
        self._setup_multimodal_infrastructure()
        
        self.logger.info("🤖 Automated Ebook Processor initialized")
        self.logger.info(f"📁 Monitoring: {self.downloads_dir}")
        self.logger.info(f"📏 Size limits: <{self.large_file_threshold_mb}MB priority, <{self.max_file_size_mb}MB max")
        self.logger.info("🏛️ Dr. Sarah Chen's multi-modal processing enabled")
    
    def _setup_directories(self):
        """Create necessary directories"""
        for directory in [self.processed_dir, self.large_files_dir, self.failed_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _setup_multimodal_infrastructure(self):
        """Setup Dr. Sarah Chen's multi-modal embedding infrastructure"""
        try:
            self.logger.info("🗂️ Setting up multi-modal embedding infrastructure...")
            if self.embedding_pipeline.setup_multimodal_tables():
                self.logger.info("✅ Multi-modal infrastructure ready")
            else:
                self.logger.warning("⚠️ Multi-modal infrastructure setup failed")
        except Exception as e:
            self.logger.error(f"❌ Multi-modal setup error: {e}")
    
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
            
            # Dr. Sarah Chen's Advanced Processing Pipeline
            self.logger.info(f"    🏛️ Dr. Sarah Chen: Starting advanced semantic processing...")
            
            # Step 1: Create semantic chunks
            self.logger.info(f"    🏗️ Creating semantic chunks...")
            chunk_results = self.semantic_chunker.process_book_semantic_chunks(book_id, ['medium'])
            
            if 'error' not in chunk_results:
                # Save semantic chunks
                if self.semantic_chunker.save_semantic_chunks_to_db(chunk_results):
                    chunk_count = chunk_results['chunk_levels']['medium']['chunk_count']
                    self.logger.info(f"    ✅ Created {chunk_count} semantic chunks")
                    
                    # Step 2: Generate multi-modal embeddings
                    self.logger.info(f"    🧠 Generating multi-modal embeddings...")
                    embedding_results = self.embedding_pipeline.process_book_multimodal_pipeline(
                        book_id=book_id,
                        chunk_level='medium',
                        max_workers=2  # Conservative for automation
                    )
                    
                    if embedding_results['status'] in ['completed', 'completed_with_save_errors']:
                        self.logger.info(f"    ✅ Generated {embedding_results['embeddings_generated']} multi-modal embeddings")
                        self.logger.info(f"    🎯 Processing rate: {embedding_results['chunks_per_second']:.1f} chunks/sec")
                    else:
                        self.logger.warning(f"    ⚠️ Multi-modal embedding generation failed: {embedding_results.get('message', 'Unknown error')}")
                else:
                    self.logger.warning(f"    ⚠️ Failed to save semantic chunks")
            else:
                self.logger.warning(f"    ⚠️ Semantic chunking failed: {chunk_results['error']}")
            
            # Enhanced genre classification with description enhancement
            self.logger.info(f"    🧠 Using advanced AI genre classifier...")
            try:
                result = self.genre_classifier.classify_book(book_id, use_semantic_chunks=True)
                if 'error' not in result:
                    self.logger.info(f"    🎯 Primary: {result['primary_genre']}")
                    if result.get('secondary_genre'):
                        self.logger.info(f"    🎯 Secondary: {result['secondary_genre']}")
                    if result.get('tertiary_genre'):
                        self.logger.info(f"    🎯 Tertiary: {result['tertiary_genre']}")
                    self.logger.info(f"    📊 Confidence: {result['confidence']:.3f}")
                    self.logger.info(f"    🧠 Used semantic chunks: {result['used_semantic_chunks']}")
                    self.logger.info(f"    ✅ Enhanced genre classification completed")
                else:
                    self.logger.warning(f"    ⚠️ Genre classification failed: {result['error']}")
            except Exception as e:
                self.logger.warning(f"    ⚠️ Genre classification error: {e}")
            
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

    def is_front_matter(self, content):
        """Advanced front matter detection"""
        content_lower = content.lower().strip()
        
        # Strong front matter indicators
        strong_indicators = [
            'copyright', '©', 'all rights reserved', 'published by',
            'isbn', 'library of congress', 'cataloging', 'first published',
            'this book is sold', 'reproduction or translation', 'without permission',
            'printed in', 'designed by', 'cover design', 'jacket design'
        ]
        
        # Moderate indicators
        moderate_indicators = [
            'dedication', 'acknowledgments', 'acknowledgement', 'table of contents',
            'contents', 'index', 'bibliography', 'notes', 'about the author',
            'also by', 'other books', 'praise for', 'advance praise'
        ]
        
        # Weak indicators (need multiple)
        weak_indicators = [
            'publisher', 'edition', 'printing', 'version', 'imprint'
        ]
        
        # Check for strong indicators (any one triggers)
        for indicator in strong_indicators:
            if indicator in content_lower:
                return True
        
        # Check for moderate indicators (1-2 trigger)
        moderate_count = sum(1 for indicator in moderate_indicators if indicator in content_lower)
        if moderate_count >= 1:
            return True
        
        # Check for weak indicators (need multiple)
        weak_count = sum(1 for indicator in weak_indicators if indicator in content_lower)
        if weak_count >= 2:
            return True
        
        # Very short chunks that are just structural
        if len(content.strip()) < 150:
            structural_words = ['chapter', 'part', 'section', 'book', 'volume', 'preface', 'foreword', 'introduction']
            if any(word in content_lower for word in structural_words) and len(content.strip().split()) < 20:
                return True
        
        # Mostly numbers/dates/codes (catalog info)
        if re.search(r'^\s*[\d\-\.\s]+$', content) or re.search(r'isbn[\d\-\s]+', content_lower):
            return True
        
        return False
    
    def is_actual_content(self, content):
        """Verify this is actual book content"""
        content_clean = re.sub(r'<[^>]+>', '', content).strip()
        
        # Must have reasonable length
        if len(content_clean) < 100:
            return False
        
        # Check for narrative/content indicators
        content_indicators = [
            # Fiction indicators
            'said', 'asked', 'replied', 'thought', 'looked', 'walked', 'felt',
            'character', 'protagonist', 'story', 'narrative', 'dialogue',
            # Non-fiction indicators  
            'research', 'study', 'analysis', 'theory', 'evidence', 'argument',
            'according', 'however', 'therefore', 'furthermore', 'moreover',
            # General content indicators
            'because', 'although', 'while', 'when', 'where', 'what', 'how', 'why'
        ]
        
        indicator_count = sum(1 for indicator in content_indicators if indicator in content.lower())
        
        # Should have some content indicators
        return indicator_count >= 2

    def get_optimized_content_sample(self, book_id, chapters):
        """Get optimized content sample avoiding front matter completely"""
        # Filter out front matter
        content_chunks = []
        front_matter_count = 0
        
        for chapter in chapters:
            if self.is_front_matter(chapter.content):
                front_matter_count += 1
            elif self.is_actual_content(chapter.content):
                content_chunks.append(chapter)
        
        # Ensure we have actual content
        if not content_chunks:
            # Fallback: take chunks from middle/end, avoiding first few
            fallback_start = max(len(chapters) // 4, 3)
            content_chunks = chapters[fallback_start:fallback_start + 5]
        
        # Select diverse content chunks strategically
        if len(content_chunks) >= 4:
            # Early, early-middle, late-middle, late content
            selected = [
                content_chunks[0],                                          # Early content
                content_chunks[len(content_chunks) // 3],                  # Early-middle
                content_chunks[len(content_chunks) * 2 // 3],              # Late-middle
                content_chunks[-1]                                         # Late content
            ]
        elif len(content_chunks) >= 2:
            # Beginning and end
            selected = [content_chunks[0], content_chunks[-1]]
        else:
            selected = content_chunks
        
        # Create optimized sample
        samples = []
        for chapter in selected:
            # Clean and extract meaningful content
            clean_content = re.sub(r'<[^>]+>', '', chapter.content)
            clean_content = re.sub(r'\s+', ' ', clean_content).strip()
            
            # Take a substantial sample
            if len(clean_content) > 250:
                sample = clean_content[:250]
            else:
                sample = clean_content
            
            samples.append(sample)
        
        return " ... ".join(samples)[:800]  # Generous content sample

    def analyze_book_structure_intelligence(self, book_id, chapters):
        """Advanced structure analysis for enhanced classification"""
        # Get first 6 chunks for structure analysis (front matter + early content)
        analysis_chunks = chapters[:6] if len(chapters) >= 6 else chapters
        
        structure_intelligence = {
            "academic_score": 0.0,
            "fiction_score": 0.0,
            "genre_hints": [],
            "confidence_boost": 0.0
        }
        
        for chunk in analysis_chunks:
            content_lower = chunk.content.lower()
            
            # Academic indicators (increase confidence for non-fiction)
            academic_indicators = [
                'bibliography', 'references', 'index', 'table of contents', 
                'research', 'study', 'analysis', 'methodology', 'hypothesis',
                'citations', 'notes', 'appendix', 'works cited'
            ]
            
            academic_count = sum(1 for indicator in academic_indicators if indicator in content_lower)
            structure_intelligence["academic_score"] += academic_count * 0.1
            
            # Fiction indicators (increase confidence for fiction)
            fiction_indicators = [
                'chapter', 'character', 'dialogue', 'protagonist', 'plot',
                'story', 'narrative', 'novel', 'fiction', 'characters'
            ]
            
            fiction_count = sum(1 for indicator in fiction_indicators if indicator in content_lower)
            structure_intelligence["fiction_score"] += fiction_count * 0.05
            
            # Specific genre hints
            if any(word in content_lower for word in ['biography', 'memoir', 'life story', 'autobiography']):
                structure_intelligence["genre_hints"].append("Biography & Memoir")
            
            if any(word in content_lower for word in ['history', 'historical', 'century', 'timeline']):
                structure_intelligence["genre_hints"].append("History")
            
            if any(word in content_lower for word in ['psychology', 'psychological', 'therapy', 'mental']):
                structure_intelligence["genre_hints"].append("Psychology")
            
            if any(word in content_lower for word in ['philosophy', 'philosophical', 'theory', 'ethics']):
                structure_intelligence["genre_hints"].append("Philosophy")
            
            if any(word in content_lower for word in ['business', 'economics', 'market', 'finance']):
                structure_intelligence["genre_hints"].append("Business & Economics")
            
            if any(word in content_lower for word in ['science fiction', 'sci-fi', 'future', 'technology', 'space']):
                structure_intelligence["genre_hints"].append("Science Fiction")
            
            if any(word in content_lower for word in ['fantasy', 'magic', 'magical', 'dragon', 'wizard']):
                structure_intelligence["genre_hints"].append("Fantasy")
        
        # Calculate confidence boost based on structural clarity
        if structure_intelligence["academic_score"] > 0.3:
            structure_intelligence["confidence_boost"] = 0.2
        elif structure_intelligence["fiction_score"] > 0.3:
            structure_intelligence["confidence_boost"] = 0.15
        
        return structure_intelligence

    def classify_with_structure_intelligence(self, book_data, content, structure_intel):
        """Classification enhanced with structural intelligence"""
        
        # Build structure context
        structure_context = ""
        if structure_intel["academic_score"] > 0.2:
            structure_context = "STRUCTURE: Academic/research book with bibliography, references, or scholarly apparatus. "
        elif structure_intel["fiction_score"] > 0.2:
            structure_context = "STRUCTURE: Narrative fiction with chapters and story elements. "
        
        if structure_intel["genre_hints"]:
            most_common_hint = max(set(structure_intel["genre_hints"]), key=structure_intel["genre_hints"].count)
            structure_context += f"STRONG STRUCTURAL INDICATOR: {most_common_hint}. "
        
        prompt = f"""You are an expert book classifier using both content and structural analysis.

BOOK: "{book_data['title']}" by {book_data['author']}

{structure_context}

CONTENT SAMPLE:
{content}

AVAILABLE GENRES:
Romance, Literary Fiction, Science Fiction, Fantasy, Mystery & Thriller, Historical Fiction, Contemporary Fiction, Self-Help, Biography & Memoir, Psychology, Philosophy, Business & Economics, History, Science & Nature, Programming & Technology, Academic & Research, Religion & Spirituality, Political Science

ENHANCED CLASSIFICATION RULES:
1. Use BOTH content and structural indicators for maximum accuracy
2. Academic structure (bibliography, index, references) strongly suggests non-fiction
3. Chapter-based narrative structure suggests fiction genres
4. Respect structural hints but prioritize actual content
5. Choose the most specific and accurate genre

Based on both content analysis and structural intelligence, what is the correct genre?

GENRE:"""

        try:
            start_time = time.time()
            
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.05, "top_p": 0.9}
                },
                timeout=25
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                classification = result['response'].strip()
                
                # Enhanced genre extraction with structure confidence
                classification_lines = [line.strip() for line in classification.split('\n') if line.strip()]
                
                for line in classification_lines:
                    for genre in self.valid_genres:
                        if genre.lower() == line.lower() or genre.lower() in line.lower():
                            # Apply structure confidence boost
                            confidence = 1.0 + structure_intel["confidence_boost"]
                            return genre, duration, confidence
                
                # Fallback
                if classification_lines:
                    return classification_lines[0], duration, 1.0
                
                return classification, duration, 1.0
            else:
                return None, duration, 0.0
                
        except Exception as e:
            self.logger.error(f"Enhanced classification error: {e}")
            return None, 25, 0.0

    def _classify_book_genre(self, book_id, metadata, chapters):
        """Classify book genre using enhanced AI system"""
        try:
            # Get structure intelligence
            structure_intel = self.analyze_book_structure_intelligence(book_id, chapters)
            
            # Get optimized content
            content = self.get_optimized_content_sample(book_id, chapters)
            if not content or len(content) < 80:
                self.logger.warning(f"    ❌ Insufficient content for genre classification")
                return False
            
            # Prepare book data for classification
            book_data = {
                'title': metadata.title,
                'author': metadata.author
            }
            
            # Classify with structure intelligence
            new_genre, duration, confidence = self.classify_with_structure_intelligence(book_data, content, structure_intel)
            if not new_genre:
                self.logger.warning(f"    ❌ Genre classification failed")
                return False
            
            confidence_indicator = "🔥" if confidence > 1.1 else "🎯"
            self.logger.info(f"    {confidence_indicator} Genre: {new_genre} ({duration:.1f}s, confidence: {confidence:.2f})")
            
            # Log structure insights
            if structure_intel["genre_hints"]:
                hints = list(set(structure_intel["genre_hints"]))[:2]
                self.logger.info(f"    📋 Structure hints: {', '.join(hints)}")
            
            # Update book genre in database
            if new_genre in self.valid_genres:
                conn = psycopg2.connect(**self.db_config)
                cursor = conn.cursor()
                cursor.execute("UPDATE books SET genre = %s WHERE book_id = %s", (new_genre, book_id))
                conn.commit()
                cursor.close()
                conn.close()
                
                self.logger.info(f"    ✅ Genre assigned: {new_genre}")
                return True
            else:
                self.logger.warning(f"    ⚠️ Invalid genre returned: {new_genre}")
                return False
                
        except Exception as e:
            self.logger.error(f"    💥 Genre classification error: {e}")
            return False


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