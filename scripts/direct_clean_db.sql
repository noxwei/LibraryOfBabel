-- 🧠 Dr. Chen's Direct Clean Database Creation
-- Copy embedded books and readable chunks to knowledge_with_embeds

\echo '🧠 DR. CHEN: Creating clean embedded database'
\echo '============================================'

-- Connect to new database (run after creating it)
\c knowledge_with_embeds

-- Copy books with embeddings
\echo 'Copying books with embeddings...'
\copy (SELECT * FROM books WHERE book_id IN (SELECT DISTINCT book_id FROM chunk_embeddings)) TO '/tmp/books_embedded.csv' CSV;

-- Copy readable chunks only
\echo 'Copying readable chunks...'  
\copy (SELECT * FROM chunks WHERE book_id IN (SELECT DISTINCT book_id FROM chunk_embeddings) AND chunk_type IN ('chapter', 'section', 'paragraph') AND content IS NOT NULL) TO '/tmp/chunks_readable.csv' CSV;

-- Copy embeddings
\echo 'Copying embeddings...'
\copy chunk_embeddings TO '/tmp/embeddings.csv' CSV;

-- Import to clean database
\copy books FROM '/tmp/books_embedded.csv' CSV;
\copy chunks FROM '/tmp/chunks_readable.csv' CSV;  
\copy chunk_embeddings FROM '/tmp/embeddings.csv' CSV;

-- Cleanup temp files
\! rm -f /tmp/books_embedded.csv /tmp/chunks_readable.csv /tmp/embeddings.csv

-- Verify
\echo 'Verification:'
SELECT 
    'books' as table_name, COUNT(*) FROM books UNION ALL
SELECT 'chunks', COUNT(*) FROM chunks UNION ALL  
SELECT 'chunk_embeddings', COUNT(*) FROM chunk_embeddings;

\echo ''
\echo '✅ Clean database ready: knowledge_with_embeds'