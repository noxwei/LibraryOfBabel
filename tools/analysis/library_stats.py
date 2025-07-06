#!/usr/bin/env python3
"""
LibraryOfBabel Quick Stats Tool
"""
import psycopg2
import os

def get_stats():
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='knowledge_base', 
            user=os.getenv('USER'),
            port=5432
        )
        cur = conn.cursor()
        
        # Basic stats
        cur.execute('SELECT COUNT(*) FROM books')
        total_books = cur.fetchone()[0]
        
        cur.execute('SELECT COUNT(*) FROM chunks')
        total_chunks = cur.fetchone()[0]
        
        cur.execute('SELECT SUM(word_count) FROM chunks')
        total_words = cur.fetchone()[0] or 0
        
        print("📊 LibraryOfBabel Stats")
        print("=" * 30)
        print(f"📚 Total books: {total_books:,}")
        print(f"📝 Total chunks: {total_chunks:,}")
        print(f"📖 Total words: {total_words:,}")
        print(f"📄 Avg words/book: {total_words//total_books if total_books > 0 else 0:,}")
        
        # Top 5 longest books
        cur.execute("""
        SELECT b.title, b.author, SUM(c.word_count) as total_words 
        FROM books b 
        JOIN chunks c ON b.book_id = c.book_id 
        GROUP BY b.book_id, b.title, b.author 
        ORDER BY total_words DESC 
        LIMIT 5
        """)
        
        print(f"\n🏆 Top 5 Longest Books:")
        for i, (title, author, words) in enumerate(cur.fetchall(), 1):
            print(f"  {i}. {title} by {author} ({words:,} words)")
            
        # Philosophy books
        cur.execute("""
        SELECT title, author FROM books 
        WHERE author ILIKE '%foucault%' 
           OR author ILIKE '%deleuze%' 
           OR author ILIKE '%heidegger%' 
           OR author ILIKE '%fanon%'
           OR title ILIKE '%philosophy%'
        """)
        
        philosophy_books = cur.fetchall()
        if philosophy_books:
            print(f"\n🧠 Philosophy Collection ({len(philosophy_books)} books):")
            for title, author in philosophy_books:
                print(f"  📖 {title} by {author}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_stats()