-- LibraryOfBabel Search Optimization Configuration
-- Advanced PostgreSQL tuning for <100ms search performance
-- Optimized for 24GB RAM system with 1GB available for database

-- =============================================================================
-- POSTGRESQL CONFIGURATION SETTINGS
-- =============================================================================

-- Memory Settings (optimized for 24GB system with ~1GB available for DB)
-- Note: These are recommendations - actual postgresql.conf changes needed
DO $$
BEGIN
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'PostgreSQL Configuration Recommendations';
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'Add these settings to postgresql.conf for optimal performance:';
    RAISE NOTICE '';
    RAISE NOTICE '# Memory settings (adjust based on available RAM)';
    RAISE NOTICE 'shared_buffers = 256MB                    # 25%% of available DB memory';
    RAISE NOTICE 'effective_cache_size = 768MB              # 75%% of available DB memory';
    RAISE NOTICE 'maintenance_work_mem = 128MB              # For index maintenance';
    RAISE NOTICE 'work_mem = 16MB                          # Per-connection work memory';
    RAISE NOTICE '';
    RAISE NOTICE '# Query optimization';
    RAISE NOTICE 'random_page_cost = 1.1                   # SSD optimization';
    RAISE NOTICE 'effective_io_concurrency = 200           # SSD concurrent I/O';
    RAISE NOTICE 'max_worker_processes = 8                 # Parallel processing';
    RAISE NOTICE 'max_parallel_workers_per_gather = 4      # Parallel query workers';
    RAISE NOTICE 'max_parallel_workers = 8                 # Total parallel workers';
    RAISE NOTICE '';
    RAISE NOTICE '# Full-text search optimization';
    RAISE NOTICE 'default_text_search_config = ''english''   # Default FTS config';
    RAISE NOTICE '';
    RAISE NOTICE '# Connection and logging';
    RAISE NOTICE 'max_connections = 100                    # Limit concurrent connections';
    RAISE NOTICE 'log_min_duration_statement = 100         # Log slow queries (>100ms)';
    RAISE NOTICE 'log_checkpoints = on                     # Monitor checkpoint performance';
    RAISE NOTICE '=============================================================================';
END $$;

-- =============================================================================
-- ADVANCED INDEXES FOR SEARCH PERFORMANCE
-- =============================================================================

-- Drop existing indexes that might be suboptimal
DROP INDEX IF EXISTS idx_chunks_content_gin;
DROP INDEX IF EXISTS idx_books_title_gin;
DROP INDEX IF EXISTS idx_books_author_gin;

-- Create optimized GIN indexes with custom configurations
CREATE INDEX CONCURRENTLY idx_chunks_content_gin_optimized 
ON chunks USING GIN(search_vector) 
WITH (fastupdate = off, gin_pending_list_limit = 4096);

CREATE INDEX CONCURRENTLY idx_books_search_gin_optimized 
ON books USING GIN(search_vector) 
WITH (fastupdate = off, gin_pending_list_limit = 4096);

-- Create covering indexes for common queries
CREATE INDEX CONCURRENTLY idx_chunks_search_covering 
ON chunks USING GIN(search_vector) 
INCLUDE (book_id, title, chapter_number, word_count);

CREATE INDEX CONCURRENTLY idx_books_search_covering 
ON books USING GIN(search_vector) 
INCLUDE (title, author, total_words, publication_date);

-- Fuzzy search indexes using trigrams
CREATE INDEX CONCURRENTLY idx_books_title_trigram 
ON books USING GIN(title gin_trgm_ops);

CREATE INDEX CONCURRENTLY idx_books_author_trigram 
ON books USING GIN(author gin_trgm_ops);

CREATE INDEX CONCURRENTLY idx_chunks_title_trigram 
ON chunks USING GIN(title gin_trgm_ops);

-- Specialized indexes for filtering
CREATE INDEX CONCURRENTLY idx_books_words_publication 
ON books(total_words DESC, publication_date DESC) 
WHERE processing_status = 'completed';

CREATE INDEX CONCURRENTLY idx_chunks_words_chapter 
ON chunks(word_count DESC, chapter_number) 
WHERE chunk_type = 'chapter';

-- =============================================================================
-- ADVANCED SEARCH FUNCTIONS
-- =============================================================================

