-- LibraryOfBabel Database Test Queries
-- Comprehensive testing and validation queries for the knowledge base

-- =============================================================================
-- DATABASE VALIDATION TESTS
-- =============================================================================

\echo '============================================================================='
\echo 'LibraryOfBabel Database Test Suite'
\echo '============================================================================='

-- Test 1: Basic database structure
\echo ''
\echo 'Test 1: Database Structure Validation'
\echo '-------------------------------------'

-- Check that all required tables exist
SELECT 
    table_name,
    CASE 
        WHEN table_name IN ('books', 'chunks', 'search_history', 'processing_log') 
        THEN '✓ PASS' 
        ELSE '✗ FAIL' 
    END as status
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Test 2: Index validation
\echo ''
\echo 'Test 2: Search Index Validation'
\echo '-------------------------------'

SELECT 
    schemaname,
    indexname,
    tablename,
    CASE 
        WHEN indexname LIKE '%gin%' OR indexname LIKE '%search%' 
        THEN '✓ Search Index' 
        ELSE 'Regular Index' 
    END as index_type
FROM pg_indexes 
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Test 3: Function validation
\echo ''
\echo 'Test 3: Search Function Validation'
\echo '----------------------------------'

SELECT 
    proname as function_name,
    pg_get_function_arguments(oid) as arguments,
    CASE 
        WHEN proname LIKE '%search%' THEN '✓ Search Function'
        ELSE 'Utility Function'
    END as function_type
FROM pg_proc 
WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
AND proname LIKE '%search%'
ORDER BY proname;

-- =============================================================================
-- DATA CONTENT TESTS
-- =============================================================================

\echo ''
\echo 'Test 4: Data Content Validation'
\echo '-------------------------------'

-- Check book count and statistics
SELECT 
    'Books' as table_name,
    COUNT(*) as record_count,
    MIN(created_at) as earliest_record,
    MAX(created_at) as latest_record,
    COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as completed_books
FROM books;

-- Check chunk count and statistics
SELECT 
    'Chunks' as table_name,
    COUNT(*) as record_count,
    SUM(word_count) as total_words,
    AVG(word_count)::INTEGER as avg_words_per_chunk,
    COUNT(DISTINCT book_id) as books_with_chunks
FROM chunks;

-- Check data integrity
SELECT 
    'Data Integrity' as test_category,
    COUNT(CASE WHEN b.book_id IS NULL THEN 1 END) as orphaned_chunks,
    COUNT(CASE WHEN c.book_id IS NULL THEN 1 END) as books_without_chunks
FROM chunks c 
FULL OUTER JOIN books b ON c.book_id = b.book_id;

-- =============================================================================
-- SEARCH PERFORMANCE TESTS
-- =============================================================================

\echo ''
\echo 'Test 5: Search Performance Validation'
\echo '------------------------------------'

-- Test basic search functionality
\echo 'Testing basic book search...'
\timing on

SELECT 
    book_id,
    title,
    author,
    relevance,
    '✓ Basic search working' as status
FROM search_books('money', 5)
LIMIT 5;

\timing off

-- Test content search
\echo ''
\echo 'Testing content search...'
\timing on

SELECT 
    chunk_id,
    book_title,
    chapter_number,
    LEFT(content_snippet, 100) || '...' as preview,
    relevance::NUMERIC(4,3),
    '✓ Content search working' as status
FROM search_content('investing', 3)
LIMIT 3;

\timing off

-- Test fuzzy search
\echo ''
\echo 'Testing fuzzy search...'
\timing on

SELECT 
    book_id,
    title,
    author,
    similarity_score::NUMERIC(4,3),
    match_type,
    '✓ Fuzzy search working' as status
FROM fuzzy_search_books('invest', 0.3, 3)
LIMIT 3;

\timing off

-- =============================================================================
-- ADVANCED SEARCH TESTS
-- =============================================================================

\echo ''
\echo 'Test 6: Advanced Search Features'
\echo '--------------------------------'

-- Test hybrid search
\echo 'Testing hybrid search...'
SELECT 
    title,
    author,
    combined_score::NUMERIC(4,3),
    match_type,
    '✓ Hybrid search working' as status
