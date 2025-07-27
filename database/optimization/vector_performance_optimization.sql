-- Vector Performance Optimization Suite
-- Dr. Sarah Chen (陈雪芳) - Database Systems Librarian  
-- Goal: Unleash 30GB vector data potential with HNSW indexes
-- Target: Vector searches <50ms, hybrid searches <200ms

-- ===============================================
-- 1. HNSW Vector Index Creation
-- ===============================================

-- Check current pgvector version and capabilities
SELECT extversion FROM pg_extension WHERE extname = 'vector';

-- Create high-performance HNSW indexes for different similarity metrics
-- These indexes will make vector searches 10-100x faster

-- Cosine similarity index (most common for semantic search)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunks_embedding_cosine 
ON chunks USING hnsw (embedding_array vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Inner product index (for certain ML models)  
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunks_embedding_inner_product
ON chunks USING hnsw (embedding_array vector_ip_ops)
WITH (m = 16, ef_construction = 64);

-- L2 distance index (Euclidean distance)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunks_embedding_l2
ON chunks USING hnsw (embedding_array vector_l2_ops) 
WITH (m = 16, ef_construction = 64);

-- ===============================================
-- 2. Vector Statistics and Analysis
-- ===============================================

-- Create view for vector coverage analysis
CREATE OR REPLACE VIEW vector_coverage_stats AS
SELECT 
    'Vector Coverage Analysis' as metric_type,
    COUNT(*) as total_chunks,
    COUNT(embedding_array) as vectorized_chunks,
    ROUND(COUNT(embedding_array)::float / COUNT(*)::float * 100, 2) as vector_coverage_percent,
    COUNT(DISTINCT book_id) as total_books,
    COUNT(DISTINCT CASE WHEN embedding_array IS NOT NULL THEN book_id END) as vectorized_books,
    AVG(CASE WHEN embedding_array IS NOT NULL THEN array_length(embedding_array, 1) END) as avg_vector_dimension
FROM chunks;

-- Genre-based vector distribution
CREATE OR REPLACE VIEW vector_genre_distribution AS  
SELECT 
    b.genre,
    COUNT(c.chunk_id) as total_chunks,
    COUNT(c.embedding_array) as vectorized_chunks,
    ROUND(COUNT(c.embedding_array)::float / COUNT(c.chunk_id)::float * 100, 2) as vector_coverage_percent,
    COUNT(DISTINCT b.book_id) as books_in_genre
FROM books b
LEFT JOIN chunks c ON b.book_id = c.book_id  
GROUP BY b.genre
HAVING COUNT(c.chunk_id) > 0
ORDER BY vectorized_chunks DESC;

-- Top vectorized books by author
CREATE OR REPLACE VIEW top_vectorized_content AS
SELECT 
    b.author,
    b.title,
    b.genre,
    COUNT(c.chunk_id) as total_chunks,
    COUNT(c.embedding_array) as vectorized_chunks,
    ROUND(COUNT(c.embedding_array)::float / COUNT(c.chunk_id)::float * 100, 2) as coverage_percent
FROM books b
JOIN chunks c ON b.book_id = c.book_id
WHERE c.embedding_array IS NOT NULL
GROUP BY b.book_id, b.author, b.title, b.genre
ORDER BY vectorized_chunks DESC;

-- ===============================================
-- 3. Optimized Vector Search Functions  
-- ===============================================

-- Function for semantic similarity search with performance optimization
CREATE OR REPLACE FUNCTION semantic_similarity_search(
    query_embedding float8[],
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
        1 - (c.embedding_array <=> query_embedding) as similarity_score,
        c.chapter_number,
        c.word_count
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE c.embedding_array IS NOT NULL
    AND (target_genres IS NULL OR b.genre = ANY(target_genres))
    AND (1 - (c.embedding_array <=> query_embedding)) > similarity_threshold
    ORDER BY c.embedding_array <=> query_embedding ASC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Function for hybrid search (vector + full-text fallback)
CREATE OR REPLACE FUNCTION hybrid_search(
    search_query text,
    query_embedding float8[] DEFAULT NULL,
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
    -- If we have embeddings, prioritize vector search
    IF query_embedding IS NOT NULL THEN
        RETURN QUERY
        SELECT 
            c.chunk_id,
            c.book_id,
            b.title,
            b.author,
            c.content,
            'vector'::varchar(20) as search_method,
            1 - (c.embedding_array <=> query_embedding) as relevance_score,
            c.chapter_number
        FROM chunks c
        JOIN books b ON c.book_id = b.book_id
        WHERE c.embedding_array IS NOT NULL
        AND (1 - (c.embedding_array <=> query_embedding)) > similarity_threshold
        ORDER BY c.embedding_array <=> query_embedding ASC
        LIMIT max_results;
    END IF;
    
    -- Fallback to full-text search for non-vectorized content
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
    WHERE c.embedding_array IS NULL
    AND to_tsvector('english', c.content) @@ plainto_tsquery('english', search_query)
    ORDER BY ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', search_query)) DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- ===============================================
-- 4. Cross-Book Semantic Discovery Function
-- ===============================================

-- Find semantically similar content across different books
CREATE OR REPLACE FUNCTION cross_book_semantic_discovery(
    source_book_title text,
    similarity_threshold float8 DEFAULT 0.7,
    max_results int DEFAULT 10
)
RETURNS TABLE (
    similar_book_title varchar(500),
    similar_author varchar(255),
    similar_genre varchar(100),
    avg_similarity float8,
    matching_chunks int,
    sample_content text
) AS $$
DECLARE
    source_book_id int;
BEGIN
    -- Get the source book ID
    SELECT book_id INTO source_book_id 
    FROM books 
    WHERE title ILIKE '%' || source_book_title || '%' 
    LIMIT 1;
    
    IF source_book_id IS NULL THEN
        RAISE EXCEPTION 'Book not found: %', source_book_title;
    END IF;
    
    RETURN QUERY
    WITH source_vectors AS (
        SELECT embedding_array 
        FROM chunks 
        WHERE book_id = source_book_id 
        AND embedding_array IS NOT NULL
    ),
    similarity_scores AS (
        SELECT 
            c.book_id,
            b.title,
            b.author,
            b.genre,
            c.content,
            AVG(1 - (c.embedding_array <=> sv.embedding_array)) as avg_sim,
            COUNT(*) as chunk_count
        FROM chunks c
        JOIN books b ON c.book_id = b.book_id
        CROSS JOIN source_vectors sv
        WHERE c.book_id != source_book_id
        AND c.embedding_array IS NOT NULL
        AND (1 - (c.embedding_array <=> sv.embedding_array)) > similarity_threshold
        GROUP BY c.book_id, b.title, b.author, b.genre, c.content
        HAVING COUNT(*) >= 2  -- At least 2 similar chunks
    )
    SELECT 
        ss.title,
        ss.author,
        ss.genre,
        ss.avg_sim,
        ss.chunk_count::int,
        LEFT(ss.content, 200) || '...' as sample_content
    FROM similarity_scores ss
    ORDER BY ss.avg_sim DESC, ss.chunk_count DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- ===============================================
-- 5. Performance Monitoring Views
-- ===============================================

-- Vector index usage statistics  
CREATE OR REPLACE VIEW vector_index_performance AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as times_used,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes 
WHERE indexname LIKE '%embedding%'
ORDER BY idx_scan DESC;

-- Vector search performance baseline
CREATE OR REPLACE VIEW vector_search_baseline AS
SELECT 
    'Vector Search Performance Test' as test_type,
    (
        SELECT COUNT(*) 
        FROM chunks 
        WHERE embedding_array IS NOT NULL
    ) as vectorized_chunks_count,
    (
        SELECT COUNT(DISTINCT book_id) 
        FROM chunks 
        WHERE embedding_array IS NOT NULL  
    ) as vectorized_books_count,
    NOW() as baseline_timestamp;

-- ===============================================
-- 6. Dr. Chen's Optimization Notes & Verification
-- ===============================================

COMMENT ON INDEX idx_chunks_embedding_cosine IS 
'Dr. Sarah Chen: HNSW cosine similarity index for 30GB vector data optimization';

COMMENT ON INDEX idx_chunks_embedding_inner_product IS
'Dr. Sarah Chen: HNSW inner product index for ML model compatibility';

COMMENT ON FUNCTION semantic_similarity_search IS
'Vector-first search function utilizing HNSW indexes for <50ms response times';

COMMENT ON FUNCTION hybrid_search IS
'Intelligent hybrid search: vectors for vectorized content, full-text fallback';

-- Verify optimization is working
SELECT * FROM vector_coverage_stats;
SELECT * FROM vector_genre_distribution ORDER BY vectorized_chunks DESC LIMIT 10;
SELECT * FROM top_vectorized_content LIMIT 10;

-- Test vector search performance (should be much faster now)
EXPLAIN (ANALYZE, BUFFERS) 
SELECT chunk_id, book_id, content, 
       1 - (embedding_array <=> (SELECT embedding_array FROM chunks WHERE embedding_array IS NOT NULL LIMIT 1)) as similarity
FROM chunks 
WHERE embedding_array IS NOT NULL
ORDER BY embedding_array <=> (SELECT embedding_array FROM chunks WHERE embedding_array IS NOT NULL LIMIT 1)
LIMIT 20;

-- Performance improvement summary:
-- Before: No vector indexes, linear scan of 30GB data
-- After: HNSW indexes enable logarithmic search, 10-100x improvement
-- Expected: Vector searches <50ms, cross-reference <200ms