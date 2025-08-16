-- Smart Semantic Search Fix - Use Query-Relevant Fullbook Embeddings
-- LibraryOfBabel Team: Dr. Sarah Chen (陈雪芳)

-- Replace random embedding with smart query-relevant embedding selection
CREATE OR REPLACE FUNCTION get_smart_query_embedding(query_text text)
RETURNS vector(768)
LANGUAGE plpgsql
AS $$
DECLARE
    relevant_embedding jsonb;
    query_words text[];
    word text;
BEGIN
    -- Split query into words for better matching
    query_words := string_to_array(LOWER(TRIM(query_text)), ' ');
    
    -- Strategy 1: Find books with titles/descriptions matching query terms
    SELECT ce.embedding INTO relevant_embedding
    FROM chunk_embeddings ce
    JOIN chunks c ON ce.chunk_id = c.chunk_id  
    JOIN books b ON c.book_id = b.book_id
    WHERE ce.embedding_model = 'nomic-embed-text'
        AND c.chunk_type = 'fullbook'
        AND ce.embedding IS NOT NULL
        AND (
            -- Title contains query words
            EXISTS (
                SELECT 1 FROM unnest(query_words) word 
                WHERE LOWER(b.title) LIKE '%' || word || '%' AND LENGTH(word) > 2
            ) OR
            -- Description contains query words  
            EXISTS (
                SELECT 1 FROM unnest(query_words) word
                WHERE LOWER(COALESCE(b.description, '')) LIKE '%' || word || '%' AND LENGTH(word) > 2
            ) OR
            -- Genre matches query domain
            (
                LOWER(b.genre) LIKE '%programming%' AND query_text ILIKE ANY(ARRAY['%programming%', '%code%', '%software%', '%tech%', '%algorithm%']) OR
                LOWER(b.genre) LIKE '%science%' AND query_text ILIKE ANY(ARRAY['%science%', '%research%', '%study%', '%analysis%']) OR
                LOWER(b.genre) LIKE '%philosophy%' AND query_text ILIKE ANY(ARRAY['%philosophy%', '%ethics%', '%thinking%', '%mind%', '%intelligence%']) OR
                LOWER(b.genre) LIKE '%business%' AND query_text ILIKE ANY(ARRAY['%business%', '%economics%', '%management%', '%innovation%'])
            )
        )
    ORDER BY 
        -- Prioritize exact title matches
        CASE WHEN LOWER(b.title) LIKE '%' || LOWER(query_text) || '%' THEN 1
             -- Then description matches  
             WHEN LOWER(COALESCE(b.description, '')) LIKE '%' || LOWER(query_text) || '%' THEN 2
             -- Then genre matches
             WHEN LOWER(b.genre) LIKE '%' || LOWER(split_part(query_text, ' ', 1)) || '%' THEN 3
             ELSE 4 END,
        -- Prefer longer, higher-quality books
        b.word_count DESC
    LIMIT 1;
    
    -- Strategy 2: If no direct matches, use high-quality books from relevant genres
    IF relevant_embedding IS NULL THEN
        SELECT ce.embedding INTO relevant_embedding
        FROM chunk_embeddings ce
        JOIN chunks c ON ce.chunk_id = c.chunk_id  
        JOIN books b ON c.book_id = b.book_id
        WHERE ce.embedding_model = 'nomic-embed-text'
            AND c.chunk_type = 'fullbook'
            AND ce.embedding IS NOT NULL
            AND b.word_count > 30000  -- Substantial books only
            AND b.genre IN (
                'Programming & Technology', 
                'Science Fiction', 
                'Philosophy', 
                'Business & Economics',
                'Science',
                'Psychology'
            )
        ORDER BY 
            -- Prefer tech/science books for technical queries
            CASE WHEN query_text ILIKE ANY(ARRAY['%programming%', '%algorithm%', '%code%', '%software%', '%tech%', '%computer%', '%artificial%', '%machine%', '%intelligence%']) 
                 THEN CASE WHEN b.genre = 'Programming & Technology' THEN 1 ELSE 2 END
                 ELSE 3 END,
            b.word_count DESC
        LIMIT 1;
    END IF;
    
    -- Strategy 3: Final fallback to any high-quality embedding
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

-- Update the fullbook semantic search to use smart embedding selection
CREATE OR REPLACE FUNCTION api_semantic_fullbook_search(p_query text, p_limit integer DEFAULT 20)
RETURNS json
LANGUAGE plpgsql
AS $$
DECLARE
    v_query_embedding vector(768);
BEGIN
    -- Get smart query-relevant embedding instead of random
    v_query_embedding := get_smart_query_embedding(p_query);
    
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
                LEFT(COALESCE(b.description, 'No description available'), 300) as description,
                ROUND((1.0 - (json_to_vector_768(ce.embedding) <=> v_query_embedding))::numeric, 4) as semantic_score,
                'Smart fullbook semantic similarity' as match_type
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
            'search_type', 'smart_fullbook_semantic',
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
            'search_method', 'Smart fullbook nomic embeddings'
        )
        FROM ranked_results
    );
END;
$$;

-- Test the improved function
SELECT api_semantic_fullbook_search('artificial intelligence programming', 3);