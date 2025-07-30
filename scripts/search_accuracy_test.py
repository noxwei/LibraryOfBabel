#!/usr/bin/env python3
"""
Search Accuracy Test - Dr. Rodriguez & Dr. Chen Database Team
============================================================

Test case: Extract random sentences from middle sections of books,
then test search functionality to ensure chunks are findable.

This validates:
- Database chunk integrity
- Search index effectiveness  
- Vector embedding accuracy
- Full-text search performance
"""

import psycopg2
import psycopg2.extras
import random
import re
import requests
import json
import time
from typing import List, Dict, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'knowledge_base',
    'user': 'weixiangzhang',
    'port': 5432
}

# API endpoints for testing
API_BASE = "http://localhost:9003"  # Optimized test server
PROD_API_BASE = "https://api.ashortstayinhell.com:5562"
API_KEY = os.environ.get('API_KEY', 'YOUR_API_KEY_HERE')

def get_db_connection():
    """Get database connection"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def extract_random_book_samples(num_books: int = 20) -> List[Dict]:
    """
    Extract random sentence samples from middle sections of books
    Returns metadata only, not full content to respect copyright
    """
    conn = get_db_connection()
    if not conn:
        return []
    
    samples = []
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Get random books with sufficient content
            cur.execute("""
                SELECT book_id, title, author, word_count
                FROM books 
                WHERE word_count > 10000
                ORDER BY RANDOM()
                LIMIT %s
            """, (num_books,))
            
            books = cur.fetchall()
            logger.info(f"Selected {len(books)} books for testing")
            
            for book in books:
                # Get chunks from middle 60% of book (avoid intro/conclusion)
                cur.execute("""
                    SELECT chunk_id, word_count, chapter_number
                    FROM chunks
                    WHERE book_id = %s 
                    AND chunk_type = 'chapter'
                    AND chapter_number > (
                        SELECT COUNT(*) * 0.2 FROM chunks 
                        WHERE book_id = %s AND chunk_type = 'chapter'
                    )
                    AND chapter_number < (
                        SELECT COUNT(*) * 0.8 FROM chunks 
                        WHERE book_id = %s AND chunk_type = 'chapter'
                    )
                    ORDER BY RANDOM()
                    LIMIT 3
                """, (book['book_id'], book['book_id'], book['book_id']))
                
                chunks = cur.fetchall()
                
                for chunk in chunks:
                    # Get a short excerpt for testing (respecting copyright)
                    cur.execute("""
                        SELECT content
                        FROM chunks
                        WHERE chunk_id = %s
                    """, (chunk['chunk_id'],))
                    
                    content_result = cur.fetchone()
                    if content_result and content_result['content']:
                        content = content_result['content']
                        
                        # Extract sentences (not full paragraphs)
                        sentences = re.split(r'[.!?]+', content)
                        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
                        
                        if sentences:
                            # Take a random sentence from middle of chapter
                            mid_idx = len(sentences) // 2
                            start_idx = max(0, mid_idx - 2)
                            end_idx = min(len(sentences), mid_idx + 2)
                            
                            test_sentence = random.choice(sentences[start_idx:end_idx])
                            
                            # Create test query (first few words only)
                            words = test_sentence.split()
                            if len(words) >= 4:
                                # Use 3-5 consecutive words as search query
                                query_length = min(5, len(words) - 1)
                                start_word = random.randint(0, max(0, len(words) - query_length))
                                test_query = ' '.join(words[start_word:start_word + query_length])
                                
                                samples.append({
                                    'book_id': book['book_id'],
                                    'book_title': book['title'],
                                    'author': book['author'],
                                    'chunk_id': chunk['chunk_id'],
                                    'chapter_number': chunk['chapter_number'],
                                    'test_query': test_query,
                                    'expected_chunk_id': chunk['chunk_id'],
                                    'word_count': len(words)
                                })
                                
                                logger.info(f"Sample from {book['title']}: '{test_query[:50]}...'")
    
    except Exception as e:
        logger.error(f"Sample extraction failed: {e}")
    finally:
        conn.close()
    
    return samples

def test_search_accuracy(samples: List[Dict]) -> Dict:
    """Test search accuracy against extracted samples"""
    results = {
        'total_tests': len(samples),
        'successful_finds': 0,
        'failed_finds': 0,
        'response_times': [],
        'search_results': []
    }
    
    for i, sample in enumerate(samples):
        logger.info(f"Testing {i+1}/{len(samples)}: {sample['test_query'][:30]}...")
        
        # Test full-text search
        start_time = time.time()
        
        try:
            # Use the optimized local API
            response = requests.get(
                f"{API_BASE}/api/v4/search",
                params={
                    'q': sample['test_query'],
                    'type': 'content',
                    'limit': 10
                },
                timeout=10
            )
            
            response_time = (time.time() - start_time) * 1000
            results['response_times'].append(response_time)
            
            if response.status_code == 200:
                search_data = response.json()
                found_chunks = search_data.get('results', [])
                
                # Check if expected chunk is in results
                found_expected = any(
                    result.get('chunk_id') == sample['expected_chunk_id']
                    for result in found_chunks
                )
                
                if found_expected:
                    results['successful_finds'] += 1
                    status = "✅ FOUND"
                else:
                    results['failed_finds'] += 1
                    status = "❌ NOT FOUND"
                
                results['search_results'].append({
                    'sample': sample,
                    'found': found_expected,
                    'num_results': len(found_chunks),
                    'response_time_ms': response_time,
                    'status': status
                })
                
                logger.info(f"  {status} - {len(found_chunks)} results in {response_time:.1f}ms")
                
            else:
                logger.error(f"  ❌ API Error: {response.status_code}")
                results['failed_finds'] += 1
                
        except Exception as e:
            logger.error(f"  ❌ Search failed: {e}")
            results['failed_finds'] += 1
    
    return results

def test_vector_search_accuracy(samples: List[Dict]) -> Dict:
    """Test vector search accuracy"""
    results = {
        'total_tests': len(samples[:10]),  # Limit for performance
        'successful_finds': 0,
        'failed_finds': 0,
        'response_times': []
    }
    
    for i, sample in enumerate(samples[:10]):  # Test subset for vector search
        logger.info(f"Vector testing {i+1}/10: {sample['test_query'][:30]}...")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{API_BASE}/api/v4/vector/search",
                json={
                    'query': sample['test_query'],
                    'limit': 10
                },
                timeout=15
            )
            
            response_time = (time.time() - start_time) * 1000
            results['response_times'].append(response_time)
            
            if response.status_code == 200:
                search_data = response.json()
                found_chunks = search_data.get('results', [])
                
                # Check if expected chunk is in results
                found_expected = any(
                    result.get('chunk_id') == sample['expected_chunk_id']
                    for result in found_chunks
                )
                
                if found_expected:
                    results['successful_finds'] += 1
                    status = "✅ FOUND"
                else:
                    results['failed_finds'] += 1
                    status = "❌ NOT FOUND"
                
                logger.info(f"  {status} - {len(found_chunks)} results in {response_time:.1f}ms")
                
        except Exception as e:
            logger.error(f"  ❌ Vector search failed: {e}")
            results['failed_finds'] += 1
    
    return results

def generate_test_report(samples: List[Dict], search_results: Dict, vector_results: Dict):
    """Generate comprehensive test report"""
    
    print("\n" + "="*60)
    print("🧪 SEARCH ACCURACY TEST REPORT")
    print("="*60)
    
    print(f"\n📚 Test Dataset:")
    print(f"   Books sampled: {len(set(s['book_id'] for s in samples))}")
    print(f"   Total test queries: {len(samples)}")
    print(f"   Avg query length: {sum(s['word_count'] for s in samples) / len(samples):.1f} words")
    
    print(f"\n🔍 Full-Text Search Results:")
    accuracy = (search_results['successful_finds'] / search_results['total_tests']) * 100
    avg_time = sum(search_results['response_times']) / len(search_results['response_times'])
    print(f"   Accuracy: {search_results['successful_finds']}/{search_results['total_tests']} ({accuracy:.1f}%)")
    print(f"   Avg Response Time: {avg_time:.1f}ms")
    print(f"   Success Rate: {'✅ EXCELLENT' if accuracy > 80 else '⚠️ NEEDS IMPROVEMENT' if accuracy > 60 else '❌ POOR'}")
    
    print(f"\n🧠 Vector Search Results:")
    if vector_results['response_times']:
        vector_accuracy = (vector_results['successful_finds'] / vector_results['total_tests']) * 100
        vector_avg_time = sum(vector_results['response_times']) / len(vector_results['response_times'])
        print(f"   Accuracy: {vector_results['successful_finds']}/{vector_results['total_tests']} ({vector_accuracy:.1f}%)")
        print(f"   Avg Response Time: {vector_avg_time:.1f}ms")
        print(f"   Success Rate: {'✅ EXCELLENT' if vector_accuracy > 70 else '⚠️ NEEDS IMPROVEMENT' if vector_accuracy > 50 else '❌ POOR'}")
    else:
        print("   ❌ No vector search results available")
    
    print(f"\n📊 Performance Analysis:")
    if search_results['response_times']:
        min_time = min(search_results['response_times'])
        max_time = max(search_results['response_times'])
        print(f"   Fastest search: {min_time:.1f}ms")
        print(f"   Slowest search: {max_time:.1f}ms")
        print(f"   Performance: {'✅ FAST' if avg_time < 100 else '⚠️ MODERATE' if avg_time < 500 else '❌ SLOW'}")
    
    print(f"\n🎯 Recommendations:")
    if accuracy < 70:
        print("   - Review search indexing strategy")
        print("   - Consider improving text preprocessing")
        print("   - Check chunk size optimization")
    elif accuracy < 90:
        print("   - Fine-tune search ranking algorithms")
        print("   - Consider semantic search enhancements")
    else:
        print("   - ✅ Search accuracy is excellent!")
        print("   - Consider optimizing for speed if needed")
    
    print("\n" + "="*60)

def main():
    print("🧪 Starting Search Accuracy Test - Dr. Rodriguez & Dr. Chen")
    print("📖 Extracting random samples from book collection...")
    
    # Start optimized test server if not running
    try:
        response = requests.get(f"{API_BASE}/api/v4/health", timeout=5)
        if response.status_code != 200:
            print("⚠️ Optimized test server not responding - please start it first")
            return
    except:
        print("⚠️ Optimized test server not available - please start it first")
        print("Run: python3 scripts/test_api_endpoints_optimized.py")
        return
    
    # Extract samples
    samples = extract_random_book_samples(20)
    
    if not samples:
        print("❌ Failed to extract samples")
        return
    
    print(f"✅ Extracted {len(samples)} test samples")
    
    # Test search accuracy
    print("\n🔍 Testing full-text search accuracy...")
    search_results = test_search_accuracy(samples)
    
    print("\n🧠 Testing vector search accuracy...")
    vector_results = test_vector_search_accuracy(samples)
    
    # Generate report
    generate_test_report(samples, search_results, vector_results)

if __name__ == "__main__":
    main()