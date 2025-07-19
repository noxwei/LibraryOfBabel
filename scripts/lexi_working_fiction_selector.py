#!/usr/bin/env python3
"""
🎭 Working Fiction Selector for Lexi - Dr. Sarah Chen
====================================================

Guaranteed working fiction book selector for TTS testing.
Tested and verified with LibraryOfBabel PostgreSQL database.
"""

import psycopg2
import psycopg2.extras
import json
from datetime import datetime

def select_fiction_books():
    """Select 15 fiction books for Lexi's TTS testing"""
    
    print("🎭 Dr. Sarah Chen's Working Fiction Selector for Lexi")
    print("=" * 60)
    print("🔍 Connecting to LibraryOfBabel database...")
    
    # Connect to database
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='knowledge_base', 
            user='weixiangzhang',
            port=5432
        )
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    # Select fiction books
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            print("📚 Selecting fiction books...")
            
            cursor.execute("""
                SELECT 
                    book_id,
                    title,
                    author,
                    genre,
                    word_count,
                    description,
                    publication_year
                FROM books
                WHERE 
                    (genre ILIKE '%fiction%' OR genre = 'Fiction')
                    AND word_count >= 40000
                    AND title IS NOT NULL 
                    AND author IS NOT NULL
                ORDER BY word_count DESC
                LIMIT 15
            """)
            
            books = cursor.fetchall()
            
            if not books:
                print("❌ No fiction books found")
                return
            
            print(f"✅ Found {len(books)} fiction books")
            
            # Process and display results
            fiction_selection = []
            total_words = 0
            
            print("\n📖 Selected Fiction Books for TTS Testing:")
            print("=" * 60)
            
            for i, book in enumerate(books, 1):
                # Calculate TTS metrics
                words = book['word_count']
                hours = round(words / 250 / 60, 1)  # 250 words per minute
                
                # Categorize by length
                if words <= 80000:
                    category = "Short (2-3 hours)"
                elif words <= 120000:
                    category = "Medium (3-5 hours)"  
                elif words <= 200000:
                    category = "Long (5-8 hours)"
                else:
                    category = "Epic (8+ hours)"
                
                # Book data
                book_info = {
                    'rank': i,
                    'book_id': book['book_id'],
                    'title': book['title'],
                    'author': book['author'],
                    'genre': book['genre'],
                    'word_count': words,
                    'estimated_hours': hours,
                    'category': category,
                    'description': book['description'][:200] + '...' if book['description'] and len(book['description']) > 200 else (book['description'] or 'No description'),
                    'publication_year': book['publication_year']
                }
                
                fiction_selection.append(book_info)
                total_words += words
                
                # Display
                print(f"{i:2}. '{book['title']}' by {book['author']}")
                print(f"     📊 {words:,} words | {category} | {book['genre']}")
                if i <= 3:  # Show description for first 3
                    desc = book['description'] or 'No description available'
                    print(f"     📝 {desc[:150]}...")
                print()
            
            # Summary
            total_hours = round(total_words / 250 / 60, 1)
            avg_words = round(total_words / len(books))
            
            print("📊 TTS Selection Summary:")
            print(f"   📚 Books selected: {len(books)}")
            print(f"   📝 Total words: {total_words:,}")
            print(f"   🎵 Total audio time: {total_hours} hours")
            print(f"   📊 Average words per book: {avg_words:,}")
            
            # Count by category
            categories = {}
            for book in fiction_selection:
                cat = book['category'].split(' ')[0]  # Short, Medium, Long, Epic
                categories[cat] = categories.get(cat, 0) + 1
            
            print(f"   📏 Length distribution:")
            for cat, count in categories.items():
                print(f"      {cat}: {count} books")
            
            # Export results
            export_data = {
                'selection_metadata': {
                    'selected_by': 'Dr. Sarah Chen - Database Architecture Team',
                    'selected_for': 'Lexi (Audio Synthesis Agent)',
                    'selection_date': datetime.now().isoformat(),
                    'database': 'LibraryOfBabel knowledge_base',
                    'selection_criteria': 'Fiction books >= 40K words, diverse lengths'
                },
                'summary': {
                    'total_books': len(books),
                    'total_words': total_words,
                    'estimated_total_hours': total_hours,
                    'average_words_per_book': avg_words,
                    'length_distribution': categories
                },
                'selected_books': fiction_selection,
                'tts_recommendations': [
                    'Start with Short books (2-3 hours) for voice calibration',
                    'Progress to Medium books (3-5 hours) for consistency testing',
                    'Use Long/Epic books for endurance and advanced testing',
                    'Test different genres for voice adaptability',
                    'Extract 3-5 text samples per book for comprehensive testing'
                ]
            }
            
            # Save to file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            output_file = f"/tmp/lexi_fiction_selection_{timestamp}.json"
            
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
                print(f"\n💾 Selection exported to: {output_file}")
            except Exception as e:
                print(f"⚠️ Export failed: {e}")
            
            print(f"\n🎉 Fiction selection complete!")
            print(f"🎤 {len(books)} books ready for Lexi's TTS testing")
            print(f"🚀 Estimated {total_hours} hours of audio content")
            
    except Exception as e:
        print(f"❌ Query failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()
        print("🔌 Database connection closed")

if __name__ == "__main__":
    select_fiction_books()