#!/usr/bin/env python3
"""
Batch EPUB Processor for LibraryOfBabel
=======================================

Processes multiple EPUB files in batch with memory-efficient streaming.
Handles error recovery and progress tracking.

Author: Librarian Agent
Version: 1.0
"""

import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional, Iterator
import concurrent.futures
from dataclasses import asdict

from epub_processor import EPUBProcessor
from text_chunker import TextChunker

logger = logging.getLogger(__name__)

class PathJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles Path objects by converting them to strings."""
    def default(self, obj):
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)

class BatchProcessor:
    """Batch processes EPUB files with memory efficiency and error handling."""
    
    def __init__(self, config_path: str = None):
        """Initialize batch processor."""
        self.config_path = config_path
        self.config = self._load_config()
        self.epub_processor = EPUBProcessor(config_path)
        self.text_chunker = TextChunker(self.config.get('text_chunking', {}))
        
        # Set up logging
        self._setup_logging()
        
        # Processing statistics
        self.stats = {
            'total_files': 0,
            'processed_successfully': 0,
            'failed_files': 0,
            'total_chapters': 0,
            'total_words': 0,
            'total_chunks': 0,
            'start_time': None,
            'end_time': None
        }
        
    def _load_config(self) -> Dict:
        """Load configuration from file."""
        default_config = {
            'batch_processing': {
                'max_concurrent_books': 1,
                'memory_limit_mb': 512,
                'error_retry_count': 3,
                'skip_processed': True,
                'output_format': 'json'
            }
        }
        
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    default_config.update(config)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
        
        return default_config
    
    def _setup_logging(self):
        """Set up logging configuration."""
        log_config = self.config.get('logging', {})
        
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_format = log_config.get('format', '%(asctime)s - %(levelname)s - %(message)s')
        
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_config.get('file', 'batch_processing.log'))
            ]
        )
    
    def find_epub_files(self, directory: str) -> List[str]:
        """Find all EPUB files and directories in directory."""
        epub_files = []
        
        # Look for EPUB directories (extracted EPUBs)
        for item in os.listdir(directory):
            item_path = Path(directory, item)
            
            # Check if it's a directory ending with .epub
            if os.path.isdir(item_path) and item.lower().endswith('.epub'):
                # Verify it has EPUB structure
                if self._is_valid_epub_directory(item_path):
                    epub_files.append(item_path)
            
            # Check if it's a regular EPUB file
            elif os.path.isfile(item_path) and item.lower().endswith('.epub'):
                epub_files.append(item_path)
        
        return sorted(epub_files)
    
    def _is_valid_epub_directory(self, directory: str) -> bool:
        """Check if directory contains valid EPUB structure."""
        # Check for required EPUB files
        meta_inf = Path(directory, 'META-INF')
        container_xml = Path(meta_inf, 'container.xml')
        mimetype = Path(directory, 'mimetype')
        
        return (os.path.exists(meta_inf) and 
                os.path.exists(container_xml) and
                (os.path.exists(mimetype) or os.path.exists(Path(directory, 'OEBPS'))))
    
    def process_directory(self, directory: str, output_dir: str) -> Dict:
        """Process all EPUB files in a directory."""
        logger.info(f"Starting batch processing of directory: {directory}")
        
        # Find all EPUB files
        epub_files = self.find_epub_files(directory)
        self.stats['total_files'] = len(epub_files)
        
        logger.info(f"Found {len(epub_files)} EPUB files to process")
        
        if not epub_files:
            logger.warning("No EPUB files found")
            return self.stats
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Start processing
        self.stats['start_time'] = time.time()
        
        # Process files (currently single-threaded due to memory constraints)
        for i, epub_path in enumerate(epub_files, 1):
            logger.info(f"Processing {i}/{len(epub_files)}: {os.path.basename(epub_path)}")
            
            try:
                result = self._process_single_epub(epub_path, output_dir)
                if result:
                    self.stats['processed_successfully'] += 1
                    self.stats['total_chapters'] += result['chapter_count']
                    self.stats['total_words'] += result['word_count']
                    self.stats['total_chunks'] += result['chunk_count']
                else:
                    self.stats['failed_files'] += 1
                    
            except Exception as e:
                logger.error(f"Failed to process {epub_path}: {e}")
                self.stats['failed_files'] += 1
                
            # Progress update
            if i % 5 == 0 or i == len(epub_files):
                progress = (i / len(epub_files)) * 100
                logger.info(f"Progress: {progress:.1f}% ({i}/{len(epub_files)} files)")
        
        self.stats['end_time'] = time.time()
        self._log_final_stats()
        
        return self.stats
    
    def _process_single_epub(self, epub_path: str, output_dir: str) -> Optional[Dict]:
        """Process a single EPUB file."""
        try:
            # Check if already processed
            output_file = self._get_output_filename(epub_path, output_dir)
            if (self.config['batch_processing']['skip_processed'] 
                and os.path.exists(output_file)):
                logger.debug(f"Skipping already processed file: {epub_path}")
                return self._load_existing_result(output_file)
            
            # Process EPUB
            metadata, chapters = self.epub_processor.process_epub(epub_path)
            
            # Create chunks
            chunks = self.text_chunker.chunk_book(metadata, chapters)
            
            # Prepare output data with enum conversion
            output_data = {
                'metadata': self._convert_paths_to_strings(asdict(metadata)),
                'chapters': [self._convert_paths_to_strings(asdict(chapter)) for chapter in chapters],
                'chunks': [self._chunk_to_dict(chunk) for chunk in chunks],
                'processing_info': {
                    'processed_at': time.time(),
                    'epub_path': str(epub_path),
                    'chapter_count': len(chapters),
                    'word_count': metadata.total_words,
                    'chunk_count': len(chunks)
                }
            }
            
            # Save results
            self._save_results(output_data, output_file)
            
            return output_data['processing_info']
            
        except Exception as e:
            logger.error(f"Error processing {epub_path}: {e}")
            return None
    
    def _chunk_to_dict(self, chunk) -> Dict:
        """Convert TextChunk to dictionary with enum serialization."""
        chunk_dict = asdict(chunk)
        # Convert enum to string
        chunk_dict['chunk_type'] = chunk.chunk_type.value
        # Convert any Path objects to strings
        chunk_dict = self._convert_paths_to_strings(chunk_dict)
        return chunk_dict
    
    def _convert_paths_to_strings(self, obj):
        """Recursively convert Path objects to strings in nested dictionaries/lists."""
        if isinstance(obj, Path):
            return str(obj)
        elif isinstance(obj, dict):
            return {key: self._convert_paths_to_strings(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_paths_to_strings(item) for item in obj]
        else:
            return obj
    
    def _get_output_filename(self, epub_path: str, output_dir: str) -> str:
        """Generate output filename for processed EPUB."""
        base_name = os.path.splitext(os.path.basename(epub_path))[0]
        # Clean filename for filesystem compatibility
        clean_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).strip()
        clean_name = clean_name.replace(' ', '_')
        
        return Path(output_dir, f"{clean_name}_processed.json")
    
    def _save_results(self, data: Dict, output_file: str):
        """Save processing results to file."""
        try:
            # Apply path conversion to entire data structure before saving
            clean_data = self._convert_paths_to_strings(data)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(clean_data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved results to: {output_file}")
        except Exception as e:
            logger.error(f"Failed to save results to {output_file}: {e}")
            raise
    
    def _load_existing_result(self, output_file: str) -> Optional[Dict]:
        """Load existing processing results."""
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('processing_info')
        except Exception as e:
            logger.warning(f"Failed to load existing result from {output_file}: {e}")
            return None
    
    def _log_final_stats(self):
        """Log final processing statistics."""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        logger.info("=" * 60)
        logger.info("BATCH PROCESSING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total files found: {self.stats['total_files']}")
        logger.info(f"Successfully processed: {self.stats['processed_successfully']}")
        logger.info(f"Failed files: {self.stats['failed_files']}")
        logger.info(f"Total chapters extracted: {self.stats['total_chapters']:,}")
        logger.info(f"Total words processed: {self.stats['total_words']:,}")
        logger.info(f"Total chunks created: {self.stats['total_chunks']:,}")
        logger.info(f"Processing time: {duration:.2f} seconds")
        
        if self.stats['processed_successfully'] > 0:
            avg_time = duration / self.stats['processed_successfully']
            logger.info(f"Average time per book: {avg_time:.2f} seconds")
            
            success_rate = (self.stats['processed_successfully'] / self.stats['total_files']) * 100
            logger.info(f"Success rate: {success_rate:.1f}%")
        
        logger.info("=" * 60)


def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 3:
        print("Usage: python batch_processor.py <input_directory> <output_directory> [config_file]")
        print("\nExample:")
        print("  python batch_processor.py /path/to/ebooks /path/to/output config/processing_config.json")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    config_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    if not os.path.exists(input_dir):
        print(f"Error: Input directory not found: {input_dir}")
        sys.exit(1)
    
    # Initialize processor
    processor = BatchProcessor(config_file)
    
    try:
        # Process directory
        stats = processor.process_directory(input_dir, output_dir)
        
        # Print summary
        print(f"\nProcessing complete!")
        print(f"Processed {stats['processed_successfully']}/{stats['total_files']} files successfully")
        print(f"Total chapters: {stats['total_chapters']:,}")
        print(f"Total words: {stats['total_words']:,}")
        print(f"Total chunks: {stats['total_chunks']:,}")
        print(f"Results saved to: {output_dir}")
        
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error during processing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()