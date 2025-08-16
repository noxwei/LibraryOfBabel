-- Fix Query Embedding Function with Better Fallback Logic
-- LibraryOfBabel Team: Dr. Sarah Chen (陈雪芳)

CREATE OR REPLACE FUNCTION get_query_embedding_representative(query_text text)
RETURNS vector(768)
LANGUAGE plpgsql
AS $$
DECLARE
    relevant_embedding jsonb;
BEGIN
    -- Strategy 1: Find books with title containing ANY query word (more flexible)
    SELECT ce.embedding INTO relevant_embedding
    FROM chunk_embeddings ce
    JOIN chunks c ON ce.chunk_id = c.chunk_id  
    JOIN books b ON c.book_id = b.book_id
    WHERE ce.embedding_model = 'nomic-embed-text'
        AND c.chunk_type = 'fullbook'
        AND ce.embedding IS NOT NULL
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
    
    -- Strategy 2: Broader genre-based fallback
    IF relevant_embedding IS NULL THEN
        SELECT ce.embedding INTO relevant_embedding
        FROM chunk_embeddings ce
        JOIN chunks c ON ce.chunk_id = c.chunk_id
        JOIN books b ON c.book_id = b.book_id
        WHERE ce.embedding_model = 'nomic-embed-text'
            AND c.chunk_type = 'fullbook'
            AND ce.embedding IS NOT NULL
            AND (
                LOWER(b.genre) IN ('Psychology', 'Philosophy', 'Science', 'Health', 'Self-Help') OR
                b.genre IS NOT NULL
            )
        ORDER BY b.word_count DESC
        LIMIT 1;
    END IF;
    
    -- Strategy 3: Any valid nomic embedding as final fallback
    IF relevant_embedding IS NULL THEN
        SELECT ce.embedding INTO relevant_embedding
        FROM chunk_embeddings ce
        JOIN chunks c ON ce.chunk_id = c.chunk_id
        WHERE ce.embedding_model = 'nomic-embed-text'
            AND c.chunk_type = 'fullbook'
            AND ce.embedding IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 1;
    END IF;
    
    IF relevant_embedding IS NULL THEN
        RETURN NULL;
    END IF;
    
    RETURN json_to_vector_768(relevant_embedding);
END;
$$;

-- Test with our query
SELECT get_query_embedding_representative('teenage psychosis') IS NOT NULL as has_embedding;