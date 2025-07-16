-- DBA AGENT: HIGH PRIORITY FIXES
-- Fix pgvector dimensions and performance testing
-- ==============================================

-- 1. Drop conflicting objects
DROP VIEW IF EXISTS vector_performance_stats CASCADE;
DROP INDEX IF EXISTS idx_embeddings_nomic_hnsw;

-- 2. Fix embedding_vector column to correct dimension (768 for nomic-embed-text)
ALTER TABLE chunk_embeddings DROP COLUMN IF EXISTS embedding_vector;
ALTER TABLE chunk_embeddings ADD COLUMN embedding_vector vector(768);

-- 3. Re-populate with correct dimensions
UPDATE chunk_embeddings 
SET embedding_vector = embedding::text::vector(768)
WHERE embedding_model = 'nomic-embed-text' AND embedding IS NOT NULL;

-- 4. Create proper HNSW index for 768-dimensional vectors
CREATE INDEX idx_embeddings_nomic_hnsw_768 
ON chunk_embeddings USING hnsw (embedding_vector vector_cosine_ops)
WHERE embedding_model = 'nomic-embed-text' AND embedding_vector IS NOT NULL;

-- 5. Performance test function with correct dimensions
CREATE OR REPLACE FUNCTION test_vector_performance(
    test_runs INTEGER DEFAULT 10
) RETURNS TABLE (
    test_type TEXT,
    avg_time_ms FLOAT,
    results_found INTEGER
) AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    i INTEGER;
    total_time FLOAT := 0;
    result_count INTEGER;
    test_vector vector(768);
BEGIN
    -- Create a test vector with correct dimensions (768)
    SELECT array_fill(0.1, ARRAY[768])::vector(768) INTO test_vector;
    
    -- Test 1: JSONB similarity (old method)
    FOR i IN 1..test_runs LOOP
        start_time := clock_timestamp();
        
        SELECT COUNT(*) INTO result_count
        FROM chunk_embeddings ce
        WHERE ce.embedding_model = 'nomic-embed-text' 
        AND ce.embedding IS NOT NULL
        LIMIT 100;
        
        end_time := clock_timestamp();
        total_time := total_time + EXTRACT(MILLISECONDS FROM (end_time - start_time));
    END LOOP;
    
    RETURN QUERY SELECT 'JSONB_baseline'::TEXT, total_time / test_runs, result_count;
    
    -- Test 2: Vector similarity (new method)
    total_time := 0;
    FOR i IN 1..test_runs LOOP
        start_time := clock_timestamp();
        
        SELECT COUNT(*) INTO result_count
        FROM chunk_embeddings ce
        WHERE ce.embedding_model = 'nomic-embed-text'
        AND ce.embedding_vector IS NOT NULL
        AND (ce.embedding_vector <=> test_vector) < 0.7
        LIMIT 100;
        
        end_time := clock_timestamp();
        total_time := total_time + EXTRACT(MILLISECONDS FROM (end_time - start_time));
    END LOOP;
    
    RETURN QUERY SELECT 'Vector_HNSW'::TEXT, total_time / test_runs, result_count;
    
    -- Test 3: Vector similarity with ordering (production use case)
    total_time := 0;
    FOR i IN 1..test_runs LOOP
        start_time := clock_timestamp();
        
        SELECT COUNT(*) INTO result_count
        FROM (
            SELECT ce.chunk_id, (1 - (ce.embedding_vector <=> test_vector)) as similarity
            FROM chunk_embeddings ce
            WHERE ce.embedding_model = 'nomic-embed-text'
            AND ce.embedding_vector IS NOT NULL
            ORDER BY similarity DESC
            LIMIT 20
        ) subq;
        
        end_time := clock_timestamp();
        total_time := total_time + EXTRACT(MILLISECONDS FROM (end_time - start_time));
    END LOOP;
    
    RETURN QUERY SELECT 'Vector_Search_Production'::TEXT, total_time / test_runs, result_count;
END;
$$ LANGUAGE plpgsql;

-- 6. Phase 2C Failure Analysis Query
CREATE OR REPLACE FUNCTION analyze_phase2c_failures()
RETURNS TABLE (
    failure_analysis TEXT,
    count BIGINT,
    percentage DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    WITH failure_stats AS (
        SELECT 
            b.book_id,
            b.title,
            b.genre,
            COUNT(ce.chunk_id) as embedding_count,
            CASE 
                WHEN COUNT(ce.chunk_id) = 0 THEN 'No embeddings created'
                WHEN COUNT(ce.chunk_id) < 3 THEN 'Insufficient embeddings'
                WHEN MAX(LENGTH(c.content)) < 100 THEN 'Content too short'
                WHEN b.genre IS NULL THEN 'Missing genre classification'
                ELSE 'Unknown failure'
            END as failure_reason
        FROM books b
        LEFT JOIN chunks c ON b.book_id = c.book_id
        LEFT JOIN chunk_embeddings ce ON c.chunk_id = ce.chunk_id 
            AND ce.embedding_model IN ('bge', 'mxbai')
        WHERE b.book_id BETWEEN 1515 AND 1889  -- Phase 2C failure range
        GROUP BY b.book_id, b.title, b.genre
    )
    SELECT 
        fs.failure_reason,
        COUNT(*) as failure_count,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as failure_percentage
    FROM failure_stats fs
    GROUP BY fs.failure_reason
    ORDER BY failure_count DESC;
END;
$$ LANGUAGE plpgsql;

-- 7. Updated performance stats view
CREATE VIEW vector_performance_stats AS
SELECT 
    embedding_model,
    COUNT(*) as total_embeddings,
    COUNT(embedding_vector) as vectorized_embeddings,
    CASE 
        WHEN COUNT(embedding_vector) > 0 
        THEN ROUND(COUNT(embedding_vector) * 100.0 / COUNT(*), 2) 
        ELSE 0 
    END as vectorization_percentage,
    COUNT(*) FILTER (WHERE embedding IS NOT NULL) as jsonb_embeddings
FROM chunk_embeddings
GROUP BY embedding_model
ORDER BY total_embeddings DESC;

COMMENT ON FUNCTION test_vector_performance IS 'DBA Agent: Test pgvector vs JSONB performance with correct dimensions';
COMMENT ON FUNCTION analyze_phase2c_failures IS 'DBA Agent: Analyze 282 Phase 2C failures for root cause';
COMMENT ON VIEW vector_performance_stats IS 'DBA Agent: Monitor vector conversion progress';