-- =============================================================================
-- 🚀 SIMPLE GUARANTEED FAST SEARCH - SUB-1-SECOND
-- =============================================================================

CREATE OR REPLACE FUNCTION api_search_lightning_fast(
    p_term TEXT,
    p_limit INTEGER DEFAULT 10
)
RETURNS JSON AS $$
DECLARE
    v_start_time TIMESTAMP := clock_timestamp();
    v_result JSON;
BEGIN
    -- Simple, fast search without complex JOINs
    WITH fast_search AS (
        SELECT 
            c.chunk_id,
            c.content,
            c.book_id,
            c.chunk_type,
            c.word_count,
            ts_rank(c.search_vector, plainto_tsquery('english', p_term)) as score
        FROM chunks c
        WHERE c.search_vector @@ plainto_tsquery('english', p_term)
        AND c.content IS NOT NULL
        ORDER BY score DESC
        LIMIT p_limit
    ),
    with_books AS (
        SELECT 
            fs.*,
            b.title,
            b.author
        FROM fast_search fs
        JOIN books b ON fs.book_id = b.book_id
    )
    SELECT json_build_object(
        'success', true,
        'data', json_build_object(
            'query', p_term,
            'search_type', 'lightning_fast_fts',
            'search_time_ms', EXTRACT(MILLISECONDS FROM clock_timestamp() - v_start_time)::INTEGER,
            'results', json_agg(
                json_build_object(
                    'chunk_id', chunk_id,
                    'content', LEFT(content, 400),
                    'book_id', book_id,
                    'title', title,
                    'author', author,
                    'chunk_type', chunk_type,
                    'relevance_score', score,
                    'match_type', 'fulltext_search',
                    'word_count', word_count
                ) ORDER BY score DESC
            )
        )
    ) INTO v_result
    FROM with_books;
    
    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- Even simpler test
CREATE OR REPLACE FUNCTION test_lightning_speed()
RETURNS TABLE(
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
    -- Test simple term
    v_start := clock_timestamp();
    SELECT api_search_lightning_fast('technology', 3) INTO v_result;
    v_time := EXTRACT(MILLISECONDS FROM clock_timestamp() - v_start)::INTEGER;
    
    RETURN QUERY SELECT 
        'technology'::TEXT,
        v_time,
        jsonb_array_length((v_result->>'data')::jsonb->'results')::INTEGER,
        CASE WHEN v_time < 1000 THEN '🚀 FAST' ELSE '❌ SLOW' END::TEXT;
        
    -- Test compound term
    v_start := clock_timestamp();
    SELECT api_search_lightning_fast('artificial intelligence', 3) INTO v_result;
    v_time := EXTRACT(MILLISECONDS FROM clock_timestamp() - v_start)::INTEGER;
    
    RETURN QUERY SELECT 
        'artificial intelligence'::TEXT,
        v_time,
        jsonb_array_length((v_result->>'data')::jsonb->'results')::INTEGER,
        CASE WHEN v_time < 1000 THEN '🚀 FAST' ELSE '❌ SLOW' END::TEXT;
END;
$$ LANGUAGE plpgsql;