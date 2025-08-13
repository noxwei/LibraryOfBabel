-- =============================================================================
-- 🚀 SIMPLE WORKING FAST SEARCH
-- =============================================================================

CREATE OR REPLACE FUNCTION api_search_simple_fast(
    p_term TEXT,
    p_limit INTEGER DEFAULT 10
)
RETURNS JSON AS $$
DECLARE
    v_start_time TIMESTAMP := clock_timestamp();
    v_result_array JSON[];
    v_chunk_record RECORD;
    v_count INTEGER := 0;
BEGIN
    -- Initialize array
    v_result_array := ARRAY[]::JSON[];
    
    -- Simple loop approach for guaranteed performance
    FOR v_chunk_record IN 
        SELECT 
            c.chunk_id,
            LEFT(c.content, 400) as content_preview,
            c.book_id,
            c.chunk_type,
            c.word_count,
            b.title,
            b.author,
            ts_rank(c.search_vector, plainto_tsquery('english', p_term)) as score
        FROM chunks c
        JOIN books b ON c.book_id = b.book_id
        WHERE c.search_vector @@ plainto_tsquery('english', p_term)
        AND c.chunk_type = 'chapter'
        AND c.content IS NOT NULL
        AND c.word_count > 100
        ORDER BY ts_rank(c.search_vector, plainto_tsquery('english', p_term)) DESC
        LIMIT p_limit
    LOOP
        v_count := v_count + 1;
        v_result_array := v_result_array || json_build_object(
            'chunk_id', v_chunk_record.chunk_id,
            'content', v_chunk_record.content_preview,
            'book_id', v_chunk_record.book_id,
            'title', v_chunk_record.title,
            'author', v_chunk_record.author,
            'chunk_type', v_chunk_record.chunk_type,
            'relevance_score', v_chunk_record.score,
            'match_type', 'chapter_fts',
            'word_count', v_chunk_record.word_count
        );
    END LOOP;
    
    RETURN json_build_object(
        'success', true,
        'data', json_build_object(
            'query', p_term,
            'search_type', 'simple_fast_chapters',
            'search_time_ms', EXTRACT(MILLISECONDS FROM clock_timestamp() - v_start_time)::INTEGER,
            'total_results', v_count,
            'results', array_to_json(v_result_array)
        )
    );
END;
$$ LANGUAGE plpgsql;

-- Simple test function
CREATE OR REPLACE FUNCTION test_simple_speed()
RETURNS TEXT AS $$
DECLARE
    v_start TIMESTAMP;
    v_result JSON;
    v_time INTEGER;
    v_count INTEGER;
BEGIN
    v_start := clock_timestamp();
    SELECT api_search_simple_fast('technology', 3) INTO v_result;
    v_time := EXTRACT(MILLISECONDS FROM clock_timestamp() - v_start)::INTEGER;
    v_count := (v_result->'data'->>'total_results')::INTEGER;
    
    RETURN 'Time: ' || v_time || 'ms | Results: ' || v_count || ' | Status: ' || 
           CASE WHEN v_time < 1000 THEN '🚀 FAST' ELSE '❌ SLOW' END;
END;
$$ LANGUAGE plpgsql;

-- Update main API function
CREATE OR REPLACE FUNCTION api_shortcuts_search_enhanced(
    p_term TEXT,
    p_limit INTEGER DEFAULT 10
)
RETURNS JSON AS $$
BEGIN
    RETURN api_search_simple_fast(p_term, p_limit);
END;
$$ LANGUAGE plpgsql;