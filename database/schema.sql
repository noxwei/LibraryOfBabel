-- LibraryOfBabel Database Schema
-- PostgreSQL schema for searchable book content system
-- Optimized for <100ms search performance on 1.2M+ words

-- =============================================================================
-- EXTENSIONS
-- =============================================================================

-- Enable full-text search extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;     -- Trigram matching for fuzzy search
CREATE EXTENSION IF NOT EXISTS btree_gin;  -- GIN indexes on btree types
CREATE EXTENSION IF NOT EXISTS unaccent;   -- Remove accents for search

-- =============================================================================
-- CUSTOM TYPES
-- =============================================================================

-- Enum for processing status tracking
CREATE TYPE processing_status AS ENUM ('pending', 'processing', 'completed', 'failed');

-- Enum for chunk types
CREATE TYPE chunk_type AS ENUM ('chapter', 'section', 'paragraph', 'metadata');

-- =============================================================================
-- TABLES
-- =============================================================================

-- Books table - stores book metadata and processing information
CREATE TABLE books (
    book_id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    author VARCHAR(200),
    publisher VARCHAR(200),
    publication_date DATE,
    language VARCHAR(10) DEFAULT 'en',
    isbn VARCHAR(20),
    description TEXT,
    subject VARCHAR(100),
    
    -- File and processing information
    file_path TEXT NOT NULL,
    original_filename VARCHAR(500),
    file_size_bytes BIGINT,
    
    -- Content statistics
    total_chapters INTEGER DEFAULT 0,
    total_words INTEGER DEFAULT 0,
    total_characters INTEGER DEFAULT 0,
    
    -- Processing tracking
    processing_status processing_status DEFAULT 'pending',
    processed_date TIMESTAMP WITH TIME ZONE,
    processing_time_seconds INTEGER,
    processing_version VARCHAR(10) DEFAULT '1.0',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Search vector for book metadata
    search_vector tsvector,
    
    -- Constraints
    CONSTRAINT books_title_not_empty CHECK (length(trim(title)) > 0),
    CONSTRAINT books_total_words_positive CHECK (total_words >= 0),
    CONSTRAINT books_total_chapters_positive CHECK (total_chapters >= 0)
);

-- Chunks table - stores hierarchical text content
CREATE TABLE chunks (
    chunk_id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
    
    -- Hierarchy and organization
    chunk_type chunk_type NOT NULL DEFAULT 'chapter',
    title VARCHAR(500),
    chapter_number INTEGER,
    section_number INTEGER,
    spine_order INTEGER,  -- Order in book structure
    
    -- Content
    content TEXT NOT NULL,
    content_hash VARCHAR(64), -- SHA-256 hash for deduplication
    
    -- Content statistics
    word_count INTEGER NOT NULL DEFAULT 0,
    character_count INTEGER NOT NULL DEFAULT 0,
    
    -- File reference
    file_path TEXT,
    
    -- Search optimization
    search_vector tsvector,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chunks_content_not_empty CHECK (length(trim(content)) > 0),
    CONSTRAINT chunks_word_count_positive CHECK (word_count >= 0),
    CONSTRAINT chunks_character_count_positive CHECK (character_count >= 0),
    CONSTRAINT chunks_chapter_number_positive CHECK (chapter_number IS NULL OR chapter_number > 0),
    CONSTRAINT chunks_section_number_positive CHECK (section_number IS NULL OR section_number > 0)
);

-- Search history table - track search queries for optimization
CREATE TABLE search_history (
    search_id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    query_type VARCHAR(50) DEFAULT 'fulltext', -- fulltext, semantic, fuzzy
    results_count INTEGER DEFAULT 0,
    execution_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Search parameters
    filters JSONB, -- Store filters like author, date range, etc.
    
    CONSTRAINT search_history_query_not_empty CHECK (length(trim(query_text)) > 0),
    CONSTRAINT search_history_results_positive CHECK (results_count >= 0)
);

