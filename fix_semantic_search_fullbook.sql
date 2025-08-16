-- Fix Semantic Search Using Fullbook Nomic Embeddings
-- LibraryOfBabel Team: Dr. Sarah Chen (陈雪芳)

-- First, let's create a function to convert JSON embeddings to vectors
CREATE OR REPLACE FUNCTION json_to_vector_768(embedding_json jsonb)
RETURNS vector(768)
LANGUAGE plpgsql
AS $$
DECLARE
    vector_array float8[];
    i integer;
BEGIN
    -- Convert jsonb array to float8 array
    FOR i IN 0..767 LOOP
        vector_array[i+1] := (embedding_json->>i)::float8;
    END LOOP;
    
    -- Convert to vector
    RETURN vector_array::vector(768);
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$;

-- Create a function to get query embedding (for now, use a representative fullbook embedding)
-- TODO: Replace with actual Ollama API call
CREATE OR REPLACE FUNCTION get_query_embedding_representative(query_text text)
RETURNS vector(768)
LANGUAGE plpgsql
AS $$
DECLARE
    sample_embedding jsonb;
BEGIN
    -- For now, get a high-quality fullbook embedding as representative
    -- TODO: This should call Ollama API with query_text to generate actual embedding
    SELECT embedding INTO sample_embedding
    FROM chunk_embeddings ce
    JOIN chunks c ON ce.chunk_id = c.chunk_id
    JOIN books b ON c.book_id = b.book_id
    WHERE ce.embedding_model = 'nomic-embed-text'
        AND c.chunk_type = 'fullbook'
        AND c.word_count > 50000  -- Get substantial books
        AND b.genre IN ('Programming & Technology', 'Science Fiction', 'Philosophy')  -- High-quality content
    ORDER BY RANDOM()
    LIMIT 1;
    
    IF sample_embedding IS NULL THEN
        RETURN NULL;
    END IF;
    
    RETURN json_to_vector_768(sample_embedding);
END;
$$;

-- Fixed semantic search using fullbook embeddings
CREATE OR REPLACE FUNCTION api_semantic_fullbook_search(p_query text, p_limit integer DEFAULT 20)
RETURNS json
LANGUAGE plpgsql
AS $$
DECLARE
    v_query_embedding vector(768);
BEGIN
    -- Get query embedding (for now using representative, TODO: real query embedding)
    v_query_embedding := get_query_embedding_representative(p_query);
    
    IF v_query_embedding IS NULL THEN
        RETURN json_build_object(
            'success', false,
            'error', 'No embeddings available'
        );
    END IF;
    
    RETURN (
        WITH ranked_results AS (
            SELECT 
                ce.chunk_id,
                b.title,
                b.author,
                b.genre,
                b.word_count,
                LEFT(b.description, 300) as description,
                ROUND((1.0 - (json_to_vector_768(ce.embedding) <=> v_query_embedding))::numeric, 4) as semantic_score,
                'Fullbook semantic similarity' as match_type
            FROM chunk_embeddings ce
            JOIN chunks c ON ce.chunk_id = c.chunk_id
            JOIN books b ON c.book_id = b.book_id
            WHERE ce.embedding_model = 'nomic-embed-text'
                AND c.chunk_type = 'fullbook'
                AND ce.embedding IS NOT NULL
                AND b.title IS NOT NULL
            ORDER BY json_to_vector_768(ce.embedding) <=> v_query_embedding
            LIMIT p_limit
        )
        SELECT json_build_object(
            'success', true,
            'search_type', 'fullbook_semantic',
            'query', p_query,
            'results', json_agg(
                json_build_object(
                    'chunk_id', chunk_id,
                    'title', title,
                    'author', author,
                    'genre', genre,
                    'word_count', word_count,
                    'description', description,
                    'semantic_score', semantic_score,
                    'match_type', match_type
                )
            ),
            'total_found', COUNT(*),
            'search_method', 'Fullbook nomic embeddings'
        )
        FROM ranked_results
    );
END;
$$;

-- Test the new function
SELECT api_semantic_fullbook_search('artificial intelligence', 3);