FROM hybrid_search('financial', 0.7, 0.3, 3)
LIMIT 3;

-- Test content search with highlights
\echo ''
\echo 'Testing search with highlights...'
SELECT 
    book_title,
    chunk_title,
    chapter_number,
    CASE 
        WHEN highlighted_snippet LIKE '%<mark>%' 
        THEN '✓ Highlighting working'
        ELSE '✗ Highlighting failed'
    END as highlight_status
FROM search_content_with_highlights('money', 2)
LIMIT 2;

-- =============================================================================
-- PERFORMANCE BENCHMARKS
-- =============================================================================

\echo ''
\echo 'Test 7: Performance Benchmarks'
\echo '------------------------------'

-- Benchmark search performance
\echo 'Running performance benchmark...'

-- Create temporary table for timing results
CREATE TEMP TABLE timing_results (
    test_name TEXT,
    execution_time_ms INTEGER,
    result_count INTEGER,
    performance_rating TEXT
);

-- Test multiple search queries and measure performance
DO $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    execution_ms INTEGER;
    result_count INTEGER;
BEGIN
    -- Test 1: Basic book search
    start_time := clock_timestamp();
    SELECT COUNT(*) INTO result_count FROM search_books('investment', 10);
    end_time := clock_timestamp();
    execution_ms := EXTRACT(milliseconds FROM (end_time - start_time))::INTEGER;
    
    INSERT INTO timing_results VALUES (
        'Basic Book Search',
        execution_ms,
        result_count,
        CASE WHEN execution_ms < 100 THEN '✓ EXCELLENT' 
             WHEN execution_ms < 250 THEN '△ GOOD' 
             ELSE '✗ NEEDS OPTIMIZATION' END
    );
    
    -- Test 2: Content search
    start_time := clock_timestamp();
    SELECT COUNT(*) INTO result_count FROM search_content('financial', 10);
    end_time := clock_timestamp();
    execution_ms := EXTRACT(milliseconds FROM (end_time - start_time))::INTEGER;
    
    INSERT INTO timing_results VALUES (
        'Content Search',
        execution_ms,
        result_count,
        CASE WHEN execution_ms < 100 THEN '✓ EXCELLENT' 
             WHEN execution_ms < 250 THEN '△ GOOD' 
             ELSE '✗ NEEDS OPTIMIZATION' END
    );
    
    -- Test 3: Fuzzy search
    start_time := clock_timestamp();
    SELECT COUNT(*) INTO result_count FROM fuzzy_search_books('invest', 0.3, 10);
    end_time := clock_timestamp();
    execution_ms := EXTRACT(milliseconds FROM (end_time - start_time))::INTEGER;
    
    INSERT INTO timing_results VALUES (
        'Fuzzy Search',
        execution_ms,
        result_count,
        CASE WHEN execution_ms < 100 THEN '✓ EXCELLENT' 
             WHEN execution_ms < 250 THEN '△ GOOD' 
             ELSE '✗ NEEDS OPTIMIZATION' END
    );
END $$;

-- Display performance results
SELECT 
    test_name,
    execution_time_ms || 'ms' as execution_time,
    result_count,
    performance_rating
FROM timing_results
ORDER BY execution_time_ms;

-- =============================================================================
-- DATABASE STATISTICS
-- =============================================================================

\echo ''
\echo 'Test 8: Database Statistics'
\echo '---------------------------'

-- Overall database statistics
SELECT * FROM database_stats;

-- Search vector statistics
SELECT 
    'Search Optimization' as category,
    COUNT(CASE WHEN search_vector IS NOT NULL THEN 1 END) as books_with_search_vectors,
    COUNT(*) as total_books,
    ROUND(
        (COUNT(CASE WHEN search_vector IS NOT NULL THEN 1 END)::NUMERIC / COUNT(*)) * 100, 2
    ) || '%' as optimization_percentage
FROM books
UNION ALL
SELECT 
    'Chunk Optimization' as category,
    COUNT(CASE WHEN search_vector IS NOT NULL THEN 1 END) as chunks_with_search_vectors,
    COUNT(*) as total_chunks,
    ROUND(
        (COUNT(CASE WHEN search_vector IS NOT NULL THEN 1 END)::NUMERIC / COUNT(*)) * 100, 2
    ) || '%' as optimization_percentage
