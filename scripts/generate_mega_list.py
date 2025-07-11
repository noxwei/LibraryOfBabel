import sqlite3

db_path = 'database/data/audiobook_ebook_tracker.db'

with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()
    
    query = """
    SELECT a.clean_title, a.clean_author
    FROM audiobooks a
    LEFT JOIN ebooks e ON a.album_id = e.audiobook_id
    WHERE e.audiobook_id IS NULL
    AND a.clean_title IS NOT NULL
    AND a.clean_title != ''
    AND a.clean_author IS NOT NULL
    AND a.clean_author != ''
    ORDER BY RANDOM()
    LIMIT 600
    """
    
    cursor.execute(query)
    random_books = cursor.fetchall()
    print(f'📚 Selected {len(random_books)} books (500 target + 100 buffer)')
    
    with open('mega_book_list.txt', 'w') as f:
        for clean_title, clean_author in random_books:
            author_first = clean_author.split()[0] if clean_author else ''
            search_query = f'{clean_title} {author_first}'.strip()
            f.write(search_query + '\n')
    
    print('✅ Created mega_book_list.txt')
    print('📖 First 10 books:')
    for i, (clean_title, clean_author) in enumerate(random_books[:10], 1):
        author_first = clean_author.split()[0] if clean_author else ''
        search_query = f'{clean_title} {author_first}'.strip()
        print(f'{i:2}. {search_query}')