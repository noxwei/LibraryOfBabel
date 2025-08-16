-- =========================================================================
-- Isolate Vector/Embedding Functions to vectors Schema
-- =========================================================================
-- Description: Move all vector/embedding functions to separate schema
-- Strategy: Isolate from production API, keep accessible for pipeline
-- =========================================================================

-- Create vectors schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS vectors;

-- Grant permissions
GRANT USAGE ON SCHEMA vectors TO weixiangzhang;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA vectors TO weixiangzhang;
ALTER DEFAULT PRIVILEGES IN SCHEMA vectors GRANT EXECUTE ON FUNCTIONS TO weixiangzhang;

-- Move custom embedding functions (our functions, not pgVector extension)
DO $$
BEGIN
    -- Our custom embedding functions
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'check_embedding_write_locations' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION check_embedding_write_locations SET SCHEMA vectors';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'generate_chunk_embeddings_batch' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION generate_chunk_embeddings_batch SET SCHEMA vectors';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'get_embedding_model_usage_stats' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION get_embedding_model_usage_stats SET SCHEMA vectors';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'get_embedding_system_status' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION get_embedding_system_status SET SCHEMA vectors';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'get_fast_representative_embedding' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION get_fast_representative_embedding SET SCHEMA vectors';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'get_optimal_embedding_model' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION get_optimal_embedding_model SET SCHEMA vectors';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'get_phase_1_2_chunks_for_embedding' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION get_phase_1_2_chunks_for_embedding SET SCHEMA vectors';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'safe_batch_migrate_embeddings' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION safe_batch_migrate_embeddings SET SCHEMA vectors';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'validate_embedding_search_capability' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION validate_embedding_search_capability SET SCHEMA vectors';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'vector_cross_reference_search' AND routine_schema = 'public') THEN
        EXECUTE 'ALTER FUNCTION vector_cross_reference_search SET SCHEMA vectors';
    END IF;
    
END $$;

-- Note: pgVector extension functions (vector, cosine_distance, etc.) 
-- are system functions and should remain in public schema for compatibility

SELECT 'Vector/embedding functions isolated to vectors schema' AS isolation_message;