-- 🔥 BATCHED SENTENCE REMOVAL STRATEGY
-- Delete 12.6M sentence chunks in manageable batches to avoid locks

\echo '🔥 DR. CHEN: BATCHED SENTENCE REMOVAL'
\echo '=================================='
\echo 'Target: 12,646,678 sentence chunks'
\echo 'Strategy: 100K row batches with progress tracking'
\echo ''

-- Disable autovacuum temporarily for performance
ALTER TABLE chunks SET (autovacuum_enabled = false);

-- Create progress tracking
CREATE TEMP TABLE IF NOT EXISTS removal_progress (
    batch_number INTEGER,
    rows_deleted INTEGER,
    batch_start TIMESTAMP,
    batch_end TIMESTAMP,
    total_remaining BIGINT
);

\echo 'Starting batched deletion...'

-- Batch 1: Delete first 100K sentences
\echo 'Batch 1: Deleting 100K sentences...'
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
INSERT INTO removal_progress 
SELECT 1, COUNT(*), NOW(), NOW(), 
       (SELECT COUNT(*) FROM chunks WHERE chunk_type = 'sentence')
FROM batch_delete;

\echo 'Batch 1 complete - checking progress...'
SELECT 
    'Batch 1 Results' as status,
    rows_deleted,
    total_remaining,
    batch_end - batch_start as duration
FROM removal_progress 
WHERE batch_number = 1;

-- Batch 2: Delete next 100K sentences  
\echo 'Batch 2: Deleting next 100K sentences...'
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
INSERT INTO removal_progress 
SELECT 2, COUNT(*), NOW(), NOW(),
       (SELECT COUNT(*) FROM chunks WHERE chunk_type = 'sentence')
FROM batch_delete;

\echo 'Batch 2 complete - progress check...'
SELECT 
    'Batch 2 Results' as status,
    rows_deleted,
    total_remaining,
    batch_end - batch_start as duration
FROM removal_progress 
WHERE batch_number = 2;

-- Batch 3: Delete next 100K sentences
\echo 'Batch 3: Deleting next 100K sentences...'
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
INSERT INTO removal_progress 
SELECT 3, COUNT(*), NOW(), NOW(),
       (SELECT COUNT(*) FROM chunks WHERE chunk_type = 'sentence')
FROM batch_delete;

\echo 'Batch 3 complete - progress summary...'
SELECT 
    batch_number,
    rows_deleted,
    total_remaining,
    batch_end - batch_start as batch_duration
FROM removal_progress 
ORDER BY batch_number;

-- Calculate remaining work
\echo 'Remaining work estimation:'
SELECT 
    COUNT(*) as sentences_remaining,
    ROUND(COUNT(*)::NUMERIC / 100000, 1) as batches_remaining,
    'Continue with more batches as needed' as next_step
FROM chunks 
WHERE chunk_type = 'sentence';

-- Re-enable autovacuum
ALTER TABLE chunks SET (autovacuum_enabled = true);

\echo ''
\echo '✅ First 3 batches complete (300K sentences)'
\echo '📊 Check remaining count and continue batching'
\echo '⚡ Each batch should complete in seconds, not hours'