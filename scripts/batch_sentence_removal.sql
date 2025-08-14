-- =============================================================================
-- 🧠 DR. CHEN'S BATCH SENTENCE REMOVAL
-- =============================================================================
-- Remove sentence chunks in batches to avoid timeouts
-- Current: 90GB database, 51GB chunks table, 12.6M sentence chunks

\echo 'Starting sentence chunk removal...'

-- Remove in batches of 100,000 to avoid timeouts
DELETE FROM chunks WHERE chunk_id IN (
    SELECT chunk_id FROM chunks 
    WHERE chunk_type = 'sentence' 
    LIMIT 100000
);

\echo 'Batch 1 complete'

DELETE FROM chunks WHERE chunk_id IN (
    SELECT chunk_id FROM chunks 
    WHERE chunk_type = 'sentence' 
    LIMIT 100000
);

\echo 'Batch 2 complete'

-- Check remaining
SELECT COUNT(*) as remaining_sentences FROM chunks WHERE chunk_type = 'sentence';