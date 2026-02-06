-- Backup and delete FULLBOOK chunks (entire books stored as single chunks)
-- These are un-embeddable garbage polluting the embedding queue
-- Created: 2026-02-06

-- Step 1: Check how many FULLBOOK chunks exist
SELECT COUNT(*) as fullbook_chunks_count FROM chunks WHERE chunk_id LIKE 'FULLBOOK%';

-- Step 2: Backup FULLBOOK chunk metadata before deletion
-- (Not backing up content since these are entire books - too large and already in books table)
CREATE TEMP TABLE backup_fullbook_chunks AS
SELECT chunk_id, book_id, chunk_type, character_count, word_count, created_at
FROM chunks
WHERE chunk_id LIKE 'FULLBOOK%';

-- Step 3: Show what we're deleting
SELECT COUNT(*) as chunks_to_delete FROM backup_fullbook_chunks;
SELECT chunk_type, COUNT(*) as count,
       AVG(character_count) as avg_chars,
       MAX(character_count) as max_chars
FROM backup_fullbook_chunks
GROUP BY chunk_type;

-- Step 4: Show sample
SELECT * FROM backup_fullbook_chunks LIMIT 10;

-- Step 5: Export backup chunk_ids to file (run from psql):
-- \COPY (SELECT chunk_id FROM chunks WHERE chunk_id LIKE 'FULLBOOK%') TO 'fullbook_chunk_ids_backup.txt'

-- Step 6: Delete FULLBOOK chunks
-- UNCOMMENT THE LINE BELOW TO EXECUTE:
-- DELETE FROM chunks WHERE chunk_id LIKE 'FULLBOOK%';

-- Step 7: Verify deletion
-- SELECT COUNT(*) as remaining_fullbook FROM chunks WHERE chunk_id LIKE 'FULLBOOK%';
