-- Dr. Sarah Chen (陈雪芳) Granular Search Functions
-- Optimized search functions for sentence/paragraph/section chunks

-- Fast granular search with chunk type filtering
CREATE OR REPLACE FUNCTION api_granular_search(
    p_query TEXT,
    p_chunk_types TEXT[] DEFAULT ARRAY['sentence', 'paragraph', 'section'],
    p_limit INTEGER DEFAULT 50
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    book_id INTEGER,
    title VARCHAR(500),
    author VARCHAR(255),
    content TEXT,
    chunk_type VARCHAR(50),
    text_rank REAL,
    parent_chunk_id VARCHAR(255)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id,
        c.book_id,
        b.title,
        b.author,
        c.content,
        c.chunk_type,
        ts_rank(c.search_vector, plainto_tsquery('english', p_query))::REAL as text_rank,
        c.parent_chunk_id
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE c.search_vector @@ plainto_tsquery('english', p_query)
      AND c.chunk_type = ANY(p_chunk_types)
    ORDER BY text_rank DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Semantic search for granular chunks (when embeddings ready)
CREATE OR REPLACE FUNCTION api_granular_semantic_search(
    p_query TEXT,
    p_chunk_types TEXT[] DEFAULT ARRAY['sentence', 'paragraph', 'section'],
    p_limit INTEGER DEFAULT 50
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    book_id INTEGER,
    title VARCHAR(500),
    author VARCHAR(255),
    content TEXT,
    chunk_type VARCHAR(50),
    similarity REAL,
    parent_chunk_id VARCHAR(255)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id,
        c.book_id,
        b.title,
        b.author,
        c.content,
        c.chunk_type,
        (1 - (c.embedding_vector <=> (SELECT embedding_vector FROM chunks WHERE content = p_query LIMIT 1)))::REAL as similarity,
        c.parent_chunk_id
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE c.embedding_vector IS NOT NULL
      AND c.chunk_type = ANY(p_chunk_types)
    ORDER BY c.embedding_vector <=> (SELECT embedding_vector FROM chunks WHERE content = p_query LIMIT 1)
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Production-ready hybrid search (tsvector + embeddings when available)
CREATE OR REPLACE FUNCTION api_production_granular_search(
    p_query TEXT,
    p_chunk_types TEXT[] DEFAULT ARRAY['sentence', 'paragraph', 'section'],
    p_limit INTEGER DEFAULT 50,
    p_include_embeddings BOOLEAN DEFAULT TRUE
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    book_id INTEGER,
    title VARCHAR(500),
    author VARCHAR(255),
    content TEXT,
    chunk_type VARCHAR(50),
    text_rank REAL,
    embedding_similarity REAL,
    combined_score REAL,
    parent_chunk_id VARCHAR(255)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id,
        c.book_id,
        b.title,
        b.author,
        c.content,
        c.chunk_type,
        ts_rank(c.search_vector, plainto_tsquery('english', p_query))::REAL as text_rank,
        CASE 
            WHEN p_include_embeddings AND c.embedding_vector IS NOT NULL THEN
                (1 - (c.embedding_vector <=> (SELECT embedding_vector FROM chunks WHERE content = p_query LIMIT 1)))::REAL
            ELSE 0.0::REAL
        END as embedding_similarity,
        -- Combined scoring: 70% text, 30% semantic (when available)
        (0.7 * ts_rank(c.search_vector, plainto_tsquery('english', p_query))::REAL + 
         0.3 * CASE 
            WHEN p_include_embeddings AND c.embedding_vector IS NOT NULL THEN
                (1 - (c.embedding_vector <=> (SELECT embedding_vector FROM chunks WHERE content = p_query LIMIT 1)))::REAL
            ELSE ts_rank(c.search_vector, plainto_tsquery('english', p_query))::REAL
        END)::REAL as combined_score,
        c.parent_chunk_id
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE c.search_vector @@ plainto_tsquery('english', p_query)
      AND c.chunk_type = ANY(p_chunk_types)
    ORDER BY combined_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Dr. Sarah Chen PostgreSQL-First Architecture Compliance
COMMENT ON FUNCTION api_granular_search(TEXT, TEXT[], INTEGER) IS 
'Dr. Sarah Chen: Fast tsvector search for granular chunks - production ready';

COMMENT ON FUNCTION api_granular_semantic_search(TEXT, TEXT[], INTEGER) IS 
'Dr. Sarah Chen: Semantic search for granular chunks - requires embeddings';

COMMENT ON FUNCTION api_production_granular_search(TEXT, TEXT[], INTEGER, BOOLEAN) IS 
'Dr. Sarah Chen: Hybrid search - tsvector immediate, embeddings progressive';