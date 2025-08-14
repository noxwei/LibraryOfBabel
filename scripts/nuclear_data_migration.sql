-- 🚀 NUCLEAR DATA MIGRATION: Copy only readable chunks (NO SENTENCES)
-- Target: 84% reduction (15M → 2.4M chunks)

\echo '🚀 NUCLEAR DATA MIGRATION: SELECTIVE COPY'
\echo '========================================='
\echo 'Source: knowledge_base (121GB, 14.9M chunks)'
\echo 'Target: knowledge_base_clean (readable only)'
\echo ''

-- Connect to clean database
\c knowledge_base_clean

\echo '📚 PHASE 1: Copying all books...'
INSERT INTO books 
SELECT * FROM dblink('host=localhost dbname=knowledge_base user=weixiangzhang',
    'SELECT book_id, title, author, file_path, file_size, created_at, updated_at, 
            word_count, chapter_count, isbn, publisher, publication_year, genre, 
            language, description, tags, calibre_id, calibre_path, calibre_library_path,
            file_hash, file_sync_status, metadata
     FROM books ORDER BY book_id')
AS remote_books(
    book_id int, title varchar(500), author varchar(255), file_path text, 
    file_size bigint, created_at timestamp, updated_at timestamp, 
    word_count int, chapter_count int, isbn varchar(20), publisher varchar(255),
    publication_year int, genre varchar(100), language varchar(10), 
    description text, tags text[], calibre_id int, calibre_path text, 
    calibre_library_path text, file_hash varchar(64), file_sync_status varchar(20),
    metadata jsonb
);

\echo '📖 PHASE 2: Copying readable chunks ONLY (no sentences)...'
INSERT INTO chunks (chunk_id, book_id, chunk_type, title, content, word_count, character_count,
                   chapter_number, section_number, paragraph_number, search_vector, created_at)
SELECT * FROM dblink('host=localhost dbname=knowledge_base user=weixiangzhang',
    'SELECT chunk_id, book_id, chunk_type, title, content, word_count, 
            character_count, chapter_number, section_number, paragraph_number,
            search_vector, created_at
     FROM chunks 
     WHERE chunk_type IN (''chapter'', ''section'', ''paragraph'')
     AND content IS NOT NULL
     ORDER BY book_id, chunk_id')
AS remote_chunks(
    chunk_id varchar(255), book_id int, chunk_type varchar(50), title varchar(500),
    content text, word_count int, character_count int, chapter_number int,
    section_number int, paragraph_number int, search_vector tsvector, created_at timestamp
);

\echo '🧠 PHASE 3: Copying all embeddings...'
INSERT INTO chunk_embeddings (embedding_id, chunk_id, book_id, embedding, embedding_model, 
                             embedding_dimension, created_at, content_type, routing_reason, 
                             confidence_score, embedding_vector, embedding_vector_bge, 
                             embedding_vector_granite, embedding_vector_mxbai)
SELECT * FROM dblink('host=localhost dbname=knowledge_base user=weixiangzhang',
    'SELECT embedding_id, chunk_id, book_id, embedding, embedding_model, embedding_dimension, 
            created_at, content_type, routing_reason, confidence_score, embedding_vector, 
            embedding_vector_bge, embedding_vector_granite, embedding_vector_mxbai
     FROM chunk_embeddings ORDER BY embedding_id')
AS remote_embeddings(
    embedding_id int, chunk_id varchar(255), book_id int, embedding jsonb,
    embedding_model varchar(100), embedding_dimension int, created_at timestamp,
    content_type varchar(50), routing_reason text, confidence_score numeric(3,2),
    embedding_vector vector(768), embedding_vector_bge vector(1024),
    embedding_vector_granite vector(384), embedding_vector_mxbai vector(1024)
);

\echo '📊 MIGRATION COMPLETE - Verification:'
SELECT 
    'books' as table_name, COUNT(*) as count FROM books UNION ALL
SELECT 'chunks', COUNT(*) FROM chunks UNION ALL
SELECT 'chunk_embeddings', COUNT(*) FROM chunk_embeddings
ORDER BY table_name;

\echo ''
\echo '🎉 NUCLEAR MIGRATION COMPLETE!'
\echo '✅ Books: Complete dataset'
\echo '✅ Chunks: Readable only (84% reduction)'
\echo '✅ Embeddings: All preserved'