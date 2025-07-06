#!/usr/bin/env python3
"""
Simple Search Tool for LibraryOfBabel
Quick text search without vector embeddings
"""
import psycopg2
import os
import sys
import json
from datetime import datetime

def search_books(query, limit=5):
    """Search books using basic PostgreSQL text search"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='knowledge_base', 
            user=os.getenv('USER'),
            port=5432
        )
        cur = conn.cursor()
        
        # Search in content with context
        search_sql = """
        SELECT 
            b.title,
            b.author,
            c.chunk_type,
            LEFT(c.content, 400) as snippet,
            ts_rank_cd(to_tsvector('english', c.content), plainto_tsquery('english', %s)) as rank
        FROM chunks c 
        JOIN books b ON c.book_id = b.book_id 
        WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', %s)
        ORDER BY rank DESC, c.word_count DESC
        LIMIT %s
        """
        
        cur.execute(search_sql, (query, query, limit))
        results = cur.fetchall()
        
        print(f"\n🔍 Search Results for: '{query}'")
        print("=" * 60)
        
        if not results:
            print("❌ No results found. Try different keywords.")
            return
            
        for i, (title, author, chunk_type, snippet, rank) in enumerate(results, 1):
            print(f"\n📖 {i}. {title}")
            print(f"👤 Author: {author}")
            if chunk_type:
                print(f"📄 Type: {chunk_type}")
            print(f"📝 Excerpt: {snippet.strip()}...")
            print(f"⭐ Relevance: {rank:.3f}")
            print("-" * 50)
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Search error: {e}")

def list_books():
    """List all available books"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='knowledge_base', 
            user=os.getenv('USER'),
            port=5432
        )
        cur = conn.cursor()
        
        cur.execute("""
        SELECT b.title, b.author, COUNT(c.chunk_id) as sections
        FROM books b
        LEFT JOIN chunks c ON b.book_id = c.book_id
        GROUP BY b.book_id, b.title, b.author
        ORDER BY b.title
        """)
        
        results = cur.fetchall()
        print(f"\n📚 Your Library ({len(results)} books):")
        print("=" * 60)
        
        for title, author, sections in results:
            print(f"📖 {title} by {author} ({sections} sections)")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    if len(sys.argv) < 2:
        print("🔍 LibraryOfBabel Simple Search")
        print("\nUsage:")
        print("  python3 simple_search.py 'search term'     # Search books")
        print("  python3 simple_search.py --list            # List all books")
        print("\nExamples:")
        print("  python3 simple_search.py 'power'")
        print("  python3 simple_search.py 'surveillance'")
        print("  python3 simple_search.py 'consciousness'")
        return
        
    if sys.argv[1] == '--list':
        list_books()
    else:
        query = sys.argv[1]
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        search_books(query, limit)

if __name__ == "__main__":
    main()