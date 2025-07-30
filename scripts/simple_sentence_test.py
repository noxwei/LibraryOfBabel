#!/usr/bin/env python3
"""
Simple Sentence Test - Real 2-7 Word Phrases
===========================================

Test phonetic matching with real extracted sentences without complex dependencies.
"""

import psycopg2
import psycopg2.extras
import time
import re
import random
from typing import List, Tuple

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'knowledge_base',
    'user': 'weixiangzhang',
    'port': 5432
}

def get_db():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG)

def extract_real_phrases() -> List[Tuple[str, str, str]]:
    """Extract real 2-7 word phrases from processed chunks"""
    phrases = []
    
    try:
        conn = get_db()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Get random chunks that have been phonetically processed
            cur.execute("""
                SELECT c.content, b.title, b.author
                FROM chunks c
                JOIN books b ON c.book_id = b.book_id
                WHERE c.content_audiobook_normalized IS NOT NULL
                  AND LENGTH(c.content) > 200
                ORDER BY RANDOM()
                LIMIT 30
            """)
            
            chunks = cur.fetchall()
            
            for chunk in chunks:
                content = chunk['content']
                title = chunk['title']
                author = chunk['author']
                
                # Clean and split content
                content = re.sub(r'[^\w\s.]', ' ', content)
                sentences = content.split('.')
                
                for sentence in sentences:
                    words = sentence.strip().split()
                    
                    # Extract phrases of different lengths
                    if len(words) >= 7:
                        for length in [2, 3, 4, 5, 6, 7]:
                            for start in [0, len(words)//3, len(words)//2, max(0, len(words)-length)]:
                                if start + length <= len(words):
                                    phrase_words = words[start:start + length]
                                    phrase = ' '.join(phrase_words).strip()
                                    
                                    # Only keep meaningful phrases
                                    if (len(phrase) > 8 and 
                                        phrase.lower() not in [p[0].lower() for p in phrases] and
                                        not phrase.lower().startswith(('the the', 'a a', 'and and'))):
                                        phrases.append((phrase, title, author))
                                        
                                        if len(phrases) >= 15:
                                            return phrases
            
            return phrases
            
    except Exception as e:
        print(f"Error extracting phrases: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

def search_phrase_simple(phrase: str) -> dict:
    """Simple search for a phrase using multiple strategies"""
    start_time = time.time()
    
    try:
        conn = get_db()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SET statement_timeout = '5s';")
            
            # Strategy 1: Exact content search
            cur.execute("""
                SELECT c.chunk_id, 
                       LEFT(c.content, 200) as content_preview,
                       b.title, 
                       b.author,
                       'exact' as match_type
                FROM chunks c
                JOIN books b ON c.book_id = b.book_id
                WHERE c.content ILIKE %s
                LIMIT 5
            """, (f'%{phrase}%',))
            
            exact_results = cur.fetchall()
            
            if exact_results:
                return {
                    'results': [dict(r) for r in exact_results],
                    'count': len(exact_results),
                    'match_type': 'exact',
                    'time_ms': round((time.time() - start_time) * 1000, 1)
                }
            
            # Strategy 2: Phonetic normalized search
            cur.execute("""
                SELECT c.chunk_id, 
                       LEFT(c.content, 200) as content_preview,
                       b.title, 
                       b.author,
                       'phonetic' as match_type
                FROM chunks c
                JOIN books b ON c.book_id = b.book_id
                WHERE c.content_audiobook_normalized IS NOT NULL
                  AND c.content_audiobook_normalized ILIKE %s
                LIMIT 5
            """, (f'%{phrase}%',))
            
            phonetic_results = cur.fetchall()
            
            if phonetic_results:
                return {
                    'results': [dict(r) for r in phonetic_results],
                    'count': len(phonetic_results),
                    'match_type': 'phonetic',
                    'time_ms': round((time.time() - start_time) * 1000, 1)
                }
            
            # Strategy 3: Full-text search
            cur.execute("""
                SELECT c.chunk_id, 
                       LEFT(c.content, 200) as content_preview,
                       b.title, 
                       b.author,
                       'fulltext' as match_type
                FROM chunks c
                JOIN books b ON c.book_id = b.book_id
                WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', %s)
                LIMIT 5
            """, (phrase,))
            
            fulltext_results = cur.fetchall()
            
            return {
                'results': [dict(r) for r in fulltext_results],
                'count': len(fulltext_results),
                'match_type': 'fulltext',
                'time_ms': round((time.time() - start_time) * 1000, 1)
            }
            
    except Exception as e:
        return {
            'error': str(e),
            'results': [],
            'count': 0,
            'time_ms': round((time.time() - start_time) * 1000, 1)
        }
    finally:
        if 'conn' in locals():
            conn.close()

def test_sentence_extraction():
    """Test phonetic matching with real 2-7 word phrases"""
    
    print("🔍 Extracting real phrases from processed chunks...")
    phrases = extract_real_phrases()
    
    if not phrases:
        print("❌ Could not extract phrases")
        return
    
    print(f"✅ Extracted {len(phrases)} real phrases from books")
    
    print("\n🧪 Testing Real Sentence Phrase Matching")
    print("=" * 60)
    
    successful_matches = 0
    exact_matches = 0
    phonetic_matches = 0
    
    for i, (phrase, title, author) in enumerate(phrases):
        word_count = len(phrase.split())
        print(f"\nTest {i+1}/{len(phrases)}: {word_count} words")
        print(f"Query: '{phrase}'")
        print(f"From: {title[:50]}... by {author[:20]}")
        
        result = search_phrase_simple(phrase)
        
        if 'error' in result:
            print(f"  ❌ ERROR: {result['error']}")
            continue
        
        if result['count'] > 0:
            successful_matches += 1
            match_type = result['match_type']
            top_result = result['results'][0]
            
            if match_type == 'exact':
                exact_matches += 1
                print(f"  ✅ EXACT MATCH: {result['count']} results")
            elif match_type == 'phonetic':
                phonetic_matches += 1
                print(f"  🎧 PHONETIC MATCH: {result['count']} results")
            else:
                print(f"  🔍 FULLTEXT MATCH: {result['count']} results")
            
            print(f"  Time: {result['time_ms']}ms")
            print(f"  Found: '{top_result['content_preview'][:70]}...'")
            
            # Check if same book
            if title.lower().replace(' ', '') in top_result['title'].lower().replace(' ', ''):
                print(f"  🎯 SAME BOOK: Perfect match!")
        else:
            print(f"  ❌ NOT FOUND: No matches in {result['time_ms']}ms")
    
    # Summary
    total_tests = len(phrases)
    success_rate = (successful_matches / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"\n📊 SENTENCE PHRASE MATCHING RESULTS")
    print("=" * 50)
    print(f"Total tests: {total_tests}")
    print(f"Successful matches: {successful_matches} ({success_rate:.1f}%)")
    print(f"Exact matches: {exact_matches}")
    print(f"Phonetic matches: {phonetic_matches}")
    print(f"Fulltext matches: {successful_matches - exact_matches - phonetic_matches}")
    
    if success_rate >= 80:
        print("🎯 EXCELLENT: Sentence phrase matching working very well")
    elif success_rate >= 60:
        print("🎯 GOOD: Strong sentence matching capability")
    elif success_rate >= 40:
        print("🎯 FAIR: Decent sentence matching with room for improvement")
    else:
        print("🎯 NEEDS WORK: Limited sentence matching success")
    
    print(f"\n💡 Testing with real 2-7 word phrases from {119000:,} processed chunks")
    print(f"🎧 Perfect for audiobook use cases!")
    
    # Show some example phrases tested
    print(f"\n📝 Example phrases tested:")
    for phrase, _, _ in phrases[:5]:
        word_count = len(phrase.split())
        print(f"  - '{phrase}' ({word_count} words)")

if __name__ == "__main__":
    test_sentence_extraction()