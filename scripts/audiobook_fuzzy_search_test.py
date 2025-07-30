#!/usr/bin/env python3
"""
Audiobook Fuzzy Search Test - Dr. Rodriguez & Dr. Chen
=====================================================

Real-world scenario: User listens to audiobook and types approximate words 
to find the text passage. Test fuzzy matching with intentional typos/variations.

Test Cases:
1. Known book + exact words (5 tests)
2. Known book + fuzzy words (5 tests) 
3. Unknown book + fuzzy words (5 tests)
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

API_BASE = "http://localhost:9003"

def get_db_connection():
    """Get database connection"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def create_fuzzy_variations(text: str) -> List[str]:
    """Create fuzzy variations like user would type while listening"""
    variations = []
    words = text.split()
    
    # Common typing mistakes when listening to audiobooks
    variations.append(text)  # Original
    
    # Missing punctuation
    variations.append(text.replace(",", "").replace(".", ""))
    
    # Common homophones/mishearings
    fuzzy_text = text.lower()
    fuzzy_text = fuzzy_text.replace("their", "there").replace("there", "their")
    fuzzy_text = fuzzy_text.replace("you're", "your").replace("your", "youre")
    fuzzy_text = fuzzy_text.replace("it's", "its").replace("its", "its")
    variations.append(fuzzy_text)
    
    # Partial words (user didn't catch full word)
    if len(words) >= 4:
        partial_words = []
        for word in words:
            if len(word) > 4:
                partial_words.append(word[:3] + "*")  # Truncated
            else:
                partial_words.append(word)
        variations.append(" ".join(partial_words))
    
    # Word order slightly off (common when typing fast)
    if len(words) >= 3:
        shuffled = words.copy()
        if len(shuffled) >= 2:
            # Swap two adjacent words
            i = random.randint(0, len(shuffled) - 2)
            shuffled[i], shuffled[i + 1] = shuffled[i + 1], shuffled[i]
            variations.append(" ".join(shuffled))
    
    # Typos (missing/extra letters)
    typo_text = text
    if len(typo_text) > 5:
        # Insert random typo
        pos = random.randint(1, len(typo_text) - 2)
        typo_text = typo_text[:pos] + typo_text[pos] + typo_text[pos:]
    variations.append(typo_text)
    
    return variations

def extract_known_book_samples(book_ids: List[int], samples_per_book: int = 1) -> List[Dict]:
    """Extract samples from specific known books"""
    conn = get_db_connection()
    if not conn:
        return []
    
    samples = []
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            for book_id in book_ids:
                # Get book info
                cur.execute("SELECT title, author FROM books WHERE book_id = %s", (book_id,))
                book_info = cur.fetchone()
                
                if book_info:
                    # Get middle chapters from this book
                    cur.execute("""
                        SELECT chunk_id, content, chapter_number
                        FROM chunks
                        WHERE book_id = %s 
                        AND chunk_type = 'chapter'
                        AND LENGTH(content) > 500
                        ORDER BY RANDOM()
                        LIMIT %s
                    """, (book_id, samples_per_book))
                    
                    chunks = cur.fetchall()
                    
                    for chunk in chunks:
                        content = chunk['content']
                        
                        # Extract a good 4-word phrase
                        sentences = re.split(r'[.!?]+', content)
                        for sentence in sentences:
                            words = sentence.strip().split()
                            if len(words) >= 6:  # Need at least 6 to extract 4
                                start_idx = random.randint(0, len(words) - 4)
                                phrase = " ".join(words[start_idx:start_idx + 4])
                                
                                # Clean up phrase
                                phrase = re.sub(r'[^\w\s]', '', phrase).strip()
                                
                                if len(phrase.split()) == 4:
                                    samples.append({
                                        'book_id': book_id,
                                        'book_title': book_info['title'],
                                        'author': book_info['author'],
                                        'chunk_id': chunk['chunk_id'],
                                        'chapter_number': chunk['chapter_number'],
                                        'original_phrase': phrase,
                                        'test_type': 'known_book'
                                    })
                                    break
    
    except Exception as e:
        logger.error(f"Known book sampling failed: {e}")
    finally:
        conn.close()
    
    return samples

