#!/usr/bin/env python3
"""
Quick test of optimized search performance
"""

import psycopg2
import psycopg2.extras
import time

DB_CONFIG = {
    'host': 'localhost',
    'database': 'knowledge_base',
    'user': 'weixiangzhang',
    'port': 5432
}

def test_search_performance():
    """Test optimized vs old search methods"""
    
    conn = psycopg2.connect(**DB_CONFIG)
    
    test_queries = [
        "the last call for",
        "in which we live", 
        "preparing for drought"
    ]
    
    print("🔍 Testing Search Performance Optimization")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        
        # Test optimized full-text search
        start_time = time.time()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.chunk_id, c.content, b.title, b.author,
                       ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', %s)) as rank
                FROM chunks c
                JOIN books b ON c.book_id = b.book_id
                WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', %s)
                ORDER BY rank DESC
                LIMIT 5
            """, (query, query))
            
            results = cur.fetchall()
            optimized_time = (time.time() - start_time) * 1000
        
        print(f"  Optimized: {len(results)} results in {optimized_time:.1f}ms")
        
        if results:
            print(f"  Top match: '{results[0][1][:50]}...'")
            print(f"  From book: {results[0][2]}")
    
    conn.close()
    print(f"\n✅ Search optimization test complete!")

if __name__ == "__main__":
    test_search_performance()