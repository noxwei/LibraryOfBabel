-- =============================================================================
-- Dr. Elena Rodriguez - Description Enhancement PostgreSQL Functions
-- =============================================================================
--
-- Enhanced book description and metadata system with Calibre integration
-- Supports multi-tier description fetching and EPUB library organization
--
-- Architecture: Dr. Sarah Chen (陈雪芳) PostgreSQL-First principles
-- Performance: Optimized for 3,896 books missing descriptions
-- Sources: Calibre → Open Library → Google Books → AI Content Analysis
--
-- Author: Dr. Elena Rodriguez - Digital Content Curator
-- Integration: LibraryOfBabel Enhanced Description System
-- =============================================================================

-- =============================================================================
-- DESCRIPTION ENHANCEMENT TRACKING
-- =============================================================================

-- Table to track description enhancement attempts and results
CREATE TABLE IF NOT EXISTS dr_elena_description_enhancement_log (
    log_id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(book_id),
    enhancement_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_attempted VARCHAR(50) NOT NULL, -- 'calibre', 'open_library', 'google_books', 'content_analysis'
    success BOOLEAN NOT NULL DEFAULT FALSE,
    confidence_score DECIMAL(5,2) DEFAULT 0.00,
    description_length INTEGER,
    error_message TEXT,
    metadata_json JSONB, -- Store additional metadata found
    processing_time_ms INTEGER
);

-- Index for efficient lookups
CREATE INDEX IF NOT EXISTS idx_description_log_book_id ON dr_elena_description_enhancement_log(book_id);
CREATE INDEX IF NOT EXISTS idx_description_log_source ON dr_elena_description_enhancement_log(source_attempted);
CREATE INDEX IF NOT EXISTS idx_description_log_success ON dr_elena_description_enhancement_log(success);

-- =============================================================================
-- EPUB MIGRATION TRACKING
-- =============================================================================

-- Table to track EPUB migration to Calibre Library
CREATE TABLE IF NOT EXISTS dr_elena_epub_migration_log (
    migration_id SERIAL PRIMARY KEY,
    book_id INTEGER REFERENCES books(book_id),
    original_epub_path TEXT NOT NULL,
    calibre_library_path TEXT,
    migration_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    migration_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'completed', 'failed'
    calibre_book_id INTEGER, -- Calibre's internal book ID
    metadata_enhanced BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    file_size_bytes BIGINT,
    processing_time_ms INTEGER
);

CREATE INDEX IF NOT EXISTS idx_epub_migration_book_id ON dr_elena_epub_migration_log(book_id);
CREATE INDEX IF NOT EXISTS idx_epub_migration_status ON dr_elena_epub_migration_log(migration_status);

-- =============================================================================
-- DESCRIPTION ENHANCEMENT FUNCTIONS
-- =============================================================================

