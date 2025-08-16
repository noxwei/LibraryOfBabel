-- =========================================================================
-- Isolate Data Pipeline Functions to pipeline Schema
-- =========================================================================
-- Description: Move data processing functions away from production
-- =========================================================================

-- Create pipeline schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS pipeline;

-- Grant permissions
GRANT USAGE ON SCHEMA pipeline TO weixiangzhang;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA pipeline TO weixiangzhang;
ALTER DEFAULT PRIVILEGES IN SCHEMA pipeline GRANT EXECUTE ON FUNCTIONS TO weixiangzhang;

-- Move pipeline functions
DO $$
BEGIN
    -- Book processing functions
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_ingest_complete_book' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_ingest_complete_book SET SCHEMA pipeline';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_process_book_batch' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_process_book_batch SET SCHEMA pipeline';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_process_book_content' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_process_book_content SET SCHEMA pipeline';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'batch_process_books_simple' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION batch_process_books_simple SET SCHEMA pipeline';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'batch_process_unclassified_books' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION batch_process_unclassified_books SET SCHEMA pipeline';
    END IF;
    
    -- Content classification
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'hybrid_ensemble_classification' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION hybrid_ensemble_classification SET SCHEMA pipeline';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'ml_phase1_subject_classification' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION ml_phase1_subject_classification SET SCHEMA pipeline';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'batch_classify_content' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION batch_classify_content SET SCHEMA pipeline';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'update_books_with_chunk_classification' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION update_books_with_chunk_classification SET SCHEMA pipeline';
    END IF;
    
    -- Book maintenance functions
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'update_book_word_count' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION update_book_word_count SET SCHEMA pipeline';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'update_search_vector' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION update_search_vector SET SCHEMA pipeline';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'update_book_statistics' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION update_book_statistics SET SCHEMA pipeline';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'refresh_book_statistics' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION refresh_book_statistics SET SCHEMA pipeline';
    END IF;
    
    -- Data insertion functions
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_insert_book' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_insert_book SET SCHEMA pipeline';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_insert_chapter_chunk' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_insert_chapter_chunk SET SCHEMA pipeline';
    END IF;
    
    -- Performance monitoring
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'log_search_performance' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION log_search_performance SET SCHEMA pipeline';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'get_search_performance_stats' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION get_search_performance_stats SET SCHEMA pipeline';
    END IF;
    
END $$;

SELECT 'Data pipeline functions isolated to pipeline schema' AS isolation_message;