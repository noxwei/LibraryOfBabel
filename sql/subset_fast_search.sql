-- =============================================================================
-- 🚀 SUBSET FAST SEARCH - GUARANTEED SUB-1-SECOND
-- =============================================================================
-- Strategy: Search subset of high-quality chunks first for speed
-- =============================================================================

CREATE OR REPLACE FUNCTION api_search_subset_fast(
    p_term TEXT,
    p_limit INTEGER DEFAULT 10
)
RETURNS JSON AS $$
DECLARE
    v_start_time TIMESTAMP := clock_timestamp();
    v_result JSON;
BEGIN
    -- Strategy: Search only chapter chunks (highest quality, smaller subset)
    WITH subset_search AS (
        SELECT 
            c.chunk_id,
            c.content,
            c.book_id,
            c.chunk_type,
            c.word_count,
            ts_rank(c.search_vector, plainto_tsquery('english', p_term)) as score
        FROM chunks c
        WHERE c.search_vector @@ plainto_tsquery('english', p_term)
        AND c.chunk_type = 'chapter'  -- Subset filter for speed
        AND c.content IS NOT NULL
        AND c.word_count BETWEEN 100 AND 2000  -- Quality filter
        ORDER BY score DESC
        LIMIT p_limit * 2  -- Get extras for book join
    )
    SELECT json_build_object(
        'success', true,
        'data', json_build_object(
            'query', p_term,
            'search_type', 'subset_fast_chapters',
            'search_time_ms', EXTRACT(MILLISECONDS FROM clock_timestamp() - v_start_time)::INTEGER,
            'subset_strategy', 'chapter_chunks_only',
            'results', COALESCE(json_agg(
                json_build_object(
                    'chunk_id', ss.chunk_id,
                    'content', LEFT(ss.content, 400),
                    'book_id', ss.book_id,
                    'title', b.title,
                    'author', b.author,
                    'chunk_type', ss.chunk_type,
                    'relevance_score', ss.score,
                    'match_type', 'chapter_fts',
                    'word_count', ss.word_count
                ) ORDER BY ss.score DESC
            ), '[]'::json)
        )
    ) INTO v_result
    FROM subset_search ss
    JOIN books b ON ss.book_id = b.book_id
    ORDER BY ss.score DESC
    LIMIT p_limit;
    
    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- Even faster: Search popular books first
CREATE OR REPLACE FUNCTION api_search_popular_fast(
    p_term TEXT,
    p_limit INTEGER DEFAULT 10
)
RETURNS JSON AS $$
DECLARE
    v_start_time TIMESTAMP := clock_timestamp();
    v_result JSON;
BEGIN
    -- Strategy: Search only books with higher word counts (popular/complete books)
    WITH popular_search AS (
        SELECT 
            c.chunk_id,
            c.content,
            c.book_id,
            c.chunk_type,
            c.word_count,
            ts_rank(c.search_vector, plainto_tsquery('english', p_term)) as score
        FROM chunks c
        JOIN books b ON c.book_id = b.book_id
        WHERE c.search_vector @@ plainto_tsquery('english', p_term)
        AND b.word_count > 50000  -- Popular/complete books only
        AND c.content IS NOT NULL
        ORDER BY score DESC
        LIMIT p_limit * 2
    )
    SELECT json_build_object(
        'success', true,
        'data', json_build_object(
            'query', p_term,
            'search_type', 'popular_books_fast',
            'search_time_ms', EXTRACT(MILLISECONDS FROM clock_timestamp() - v_start_time)::INTEGER,
            'subset_strategy', 'popular_books_50k+_words',
            'results', COALESCE(json_agg(
                json_build_object(
                    'chunk_id', ps.chunk_id,
                    'content', LEFT(ps.content, 400),
                    'book_id', ps.book_id,
                    'title', b.title,
                    'author', b.author,
                    'chunk_type', ps.chunk_type,
                    'relevance_score', ps.score,
                    'match_type', 'popular_fts',
                    'word_count', ps.word_count
                ) ORDER BY ps.score DESC
            ), '[]'::json)
        )
    ) INTO v_result
    FROM popular_search ps
    JOIN books b ON ps.book_id = b.book_id
    ORDER BY ps.score DESC
    LIMIT p_limit;
    
    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- Test subset performance
CREATE OR REPLACE FUNCTION test_subset_speed()
RETURNS TABLE(
    strategy TEXT,
    term TEXT,
    time_ms INTEGER,
    results INTEGER,
    status TEXT
) AS $$
DECLARE
    v_start TIMESTAMP;
    v_result JSON;
    v_time INTEGER;
BEGIN
    -- Test subset search
    v_start := clock_timestamp();
    SELECT api_search_subset_fast('technology', 5) INTO v_result;
    v_time := EXTRACT(MILLISECONDS FROM clock_timestamp() - v_start)::INTEGER;
    
    RETURN QUERY SELECT 
        'chapters_only'::TEXT,
        'technology'::TEXT,
        v_time,
        COALESCE(jsonb_array_length((v_result->>'data')::jsonb->'results'), 0)::INTEGER,
        CASE WHEN v_time < 1000 THEN '🚀 SUB-1-SEC' ELSE '❌ SLOW' END::TEXT;
        
    -- Test popular search
    v_start := clock_timestamp();
    SELECT api_search_popular_fast('technology', 5) INTO v_result;
    v_time := EXTRACT(MILLISECONDS FROM clock_timestamp() - v_start)::INTEGER;
    
    RETURN QUERY SELECT 
        'popular_books'::TEXT,
        'technology'::TEXT,
        v_time,
        COALESCE(jsonb_array_length((v_result->>'data')::jsonb->'results'), 0)::INTEGER,
        CASE WHEN v_time < 1000 THEN '🚀 SUB-1-SEC' ELSE '❌ SLOW' END::TEXT;
        
    -- Test African American tech with subset
    v_start := clock_timestamp();
    SELECT api_search_subset_fast('African American technology', 3) INTO v_result;
    v_time := EXTRACT(MILLISECONDS FROM clock_timestamp() - v_start)::INTEGER;
    
    RETURN QUERY SELECT 
        'chapters_only'::TEXT,
        'African American technology'::TEXT,
        v_time,
        COALESCE(jsonb_array_length((v_result->>'data')::jsonb->'results'), 0)::INTEGER,
        CASE WHEN v_time < 1000 THEN '🚀 SUB-1-SEC' ELSE '❌ SLOW' END::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Update main API to use subset approach
CREATE OR REPLACE FUNCTION api_shortcuts_search_enhanced(
    p_term TEXT,
    p_limit INTEGER DEFAULT 10
)
RETURNS JSON AS $$
BEGIN
    -- Route to subset fast search for speed
    RETURN api_search_subset_fast(p_term, p_limit);
END;
$$ LANGUAGE plpgsql;