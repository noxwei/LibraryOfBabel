-- ====================================================================
-- DR. SARAH CHEN SAFE BATCH MIGRATION APPROACH
-- PostgreSQL-First Emergency Fix with Smaller Batches
-- ====================================================================

CREATE OR REPLACE FUNCTION safe_batch_migrate_embeddings(
    batch_size INTEGER DEFAULT 100
)
RETURNS TABLE(
    batch_number INTEGER,
    records_migrated INTEGER,
    total_migrated INTEGER,
    success BOOLEAN,
    message TEXT
) AS $$
DECLARE
    total_migrated_count INTEGER := 0;
    current_batch INTEGER := 1;
    batch_migrated INTEGER;
    chunk_ids_to_migrate VARCHAR[];
BEGIN
    -- Get chunk IDs that need migration in small batches
    LOOP
        -- Get next batch of chunk IDs
        SELECT ARRAY(
            SELECT ce.chunk_id
            FROM chunk_embeddings ce
            INNER JOIN chunks c ON ce.chunk_id = c.chunk_id
            WHERE ce.embedding_vector IS NOT NULL
              AND c.embedding_vector IS NULL
            LIMIT batch_size
        ) INTO chunk_ids_to_migrate;
        
        -- Exit if no more records to migrate
        IF array_length(chunk_ids_to_migrate, 1) IS NULL THEN
            RETURN QUERY SELECT 
                current_batch,
                0,
                total_migrated_count,
                TRUE,
                'Migration completed - no more records to process';
            EXIT;
        END IF;
        
        -- Migrate this batch
        UPDATE chunks 
        SET 
            embedding_vector = ce.embedding_vector,
            embedding_model_used = ce.embedding_model,
            last_embedding_update = COALESCE(ce.created_at, NOW())
        FROM chunk_embeddings ce
        WHERE chunks.chunk_id = ce.chunk_id
          AND chunks.chunk_id = ANY(chunk_ids_to_migrate)
          AND ce.embedding_vector IS NOT NULL;
        
        GET DIAGNOSTICS batch_migrated = ROW_COUNT;
        total_migrated_count := total_migrated_count + batch_migrated;
        
        RETURN QUERY SELECT 
            current_batch,
            batch_migrated,
            total_migrated_count,
            TRUE,
            'Batch ' || current_batch || ' completed: ' || batch_migrated || ' records migrated';
            
        current_batch := current_batch + 1;
        
        -- Safety exit after 1000 batches
        IF current_batch > 1000 THEN
            RETURN QUERY SELECT 
                current_batch,
                0,
                total_migrated_count,
                FALSE,
                'Safety exit: Too many batches, stopping at ' || total_migrated_count || ' records';
            EXIT;
        END IF;
        
    END LOOP;
    
EXCEPTION
    WHEN OTHERS THEN
        RETURN QUERY SELECT 
            current_batch,
            0,
            total_migrated_count,
            FALSE,
            'ERROR: ' || SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- Quick validation function
CREATE OR REPLACE FUNCTION check_migration_progress()
RETURNS TABLE(
    chunks_with_embeddings INTEGER,
    chunk_embeddings_total INTEGER,
    migration_candidates INTEGER,
    progress_percentage NUMERIC
) AS $$
DECLARE
    chunks_count INTEGER;
    ce_count INTEGER;
    candidates INTEGER;
BEGIN
    SELECT COUNT(*) INTO chunks_count
    FROM chunks WHERE embedding_vector IS NOT NULL;
    
    SELECT COUNT(*) INTO ce_count
    FROM chunk_embeddings WHERE embedding_vector IS NOT NULL;
    
    SELECT COUNT(*) INTO candidates
    FROM chunk_embeddings ce
    INNER JOIN chunks c ON ce.chunk_id = c.chunk_id
    WHERE ce.embedding_vector IS NOT NULL
      AND c.embedding_vector IS NULL;
    
    RETURN QUERY SELECT 
        chunks_count,
        ce_count,
        candidates,
        CASE WHEN ce_count > 0 
             THEN ROUND((chunks_count::NUMERIC / ce_count) * 100, 2)
             ELSE 0::NUMERIC 
        END as progress_percentage;
END;
$$ LANGUAGE plpgsql;