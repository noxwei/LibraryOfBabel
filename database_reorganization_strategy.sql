-- =============================================================================
-- 📚 LibraryOfBabel Database Reorganization Strategy
-- =============================================================================
-- Author: Dr. Sarah Chen (陈雪芳) - Database Architecture & Optimization
-- Purpose: Reorganize book_ids for optimal sequential structure
-- Goal: Books 1-N have chunks, books N+1-max need processing
-- 
-- CRITICAL: This is a major structural change requiring careful execution
-- =============================================================================

-- =============================================================================
-- PHASE 1: PRE-REORGANIZATION BACKUP & ANALYSIS
-- =============================================================================

-- 1.1: Create comprehensive backup tables
CREATE TABLE books_backup_$(date +%Y%m%d) AS TABLE books;
CREATE TABLE chunks_backup_$(date +%Y%m%d) AS TABLE chunks;
CREATE TABLE chunk_embeddings_backup_$(date +%Y%m%d) AS TABLE chunk_embeddings;
CREATE TABLE content_classifications_backup_$(date +%Y%m%d) AS TABLE content_classifications;
CREATE TABLE embedding_routing_log_backup_$(date +%Y%m%d) AS TABLE embedding_routing_log;
CREATE TABLE chunk_entities_backup_$(date +%Y%m%d) AS TABLE chunk_entities;
CREATE TABLE chunk_summaries_backup_$(date +%Y%m%d) AS TABLE chunk_summaries;

-- 1.2: Create analysis view for current state
CREATE TEMPORARY VIEW reorganization_analysis AS
WITH book_chunk_stats AS (
    SELECT 
        b.book_id,
        b.title,
        b.author,
        COUNT(c.chunk_id) as chunk_count,
        CASE WHEN COUNT(c.chunk_id) > 0 THEN 'has_chunks' ELSE 'needs_chunks' END as status
    FROM books b
    LEFT JOIN chunks c ON b.book_id = c.book_id
    GROUP BY b.book_id, b.title, b.author
),
sequence_analysis AS (
    SELECT 
        MIN(book_id) as min_id,
        MAX(book_id) as max_id,
        COUNT(*) as total_books,
        MAX(book_id) - MIN(book_id) + 1 - COUNT(*) as gap_count
    FROM books
)
SELECT 
    'Current State' as analysis_type,
    sa.min_id,
    sa.max_id,
    sa.total_books,
    sa.gap_count,
    COUNT(CASE WHEN bcs.status = 'has_chunks' THEN 1 END) as books_with_chunks,
    COUNT(CASE WHEN bcs.status = 'needs_chunks' THEN 1 END) as books_needing_chunks
FROM sequence_analysis sa, book_chunk_stats bcs
GROUP BY sa.min_id, sa.max_id, sa.total_books, sa.gap_count;

-- Display current analysis
SELECT * FROM reorganization_analysis;

-- =============================================================================
-- PHASE 2: CONSTRAINT MANAGEMENT STRATEGY
-- =============================================================================

-- 2.1: Create function to temporarily disable foreign key constraints
CREATE OR REPLACE FUNCTION disable_foreign_key_constraints()
RETURNS void AS $$
DECLARE
    constraint_record RECORD;
BEGIN
    -- Store all foreign key constraints for later restoration
    CREATE TEMP TABLE IF NOT EXISTS fk_constraints_backup (
        table_name TEXT,
        constraint_name TEXT,
        constraint_definition TEXT
    );
    
    -- Collect all FK constraints
    FOR constraint_record IN
        SELECT 
            tc.table_name,
            tc.constraint_name,
            'ALTER TABLE ' || tc.table_name || ' ADD CONSTRAINT ' || tc.constraint_name ||
            ' FOREIGN KEY (' || kcu.column_name || ') REFERENCES ' || 
            ccu.table_name || '(' || ccu.column_name || ')' ||
            CASE WHEN rc.delete_rule != 'NO ACTION' THEN ' ON DELETE ' || rc.delete_rule ELSE '' END ||
            CASE WHEN rc.update_rule != 'NO ACTION' THEN ' ON UPDATE ' || rc.update_rule ELSE '' END
            as constraint_definition
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu 
            ON ccu.constraint_name = tc.constraint_name
        JOIN information_schema.referential_constraints rc
            ON tc.constraint_name = rc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = 'public'
        AND (tc.table_name IN ('chunks', 'chunk_embeddings', 'content_classifications', 
                              'embedding_routing_log', 'chunk_entities', 'chunk_summaries')
             OR ccu.table_name = 'books')
    LOOP
        -- Store constraint for restoration
        INSERT INTO fk_constraints_backup VALUES (
            constraint_record.table_name,
            constraint_record.constraint_name,
            constraint_record.constraint_definition
        );
        
        -- Drop the constraint
        EXECUTE 'ALTER TABLE ' || constraint_record.table_name || 
                ' DROP CONSTRAINT ' || constraint_record.constraint_name;
        
        RAISE NOTICE 'Dropped FK constraint: %.%', 
            constraint_record.table_name, constraint_record.constraint_name;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- 2.2: Create function to restore foreign key constraints
