#!/usr/bin/env python3
"""
Streamlined Audiobook Search Test - Performance Focused
Dr. Rodriguez & Dr. Chen - Optimized Implementation
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

@app.route('/search')
def optimized_search():
    """Optimized search endpoint with strict performance limits"""
    query = request.args.get('q', '')
    if not query or len(query) < 3:
        return jsonify({"error": "Query too short"}), 400
    
    start_time = time.time()
    
    try:
        conn = get_db()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Optimized query with performance limits
            cur.execute("""
                SELECT c.chunk_id, 
                       LEFT(c.content, 200) as content_preview,
                       b.title, 
                       b.author,
                       ts_rank_cd(to_tsvector('english', c.content), plainto_tsquery('english', %s)) as rank
                FROM chunks c
                JOIN books b ON c.book_id = b.book_id
                WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', %s)
                  AND ts_rank_cd(to_tsvector('english', c.content), plainto_tsquery('english', %s)) > 0.1
                ORDER BY rank DESC
                LIMIT 5
            """, (query, query, query))
            
            results = cur.fetchall()
            response_time = (time.time() - start_time) * 1000
            
            return jsonify({
                "query": query,
                "results": [dict(r) for r in results],
                "count": len(results),
                "response_time_ms": round(response_time, 1),
                "optimization": "full_text_search_with_rank_filter"
            })
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "response_time_ms": round((time.time() - start_time) * 1000, 1)
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

def test_audiobook_scenarios():
    """Test audiobook search scenarios with optimized endpoint"""
    
    # Start minimal test server
    def run_server():
        app.run(host='127.0.0.1', port=9004, debug=False, use_reloader=False)
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(2)  # Wait for server to start
    
    print("🎧 Streamlined Audiobook Search Test")
    print("=" * 50)
    
    test_queries = [
        "the last call for",
        "jaunt stephen king", 
        "preparing for drought",
        "in which we live",
        "data smart using"
    ]
    
    results = []
    
    for i, query in enumerate(test_queries):
        print(f"\nTest {i+1}/5: '{query}'")
        
        try:
            start_time = time.time()
            response = requests.get(
                f"http://127.0.0.1:9004/search",
                params={'q': query},
                timeout=5
            )
            total_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                internal_time = data.get('response_time_ms', 0)
                result_count = data.get('count', 0)
                
                status = "✅ SUCCESS" if total_time < 5000 else "⚠️ SLOW"
                print(f"  {status}: {result_count} results")
                print(f"  Total time: {total_time:.1f}ms")
                print(f"  DB time: {internal_time}ms")
                
                if result_count > 0 and 'results' in data:
                    top_result = data['results'][0]
                    print(f"  Top: {top_result['title'][:30]}...")
                
                results.append({
                    'query': query,
                    'success': True,
                    'total_time': total_time,
                    'db_time': internal_time,
                    'results': result_count
                })
            else:
                print(f"  ❌ ERROR: {response.status_code}")
                results.append({
                    'query': query,
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                })
                
        except Exception as e:
            print(f"  ❌ TIMEOUT/ERROR: {e}")
            results.append({
                'query': query,
                'success': False,
                'error': str(e)
            })
    
    # Summary
    successful = [r for r in results if r.get('success', False)]
    fast_enough = [r for r in successful if r.get('total_time', 9999) < 5000]
    
    print(f"\n📊 PERFORMANCE SUMMARY")
    print("=" * 30)
    print(f"Successful searches: {len(successful)}/5")
    print(f"Under 5 seconds: {len(fast_enough)}/5")
    
    if successful:
        avg_time = sum(r['total_time'] for r in successful) / len(successful)
        avg_db_time = sum(r['db_time'] for r in successful) / len(successful)
        
        print(f"Average total time: {avg_time:.1f}ms")
        print(f"Average DB time: {avg_db_time:.1f}ms")
    
    print(f"\n🎯 AUDIOBOOK READINESS:")
    if len(fast_enough) >= 4:
        print("  ✅ EXCELLENT - Ready for audiobook use")
    elif len(fast_enough) >= 3:
        print("  ⚠️ GOOD - Mostly ready")
    elif len(fast_enough) >= 2:
        print("  ⚠️ FAIR - Needs more optimization")
    else:
        print("  ❌ POOR - Not ready for audiobook use")
    
    return results

if __name__ == "__main__":
    test_audiobook_scenarios()