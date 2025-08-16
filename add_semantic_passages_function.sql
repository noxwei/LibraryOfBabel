-- Add Semantic Passages Search Function
-- LibraryOfBabel Team: Dr. Sarah Chen (陈雪芳)

-- Fast semantic search for specific passages/chunks using native vectors
CREATE OR REPLACE FUNCTION api_semantic_passages_search(p_query text, p_limit integer DEFAULT 20)
RETURNS json
LANGUAGE plpgsql
AS $$
DECLARE
    v_query_embedding vector(768);
    native_count integer;
BEGIN
    -- Get query embedding (prefers native vectors)
    v_query_embedding := get_query_embedding_representative(p_query);
    
    IF v_query_embedding IS NULL THEN
        RETURN json_build_object('success', false, 'error', 'No embeddings available');
    END IF;
    
    -- Check available native vectors for passages/chunks
    SELECT COUNT(*) INTO native_count
    FROM chunk_embeddings ce
    WHERE ce.embedding_model = 'nomic-embed-text'
        AND ce.embedding_vector IS NOT NULL;
    
    -- Use native vectors for ultra-fast passage search
    IF native_count >= 100 THEN
        -- ULTRA-FAST: Native vector passage search with HNSW index
        RETURN (
            WITH ranked_passages AS (
                SELECT 
                    ce.chunk_id,
                    c.content,
                    c.chunk_type,
                    c.chunk_index,
                    b.title,
                    b.author,
                    b.genre,
                    ROUND((1.0 - (ce.embedding_vector <=> v_query_embedding))::numeric, 4) as semantic_score
                FROM chunk_embeddings ce
                JOIN chunks c ON ce.chunk_id = c.chunk_id
                JOIN books b ON c.book_id = b.book_id
                WHERE ce.embedding_model = 'nomic-embed-text'
                    AND ce.embedding_vector IS NOT NULL
                    AND c.content IS NOT NULL
                    AND LENGTH(c.content) > 50  -- Meaningful content only
                ORDER BY ce.embedding_vector <=> v_query_embedding
                LIMIT p_limit
            )
            SELECT json_build_object(
                'success', true,
                'query', p_query,
                'search_method', 'native_vector_passages_hnsw',
                'native_vectors_used', native_count,
                'results', json_agg(json_build_object(
                    'chunk_id', chunk_id,
                    'content', LEFT(content, 500) || CASE WHEN LENGTH(content) > 500 THEN '...' ELSE '' END,
                    'chunk_type', chunk_type,
                    'chunk_index', chunk_index,
                    'title', title,
                    'author', author,
                    'genre', genre,
                    'score', semantic_score
                )),
                'total_found', COUNT(*)
            )
            FROM ranked_passages
        );
    ELSE
        -- FALLBACK: JSON conversion for passages (slower but complete coverage)
        RETURN (
            WITH ranked_passages AS (
                SELECT 
                    ce.chunk_id,
                    c.content,
                    c.chunk_type,
                    c.chunk_index,
                    b.title,
                    b.author,
                    b.genre,
                    ROUND((1.0 - (json_to_vector_768(ce.embedding) <=> v_query_embedding))::numeric, 4) as semantic_score
                FROM chunk_embeddings ce
                JOIN chunks c ON ce.chunk_id = c.chunk_id
                JOIN books b ON c.book_id = b.book_id
                WHERE ce.embedding_model = 'nomic-embed-text'
                    AND ce.embedding IS NOT NULL
                    AND c.content IS NOT NULL
                    AND LENGTH(c.content) > 50
                ORDER BY json_to_vector_768(ce.embedding) <=> v_query_embedding
                LIMIT p_limit
            )
            SELECT json_build_object(
                'success', true,
                'query', p_query,
                'search_method', 'json_conversion_passages_fallback',
                'native_vectors_used', native_count,
                'results', json_agg(json_build_object(
                    'chunk_id', chunk_id,
                    'content', LEFT(content, 500) || CASE WHEN LENGTH(content) > 500 THEN '...' ELSE '' END,
                    'chunk_type', chunk_type,
                    'chunk_index', chunk_index,
                    'title', title,
                    'author', author,
                    'genre', genre,
                    'score', semantic_score
                )),
                'total_found', COUNT(*)
            )
            FROM ranked_passages
        );
    END IF;
END;
$$;

-- Test the new passages function
SELECT api_semantic_passages_search('artificial intelligence', 3);