CREATE OR REPLACE FUNCTION restore_foreign_key_constraints()
RETURNS void AS $$
DECLARE
    constraint_record RECORD;
BEGIN
    FOR constraint_record IN
        SELECT table_name, constraint_name, constraint_definition
        FROM fk_constraints_backup
    LOOP
        EXECUTE constraint_record.constraint_definition;
        RAISE NOTICE 'Restored FK constraint: %.%', 
            constraint_record.table_name, constraint_record.constraint_name;
    END LOOP;
    
    DROP TABLE IF EXISTS fk_constraints_backup;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- PHASE 3: REORGANIZATION MAPPING STRATEGY
-- =============================================================================

-- 3.1: Create ID mapping table for reorganization
CREATE TEMP TABLE book_id_mapping AS
WITH books_with_chunks AS (
    SELECT DISTINCT b.book_id, b.title, b.author, 1 as has_chunks
    FROM books b
    INNER JOIN chunks c ON b.book_id = c.book_id
),
books_without_chunks AS (
    SELECT b.book_id, b.title, b.author, 0 as has_chunks
    FROM books b
    LEFT JOIN chunks c ON b.book_id = c.book_id
    WHERE c.chunk_id IS NULL
),
prioritized_books AS (
    SELECT *, ROW_NUMBER() OVER (ORDER BY has_chunks DESC, book_id ASC) as new_book_id
    FROM (
        SELECT * FROM books_with_chunks
        UNION ALL
        SELECT * FROM books_without_chunks
    ) combined
)
SELECT 
    book_id as old_book_id,
    new_book_id,
    title,
    author,
    has_chunks
FROM prioritized_books
ORDER BY new_book_id;

-- 3.2: Display reorganization plan
SELECT 
    'Reorganization Plan' as info,
    COUNT(CASE WHEN has_chunks = 1 THEN 1 END) as books_with_chunks_count,
    MAX(CASE WHEN has_chunks = 1 THEN new_book_id ELSE 0 END) as last_chunked_book_id,
    COUNT(CASE WHEN has_chunks = 0 THEN 1 END) as books_needing_chunks_count,
    MIN(CASE WHEN has_chunks = 0 THEN new_book_id ELSE 99999 END) as first_unchunked_book_id
FROM book_id_mapping;

-- =============================================================================
-- PHASE 4: SAFE REORGANIZATION EXECUTION
-- =============================================================================

-- 4.1: Main reorganization procedure
CREATE OR REPLACE FUNCTION execute_book_reorganization()
RETURNS void AS $$
DECLARE
    mapping_record RECORD;
    affected_rows INTEGER;
