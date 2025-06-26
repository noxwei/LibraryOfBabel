#!/usr/bin/env python3
"""
Performance Benchmarking Tests
==============================

Comprehensive performance testing for EPUB processing, memory usage, and system scalability.
Validates Phase 1 performance meets targets for Phase 2 scaling.

QA Agent: LibraryOfBabel
Targets: 10-20 books/hour, <512MB memory, <100ms search
"""

import json
import os
import sys
import unittest
import logging
import time
import psutil
import threading
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import tempfile
import gc

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from epub_processor import EPUBProcessor
from text_chunker import TextChunker
from batch_processor import BatchProcessor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestPerformance(unittest.TestCase):
    """Test suite for performance benchmarking and validation."""
    
    @classmethod
    def setUpClass(cls):
        """Set up performance testing environment."""
        cls.base_dir = Path(__file__).parent.parent
        cls.samples_dir = cls.base_dir / 'ebooktestsamples'
        cls.output_dir = cls.base_dir / 'output'
        
        # Get system info
        cls.system_info = {
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'platform': sys.platform
        }
        
        logger.info(f"System: {cls.system_info['cpu_count']} CPUs, "
                   f"{cls.system_info['memory_total'] // (1024**3)}GB RAM")
    
    def setUp(self):
        """Set up individual test."""
        # Record initial memory state
        gc.collect()  # Force garbage collection
        self.initial_memory = psutil.Process().memory_info().rss
        self.start_time = time.time()
    
    def tearDown(self):
        """Clean up after test."""
        gc.collect()
        end_time = time.time()
        final_memory = psutil.Process().memory_info().rss
        
        test_duration = end_time - self.start_time
        memory_delta = final_memory - self.initial_memory
        
        logger.info(f"Test duration: {test_duration:.2f}s, Memory delta: {memory_delta // 1024}KB")
    
    def test_01_single_epub_processing_speed(self):
        """Test single EPUB processing speed and memory usage."""
        processor = EPUBProcessor()
        
        # Find a representative EPUB file
        epub_files = list(self.samples_dir.glob('*.epub'))
        if not epub_files:
            self.skipTest("No EPUB files found for testing")
        
        # Test with first available EPUB
        test_epub = epub_files[0]
        file_size = test_epub.stat().st_size
        
        # Monitor memory during processing
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        start_time = time.time()
        
        try:
            metadata, chapters = processor.process_epub(str(test_epub))
            
            end_time = time.time()
            processing_time = end_time - start_time
            final_memory = process.memory_info().rss
            memory_used = final_memory - initial_memory
            
            # Validate results
            self.assertIsNotNone(metadata, "Metadata extraction failed")
            self.assertGreater(len(chapters), 0, "No chapters extracted")
            self.assertGreater(metadata.total_words, 0, "No words extracted")
            
            # Performance benchmarks
            words_per_second = metadata.total_words / processing_time
            mb_per_second = (file_size / (1024*1024)) / processing_time
            memory_mb = memory_used / (1024*1024)
            
            # Log performance metrics
            logger.info(f"File: {test_epub.name}")
            logger.info(f"Size: {file_size / (1024*1024):.2f}MB")
            logger.info(f"Processing time: {processing_time:.2f}s")
            logger.info(f"Words/second: {words_per_second:.0f}")
            logger.info(f"MB/second: {mb_per_second:.2f}")
            logger.info(f"Memory used: {memory_mb:.2f}MB")
            
            # Performance assertions
            self.assertLess(processing_time, 300,  # Max 5 minutes per book
                          f"Processing took too long: {processing_time:.2f}s")
            
            self.assertLess(memory_mb, 256,  # Max 256MB per book
                          f"Memory usage too high: {memory_mb:.2f}MB")
            
            self.assertGreater(words_per_second, 1000,  # Min 1000 words/second
                             f"Processing too slow: {words_per_second:.0f} words/s")
            
        except Exception as e:
            self.fail(f"EPUB processing failed: {e}")
    
    def test_02_batch_processing_throughput(self):
        """Test batch processing throughput and scalability."""
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_output:
            batch_processor = BatchProcessor()
            
            # Monitor system resources
            start_time = time.time()
            initial_memory = psutil.Process().memory_info().rss
            
            # Process sample directory
            stats = batch_processor.process_directory(str(self.samples_dir), temp_output)
            
            end_time = time.time()
            total_time = end_time - start_time
            final_memory = psutil.Process().memory_info().rss
            memory_used = (final_memory - initial_memory) / (1024*1024)  # MB
            
            # Validate batch processing results
            self.assertGreater(stats['processed_successfully'], 0,
                             "No files processed successfully")
            
            self.assertEqual(stats['failed_files'], 0,
                           f"Failed to process {stats['failed_files']} files")
            
            # Calculate throughput metrics
            books_per_hour = (stats['processed_successfully'] / total_time) * 3600
            words_per_minute = (stats['total_words'] / total_time) * 60
            
            logger.info(f"Batch processing results:")
            logger.info(f"Total time: {total_time:.2f}s")
            logger.info(f"Books processed: {stats['processed_successfully']}")
            logger.info(f"Books per hour: {books_per_hour:.1f}")
            logger.info(f"Words per minute: {words_per_minute:.0f}")
            logger.info(f"Memory used: {memory_used:.2f}MB")
            
            # Performance targets
            self.assertGreaterEqual(books_per_hour, 10,
                                  f"Throughput too low: {books_per_hour:.1f} books/hour (target: ≥10)")
            
            self.assertLess(memory_used, 512,
                          f"Memory usage too high: {memory_used:.2f}MB (target: <512MB)")
    
    def test_03_memory_efficiency_validation(self):
        """Test memory efficiency and leak detection."""
        processor = EPUBProcessor()
        chunker = TextChunker()
        
        # Find multiple EPUB files for testing
        epub_files = list(self.samples_dir.glob('*.epub'))[:5]  # Test first 5
        if len(epub_files) < 2:
            self.skipTest("Need at least 2 EPUB files for memory testing")
        
        initial_memory = psutil.Process().memory_info().rss
        memory_readings = []
        
        for i, epub_file in enumerate(epub_files):
            gc.collect()  # Force garbage collection
            current_memory = psutil.Process().memory_info().rss
            memory_readings.append(current_memory)
            
            try:
                # Process EPUB
                metadata, chapters = processor.process_epub(str(epub_file))
                
                # Create chunks
                chunks = chunker.chunk_book(metadata, chapters)
                
                # Clear variables to test cleanup
                del metadata, chapters, chunks
                
                logger.info(f"Processed {epub_file.name}, "
                           f"Memory: {(current_memory - initial_memory) // 1024}KB")
                
            except Exception as e:
                logger.warning(f"Failed to process {epub_file}: {e}")
        
        # Final cleanup and memory check
        gc.collect()
        final_memory = psutil.Process().memory_info().rss
        
        # Calculate memory growth
        memory_growth = final_memory - initial_memory
        avg_memory_per_book = memory_growth / len(epub_files)
        
        logger.info(f"Memory efficiency test:")
        logger.info(f"Initial memory: {initial_memory // 1024}KB")
        logger.info(f"Final memory: {final_memory // 1024}KB")
        logger.info(f"Memory growth: {memory_growth // 1024}KB")
        logger.info(f"Avg per book: {avg_memory_per_book // 1024}KB")
        
        # Memory efficiency assertions
        memory_growth_mb = memory_growth / (1024 * 1024)
        self.assertLess(memory_growth_mb, 100,
                       f"Memory growth too high: {memory_growth_mb:.2f}MB")
        
        avg_memory_mb = avg_memory_per_book / (1024 * 1024)
        self.assertLess(avg_memory_mb, 20,
                       f"Average memory per book too high: {avg_memory_mb:.2f}MB")
    
    def test_04_concurrent_processing_scalability(self):
        """Test concurrent processing capabilities and resource management."""
        import concurrent.futures
        import queue
        
        epub_files = list(self.samples_dir.glob('*.epub'))[:3]  # Test with 3 files
        if len(epub_files) < 2:
            self.skipTest("Need at least 2 EPUB files for concurrent testing")
        
        results_queue = queue.Queue()
        error_queue = queue.Queue()
        
        def process_single_epub(epub_path):
            """Process single EPUB in thread."""
            try:
                processor = EPUBProcessor()
                start_time = time.time()
                metadata, chapters = processor.process_epub(str(epub_path))
                end_time = time.time()
                
                results_queue.put({
                    'file': epub_path.name,
                    'duration': end_time - start_time,
                    'words': metadata.total_words,
                    'chapters': len(chapters)
                })
                
            except Exception as e:
                error_queue.put(f"{epub_path.name}: {str(e)}")
        
        # Monitor system resources
        initial_memory = psutil.Process().memory_info().rss
        start_time = time.time()
        
        # Execute concurrent processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(process_single_epub, epub) for epub in epub_files]
            concurrent.futures.wait(futures)
        
        end_time = time.time()
        final_memory = psutil.Process().memory_info().rss
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        errors = []
        while not error_queue.empty():
            errors.append(error_queue.get())
        
        # Validate concurrent processing
        self.assertEqual(len(errors), 0, f"Concurrent processing errors: {errors}")
        self.assertEqual(len(results), len(epub_files),
                        "Not all files processed successfully")
        
        total_duration = end_time - start_time
        memory_used = (final_memory - initial_memory) / (1024 * 1024)
        
        logger.info(f"Concurrent processing results:")
        logger.info(f"Files processed: {len(results)}")
        logger.info(f"Total time: {total_duration:.2f}s")
        logger.info(f"Memory used: {memory_used:.2f}MB")
        
        # Performance validation
        self.assertLess(memory_used, 300,
                       f"Concurrent memory usage too high: {memory_used:.2f}MB")
    
    def test_05_large_file_handling(self):
        """Test handling of large EPUB files for scalability assessment."""
        epub_files = sorted(self.samples_dir.glob('*.epub'), 
                          key=lambda x: x.stat().st_size, reverse=True)
        
        if not epub_files:
            self.skipTest("No EPUB files found for testing")
        
        # Test largest available file
        largest_epub = epub_files[0]
        file_size_mb = largest_epub.stat().st_size / (1024 * 1024)
        
        logger.info(f"Testing large file: {largest_epub.name} ({file_size_mb:.2f}MB)")
        
        processor = EPUBProcessor()
        initial_memory = psutil.Process().memory_info().rss
        
        start_time = time.time()
        
        try:
            metadata, chapters = processor.process_epub(str(largest_epub))
            
            end_time = time.time()
            processing_time = end_time - start_time
            final_memory = psutil.Process().memory_info().rss
            memory_used_mb = (final_memory - initial_memory) / (1024 * 1024)
            
            # Validate processing
            self.assertGreater(len(chapters), 0, "No chapters extracted from large file")
            self.assertGreater(metadata.total_words, 0, "No words extracted from large file")
            
            # Calculate performance metrics
            processing_rate_mb_s = file_size_mb / processing_time
            memory_efficiency = memory_used_mb / file_size_mb
            
            logger.info(f"Large file processing:")
            logger.info(f"Processing time: {processing_time:.2f}s")
            logger.info(f"Processing rate: {processing_rate_mb_s:.2f}MB/s")
            logger.info(f"Memory used: {memory_used_mb:.2f}MB")
            logger.info(f"Memory efficiency: {memory_efficiency:.2f}x")
            
            # Performance assertions for large files
            self.assertLess(processing_time, 600,  # Max 10 minutes for large files
                          f"Large file processing too slow: {processing_time:.2f}s")
            
            self.assertLess(memory_efficiency, 3.0,  # Memory should be <3x file size
                          f"Memory efficiency poor: {memory_efficiency:.2f}x")
            
        except Exception as e:
            self.fail(f"Large file processing failed: {e}")
    
    def test_06_search_performance_simulation(self):
        """Simulate search performance for processed data."""
        # Load processed data for search simulation
        processed_data = []
        
        if not self.output_dir.exists():
            self.skipTest("No processed output found for search testing")
        
        for json_file in self.output_dir.glob('*_processed.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    processed_data.append(data)
            except Exception as e:
                logger.warning(f"Failed to load {json_file}: {e}")
        
        if not processed_data:
            self.skipTest("No valid processed data found")
        
        # Simulate various search operations
        search_times = []
        
        # Test 1: Author search
        start_time = time.time()
        author_results = []
        for data in processed_data:
            author = data.get('metadata', {}).get('author', '')
            if 'author' in author.lower():  # Simple search simulation
                author_results.append(data)
        search_times.append(time.time() - start_time)
        
        # Test 2: Title search
        start_time = time.time()
        title_results = []
        for data in processed_data:
            title = data.get('metadata', {}).get('title', '')
            if 'guide' in title.lower():  # Simple search simulation
                title_results.append(data)
        search_times.append(time.time() - start_time)
        
        # Test 3: Content search
        start_time = time.time()
        content_results = []
        for data in processed_data:
            for chunk in data.get('chunks', []):
                content = chunk.get('content', '')
                if 'money' in content.lower():  # Simple search simulation
                    content_results.append(chunk)
                    break  # Only count first match per book
        search_times.append(time.time() - start_time)
        
        # Calculate performance metrics
        max_search_time = max(search_times) * 1000  # Convert to milliseconds
        avg_search_time = (sum(search_times) / len(search_times)) * 1000
        
        logger.info(f"Search performance simulation:")
        logger.info(f"Data sources: {len(processed_data)} books")
        logger.info(f"Max search time: {max_search_time:.2f}ms")
        logger.info(f"Avg search time: {avg_search_time:.2f}ms")
        
        # Performance assertions (simulated search should be fast)
        self.assertLess(max_search_time, 100,
                       f"Simulated search too slow: {max_search_time:.2f}ms")
        
        self.assertLess(avg_search_time, 50,
                       f"Average search time too high: {avg_search_time:.2f}ms")
    
    def test_07_system_resource_monitoring(self):
        """Monitor overall system resource usage during processing."""
        # Monitor CPU and memory usage during a representative workload
        epub_files = list(self.samples_dir.glob('*.epub'))[:3]
        if not epub_files:
            self.skipTest("No EPUB files found for monitoring")
        
        processor = EPUBProcessor()
        
        # Resource monitoring data
        cpu_readings = []
        memory_readings = []
        
        def monitor_resources():
            """Background resource monitoring."""
            for _ in range(30):  # Monitor for ~30 seconds
                cpu_readings.append(psutil.cpu_percent(interval=1))
                memory_readings.append(psutil.virtual_memory().percent)
        
        # Start monitoring in background
        monitor_thread = threading.Thread(target=monitor_resources)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Perform processing workload
        for epub_file in epub_files:
            try:
                metadata, chapters = processor.process_epub(str(epub_file))
                chunker = TextChunker()
                chunks = chunker.chunk_book(metadata, chapters)
                
                # Small delay to allow monitoring
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Failed to process {epub_file}: {e}")
        
        # Wait for monitoring to complete
        monitor_thread.join(timeout=5)
        
        # Analyze resource usage
        if cpu_readings and memory_readings:
            avg_cpu = sum(cpu_readings) / len(cpu_readings)
            max_cpu = max(cpu_readings)
            avg_memory = sum(memory_readings) / len(memory_readings)
            max_memory = max(memory_readings)
            
            logger.info(f"System resource usage:")
            logger.info(f"CPU - Avg: {avg_cpu:.1f}%, Max: {max_cpu:.1f}%")
            logger.info(f"Memory - Avg: {avg_memory:.1f}%, Max: {max_memory:.1f}%")
            
            # Resource usage assertions
            self.assertLess(max_cpu, 95,
                          f"CPU usage too high: {max_cpu:.1f}%")
            
            self.assertLess(max_memory, 80,
                          f"Memory usage too high: {max_memory:.1f}%")


def run_performance_tests():
    """Run performance tests and return results."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPerformance)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful(), len(result.failures), len(result.errors)


if __name__ == '__main__':
    print("=" * 80)
    print("PERFORMANCE BENCHMARKING VALIDATION")
    print("=" * 80)
    
    # Display system information
    system_info = {
        'cpu_count': psutil.cpu_count(),
        'memory_total': psutil.virtual_memory().total // (1024**3),
        'memory_available': psutil.virtual_memory().available // (1024**3),
        'platform': sys.platform
    }
    
    print(f"System: {system_info['cpu_count']} CPUs, {system_info['memory_total']}GB RAM")
    print("=" * 80)
    
    success, failures, errors = run_performance_tests()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ ALL PERFORMANCE TESTS PASSED")
        print("System performance meets Phase 2 scaling requirements")
    else:
        print("❌ PERFORMANCE TESTS FAILED")
        print(f"Failures: {failures}, Errors: {errors}")
    print("=" * 80)
    
    sys.exit(0 if success else 1)