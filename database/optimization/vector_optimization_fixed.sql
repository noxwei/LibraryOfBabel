-- Vector Performance Optimization - Fixed for PostgreSQL Arrays
-- Dr. Sarah Chen (陈雪芳) - Database Systems Librarian  
-- Converting double precision[] to proper vector type for HNSW optimization

-- ===============================================
-- 1. Add proper vector column and migrate data
-- ===============================================

-- Add new vector column with correct type
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS embedding_vector vector(768);

-- Migrate existing double precision[] arrays to vector type
UPDATE chunks 
SET embedding_vector = embedding_array::vector
WHERE embedding_array IS NOT NULL 
AND array_length(embedding_array, 1) = 768;

-- Verify migration
SELECT 
    COUNT(*) as total_chunks,
    COUNT(embedding_array) as old_embeddings,
    COUNT(embedding_vector) as new_vectors,
    'Migration Status' as status
FROM chunks;

-- ===============================================
-- 2. Create HNSW Vector Indexes (Fixed)
-- ===============================================

-- Create high-performance HNSW indexes using proper vector type
-- Cosine similarity index (most common for semantic search)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunks_vector_cosine 
ON chunks USING hnsw (embedding_vector vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Inner product index  
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunks_vector_ip
ON chunks USING hnsw (embedding_vector vector_ip_ops)
WITH (m = 16, ef_construction = 64);

-- L2 distance index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunks_vector_l2
ON chunks USING hnsw (embedding_vector vector_l2_ops) 
WITH (m = 16, ef_construction = 64);

-- ===============================================
-- 3. Vector Statistics Views (Fixed ROUND issues)
-- ===============================================

-- Vector coverage analysis
CREATE OR REPLACE VIEW vector_coverage_stats AS
SELECT 
    'Vector Coverage Analysis' as metric_type,
    COUNT(*) as total_chunks,
    COUNT(embedding_vector) as vectorized_chunks,
    ROUND((COUNT(embedding_vector)::numeric / COUNT(*)::numeric * 100), 2) as vector_coverage_percent,
    COUNT(DISTINCT book_id) as total_books,
    COUNT(DISTINCT CASE WHEN embedding_vector IS NOT NULL THEN book_id END) as vectorized_books
FROM chunks;

-- Genre-based vector distribution  
CREATE OR REPLACE VIEW vector_genre_distribution AS  
SELECT 
    b.genre,
    COUNT(c.chunk_id) as total_chunks,
    COUNT(c.embedding_vector) as vectorized_chunks,
    ROUND((COUNT(c.embedding_vector)::numeric / COUNT(c.chunk_id)::numeric * 100), 2) as vector_coverage_percent,
    COUNT(DISTINCT b.book_id) as books_in_genre
FROM books b
LEFT JOIN chunks c ON b.book_id = c.book_id  
GROUP BY b.genre
HAVING COUNT(c.chunk_id) > 0
ORDER BY vectorized_chunks DESC;

-- Top vectorized content
CREATE OR REPLACE VIEW top_vectorized_content AS
SELECT 
    b.author,
    b.title,
    b.genre,
    COUNT(c.chunk_id) as total_chunks,
    COUNT(c.embedding_vector) as vectorized_chunks,
    ROUND((COUNT(c.embedding_vector)::numeric / COUNT(c.chunk_id)::numeric * 100), 2) as coverage_percent
FROM books b
JOIN chunks c ON b.book_id = c.book_id
WHERE c.embedding_vector IS NOT NULL
GROUP BY b.book_id, b.author, b.title, b.genre
ORDER BY vectorized_chunks DESC;

-- ===============================================
-- 4. Optimized Vector Search Functions (Fixed)
-- ===============================================

-- Semantic similarity search with proper vector operations
CREATE OR REPLACE FUNCTION semantic_similarity_search_v2(
    query_embedding vector(768),
    similarity_threshold float8 DEFAULT 0.7,
    max_results int DEFAULT 20,
    target_genres text[] DEFAULT NULL
) 
RETURNS TABLE (
    chunk_id varchar(255),
    book_id int,
    title varchar(500),
    author varchar(255),
    genre varchar(100),
    content text,
    similarity_score float8,
    chapter_number int,
    word_count int
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id,
        c.book_id,
        b.title,
        b.author,
        b.genre,
        c.content,
        1 - (c.embedding_vector <=> query_embedding) as similarity_score,
        c.chapter_number,
        c.word_count
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE c.embedding_vector IS NOT NULL
    AND (target_genres IS NULL OR b.genre = ANY(target_genres))
    AND (1 - (c.embedding_vector <=> query_embedding)) > similarity_threshold
    ORDER BY c.embedding_vector <=> query_embedding ASC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Hybrid search function (vector + full-text)
CREATE OR REPLACE FUNCTION hybrid_search_v2(
    search_query text,
    query_embedding vector(768) DEFAULT NULL,
    max_results int DEFAULT 20,
    similarity_threshold float8 DEFAULT 0.6
)
RETURNS TABLE (
    chunk_id varchar(255),
    book_id int,
    title varchar(500),
    author varchar(255),
    content text,
    search_method varchar(20),
    relevance_score float8,
    chapter_number int
) AS $$
BEGIN
    -- Vector search for vectorized content
    IF query_embedding IS NOT NULL THEN
        RETURN QUERY
        SELECT 
            c.chunk_id,
            c.book_id,
            b.title,
            b.author,
            c.content,
            'vector'::varchar(20) as search_method,
            1 - (c.embedding_vector <=> query_embedding) as relevance_score,
            c.chapter_number
        FROM chunks c
        JOIN books b ON c.book_id = b.book_id
        WHERE c.embedding_vector IS NOT NULL
        AND (1 - (c.embedding_vector <=> query_embedding)) > similarity_threshold
        ORDER BY c.embedding_vector <=> query_embedding ASC
        LIMIT max_results;
        
        -- If we got enough results, return
        IF FOUND THEN
            RETURN;
        END IF;
    END IF;
    
    -- Full-text search fallback
    RETURN QUERY
    SELECT 
        c.chunk_id,
        c.book_id,
        b.title,
        b.author,
        c.content,
        'fulltext'::varchar(20) as search_method,
        ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', search_query)) as relevance_score,
        c.chapter_number
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', search_query)
    ORDER BY ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', search_query)) DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- ===============================================
-- 5. Vector-Optimized Cross-Reference Search
-- ===============================================

CREATE OR REPLACE FUNCTION vector_cross_reference_search(
    search_term text,
    query_embedding vector(768) DEFAULT NULL,
    max_results int DEFAULT 20
)
RETURNS TABLE (
    chunk_id varchar(255),
    book_id int,
    chapter_number int,
    section_number int,
    content text,
    word_count int,
    chunk_type varchar(50),
    title varchar(500),
    author varchar(255),
    book_match_count bigint,
    relevance float8
) AS $$
BEGIN
    -- Use vector search if embedding provided (much faster)
    IF query_embedding IS NOT NULL THEN
        RETURN QUERY
        SELECT 
            c.chunk_id,
            c.book_id,
            c.chapter_number,
            c.section_number,
            c.content,
            c.word_count,
            c.chunk_type,
            b.title,
            b.author,
            b.chunk_count::bigint as book_match_count,  -- Pre-computed from our earlier optimization
            1 - (c.embedding_vector <=> query_embedding) as relevance
        FROM chunks c
        JOIN books b ON c.book_id = b.book_id
        WHERE c.embedding_vector IS NOT NULL
        ORDER BY b.chunk_count DESC, c.embedding_vector <=> query_embedding ASC
        LIMIT max_results;
    ELSE
        -- Fallback to optimized tsvector search
        RETURN QUERY
        SELECT 
            c.chunk_id,
            c.book_id,
            c.chapter_number,
            c.section_number,
            c.content,
            c.word_count,
            c.chunk_type,
            b.title,
            b.author,
            b.chunk_count::bigint as book_match_count,
            ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', search_term)) as relevance
        FROM chunks c
        JOIN books b ON c.book_id = b.book_id
        WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', search_term)
        ORDER BY b.chunk_count DESC, relevance DESC
        LIMIT max_results;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ===============================================
-- 6. Performance Testing and Verification
-- ===============================================

-- Test vector search performance
EXPLAIN (ANALYZE, BUFFERS) 
SELECT chunk_id, book_id, content, 
       1 - (embedding_vector <=> (SELECT embedding_vector FROM chunks WHERE embedding_vector IS NOT NULL LIMIT 1)) as similarity
FROM chunks 
WHERE embedding_vector IS NOT NULL
ORDER BY embedding_vector <=> (SELECT embedding_vector FROM chunks WHERE embedding_vector IS NOT NULL LIMIT 1)
LIMIT 20;

-- Verify all optimizations
SELECT * FROM vector_coverage_stats;

-- Test the new vector search function
SELECT chunk_id, title, author, similarity_score 
FROM semantic_similarity_search_v2(
    (SELECT embedding_vector FROM chunks WHERE embedding_vector IS NOT NULL LIMIT 1),
    0.5, 5, NULL
);

-- Dr. Chen's performance notes
COMMENT ON COLUMN chunks.embedding_vector IS 
'Dr. Sarah Chen: Proper vector(768) type for HNSW indexes, migrated from double precision[]';

COMMENT ON FUNCTION semantic_similarity_search_v2 IS
'Optimized vector search using HNSW indexes - expected <50ms response time';

COMMENT ON FUNCTION vector_cross_reference_search IS
'Vector-first cross-reference search replacing slow window function approach';

-- Performance summary:
-- Before: double precision[] arrays with no indexes, linear scans
-- After: vector(768) with HNSW indexes, logarithmic search
-- Expected improvement: 10-100x faster vector operations
-- Cross-reference: 4-12s → <200ms
-- Vector similarity: linear → <50ms