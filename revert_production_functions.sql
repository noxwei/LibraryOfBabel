-- =========================================================================
-- Revert Production Functions Back to Public Schema
-- =========================================================================
-- Description: Move production API functions back to public schema
-- Reason: API layer expects functions in public schema, not api schema
-- =========================================================================

-- Move API functions back from api schema to public
DO $$
BEGIN
    -- Core API functions back to public
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_search_content_with_highlights' AND routine_schema = 'api') THEN
        EXECUTE 'ALTER FUNCTION api.api_search_content_with_highlights SET SCHEMA public';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_system_health_check' AND routine_schema = 'api') THEN
        EXECUTE 'ALTER FUNCTION api.api_system_health_check SET SCHEMA public';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_v3_health' AND routine_schema = 'api') THEN
        EXECUTE 'ALTER FUNCTION api.api_v3_health SET SCHEMA public';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_v3_search' AND routine_schema = 'api') THEN
        EXECUTE 'ALTER FUNCTION api.api_v3_search SET SCHEMA public';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_search_comprehensive' AND routine_schema = 'api') THEN
        EXECUTE 'ALTER FUNCTION api.api_search_comprehensive SET SCHEMA public';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_get_book_details' AND routine_schema = 'api') THEN
        EXECUTE 'ALTER FUNCTION api.api_get_book_details SET SCHEMA public';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_get_book_chunks' AND routine_schema = 'api') THEN
        EXECUTE 'ALTER FUNCTION api.api_get_book_chunks SET SCHEMA public';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_list_books' AND routine_schema = 'api') THEN
        EXECUTE 'ALTER FUNCTION api.api_list_books SET SCHEMA public';
    END IF;
    
    -- Shortcuts API functions back to public
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_shortcuts_search_simple' AND routine_schema = 'api') THEN
        EXECUTE 'ALTER FUNCTION api.api_shortcuts_search_simple SET SCHEMA public';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_shortcuts_dashboard' AND routine_schema = 'api') THEN
        EXECUTE 'ALTER FUNCTION api.api_shortcuts_dashboard SET SCHEMA public';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_shortcuts_collection_health' AND routine_schema = 'api') THEN
        EXECUTE 'ALTER FUNCTION api.api_shortcuts_collection_health SET SCHEMA public';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_shortcuts_random_citation' AND routine_schema = 'api') THEN
        EXECUTE 'ALTER FUNCTION api.api_shortcuts_random_citation SET SCHEMA public';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_shortcuts_book_summary' AND routine_schema = 'api') THEN
        EXECUTE 'ALTER FUNCTION api.api_shortcuts_book_summary SET SCHEMA public';
    END IF;
    
END $$;

-- Move pipeline functions back from pipeline schema to public  
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'update_book_word_count' AND routine_schema = 'pipeline') THEN
        EXECUTE 'ALTER FUNCTION pipeline.update_book_word_count SET SCHEMA public';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'update_search_vector' AND routine_schema = 'pipeline') THEN
        EXECUTE 'ALTER FUNCTION pipeline.update_search_vector SET SCHEMA public';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'update_book_statistics' AND routine_schema = 'pipeline') THEN
        EXECUTE 'ALTER FUNCTION pipeline.update_book_statistics SET SCHEMA public';
    END IF;
    
END $$;

SELECT 'Production functions reverted to public schema - API should now work' AS revert_message;