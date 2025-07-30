#!/usr/bin/env python3
"""
Test Phonetic Processing Progress - Dr. Rodriguez & Dr. Chen
==========================================================

Test the phonetic matching capabilities on already-processed chunks
while the daemon continues processing the remaining chunks.
"""

import psycopg2
import psycopg2.extras
import time
import requests
from flask import Flask, request, jsonify
import threading

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

@app.route('/phonetic_search')
def phonetic_search():
    """Test phonetic search on processed chunks"""
    query = request.args.get('q', '')
    if not query or len(query) < 3:
        return jsonify({"error": "Query too short"}), 400
    
    start_time = time.time()
    
    try:
        conn = get_db()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Test 1: Audiobook normalized search (homophone/mishearing tolerant)
            cur.execute("""
                SELECT COUNT(*) 
                FROM chunks 
                WHERE content_audiobook_normalized IS NOT NULL
            """)
            processed_count = cur.fetchone()['count']
            
            # Search in audiobook normalized content
            cur.execute("""
                SELECT c.chunk_id, 
                       LEFT(c.content, 150) as content_preview,
                       LEFT(c.content_audiobook_normalized, 150) as normalized_preview,
                       b.title, 
                       b.author,
                       similarity(c.content_audiobook_normalized, %s) as similarity_score
                FROM chunks c
                JOIN books b ON c.book_id = b.book_id
                WHERE c.content_audiobook_normalized IS NOT NULL
                  AND (
                    c.content_audiobook_normalized ILIKE %s
                    OR similarity(c.content_audiobook_normalized, %s) > 0.2
                  )
                ORDER BY similarity_score DESC
                LIMIT 5
            """, (query, f'%{query}%', query))
            
            results = cur.fetchall()
            response_time = (time.time() - start_time) * 1000
            
            return jsonify({
                "query": query,
                "processed_chunks": processed_count,
                "results": [dict(r) for r in results],
                "count": len(results),
                "response_time_ms": round(response_time, 1),
                "search_type": "phonetic_audiobook_normalized"
            })
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "response_time_ms": round((time.time() - start_time) * 1000, 1)
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/soundex_search')
def soundex_search():
    """Test soundex phonetic search"""
    query = request.args.get('q', '')
    if not query or len(query) < 3:
        return jsonify({"error": "Query too short"}), 400
    
    start_time = time.time()
    
    try:
        conn = get_db()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Generate soundex for query
            cur.execute("SELECT soundex(%s) as query_soundex", (query,))
            query_soundex = cur.fetchone()['query_soundex']
            
            # Search using soundex matching
            cur.execute("""
                SELECT c.chunk_id,
                       LEFT(c.content, 150) as content_preview,
                       LEFT(c.content_soundex, 100) as soundex_codes,
                       b.title,
                       b.author
                FROM chunks c
                JOIN books b ON c.book_id = b.book_id
                WHERE c.content_soundex IS NOT NULL
                  AND c.content_soundex LIKE %s
                LIMIT 5
            """, (f'%{query_soundex}%',))
            
            results = cur.fetchall()
            response_time = (time.time() - start_time) * 1000
            
            return jsonify({
                "query": query,
                "query_soundex": query_soundex,
                "results": [dict(r) for r in results],
                "count": len(results),
                "response_time_ms": round(response_time, 1),
                "search_type": "soundex_phonetic"
            })
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "response_time_ms": round((time.time() - start_time) * 1000, 1)
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

