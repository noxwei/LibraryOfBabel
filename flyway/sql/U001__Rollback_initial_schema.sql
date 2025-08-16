-- =========================================================================
-- U001: Rollback Initial Database Schema
-- =========================================================================
-- Description: Rollback script for V001__Initial_schema.sql
-- Author: Database Team
-- Date: 2025-08-15
-- =========================================================================

-- Drop triggers first
DROP TRIGGER IF EXISTS trigger_update_book_word_count ON chunks;
DROP TRIGGER IF EXISTS trigger_update_search_vector ON chunks;

-- Drop functions
DROP FUNCTION IF EXISTS update_book_word_count();
DROP FUNCTION IF EXISTS update_search_vector();

-- Drop tables in reverse order (respecting foreign keys)
DROP TABLE IF EXISTS chunks CASCADE;
DROP TABLE IF EXISTS books CASCADE;
DROP TABLE IF EXISTS authors CASCADE;