FROM chunks;

-- =============================================================================
-- SAMPLE DATA PREVIEW
-- =============================================================================

\echo ''
\echo 'Test 9: Sample Data Preview'
\echo '---------------------------'

-- Show sample books
\echo 'Sample Books:'
SELECT 
    book_id,
    LEFT(title, 50) || CASE WHEN LENGTH(title) > 50 THEN '...' ELSE '' END as title,
    author,
    total_words,
    total_chapters,
    processing_status
FROM books
ORDER BY total_words DESC
LIMIT 5;

-- Show sample chunks
\echo ''
\echo 'Sample Chunks:'
SELECT 
    c.chunk_id,
    b.title as book_title,
    c.chapter_number,
    LEFT(c.title, 30) || CASE WHEN LENGTH(c.title) > 30 THEN '...' ELSE '' END as chunk_title,
    c.word_count
FROM chunks c
JOIN books b ON c.book_id = b.book_id
ORDER BY c.word_count DESC
LIMIT 5;

-- =============================================================================
-- FINAL VALIDATION SUMMARY
-- =============================================================================

\echo ''
\echo 'Test 10: Final Validation Summary'
\echo '---------------------------------'

-- Comprehensive validation summary
WITH validation_summary AS (
    SELECT 
        'Database Structure' as test_category,
        CASE 
            WHEN (SELECT COUNT(*) FROM information_schema.tables 
                  WHERE table_schema = 'public' AND table_type = 'BASE TABLE') >= 4
            THEN '✓ PASS'
            ELSE '✗ FAIL'
        END as status
    UNION ALL
    SELECT 
        'Search Indexes',
        CASE 
            WHEN (SELECT COUNT(*) FROM pg_indexes 
                  WHERE schemaname = 'public' AND indexname LIKE '%gin%') >= 2
            THEN '✓ PASS'
            ELSE '✗ FAIL'
        END
    UNION ALL
    SELECT 
        'Search Functions',
        CASE 
            WHEN (SELECT COUNT(*) FROM pg_proc 
                  WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
                  AND proname LIKE '%search%') >= 4
            THEN '✓ PASS'
            ELSE '✗ FAIL'
        END
    UNION ALL
    SELECT 
        'Data Content',
        CASE 
            WHEN (SELECT COUNT(*) FROM books WHERE processing_status = 'completed') > 0
            AND (SELECT COUNT(*) FROM chunks) > 0
            THEN '✓ PASS'
            ELSE '✗ FAIL'
        END
    UNION ALL
    SELECT 
        'Search Performance',
        CASE 
            WHEN (SELECT AVG(execution_time_ms) FROM timing_results) < 200
            THEN '✓ PASS'
            ELSE '△ ACCEPTABLE'
        END
)
SELECT 
    test_category,
    status,
    CASE 
        WHEN status LIKE '✓%' THEN 'All tests passed'
        WHEN status LIKE '△%' THEN 'Acceptable performance'
        ELSE 'Needs attention'
    END as notes
FROM validation_summary;

-- Final database readiness check
\echo ''
\echo '============================================================================='
WITH readiness_check AS (
    SELECT 
        COUNT(*) as total_books,
        SUM(total_words) as total_words,
        COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as completed_books,
        (SELECT COUNT(*) FROM chunks) as total_chunks,
        (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public' AND indexname LIKE '%search%') as search_indexes
    FROM books
)
SELECT 
    CASE 
        WHEN total_books > 0 AND total_chunks > 0 AND search_indexes >= 4
        THEN '🚀 DATABASE READY FOR PRODUCTION'
        ELSE '⚠️  DATABASE NEEDS CONFIGURATION'
    END as status,
    total_books || ' books' as books,
    total_words || ' words' as words,
    total_chunks || ' chunks' as chunks,
    search_indexes || ' search indexes' as indexes
FROM readiness_check;

\echo '============================================================================='
\echo 'Test suite completed. Check results above for any failures.'
\echo '============================================================================='