def run_search_test(query: str, expected_chunk_id: int = None) -> Dict:
    """Run a search test and return results with 5-second timeout"""
    start_time = time.time()
    
    try:
        response = requests.get(
            f"{API_BASE}/api/v4/search",
            params={
                'q': query,
                'type': 'content',
                'limit': 10
            },
            timeout=5  # 5-second timeout for audiobook use case
        )
        
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            search_data = response.json()
            results = search_data.get('results', [])
            
            found_expected = False
            if expected_chunk_id:
                found_expected = any(
                    result.get('chunk_id') == expected_chunk_id
                    for result in results
                )
            
            return {
                'success': True,
                'found_expected': found_expected,
                'num_results': len(results),
                'response_time_ms': response_time,
                'results': results
            }
        else:
            return {
                'success': False,
                'error': f"HTTP {response.status_code}",
                'response_time_ms': response_time
            }
            
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        error_msg = str(e)
        if "timeout" in error_msg.lower():
            error_msg = "TIMEOUT (>5s) - TOO SLOW for audiobook use"
        
        return {
            'success': False,
            'error': error_msg,
            'response_time_ms': response_time,
            'timeout': response_time > 5000
        }

def main():
    print("🎧 Audiobook Fuzzy Search Test - Dr. Rodriguez & Dr. Chen")
    print("=" * 60)
    print("Scenario: User listens to audiobook, types approximate words to find text")
    
    # Check if API is available
    try:
        response = requests.get(f"{API_BASE}/api/v4/health", timeout=5)
        if response.status_code != 200:
            print("⚠️ Test server not available")
            return
    except:
        print("⚠️ Test server not available - start with: python3 scripts/test_api_endpoints_optimized.py")
        return
    
    # Select 5 specific books for testing
    test_book_ids = [1373, 738, 1379, 3784, 1889]  # From previous results
    
    print(f"\n📚 Extracting test phrases from {len(test_book_ids)} books...")
    known_samples = extract_known_book_samples(test_book_ids, samples_per_book=1)
    
    if len(known_samples) < 5:
        print(f"❌ Only got {len(known_samples)} samples, need 5")
        return
    
    print(f"✅ Generated {len(known_samples)} test samples")
    
    # Test 1: Known book + exact words (5 tests)
    print(f"\n🎯 TEST 1: Known Book + Exact Words")
    print("-" * 40)
    
    exact_results = []
    for i, sample in enumerate(known_samples[:5]):
        query = sample['original_phrase']
        print(f"Book: {sample['book_title'][:30]}...")
        print(f"Query: '{query}'")
        
        result = run_search_test(query, sample['chunk_id'])
        exact_results.append(result)
        
        if result['success']:
            status = "✅ FOUND" if result['found_expected'] else "❌ NOT FOUND"
            print(f"Result: {status} - {result['num_results']} results in {result['response_time_ms']:.1f}ms")
        else:
            print(f"Result: ❌ ERROR - {result['error']}")
        print()
    
    # Test 2: Known book + fuzzy words (5 tests)
    print(f"\n🔍 TEST 2: Known Book + Fuzzy Words (Audiobook Simulation)")
    print("-" * 40)
    
    fuzzy_results = []
    for i, sample in enumerate(known_samples[:5]):
        variations = create_fuzzy_variations(sample['original_phrase'])
        fuzzy_query = random.choice(variations[1:])  # Skip original
        
        print(f"Book: {sample['book_title'][:30]}...")
        print(f"Original: '{sample['original_phrase']}'")
        print(f"Fuzzy:    '{fuzzy_query}'")
        
        result = run_search_test(fuzzy_query, sample['chunk_id'])
        fuzzy_results.append(result)
        
        if result['success']:
            status = "✅ FOUND" if result['found_expected'] else "❌ NOT FOUND"
            print(f"Result: {status} - {result['num_results']} results in {result['response_time_ms']:.1f}ms")
        else:
            print(f"Result: ❌ ERROR - {result['error']}")
        print()
    
    # Test 3: Unknown book + fuzzy words (5 tests) 
    print(f"\n❓ TEST 3: Unknown Book + Fuzzy Words (Blind Search)")
    print("-" * 40)
    
    blind_results = []
    for i, sample in enumerate(known_samples[:5]):
        variations = create_fuzzy_variations(sample['original_phrase'])
        fuzzy_query = random.choice(variations[1:])
        
        print(f"Fuzzy Query: '{fuzzy_query}' (book unknown to searcher)")
        
        result = run_search_test(fuzzy_query)  # No expected chunk
        blind_results.append(result)
        
        if result['success']:
            print(f"Result: ✅ {result['num_results']} results in {result['response_time_ms']:.1f}ms")
            if result['results']:
                # Show top result
                top_result = result['results'][0]
                print(f"Top match: '{top_result.get('content', '')[:50]}...'")
        else:
            print(f"Result: ❌ ERROR - {result['error']}")
        print()
    
    # Generate Summary Report
    print(f"\n📊 AUDIOBOOK SEARCH TEST RESULTS")
    print("=" * 60)
    
    # Test 1 Stats
    exact_successful = sum(1 for r in exact_results if r['success'] and r['found_expected'])
    exact_avg_time = sum(r['response_time_ms'] for r in exact_results if r['success']) / max(1, len([r for r in exact_results if r['success']]))
    
    print(f"Test 1 - Known Book + Exact Words:")
    print(f"  Success Rate: {exact_successful}/5 ({exact_successful/5*100:.1f}%)")
    print(f"  Avg Response: {exact_avg_time:.1f}ms")
    
    # Test 2 Stats  
    fuzzy_successful = sum(1 for r in fuzzy_results if r['success'] and r['found_expected'])
    fuzzy_avg_time = sum(r['response_time_ms'] for r in fuzzy_results if r['success']) / max(1, len([r for r in fuzzy_results if r['success']]))
    
    print(f"\nTest 2 - Known Book + Fuzzy Words:")
    print(f"  Success Rate: {fuzzy_successful}/5 ({fuzzy_successful/5*100:.1f}%)")
    print(f"  Avg Response: {fuzzy_avg_time:.1f}ms")
    print(f"  Fuzzy Tolerance: {fuzzy_successful/max(1,exact_successful)*100:.1f}% of exact performance")
    
    # Test 3 Stats
    blind_successful = sum(1 for r in blind_results if r['success'] and r['num_results'] > 0)
    blind_avg_time = sum(r['response_time_ms'] for r in blind_results if r['success']) / max(1, len([r for r in blind_results if r['success']]))
    
    print(f"\nTest 3 - Unknown Book + Fuzzy Words:")
    print(f"  Results Found: {blind_successful}/5 ({blind_successful/5*100:.1f}%)")
    print(f"  Avg Response: {blind_avg_time:.1f}ms")
    
    print(f"\n🎯 AUDIOBOOK USE CASE ASSESSMENT:")
    if fuzzy_successful >= 3:
        print("  ✅ EXCELLENT - Good fuzzy matching for audiobook listeners")
    elif fuzzy_successful >= 2:
        print("  ⚠️ MODERATE - Some fuzzy matching capability")
    else:
        print("  ❌ POOR - Needs better fuzzy search implementation")
    
    # Count timeout failures
    exact_timeouts = sum(1 for r in exact_results if not r['success'] and r.get('timeout', False))
    fuzzy_timeouts = sum(1 for r in fuzzy_results if not r['success'] and r.get('timeout', False))
    blind_timeouts = sum(1 for r in blind_results if not r['success'] and r.get('timeout', False))
    
    total_timeouts = exact_timeouts + fuzzy_timeouts + blind_timeouts
    
    print(f"\n⏱️ TIMEOUT ANALYSIS:")
    print(f"  Total timeouts (>5s): {total_timeouts}/15")
    if total_timeouts > 5:
        print("  ❌ CRITICAL: Too many slow searches for audiobook use")
    elif total_timeouts > 2:
        print("  ⚠️ WARNING: Some searches too slow")
    else:
        print("  ✅ GOOD: Most searches complete quickly")
    
    print(f"\n💡 RECOMMENDATIONS:")
    if total_timeouts > 0:
        print("  🚨 PRIORITY: Optimize search performance (5s timeout requirement)")
        print("  - Add search result caching")
        print("  - Optimize database indexes")
        print("  - Consider search result limits")
    
    if fuzzy_successful < exact_successful:
        print("  - Implement fuzzy string matching algorithms")
        print("  - Add phonetic matching for audiobook queries")
        print("  - Consider Levenshtein distance scoring")
    
    print("  - Consider autocomplete/suggestion features")
    print("  - Add 'sound-alike' word matching")
    
    print(f"\n🎧 AUDIOBOOK USER EXPERIENCE:")
    if total_timeouts == 0 and fuzzy_successful >= 3:
        print("  ✅ EXCELLENT - Fast, fuzzy-tolerant searches")
    elif total_timeouts <= 2 and fuzzy_successful >= 2:
        print("  ⚠️ ACCEPTABLE - Mostly fast with some fuzzy capability")
    else:
        print("  ❌ POOR - Too slow or inflexible for audiobook listeners")

if __name__ == "__main__":
    main()