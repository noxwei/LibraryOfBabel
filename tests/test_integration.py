#!/usr/bin/env python3
"""
LibraryOfBabel Integration Test Suite
Comprehensive testing for Phase 2 completion validation
"""

import pytest
import requests
import psycopg2
import psycopg2.extras
import time
import json
import os
from typing import Dict, List
import subprocess

# Test configuration
API_BASE = "http://localhost:5000/api"
DB_CONFIG = {
    'host': 'localhost',
    'database': 'knowledge_base',
    'user': 'postgres',
    'port': 5432
}

class TestKnowledgeBaseIntegration:
    """Integration tests for the complete LibraryOfBabel system"""
    
    @classmethod
    def setup_class(cls):
        """Setup test environment"""
        cls.db_connection = None
        cls.api_running = False
        
        # Check if database is accessible
        try:
            cls.db_connection = psycopg2.connect(**DB_CONFIG)
            print("✅ Database connection established")
        except psycopg2.Error as e:
            print(f"❌ Database connection failed: {e}")
            pytest.skip("Database not available")
        
        # Check if API is running
        try:
            response = requests.get(f"{API_BASE}/health", timeout=5)
            if response.status_code == 200:
                cls.api_running = True
                print("✅ API service accessible")
        except requests.RequestException:
            print("⚠️  API service not running - some tests will be skipped")
    
    @classmethod
    def teardown_class(cls):
        """Cleanup after tests"""
        if cls.db_connection:
            cls.db_connection.close()
    
    def test_database_schema_exists(self):
        """Test that all required database tables exist"""
        cursor = self.db_connection.cursor()
        
        required_tables = ['books', 'chunks', 'authors', 'book_authors']
        
        for table in required_tables:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                )
            """, (table,))
            
            exists = cursor.fetchone()[0]
            assert exists, f"Required table '{table}' does not exist"
        
        print("✅ All required database tables exist")
    
    def test_database_has_data(self):
        """Test that database contains processed book data"""
        cursor = self.db_connection.cursor()
        
        # Check books table
        cursor.execute("SELECT COUNT(*) FROM books")
        book_count = cursor.fetchone()[0]
        assert book_count > 0, "No books found in database"
        
        # Check chunks table
        cursor.execute("SELECT COUNT(*) FROM chunks")
        chunk_count = cursor.fetchone()[0]
        assert chunk_count > 0, "No text chunks found in database"
        
        # Check data integrity
        cursor.execute("""
            SELECT COUNT(*) FROM chunks c
            LEFT JOIN books b ON c.book_id = b.book_id
            WHERE b.book_id IS NULL
        """)
        orphaned_chunks = cursor.fetchone()[0]
        assert orphaned_chunks == 0, f"Found {orphaned_chunks} orphaned chunks"
        
        print(f"✅ Database contains {book_count} books and {chunk_count} chunks")
    
    def test_full_text_search_performance(self):
        """Test full-text search performance and accuracy"""
        cursor = self.db_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Test queries with different complexity levels
        test_queries = [
            "technology",
            "artificial intelligence", 
            "human rights digital",
            "democracy and governance"
        ]
        
        for query in test_queries:
            start_time = time.time()
            
            cursor.execute("""
                SELECT COUNT(*) as total,
                       AVG(ts_rank(c.search_vector, plainto_tsquery('english', %s))) as avg_rank
                FROM chunks c
                WHERE c.search_vector @@ plainto_tsquery('english', %s)
            """, (query, query))
            
            result = cursor.fetchone()
            query_time = (time.time() - start_time) * 1000
            
            # Performance assertion: <100ms target
            assert query_time < 100, f"Query '{query}' took {query_time:.2f}ms (>100ms target)"
            
            # Relevance assertion: results should exist for common terms
            if query in ["technology", "human"]:  # Common terms
                assert result['total'] > 0, f"No results for common query '{query}'"
            
            print(f"✅ Query '{query}': {result['total']} results in {query_time:.2f}ms")
    
    def test_search_index_optimization(self):
        """Test that search indexes are properly created and used"""
        cursor = self.db_connection.cursor()
        
        # Check that GIN indexes exist for full-text search
        cursor.execute("""
            SELECT indexname, tablename 
            FROM pg_indexes 
            WHERE indexname LIKE '%search%' OR indexname LIKE '%gin%'
        """)
        
        indexes = cursor.fetchall()
        assert len(indexes) > 0, "No search indexes found"
        
        # Test that indexes are being used (check query plan)
        cursor.execute("""
            EXPLAIN (FORMAT JSON) 
            SELECT * FROM chunks 
            WHERE search_vector @@ plainto_tsquery('english', 'technology')
        """)
        
        plan = cursor.fetchone()[0]
        plan_text = json.dumps(plan)
        
        # Should use index scan, not sequential scan for large tables
        assert "Index Scan" in plan_text or "Bitmap" in plan_text, \
               "Query not using indexes efficiently"
        
        print(f"✅ Found {len(indexes)} search indexes, query plan optimized")
    
    @pytest.mark.skipif(not hasattr(setup_class, 'api_running') or not setup_class.api_running, 
                       reason="API service not available")
    def test_api_health_endpoint(self):
        """Test API health check functionality"""
        response = requests.get(f"{API_BASE}/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['status'] == 'healthy'
        assert data['database'] == 'connected'
        assert 'books_indexed' in data
        assert 'chunks_indexed' in data
        assert data['books_indexed'] > 0
        assert data['chunks_indexed'] > 0
        
        print(f"✅ API healthy: {data['books_indexed']} books, {data['chunks_indexed']} chunks")
    
    @pytest.mark.skipif(not hasattr(setup_class, 'api_running') or not setup_class.api_running,
                       reason="API service not available")
    def test_api_content_search(self):
        """Test API content search functionality"""
        test_queries = [
            {"query": "technology", "min_results": 1},
            {"query": "artificial intelligence", "min_results": 0},  # May not exist
            {"query": "human", "min_results": 1}
        ]
        
        for test_case in test_queries:
            response = requests.get(f"{API_BASE}/search", params={
                'q': test_case['query'],
                'type': 'content',
                'limit': 5
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Check response structure
            assert 'query_metadata' in data
            assert 'results' in data
            assert 'search_suggestions' in data
            
            # Check performance
            response_time = data['query_metadata']['response_time_ms']
            assert response_time < 100, f"API response too slow: {response_time}ms"
            
            # Check minimum results if specified
            if test_case['min_results'] > 0:
                assert len(data['results']) >= test_case['min_results'], \
                       f"Expected at least {test_case['min_results']} results for '{test_case['query']}'"
            
            print(f"✅ API search '{test_case['query']}': {len(data['results'])} results in {response_time}ms")
    
    @pytest.mark.skipif(not hasattr(setup_class, 'api_running') or not setup_class.api_running,
                       reason="API service not available")
    def test_api_search_types(self):
        """Test different API search types"""
        # Test author search
        response = requests.get(f"{API_BASE}/search", params={
            'q': 'Coleman',
            'type': 'author',
            'limit': 5
        })
        assert response.status_code == 200
        author_data = response.json()
        
        # Test title search  
        response = requests.get(f"{API_BASE}/search", params={
            'q': 'History',
            'type': 'title',
            'limit': 5
        })
        assert response.status_code == 200
        title_data = response.json()
        
        # Test cross-reference search
        response = requests.get(f"{API_BASE}/search", params={
            'q': 'technology,human',
            'type': 'cross_reference',
            'limit': 3
        })
        assert response.status_code == 200
        cross_ref_data = response.json()
        
        print("✅ All API search types functional")
    
    def test_data_integrity_and_quality(self):
        """Test data quality and integrity across the system"""
        cursor = self.db_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Test that all books have reasonable word counts
        cursor.execute("""
            SELECT title, word_count 
            FROM books 
            WHERE word_count < 1000 OR word_count > 500000
        """)
        
        outliers = cursor.fetchall()
        if outliers:
            print(f"⚠️  Found {len(outliers)} books with unusual word counts:")
            for book in outliers:
                print(f"   {book['title']}: {book['word_count']} words")
        
        # Test that chunks have reasonable sizes
        cursor.execute("""
            SELECT chunk_type, 
                   COUNT(*) as count,
                   AVG(word_count) as avg_words,
                   MIN(word_count) as min_words,
                   MAX(word_count) as max_words
            FROM chunks 
            GROUP BY chunk_type
        """)
        
        chunk_stats = cursor.fetchall()
        for stat in chunk_stats:
            print(f"✅ {stat['chunk_type']} chunks: {stat['count']} total, "
                  f"avg {stat['avg_words']:.0f} words ({stat['min_words']}-{stat['max_words']})")
        
        # Test that all chunks have content
        cursor.execute("SELECT COUNT(*) FROM chunks WHERE content IS NULL OR content = ''")
        empty_chunks = cursor.fetchone()[0]
        assert empty_chunks == 0, f"Found {empty_chunks} chunks with no content"
        
        print("✅ Data integrity validation passed")
    
    def test_system_scalability_metrics(self):
        """Test system performance under load"""
        cursor = self.db_connection.cursor()
        
        # Measure database size
        cursor.execute("""
            SELECT pg_size_pretty(pg_database_size('knowledge_base')) as db_size
        """)
        db_size = cursor.fetchone()[0]
        
        # Measure table sizes
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """)
        
        table_sizes = cursor.fetchall()
        
        print(f"✅ Database size: {db_size}")
        for table in table_sizes:
            print(f"   {table[1]}: {table[2]}")
        
        # Performance stress test - multiple concurrent searches
        if self.api_running:
            import threading
            import concurrent.futures
            
            def stress_search(query_id):
                try:
                    response = requests.get(f"{API_BASE}/search", params={
                        'q': f'test query {query_id}',
                        'type': 'content',
                        'limit': 5
                    }, timeout=5)
                    return response.status_code == 200, response.elapsed.total_seconds()
                except:
                    return False, None
            
            # Run 10 concurrent searches
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(stress_search, i) for i in range(10)]
                results = [future.result() for future in futures]
            
            successful = sum(1 for success, _ in results if success)
            avg_time = sum(time for success, time in results if success and time) / successful if successful > 0 else 0
            
            print(f"✅ Stress test: {successful}/10 concurrent requests successful, "
                  f"avg response time: {avg_time:.3f}s")
            
            assert successful >= 8, f"Only {successful}/10 concurrent requests succeeded"

def run_comprehensive_validation():
    """Run all integration tests and generate report"""
    print("🚀 LibraryOfBabel Phase 2 - Comprehensive Validation")
    print("=" * 60)
    
    # Run pytest with detailed output
    result = subprocess.run([
        'python', '-m', 'pytest', __file__, '-v', '--tb=short'
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED - SYSTEM VALIDATION COMPLETE")
        print("✅ Phase 2 ready for production deployment")
        return True
    else:
        print("\n" + "=" * 60)
        print("❌ SOME TESTS FAILED - REVIEW REQUIRED")
        print("🔧 System needs attention before production deployment")
        return False

if __name__ == "__main__":
    success = run_comprehensive_validation()
    exit(0 if success else 1)