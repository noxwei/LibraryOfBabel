-- Phonetic Search Performance Report
-- Dr. Sarah Chen - Optimization Results Analysis

-- Database Stats
SELECT 
    'Database Size Analysis' as report_section,
    pg_size_pretty(pg_database_size('knowledge_base')) as total_db_size,
    (SELECT COUNT(*) FROM chunks) as total_chunks,
    (SELECT COUNT(*) FROM books) as total_books;

-- Phonetic Column Stats
SELECT 
    'Phonetic Enhancement Status' as report_section,
    COUNT(*) as total_chunks,
    COUNT(content_soundex) as soundex_ready,
    COUNT(content_metaphone) as metaphone_ready,
    COUNT(content_audiobook_normalized) as normalized_ready,
    ROUND(AVG(LENGTH(content_soundex)), 2) as avg_soundex_length,
    ROUND(AVG(LENGTH(content_audiobook_normalized)), 2) as avg_normalized_length
FROM chunks;

-- Index Usage Analysis
SELECT 
    'Performance Indexes' as report_section,
    schemaname,
    tablename,
    indexname,
    idx_scan as times_used,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes 
WHERE indexname LIKE '%phonetic%' 
   OR indexname LIKE '%soundex%' 
   OR indexname LIKE '%metaphone%'
   OR indexname LIKE '%audiobook%'
   OR indexname LIKE '%trigram%'
ORDER BY idx_scan DESC;

-- Sample Search Performance Test
-- Test 1: Traditional text search
\timing on
SELECT COUNT(*) as traditional_search_results
FROM chunks c
JOIN books b ON c.book_id = b.book_id
WHERE c.content ILIKE '%philosophy%'
LIMIT 20;

-- Test 2: Enhanced phonetic search (simplified)
SELECT COUNT(*) as phonetic_search_results
FROM chunks c
JOIN books b ON c.book_id = b.book_id
WHERE (
    c.content ILIKE '%philosophy%'
    OR c.content_audiobook_normalized ILIKE '%philosophy%'
    OR c.content_soundex LIKE '%P421%'  -- soundex for 'philosophy'
)
LIMIT 20;

-- Test 3: Author similarity search
SELECT 
    'Author Search Test' as test_type,
    author,
    COUNT(*) as book_count,
    similarity(author, 'foucault') as similarity_score
FROM books 
WHERE similarity(author, 'foucault') > 0.2
GROUP BY author
ORDER BY similarity_score DESC
LIMIT 5;

\timing off

-- Storage Impact Analysis
SELECT 
    'Storage Impact' as analysis_type,
    pg_size_pretty(pg_total_relation_size('chunks')) as chunks_table_size,
    pg_size_pretty(
        pg_total_relation_size('idx_chunks_phonetic_composite')
    ) as composite_index_size,
    ROUND(
        (pg_total_relation_size('idx_chunks_phonetic_composite')::numeric / 
         pg_total_relation_size('chunks')::numeric) * 100, 2
    ) as index_overhead_percent;

-- Function Readiness Check
SELECT 
    'Function Status' as check_type,
    routine_name,
    routine_type,
    data_type as returns
FROM information_schema.routines 
WHERE routine_name IN (
    'api_ultra_fast_phonetic_search',
    'api_fast_author_phonetic_search',
    'api_simple_phonetic_test'
)
ORDER BY routine_name;