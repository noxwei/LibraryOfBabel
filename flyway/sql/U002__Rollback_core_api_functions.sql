-- =========================================================================
-- U002: Rollback Core API Functions
-- =========================================================================
-- Description: Rollback script for V002__Core_api_functions.sql
-- Author: Database Team
-- Date: 2025-08-15
-- =========================================================================

-- Drop functions
DROP FUNCTION IF EXISTS api_get_book_details(INTEGER);
DROP FUNCTION IF EXISTS api_search_comprehensive(TEXT, TEXT, INTEGER, TEXT);
DROP FUNCTION IF EXISTS api_system_health_check();

-- Drop tables
DROP TABLE IF EXISTS chunk_embeddings CASCADE;