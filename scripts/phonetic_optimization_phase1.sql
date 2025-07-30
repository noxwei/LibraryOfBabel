-- Phonetic Search Optimization Phase 1
-- Dr. Sarah Chen's Performance Enhancement Implementation
-- ====================================================
-- Target: Sub-second search performance through composite indexing
-- Expected: 70-80% performance improvement

-- Enable extensions if not already enabled
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Phase 1.1: Composite Phonetic Index for Multi-Field Search
-- This index will dramatically speed up complex phonetic searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunks_phonetic_composite 
ON chunks USING gin((
    setweight(to_tsvector('english', content), 'A') ||
    setweight(to_tsvector('english', COALESCE(content_audiobook_normalized, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(content_soundex, '')), 'C') ||
    setweight(to_tsvector('english', COALESCE(content_metaphone, '')), 'D')
));

-- Phase 1.2: Trigram Index for Fuzzy Author Name Matching
-- Essential for handling author name misspellings like "Foucault" vs "Focault"
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_books_author_trigram 
ON books USING gin(author gin_trgm_ops);

-- Phase 1.3: Book Title Phonetic Search Index
-- Optimized for book title searches with phonetic matching
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_books_title_phonetic 
ON books USING gin(to_tsvector('english', title));

-- Phase 1.4: Soundex Performance Index
-- Dedicated index for soundex-based searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunks_soundex_performance
ON chunks USING btree(content_soundex) 
WHERE content_soundex IS NOT NULL;

-- Phase 1.5: Metaphone Performance Index  
-- Dedicated index for metaphone-based searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunks_metaphone_performance
ON chunks USING btree(content_metaphone)
WHERE content_metaphone IS NOT NULL;

-- Phase 1.6: Combined Book-Chunk Performance Index
-- For joining chunks with book information efficiently
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunks_book_performance
ON chunks USING btree(book_id, chunk_id);

-- Performance Analysis Query
-- Run this to verify index usage and performance
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan
FROM pg_stat_user_indexes 
WHERE indexname LIKE '%phonetic%' OR indexname LIKE '%trigram%'
ORDER BY idx_scan DESC;

-- Verify all phonetic extensions and indexes are ready
SELECT 
    'Extensions' as category,
    extname as name,
    'INSTALLED' as status
FROM pg_extension 
WHERE extname IN ('fuzzystrmatch', 'pg_trgm')
UNION ALL
SELECT 
    'Indexes' as category,
    indexname as name,
    CASE 
        WHEN indisvalid THEN 'READY'
        ELSE 'BUILDING'
    END as status
FROM pg_indexes pi
JOIN pg_index pgi ON pi.indexname = pgi.indexname::text
WHERE pi.indexname LIKE '%phonetic%' 
   OR pi.indexname LIKE '%trigram%'
   OR pi.indexname LIKE '%soundex%'
   OR pi.indexname LIKE '%metaphone%'
ORDER BY category, name;