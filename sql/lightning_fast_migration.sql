-- ====================================================================
-- DR. SARAH CHEN LIGHTNING-FAST MIGRATION STRATEGY
-- PostgreSQL-First: Use efficient column update strategy
-- ====================================================================

-- Check current state
SELECT 
    'Before Migration' as status,
    COUNT(*) as chunks_with_embeddings
FROM chunks 
WHERE embedding_vector IS NOT NULL;

-- Lightning-fast migration using optimized approach
-- Strategy: Update only the specific columns we need
BEGIN;

-- Create index for fast lookup (if not exists)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunks_chunk_id_no_embedding 
ON chunks(chunk_id) WHERE embedding_vector IS NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunk_embeddings_chunk_id_with_vector 
ON chunk_embeddings(chunk_id) WHERE embedding_vector IS NOT NULL;

COMMIT;

-- Fast migration using JOIN approach with batching
-- This avoids the massive table scan issue
DO $$
DECLARE
    batch_size INTEGER := 500;
    total_migrated INTEGER := 0;
    batch_count INTEGER;
    current_offset INTEGER := 0;
BEGIN
    LOOP
        -- Update next batch
        WITH migration_batch AS (
            SELECT ce.chunk_id, ce.embedding_vector, ce.embedding_model
            FROM chunk_embeddings ce
            INNER JOIN chunks c ON ce.chunk_id = c.chunk_id
            WHERE ce.embedding_vector IS NOT NULL
              AND c.embedding_vector IS NULL
            OFFSET current_offset
            LIMIT batch_size
        )
        UPDATE chunks 
        SET 
            embedding_vector = mb.embedding_vector,
            embedding_model_used = mb.embedding_model,
            last_embedding_update = NOW()
        FROM migration_batch mb
        WHERE chunks.chunk_id = mb.chunk_id;
        
        GET DIAGNOSTICS batch_count = ROW_COUNT;
        total_migrated := total_migrated + batch_count;
        
        RAISE NOTICE 'Migrated batch: % records (total: %)', batch_count, total_migrated;
        
        -- Exit if no more records
        IF batch_count = 0 THEN
            EXIT;
        END IF;
        
        current_offset := current_offset + batch_size;
        
        -- Commit this batch
        COMMIT;
        BEGIN;
        
        -- Safety exit
        IF current_offset > 50000 THEN
            RAISE NOTICE 'Safety exit at % records', total_migrated;
            EXIT;
        END IF;
    END LOOP;
    
    RAISE NOTICE 'Migration completed: % total records migrated', total_migrated;
END $$;

-- Verify migration results
SELECT 
    'After Migration' as status,
    COUNT(*) as chunks_with_embeddings
FROM chunks 
WHERE embedding_vector IS NOT NULL;