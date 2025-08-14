-- =============================================================================
-- 🚀 ULTRA-FAST TRIGRAM FUNCTIONS (No Indexing)
-- =============================================================================

-- Ultra-fast trigram search with smart filtering
CREATE OR REPLACE FUNCTION api_trigram_search_fast(
    p_term TEXT,
    p_limit INTEGER DEFAULT 10
)
RETURNS JSON AS $$
DECLARE
    v_result JSON;
    v_term_length INTEGER;
BEGIN
    -- Input validation
    IF p_term IS NULL OR LENGTH(TRIM(p_term)) < 3 THEN
        RETURN json_build_object(
            'success', false,
            'error', 'Search term must be at least 3 characters',
            'results', '[]'::json
        );
    END IF;
    
    v_term_length := LENGTH(p_term);
    
    -- Strategy: Smart filtering to avoid full table scans
    SELECT json_build_object(
        'success', true,
        'strategy', 'optimized_filtering',
        'term_length', v_term_length,
        'results', COALESCE(json_agg(
            json_build_object(
                'chunk_id', c.chunk_id,
                'title', b.title,
                'author', b.author,
                'content', LEFT(c.content, 300),
                'similarity_score', similarity(c.content, p_term),
                'chunk_type', c.chunk_type
            ) ORDER BY similarity(c.content, p_term) DESC
        ), '[]'::json)
    ) INTO v_result
    FROM (
        SELECT c.chunk_id, c.content, c.book_id, c.chunk_type
        FROM chunks c
        WHERE c.content IS NOT NULL
        AND length(c.content) BETWEEN 50 AND 1500  -- Filter early
        AND c.content % p_term  -- Trigram match
        ORDER BY similarity(c.content, p_term) DESC
        LIMIT p_limit * 2  -- Get extra for filtering
    ) c
    JOIN books b ON c.book_id = b.book_id
    ORDER BY similarity(c.content, p_term) DESC
    LIMIT p_limit;
    
    RETURN v_result;
    
EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object(
            'success', false,
            'error', 'Search failed: ' || SQLERRM,
            'results', '[]'::json
        );
END;
$$ LANGUAGE plpgsql;

-- Ultra-fast enhanced API function
CREATE OR REPLACE FUNCTION api_shortcuts_search_ultra_fast(
    p_term TEXT,
    p_limit INTEGER DEFAULT 10
)
RETURNS JSON AS $$
DECLARE
    v_json_result JSON;
    v_search_start TIMESTAMP := clock_timestamp();
    v_search_duration INTERVAL;
BEGIN
    -- Input validation
    IF p_term IS NULL OR LENGTH(TRIM(p_term)) = 0 THEN
        RETURN json_build_object(
            'success', true,
            'data', json_build_object(
                'query', p_term,
                'total_results', 0,
                'search_time_ms', 0,
                'results', '[]'::json
            )
        );
    END IF;
    
    -- ULTRA-FAST SEARCH with early filtering
    SELECT json_build_object(
        'success', true,
        'data', json_build_object(
            'query', p_term,
            'search_type', 'ultra_fast_filtered',
            'results', COALESCE(json_agg(
                json_build_object(
                    'chunk_id', search_results.chunk_id,
                    'content', search_results.content_preview,
                    'book_id', search_results.book_id,
                    'title', search_results.title,
                    'author', search_results.author,
                    'chunk_type', search_results.chunk_type,
                    'relevance_score', search_results.combined_score,
                    'match_type', search_results.match_type,
                    'word_count', search_results.word_count
                ) ORDER BY search_results.combined_score DESC
            ), '[]'::json)
        )
    ) INTO v_json_result
    FROM (
        -- SMART FILTERING STRATEGY
        SELECT 
            c.chunk_id,
            LEFT(c.content, 400) as content_preview,
            c.book_id,
            c.chunk_type,
            c.word_count,
            b.title,
            b.author,
            -- Fast scoring
            similarity(c.content, p_term) * 0.8 + 
            CASE WHEN b.title ILIKE '%' || p_term || '%' THEN 0.2 ELSE 0 END as combined_score,
            'trigram_similarity' as match_type
        FROM (
            SELECT chunk_id, content, book_id, chunk_type, word_count
            FROM chunks 
            WHERE content IS NOT NULL
            AND length(content) BETWEEN 100 AND 1200  -- Pre-filter size
            AND content % p_term  -- Trigram first
            ORDER BY similarity(content, p_term) DESC
            LIMIT p_limit * 3  -- Get extras for join filtering
        ) c
        JOIN books b ON c.book_id = b.book_id
        ORDER BY combined_score DESC
        LIMIT p_limit
    ) search_results;
    
    -- Add timing
    v_search_duration := clock_timestamp() - v_search_start;
    SELECT jsonb_set(
        v_json_result::jsonb,
        '{data,search_time_ms}',
        to_jsonb(EXTRACT(MILLISECONDS FROM v_search_duration)::INTEGER)
    )::json INTO v_json_result;
    
    RETURN v_json_result;
    
EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object(
            'success', false,
            'error', 'Ultra-fast search failed: ' || SQLERRM,
            'search_time_ms', EXTRACT(MILLISECONDS FROM clock_timestamp() - v_search_start)::INTEGER
        );
END;
$$ LANGUAGE plpgsql;

-- Speed test function
CREATE OR REPLACE FUNCTION test_trigram_speed_quick()
RETURNS TABLE(
    test_term TEXT,
    search_time_ms INTEGER,
    result_count INTEGER,
    performance_rating TEXT
) AS $$
DECLARE
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_duration_ms INTEGER;
    v_result JSON;
BEGIN
    -- Test: African American tech
    v_start_time := clock_timestamp();
    SELECT api_shortcuts_search_ultra_fast('African American tech', 3) INTO v_result;
    v_end_time := clock_timestamp();
    v_duration_ms := EXTRACT(MILLISECONDS FROM v_end_time - v_start_time)::INTEGER;
    
    RETURN QUERY SELECT 
        'African American tech'::TEXT,
        v_duration_ms,
        COALESCE(jsonb_array_length((v_result->>'data')::jsonb->'results'), 0)::INTEGER,
        CASE 
            WHEN v_duration_ms < 1000 THEN 'EXCELLENT (<1s)' 
            WHEN v_duration_ms < 3000 THEN 'GOOD (<3s)'
            ELSE 'NEEDS_WORK'
        END::TEXT;
        
    -- Test: AI fairness  
    v_start_time := clock_timestamp();
    SELECT api_shortcuts_search_ultra_fast('AI fairness', 3) INTO v_result;
    v_end_time := clock_timestamp();
    v_duration_ms := EXTRACT(MILLISECONDS FROM v_end_time - v_start_time)::INTEGER;
    
    RETURN QUERY SELECT 
        'AI fairness'::TEXT,
        v_duration_ms,
        COALESCE(jsonb_array_length((v_result->>'data')::jsonb->'results'), 0)::INTEGER,
        CASE 
            WHEN v_duration_ms < 1000 THEN 'EXCELLENT (<1s)'
            WHEN v_duration_ms < 3000 THEN 'GOOD (<3s)'
            ELSE 'NEEDS_WORK'
        END::TEXT;
END;
$$ LANGUAGE plpgsql;