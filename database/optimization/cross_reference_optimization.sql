-- Cross-Reference Performance Optimization
-- Dr. Sarah Chen (陈雪芳) - Database Systems Librarian
-- Goal: Reduce cross-reference search from 4-12s to <500ms

-- ===============================================
-- 1. Create materialized view for book statistics
-- ===============================================

-- Drop existing if it exists
DROP MATERIALIZED VIEW IF EXISTS book_match_counts;

-- Create materialized view with book chunk statistics
CREATE MATERIALIZED VIEW book_match_counts AS
SELECT 
    b.book_id,
    b.title,
    b.author,
    COUNT(c.chunk_id) as total_chunks,
    COUNT(CASE WHEN c.chunk_type IN ('chapter', 'section') THEN 1 END) as searchable_chunks,
    SUM(c.word_count) as total_words,
    MAX(c.chapter_number) as max_chapter,
    NOW() as last_updated
FROM books b
LEFT JOIN chunks c ON b.book_id = c.book_id
GROUP BY b.book_id, b.title, b.author;

-- Create index on the materialized view
CREATE INDEX idx_book_match_counts_book_id ON book_match_counts(book_id);
CREATE INDEX idx_book_match_counts_chunks ON book_match_counts(total_chunks DESC);

-- ===============================================
-- 2. Create book_chunk_count column in books table
-- ===============================================

-- Add pre-computed chunk count to books table
ALTER TABLE books ADD COLUMN IF NOT EXISTS chunk_count INTEGER DEFAULT 0;
ALTER TABLE books ADD COLUMN IF NOT EXISTS searchable_chunk_count INTEGER DEFAULT 0;

-- Populate the new columns
UPDATE books 
SET 
    chunk_count = (
        SELECT COUNT(*) 
        FROM chunks 
        WHERE chunks.book_id = books.book_id
    ),
    searchable_chunk_count = (
        SELECT COUNT(*) 
        FROM chunks 
        WHERE chunks.book_id = books.book_id 
        AND chunk_type IN ('chapter', 'section')
    );

-- Create index on the new columns
CREATE INDEX IF NOT EXISTS idx_books_chunk_count ON books(chunk_count DESC);
CREATE INDEX IF NOT EXISTS idx_books_searchable_chunk_count ON books(searchable_chunk_count DESC);

-- ===============================================
-- 3. Optimized cross-reference query
-- ===============================================

-- Function to refresh book statistics
CREATE OR REPLACE FUNCTION refresh_book_statistics()
RETURNS VOID AS $$
BEGIN
    -- Refresh materialized view
    REFRESH MATERIALIZED VIEW book_match_counts;
    
    -- Update books table chunk counts
    UPDATE books 
    SET 
        chunk_count = (
            SELECT COUNT(*) 
            FROM chunks 
            WHERE chunks.book_id = books.book_id
        ),
        searchable_chunk_count = (
            SELECT COUNT(*) 
            FROM chunks 
            WHERE chunks.book_id = books.book_id 
            AND chunk_type IN ('chapter', 'section')
        );
    
    RAISE NOTICE 'Book statistics refreshed successfully';
END;
$$ LANGUAGE plpgsql;

-- ===============================================
-- 4. Trigger to keep statistics up to date
-- ===============================================

-- Function to update book stats when chunks change
CREATE OR REPLACE FUNCTION update_book_chunk_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE books 
        SET 
            chunk_count = chunk_count + 1,
            searchable_chunk_count = CASE 
                WHEN NEW.chunk_type IN ('chapter', 'section') 
                THEN searchable_chunk_count + 1 
                ELSE searchable_chunk_count 
            END
        WHERE book_id = NEW.book_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE books 
        SET 
            chunk_count = chunk_count - 1,
            searchable_chunk_count = CASE 
                WHEN OLD.chunk_type IN ('chapter', 'section') 
                THEN searchable_chunk_count - 1 
                ELSE searchable_chunk_count 
            END
        WHERE book_id = OLD.book_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS trigger_update_book_chunk_count ON chunks;
CREATE TRIGGER trigger_update_book_chunk_count
    AFTER INSERT OR DELETE ON chunks
    FOR EACH ROW
    EXECUTE FUNCTION update_book_chunk_count();

-- ===============================================
-- 5. Performance analysis view
-- ===============================================

CREATE OR REPLACE VIEW cross_reference_performance AS
SELECT 
    'cross_reference_optimization' as optimization_type,
    COUNT(*) as total_books,
    AVG(chunk_count) as avg_chunks_per_book,
    MAX(chunk_count) as max_chunks_per_book,
    SUM(chunk_count) as total_chunks,
    'Ready for optimized cross-reference queries' as status
FROM books 
WHERE chunk_count > 0;

-- ===============================================
-- 6. Dr. Chen's Performance Notes
-- ===============================================

-- Performance improvement summary:
-- Before: SELECT with COUNT(*) OVER (PARTITION BY b.book_id) - scans all chunks
-- After: Simple JOIN with pre-computed book.chunk_count - O(1) lookup
-- Expected improvement: 4-12s → <500ms (90%+ faster)

COMMENT ON MATERIALIZED VIEW book_match_counts IS 
'Dr. Sarah Chen optimization: Pre-computed book statistics for cross-reference performance';

COMMENT ON FUNCTION refresh_book_statistics() IS 
'Maintenance function to keep book statistics current - run during low traffic periods';

-- Manual refresh command for immediate effect
SELECT refresh_book_statistics();

-- Verify optimization is working
SELECT * FROM cross_reference_performance;

-- Test query performance (should be much faster now)
EXPLAIN ANALYZE
SELECT 
    c.chunk_id, c.book_id, c.chapter_number, c.section_number,
    c.content, c.word_count, c.chunk_type,
    b.title, b.author,
    b.chunk_count as book_match_count,  -- Pre-computed instead of window function
    ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', 'artificial intelligence')) as relevance
FROM chunks c
JOIN books b ON c.book_id = b.book_id
WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', 'artificial intelligence')
ORDER BY b.chunk_count DESC, relevance DESC
LIMIT 20;