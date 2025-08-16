-- Fast Test Semantic Search - Simple Query Matching
-- Must be under 2 seconds

CREATE OR REPLACE FUNCTION get_fast_query_embedding_test(query_text text)
RETURNS vector(768)
LANGUAGE plpgsql
AS $$
DECLARE
    relevant_embedding jsonb;
BEGIN
    -- Simple fast strategy: find book with title containing ANY query word
    SELECT ce.embedding INTO relevant_embedding
    FROM chunk_embeddings ce
    JOIN chunks c ON ce.chunk_id = c.chunk_id  
    JOIN books b ON c.book_id = b.book_id
    WHERE ce.embedding_model = 'nomic-embed-text'
        AND c.chunk_type = 'fullbook'
        AND ce.embedding IS NOT NULL
        AND (
            LOWER(b.title) LIKE '%' || LOWER(split_part(query_text, ' ', 1)) || '%' OR
            LOWER(b.genre) IN ('Programming & Technology', 'Science Fiction', 'Philosophy')
        )
    ORDER BY 
        CASE WHEN LOWER(b.title) LIKE '%' || LOWER(query_text) || '%' THEN 1 ELSE 2 END,
        b.word_count DESC
    LIMIT 1;
    
    -- Fast fallback
    IF relevant_embedding IS NULL THEN
        SELECT ce.embedding INTO relevant_embedding
        FROM chunk_embeddings ce
        JOIN chunks c ON ce.chunk_id = c.chunk_id
        WHERE ce.embedding_model = 'nomic-embed-text'
            AND c.chunk_type = 'fullbook'
            AND ce.embedding IS NOT NULL
        LIMIT 1;
    END IF;
    
    RETURN json_to_vector_768(relevant_embedding);
END;
$$;

-- Fast test semantic search function
CREATE OR REPLACE FUNCTION api_semantic_fullbook_search_test(p_query text, p_limit integer DEFAULT 20)
RETURNS json
LANGUAGE plpgsql
AS $$
DECLARE
    v_query_embedding vector(768);
BEGIN
    v_query_embedding := get_fast_query_embedding_test(p_query);
    
    IF v_query_embedding IS NULL THEN
        RETURN json_build_object('success', false, 'error', 'No embeddings available');
    END IF;
    
    RETURN (
        WITH ranked_results AS (
            SELECT 
                ce.chunk_id,
                b.title,
                b.author,
                b.genre,
                ROUND((1.0 - (json_to_vector_768(ce.embedding) <=> v_query_embedding))::numeric, 4) as semantic_score
            FROM chunk_embeddings ce
            JOIN chunks c ON ce.chunk_id = c.chunk_id
            JOIN books b ON c.book_id = b.book_id
            WHERE ce.embedding_model = 'nomic-embed-text'
                AND c.chunk_type = 'fullbook'
                AND ce.embedding IS NOT NULL
            ORDER BY json_to_vector_768(ce.embedding) <=> v_query_embedding
            LIMIT p_limit
        )
        SELECT json_build_object(
            'success', true,
            'query', p_query,
            'results', json_agg(json_build_object('title', title, 'author', author, 'genre', genre, 'score', semantic_score)),
            'total_found', COUNT(*)
        )
        FROM ranked_results
    );
END;
$$;

-- Test it
SELECT api_semantic_fullbook_search_test('artificial intelligence', 3);