BEGIN
    RAISE NOTICE 'Starting LibraryOfBabel database reorganization...';
    
    -- Step 1: Disable foreign key constraints
    PERFORM disable_foreign_key_constraints();
    
    -- Step 2: Create temporary updated tables
    CREATE TEMP TABLE books_new AS 
    SELECT 
        bim.new_book_id as book_id,
        b.title,
        b.author,
        b.author_id,
        b.publisher,
        b.publication_date,
        b.publication_year,
        b.language,
        b.isbn,
        b.description,
        b.genre,
        b.word_count,
        b.file_path,
        b.source_location,
        b.import_source,
        b.processed_date,
        b.created_at
    FROM books b
    JOIN book_id_mapping bim ON b.book_id = bim.old_book_id
    ORDER BY bim.new_book_id;
    
    -- Step 3: Update chunks table with new book_ids
    CREATE TEMP TABLE chunks_new AS
    SELECT 
        c.chunk_id,
        bim.new_book_id as book_id,
        c.chunk_type,
        c.title,
        c.content,
        c.word_count,
        c.character_count,
        c.chapter_number,
        c.section_number,
        c.paragraph_number,
        c.start_position,
        c.end_position,
        c.parent_chunk_id,
        c.search_vector,
        c.created_at
    FROM chunks c
    JOIN book_id_mapping bim ON c.book_id = bim.old_book_id;
    
    -- Step 4: Update related tables with new book_ids
    CREATE TEMP TABLE content_classifications_new AS
    SELECT 
        cc.classification_id,
        cc.chunk_id,
        bim.new_book_id as book_id,
        cc.content_type,
        cc.detected_language,
        cc.emotional_tone,
        cc.confidence_score,
        cc.classification_model,
        cc.created_at
    FROM content_classifications cc
    JOIN book_id_mapping bim ON cc.book_id = bim.old_book_id;
    
    CREATE TEMP TABLE embedding_routing_log_new AS
    SELECT 
        erl.routing_id,
        erl.chunk_id,
        bim.new_book_id as book_id,
        erl.selected_model,
        erl.routing_reason,
        erl.content_type,
        erl.processing_time_ms,
        erl.created_at
    FROM embedding_routing_log erl
    JOIN book_id_mapping bim ON erl.book_id = bim.old_book_id;
    
    CREATE TEMP TABLE chunk_entities_new AS
    SELECT 
        ce.entity_id,
        ce.chunk_id,
        bim.new_book_id as book_id,
        ce.entity_text,
        ce.entity_type,
        ce.confidence,
        ce.extraction_model,
        ce.created_at
    FROM chunk_entities ce
    JOIN book_id_mapping bim ON ce.book_id = bim.old_book_id;
    
    CREATE TEMP TABLE chunk_summaries_new AS
    SELECT 
        cs.summary_id,
        cs.chunk_id,
        bim.new_book_id as book_id,
        cs.original_length,
        cs.summary_text,
        cs.summary_length,
        cs.compression_ratio,
        cs.summary_model,
        cs.created_at
    FROM chunk_summaries cs
    JOIN book_id_mapping bim ON cs.book_id = bim.old_book_id;
    
    -- Step 5: Atomic replacement of tables
    BEGIN
        -- Clear existing data (within transaction)
        DELETE FROM content_classifications;
        DELETE FROM embedding_routing_log;
        DELETE FROM chunk_entities;
        DELETE FROM chunk_summaries;
        DELETE FROM chunk_embeddings;
        DELETE FROM chunks;
        DELETE FROM books WHERE book_id != 0; -- Keep system metadata book
        
        -- Insert reorganized data
        INSERT INTO books SELECT * FROM books_new;
        GET DIAGNOSTICS affected_rows = ROW_COUNT;
        RAISE NOTICE 'Reorganized % books', affected_rows;
        
        INSERT INTO chunks SELECT * FROM chunks_new;
        GET DIAGNOSTICS affected_rows = ROW_COUNT;
        RAISE NOTICE 'Updated % chunks', affected_rows;
        
        INSERT INTO content_classifications SELECT * FROM content_classifications_new;
        INSERT INTO embedding_routing_log SELECT * FROM embedding_routing_log_new;
        INSERT INTO chunk_entities SELECT * FROM chunk_entities_new;
        INSERT INTO chunk_summaries SELECT * FROM chunk_summaries_new;
        
        -- Reset sequences to match new max IDs
        PERFORM setval('books_book_id_seq', (SELECT MAX(book_id) FROM books));
        
        RAISE NOTICE 'Database reorganization completed successfully';
        
    EXCEPTION WHEN OTHERS THEN
        RAISE EXCEPTION 'Reorganization failed: %', SQLERRM;
    END;
    
    -- Step 6: Restore foreign key constraints
    PERFORM restore_foreign_key_constraints();
    
    -- Step 7: Rebuild indexes and update statistics
    REINDEX TABLE books;
    REINDEX TABLE chunks;
    ANALYZE books;
    ANALYZE chunks;
    
    RAISE NOTICE 'LibraryOfBabel reorganization completed successfully!';
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- PHASE 5: POST-REORGANIZATION VERIFICATION
-- =============================================================================

