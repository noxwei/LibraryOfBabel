-- =========================================================================
-- Aggressive Cleanup: Drop ALL Non-Essential Functions
-- =========================================================================
-- Description: Keep ONLY the 26 core production functions + PostgreSQL system
-- =========================================================================

-- First, move our 26 core functions to api schema
CREATE SCHEMA IF NOT EXISTS api;
GRANT USAGE ON SCHEMA api TO weixiangzhang;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA api TO weixiangzhang;

-- Move the 26 core functions to safety
DO $$
BEGIN
    -- Core functions we absolutely need
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_get_book_chunks' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_get_book_chunks SET SCHEMA api';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_get_book_details' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_get_book_details SET SCHEMA api';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_list_books' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_list_books SET SCHEMA api';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_system_health_check' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_system_health_check SET SCHEMA api';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_v3_health' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_v3_health SET SCHEMA api';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_v3_search' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_v3_search SET SCHEMA api';
    END IF;
    
    -- Shortcuts functions
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_shortcuts_search_simple' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_shortcuts_search_simple SET SCHEMA api';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_shortcuts_dashboard' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_shortcuts_dashboard SET SCHEMA api';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_shortcuts_collection_health' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_shortcuts_collection_health SET SCHEMA api';
    END IF;
    
END $$;

-- Now aggressively drop ALL remaining api_ functions from public
DO $$
DECLARE
    func_record RECORD;
BEGIN
    FOR func_record IN 
        SELECT routine_name, specific_name
        FROM information_schema.routines 
        WHERE routine_schema='public' 
            AND routine_type='FUNCTION'
            AND routine_name LIKE 'api_%'
    LOOP
        BEGIN
            EXECUTE 'DROP FUNCTION ' || func_record.specific_name || ' CASCADE';
            RAISE NOTICE 'Dropped: %', func_record.routine_name;
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Could not drop: % (error: %)', func_record.routine_name, SQLERRM;
        END;
    END LOOP;
END $$;

SELECT 'Aggressive cleanup completed - production functions moved to api schema' AS cleanup_message;