def check_processing_status():
    """Check how many chunks have been phonetically processed"""
    try:
        conn = get_db()
        with conn.cursor() as cur:
            # Check processing progress
            cur.execute("""
                SELECT 
                    COUNT(*) as total_chunks,
                    COUNT(CASE WHEN content_audiobook_normalized IS NOT NULL THEN 1 END) as normalized_processed,
                    COUNT(CASE WHEN content_soundex IS NOT NULL THEN 1 END) as soundex_processed,
                    COUNT(CASE WHEN content_metaphone IS NOT NULL THEN 1 END) as metaphone_processed
                FROM chunks
            """)
            
            stats = cur.fetchone()
            return {
                'total_chunks': stats[0],
                'normalized_processed': stats[1],
                'soundex_processed': stats[2],
                'metaphone_processed': stats[3]
            }
    except Exception as e:
        print(f"Error checking status: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()

def test_phonetic_audiobook_scenarios():
    """Test real audiobook mishearing scenarios"""
    
    # Start test server
    def run_server():
        app.run(host='127.0.0.1', port=9005, debug=False, use_reloader=False)
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(2)
    
    print("🔊 Testing Phonetic Processing - Dr. Rodriguez & Dr. Chen")
    print("=" * 60)
    
    # Check processing status
    status = check_processing_status()
    if status:
        processed_percent = (status['normalized_processed'] / status['total_chunks']) * 100
        print(f"📊 Processing Status:")
        print(f"   Total chunks: {status['total_chunks']:,}")
        print(f"   Normalized: {status['normalized_processed']:,} ({processed_percent:.1f}%)")
        print(f"   Soundex: {status['soundex_processed']:,}")
        print(f"   Metaphone: {status['metaphone_processed']:,}")
        print()
    
    # Test audiobook mishearing scenarios
    audiobook_tests = [
        # Homophones (common audiobook mistakes)
        ("there house", "their house mishearing"),
        ("your right", "you're right mishearing"),
        ("its working", "it's working mishearing"),
        
        # Common mishearings
        ("effect change", "affect/effect confusion"),
        ("then better", "than/then confusion"),
        
        # Pronunciation variants
        ("lisen carefully", "listen with silent T"),
        ("ofen happens", "often with silent T"),
        
        # Partial words (user didn't catch full word)
        ("preparin for", "preparing for - partial"),
    ]
    
    print("🎧 Testing Audiobook Mishearing Scenarios:")
    print("-" * 45)
    
    successful_tests = 0
    
    for i, (mishearing, description) in enumerate(audiobook_tests):
        print(f"\nTest {i+1}: {description}")
        print(f"Query: '{mishearing}'")
        
        try:
            # Test phonetic search
            start_time = time.time()
            response = requests.get(
                f"http://127.0.0.1:9005/phonetic_search",
                params={'q': mishearing},
                timeout=5
            )
            total_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                result_count = data.get('count', 0)
                processed_chunks = data.get('processed_chunks', 0)
                
                if result_count > 0:
                    successful_tests += 1
                    status = "✅ FOUND"
                    top_result = data['results'][0]
                    similarity = top_result.get('similarity_score', 0)
                    print(f"  {status}: {result_count} results (similarity: {similarity:.2f})")
                    print(f"  From: {top_result['title'][:40]}...")
                    print(f"  Match: '{top_result['content_preview'][:60]}...'")
                else:
                    print(f"  ❌ NOT FOUND: No phonetic matches")
                
                print(f"  Time: {total_time:.1f}ms | Processed chunks: {processed_chunks:,}")
                
            else:
                print(f"  ❌ ERROR: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
    
    print(f"\n📊 PHONETIC TEST RESULTS")
    print("=" * 30)
    print(f"Successful phonetic matches: {successful_tests}/{len(audiobook_tests)}")
    
    if successful_tests >= 6:
        print("🎯 EXCELLENT: Phonetic matching working well")
    elif successful_tests >= 4:
        print("🎯 GOOD: Decent phonetic matching capability")
    elif successful_tests >= 2:
        print("🎯 FAIR: Some phonetic matching working")
    else:
        print("🎯 NEEDS WORK: Limited phonetic matching")
    
    # Test specific soundex search
    print(f"\n🔤 Testing Soundex Phonetic Search:")
    print("-" * 35)
    
    soundex_tests = ["hello", "world", "listen", "there"]
    
    for word in soundex_tests:
        try:
            response = requests.get(
                f"http://127.0.0.1:9005/soundex_search",
                params={'q': word},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"'{word}' (soundex: {data.get('query_soundex')}) -> {data.get('count', 0)} matches")
            else:
                print(f"'{word}' -> ERROR")
                
        except Exception as e:
            print(f"'{word}' -> ERROR: {e}")
    
    print(f"\n💡 Note: Daemon continues processing remaining chunks in background")
    print(f"🎧 Phonetic matching will improve as more chunks are processed!")

if __name__ == "__main__":
    test_phonetic_audiobook_scenarios()