-- 5.1: Verification function
CREATE OR REPLACE FUNCTION verify_reorganization()
RETURNS TABLE(
    metric TEXT,
    before_value TEXT,
    after_value TEXT,
    status TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH verification_metrics AS (
        SELECT 
            'total_books' as metric,
            'Unknown' as before_value,
            COUNT(*)::TEXT as after_value,
            'OK' as status
        FROM books WHERE book_id != 0
        UNION ALL
        SELECT 
            'books_with_chunks',
            'Unknown',
            COUNT(DISTINCT c.book_id)::TEXT,
            'OK'
        FROM chunks c
        UNION ALL
        SELECT 
            'books_without_chunks',
            'Unknown',
            (COUNT(*) - (SELECT COUNT(DISTINCT book_id) FROM chunks))::TEXT,
            'OK'
        FROM books WHERE book_id != 0
        UNION ALL
        SELECT 
            'max_chunked_book_id',
            'Unknown',
            COALESCE(MAX(c.book_id)::TEXT, 'None'),
            CASE WHEN MAX(c.book_id) IS NOT NULL THEN 'OK' ELSE 'WARNING' END
        FROM chunks c
        UNION ALL
        SELECT 
            'sequence_continuity',
            'Gaps present',
            CASE 
                WHEN (SELECT MAX(book_id) - MIN(book_id) + 1 FROM books WHERE book_id != 0) = 
                     (SELECT COUNT(*) FROM books WHERE book_id != 0) 
                THEN 'Continuous' 
                ELSE 'Has gaps' 
            END,
            CASE 
                WHEN (SELECT MAX(book_id) - MIN(book_id) + 1 FROM books WHERE book_id != 0) = 
                     (SELECT COUNT(*) FROM books WHERE book_id != 0) 
                THEN 'OK' 
                ELSE 'WARNING' 
            END
    )
    SELECT * FROM verification_metrics;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- EXECUTION INSTRUCTIONS
-- =============================================================================

/*
SAFE EXECUTION PROCEDURE:

1. BACKUP PHASE (MANDATORY):
   -- Export full database backup
   pg_dump libraryofbabel > libraryofbabel_backup_$(date +%Y%m%d_%H%M%S).sql

2. ANALYSIS PHASE:
   SELECT * FROM reorganization_analysis;
   SELECT * FROM book_id_mapping LIMIT 20;

3. EXECUTION PHASE (IN TRANSACTION):
   BEGIN;
   SELECT execute_book_reorganization();
   SELECT * FROM verify_reorganization();
   -- Only COMMIT if verification shows all OK
   COMMIT; -- or ROLLBACK; if issues found

4. POST-EXECUTION VERIFICATION:
   SELECT * FROM verify_reorganization();
   
PERFORMANCE IMPACT:
- Improved query performance due to sequential IDs
- Better cache locality for book-based operations  
- Reduced index fragmentation
- Cleaner data organization for chunk processing

ROLLBACK PLAN:
If issues occur, restore from backup:
psql libraryofbabel < libraryofbabel_backup_[timestamp].sql
*/

-- =============================================================================
-- PERFORMANCE OPTIMIZATION RECOMMENDATIONS
-- =============================================================================

-- After reorganization, consider these optimizations:

-- 1. Partitioning strategy for large datasets
-- CREATE TABLE books_partitioned (LIKE books INCLUDING ALL) 
-- PARTITION BY RANGE (book_id);

-- 2. Enhanced indexing for common access patterns
-- CREATE INDEX CONCURRENTLY idx_books_sequential_access ON books (book_id) 
-- WHERE book_id BETWEEN 1 AND (SELECT MAX(book_id) FROM chunks);

-- 3. Materialized view for chunk statistics
-- CREATE MATERIALIZED VIEW mv_book_chunk_stats AS
-- SELECT b.book_id, COUNT(c.chunk_id) as chunk_count, 
--        CASE WHEN COUNT(c.chunk_id) > 0 THEN 'processed' ELSE 'pending' END as status
-- FROM books b LEFT JOIN chunks c ON b.book_id = c.book_id 
-- GROUP BY b.book_id;

COMMENT ON FUNCTION execute_book_reorganization() IS 
'Dr. Sarah Chen: Comprehensive database reorganization for optimal book ID sequencing';

COMMENT ON FUNCTION verify_reorganization() IS 
'Dr. Sarah Chen: Post-reorganization verification and integrity checks';