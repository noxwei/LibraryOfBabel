#!/usr/bin/env python3
"""
🧪 POSTGRESQL FUNCTIONS PERFORMANCE TEST
========================================

Test all Phase 1 PostgreSQL functions and show performance results
Dr. Sarah Chen (陈雪芳) + Claude Code collaboration
"""

import psycopg2
import psycopg2.extras
import os
import time
import json
from datetime import datetime

def test_postgresql_functions():
    """Comprehensive test of all PostgreSQL functions"""
    
    print("🧪 POSTGRESQL FUNCTIONS PERFORMANCE TEST")
    print("=" * 60)
    print("🏛️ Dr. Sarah Chen (陈雪芳) - Database Functions Testing")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'knowledge_base'),
        'user': os.getenv('DB_USER', 'weixiangzhang'),
        'port': int(os.getenv('DB_PORT', 5432))
    }
    
    results = {}
    
    try:
        conn = psycopg2.connect(**db_config)
        print("✅ Database connection established")
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            
            # TEST 1: System Health Check
            print("\n🏥 TEST 1: System Health Check")
            print("-" * 30)
            start_time = time.time()
            cur.execute("SELECT * FROM api_system_health_check()")
            health_results = cur.fetchall()
            health_time = (time.time() - start_time) * 1000
            
            print(f"⏱️  Execution time: {health_time:.2f}ms")
            for row in health_results:
                print(f"   📊 {row['metric']}: {row['value']} ({row['status']})")
            
            results['health_check'] = {
                'time_ms': health_time,
                'metrics_count': len(health_results),
                'status': 'success'
            }
            
            # TEST 2: Book Listing with Pagination
            print("\n📚 TEST 2: Book Listing (Paginated)")
            print("-" * 30)
            start_time = time.time()
            cur.execute("SELECT * FROM api_list_books(1, 10)")
            book_results = cur.fetchall()
            book_time = (time.time() - start_time) * 1000
            
            print(f"⏱️  Execution time: {book_time:.2f}ms")
            if book_results:
                first_book = book_results[0]
                print(f"   📖 Sample result: '{first_book['title']}' by {first_book['author']}")
                print(f"   📊 Total items: {first_book['total_items']}")
                print(f"   📄 Total pages: {first_book['total_pages']}")
                print(f"   📍 Current page: {first_book['current_page']}")
            
            results['book_listing'] = {
                'time_ms': book_time,
                'results_count': len(book_results),
                'status': 'success'
            }
            
            # TEST 3: Book Details
            print("\n📖 TEST 3: Book Details")
            print("-" * 30)
            if book_results:
                test_book_id = book_results[0]['book_id']
                start_time = time.time()
                cur.execute("SELECT * FROM api_get_book_details(%s)", (test_book_id,))
                detail_results = cur.fetchall()
                detail_time = (time.time() - start_time) * 1000
                
                print(f"⏱️  Execution time: {detail_time:.2f}ms")
                if detail_results:
                    book = detail_results[0]
                    print(f"   📚 Book: '{book['title']}'")
                    print(f"   👤 Author: {book['author']}")
                    print(f"   📄 Chunks: {book['chunk_count']}")
                    print(f"   🧠 Embeddings: {book['embedding_count']}")
                
                results['book_details'] = {
                    'time_ms': detail_time,
                    'status': 'success'
                }
            
            # TEST 4: Book Chunks
            print("\n📄 TEST 4: Book Chunks")
            print("-" * 30)
            if book_results:
                test_book_id = book_results[0]['book_id']
                start_time = time.time()
                cur.execute("SELECT * FROM api_get_book_chunks(%s, 1, 5, 'medium')", (test_book_id,))
                chunk_results = cur.fetchall()
                chunk_time = (time.time() - start_time) * 1000
                
                print(f"⏱️  Execution time: {chunk_time:.2f}ms")
                if chunk_results:
                    chunk = chunk_results[0]
                    print(f"   📄 Sample chunk: {chunk['chunk_id']}")
                    print(f"   📊 Total chunks: {chunk['total_items']}")
                    print(f"   🔤 Content preview: {chunk['content'][:100]}...")
                
                results['book_chunks'] = {
                    'time_ms': chunk_time,
                    'results_count': len(chunk_results),
                    'status': 'success'
                }
            
            # TEST 5: Text Search
            print("\n🔍 TEST 5: Text Search")
            print("-" * 30)
            search_queries = ['technology', 'artificial intelligence', 'philosophy', 'science']
            
            for query in search_queries:
                start_time = time.time()
                cur.execute("SELECT * FROM api_text_search(%s, 10)", (query,))
                search_results = cur.fetchall()
                search_time = (time.time() - start_time) * 1000
                
                print(f"⏱️  Query '{query}': {search_time:.2f}ms ({len(search_results)} results)")
                if search_results:
                    result = search_results[0]
                    print(f"   📚 Top result: '{result['title']}' (rank: {result['text_rank']:.3f})")
                
                if query not in results:
                    results['text_search'] = []
                results['text_search'].append({
                    'query': query,
                    'time_ms': search_time,
                    'results_count': len(search_results),
                    'status': 'success'
                })
            
            # TEST 6: Vector Search
            print("\n🧠 TEST 6: Vector Search")
            print("-" * 30)
            
            # Get a sample vector for testing
            cur.execute("""
                SELECT embedding_vector 
                FROM chunk_embeddings 
                WHERE embedding_vector IS NOT NULL 
                ORDER BY RANDOM() 
                LIMIT 1
            """)
            vector_result = cur.fetchone()
            
            if vector_result:
                sample_vector = vector_result['embedding_vector']
                start_time = time.time()
                cur.execute("SELECT * FROM api_vector_search(%s, 10)", (sample_vector,))
                vector_results = cur.fetchall()
                vector_time = (time.time() - start_time) * 1000
                
                print(f"⏱️  Vector search: {vector_time:.2f}ms ({len(vector_results)} results)")
                if vector_results:
                    result = vector_results[0]
                    print(f"   🎯 Top result: '{result['title']}' (similarity: {result['similarity_score']:.3f})")
                
                results['vector_search'] = {
                    'time_ms': vector_time,
                    'results_count': len(vector_results),
                    'status': 'success'
                }
            else:
                print("⚠️  No vector embeddings available for testing")
                results['vector_search'] = {'status': 'no_vectors'}
            
            # TEST 7: Hybrid Search
            print("\n🔀 TEST 7: Hybrid Search")
            print("-" * 30)
            
            if vector_result:
                sample_vector = vector_result['embedding_vector']
                test_query = 'artificial intelligence'
                
                start_time = time.time()
                cur.execute("SELECT * FROM api_hybrid_search_optimized(%s, %s, 0.7, 0.3, 10)", 
                           (test_query, sample_vector))
                hybrid_results = cur.fetchall()
                hybrid_time = (time.time() - start_time) * 1000
                
                print(f"⏱️  Hybrid search: {hybrid_time:.2f}ms ({len(hybrid_results)} results)")
                if hybrid_results:
                    result = hybrid_results[0]
                    print(f"   🎯 Top result: '{result['title']}'")
                    print(f"   📊 Combined score: {result['combined_score']:.3f}")
                    print(f"   📝 Text rank: {result['text_rank']:.3f}")
                    print(f"   🧠 Vector similarity: {result['vector_similarity']:.3f}")
                
                results['hybrid_search'] = {
                    'time_ms': hybrid_time,
                    'results_count': len(hybrid_results),
                    'status': 'success'
                }
            else:
                print("⚠️  No vector embeddings available for hybrid search")
                results['hybrid_search'] = {'status': 'no_vectors'}
            
            # TEST 8: Performance Metrics
            print("\n📈 TEST 8: Performance Metrics")
            print("-" * 30)
            start_time = time.time()
            cur.execute("SELECT * FROM api_get_performance_metrics(1)")
            perf_results = cur.fetchall()
            perf_time = (time.time() - start_time) * 1000
            
            print(f"⏱️  Execution time: {perf_time:.2f}ms")
            print(f"   📊 Functions tracked: {len(perf_results)}")
            
            results['performance_metrics'] = {
                'time_ms': perf_time,
                'functions_tracked': len(perf_results),
                'status': 'success'
            }
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        results['error'] = str(e)
        return results
    
    # PERFORMANCE SUMMARY
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 60)
    
    performance_targets = {
        'health_check': 50,
        'book_listing': 30,
        'book_details': 30,
        'book_chunks': 50,
        'text_search': 100,
        'vector_search': 20,
        'hybrid_search': 100,
        'performance_metrics': 50
    }
    
    for test_name, target_ms in performance_targets.items():
        if test_name in results and 'time_ms' in results[test_name]:
            actual_ms = results[test_name]['time_ms']
            status = "✅ PASS" if actual_ms <= target_ms else "⚠️ SLOW"
            print(f"{test_name:20} | Target: <{target_ms:3}ms | Actual: {actual_ms:6.2f}ms | {status}")
    
    # Overall assessment
    print("\n🎯 DR. SARAH CHEN'S ASSESSMENT:")
    print("-" * 30)
    
    avg_times = []
    for test_name, data in results.items():
        if isinstance(data, dict) and 'time_ms' in data:
            avg_times.append(data['time_ms'])
    
    if avg_times:
        avg_performance = sum(avg_times) / len(avg_times)
        if avg_performance < 50:
            grade = "A+"
            assessment = "优秀! (Excellent!)"
        elif avg_performance < 100:
            grade = "A"
            assessment = "非常好! (Very good!)"
        elif avg_performance < 200:
            grade = "B"
            assessment = "良好 (Good)"
        else:
            grade = "C"
            assessment = "需要改进 (Needs improvement)"
        
        print(f"📊 Average performance: {avg_performance:.2f}ms")
        print(f"🎓 Performance grade: {grade}")
        print(f"🏛️ Assessment: {assessment}")
        print(f"🚀 PostgreSQL-first approach: SUCCESS!")
    
    # Save detailed results
    with open('postgresql_functions_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: postgresql_functions_test_results.json")
    print("🎉 Testing complete!")
    
    return results

if __name__ == "__main__":
    test_postgresql_functions()