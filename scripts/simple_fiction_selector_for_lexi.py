#!/usr/bin/env python3
"""
🎭 Simple Fiction Book Selector for Lexi
========================================

Dr. Sarah Chen's simplified, reliable PostgreSQL fiction book selector
Guaranteed to work with the LibraryOfBabel database for Lexi's TTS testing.
"""

import os
import json
import psycopg2
import psycopg2.extras
from datetime import datetime

def get_fiction_books_for_lexi(count=15):
    """Get fiction books using simple, reliable query"""
    
    print(f"🎭 Dr. Sarah Chen's Fiction Selector for Lexi")
    print(f"🔍 Selecting {count} fiction books for TTS testing...")
    
    # Database connection
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='knowledge_base',
            user='weixiangzhang',
            port=5432
        )
        print("✅ Database connected")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return []
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Simple, reliable fiction selection query
            cur.execute("""
                SELECT 
                    b.book_id,
                    b.title,
                    b.author,
                    b.genre,
                    b.word_count,
                    COALESCE(b.description, 'No description available') as description,
                    COALESCE(b.publication_year, 0) as publication_year
                FROM books b
                WHERE 
                    (b.genre ILIKE '%fiction%' OR b.genre = 'Fiction')
                    AND b.word_count >= 40000
                    AND b.title IS NOT NULL 
                    AND b.author IS NOT NULL
                    AND b.author != 'Unknown'
                ORDER BY b.word_count DESC
                LIMIT %s
            """, (count,))
            
            books = cur.fetchall()
            
            if not books:
                print("❌ No fiction books found")
                return []
            
            print(f"✅ Found {len(books)} fiction books")
            
            # Convert to simple list
            fiction_list = []
            for book in books:
                # Calculate TTS estimates
                word_count = book['word_count']
                estimated_hours = round(word_count / 250 / 60, 1)  # 250 words/minute
                
                if word_count <= 80000:
                    length_category = "Short (2-3 hours)"
                elif word_count <= 120000:
                    length_category = "Medium (3-5 hours)"
                elif word_count <= 200000:
                    length_category = "Long (5-8 hours)"
                else:
                    length_category = "Epic (8+ hours)"
                
                fiction_book = {
                    'book_id': book['book_id'],
                    'title': book['title'],
                    'author': book['author'],
                    'genre': book['genre'],
                    'word_count': word_count,
                    'estimated_hours': estimated_hours,
                    'length_category': length_category,
                    'description': book['description'][:200] + '...' if len(book['description']) > 200 else book['description'],
                    'publication_year': book['publication_year']
                }
                fiction_list.append(fiction_book)
            
            return fiction_list
            
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return []
    finally:
        conn.close()

def main():
    """Main execution"""
    print("🎤 LibraryOfBabel Simple Fiction Selector for Lexi")
    print("=" * 60)
    
    # Get fiction books
    books = get_fiction_books_for_lexi(15)
    
    if not books:
        print("❌ No books selected. Check database connection.")
        return
    
    # Show results
    print(f"\n📚 Selected {len(books)} Fiction Books for TTS Testing:")
    print("=" * 60)
    
    total_words = 0
    for i, book in enumerate(books, 1):
        total_words += book['word_count']
        print(f"{i:2}. '{book['title']}' by {book['author']}")
        print(f"     📊 {book['word_count']:,} words | {book['length_category']} | {book['genre']}")
        if i <= 3:  # Show description for first 3
            print(f"     📝 {book['description']}")
        print()
    
    # Summary statistics
    total_hours = round(total_words / 250 / 60, 1)
    avg_words = round(total_words / len(books))
    
    print("📊 TTS Testing Summary:")
    print(f"   📚 Total books: {len(books)}")
    print(f"   📝 Total words: {total_words:,}")
    print(f"   🎵 Estimated audio: {total_hours} hours")
    print(f"   📊 Average words/book: {avg_words:,}")
    
    # Export results
    report = {
        "selection_date": datetime.now().isoformat(),
        "total_books": len(books),
        "total_words": total_words,
        "estimated_hours": total_hours,
        "selected_books": books
    }
    
    output_file = f"/tmp/lexi_fiction_selection_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    try:
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n💾 Results exported to: {output_file}")
    except Exception as e:
        print(f"⚠️ Export failed: {e}")
    
    print(f"\n🎭 Fiction books ready for Lexi's TTS testing!")
    print(f"🚀 Use these {len(books)} books to test voice synthesis across different genres and lengths")

if __name__ == "__main__":
    main()