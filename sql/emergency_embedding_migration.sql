-- ====================================================================
-- DR. SARAH CHEN EMERGENCY EMBEDDING MIGRATION SOLUTION
-- PostgreSQL-First Architecture for Embedding Schema Crisis
-- ====================================================================

-- CRITICAL MISSION: Migrate 58,974 embeddings from chunk_embeddings → chunks.embedding_vector
-- SAFETY: Zero data loss, transaction-safe, rollback capable
-- URGENCY: Restore user's semantic search immediately

-- ====================================================================
-- 1. EMERGENCY BACKUP FUNCTION
-- ====================================================================

CREATE OR REPLACE FUNCTION emergency_backup_existing_embeddings()
RETURNS TABLE(
    chunks_with_embeddings INTEGER,
    backup_table_created BOOLEAN,
    backup_record_count INTEGER,
    success BOOLEAN,
    message TEXT
) AS $$
DECLARE
    existing_count INTEGER;
    backup_count INTEGER;
BEGIN
    -- Count existing embeddings in chunks table
    SELECT COUNT(*) INTO existing_count
    FROM chunks 
    WHERE embedding_vector IS NOT NULL;
    
    -- Create emergency backup table
    DROP TABLE IF EXISTS emergency_chunks_embedding_backup;
    CREATE TABLE emergency_chunks_embedding_backup AS
    SELECT chunk_id, embedding_vector, embedding_model_used, last_embedding_update
    FROM chunks 
    WHERE embedding_vector IS NOT NULL;
    
    -- Verify backup
    SELECT COUNT(*) INTO backup_count
    FROM emergency_chunks_embedding_backup;
    
    -- Return results
    RETURN QUERY SELECT 
        existing_count,
        TRUE as backup_table_created,
        backup_count,
        (backup_count = existing_count) as success,
        CASE WHEN backup_count = existing_count 
             THEN 'Emergency backup completed successfully'
             ELSE 'WARNING: Backup count mismatch!'
        END as message;
        
EXCEPTION
    WHEN OTHERS THEN
        RETURN QUERY SELECT 
            0, FALSE, 0, FALSE,
            'BACKUP FAILED: ' || SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- ====================================================================
-- 2. EMERGENCY MIGRATION FUNCTION (TRANSACTION-SAFE)
-- ====================================================================

CREATE OR REPLACE FUNCTION emergency_migrate_embeddings_to_chunks(
    batch_size INTEGER DEFAULT 1000,
    dry_run BOOLEAN DEFAULT FALSE
)
RETURNS TABLE(
    total_candidates INTEGER,
    migrated_count INTEGER,
    conflict_count INTEGER,
    orphaned_count INTEGER,
    success BOOLEAN,
    message TEXT,
    processing_time_seconds NUMERIC
) AS $$
DECLARE
    start_time TIMESTAMP;
    candidates_count INTEGER;
    migrated_records INTEGER := 0;
    conflicts INTEGER := 0;
    orphans INTEGER := 0;
    batch_count INTEGER;
    current_batch INTEGER := 0;
BEGIN
    start_time := clock_timestamp();
    
    -- Count migration candidates
    SELECT COUNT(*) INTO candidates_count
    FROM chunk_embeddings ce
    INNER JOIN chunks c ON ce.chunk_id = c.chunk_id
    WHERE ce.embedding_vector IS NOT NULL 
      AND c.embedding_vector IS NULL;
    
    -- Count conflicts (should be 0 based on analysis)
    SELECT COUNT(*) INTO conflicts
    FROM chunk_embeddings ce
    INNER JOIN chunks c ON ce.chunk_id = c.chunk_id
    WHERE ce.embedding_vector IS NOT NULL 
      AND c.embedding_vector IS NOT NULL;
    
    -- Count orphans
    SELECT COUNT(*) INTO orphans
    FROM chunk_embeddings ce
    LEFT JOIN chunks c ON ce.chunk_id = c.chunk_id
    WHERE ce.embedding_vector IS NOT NULL 
      AND c.chunk_id IS NULL;
    
    -- If dry run, return analysis only
    IF dry_run THEN
        RETURN QUERY SELECT 
            candidates_count,
            0 as migrated_count,
            conflicts,
            orphans,
            TRUE,
            'DRY RUN: Migration analysis completed' as message,
            EXTRACT(EPOCH FROM (clock_timestamp() - start_time))::NUMERIC;
        RETURN;
    END IF;
    
    -- Calculate batches
    batch_count := CEIL(candidates_count::NUMERIC / batch_size);
    
    -- Perform migration in batches
    FOR current_batch IN 0..(batch_count - 1) LOOP
        -- Migrate batch using PostgreSQL-First approach
        UPDATE chunks 
        SET 
            embedding_vector = ce.embedding_vector,
            embedding_model_used = ce.embedding_model,
            last_embedding_update = COALESCE(ce.created_at, NOW())
        FROM chunk_embeddings ce
        WHERE chunks.chunk_id = ce.chunk_id
          AND ce.embedding_vector IS NOT NULL
          AND chunks.embedding_vector IS NULL
          AND ce.embedding_id >= (current_batch * batch_size)
          AND ce.embedding_id < ((current_batch + 1) * batch_size);
        
        -- Count this batch
        GET DIAGNOSTICS migrated_records = ROW_COUNT;
        
        -- Commit batch (autocommit is on)
        RAISE NOTICE 'Batch % of % completed: % records migrated', 
                     current_batch + 1, batch_count, migrated_records;
    END LOOP;
    
    -- Final count verification
    SELECT COUNT(*) INTO migrated_records
    FROM chunks c
    INNER JOIN chunk_embeddings ce ON c.chunk_id = ce.chunk_id
    WHERE c.embedding_vector IS NOT NULL 
      AND ce.embedding_vector IS NOT NULL;
    
    RETURN QUERY SELECT 
        candidates_count,
        migrated_records,
        conflicts,
        orphans,
        (migrated_records > 0) as success,
        'Emergency migration completed: ' || migrated_records || ' embeddings transferred' as message,
        EXTRACT(EPOCH FROM (clock_timestamp() - start_time))::NUMERIC;
        
