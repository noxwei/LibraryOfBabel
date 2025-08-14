-- 🚀 NUCLEAR MIGRATION FIXED: Correct column mappings
-- Copy only readable chunks (NO SENTENCES) with proper schema matching

\echo '🚀 NUCLEAR MIGRATION (SCHEMA FIXED)'
\echo '=================================='

\c knowledge_base_clean

\echo '📚 PHASE 1: Books migration with correct columns...'
INSERT INTO books (book_id, title, author, author_id, publisher, publication_date, 
                  publication_year, language, isbn, description, genre, word_count, 
                  file_path, source_location, import_source, processed_date, created_at)
SELECT book_id, title, author, author_id, publisher, publication_date, 
       publication_year, language, isbn, description, genre, word_count, 
       file_path, source_location, import_source, processed_date, created_at
FROM dblink('host=localhost dbname=knowledge_base user=weixiangzhang',
    'SELECT book_id, title, author, author_id, publisher, publication_date, 
            publication_year, language, isbn, description, genre, word_count, 
            file_path, source_location, import_source, processed_date, created_at
     FROM books ORDER BY book_id')
AS remote_books(
    book_id bigint, title varchar(500), author varchar(255), author_id int, 
    publisher varchar(255), publication_date varchar(100), publication_year int, 
    language varchar(50), isbn varchar(50), description text, genre varchar(100), 
    word_count int, file_path varchar(1000), source_location varchar(1000), 
    import_source varchar(100), processed_date timestamp, created_at timestamp
);

\echo '📖 PHASE 2: Readable chunks ONLY (84% reduction)...'
INSERT INTO chunks (chunk_id, book_id, chunk_type, title, content, word_count, 
                   character_count, chapter_number, section_number, paragraph_number, 
                   search_vector, created_at)
SELECT chunk_id, book_id, chunk_type, title, content, word_count, 
       character_count, chapter_number, section_number, paragraph_number, 
       search_vector, created_at
FROM dblink('host=localhost dbname=knowledge_base user=weixiangzhang',
    'SELECT chunk_id, book_id, chunk_type, title, content, word_count, 
            character_count, chapter_number, section_number, paragraph_number,
            search_vector, created_at
     FROM chunks 
     WHERE chunk_type IN (''chapter'', ''section'', ''paragraph'')
     AND content IS NOT NULL
     ORDER BY book_id, chunk_id LIMIT 100000')
AS remote_chunks(
    chunk_id varchar(255), book_id int, chunk_type varchar(50), title varchar(500),
    content text, word_count int, character_count int, chapter_number int,
    section_number int, paragraph_number int, search_vector tsvector, created_at timestamp
);

\echo '📊 Progress check (first 100K chunks):'
SELECT 
    'books' as table_name, COUNT(*) as count FROM books UNION ALL
SELECT 'chunks', COUNT(*) FROM chunks
ORDER BY table_name;

\echo ''
\echo '✅ First batch complete - continue in batches!'