CREATE OR REPLACE FUNCTION dr_elena_get_books_needing_descriptions(p_limit INTEGER DEFAULT 50)
RETURNS TABLE(
    book_id INTEGER,
    title TEXT,
    author TEXT,
    isbn TEXT,
    has_isbn BOOLEAN,
    priority_score DECIMAL(5,2),
    last_attempt_date TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    WITH book_priorities AS (
        SELECT 
            b.book_id,
            b.title,
            b.author,
            b.isbn,
            (b.isbn IS NOT NULL AND LENGTH(TRIM(b.isbn)) > 0) as has_isbn,
            -- Priority scoring: ISBN books get higher priority
            CASE 
                WHEN b.isbn IS NOT NULL AND LENGTH(TRIM(b.isbn)) > 0 THEN 100.0
                WHEN b.publication_year IS NOT NULL THEN 75.0
                WHEN b.genre IS NOT NULL THEN 50.0
                ELSE 25.0
            END as priority_score,
            -- Get last attempt timestamp
            (SELECT MAX(enhancement_timestamp) 
             FROM dr_elena_description_enhancement_log 
             WHERE book_id = b.book_id) as last_attempt_date
        FROM books b
        WHERE (b.description IS NULL OR LENGTH(TRIM(b.description)) = 0)
        AND NOT EXISTS (
            -- Don't retry books that failed all sources in last 7 days
            SELECT 1 FROM dr_elena_description_enhancement_log del
            WHERE del.book_id = b.book_id 
            AND del.enhancement_timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days'
            AND del.source_attempted = 'content_analysis'
            AND del.success = FALSE
        )
    )
    SELECT 
        bp.book_id,
        bp.title,
        bp.author,
        bp.isbn,
        bp.has_isbn,
        bp.priority_score,
        bp.last_attempt_date
    FROM book_priorities bp
    ORDER BY bp.priority_score DESC, bp.book_id ASC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION dr_elena_log_description_enhancement(
    p_book_id INTEGER,
    p_source_attempted VARCHAR(50),
    p_success BOOLEAN,
    p_confidence_score DECIMAL(5,2) DEFAULT 0.00,
    p_description TEXT DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL,
    p_metadata_json JSONB DEFAULT NULL,
    p_processing_time_ms INTEGER DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_description_length INTEGER := 0;
BEGIN
    -- Calculate description length if provided
    IF p_description IS NOT NULL THEN
        v_description_length := LENGTH(p_description);
    END IF;
    
    -- Insert enhancement log
    INSERT INTO dr_elena_description_enhancement_log (
        book_id,
        source_attempted,
        success,
        confidence_score,
        description_length,
        error_message,
        metadata_json,
        processing_time_ms
    ) VALUES (
        p_book_id,
        p_source_attempted,
        p_success,
        p_confidence_score,
        v_description_length,
        p_error_message,
        p_metadata_json,
        p_processing_time_ms
    );
    
    -- If successful, update the book record
    IF p_success AND p_description IS NOT NULL THEN
        UPDATE books 
        SET description = p_description,
            -- Update other metadata if provided in JSON
            genre = COALESCE(
                CASE WHEN p_metadata_json ? 'genre' THEN p_metadata_json->>'genre' END,
                genre
            ),
            publication_year = COALESCE(
                CASE WHEN p_metadata_json ? 'publication_year' THEN (p_metadata_json->>'publication_year')::INTEGER END,
                publication_year
            ),
            publisher = COALESCE(
                CASE WHEN p_metadata_json ? 'publisher' THEN p_metadata_json->>'publisher' END,
                publisher
            ),
            isbn = COALESCE(
                CASE WHEN p_metadata_json ? 'isbn' THEN p_metadata_json->>'isbn' END,
                isbn
            )
        WHERE book_id = p_book_id;
    END IF;
    
    RETURN TRUE;
    
EXCEPTION WHEN OTHERS THEN
    -- Log the error but don't fail the transaction
    RAISE WARNING 'Failed to log description enhancement for book %: %', p_book_id, SQLERRM;
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION dr_elena_update_book_metadata(
    p_book_id INTEGER,
    p_description TEXT DEFAULT NULL,
    p_genre TEXT DEFAULT NULL,
    p_publication_year INTEGER DEFAULT NULL,
    p_publisher TEXT DEFAULT NULL,
    p_isbn TEXT DEFAULT NULL,
    p_language TEXT DEFAULT NULL,
    p_page_count INTEGER DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE books 
    SET description = COALESCE(p_description, description),
        genre = COALESCE(p_genre, genre),
        publication_year = COALESCE(p_publication_year, publication_year),
        publisher = COALESCE(p_publisher, publisher),
        isbn = COALESCE(p_isbn, isbn),
        -- Store additional metadata in a JSON field if it exists
        metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
            'language', COALESCE(p_language, (metadata->>'language')),
            'page_count', COALESCE(p_page_count, (metadata->>'page_count')::INTEGER),
            'last_enhanced', CURRENT_TIMESTAMP
        )
    WHERE book_id = p_book_id;
    
    RETURN FOUND;
    
EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'Failed to update book metadata for book %: %', p_book_id, SQLERRM;
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- EPUB MIGRATION FUNCTIONS
-- =============================================================================

CREATE OR REPLACE FUNCTION dr_elena_log_epub_migration(
    p_book_id INTEGER,
    p_original_epub_path TEXT,
    p_calibre_library_path TEXT DEFAULT NULL,
    p_migration_status VARCHAR(20) DEFAULT 'pending',
    p_calibre_book_id INTEGER DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL,
    p_file_size_bytes BIGINT DEFAULT NULL,
    p_processing_time_ms INTEGER DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    v_migration_id INTEGER;
BEGIN
    INSERT INTO dr_elena_epub_migration_log (
        book_id,
        original_epub_path,
        calibre_library_path,
        migration_status,
        calibre_book_id,
        error_message,
        file_size_bytes,
        processing_time_ms
    ) VALUES (
        p_book_id,
        p_original_epub_path,
        p_calibre_library_path,
        p_migration_status,
        p_calibre_book_id,
        p_error_message,
        p_file_size_bytes,
        p_processing_time_ms
    ) RETURNING migration_id INTO v_migration_id;
    
    RETURN v_migration_id;
    
EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'Failed to log EPUB migration for book %: %', p_book_id, SQLERRM;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION dr_elena_get_books_for_epub_migration(p_limit INTEGER DEFAULT 50)
RETURNS TABLE(
    book_id INTEGER,
    title TEXT,
    author TEXT,
    epub_filename TEXT,
    migration_attempted BOOLEAN,
    last_migration_attempt TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        b.book_id,
        b.title,
        b.author,
        b.epub_filename,
        EXISTS(
            SELECT 1 FROM dr_elena_epub_migration_log eml 
            WHERE eml.book_id = b.book_id
        ) as migration_attempted,
        (SELECT MAX(migration_timestamp) 
         FROM dr_elena_epub_migration_log eml2 
         WHERE eml2.book_id = b.book_id) as last_migration_attempt
    FROM books b
    WHERE b.epub_filename IS NOT NULL
    AND NOT EXISTS (
        -- Don't retry books that completed migration
        SELECT 1 FROM dr_elena_epub_migration_log eml3
        WHERE eml3.book_id = b.book_id 
        AND eml3.migration_status = 'completed'
    )
    ORDER BY b.book_id
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- REPORTING AND ANALYTICS FUNCTIONS
-- =============================================================================

CREATE OR REPLACE FUNCTION dr_elena_description_enhancement_summary()
RETURNS TABLE(
    metric_name TEXT,
    current_value BIGINT,
    status TEXT,
    details JSONB
) AS $$
BEGIN
    RETURN QUERY
    -- Total books without descriptions
    SELECT 
        'Books Without Descriptions'::TEXT,
        COUNT(*)::BIGINT,
        CASE WHEN COUNT(*) = 0 THEN 'Complete' ELSE 'In Progress' END::TEXT,
        jsonb_build_object(
            'percentage_missing', ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM books)), 2),
            'priority_breakdown', jsonb_build_object(
                'with_isbn', (SELECT COUNT(*) FROM books WHERE (description IS NULL OR LENGTH(TRIM(description)) = 0) AND isbn IS NOT NULL),
                'without_isbn', (SELECT COUNT(*) FROM books WHERE (description IS NULL OR LENGTH(TRIM(description)) = 0) AND isbn IS NULL)
            )
        )
    FROM books 
    WHERE description IS NULL OR LENGTH(TRIM(description)) = 0
    
    UNION ALL
    
    -- Enhancement attempts by source
    SELECT 
        'Calibre Successes'::TEXT,
        COUNT(*)::BIGINT,
        'Info'::TEXT,
        jsonb_build_object(
            'avg_confidence', ROUND(AVG(confidence_score), 2),
            'avg_description_length', ROUND(AVG(description_length), 0)
        )
    FROM dr_elena_description_enhancement_log 
    WHERE source_attempted = 'calibre' AND success = TRUE
    
    UNION ALL
    
    SELECT 
        'Open Library Successes'::TEXT,
        COUNT(*)::BIGINT,
        'Info'::TEXT,
        jsonb_build_object(
            'avg_confidence', ROUND(AVG(confidence_score), 2),
            'avg_description_length', ROUND(AVG(description_length), 0)
        )
    FROM dr_elena_description_enhancement_log 
    WHERE source_attempted = 'open_library' AND success = TRUE
    
    UNION ALL
    
    SELECT 
        'Google Books Successes'::TEXT,
        COUNT(*)::BIGINT,
        'Info'::TEXT,
        jsonb_build_object(
            'avg_confidence', ROUND(AVG(confidence_score), 2),
            'avg_description_length', ROUND(AVG(description_length), 0)
        )
    FROM dr_elena_description_enhancement_log 
    WHERE source_attempted = 'google_books' AND success = TRUE
    
    UNION ALL
    
    SELECT 
        'Content Analysis Successes'::TEXT,
        COUNT(*)::BIGINT,
        'Info'::TEXT,
        jsonb_build_object(
            'avg_confidence', ROUND(AVG(confidence_score), 2),
            'avg_description_length', ROUND(AVG(description_length), 0)
        )
    FROM dr_elena_description_enhancement_log 
    WHERE source_attempted = 'content_analysis' AND success = TRUE
    
    UNION ALL
    
    -- EPUB Migration Status
    SELECT 
        'EPUBs Migrated to Calibre'::TEXT,
        COUNT(*)::BIGINT,
        CASE WHEN COUNT(*) > 0 THEN 'Active' ELSE 'Pending' END::TEXT,
        jsonb_build_object(
            'completed', (SELECT COUNT(*) FROM dr_elena_epub_migration_log WHERE migration_status = 'completed'),
            'failed', (SELECT COUNT(*) FROM dr_elena_epub_migration_log WHERE migration_status = 'failed'),
            'pending', (SELECT COUNT(*) FROM dr_elena_epub_migration_log WHERE migration_status = 'pending')
        )
    FROM dr_elena_epub_migration_log;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION dr_elena_recent_enhancement_activity(p_days INTEGER DEFAULT 7)
RETURNS TABLE(
    book_id INTEGER,
    title TEXT,
    author TEXT,
    source_used TEXT,
    success BOOLEAN,
    confidence_score DECIMAL(5,2),
    description_length INTEGER,
    enhancement_timestamp TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        del.book_id,
        b.title,
        b.author,
        del.source_attempted,
        del.success,
        del.confidence_score,
        del.description_length,
        del.enhancement_timestamp
    FROM dr_elena_description_enhancement_log del
    JOIN books b ON del.book_id = b.book_id
    WHERE del.enhancement_timestamp > CURRENT_TIMESTAMP - (p_days || ' days')::INTERVAL
    ORDER BY del.enhancement_timestamp DESC;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- BATCH PROCESSING FUNCTIONS
-- =============================================================================

CREATE OR REPLACE FUNCTION dr_elena_get_next_enhancement_batch(p_batch_size INTEGER DEFAULT 50)
RETURNS TABLE(
    book_id INTEGER,
    title TEXT,
    author TEXT,
    isbn TEXT,
    priority_score DECIMAL(5,2),
    suggested_sources TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    WITH prioritized_books AS (
        SELECT 
            b.book_id,
            b.title,
            b.author,
            b.isbn,
            CASE 
                WHEN b.isbn IS NOT NULL AND LENGTH(TRIM(b.isbn)) > 0 THEN 100.0
                WHEN b.publication_year IS NOT NULL THEN 75.0
                WHEN b.genre IS NOT NULL THEN 50.0
                ELSE 25.0
            END as priority_score,
            -- Determine which sources to try based on available metadata
            CASE 
                WHEN b.isbn IS NOT NULL AND LENGTH(TRIM(b.isbn)) > 0 
                THEN ARRAY['calibre', 'open_library', 'google_books', 'content_analysis']
                WHEN b.publication_year IS NOT NULL 
                THEN ARRAY['calibre', 'open_library', 'google_books', 'content_analysis']
                ELSE ARRAY['calibre', 'content_analysis']
            END as suggested_sources
        FROM books b
        WHERE (b.description IS NULL OR LENGTH(TRIM(b.description)) = 0)
        AND NOT EXISTS (
            -- Skip books that failed all attempts recently
            SELECT 1 FROM dr_elena_description_enhancement_log del
            WHERE del.book_id = b.book_id 
            AND del.enhancement_timestamp > CURRENT_TIMESTAMP - INTERVAL '3 days'
            AND del.source_attempted = 'content_analysis'
            AND del.success = FALSE
        )
    )
    SELECT 
        pb.book_id,
        pb.title,
        pb.author,
        pb.isbn,
        pb.priority_score,
        pb.suggested_sources
    FROM prioritized_books pb
    ORDER BY pb.priority_score DESC, pb.book_id ASC
    LIMIT p_batch_size;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- UTILITY FUNCTIONS FOR MAINTENANCE
-- =============================================================================

CREATE OR REPLACE FUNCTION dr_elena_cleanup_enhancement_logs(p_days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    -- Keep only recent logs and successful enhancements
    DELETE FROM dr_elena_description_enhancement_log 
    WHERE enhancement_timestamp < CURRENT_TIMESTAMP - (p_days_to_keep || ' days')::INTERVAL
    AND success = FALSE;
    
    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    
    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- GRANT PERMISSIONS
-- =============================================================================

-- Grant permissions for API access
GRANT SELECT, INSERT, UPDATE ON dr_elena_description_enhancement_log TO weixiangzhang;
GRANT SELECT, INSERT, UPDATE ON dr_elena_epub_migration_log TO weixiangzhang;
GRANT USAGE ON SEQUENCE dr_elena_description_enhancement_log_log_id_seq TO weixiangzhang;
GRANT USAGE ON SEQUENCE dr_elena_epub_migration_log_migration_id_seq TO weixiangzhang;

GRANT EXECUTE ON FUNCTION dr_elena_get_books_needing_descriptions(INTEGER) TO weixiangzhang;
GRANT EXECUTE ON FUNCTION dr_elena_log_description_enhancement(INTEGER, VARCHAR, BOOLEAN, DECIMAL, TEXT, TEXT, JSONB, INTEGER) TO weixiangzhang;
GRANT EXECUTE ON FUNCTION dr_elena_update_book_metadata(INTEGER, TEXT, TEXT, INTEGER, TEXT, TEXT, TEXT, INTEGER) TO weixiangzhang;
GRANT EXECUTE ON FUNCTION dr_elena_log_epub_migration(INTEGER, TEXT, TEXT, VARCHAR, INTEGER, TEXT, BIGINT, INTEGER) TO weixiangzhang;
GRANT EXECUTE ON FUNCTION dr_elena_get_books_for_epub_migration(INTEGER) TO weixiangzhang;
GRANT EXECUTE ON FUNCTION dr_elena_description_enhancement_summary() TO weixiangzhang;
GRANT EXECUTE ON FUNCTION dr_elena_recent_enhancement_activity(INTEGER) TO weixiangzhang;
GRANT EXECUTE ON FUNCTION dr_elena_get_next_enhancement_batch(INTEGER) TO weixiangzhang;
GRANT EXECUTE ON FUNCTION dr_elena_cleanup_enhancement_logs(INTEGER) TO weixiangzhang;

-- =============================================================================
-- USAGE EXAMPLES
-- =============================================================================

/*
-- Example Usage:

-- 1. Get books needing descriptions (prioritizes ISBN books)
SELECT * FROM dr_elena_get_books_needing_descriptions(25);

-- 2. Log a successful description enhancement
SELECT dr_elena_log_description_enhancement(
    123, 'calibre', TRUE, 0.95, 
    'This fascinating novel explores...', NULL,
    '{"genre": "Science Fiction", "publication_year": 2023}'::jsonb,
    2500
);

-- 3. Get enhancement summary
SELECT * FROM dr_elena_description_enhancement_summary();

-- 4. View recent enhancement activity
SELECT * FROM dr_elena_recent_enhancement_activity(7);

-- 5. Get next batch for processing
SELECT * FROM dr_elena_get_next_enhancement_batch(50);

-- 6. Log EPUB migration
SELECT dr_elena_log_epub_migration(
    123, '/path/to/original.epub', '/Calibre Library/Author/Book/',
    'completed', 456, NULL, 2048576, 15000
);

-- 7. Clean up old logs
SELECT dr_elena_cleanup_enhancement_logs(30);
*/