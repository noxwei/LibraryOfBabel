-- 🚀 CONTINUE BATCHED SENTENCE REMOVAL
-- Continue deleting remaining 12.3M sentences in 100K batches

\echo '🚀 CONTINUING BATCHED SENTENCE REMOVAL'
\echo '===================================='

-- Create automated batch loop (batches 4-20)
DO $$
DECLARE
    batch_num INTEGER := 4;
    rows_deleted_count INTEGER;
    remaining_count BIGINT;
    start_time TIMESTAMP;
    end_time TIMESTAMP;
BEGIN
    -- Create temp table if not exists
    CREATE TEMP TABLE IF NOT EXISTS removal_progress (
        batch_number INTEGER,
        rows_deleted INTEGER,
        batch_start TIMESTAMP,
        batch_end TIMESTAMP,
        total_remaining BIGINT
    );

    -- Loop through batches 4-20 (1.7M more sentences)
    WHILE batch_num <= 20 LOOP
        start_time := NOW();
        
        -- Delete batch
        WITH batch_delete AS (
            DELETE FROM chunks 
            WHERE chunk_id IN (
                SELECT chunk_id 
                FROM chunks 
                WHERE chunk_type = 'sentence' 
                LIMIT 100000
            )
            RETURNING chunk_id
        )
        SELECT COUNT(*) INTO rows_deleted_count FROM batch_delete;
        
        end_time := NOW();
        
        -- Get remaining count
        SELECT COUNT(*) INTO remaining_count 
        FROM chunks 
        WHERE chunk_type = 'sentence';
        
        -- Log progress
        INSERT INTO removal_progress VALUES (
            batch_num, 
            rows_deleted_count, 
            start_time, 
            end_time, 
            remaining_count
        );
        
        -- Progress report every 5 batches
        IF batch_num % 5 = 0 THEN
            RAISE NOTICE 'Batch % complete: % rows deleted, % remaining, duration: %', 
                batch_num, rows_deleted_count, remaining_count, (end_time - start_time);
        END IF;
        
        batch_num := batch_num + 1;
        
        -- Break if no more sentences to delete
        EXIT WHEN rows_deleted_count = 0;
    END LOOP;
    
    RAISE NOTICE 'Batches 4-20 complete. Total progress:';
END $$;

-- Show comprehensive progress
\echo 'Progress Summary:'
SELECT 
    batch_number,
    rows_deleted,
    total_remaining,
    EXTRACT(EPOCH FROM (batch_end - batch_start)) as seconds_taken
FROM removal_progress 
WHERE batch_number >= 4
ORDER BY batch_number;

-- Show overall statistics
SELECT 
    'Overall Progress' as status,
    SUM(rows_deleted) as total_deleted,
    MIN(total_remaining) as sentences_remaining,
    COUNT(*) as batches_completed
FROM removal_progress;

\echo ''
\echo '🎯 Next: Run additional batches as needed'
\echo '📊 Monitor progress and continue until < 1M sentences remain'
\echo '⚡ Each batch: ~100K deletions in seconds'