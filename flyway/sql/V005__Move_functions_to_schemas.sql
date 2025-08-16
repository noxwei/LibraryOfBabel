-- =========================================================================
-- V005: Move Functions to Schemas - Simple Version for Staging
-- =========================================================================
-- Description: Move existing functions to appropriate schemas
-- Author: Database Architecture Team
-- Date: 2025-08-15
-- Dependencies: V004__Schema_separation.sql
-- =========================================================================

-- =============================================================================
-- MOVE EXISTING FUNCTIONS TO APPROPRIATE SCHEMAS
-- =============================================================================

DO $$
BEGIN
    -- Move API functions that exist in staging
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_system_health_check' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_system_health_check SET SCHEMA api';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_search_comprehensive' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_search_comprehensive SET SCHEMA api';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'api_get_book_details' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION api_get_book_details SET SCHEMA api';
    END IF;
    
    -- Move pipeline functions that exist in staging
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'update_book_word_count' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION update_book_word_count SET SCHEMA pipeline';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'update_search_vector' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION update_search_vector SET SCHEMA pipeline';
    END IF;
    
END $$;

-- =============================================================================
-- SUMMARY
-- =============================================================================

SELECT 'V005 function organization completed - existing functions moved to schemas' AS migration_message;