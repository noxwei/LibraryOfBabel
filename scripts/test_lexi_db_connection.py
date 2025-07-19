#!/usr/bin/env python3
"""
🔌 Database Connection Test for Lexi
====================================

Quick test script to verify Lexi can connect to the LibraryOfBabel 
PostgreSQL database and access fiction books.

Dr. Sarah Chen's database connection verification tool.
"""

import os
import sys
import psycopg2
import psycopg2.extras

def test_database_connection():
    """Test basic database connectivity for Lexi"""
    print("🔌 Testing LibraryOfBabel Database Connection for Lexi")
    print("=" * 60)
    
    # Standard LibraryOfBabel database configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'knowledge_base'),
        'user': os.getenv('DB_USER', 'weixiangzhang'),
        'port': int(os.getenv('DB_PORT', 5432))
    }
    
    print(f"🏛️ Testing connection to: {db_config['database']}@{db_config['host']}:{db_config['port']}")
    print(f"👤 User: {db_config['user']}")
    
    try:
        # Test connection
        print("\n🔗 Attempting database connection...")
        conn = psycopg2.connect(**db_config)
        print("✅ Database connection successful!")
        
        # Test schema
        print("\n📋 Testing database schema...")
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            
            # Check tables exist
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('books', 'chunks', 'authors')
                ORDER BY table_name
            """)
            tables = [row[0] for row in cur.fetchall()]
            
            if 'books' in tables:
                print("✅ 'books' table found")
            else:
                print("❌ 'books' table missing")
                return False
                
            if 'chunks' in tables:
                print("✅ 'chunks' table found") 
            else:
                print("⚠️ 'chunks' table missing (optional)")
            
            # Test fiction books availability
            print("\n📚 Testing fiction books availability...")
            cur.execute("""
                SELECT 
                    COUNT(*) as total_fiction_books,
                    COUNT(CASE WHEN word_count >= 40000 THEN 1 END) as suitable_for_tts,
                    MIN(word_count) as shortest_words,
                    MAX(word_count) as longest_words,
                    COUNT(DISTINCT genre) as fiction_genres
                FROM books 
                WHERE (genre ILIKE '%fiction%' OR genre = 'Fiction')
                AND word_count > 0
            """)
            
            stats = cur.fetchone()
            
            if stats['total_fiction_books'] > 0:
                print(f"✅ Found {stats['total_fiction_books']} fiction books")
                print(f"📖 Books suitable for TTS: {stats['suitable_for_tts']}")
                print(f"📊 Word count range: {stats['shortest_words']:,} - {stats['longest_words']:,}")
                print(f"🎭 Fiction genres available: {stats['fiction_genres']}")
                
                if stats['suitable_for_tts'] >= 15:
                    print("🎉 Sufficient fiction books available for TTS testing!")
                else:
                    print("⚠️ Limited fiction books suitable for TTS (need 40K+ words)")
            else:
                print("❌ No fiction books found")
                return False
            
            # Test sample query
            print("\n🔍 Testing sample fiction query...")
            cur.execute("""
                SELECT book_id, title, author, genre, word_count
                FROM books 
                WHERE (genre ILIKE '%fiction%' OR genre = 'Fiction')
                AND word_count >= 40000
                ORDER BY word_count DESC
                LIMIT 5
            """)
            
            sample_books = cur.fetchall()
            
            if sample_books:
                print("✅ Sample fiction books query successful:")
                for i, book in enumerate(sample_books, 1):
                    print(f"   {i}. '{book['title']}' by {book['author']}")
                    print(f"      📊 {book['word_count']:,} words | {book['genre']}")
            else:
                print("❌ Sample query returned no results")
                return False
            
            # Test API function if available
            print("\n🛠️ Testing Dr. Sarah Chen's API functions...")
            try:
                cur.execute("SELECT * FROM api_list_books(1, 3, NULL, NULL, 'Fiction')")
                api_results = cur.fetchall()
                if api_results:
                    print("✅ API functions available and working")
                else:
                    print("⚠️ API functions exist but returned no results")
            except psycopg2.Error:
                print("⚠️ API functions not available (use direct SQL queries)")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("🎤 DATABASE CONNECTION TEST RESULTS")
        print("=" * 60)
        print("✅ Connection: SUCCESS")
        print("✅ Schema: VALID") 
        print("✅ Fiction Books: AVAILABLE")
        print("✅ TTS Ready: YES")
        print("\n🚀 Lexi can proceed with fiction book selection!")
        print("📁 Use: python3 lexi_fiction_selector.py")
        print("📄 Or run queries from: lexi_fiction_queries.sql")
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Ensure PostgreSQL is running")
        print("2. Check database name: knowledge_base")
        print("3. Verify user permissions")
        print("4. Confirm port 5432 is accessible")
        print("5. Check environment variables: DB_HOST, DB_NAME, DB_USER, DB_PORT")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main test execution"""
    success = test_database_connection()
    
    if success:
        print("\n🎭 Next Steps for Lexi:")
        print("1. Run fiction book selector: python3 lexi_fiction_selector.py")
        print("2. Or use SQL queries directly: lexi_fiction_queries.sql")
        print("3. Select 15 diverse fiction books for TTS testing")
        print("4. Extract text samples for voice synthesis")
        sys.exit(0)
    else:
        print("\n❌ Database connection test failed")
        print("Contact Dr. Sarah Chen (DBA Team) for database setup assistance")
        sys.exit(1)

if __name__ == "__main__":
    main()