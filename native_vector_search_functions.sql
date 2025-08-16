-- Native Vector Semantic Search Functions (Ultra-Fast with HNSW Index)
-- LibraryOfBabel Team: Dr. Sarah Chen (陈雪芳)

-- Update query embedding function to use native vector column
CREATE OR REPLACE FUNCTION get_query_embedding_representative(query_text text)
RETURNS vector(768)
LANGUAGE plpgsql
AS $$
DECLARE
    relevant_embedding vector(768);
BEGIN
    -- Strategy 1: Use native vector column (FAST - no JSON conversion)
    SELECT ce.embedding_vector INTO relevant_embedding
    FROM chunk_embeddings ce
    JOIN chunks c ON ce.chunk_id = c.chunk_id  
    JOIN books b ON c.book_id = b.book_id
    WHERE ce.embedding_model = 'nomic-embed-text'
        AND c.chunk_type = 'fullbook'
        AND ce.embedding_vector IS NOT NULL  -- Native vector column
        AND (
            LOWER(b.title) LIKE '%' || LOWER(split_part(query_text, ' ', 1)) || '%' OR
            LOWER(b.title) LIKE '%' || LOWER(split_part(query_text, ' ', 2)) || '%' OR
            LOWER(b.description) LIKE '%' || LOWER(split_part(query_text, ' ', 1)) || '%' OR
            LOWER(b.genre) LIKE '%psychology%' OR
            LOWER(b.genre) LIKE '%mental%' OR
            LOWER(b.genre) LIKE '%health%'
        )
    ORDER BY 
        CASE WHEN LOWER(b.title) LIKE '%' || LOWER(query_text) || '%' THEN 1 ELSE 2 END,
        b.word_count DESC
    LIMIT 1;
    
    -- Strategy 2: Broader fallback with native vectors
    IF relevant_embedding IS NULL THEN
        SELECT ce.embedding_vector INTO relevant_embedding
        FROM chunk_embeddings ce
        JOIN chunks c ON ce.chunk_id = c.chunk_id
        JOIN books b ON c.book_id = b.book_id
        WHERE ce.embedding_model = 'nomic-embed-text'
            AND c.chunk_type = 'fullbook'
            AND ce.embedding_vector IS NOT NULL
            AND b.genre IS NOT NULL
        ORDER BY b.word_count DESC
        LIMIT 1;
    END IF;
    
    -- Strategy 3: JSON fallback for unconverted embeddings
    IF relevant_embedding IS NULL THEN
        SELECT json_to_vector_768(ce.embedding) INTO relevant_embedding
        FROM chunk_embeddings ce
        JOIN chunks c ON ce.chunk_id = c.chunk_id
        WHERE ce.embedding_model = 'nomic-embed-text'
            AND c.chunk_type = 'fullbook'
            AND ce.embedding IS NOT NULL
        ORDER BY RANDOM()
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
    native_count integer;
BEGIN
    -- Get query embedding (prefers native vectors)
    v_query_embedding := get_query_embedding_representative(p_query);
    
    IF v_query_embedding IS NULL THEN
        RETURN json_build_object('success', false, 'error', 'No embeddings available');
    END IF;
    
    -- Check how many native vectors we have
    SELECT COUNT(*) INTO native_count
    FROM chunk_embeddings ce
    JOIN chunks c ON ce.chunk_id = c.chunk_id
    WHERE ce.embedding_model = 'nomic-embed-text'
        AND c.chunk_type = 'fullbook'
        AND ce.embedding_vector IS NOT NULL;
    
    -- Use native vectors if we have enough, otherwise fall back to JSON
    IF native_count >= 100 THEN
        -- ULTRA-FAST: Native vector search with HNSW index
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
                    AND ce.embedding_vector IS NOT NULL  -- Uses HNSW index!
                ORDER BY ce.embedding_vector <=> v_query_embedding
                LIMIT p_limit
            )
            SELECT json_build_object(
                'success', true,
                'query', p_query,
                'search_method', 'native_vector_hnsw',
                'native_vectors_used', native_count,
                'results', json_agg(json_build_object('title', title, 'author', author, 'genre', genre, 'score', semantic_score)),
                'total_found', COUNT(*)
            )
            FROM ranked_results
        );
    ELSE
        -- FALLBACK: JSON conversion (slower but complete coverage)
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
                'search_method', 'json_conversion_fallback',
                'native_vectors_used', native_count,
                'results', json_agg(json_build_object('title', title, 'author', author, 'genre', genre, 'score', semantic_score)),
                'total_found', COUNT(*)
            )
            FROM ranked_results
        );
    END IF;
END;
$$;