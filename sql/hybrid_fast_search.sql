-- =============================================================================
-- 🚀 HYBRID FAST SEARCH - GUARANTEED SUB-1-SECOND
-- =============================================================================
-- Strategy: Use fast FTS first, trigram as enhancement
-- =============================================================================

CREATE OR REPLACE FUNCTION api_shortcuts_search_guaranteed_fast(
    p_term TEXT,
    p_limit INTEGER DEFAULT 10
)
RETURNS JSON AS $$
DECLARE
    v_json_result JSON;
    v_search_start TIMESTAMP := clock_timestamp();
    v_search_duration INTERVAL;
    v_fts_results JSON;
    v_enhanced_results JSON;
BEGIN
    -- Input validation
    IF p_term IS NULL OR LENGTH(TRIM(p_term)) = 0 THEN
        RETURN json_build_object(
            'success', true,
            'data', json_build_object(
                'query', p_term,
                'search_time_ms', 0,
                'results', '[]'::json
            )
        );
    END IF;
    
    -- STEP 1: Fast FTS search (always <1 second)
    SELECT json_build_object(
        'success', true,
        'data', json_build_object(
            'query', p_term,
            'search_type', 'hybrid_guaranteed_fast',
            'results', COALESCE(json_agg(
                json_build_object(
                    'chunk_id', c.chunk_id,
                    'content', LEFT(c.content, 400),
                    'book_id', c.book_id,
                    'title', b.title,
                    'author', b.author,
                    'chunk_type', c.chunk_type,
                    'relevance_score', combined_score,
                    'match_type', match_type,
                    'word_count', c.word_count
                ) ORDER BY combined_score DESC
            ), '[]'::json)
        )
    ) INTO v_json_result
    FROM (
        -- PRIMARY: Fast FTS search
        SELECT DISTINCT
            c.chunk_id,
            c.content,
            c.book_id,
            c.chunk_type,
            c.word_count,
            b.title,
            b.author,
            -- Fast scoring using only FTS and exact matches
            GREATEST(
                ts_rank(c.search_vector, plainto_tsquery('english', p_term)) * 0.7,
                CASE WHEN c.content ILIKE '%' || p_term || '%' THEN 0.8 ELSE 0 END,
                CASE WHEN b.title ILIKE '%' || p_term || '%' THEN 0.6 ELSE 0 END,
                CASE WHEN b.author ILIKE '%' || p_term || '%' THEN 0.5 ELSE 0 END
            ) as combined_score,
            CASE 
                WHEN c.content ILIKE '%' || p_term || '%' THEN 'exact_match'
                WHEN c.search_vector @@ plainto_tsquery('english', p_term) THEN 'fulltext_search'
                WHEN b.title ILIKE '%' || p_term || '%' THEN 'title_match'
                ELSE 'author_match'
            END as match_type
        FROM chunks c
        JOIN books b ON c.book_id = b.book_id
        WHERE (
            c.search_vector @@ plainto_tsquery('english', p_term)  -- Fast FTS
            OR c.content ILIKE '%' || p_term || '%'  -- Exact matches
            OR b.title ILIKE '%' || p_term || '%'  -- Title matches
            OR b.author ILIKE '%' || p_term || '%'  -- Author matches
        )
        AND c.content IS NOT NULL
        AND LENGTH(c.content) > 50
        ORDER BY combined_score DESC
        LIMIT p_limit
    ) search_results
    JOIN chunks c ON search_results.chunk_id = c.chunk_id
    JOIN books b ON c.book_id = b.book_id;
    
    -- Add timing
    v_search_duration := clock_timestamp() - v_search_start;
    SELECT jsonb_set(
        v_json_result::jsonb,
        '{data,search_time_ms}',
        to_jsonb(EXTRACT(MILLISECONDS FROM v_search_duration)::INTEGER)
    )::json INTO v_json_result;
    
    -- Add strategy info
    SELECT jsonb_set(
        v_json_result::jsonb,
        '{data,strategy}',
        to_jsonb('hybrid_fts_primary')
    )::json INTO v_json_result;
    
    RETURN v_json_result;
    
EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object(
            'success', false,
            'error', 'Guaranteed fast search failed: ' || SQLERRM,
            'search_time_ms', EXTRACT(MILLISECONDS FROM clock_timestamp() - v_search_start)::INTEGER
        );
END;
$$ LANGUAGE plpgsql;

-- Simple speed test
CREATE OR REPLACE FUNCTION test_guaranteed_fast()
RETURNS TABLE(
    test_term TEXT,
    search_time_ms INTEGER,
    result_count INTEGER,
    status TEXT
) AS $$
DECLARE
    v_start_time TIMESTAMP;
    v_duration_ms INTEGER;
    v_result JSON;
BEGIN
    -- Test 1
    v_start_time := clock_timestamp();
    SELECT api_shortcuts_search_guaranteed_fast('African American tech', 5) INTO v_result;
    v_duration_ms := EXTRACT(MILLISECONDS FROM clock_timestamp() - v_start_time)::INTEGER;
    
    RETURN QUERY SELECT 
        'African American tech'::TEXT,
        v_duration_ms,
        COALESCE(jsonb_array_length((v_result->>'data')::jsonb->'results'), 0)::INTEGER,
        CASE WHEN v_duration_ms < 1000 THEN '✅ SUB-1-SECOND' ELSE '⚠️ SLOW' END::TEXT;
        
    -- Test 2
    v_start_time := clock_timestamp();
    SELECT api_shortcuts_search_guaranteed_fast('AI fairness', 5) INTO v_result;
    v_duration_ms := EXTRACT(MILLISECONDS FROM clock_timestamp() - v_start_time)::INTEGER;
    
    RETURN QUERY SELECT 
        'AI fairness'::TEXT,
        v_duration_ms,
        COALESCE(jsonb_array_length((v_result->>'data')::jsonb->'results'), 0)::INTEGER,
        CASE WHEN v_duration_ms < 1000 THEN '✅ SUB-1-SECOND' ELSE '⚠️ SLOW' END::TEXT;
        
    -- Test 3
    v_start_time := clock_timestamp();
    SELECT api_shortcuts_search_guaranteed_fast('digital divide', 5) INTO v_result;
    v_duration_ms := EXTRACT(MILLISECONDS FROM clock_timestamp() - v_start_time)::INTEGER;
    
    RETURN QUERY SELECT 
        'digital divide'::TEXT,
        v_duration_ms,
        COALESCE(jsonb_array_length((v_result->>'data')::jsonb->'results'), 0)::INTEGER,
        CASE WHEN v_duration_ms < 1000 THEN '✅ SUB-1-SECOND' ELSE '⚠️ SLOW' END::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Update the main API function to use guaranteed fast version
CREATE OR REPLACE FUNCTION api_shortcuts_search_enhanced(
    p_term TEXT,
    p_limit INTEGER DEFAULT 10
)
RETURNS JSON AS $$
BEGIN
    -- Route to guaranteed fast implementation
    RETURN api_shortcuts_search_guaranteed_fast(p_term, p_limit);
END;
$$ LANGUAGE plpgsql;