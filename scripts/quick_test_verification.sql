-- Quick test database verification
\echo '🧠 DR. CHEN TEST DATABASE VERIFICATION'
\echo '===================================='

-- Check what we have
SELECT 
    'books' as table_name, COUNT(*) as count FROM books UNION ALL
SELECT 'chunks', COUNT(*) FROM chunks UNION ALL
SELECT 'chunk_embeddings', COUNT(*) FROM chunk_embeddings UNION ALL
SELECT 'chen_functions', COUNT(*) FROM pg_proc WHERE proname LIKE 'chen_%';

-- Test one Chen function
\echo ''
\echo 'Testing Chen lightning search...'
SELECT chunk_id, LEFT(title, 50) as title_sample 
FROM chen_lightning_search('love', 2);

\echo ''  
\echo '✅ Test database verification complete!'