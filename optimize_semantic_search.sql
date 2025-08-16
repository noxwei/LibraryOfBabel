-- Ultra-Fast Semantic Search - Sub-2-Second Performance
-- LibraryOfBabel Team: Dr. Sarah Chen (陈雪芳)

-- Create HNSW index for faster vector similarity if it doesn't exist
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunk_embeddings_nomic_hnsw 
ON chunk_embeddings USING hnsw (json_to_vector_768(embedding)) 
WHERE embedding_model = 'nomic-embed-text' AND chunk_type = 'fullbook';

-- Ultra-fast semantic search with pre-filtering
CREATE OR REPLACE FUNCTION api_semantic_fullbook_search(p_query text, p_limit integer DEFAULT 20)
RETURNS json
LANGUAGE plpgsql
AS $$
DECLARE
    v_query_embedding vector(768);
    result_json json;
BEGIN
    -- Get query embedding (already fast)
    v_query_embedding := get_query_embedding_representative(p_query);
    
    IF v_query_embedding IS NULL THEN
        RETURN json_build_object('success', false, 'error', 'No embeddings available');
    END IF;
    
    -- Ultra-fast vector search with LIMIT before expensive operations
    WITH fast_vector_search AS (
        SELECT 
            ce.chunk_id,
            ce.embedding,
            (1.0 - (json_to_vector_768(ce.embedding) <=> v_query_embedding)) as raw_similarity
        FROM chunk_embeddings ce
        WHERE ce.embedding_model = 'nomic-embed-text'
            AND ce.embedding IS NOT NULL
        ORDER BY json_to_vector_768(ce.embedding) <=> v_query_embedding
        LIMIT (p_limit * 2)  -- Get 2x limit for better results
    ),
    ranked_results AS (
        SELECT 
            fvs.chunk_id,
            b.title,
            b.author,
            b.genre,
            ROUND(fvs.raw_similarity::numeric, 4) as semantic_score
        FROM fast_vector_search fvs
        JOIN chunks c ON fvs.chunk_id = c.chunk_id
        JOIN books b ON c.book_id = b.book_id
        WHERE c.chunk_type = 'fullbook'
            AND b.title IS NOT NULL
        ORDER BY fvs.raw_similarity DESC
        LIMIT p_limit
    )
    SELECT json_build_object(
        'success', true,
        'query', p_query,
        'results', json_agg(json_build_object('title', title, 'author', author, 'genre', genre, 'score', semantic_score)),
        'total_found', COUNT(*)
    ) INTO result_json
    FROM ranked_results;
    
    RETURN result_json;
END;
$$;