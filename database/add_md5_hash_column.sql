-- 📚 DBA TEAM - MD5 Hash Column Addition
-- ========================================
-- 
-- Adds MD5 hash column for unique book identification
-- Designed by Dr. Sarah Chen (陈雪芳) - Database Systems Librarian
-- Supervised by Linda Zhang (张丽娜) - HR Manager
--
-- Purpose: Prevent duplicate book ingestion using content hash
-- Implementation: UNIQUE constraint prevents duplicate MD5s

BEGIN;

-- Add MD5 hash column to books table
ALTER TABLE books 
ADD COLUMN md5_hash VARCHAR(32);

-- Add unique constraint to prevent duplicate hashes
ALTER TABLE books 
ADD CONSTRAINT books_md5_hash_unique UNIQUE (md5_hash);

-- Create index for fast MD5 lookups
CREATE INDEX idx_books_md5_hash ON books(md5_hash);

-- Add comment for documentation
COMMENT ON COLUMN books.md5_hash IS 'MD5 hash of book content for duplicate detection - Added by DBA Team';

-- Log the schema change
INSERT INTO processing_log (timestamp, operation_type, status, details, processing_time_ms)
VALUES (
    NOW(),
    'schema_modification',
    'success',
    'Added md5_hash column with unique constraint and index - DBA Team implementation',
    0
);

COMMIT;

-- Display confirmation
SELECT 'MD5 hash column successfully added to books table' AS status;