-- Ultra-fast fuzzy search function
CREATE OR REPLACE FUNCTION fuzzy_search_books(
    query_text TEXT,
    similarity_threshold REAL DEFAULT 0.3,
    result_limit INTEGER DEFAULT 10
) RETURNS TABLE(
    book_id INTEGER,
    title VARCHAR(500),
    author VARCHAR(200),
    similarity_score REAL,
    match_type TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH fuzzy_matches AS (
        SELECT 
            b.book_id,
            b.title,
            b.author,
            GREATEST(
                similarity(b.title, query_text),
                similarity(coalesce(b.author, ''), query_text),
                similarity(coalesce(b.subject, ''), query_text)
            ) as sim_score,
            CASE 
                WHEN similarity(b.title, query_text) >= similarity_threshold THEN 'title'
                WHEN similarity(coalesce(b.author, ''), query_text) >= similarity_threshold THEN 'author'
                ELSE 'subject'
            END as match_type
        FROM books b
        WHERE (
            b.title % query_text OR 
            coalesce(b.author, '') % query_text OR 
            coalesce(b.subject, '') % query_text
        )
    )
    SELECT 
        fm.book_id,
        fm.title,
        fm.author,
        fm.sim_score,
        fm.match_type
    FROM fuzzy_matches fm
    WHERE fm.sim_score >= similarity_threshold
    ORDER BY fm.sim_score DESC, fm.title
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- Hybrid search combining exact and fuzzy matching
CREATE OR REPLACE FUNCTION hybrid_search(
    query_text TEXT,
    exact_weight REAL DEFAULT 0.7,
    fuzzy_weight REAL DEFAULT 0.3,
    result_limit INTEGER DEFAULT 10
) RETURNS TABLE(
    book_id INTEGER,
    title VARCHAR(500),
    author VARCHAR(200),
    combined_score REAL,
    exact_relevance REAL,
    fuzzy_similarity REAL,
    match_type TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH exact_matches AS (
        SELECT 
            b.book_id,
            b.title,
            b.author,
            ts_rank(b.search_vector, plainto_tsquery('english', query_text)) as exact_score,
            'exact' as match_type
        FROM books b
        WHERE b.search_vector @@ plainto_tsquery('english', query_text)
    ),
    fuzzy_matches AS (
        SELECT 
            b.book_id,
            b.title,
            b.author,
            GREATEST(
                similarity(b.title, query_text),
                similarity(coalesce(b.author, ''), query_text)
            ) as fuzzy_score,
            'fuzzy' as match_type
        FROM books b
        WHERE (b.title % query_text OR coalesce(b.author, '') % query_text)
        AND NOT EXISTS (
            SELECT 1 FROM exact_matches em WHERE em.book_id = b.book_id
        )
    ),
    combined_results AS (
        SELECT 
            book_id, title, author,
            exact_score * exact_weight as weighted_exact,
            0.0 as weighted_fuzzy,
            exact_score,
            0.0 as fuzzy_score,
            match_type
        FROM exact_matches
        UNION ALL
        SELECT 
            book_id, title, author,
            0.0 as weighted_exact,
            fuzzy_score * fuzzy_weight as weighted_fuzzy,
            0.0 as exact_score,
            fuzzy_score,
            match_type
        FROM fuzzy_matches
    )
    SELECT 
        cr.book_id,
        cr.title,
        cr.author,
        (cr.weighted_exact + cr.weighted_fuzzy) as combined_score,
        cr.exact_score,
        cr.fuzzy_score,
        cr.match_type
    FROM combined_results cr
    ORDER BY combined_score DESC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- Content search with snippet highlighting
CREATE OR REPLACE FUNCTION search_content_with_highlights(
    query_text TEXT,
    result_limit INTEGER DEFAULT 10,
    snippet_length INTEGER DEFAULT 200
) RETURNS TABLE(
    chunk_id INTEGER,
    book_id INTEGER,
    book_title VARCHAR(500),
    book_author VARCHAR(200),
    chunk_title VARCHAR(500),
    chapter_number INTEGER,
    highlighted_snippet TEXT,
    relevance REAL,
    word_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id,
        c.book_id,
        b.title as book_title,
        b.author as book_author,
        c.title as chunk_title,
        c.chapter_number,
        ts_headline('english', c.content, 
                   plainto_tsquery('english', query_text),
                   'MaxFragments=1, MaxWords=' || snippet_length || 
                   ', MinWords=10, StartSel=<mark>, StopSel=</mark>') as highlighted_snippet,
        ts_rank_cd(c.search_vector, plainto_tsquery('english', query_text)) as relevance,
        c.word_count
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE c.search_vector @@ plainto_tsquery('english', query_text)
    ORDER BY relevance DESC, c.word_count DESC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- Cross-reference search (find books discussing multiple concepts)
CREATE OR REPLACE FUNCTION cross_reference_search(
    concept_a TEXT,
    concept_b TEXT,
    result_limit INTEGER DEFAULT 10
) RETURNS TABLE(
    book_id INTEGER,
    book_title VARCHAR(500),
    book_author VARCHAR(200),
    concept_a_relevance REAL,
    concept_b_relevance REAL,
    combined_relevance REAL,
    concept_a_matches INTEGER,
    concept_b_matches INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH concept_matches AS (
        SELECT 
            c.book_id,
            SUM(CASE WHEN c.search_vector @@ plainto_tsquery('english', concept_a) 
                THEN ts_rank(c.search_vector, plainto_tsquery('english', concept_a)) 
                ELSE 0 END) as concept_a_relevance,
            SUM(CASE WHEN c.search_vector @@ plainto_tsquery('english', concept_b) 
                THEN ts_rank(c.search_vector, plainto_tsquery('english', concept_b)) 
                ELSE 0 END) as concept_b_relevance,
            COUNT(CASE WHEN c.search_vector @@ plainto_tsquery('english', concept_a) THEN 1 END) as concept_a_count,
            COUNT(CASE WHEN c.search_vector @@ plainto_tsquery('english', concept_b) THEN 1 END) as concept_b_count
        FROM chunks c
        WHERE (
            c.search_vector @@ plainto_tsquery('english', concept_a) OR
            c.search_vector @@ plainto_tsquery('english', concept_b)
        )
        GROUP BY c.book_id
        HAVING 
            COUNT(CASE WHEN c.search_vector @@ plainto_tsquery('english', concept_a) THEN 1 END) > 0 AND
            COUNT(CASE WHEN c.search_vector @@ plainto_tsquery('english', concept_b) THEN 1 END) > 0
    )
    SELECT 
        cm.book_id,
        b.title as book_title,
        b.author as book_author,
        cm.concept_a_relevance,
        cm.concept_b_relevance,
        (cm.concept_a_relevance + cm.concept_b_relevance) as combined_relevance,
        cm.concept_a_count::INTEGER,
        cm.concept_b_count::INTEGER
    FROM concept_matches cm
    JOIN books b ON cm.book_id = b.book_id
    ORDER BY combined_relevance DESC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- PERFORMANCE MONITORING FUNCTIONS
-- =============================================================================

-- Function to log search performance
CREATE OR REPLACE FUNCTION log_search_performance(
    query_text TEXT,
    query_type TEXT DEFAULT 'fulltext',
    results_count INTEGER DEFAULT 0,
    execution_time_ms INTEGER DEFAULT 0,
    filters JSONB DEFAULT NULL
) RETURNS INTEGER AS $$
DECLARE
    search_id INTEGER;
BEGIN
    INSERT INTO search_history (
        query_text, query_type, results_count, 
        execution_time_ms, filters
    ) VALUES (
        query_text, query_type, results_count, 
        execution_time_ms, filters
    ) RETURNING search_history.search_id INTO search_id;
    
    RETURN search_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get search performance statistics
CREATE OR REPLACE FUNCTION get_search_statistics(
    days_back INTEGER DEFAULT 7
) RETURNS TABLE(
    metric VARCHAR(50),
    value NUMERIC,
    unit VARCHAR(20)
) AS $$
BEGIN
    RETURN QUERY
    WITH stats AS (
        SELECT 
            COUNT(*)::NUMERIC as total_searches,
            AVG(execution_time_ms)::NUMERIC as avg_execution_time,
            MAX(execution_time_ms)::NUMERIC as max_execution_time,
            MIN(execution_time_ms)::NUMERIC as min_execution_time,
            AVG(results_count)::NUMERIC as avg_results_count,
            COUNT(CASE WHEN execution_time_ms > 100 THEN 1 END)::NUMERIC as slow_queries
        FROM search_history 
        WHERE created_at >= NOW() - INTERVAL '1 day' * days_back
    )
    SELECT 'total_searches'::VARCHAR(50), s.total_searches, 'queries'::VARCHAR(20) FROM stats s
    UNION ALL
    SELECT 'avg_execution_time'::VARCHAR(50), s.avg_execution_time, 'milliseconds'::VARCHAR(20) FROM stats s
    UNION ALL
    SELECT 'max_execution_time'::VARCHAR(50), s.max_execution_time, 'milliseconds'::VARCHAR(20) FROM stats s
    UNION ALL
    SELECT 'min_execution_time'::VARCHAR(50), s.min_execution_time, 'milliseconds'::VARCHAR(20) FROM stats s
    UNION ALL
    SELECT 'avg_results_count'::VARCHAR(50), s.avg_results_count, 'results'::VARCHAR(20) FROM stats s
    UNION ALL
    SELECT 'slow_queries_count'::VARCHAR(50), s.slow_queries, 'queries'::VARCHAR(20) FROM stats s
    UNION ALL
    SELECT 'slow_queries_percentage'::VARCHAR(50), 
           CASE WHEN s.total_searches > 0 THEN (s.slow_queries / s.total_searches) * 100 ELSE 0 END,
           'percent'::VARCHAR(20) FROM stats s;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- DATABASE MAINTENANCE FUNCTIONS
-- =============================================================================

-- Function to update all search statistics
CREATE OR REPLACE FUNCTION refresh_search_statistics() RETURNS VOID AS $$
BEGIN
    -- Update table statistics
    ANALYZE books;
    ANALYZE chunks;
    ANALYZE search_history;
    
    -- Refresh materialized views if any exist
    -- (placeholder for future materialized views)
    
    RAISE NOTICE 'Search statistics refreshed successfully';
END;
$$ LANGUAGE plpgsql;

-- Function to optimize database for search performance
CREATE OR REPLACE FUNCTION optimize_search_performance() RETURNS TEXT AS $$
DECLARE
    result_text TEXT := '';
BEGIN
    -- Reindex search indexes
    REINDEX INDEX CONCURRENTLY idx_chunks_content_gin_optimized;
    REINDEX INDEX CONCURRENTLY idx_books_search_gin_optimized;
    
    result_text := result_text || 'Search indexes reindexed. ';
    
    -- Update statistics
    PERFORM refresh_search_statistics();
    result_text := result_text || 'Statistics updated. ';
    
    -- Vacuum analyze for optimal performance
    VACUUM ANALYZE books;
    VACUUM ANALYZE chunks;
    result_text := result_text || 'Tables vacuumed and analyzed. ';
    
    RETURN result_text || 'Search optimization completed successfully.';
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMPLETION AND VERIFICATION
-- =============================================================================

-- Verify search optimization setup
DO $$
DECLARE
    index_count INTEGER;
    function_count INTEGER;
BEGIN
    -- Count search-related indexes
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND (indexname LIKE '%search%' OR indexname LIKE '%gin%' OR indexname LIKE '%trigram%');
    
    -- Count search functions
    SELECT COUNT(*) INTO function_count
    FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE n.nspname = 'public' 
    AND p.proname LIKE '%search%';
    
    RAISE NOTICE '';
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'LibraryOfBabel Search Optimization Setup Complete';
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'Search Indexes Created: %', index_count;
    RAISE NOTICE 'Search Functions Available: %', function_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Available Search Functions:';
    RAISE NOTICE '- search_books(query_text, limit, offset)';
    RAISE NOTICE '- search_content(query_text, limit, offset)';
    RAISE NOTICE '- fuzzy_search_books(query_text, similarity_threshold, limit)';
    RAISE NOTICE '- hybrid_search(query_text, exact_weight, fuzzy_weight, limit)';
    RAISE NOTICE '- search_content_with_highlights(query_text, limit, snippet_length)';
    RAISE NOTICE '- cross_reference_search(concept_a, concept_b, limit)';
    RAISE NOTICE '';
    RAISE NOTICE 'Performance Monitoring:';
    RAISE NOTICE '- log_search_performance(query, type, results, time_ms, filters)';
    RAISE NOTICE '- get_search_statistics(days_back)';
    RAISE NOTICE '- optimize_search_performance()';
    RAISE NOTICE '';
    RAISE NOTICE 'Target: <100ms search performance';
    RAISE NOTICE 'Status: Ready for production use';
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE '';
END $$;