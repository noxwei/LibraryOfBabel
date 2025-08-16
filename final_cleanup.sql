-- =========================================================================
-- Final Cleanup: Remove ALL Experimental Functions
-- =========================================================================
-- Description: Keep only core production API (26 functions) + PostgreSQL system
-- Remove all experimental, agent, team, calibre, and test functions
-- =========================================================================

-- Remove ALL remaining experimental functions
DO $$
DECLARE
    func_name TEXT;
BEGIN
    -- Get all api_ functions except the core 26 we want to keep
    FOR func_name IN 
        SELECT routine_name 
        FROM information_schema.routines 
        WHERE routine_schema='public' 
            AND routine_type='FUNCTION'
            AND routine_name LIKE 'api_%'
            AND routine_name NOT IN (
                'api_get_book_chunks',
                'api_get_book_details', 
                'api_list_books',
                'api_shortcuts_book_construct',
                'api_shortcuts_book_count',
                'api_shortcuts_book_page',
                'api_shortcuts_book_random_page',
                'api_shortcuts_book_summary',
                'api_shortcuts_book_toc',
                'api_shortcuts_collection_health',
                'api_shortcuts_dashboard',
                'api_shortcuts_list_authors',
                'api_shortcuts_list_titles',
                'api_shortcuts_random_author',
                'api_shortcuts_random_citation',
                'api_shortcuts_random_share_text',
                'api_shortcuts_random_title',
                'api_shortcuts_search_count',
                'api_shortcuts_search_guaranteed_fast',
                'api_shortcuts_search_has_results',
                'api_shortcuts_search_simple',
                'api_shortcuts_search_titles',
                'api_shortcuts_search_ultra_fast',
                'api_system_health_check',
                'api_v3_health',
                'api_v3_search'
            )
    LOOP
        EXECUTE 'DROP FUNCTION IF EXISTS ' || func_name || ' CASCADE';
        RAISE NOTICE 'Dropped function: %', func_name;
    END LOOP;
    
    -- Remove any remaining experimental functions by pattern
    FOR func_name IN 
        SELECT routine_name 
        FROM information_schema.routines 
        WHERE routine_schema='public' 
            AND routine_type='FUNCTION'
            AND (
                routine_name LIKE '%agent%' OR
                routine_name LIKE '%team%' OR
                routine_name LIKE '%experiment%' OR
                routine_name LIKE '%test%' OR
                routine_name LIKE '%calibre%' OR
                routine_name LIKE '%prototype%' OR
                routine_name LIKE '%temp%' OR
                routine_name LIKE '%debug%' OR
                routine_name LIKE 'hybrid_%' OR
                routine_name LIKE '%benchmark%'
            )
    LOOP
        EXECUTE 'DROP FUNCTION IF EXISTS ' || func_name || ' CASCADE';
        RAISE NOTICE 'Dropped experimental function: %', func_name;
    END LOOP;
    
END $$;

SELECT 'Final cleanup completed - only core production functions remain' AS cleanup_message;