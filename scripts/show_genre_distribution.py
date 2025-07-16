#!/usr/bin/env python3
"""
Show LibraryOfBabel Genre Classification Results
===============================================
"""
import sys
sys.path.append('/Users/weixiangzhang/Local Dev/LibraryOfBabel')
from config.api_config import get_database_config
import psycopg2
from psycopg2.extras import RealDictCursor

def show_genre_distribution():
    config = get_database_config()
    conn = psycopg2.connect(**config, cursor_factory=RealDictCursor)
    cur = conn.cursor()

    print('📚 LIBRARYOFBABEL GENRE CLASSIFICATION RESULTS')
    print('=' * 60)

    # Get total books
    cur.execute('SELECT COUNT(*) FROM books')
    result = cur.fetchone()
    total_books = result['count'] if 'count' in result else list(result.values())[0]

    # Get genre distribution
    cur.execute("""
        SELECT genre, COUNT(*) as book_count
        FROM books 
        WHERE genre IS NOT NULL AND genre != %s
        GROUP BY genre
        ORDER BY book_count DESC
    """, ('',))

    results = cur.fetchall()
    total_classified = sum(row['book_count'] for row in results)

    print(f'📊 Total Books: {total_books:,}')
    print(f'✅ Classified: {total_classified:,} ({(total_classified/total_books)*100:.1f}%)')

    # Check for unclassified
    cur.execute('SELECT COUNT(*) FROM books WHERE genre IS NULL OR genre = %s', ('',))
    result = cur.fetchone()
    unclassified = result['count'] if 'count' in result else list(result.values())[0]
    print(f'❌ Unclassified: {unclassified:,}')
    print()

    print('🏷️  GENRE DISTRIBUTION:')
    print('-' * 60)
    
    for i, row in enumerate(results, 1):
        percentage = (row['book_count'] / total_classified) * 100
        bar_length = int(percentage / 2)  # Scale for display
        bar = '█' * bar_length + '░' * (25 - bar_length)
        print(f'{i:2d}. {row["genre"]:30} {row["book_count"]:4d} │{bar}│ {percentage:4.1f}%')

    # Show some recent classifications
    print('\n📖 RECENT CLASSIFICATIONS (Sample):')
    print('-' * 60)
    cur.execute("""
        SELECT title, author, genre
        FROM books 
        WHERE genre IS NOT NULL AND genre != %s
        ORDER BY book_id DESC
        LIMIT 10
    """, ('',))
    
    recent = cur.fetchall()
    for book in recent:
        title = book['title'][:35] + '...' if len(book['title']) > 35 else book['title']
        author = book['author'][:20] + '...' if len(book['author']) > 20 else book['author']
        print(f'• "{title}" by {author}')
        print(f'  └─ Genre: {book["genre"]}')

    # Show vector embedding status
    print('\n🧮 VECTOR EMBEDDING STATUS:')
    print('-' * 60)
    cur.execute("""
        SELECT 
            embedding_model,
            COUNT(*) as vector_count,
            COUNT(DISTINCT book_id) as unique_books
        FROM chunk_embeddings 
        WHERE embedding_vector IS NOT NULL
        GROUP BY embedding_model
        ORDER BY vector_count DESC
    """)
    
    vectors = cur.fetchall()
    for row in vectors:
        print(f'• {row["embedding_model"]}: {row["vector_count"]:,} vectors across {row["unique_books"]:,} books')

    conn.close()

if __name__ == '__main__':
    show_genre_distribution()