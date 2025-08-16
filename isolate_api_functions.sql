-- =========================================================================
-- Isolate Production API Functions to api Schema
-- =========================================================================
-- Description: Move core production API functions to clean api schema
-- Keep ONLY the essential functions needed for live API
-- =========================================================================

-- Create api schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS api;

-- Grant permissions
GRANT USAGE ON SCHEMA api TO weixiangzhang;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA api TO weixiangzhang;
ALTER DEFAULT PRIVILEGES IN SCHEMA api GRANT EXECUTE ON FUNCTIONS TO weixiangzhang;

-- Move core production API functions
DO $$
BEGIN
    -- Core health and system functions
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_v3_health' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_v3_health SET SCHEMA api';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_v3_search' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_v3_search SET SCHEMA api';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_system_health_check' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_system_health_check SET SCHEMA api';
    END IF;
    
    -- Shortcuts API (iOS integration)
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_shortcuts_search_simple' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_shortcuts_search_simple SET SCHEMA api';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_shortcuts_dashboard' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_shortcuts_dashboard SET SCHEMA api';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_shortcuts_collection_health' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_shortcuts_collection_health SET SCHEMA api';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_shortcuts_random_citation' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_shortcuts_random_citation SET SCHEMA api';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_shortcuts_book_summary' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_shortcuts_book_summary SET SCHEMA api';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_shortcuts_list_books' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_shortcuts_list_books SET SCHEMA api';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_shortcuts_search_count' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_shortcuts_search_count SET SCHEMA api';
    END IF;
    
    -- Search functions (keep essential ones)
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_extended_semantic_search' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_extended_semantic_search SET SCHEMA api';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_search_comprehensive' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_search_comprehensive SET SCHEMA api';
    END IF;
    
    -- Content retrieval
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_get_book_details' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_get_book_details SET SCHEMA api';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_get_book_chunks' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_get_book_chunks SET SCHEMA api';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_list_books' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_list_books SET SCHEMA api';
    END IF;
    
    -- Essential search functions only (remove experimental fluff)
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'hybrid_search' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION hybrid_search SET SCHEMA api';
    END IF;
    
END $$;

SELECT 'Core production API functions isolated to api schema' AS isolation_message;