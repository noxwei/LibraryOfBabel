-- Test function for debugging
CREATE OR REPLACE FUNCTION test_extended_semantic_search(
    p_query TEXT,
    p_limit INTEGER DEFAULT 3
) RETURNS TABLE(
    chunk_id VARCHAR(255),
    semantic_score REAL,
    match_type TEXT,
    execution_time_ms INTEGER
) AS $$
DECLARE
    start_time TIMESTAMP := clock_timestamp();
    normalized_query TEXT;
BEGIN
    normalized_query := LOWER(TRIM(p_query));
    
    RETURN QUERY 
    SELECT c.chunk_id, 
           ts_rank(c.search_vector, plainto_tsquery('english', normalized_query))::REAL as score,
           'extended_semantic'::TEXT as match_type,
           EXTRACT(MILLISECONDS FROM (clock_timestamp() - start_time))::INTEGER as exec_time
    FROM chunks c 
    WHERE c.search_vector @@ plainto_tsquery('english', normalized_query)
    ORDER BY score DESC, c.chunk_id
    LIMIT p_limit;
    
END;
$$ LANGUAGE plpgsql;