-- Processing log table - track processing operations
CREATE TABLE processing_log (
    log_id SERIAL PRIMARY KEY,
    book_id INTEGER REFERENCES books(book_id) ON DELETE CASCADE,
    operation VARCHAR(50) NOT NULL, -- extract, chunk, index, etc.
    status processing_status NOT NULL,
    message TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Additional context
    context JSONB -- Store operation-specific data
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE (<100ms search requirement)
-- =============================================================================

-- Books table indexes
CREATE INDEX idx_books_title_gin ON books USING GIN(to_tsvector('english', title));
CREATE INDEX idx_books_author_gin ON books USING GIN(to_tsvector('english', coalesce(author, '')));
CREATE INDEX idx_books_search_vector ON books USING GIN(search_vector);
CREATE INDEX idx_books_publication_date ON books(publication_date);
CREATE INDEX idx_books_processing_status ON books(processing_status);
CREATE INDEX idx_books_total_words ON books(total_words);
CREATE INDEX idx_books_created_at ON books(created_at);

-- Chunks table indexes - critical for search performance
CREATE INDEX idx_chunks_book_id ON chunks(book_id);
CREATE INDEX idx_chunks_content_gin ON chunks USING GIN(to_tsvector('english', content));
CREATE INDEX idx_chunks_search_vector ON chunks USING GIN(search_vector);
CREATE INDEX idx_chunks_title_gin ON chunks USING GIN(to_tsvector('english', coalesce(title, '')));
CREATE INDEX idx_chunks_chunk_type ON chunks(chunk_type);
CREATE INDEX idx_chunks_chapter_number ON chunks(chapter_number);
CREATE INDEX idx_chunks_word_count ON chunks(word_count);
CREATE INDEX idx_chunks_content_hash ON chunks(content_hash);

-- Composite indexes for common queries
CREATE INDEX idx_chunks_book_chapter ON chunks(book_id, chapter_number, section_number);
CREATE INDEX idx_chunks_book_spine ON chunks(book_id, spine_order);
CREATE INDEX idx_books_author_title ON books(author, title);

-- Search history indexes
CREATE INDEX idx_search_history_query_text ON search_history USING GIN(to_tsvector('english', query_text));
CREATE INDEX idx_search_history_created_at ON search_history(created_at);
CREATE INDEX idx_search_history_execution_time ON search_history(execution_time_ms);

-- Processing log indexes
CREATE INDEX idx_processing_log_book_id ON processing_log(book_id);
CREATE INDEX idx_processing_log_created_at ON processing_log(created_at);
CREATE INDEX idx_processing_log_operation ON processing_log(operation);

-- =============================================================================
-- FUNCTIONS AND TRIGGERS
-- =============================================================================

-- Function to update search vectors
CREATE OR REPLACE FUNCTION update_search_vectors()
RETURNS TRIGGER AS $$
BEGIN
    -- Update book search vector
    IF TG_TABLE_NAME = 'books' THEN
        NEW.search_vector := 
            setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(NEW.author, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(NEW.subject, '')), 'C') ||
            setweight(to_tsvector('english', coalesce(NEW.description, '')), 'D');
    END IF;
    
    -- Update chunk search vector
    IF TG_TABLE_NAME = 'chunks' THEN
        NEW.search_vector := 
            setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(NEW.content, '')), 'B');
    END IF;
    
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers to automatically update search vectors
CREATE TRIGGER books_search_vector_update
    BEFORE INSERT OR UPDATE ON books
    FOR EACH ROW
    EXECUTE FUNCTION update_search_vectors();

CREATE TRIGGER chunks_search_vector_update
    BEFORE INSERT OR UPDATE ON chunks
    FOR EACH ROW
    EXECUTE FUNCTION update_search_vectors();

-- Function to calculate content statistics
CREATE OR REPLACE FUNCTION calculate_content_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate word and character counts
    NEW.word_count := array_length(string_to_array(trim(NEW.content), ' '), 1);
    NEW.character_count := length(NEW.content);
    
    -- Generate content hash for deduplication
    NEW.content_hash := encode(sha256(NEW.content::bytea), 'hex');
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically calculate content statistics
CREATE TRIGGER chunks_content_stats_update
    BEFORE INSERT OR UPDATE ON chunks
    FOR EACH ROW
    EXECUTE FUNCTION calculate_content_stats();

