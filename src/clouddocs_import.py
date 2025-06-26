#!/usr/bin/env python3
"""
LibraryOfBabel CloudDocs Import Module
Custom location import functionality for testing scalability and flexibility
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Tuple
import argparse
import logging

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.epub_processor import EPUBProcessor
from src.text_chunker import TextChunker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CloudDocsImporter:
    """Custom location importer for CloudDocs and other external sources"""
    
    def __init__(self, source_path: str, output_dir: str = None, max_books: int = None):
        """
        Initialize CloudDocs importer
        
        Args:
            source_path: Path to the source directory containing EPUBs
            output_dir: Output directory for processed files  
            max_books: Maximum number of books to process (for testing)
        """
        self.source_path = Path(source_path)
        self.output_dir = Path(output_dir) if output_dir else Path("output/clouddocs")
        self.max_books = max_books
        
        # Initialize processors
        self.epub_processor = EPUBProcessor()
        self.text_chunker = TextChunker()
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            'discovered': 0,
            'processed': 0,
            'failed': 0,
            'skipped': 0,
            'total_words': 0,
            'total_chunks': 0,
            'processing_time': 0
        }
        
        logger.info(f"CloudDocs Importer initialized")
        logger.info(f"Source: {self.source_path}")
        logger.info(f"Output: {self.output_dir}")
        if max_books:
            logger.info(f"Max books: {max_books}")
    
    def discover_books(self) -> List[Path]:
        """Discover all EPUB files in the source directory"""
        logger.info("Discovering EPUB files...")
        
        epub_paths = []
        
        # Look for .epub directories (extracted EPUBs)
        for item in self.source_path.iterdir():
            if item.is_dir() and item.name.endswith('.epub'):
                epub_paths.append(item)
            elif item.is_file() and item.suffix.lower() == '.epub':
                epub_paths.append(item)
        
        self.stats['discovered'] = len(epub_paths)
        logger.info(f"Discovered {len(epub_paths)} EPUB files")
        
        # Sort for consistent processing order
        epub_paths.sort(key=lambda x: x.name.lower())
        
        # Apply max_books limit if specified
        if self.max_books and len(epub_paths) > self.max_books:
            epub_paths = epub_paths[:self.max_books]
            logger.info(f"Limited to {self.max_books} books for testing")
        
        return epub_paths
    
    def analyze_collection(self, epub_paths: List[Path]) -> Dict:
        """Analyze the collection structure and formats"""
        logger.info("Analyzing collection structure...")
        
        analysis = {
            'total_books': len(epub_paths),
            'format_types': {},
            'size_distribution': {
                'small': 0,    # < 1MB
                'medium': 0,   # 1-10MB
                'large': 0,    # 10-50MB
                'xlarge': 0    # > 50MB
            },
            'sample_books': [],
            'estimated_processing_time': 0
        }
        
        for i, epub_path in enumerate(epub_paths[:10]):  # Sample first 10
            try:
                if epub_path.is_dir():
                    # Extracted EPUB directory
                    format_type = "extracted_directory"
                    size_mb = sum(f.stat().st_size for f in epub_path.rglob('*') if f.is_file()) / (1024 * 1024)
                else:
                    # EPUB file
                    format_type = "epub_file"
                    size_mb = epub_path.stat().st_size / (1024 * 1024)
                
                # Categorize by size
                if size_mb < 1:
                    analysis['size_distribution']['small'] += 1
                elif size_mb < 10:
                    analysis['size_distribution']['medium'] += 1
                elif size_mb < 50:
                    analysis['size_distribution']['large'] += 1
                else:
                    analysis['size_distribution']['xlarge'] += 1
                
                analysis['format_types'][format_type] = analysis['format_types'].get(format_type, 0) + 1
                
                if i < 5:  # Store details for first 5 books
                    analysis['sample_books'].append({
                        'name': epub_path.name,
                        'format': format_type,
                        'size_mb': round(size_mb, 2)
                    })
                    
            except Exception as e:
                logger.warning(f"Failed to analyze {epub_path.name}: {e}")
        
        # Estimate processing time (rough estimate: 2 minutes per book average)
        analysis['estimated_processing_time'] = len(epub_paths) * 2  # minutes
        
        return analysis
    
    def process_single_book(self, epub_path: Path) -> Tuple[bool, Dict]:
        """Process a single EPUB book"""
        book_name = epub_path.stem.replace('.epub', '')
        output_file = self.output_dir / f"{book_name}_processed.json"
        
        # Skip if already processed
        if output_file.exists():
            logger.info(f"Skipping {book_name} (already processed)")
            self.stats['skipped'] += 1
            return True, {}
        
        try:
            start_time = time.time()
            
            # Process EPUB (handles both directories and ZIP files)
            logger.info(f"Processing: {book_name}")
            
            # The process_epub method automatically detects directory vs ZIP
            metadata, chapters = self.epub_processor.process_epub(str(epub_path))
            
            if not chapters:
                logger.warning(f"No content extracted from {book_name}")
                self.stats['failed'] += 1
                return False, {}
            
            # Apply text chunking using original objects
            chunks = self.text_chunker.chunk_book(metadata, chapters)
            
            # Convert to our expected format for saving
            book_data = {
                'metadata': {
                    'title': metadata.title,
                    'author': metadata.author,
                    'publisher': metadata.publisher,
                    'publication_date': metadata.publication_date,
                    'language': metadata.language,
                    'isbn': metadata.isbn,
                    'description': metadata.description,
                    'total_words': sum(ch.word_count for ch in chapters)
                },
                'chapters': [
                    {
                        'title': ch.title,
                        'content': ch.content,
                        'chapter_number': ch.chapter_number,
                        'section_number': ch.section_number,
                        'word_count': ch.word_count,
                        'file_path': ch.file_path,
                        'spine_order': ch.spine_order
                    }
                    for ch in chapters
                ]
            }
            
            # Convert chunks to JSON-serializable format
            chunked_data = {
                'metadata': book_data['metadata'],
                'chapters': book_data['chapters'],
                'chunks': [
                    {
                        'chunk_id': chunk.chunk_id,
                        'book_id': chunk.book_id,
                        'chunk_type': chunk.chunk_type.value if hasattr(chunk.chunk_type, 'value') else str(chunk.chunk_type),
                        'chapter_number': chunk.chapter_number,
                        'section_number': chunk.section_number,
                        'content': chunk.content,
                        'word_count': chunk.word_count,
                        'character_count': chunk.character_count,
                        'parent_chunk_id': chunk.parent_chunk_id
                    }
                    for chunk in chunks
                ]
            }
            
            # Add custom location metadata
            chunked_data['metadata']['source_location'] = str(epub_path)
            chunked_data['metadata']['import_source'] = 'clouddocs_backup'
            chunked_data['metadata']['processed_timestamp'] = time.time()
            
            # Save processed data
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(chunked_data, f, ensure_ascii=False, indent=2)
            
            processing_time = time.time() - start_time
            
            # Update statistics
            word_count = chunked_data['metadata'].get('total_words', 0)
            chunk_count = len(chunked_data.get('chunks', []))
            
            self.stats['processed'] += 1
            self.stats['total_words'] += word_count
            self.stats['total_chunks'] += chunk_count
            self.stats['processing_time'] += processing_time
            
            logger.info(f"✅ Processed {book_name}: {word_count} words, {chunk_count} chunks in {processing_time:.1f}s")
            
            return True, {
                'word_count': word_count,
                'chunk_count': chunk_count,
                'processing_time': processing_time
            }
            
        except Exception as e:
            logger.error(f"Failed to process {book_name}: {e}")
            self.stats['failed'] += 1
            return False, {}
    
    def process_collection(self) -> Dict:
        """Process the entire discovered collection"""
        start_time = time.time()
        
        # Discover books
        epub_paths = self.discover_books()
        
        if not epub_paths:
            logger.warning("No EPUB files found in source directory")
            return self.stats
        
        # Analyze collection
        analysis = self.analyze_collection(epub_paths)
        logger.info(f"Collection analysis: {analysis['total_books']} books")
        logger.info(f"Format distribution: {analysis['format_types']}")
        logger.info(f"Size distribution: {analysis['size_distribution']}")
        
        # Process books
        logger.info(f"Starting batch processing of {len(epub_paths)} books...")
        
        for i, epub_path in enumerate(epub_paths, 1):
            logger.info(f"Processing book {i}/{len(epub_paths)}")
            success, book_stats = self.process_single_book(epub_path)
            
            # Progress update every 5 books
            if i % 5 == 0:
                self.print_progress_stats(i, len(epub_paths))
        
        # Final statistics
        total_time = time.time() - start_time
        self.stats['total_processing_time'] = total_time
        
        return self.stats
    
    def print_progress_stats(self, current: int, total: int):
        """Print progress statistics"""
        percent = (current / total) * 100
        books_per_minute = (self.stats['processed'] / (self.stats['processing_time'] / 60)) if self.stats['processing_time'] > 0 else 0
        
        logger.info(f"Progress: {current}/{total} ({percent:.1f}%)")
        logger.info(f"Success rate: {self.stats['processed']}/{current} ({(self.stats['processed']/current)*100:.1f}%)")
        logger.info(f"Processing speed: {books_per_minute:.1f} books/minute")
        logger.info(f"Total words processed: {self.stats['total_words']:,}")
    
    def generate_import_report(self) -> Dict:
        """Generate comprehensive import report"""
        if self.stats['processing_time'] > 0:
            books_per_hour = (self.stats['processed'] / (self.stats['processing_time'] / 3600))
            avg_words_per_book = self.stats['total_words'] / self.stats['processed'] if self.stats['processed'] > 0 else 0
            avg_chunks_per_book = self.stats['total_chunks'] / self.stats['processed'] if self.stats['processed'] > 0 else 0
        else:
            books_per_hour = 0
            avg_words_per_book = 0
            avg_chunks_per_book = 0
        
        report = {
            'import_summary': {
                'source_location': str(self.source_path),
                'books_discovered': self.stats['discovered'],
                'books_processed': self.stats['processed'],
                'books_failed': self.stats['failed'],
                'books_skipped': self.stats['skipped'],
                'success_rate': (self.stats['processed'] / max(self.stats['discovered'], 1)) * 100
            },
            'content_statistics': {
                'total_words': self.stats['total_words'],
                'total_chunks': self.stats['total_chunks'],
                'avg_words_per_book': round(avg_words_per_book, 0),
                'avg_chunks_per_book': round(avg_chunks_per_book, 1)
            },
            'performance_metrics': {
                'total_processing_time_minutes': round(self.stats['processing_time'] / 60, 1),
                'books_per_hour': round(books_per_hour, 1),
                'avg_processing_time_per_book': round(self.stats['processing_time'] / max(self.stats['processed'], 1), 1)
            },
            'database_ready': {
                'output_directory': str(self.output_dir),
                'json_files_created': self.stats['processed'],
                'ready_for_database_ingestion': self.stats['processed'] > 0
            }
        }
        
        return report


def main():
    """Main function for CloudDocs import"""
    parser = argparse.ArgumentParser(description='LibraryOfBabel CloudDocs Importer')
    parser.add_argument('--source', required=True, help='Source directory containing EPUB files')
    parser.add_argument('--output', default='output/clouddocs', help='Output directory for processed files')
    parser.add_argument('--max-books', type=int, help='Maximum number of books to process (for testing)')
    parser.add_argument('--report', action='store_true', help='Generate detailed import report')
    
    args = parser.parse_args()
    
    # Initialize importer
    importer = CloudDocsImporter(args.source, args.output, args.max_books)
    
    # Process collection
    logger.info("🚀 Starting CloudDocs import process...")
    stats = importer.process_collection()
    
    # Generate report
    report = importer.generate_import_report()
    
    # Print summary
    print("\n" + "="*60)
    print("📚 CLOUDDOCS IMPORT COMPLETE")
    print("="*60)
    print(f"✅ Processed: {stats['processed']} books")
    print(f"❌ Failed: {stats['failed']} books")
    print(f"⏭️  Skipped: {stats['skipped']} books")
    print(f"📊 Total words: {stats['total_words']:,}")
    print(f"🔗 Total chunks: {stats['total_chunks']:,}")
    print(f"⏱️  Processing time: {stats['processing_time']/60:.1f} minutes")
    if stats['processing_time'] > 0:
        print(f"⚡ Speed: {(stats['processed'] / (stats['processing_time'] / 3600)):.1f} books/hour")
    
    # Save detailed report if requested
    if args.report:
        report_file = Path(args.output) / 'import_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"📋 Detailed report saved: {report_file}")
    
    print(f"📁 Output directory: {args.output}")
    print("🔄 Ready for database ingestion!")


if __name__ == "__main__":
    main()