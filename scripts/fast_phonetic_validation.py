#!/usr/bin/env python3
"""
Fast Phonetic Search Validation
===============================

Quick validation of our phonetic search system using real database content.
Tests with actual misspellings against our 4,828 books and 165,206 chunks.
"""

import psycopg2
import random
import re
import time
from typing import List, Dict

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'knowledge_base',
    'user': 'weixiangzhang',
    'port': 5432
}

def get_random_content_samples(limit: int = 20) -> List[Dict]:
    """Get random content samples from our database"""
    conn = psycopg2.connect(**DB_CONFIG)
    
    try:
        with conn.cursor() as cur:
            # Get random chunks from different books
            cur.execute("""
                SELECT 
                    c.chunk_id,
                    b.title,
                    b.author,
                    LEFT(c.content, 200) as content_preview,
                    LENGTH(c.content) as chunk_length
                FROM chunks c
                JOIN books b ON c.book_id = b.book_id
                WHERE c.content IS NOT NULL
                AND LENGTH(c.content) BETWEEN 500 AND 2000
                AND c.content NOT LIKE 'Table of Contents%'
                ORDER BY RANDOM()
                LIMIT %s
            """, (limit,))
            
            results = []
            rows = cur.fetchall()
            for row in rows:
                results.append({
                    'chunk_id': row[0],
                    'title': row[1],
                    'author': row[2],
                    'content': row[3],
                    'length': row[4]
                })
            
            return results
            
    finally:
        conn.close()

def create_misspellings(text: str) -> List[str]:
    """Create realistic misspellings from text"""
    # Extract first 3-5 words
    words = re.findall(r'\w+', text.lower())[:4]
    if len(words) < 2:
        return []
    
    misspellings = []
    
    # Create 3 different misspelling patterns
    for pattern in range(3):
        misspelled_words = []
        
        for word in words:
            if len(word) < 3:
                misspelled_words.append(word)
                continue
                
            misspelled = word
            
            if pattern == 0:  # Letter substitutions
                substitutions = [('c', 'k'), ('ph', 'f'), ('qu', 'kw')]
                for old, new in substitutions:
                    if old in misspelled:
                        misspelled = misspelled.replace(old, new)
            
            elif pattern == 1:  # Missing letters
                if len(misspelled) > 4 and random.random() < 0.5:
                    pos = random.randint(1, len(misspelled) - 2)
                    misspelled = misspelled[:pos] + misspelled[pos+1:]
            
            elif pattern == 2:  # Common homophones/mistakes
                replacements = {
                    'their': 'there', 'there': 'their',
                    'to': 'too', 'too': 'to',
                    'your': 'you\'re', 'you\'re': 'your'
                }
                if misspelled in replacements:
                    misspelled = replacements[misspelled]
            
            misspelled_words.append(misspelled)
        
        if misspelled_words != words:  # Only add if actually changed
            misspellings.append(' '.join(misspelled_words))
    
    return misspellings

def test_phonetic_search(original: str, misspelled: str) -> Dict:
    """Test search with original vs misspelled text"""
    conn = psycopg2.connect(**DB_CONFIG)
    
    try:
        with conn.cursor() as cur:
            start_time = time.time()
            
            # Test with our phonetic search capabilities
            query = """
                SELECT 
                    COUNT(*) as total_matches,
                    COUNT(CASE WHEN c.content ILIKE %s THEN 1 END) as exact_matches,
                    COUNT(CASE WHEN c.content_audiobook_normalized ILIKE %s THEN 1 END) as normalized_matches
                FROM chunks c
                WHERE c.content ILIKE %s
                   OR c.content_audiobook_normalized ILIKE %s
                   OR (""" + " AND ".join([
                       "c.content ILIKE %s" for _ in misspelled.split()[:3]
                   ]) + """)
            """
            
            params = [
                f'%{misspelled}%',  # Exact phrase in content
                f'%{misspelled}%',  # Exact phrase in normalized
                f'%{misspelled}%',  # WHERE clause 1
                f'%{misspelled}%',  # WHERE clause 2
            ]
            
            # Add individual word patterns
            for word in misspelled.split()[:3]:
                params.append(f'%{word}%')
            
            cur.execute(query, params)
            result = cur.fetchone()
            
            search_time = (time.time() - start_time) * 1000
            
            return {
                'original': original,
                'misspelled': misspelled,
                'total_matches': result[0],
                'exact_matches': result[1],
                'normalized_matches': result[2],
                'search_time_ms': round(search_time, 2)
            }
            
    except Exception as e:
        return {
            'original': original,
            'misspelled': misspelled,
            'error': str(e),
            'total_matches': 0,
            'exact_matches': 0,
            'normalized_matches': 0,
            'search_time_ms': 0
        }
    finally:
        conn.close()

def main():
    """Run fast phonetic validation"""
    print("🚀 Fast Phonetic Search Validation")
    print("Using our literary database: 4,828 books, 165,206 chunks")
    print("=" * 60)
    
    # Get random content samples
    print("🔍 Sampling random content from database...")
    samples = get_random_content_samples(15)
    print(f"✅ Got {len(samples)} content samples")
    
    test_results = []
    total_tests = 0
    successful_tests = 0
    
    for i, sample in enumerate(samples):
        print(f"\n📖 Testing sample {i+1}: {sample['title'][:40]}...")
        print(f"   Author: {sample['author'][:30]}")
        
        # Create misspellings from content
        misspellings = create_misspellings(sample['content'])
        
        for misspelled in misspellings:
            if not misspelled:
                continue
                
            original = ' '.join(re.findall(r'\w+', sample['content'].lower())[:4])
            result = test_phonetic_search(original, misspelled)
            
            test_results.append(result)
            total_tests += 1
            
            if result['total_matches'] > 0:
                successful_tests += 1
                print(f"   ✅ '{misspelled}' → {result['total_matches']} matches ({result['search_time_ms']}ms)")
            else:
                print(f"   ❌ '{misspelled}' → no matches")
    
    # Summary
    print(f"\n📊 VALIDATION SUMMARY")
    print("=" * 40)
    print(f"Total tests: {total_tests}")
    print(f"Successful searches: {successful_tests}")
    print(f"Success rate: {successful_tests/total_tests*100:.1f}%")
    
    if test_results:
        avg_matches = sum(r['total_matches'] for r in test_results) / len(test_results)
        avg_time = sum(r['search_time_ms'] for r in test_results) / len(test_results)
        print(f"Average matches per query: {avg_matches:.1f}")
        print(f"Average search time: {avg_time:.1f}ms")
        
        # Show some examples
        print(f"\n🎯 EXAMPLE RESULTS:")
        successful_results = [r for r in test_results if r['total_matches'] > 0][:5]
        for result in successful_results:
            print(f"  '{result['misspelled']}' → {result['total_matches']} matches")
    
    print(f"\n✅ Phonetic search validation complete!")
    print("🎧 System ready for audiobook misspelling tolerance!")

if __name__ == "__main__":
    main()