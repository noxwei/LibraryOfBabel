-- Optimize Semantic Search Without Index Creation
-- LibraryOfBabel Team: Dr. Sarah Chen (陈雪芳)

-- Optimize the semantic search by reducing joins and using better query structure
CREATE OR REPLACE FUNCTION api_semantic_fullbook_search(p_query text, p_limit integer DEFAULT 20)
RETURNS json
LANGUAGE plpgsql
AS $$
DECLARE
    v_query_embedding vector(768);
BEGIN
    -- Get query embedding (fast title-based lookup)
    v_query_embedding := get_query_embedding_representative(p_query);
    
    IF v_query_embedding IS NULL THEN
        RETURN json_build_object('success', false, 'error', 'No embeddings available');
    END IF;
    
    -- Optimized search: filter by embedding model first, then vector similarity
    RETURN (
        WITH filtered_embeddings AS (
            -- Pre-filter by model and non-null embeddings (fast index scan)
            SELECT 
                ce.chunk_id,
                ce.embedding,
                c.book_id
            FROM chunk_embeddings ce
            JOIN chunks c ON ce.chunk_id = c.chunk_id
            WHERE ce.embedding_model = 'nomic-embed-text'
                AND c.chunk_type = 'fullbook'
                AND ce.embedding IS NOT NULL
        ),
        vector_similarities AS (
            -- Compute similarities only on pre-filtered set
            SELECT 
                fe.chunk_id,
                fe.book_id,
                (1.0 - (json_to_vector_768(fe.embedding) <=> v_query_embedding)) as similarity
            FROM filtered_embeddings fe
            ORDER BY json_to_vector_768(fe.embedding) <=> v_query_embedding
            LIMIT p_limit
        ),
        ranked_results AS (
            -- Join with book metadata only for top results
            SELECT 
                vs.chunk_id,
                b.title,
                b.author,
                b.genre,
                ROUND(vs.similarity::numeric, 4) as semantic_score
            FROM vector_similarities vs
            JOIN books b ON vs.book_id = b.book_id
            ORDER BY vs.similarity DESC
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

-- Test the optimized function
\timing on
SELECT api_semantic_fullbook_search('teenage psychosis', 3);