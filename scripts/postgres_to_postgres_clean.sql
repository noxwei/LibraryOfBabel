-- 🧠 Dr. Chen's PostgreSQL-to-PostgreSQL Clean Transfer
-- Direct INSERT INTO ... SELECT FROM across databases

\echo '🧠 DR. CHEN: PostgreSQL-to-PostgreSQL Clean Transfer'
\echo '=================================================='

-- First, ensure we're in the target database
\c knowledge_with_embeds

-- Insert books with embeddings directly
\echo 'Copying books with embeddings...'
INSERT INTO books 
SELECT * FROM dblink('host=localhost dbname=knowledge_base user=weixiangzhang', 
    'SELECT * FROM books WHERE book_id IN (SELECT DISTINCT book_id FROM chunk_embeddings)')
AS remote_books(
    book_id int, title varchar(500), author varchar(255), file_path text, 
    file_size bigint, created_at timestamp, updated_at timestamp, 
    word_count int, chapter_count int, isbn varchar(20), publisher varchar(255),
    publication_year int, genre varchar(100), language varchar(10), 
    description text, tags text[]
);

-- Insert readable chunks only (no sentences)
\echo 'Copying readable chunks (chapters/sections/paragraphs)...'
INSERT INTO chunks
SELECT * FROM dblink('host=localhost dbname=knowledge_base user=weixiangzhang',
    'SELECT chunk_id, book_id, chunk_type, title, content, word_count, 
            character_count, chapter_number, section_number, paragraph_number,
            start_position, end_position, parent_chunk_id, search_vector, 
            created_at, embedding_array, embedding_vector
     FROM chunks 
     WHERE book_id IN (SELECT DISTINCT book_id FROM chunk_embeddings)
     AND chunk_type IN (''chapter'', ''section'', ''paragraph'')
     AND content IS NOT NULL')
AS remote_chunks(
    chunk_id varchar(255), book_id int, chunk_type varchar(50), title varchar(500),
    content text, word_count int, character_count int, chapter_number int,
    section_number int, paragraph_number int, start_position int, end_position int,
    parent_chunk_id varchar(255), search_vector tsvector, created_at timestamp,
    embedding_array double precision[], embedding_vector vector(768)
);

-- Insert all embeddings
\echo 'Copying embeddings...'
INSERT INTO chunk_embeddings
SELECT * FROM dblink('host=localhost dbname=knowledge_base user=weixiangzhang',
    'SELECT * FROM chunk_embeddings')
AS remote_embeddings(
    embedding_id int, chunk_id varchar(255), book_id int, embedding jsonb,
    embedding_model varchar(100), embedding_dimension int, created_at timestamp,
    content_type varchar(50), routing_reason text, confidence_score numeric(3,2),
    embedding_vector vector(768), embedding_vector_bge vector(1024),
    embedding_vector_granite vector(384), embedding_vector_mxbai vector(1024)
);

-- Verify the clean database
\echo 'Verification:'
SELECT 
    'books' as table_name, COUNT(*) as count FROM books UNION ALL
SELECT 'chunks', COUNT(*) FROM chunks UNION ALL
SELECT 'chunk_embeddings', COUNT(*) FROM chunk_embeddings
ORDER BY table_name;

\echo ''
\echo '✅ Clean embedded database ready!'
\echo '📚 Only books with embeddings'  
\echo '📖 Only readable chunks (no sentences)'
\echo '🧠 All embeddings preserved'