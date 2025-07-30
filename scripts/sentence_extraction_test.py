#!/usr/bin/env python3
"""
Sentence Extraction Phonetic Test
=================================

Extract real 2-7 word phrases from processed chunks and test phonetic matching.
No reprocessing needed - uses existing phonetic data.
"""

import psycopg2
import psycopg2.extras
import time
import requests
import re
import random
from flask import Flask, request, jsonify
import threading
from typing import List, Tuple

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'knowledge_base',
    'user': 'weixiangzhang',
    'port': 5432
}

app = Flask(__name__)

def get_db():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG)

def extract_sentence_phrases() -> List[Tuple[str, str, str]]:
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
                  AND LENGTH(c.content) > 100
                ORDER BY RANDOM()
                LIMIT 50
            """)
            
            chunks = cur.fetchall()
            
            for chunk in chunks:
                content = chunk['content']
                title = chunk['title']
                author = chunk['author']
                
                # Split into sentences
                sentences = re.split(r'[.!?]+', content)
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    words = sentence.split()
                    
                    # Extract phrases of 2-7 words
                    if len(words) >= 7:
                        # Take from beginning, middle, or end
                        start_positions = [0, len(words)//3, len(words)//2, len(words)-7]
                        for start in start_positions:
                            if start >= 0:
                                for length in [2, 3, 4, 5, 6, 7]:
                                    if start + length <= len(words):
                                        phrase_words = words[start:start + length]
                                        phrase = ' '.join(phrase_words)
                                        
                                        # Clean phrase
                                        phrase = re.sub(r'[^\w\s]', '', phrase).strip()
                                        
                                        if len(phrase) > 10 and phrase.lower() not in [p[0].lower() for p in phrases]:
                                            phrases.append((phrase, title, author))
                                            
                                            if len(phrases) >= 20:  # Collect 20 good phrases
                                                return phrases
            
            return phrases
            
    except Exception as e:
        print(f"Error extracting phrases: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/phonetic_search')
def phonetic_search():
    """Enhanced phonetic search for sentence testing"""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 3:
        return jsonify({"error": "Query too short"}), 400
    
    start_time = time.time()
    
    try:
        conn = get_db()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Set timeout
            cur.execute("SET statement_timeout = '5s';")
            
            # Enhanced search combining multiple strategies
            cur.execute("""
                SELECT c.chunk_id, 
                       LEFT(c.content, 300) as content_preview,
                       b.title, 
                       b.author,
                       GREATEST(
                           ts_rank_cd(to_tsvector('english', c.content), plainto_tsquery('english', %s)),
                           CASE 
                               WHEN c.content_audiobook_normalized IS NOT NULL THEN
                                   GREATEST(
                                       ts_rank_cd(to_tsvector('english', c.content_audiobook_normalized), plainto_tsquery('english', %s)) * 0.9,
                                       similarity(c.content_audiobook_normalized, %s) * 0.7
                                   )
                               ELSE 0
                           END
                       ) as rank,
                       CASE 
                           WHEN c.content ILIKE %s THEN 'exact'
                           WHEN c.content_audiobook_normalized IS NOT NULL AND c.content_audiobook_normalized ILIKE %s THEN 'phonetic'
                           ELSE 'fuzzy'
                       END as match_type
                FROM chunks c
                JOIN books b ON c.book_id = b.book_id
                WHERE (
                    to_tsvector('english', c.content) @@ plainto_tsquery('english', %s)
                    OR c.content ILIKE %s
                    OR (c.content_audiobook_normalized IS NOT NULL 
                        AND (
                            to_tsvector('english', c.content_audiobook_normalized) @@ plainto_tsquery('english', %s)
                            OR c.content_audiobook_normalized ILIKE %s
                            OR similarity(c.content_audiobook_normalized, %s) > 0.3
                        ))
                )
                ORDER BY rank DESC
                LIMIT 10
            """, (query, query, query, f'%{query}%', f'%{query}%', query, f'%{query}%', query, f'%{query}%', query))
            
            results = cur.fetchall()
            response_time = (time.time() - start_time) * 1000
            
            return jsonify({
                "query": query,
                "results": [dict(r) for r in results],
                "count": len(results),
                "response_time_ms": round(response_time, 1),
                "search_type": "enhanced_phonetic_sentence"
            })
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "response_time_ms": round((time.time() - start_time) * 1000, 1)
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

def test_sentence_phonetic_matching():
    """Test phonetic matching with real extracted sentences"""
    
    print("🔍 Extracting real sentences from processed chunks...")
    extracted_phrases = extract_sentence_phrases()
    
    if not extracted_phrases:
        print("❌ Could not extract phrases")
        return
    
    print(f"✅ Extracted {len(extracted_phrases)} real phrases from books")
    
    # Start test server
    def run_server():
        app.run(host='127.0.0.1', port=9008, debug=False, use_reloader=False)
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(2)
    
    print("\n🧪 Testing Sentence-Level Phonetic Matching")
    print("=" * 60)
    
    successful_matches = 0
    total_tests = min(15, len(extracted_phrases))  # Test up to 15 phrases
    
    for i, (phrase, title, author) in enumerate(extracted_phrases[:total_tests]):
        word_count = len(phrase.split())
        print(f"\nTest {i+1}/{total_tests}: {word_count} words")
        print(f"Original: '{phrase}'")
        print(f"From: {title[:40]}... by {author}")
        
        try:
            start_time = time.time()
            response = requests.get(
                "http://127.0.0.1:9008/phonetic_search",
                params={'q': phrase},
                timeout=6
            )
            total_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                result_count = data.get('count', 0)
                
                if result_count > 0:
                    successful_matches += 1
                    top_result = data['results'][0]
                    match_type = top_result.get('match_type', 'unknown')
                    
                    print(f"  ✅ FOUND: {result_count} results ({match_type} match)")
                    print(f"  Time: {total_time:.1f}ms")
                    print(f"  Match: '{top_result['content_preview'][:80]}...'")
                    
                    # Check if it's the same book (good sign)
                    if title.lower() in top_result['title'].lower():
                        print(f"  🎯 SAME BOOK: Perfect match!")
                else:
                    print(f"  ❌ NOT FOUND: No matches")
                    print(f"  Time: {total_time:.1f}ms")
                    
            else:
                print(f"  ❌ ERROR: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
    
    # Summary
    success_rate = (successful_matches / total_tests) * 100
    print(f"\n📊 SENTENCE MATCHING RESULTS")
    print("=" * 40)
    print(f"Successful matches: {successful_matches}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎯 EXCELLENT: Sentence-level phonetic matching working very well")
    elif success_rate >= 60:
        print("🎯 GOOD: Strong sentence matching capability")
    elif success_rate >= 40:
        print("🎯 FAIR: Decent sentence matching")
    else:
        print("🎯 NEEDS WORK: Limited sentence matching success")
    
    print(f"\n💡 Testing 2-7 word phrases from real book content")
    print(f"🎧 Perfect for audiobook scenarios where you hear a sentence!")

if __name__ == "__main__":
    test_sentence_phonetic_matching()