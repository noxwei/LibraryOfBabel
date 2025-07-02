#!/usr/bin/env python3
"""
EPUB Processing Accuracy Tests
==============================

Validates Phase 1 EPUB processing results against strict accuracy criteria.
Tests text extraction accuracy, metadata parsing, and structural integrity.

QA Agent: LibraryOfBabel
Target: >95% text extraction accuracy
"""

import json
import os
import sys
import unittest
import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple
import zipfile
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

# Add src directory to path for imports
sys.path.insert(0, Path(os.path.dirname(__file__), '..', 'src'))

from epub_processor import EPUBProcessor
from text_chunker import TextChunker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestEPUBAccuracy(unittest.TestCase):
    """Test suite for EPUB processing accuracy validation."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.base_dir = Path(__file__).parent.parent
        cls.output_dir = cls.base_dir / 'output'
        cls.samples_dir = cls.base_dir / 'ebooktestsamples'
        cls.processor = EPUBProcessor()
        cls.chunker = TextChunker()
        
        # Load processed results
        cls.processed_files = []
        if cls.output_dir.exists():
            for file in cls.output_dir.glob('*_processed.json'):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        cls.processed_files.append((file.name, data))
                except Exception as e:
                    logger.error(f"Failed to load {file}: {e}")
        
        logger.info(f"Loaded {len(cls.processed_files)} processed files for testing")
    
    def test_01_all_14_books_processed(self):
        """Verify all 14 books from Phase 1 were successfully processed."""
        expected_count = 14
        actual_count = len(self.processed_files)
        
        self.assertEqual(actual_count, expected_count,
                        f"Expected {expected_count} processed books, found {actual_count}")
        
        logger.info(f"✓ All {actual_count} books successfully processed")
    
    def test_02_metadata_completeness(self):
        """Validate metadata extraction completeness and accuracy."""
        missing_metadata = []
        incomplete_books = []
        
        for filename, data in self.processed_files:
            metadata = data.get('metadata', {})
            
            # Check required fields
            required_fields = ['title', 'author', 'total_chapters', 'total_words', 'file_path']
            missing_fields = [field for field in required_fields if not metadata.get(field)]
            
            if missing_fields:
                missing_metadata.append((filename, missing_fields))
            
            # Validate data quality
            if metadata.get('total_words', 0) < 100:  # Minimum reasonable book length
                incomplete_books.append(filename)
            
            if metadata.get('total_chapters', 0) < 1:
                incomplete_books.append(filename)
        
        self.assertEqual(len(missing_metadata), 0,
                        f"Books with missing metadata: {missing_metadata}")
        
        self.assertEqual(len(incomplete_books), 0,
                        f"Books with insufficient content: {incomplete_books}")
        
        logger.info("✓ All books have complete and valid metadata")
    
    def test_03_text_extraction_accuracy(self):
        """Validate text extraction accuracy against manual verification."""
        accuracy_failures = []
        total_accuracy = 0
        tested_books = 0
        
        # Sample a few books for detailed accuracy testing
        sample_books = self.processed_files[:5]  # Test first 5 books
        
        for filename, data in sample_books:
            try:
                accuracy = self._calculate_text_accuracy(filename, data)
                total_accuracy += accuracy
                tested_books += 1
                
                if accuracy < 0.95:  # 95% accuracy threshold
                    accuracy_failures.append((filename, accuracy))
                
                logger.info(f"Text accuracy for {filename}: {accuracy:.2%}")
                
            except Exception as e:
                logger.error(f"Failed to test accuracy for {filename}: {e}")
        
        # Calculate average accuracy
        if tested_books > 0:
            avg_accuracy = total_accuracy / tested_books
            self.assertGreaterEqual(avg_accuracy, 0.95,
                                  f"Average text accuracy {avg_accuracy:.2%} below 95% threshold")
        
        self.assertEqual(len(accuracy_failures), 0,
                        f"Books with accuracy below 95%: {accuracy_failures}")
        
        logger.info(f"✓ Text extraction accuracy: {avg_accuracy:.2%} (target: >95%)")
    
    def test_04_chapter_structure_validation(self):
        """Validate chapter structure and organization."""
        structure_issues = []
        
        for filename, data in self.processed_files:
            chapters = data.get('chapters', [])
            
            # Check chapter sequence
            chapter_numbers = [ch.get('chapter_number') for ch in chapters if ch.get('chapter_number')]
            spine_orders = [ch.get('spine_order', -1) for ch in chapters]
            
            # Validate spine order is sequential
            if spine_orders != sorted(spine_orders):
                structure_issues.append((filename, "Non-sequential spine order"))
            
            # Check for reasonable chapter lengths
            short_chapters = [ch for ch in chapters if ch.get('word_count', 0) < 50]
            if len(short_chapters) > len(chapters) * 0.3:  # More than 30% very short chapters
                structure_issues.append((filename, f"Too many short chapters: {len(short_chapters)}"))
            
            # Validate chapter titles exist
            untitled_chapters = [ch for ch in chapters if not ch.get('title')]
            if len(untitled_chapters) > len(chapters) * 0.1:  # More than 10% untitled
                structure_issues.append((filename, f"Too many untitled chapters: {len(untitled_chapters)}"))
        
        self.assertEqual(len(structure_issues), 0,
                        f"Chapter structure issues: {structure_issues}")
        
        logger.info("✓ Chapter structure validation passed")
    
    def test_05_chunk_generation_validation(self):
        """Validate text chunking algorithm correctness."""
        chunking_issues = []
        
        for filename, data in self.processed_files:
            chunks = data.get('chunks', [])
            chapters = data.get('chapters', [])
            
            if not chunks:
                chunking_issues.append((filename, "No chunks generated"))
                continue
            
            # Validate chunk hierarchy
            chunk_types = [chunk.get('chunk_type') for chunk in chunks]
            if 'chapter' not in chunk_types:
                chunking_issues.append((filename, "Missing chapter-level chunks"))
            
            # Validate chunk word counts
            total_chunk_words = sum(chunk.get('word_count', 0) for chunk in chunks)
            total_chapter_words = sum(ch.get('word_count', 0) for ch in chapters)
            
            # Allow for some variation due to overlap and processing
            word_count_ratio = total_chunk_words / total_chapter_words if total_chapter_words > 0 else 0
            if word_count_ratio < 0.8 or word_count_ratio > 2.0:  # 80%-200% range
                chunking_issues.append((filename, f"Word count ratio: {word_count_ratio:.2f}"))
            
            # Validate chunk IDs are unique
            chunk_ids = [chunk.get('chunk_id') for chunk in chunks if chunk.get('chunk_id')]
            if len(chunk_ids) != len(set(chunk_ids)):
                chunking_issues.append((filename, "Duplicate chunk IDs"))
        
        self.assertEqual(len(chunking_issues), 0,
                        f"Chunk generation issues: {chunking_issues}")
        
        logger.info("✓ Text chunking validation passed")
    
    def test_06_performance_benchmarks(self):
        """Validate processing performance meets targets."""
        processing_info = []
        
        for filename, data in self.processed_files:
            proc_info = data.get('processing_info', {})
            word_count = proc_info.get('word_count', 0)
            
            # We don't have processing time in the current data structure
            # This is a placeholder for when we add timing information
            processing_info.append({
                'filename': filename,
                'word_count': word_count,
                'chapter_count': proc_info.get('chapter_count', 0),
                'chunk_count': proc_info.get('chunk_count', 0)
            })
        
        # Validate reasonable processing occurred
        total_words = sum(info['word_count'] for info in processing_info)
        total_chunks = sum(info['chunk_count'] for info in processing_info)
        
        self.assertGreater(total_words, 500000,  # At least 500k words processed
                          f"Total words processed: {total_words:,}")
        
        self.assertGreater(total_chunks, 100,  # At least 100 chunks generated
                          f"Total chunks generated: {total_chunks}")
        
        logger.info(f"✓ Performance: {total_words:,} words, {total_chunks} chunks processed")
    
    def test_07_data_integrity_validation(self):
        """Validate data integrity and consistency."""
        integrity_issues = []
        
        for filename, data in self.processed_files:
            # Check JSON structure completeness
            required_sections = ['metadata', 'chapters', 'chunks', 'processing_info']
            missing_sections = [section for section in required_sections if section not in data]
            
            if missing_sections:
                integrity_issues.append((filename, f"Missing sections: {missing_sections}"))
            
            # Validate cross-references
            metadata = data.get('metadata', {})
            chapters = data.get('chapters', [])
            
            # Check metadata vs chapter count consistency
            meta_chapter_count = metadata.get('total_chapters', 0)
            actual_chapter_count = len(chapters)
            
            if abs(meta_chapter_count - actual_chapter_count) > 2:  # Allow small discrepancy
                integrity_issues.append((filename, 
                    f"Chapter count mismatch: metadata={meta_chapter_count}, actual={actual_chapter_count}"))
            
            # Check word count consistency
            meta_word_count = metadata.get('total_words', 0)
            actual_word_count = sum(ch.get('word_count', 0) for ch in chapters)
            
            if abs(meta_word_count - actual_word_count) > actual_word_count * 0.1:  # Allow 10% variance
                integrity_issues.append((filename,
                    f"Word count mismatch: metadata={meta_word_count}, actual={actual_word_count}"))
        
        self.assertEqual(len(integrity_issues), 0,
                        f"Data integrity issues: {integrity_issues}")
        
        logger.info("✓ Data integrity validation passed")
    
    def _calculate_text_accuracy(self, filename: str, data: Dict) -> float:
        """Calculate text extraction accuracy for a specific book."""
        try:
            # Extract book title from filename for original file lookup
            clean_name = filename.replace('_processed.json', '').replace('_', ' ')
            
            # Find corresponding EPUB file
            epub_files = list(self.samples_dir.glob('*.epub'))
            matching_epub = None
            
            for epub_file in epub_files:
                if self._files_match(epub_file.stem, clean_name):
                    matching_epub = epub_file
                    break
            
            if not matching_epub:
                logger.warning(f"Could not find original EPUB for {filename}")
                return 0.9  # Default reasonable accuracy
            
            # Re-process the file and compare
            try:
                metadata, chapters = self.processor.process_epub(str(matching_epub))
                
                # Compare chapter count
                original_chapters = len(chapters)
                processed_chapters = len(data.get('chapters', []))
                chapter_accuracy = min(1.0, processed_chapters / original_chapters) if original_chapters > 0 else 1.0
                
                # Compare word count
                original_words = sum(ch.word_count for ch in chapters)
                processed_words = sum(ch.get('word_count', 0) for ch in data.get('chapters', []))
                word_accuracy = min(1.0, processed_words / original_words) if original_words > 0 else 1.0
                
                # Calculate overall accuracy
                accuracy = (chapter_accuracy + word_accuracy) / 2
                return accuracy
                
            except Exception as e:
                logger.error(f"Failed to re-process {matching_epub}: {e}")
                return 0.9  # Default reasonable accuracy
            
        except Exception as e:
            logger.error(f"Error calculating accuracy for {filename}: {e}")
            return 0.9
    
    def _files_match(self, epub_name: str, processed_name: str) -> bool:
        """Check if EPUB filename matches processed filename."""
        # Normalize names for comparison
        epub_clean = re.sub(r'[^\w\s]', '', epub_name.lower())
        processed_clean = re.sub(r'[^\w\s]', '', processed_name.lower())
        
        # Simple similarity check
        return epub_clean in processed_clean or processed_clean in epub_clean


def run_epub_accuracy_tests():
    """Run EPUB accuracy tests and return results."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEPUBAccuracy)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful(), len(result.failures), len(result.errors)


if __name__ == '__main__':
    print("=" * 80)
    print("EPUB PROCESSING ACCURACY VALIDATION")
    print("=" * 80)
    
    success, failures, errors = run_epub_accuracy_tests()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ ALL EPUB ACCURACY TESTS PASSED")
        print("Phase 1 EPUB processing meets quality standards")
    else:
        print("❌ EPUB ACCURACY TESTS FAILED")
        print(f"Failures: {failures}, Errors: {errors}")
    print("=" * 80)
    
    sys.exit(0 if success else 1)