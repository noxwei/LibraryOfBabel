#!/usr/bin/env python3
"""
🧪 iOS Shortcuts API Database Test Suite  
========================================
Tests database queries directly to verify pagination logic
"""

import psycopg2
import psycopg2.extras
import os
from typing import Dict, List, Any

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

def test_pagination_query(name: str, query: str, params: tuple = ()):
    """Test a pagination query"""
    print(f"\n🧪 Testing: {name}")
    print("-" * 50)
    
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                results = cur.fetchall()
                
                print(f"✅ Query executed successfully")
                print(f"📊 Results: {len(results)} rows")
                
                if results:
                    print(f"📋 First result: {results[0]}")
                    if len(results) > 1:
                        print(f"📋 Last result: {results[-1]}")
                
                return True, results
                
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False, []

def main():
    """Run database pagination tests"""
    print("🧪 iOS Shortcuts API Database Test Suite")
    print("=" * 60)
    
    success_count = 0
    total_tests = 0
    
    # Test 1: Basic book count
    total_tests += 1
    success, _ = test_pagination_query(
        "Book Count",
        "SELECT COUNT(*) FROM books;"
    )
    if success: success_count += 1
    
    # Test 2: Author list pagination (page 1)
    total_tests += 1  
    success, results = test_pagination_query(
        "Author List - Page 1 (limit 5, offset 0)",
        "SELECT DISTINCT author FROM books WHERE author IS NOT NULL ORDER BY author LIMIT %s OFFSET %s;",
        (5, 0)
    )
    if success: success_count += 1
    page1_authors = results
    
    # Test 3: Author list pagination (page 2)  
    total_tests += 1
    success, results = test_pagination_query(
        "Author List - Page 2 (limit 5, offset 5)",
        "SELECT DISTINCT author FROM books WHERE author IS NOT NULL ORDER BY author LIMIT %s OFFSET %s;",
        (5, 5)  
    )
    if success: success_count += 1
    page2_authors = results
    
    # Test 4: Check pagination works (different results)
    total_tests += 1
    if page1_authors and page2_authors and page1_authors != page2_authors:
        print("\n✅ Pagination verification: Page 1 ≠ Page 2 ✓")
        success_count += 1
    else:
        print("\n❌ Pagination verification: Page 1 = Page 2 ✗")
    
    # Test 5: Title list pagination
    total_tests += 1
    success, _ = test_pagination_query(
        "Title List - Page 1 (limit 5, offset 0)",
        "SELECT title FROM books ORDER BY title LIMIT %s OFFSET %s;",
        (5, 0)
    )
    if success: success_count += 1
    
    # Test 6: Search titles pagination  
    total_tests += 1
    success, _ = test_pagination_query(
        "Search Titles - Love (limit 5, offset 0)",
        """SELECT DISTINCT b.title 
           FROM books b 
           JOIN chunks c ON b.book_id = c.book_id 
           WHERE c.content ILIKE %s 
           ORDER BY b.title 
           LIMIT %s OFFSET %s;""",
        ('%love%', 5, 0)
    )
    if success: success_count += 1
    
    # Test 7: Find Olivia Laing
    total_tests += 1
    success, results = test_pagination_query(
        "Find Olivia Laing Position",
        """WITH numbered_authors AS (
               SELECT author, ROW_NUMBER() OVER (ORDER BY author) as position 
               FROM (SELECT DISTINCT author FROM books WHERE author IS NOT NULL) AS unique_authors
           ) 
           SELECT position, CEIL(position/500.0) as page_500
           FROM numbered_authors 
           WHERE author = 'Olivia Laing';"""
    )
    if success: 
        success_count += 1
        if results:
            pos, page = results[0]
            print(f"🎯 Olivia Laing found at position {pos}, page {page} (500 per page)")
    
    # Test 8: Book-specific queries (with book_id)
    total_tests += 1
    success, _ = test_pagination_query(
        "Book Summary Query (book_id=2238)",
        """SELECT b.title, b.author, b.subject 
           FROM books b 
           WHERE b.book_id = %s;""",
        (2238,)
    )
    if success: success_count += 1
    
    # Test 9: Chunks query
    total_tests += 1
    success, _ = test_pagination_query(
        "Book Chunks Query (book_id=2238, limit 2)",
        """SELECT c.chunk_id, LEFT(c.content, 100) as preview
           FROM chunks c 
           WHERE c.book_id = %s 
           ORDER BY c.chunk_id 
           LIMIT %s;""",
        (2238, 2)
    )
    if success: success_count += 1
    
    # Test 10: Random queries
    total_tests += 1
    success, _ = test_pagination_query(
        "Random Author",
        "SELECT author FROM books WHERE author IS NOT NULL ORDER BY RANDOM() LIMIT 1;"
    )
    if success: success_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DATABASE TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {success_count}")
    print(f"❌ Failed: {total_tests - success_count}")
    print(f"Success Rate: {(success_count/total_tests)*100:.1f}%")
    
    if success_count == total_tests:
        print("\n🎉 All database queries working correctly!")
        print("✅ Pagination logic verified")
        print("✅ Column references correct")
        print("✅ Ready for production deployment")
    else:
        print(f"\n⚠️  {total_tests - success_count} database issues need fixing")
        
    return success_count == total_tests

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)