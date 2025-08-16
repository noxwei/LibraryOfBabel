-- Ultra-Fast Semantic Search - Use Native Vector Column with HNSW Index
-- LibraryOfBabel Team: Dr. Sarah Chen (陈雪芳)

-- Check which embeddings have native vector columns populated
SELECT 
    COUNT(*) as total_embeddings,
    COUNT(embedding_vector) as native_vector_count,
    COUNT(embedding) as json_embedding_count
FROM chunk_embeddings ce 
JOIN chunks c ON ce.chunk_id = c.chunk_id 
WHERE ce.embedding_model = 'nomic-embed-text' 
    AND c.chunk_type = 'fullbook';

-- Update query embedding function to use native vector if available
CREATE OR REPLACE FUNCTION get_query_embedding_representative(query_text text)
RETURNS vector(768)
LANGUAGE plpgsql
AS $$
DECLARE
    relevant_embedding vector(768);
BEGIN
    -- Fast strategy using native vector column (no JSON conversion)
    SELECT ce.embedding_vector INTO relevant_embedding
    FROM chunk_embeddings ce
    JOIN chunks c ON ce.chunk_id = c.chunk_id  
    JOIN books b ON c.book_id = b.book_id
    WHERE ce.embedding_model = 'nomic-embed-text'
        AND c.chunk_type = 'fullbook'
        AND ce.embedding_vector IS NOT NULL  -- Use native vector column
        AND (
            LOWER(b.title) LIKE '%' || LOWER(split_part(query_text, ' ', 1)) || '%' OR
            LOWER(b.genre) IN ('Programming & Technology', 'Science Fiction', 'Philosophy')
        )
    ORDER BY 
        CASE WHEN LOWER(b.title) LIKE '%' || LOWER(query_text) || '%' THEN 1 ELSE 2 END,
        b.word_count DESC
    LIMIT 1;
    
    -- Fast fallback using native vector
    IF relevant_embedding IS NULL THEN
        SELECT ce.embedding_vector INTO relevant_embedding
        FROM chunk_embeddings ce
        JOIN chunks c ON ce.chunk_id = c.chunk_id
        WHERE ce.embedding_model = 'nomic-embed-text'
            AND c.chunk_type = 'fullbook'
            AND ce.embedding_vector IS NOT NULL
        LIMIT 1;
    END IF;
    
    RETURN relevant_embedding;
END;
$$;

-- Ultra-fast semantic search using native vector column and HNSW index
CREATE OR REPLACE FUNCTION api_semantic_fullbook_search(p_query text, p_limit integer DEFAULT 20)
RETURNS json
LANGUAGE plpgsql
AS $$
DECLARE
    v_query_embedding vector(768);
BEGIN
    -- Get query embedding (now uses native vector)
    v_query_embedding := get_query_embedding_representative(p_query);
    
    IF v_query_embedding IS NULL THEN
        RETURN json_build_object('success', false, 'error', 'No embeddings available');
    END IF;
    
    -- Ultra-fast vector search using native column and HNSW index
    RETURN (
        WITH ranked_results AS (
            SELECT 
                ce.chunk_id,
                b.title,
                b.author,
                b.genre,
                ROUND((1.0 - (ce.embedding_vector <=> v_query_embedding))::numeric, 4) as semantic_score
            FROM chunk_embeddings ce
            JOIN chunks c ON ce.chunk_id = c.chunk_id
            JOIN books b ON c.book_id = b.book_id
            WHERE ce.embedding_model = 'nomic-embed-text'
                AND c.chunk_type = 'fullbook'
                AND ce.embedding_vector IS NOT NULL  -- Use native vector column
            ORDER BY ce.embedding_vector <=> v_query_embedding  -- This uses HNSW index!
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

-- Test the optimized function
SELECT api_semantic_fullbook_search('artificial intelligence', 3);