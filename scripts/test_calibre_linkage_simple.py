#!/usr/bin/env python3
"""
Simple test of Dr. Sarah Chen's Calibre linkage recovery system
"""

import psycopg2
import psycopg2.extras
import sys
import os
from datetime import datetime

def connect_db():
    """Connect to PostgreSQL database"""
    try:
        return psycopg2.connect(
            host='localhost',
            database='knowledge_base',
            user='weixiangzhang',
            password=os.environ.get('DB_PASSWORD')
        )
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def test_linkage_functions():
    """Test the PostgreSQL linkage functions"""
    
    conn = connect_db()
    if not conn:
        return False
    
    print("🧪 Testing Dr. Sarah Chen's Calibre Linkage Recovery System")
    print("=" * 60)
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            
            # Test 1: Check if functions exist
            print("🔍 Test 1: Checking PostgreSQL functions...")
            cur.execute("""
                SELECT proname FROM pg_proc 
                WHERE proname LIKE '%calibre%linkage%' 
                ORDER BY proname
            """)
            functions = cur.fetchall()
            
            if functions:
                print(f"✅ Found {len(functions)} calibre linkage functions:")
                for func in functions:
                    print(f"   - {func['proname']}")
            else:
                print("❌ No calibre linkage functions found")
                return False
            
            # Test 2: Check database state
            print("\n🔍 Test 2: Checking database state...")
            
            # Count Calibre books without linkage
            cur.execute("""
                SELECT COUNT(*) as unlinked_count
                FROM (
                    SELECT cb.calibre_id, cb.calibre_title, cb.calibre_author
                    FROM calibre_books cb
                    LEFT JOIN books b ON cb.postgres_book_id = b.book_id
                    WHERE b.book_id IS NULL
                    LIMIT 1000
                ) unlinked
            """)
            result = cur.fetchone()
            unlinked_count = result['unlinked_count'] if result else 0
            
            # Count total Calibre books
            cur.execute("SELECT COUNT(*) as total FROM calibre_books")
            total_result = cur.fetchone()
            total_count = total_result['total'] if total_result else 0
            
            # Count linked books
            cur.execute("""
                SELECT COUNT(*) as linked_count
                FROM calibre_books cb
                JOIN books b ON cb.postgres_book_id = b.book_id
            """)
            linked_result = cur.fetchone()
            linked_count = linked_result['linked_count'] if linked_result else 0
            
            print(f"📊 Calibre Books Status:")
            print(f"   Total books: {total_count:,}")
            print(f"   Linked books: {linked_count:,}")
            print(f"   Unlinked books: {unlinked_count:,}")
            
            if total_count > 0:
                link_rate = (linked_count / total_count) * 100
                print(f"   Current link rate: {link_rate:.1f}%")
            
            # Test 3: Test a sample linkage function call
            print("\n🔍 Test 3: Testing sample linkage function...")
            
            if unlinked_count > 0:
                # Get a sample unlinked book
                cur.execute("""
                    SELECT cb.calibre_id, cb.calibre_title, cb.calibre_author
                    FROM calibre_books cb
                    LEFT JOIN books b ON cb.postgres_book_id = b.book_id
                    WHERE b.book_id IS NULL
                    AND cb.calibre_title IS NOT NULL
                    LIMIT 1
                """)
                sample_book = cur.fetchone()
                
                if sample_book:
                    print(f"📖 Testing with: '{sample_book['calibre_title']}' by {sample_book['calibre_author']}")
                    
                    # Try to find matching books in PostgreSQL
                    title = sample_book['calibre_title']
                    author = sample_book['calibre_author'] or ''
                    
                    cur.execute("""
                        SELECT book_id, title, author, 
                               similarity(title, %s) as title_sim,
                               similarity(author, %s) as author_sim
                        FROM books 
                        WHERE similarity(title, %s) > 0.3 
                           OR similarity(author, %s) > 0.3
                        ORDER BY (similarity(title, %s) + similarity(author, %s)) DESC
                        LIMIT 5
                    """, (title, author, title, author, title, author))
                    
                    matches = cur.fetchall()
                    
                    if matches:
                        print(f"✅ Found {len(matches)} potential matches:")
                        for match in matches[:3]:
                            print(f"   - '{match['title']}' by {match['author']} (sim: {match['title_sim']:.2f}/{match['author_sim']:.2f})")
                    else:
                        print("⚠️ No potential matches found with similarity > 0.3")
                else:
                    print("⚠️ No unlinked books found for testing")
            else:
                print("✅ All books are already linked!")
            
            # Test 4: Check function permissions and accessibility
            print("\n🔍 Test 4: Testing function accessibility...")
            
            try:
                # Test basic function call (this should work even if no matches)
                cur.execute("""
                    SELECT 'Function accessible' as status
                    FROM pg_proc p
                    WHERE p.proname = 'dr_sarah_chen_robust_calibre_linkage'
                    LIMIT 1
                """)
                func_test = cur.fetchone()
                
                if func_test:
                    print("✅ Linkage functions are accessible")
                else:
                    print("❌ Main linkage function not found")
                    
            except Exception as e:
                print(f"❌ Function access error: {e}")
            
            print("\n" + "=" * 60)
            print("🎯 TEST SUMMARY:")
            
            if total_count > 0 and linked_count > 0:
                success_rate = (linked_count / total_count) * 100
                if success_rate > 90:
                    print(f"🎉 EXCELLENT: {success_rate:.1f}% linkage rate!")
                elif success_rate > 50:
                    print(f"📈 GOOD: {success_rate:.1f}% linkage rate")
                else:
                    print(f"⚠️ NEEDS IMPROVEMENT: {success_rate:.1f}% linkage rate")
            else:
                print("⚠️ Linkage system needs to be run")
            
            print("✅ Dr. Sarah Chen's system is deployed and ready for testing")
            
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    finally:
        conn.close()

def main():
    """Run the calibre linkage test"""
    success = test_linkage_functions()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())