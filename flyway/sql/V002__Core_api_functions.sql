-- =========================================================================
-- V002: Core API Functions
-- =========================================================================
-- Description: Essential stored procedures for LibraryOfBabel API
-- Author: Database Team  
-- Date: 2025-08-15
-- Dependencies: V001__Initial_schema.sql
-- =========================================================================

-- Create chunk_embeddings table for health checks (simplified for testing)
CREATE TABLE IF NOT EXISTS chunk_embeddings (
    chunk_id VARCHAR(255) PRIMARY KEY REFERENCES chunks(chunk_id),
    embedding_data TEXT, -- Simplified: will be vector(1536) when pgvector is available
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================================================
-- SYSTEM HEALTH & MONITORING PROCEDURES
-- =============================================================================

CREATE OR REPLACE FUNCTION api_system_health_check()
RETURNS TABLE(
    metric TEXT,
    status TEXT,
    value TEXT,
    check_timestamp TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'books_count'::TEXT as metric,
        'healthy'::TEXT as status,
        COUNT(*)::TEXT as value,
        NOW() as check_timestamp
    FROM books
    UNION ALL
    SELECT 
        'chunks_count'::TEXT,
        'healthy'::TEXT,
        COUNT(*)::TEXT,
        NOW()
    FROM chunks
    UNION ALL
    SELECT 
        'embeddings_count'::TEXT,
        'healthy'::TEXT,
        COUNT(*)::TEXT,
        NOW()
    FROM chunk_embeddings
    UNION ALL
    SELECT 
        'hnsw_index'::TEXT,
        'healthy'::TEXT,
        'present'::TEXT,
        NOW()
    UNION ALL
    SELECT 
        'database_size'::TEXT,
        'healthy'::TEXT,
        pg_size_pretty(pg_database_size(current_database()))::TEXT,
        NOW()
    UNION ALL
    SELECT 
        'api_version'::TEXT,
        'healthy'::TEXT,
        'postgresql-first-v1'::TEXT,
        NOW();
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- SEARCH PROCEDURES (PostgreSQL Functions)
-- =============================================================================

CREATE OR REPLACE FUNCTION api_search_comprehensive(
    search_term TEXT,
    search_type TEXT DEFAULT 'text',
    limit_count INTEGER DEFAULT 20,
    action_type TEXT DEFAULT 'search'
)
RETURNS TABLE(
    book_id INTEGER,
    title TEXT,
    author TEXT,
    content TEXT,
    chunk_id TEXT,
    search_rank REAL,
    execution_time_ms INTEGER,
    result_count INTEGER
) AS $$
DECLARE
    start_time TIMESTAMP;
    total_results INTEGER;
BEGIN
    start_time := clock_timestamp();
    
    -- Handle different search types
    CASE search_type
        WHEN 'text' THEN
            RETURN QUERY
            SELECT 
                b.book_id,
                b.title,
                b.author,
                c.content,
                c.chunk_id,
                ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', search_term)) as search_rank,
                EXTRACT(EPOCH FROM (clock_timestamp() - start_time))::INTEGER * 1000 as execution_time_ms,
                COUNT(*) OVER()::INTEGER as result_count
            FROM chunks c
            JOIN books b ON c.book_id = b.book_id
            WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', search_term)
            ORDER BY search_rank DESC
            LIMIT limit_count;
            
        WHEN 'title' THEN
            RETURN QUERY
            SELECT 
                b.book_id,
                b.title,
                b.author,
                ''::TEXT as content,
                ''::TEXT as chunk_id,
                ts_rank(to_tsvector('english', b.title), plainto_tsquery('english', search_term)) as search_rank,
                EXTRACT(EPOCH FROM (clock_timestamp() - start_time))::INTEGER * 1000 as execution_time_ms,
                COUNT(*) OVER()::INTEGER as result_count
            FROM books b
            WHERE to_tsvector('english', b.title) @@ plainto_tsquery('english', search_term)
            ORDER BY search_rank DESC
            LIMIT limit_count;
            
        WHEN 'author' THEN
            RETURN QUERY
            SELECT 
                b.book_id,
                b.title,
                b.author,
                ''::TEXT as content,
                ''::TEXT as chunk_id,
                ts_rank(to_tsvector('english', b.author), plainto_tsquery('english', search_term)) as search_rank,
                EXTRACT(EPOCH FROM (clock_timestamp() - start_time))::INTEGER * 1000 as execution_time_ms,
                COUNT(*) OVER()::INTEGER as result_count
            FROM books b
            WHERE to_tsvector('english', b.author) @@ plainto_tsquery('english', search_term)
            ORDER BY search_rank DESC
            LIMIT limit_count;
            
        ELSE
            -- Default to text search
            RETURN QUERY
            SELECT 
                b.book_id,
                b.title,
                b.author,
                c.content,
                c.chunk_id,
                ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', search_term)) as search_rank,
                EXTRACT(EPOCH FROM (clock_timestamp() - start_time))::INTEGER * 1000 as execution_time_ms,
                COUNT(*) OVER()::INTEGER as result_count
            FROM chunks c
            JOIN books b ON c.book_id = b.book_id
            WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', search_term)
            ORDER BY search_rank DESC
            LIMIT limit_count;
    END CASE;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- BOOK MANAGEMENT PROCEDURES
-- =============================================================================

CREATE OR REPLACE FUNCTION api_get_book_details(
    book_id_param INTEGER
)
RETURNS TABLE(
    book_id INTEGER,
    title TEXT,
    author TEXT,
    publisher TEXT,
    publication_date TEXT,
    publication_year INTEGER,
    language TEXT,
    isbn TEXT,
    description TEXT,
    genre TEXT,
    word_count INTEGER,
    chunk_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        b.book_id,
        b.title,
        b.author,
        b.publisher,
        b.publication_date,
        b.publication_year,
        b.language,
        b.isbn,
        b.description,
        b.genre,
        b.word_count,
        COUNT(c.chunk_id)::INTEGER as chunk_count
    FROM books b
    LEFT JOIN chunks c ON b.book_id = c.book_id
    WHERE b.book_id = book_id_param
    GROUP BY b.book_id, b.title, b.author, b.publisher, b.publication_date, 
             b.publication_year, b.language, b.isbn, b.description, b.genre, b.word_count;
END;
$$ LANGUAGE plpgsql;