-- Function to update book statistics when chunks change
CREATE OR REPLACE FUNCTION update_book_statistics()
RETURNS TRIGGER AS $$
BEGIN
    -- Update book statistics based on chunks
    UPDATE books 
    SET 
        total_words = (
            SELECT COALESCE(SUM(word_count), 0) 
            FROM chunks 
            WHERE book_id = COALESCE(NEW.book_id, OLD.book_id)
        ),
        total_chapters = (
            SELECT COUNT(DISTINCT chapter_number) 
            FROM chunks 
            WHERE book_id = COALESCE(NEW.book_id, OLD.book_id) 
            AND chapter_number IS NOT NULL
        ),
        updated_at = NOW()
    WHERE book_id = COALESCE(NEW.book_id, OLD.book_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Triggers to update book statistics
CREATE TRIGGER chunks_update_book_stats
    AFTER INSERT OR UPDATE OR DELETE ON chunks
    FOR EACH ROW
    EXECUTE FUNCTION update_book_statistics();

-- =============================================================================
-- SEARCH FUNCTIONS
-- =============================================================================

-- High-performance search function
CREATE OR REPLACE FUNCTION search_books(
    query_text TEXT,
    result_limit INTEGER DEFAULT 10,
    offset_val INTEGER DEFAULT 0
) RETURNS TABLE(
    book_id INTEGER,
    title VARCHAR(500),
    author VARCHAR(200),
    relevance REAL,
    total_words INTEGER,
    match_type TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        b.book_id,
        b.title,
        b.author,
        ts_rank(b.search_vector, plainto_tsquery('english', query_text)) as relevance,
        b.total_words,
        'metadata' as match_type
    FROM books b
    WHERE b.search_vector @@ plainto_tsquery('english', query_text)
    ORDER BY relevance DESC, b.total_words DESC
    LIMIT result_limit OFFSET offset_val;
END;
$$ LANGUAGE plpgsql;

-- Search chunks with context
CREATE OR REPLACE FUNCTION search_content(
    query_text TEXT,
    result_limit INTEGER DEFAULT 10,
    offset_val INTEGER DEFAULT 0
) RETURNS TABLE(
    chunk_id INTEGER,
    book_id INTEGER,
    book_title VARCHAR(500),
    book_author VARCHAR(200),
    chunk_title VARCHAR(500),
    chapter_number INTEGER,
    content_snippet TEXT,
    relevance REAL,
    word_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id,
        c.book_id,
        b.title as book_title,
        b.author as book_author,
        c.title as chunk_title,
        c.chapter_number,
        LEFT(c.content, 500) as content_snippet,
        ts_rank(c.search_vector, plainto_tsquery('english', query_text)) as relevance,
        c.word_count
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE c.search_vector @@ plainto_tsquery('english', query_text)
    ORDER BY relevance DESC, c.word_count DESC
    LIMIT result_limit OFFSET offset_val;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- PERFORMANCE MONITORING
-- =============================================================================

-- View for database statistics
CREATE OR REPLACE VIEW database_stats AS
SELECT 
    'books' as table_name,
    COUNT(*) as record_count,
    SUM(total_words) as total_words,
    AVG(total_words) as avg_words_per_book,
    MAX(total_words) as max_words_per_book,
    MIN(total_words) as min_words_per_book
FROM books
WHERE processing_status = 'completed'
UNION ALL
SELECT 
    'chunks' as table_name,
    COUNT(*) as record_count,
    SUM(word_count) as total_words,
    AVG(word_count) as avg_words_per_chunk,
    MAX(word_count) as max_words_per_chunk,
    MIN(word_count) as min_words_per_chunk
FROM chunks;

-- View for search performance monitoring
CREATE OR REPLACE VIEW search_performance AS
SELECT 
    DATE(created_at) as search_date,
    COUNT(*) as search_count,
    AVG(execution_time_ms) as avg_execution_time_ms,
    MAX(execution_time_ms) as max_execution_time_ms,
    MIN(execution_time_ms) as min_execution_time_ms,
    AVG(results_count) as avg_results_count
FROM search_history
GROUP BY DATE(created_at)
ORDER BY search_date DESC;

-- =============================================================================
-- SAMPLE DATA VALIDATION
-- =============================================================================

-- Check that search indexes are working
DO $$
BEGIN
    -- Test basic search functionality
    PERFORM to_tsvector('english', 'test content');
    RAISE NOTICE 'Full-text search functionality verified';
    
    -- Check trigram extension
    PERFORM similarity('test', 'text');
    RAISE NOTICE 'Trigram search functionality verified';
    
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Search functionality validation failed: %', SQLERRM;
END $$;

-- =============================================================================
-- PERMISSIONS AND SECURITY
-- =============================================================================

-- Create read-only user for search applications
DO $$
BEGIN
    -- Create search user if not exists
    IF NOT EXISTS (SELECT 1 FROM pg_user WHERE usename = 'search_user') THEN
        CREATE USER search_user WITH PASSWORD 'search_readonly_2024';
    END IF;
    
    -- Grant necessary permissions
    GRANT CONNECT ON DATABASE knowledge_base TO search_user;
    GRANT USAGE ON SCHEMA public TO search_user;
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO search_user;
    GRANT EXECUTE ON FUNCTION search_books(TEXT, INTEGER, INTEGER) TO search_user;
    GRANT EXECUTE ON FUNCTION search_content(TEXT, INTEGER, INTEGER) TO search_user;
    
END $$;

-- =============================================================================
-- COMPLETION MESSAGE
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'LibraryOfBabel Database Schema Created Successfully';
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'Database: knowledge_base';
    RAISE NOTICE 'Tables: books (metadata), chunks (content), search_history, processing_log';
    RAISE NOTICE 'Search Functions: search_books(), search_content()';
    RAISE NOTICE 'Performance Target: <100ms search queries';
    RAISE NOTICE 'Ready for: 1.2M+ words, 913+ chunks, 14+ books';
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE '';
END $$;