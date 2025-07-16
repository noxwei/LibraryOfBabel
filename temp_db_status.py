#!/usr/bin/env python3
import psycopg2
import sys
sys.path.append('src')
from config.api_config import get_database_config

try:
    db_config = get_database_config()
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    
    # Get current genre status
    cur.execute("""
        SELECT 
            COUNT(*) as total_books,
            COUNT(CASE WHEN genre IS NOT NULL AND genre != '' AND TRIM(genre) != '' 
                  AND genre NOT IN ('none', 'book', 'cj5') 
                  THEN 1 END) as books_with_genre
        FROM books;
    """)
    
    total, with_genre = cur.fetchone()
    without_genre = total - with_genre
    print(f'=== DATABASE STATUS ===')
    print(f'Total Books: {total}')
    print(f'Books with Genre: {with_genre}')
    print(f'Books without Genre: {without_genre}')
    print(f'Genre Coverage: {(with_genre/total*100):.1f}%')
    
    # Get vector embedding status
    cur.execute("""
        SELECT COUNT(DISTINCT book_id) as books_with_embeddings
        FROM chunk_embeddings 
        WHERE embedding IS NOT NULL;
    """)
    
    embeddings_count = cur.fetchone()[0]
    print(f'Books with Vector Embeddings: {embeddings_count}')
    print(f'Embedding Coverage: {(embeddings_count/total*100):.1f}%')
    
    conn.close()
    
except Exception as e:
    print(f'Database error: {e}')