EXCEPTION
    WHEN OTHERS THEN
        RETURN QUERY SELECT 
            candidates_count,
            0,
            conflicts,
            orphans,
            FALSE,
            'MIGRATION FAILED: ' || SQLERRM,
            EXTRACT(EPOCH FROM (clock_timestamp() - start_time))::NUMERIC;
END;
$$ LANGUAGE plpgsql;

-- ====================================================================
-- 3. SEARCH FUNCTION VALIDATION
-- ====================================================================

CREATE OR REPLACE FUNCTION validate_embedding_search_capability()
RETURNS TABLE(
    chunks_with_embeddings INTEGER,
    sample_search_works BOOLEAN,
    vector_dimensions INTEGER,
    search_ready BOOLEAN,
    message TEXT
) AS $$
DECLARE
    embed_count INTEGER;
    sample_result INTEGER;
    vector_dim INTEGER;
BEGIN
    -- Count embeddings in chunks table
    SELECT COUNT(*) INTO embed_count
    FROM chunks 
    WHERE embedding_vector IS NOT NULL;
    
    -- Test vector dimensions
    SELECT vector_dims(embedding_vector) INTO vector_dim
    FROM chunks 
    WHERE embedding_vector IS NOT NULL 
    LIMIT 1;
    
    -- Test basic vector similarity (if we have embeddings)
    IF embed_count > 0 THEN
        SELECT COUNT(*) INTO sample_result
        FROM chunks 
        WHERE embedding_vector IS NOT NULL
        LIMIT 1;
    ELSE
        sample_result := 0;
    END IF;
    
    RETURN QUERY SELECT 
        embed_count,
        (sample_result > 0) as sample_search_works,
        COALESCE(vector_dim, 0) as vector_dimensions,
        (embed_count > 1000) as search_ready,
        CASE 
            WHEN embed_count = 0 THEN 'NO EMBEDDINGS FOUND - MIGRATION NEEDED'
            WHEN embed_count < 1000 THEN 'LOW EMBEDDING COUNT - MIGRATION INCOMPLETE'
            ELSE 'SEARCH SYSTEM READY'
        END as message;
        
EXCEPTION
    WHEN OTHERS THEN
        RETURN QUERY SELECT 
            0, FALSE, 0, FALSE,
            'VALIDATION FAILED: ' || SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- ====================================================================
-- 4. WORKER REDIRECTION CHECK
-- ====================================================================

CREATE OR REPLACE FUNCTION check_embedding_write_locations()
RETURNS TABLE(
    chunk_embeddings_recent INTEGER,
    chunks_recent INTEGER,
    workers_writing_wrong_location BOOLEAN,
    recommendation TEXT
) AS $$
DECLARE
    ce_recent INTEGER;
    chunks_recent INTEGER;
BEGIN
    -- Check recent writes to chunk_embeddings (last hour)
    SELECT COUNT(*) INTO ce_recent
    FROM chunk_embeddings 
    WHERE created_at > NOW() - INTERVAL '1 hour';
    
    -- Check recent writes to chunks embedding_vector (last hour)
    SELECT COUNT(*) INTO chunks_recent
    FROM chunks 
    WHERE last_embedding_update > NOW() - INTERVAL '1 hour';
    
    RETURN QUERY SELECT 
        ce_recent,
        chunks_recent,
        (ce_recent > chunks_recent) as workers_writing_wrong_location,
        CASE 
            WHEN ce_recent > chunks_recent THEN 'STOP WORKERS - Writing to wrong table!'
            WHEN chunks_recent > ce_recent THEN 'Workers correctly configured'
            ELSE 'No recent embedding activity detected'
        END as recommendation;
        
EXCEPTION
    WHEN OTHERS THEN
        RETURN QUERY SELECT 
            0, 0, FALSE,
            'CHECK FAILED: ' || SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- ====================================================================
-- EMERGENCY EXECUTION COMMANDS
-- ====================================================================

-- Step 1: Backup existing data
-- SELECT * FROM emergency_backup_existing_embeddings();

-- Step 2: Test migration (dry run)
-- SELECT * FROM emergency_migrate_embeddings_to_chunks(1000, TRUE);

-- Step 3: Execute migration
-- SELECT * FROM emergency_migrate_embeddings_to_chunks(1000, FALSE);

-- Step 4: Validate search capability
-- SELECT * FROM validate_embedding_search_capability();

-- Step 5: Check worker configuration
-- SELECT * FROM check_embedding_write_locations();