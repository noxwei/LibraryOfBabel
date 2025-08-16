-- =========================================================================
-- V004: Schema Separation - Create Schemas Only
-- =========================================================================
-- Description: Create schema structure for production vs data pipeline separation
-- Author: Database Architecture Team
-- Date: 2025-08-15
-- Dependencies: V003__Selective_cleanup_team_research.sql
-- =========================================================================

-- =============================================================================
-- CREATE NEW SCHEMAS
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS api;
CREATE SCHEMA IF NOT EXISTS pipeline;
CREATE SCHEMA IF NOT EXISTS vectors;

-- =============================================================================
-- CREATE SCHEMA PERMISSIONS
-- =============================================================================

-- Grant usage on schemas
GRANT USAGE ON SCHEMA api TO weixiangzhang;
GRANT USAGE ON SCHEMA pipeline TO weixiangzhang;
GRANT USAGE ON SCHEMA vectors TO weixiangzhang;

-- Grant execute permissions on all functions in schemas
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA api TO weixiangzhang;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA pipeline TO weixiangzhang;  
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA vectors TO weixiangzhang;

-- Set default privileges for future functions
ALTER DEFAULT PRIVILEGES IN SCHEMA api GRANT EXECUTE ON FUNCTIONS TO weixiangzhang;
ALTER DEFAULT PRIVILEGES IN SCHEMA pipeline GRANT EXECUTE ON FUNCTIONS TO weixiangzhang;
ALTER DEFAULT PRIVILEGES IN SCHEMA vectors GRANT EXECUTE ON FUNCTIONS TO weixiangzhang;

-- =============================================================================
-- SUMMARY
-- =============================================================================
-- 
-- Created schemas for future organization:
-- 📱 api schema: For production serving functions
-- 🔄 pipeline schema: For data processing functions  
-- 🔢 vectors schema: For pgVector extension functions
--
-- Function migration will be done in production deployment with full function set
-- This migration establishes the foundation for schema separation

SELECT 'V004 schema separation foundation created - schemas ready for function organization' AS migration_message;