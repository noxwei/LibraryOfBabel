-- 🎭 Fiction Book Queries for Lexi (Audio Synthesis Agent)
-- =========================================================
-- 
-- Dr. Sarah Chen's optimized PostgreSQL queries for fiction book selection
-- Designed specifically for Lexi's TTS testing needs
--
-- Database: knowledge_base
-- Tables: books, chunks, authors
-- Purpose: Select diverse fiction books for audio synthesis testing

-- =============================================================================
-- QUERY 1: Basic Fiction Book Selection (15 books)
-- =============================================================================
-- Simple query to get 15 fiction books with essential metadata

SELECT 
    book_id,
    title,
    author,
    genre,
    word_count,
    CASE 
        WHEN word_count BETWEEN 40000 AND 80000 THEN 'Short (2-3 hours audio)'
        WHEN word_count BETWEEN 80000 AND 120000 THEN 'Medium (3-5 hours audio)' 
        WHEN word_count BETWEEN 120000 AND 200000 THEN 'Long (5-8 hours audio)'
        WHEN word_count > 200000 THEN 'Epic (8+ hours audio)'
        ELSE 'Variable length'
    END as estimated_audio_length,
    LEFT(description, 200) || '...' as description_preview
FROM books 
WHERE 
    (genre ILIKE '%fiction%' OR genre = 'Fiction')
    AND word_count >= 40000  -- Minimum viable length for TTS testing
    AND title IS NOT NULL 
    AND author IS NOT NULL
ORDER BY word_count DESC
LIMIT 15;

-- =============================================================================
-- QUERY 2: Genre-Diverse Fiction Selection (Recommended for Lexi)
-- =============================================================================
-- Advanced query ensuring genre diversity for comprehensive TTS voice testing

WITH fiction_books AS (
    SELECT 
        b.book_id,
        b.title,
        b.author,
        b.genre,
        b.word_count,
        b.description,
        b.publication_year,
        COUNT(c.chunk_id) as chunk_count,
        
        -- TTS-specific categorization
        CASE 
            WHEN b.word_count BETWEEN 40000 AND 80000 THEN 'Short'
            WHEN b.word_count BETWEEN 80000 AND 120000 THEN 'Medium' 
            WHEN b.word_count BETWEEN 120000 AND 200000 THEN 'Long'
            WHEN b.word_count > 200000 THEN 'Epic'
            ELSE 'Variable'
        END as length_category,
        
        -- Genre priority for diversity (ensures variety in selection)
        CASE 
            WHEN b.genre ILIKE '%literary%' THEN 1  -- Literary fiction
            WHEN b.genre ILIKE '%science fiction%' THEN 2  -- Sci-fi 
            WHEN b.genre ILIKE '%fantasy%' THEN 3  -- Fantasy
            WHEN b.genre ILIKE '%historical%' THEN 4  -- Historical
            WHEN b.genre ILIKE '%mystery%' OR b.genre ILIKE '%thriller%' THEN 5  -- Mystery
            WHEN b.genre ILIKE '%romance%' THEN 6  -- Romance
            WHEN b.genre ILIKE '%contemporary%' THEN 7  -- Contemporary
            ELSE 8  -- Other fiction
        END as genre_priority,
        
        -- Estimated reading time for TTS planning
        ROUND(b.word_count / 250.0 / 60.0, 1) as estimated_hours
        
    FROM books b
    LEFT JOIN chunks c ON b.book_id = c.book_id
    WHERE 
        -- Fiction filters
        (b.genre ILIKE '%fiction%' OR b.genre = 'Fiction' OR b.genre ILIKE '%novel%')
        -- Quality filters for TTS
        AND b.word_count >= 40000
        AND b.title IS NOT NULL 
        AND b.author IS NOT NULL
        AND b.author != 'Unknown'
        AND LENGTH(COALESCE(b.description, '')) > 50
    GROUP BY 
        b.book_id, b.title, b.author, b.genre, 
        b.word_count, b.description, b.publication_year
    HAVING 
        COUNT(c.chunk_id) > 3  -- Ensure sufficient text chunks available
),
diverse_selection AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY genre_priority 
            ORDER BY chunk_count DESC, RANDOM()
        ) as genre_rank
    FROM fiction_books
)
SELECT 
    book_id,
    title,
    author,
    genre,
    word_count,
    estimated_hours || ' hours' as estimated_audio_time,
    length_category,
    chunk_count,
    LEFT(description, 150) || '...' as synopsis
FROM diverse_selection
WHERE genre_rank <= 2  -- Max 2 books per genre category
ORDER BY genre_priority, estimated_hours DESC
LIMIT 15;

-- =============================================================================
-- QUERY 3: Get Sample Text Chunks for TTS Testing
-- =============================================================================
-- Use this query with a specific book_id to get text samples for voice testing

SELECT 
    chunk_id,
    title as chunk_title,
    LEFT(content, 500) || '...' as content_sample,
    word_count,
    chapter_number,
    CASE 
        WHEN chapter_number <= 2 THEN 'Opening - Character introduction'
        WHEN chapter_number >= (
            SELECT MAX(chapter_number) * 0.8 
            FROM chunks 
            WHERE book_id = 1 -- Replace with actual book_id
        ) THEN 'Climax - High tension sections'
        ELSE 'Middle - Character development'
    END as narrative_section
FROM chunks 
WHERE 
    book_id = 1  -- Replace with the book_id you want samples from
    AND content IS NOT NULL
    AND word_count BETWEEN 150 AND 400  -- Ideal chunk size for TTS samples
    AND LENGTH(content) > 200
ORDER BY chapter_number
LIMIT 5;

-- =============================================================================
-- QUERY 4: Fiction Books by Audio Length (TTS Planning)
-- =============================================================================
-- Organize fiction books by estimated audio length for systematic TTS testing

SELECT 
    CASE 
        WHEN word_count BETWEEN 40000 AND 80000 THEN 'Short (2-3 hours)'
        WHEN word_count BETWEEN 80000 AND 120000 THEN 'Medium (3-5 hours)' 
        WHEN word_count BETWEEN 120000 AND 200000 THEN 'Long (5-8 hours)'
        WHEN word_count > 200000 THEN 'Epic (8+ hours)'
    END as audio_length_category,
    COUNT(*) as book_count,
    AVG(word_count) as avg_words,
    STRING_AGG(title || ' by ' || author, '; ' ORDER BY word_count DESC) as sample_books
FROM books 
WHERE 
    (genre ILIKE '%fiction%' OR genre = 'Fiction')
    AND word_count >= 40000
    AND title IS NOT NULL
GROUP BY 
    CASE 
        WHEN word_count BETWEEN 40000 AND 80000 THEN 'Short (2-3 hours)'
        WHEN word_count BETWEEN 80000 AND 120000 THEN 'Medium (3-5 hours)' 
        WHEN word_count BETWEEN 120000 AND 200000 THEN 'Long (5-8 hours)'
        WHEN word_count > 200000 THEN 'Epic (8+ hours)'
    END
ORDER BY AVG(word_count);

-- =============================================================================
-- QUERY 5: Using Dr. Sarah Chen's API Function (Recommended)
-- =============================================================================
-- Use the optimized PostgreSQL function for paginated fiction search

-- Get fiction books using the API function
SELECT * FROM api_list_books(
    1,          -- page number
    15,         -- page size (15 books for Lexi)
    NULL,       -- search query (null for all)
    NULL,       -- author filter (null for all authors)
    'Fiction'   -- genre filter (fiction only)
);

-- Alternative: Get various fiction subgenres
SELECT * FROM api_list_books(1, 5, NULL, NULL, 'Literary Fiction')
UNION ALL
SELECT * FROM api_list_books(1, 5, NULL, NULL, 'Science Fiction')
UNION ALL
SELECT * FROM api_list_books(1, 5, NULL, NULL, 'Fantasy');

-- =============================================================================
-- QUERY 6: Fiction Book Statistics for TTS Planning
-- =============================================================================
-- Get overview statistics to help Lexi plan TTS testing strategy

SELECT 
    'Fiction Collection Overview' as metric,
    COUNT(*) as total_fiction_books,
    SUM(word_count) as total_words,
    ROUND(AVG(word_count)) as avg_words_per_book,
    ROUND(SUM(word_count) / 250.0 / 60.0, 1) as total_estimated_hours,
    COUNT(DISTINCT genre) as unique_genres
FROM books 
WHERE 
    (genre ILIKE '%fiction%' OR genre = 'Fiction')
    AND word_count > 0;

-- Show genre distribution
SELECT 
    genre,
    COUNT(*) as book_count,
    ROUND(AVG(word_count)) as avg_words,
    ROUND(SUM(word_count) / 250.0 / 60.0, 1) as estimated_total_hours
FROM books 
WHERE 
    (genre ILIKE '%fiction%' OR genre = 'Fiction')
    AND word_count > 0
GROUP BY genre
ORDER BY book_count DESC;

-- =============================================================================
-- QUERY 7: Quick Connection Test
-- =============================================================================
-- Simple query to test database connectivity

SELECT 
    'LibraryOfBabel Database Connection Test' as status,
    current_database() as database_name,
    current_user as connected_user,
    now() as connection_time;

-- Count available fiction books
SELECT 
    COUNT(*) as available_fiction_books,
    MIN(word_count) as shortest_book,
    MAX(word_count) as longest_book
FROM books 
WHERE genre ILIKE '%fiction%' AND word_count > 0;

-- =============================================================================
-- USAGE INSTRUCTIONS FOR LEXI
-- =============================================================================

/*
📖 How to Use These Queries:

1. CONNECTION:
   - Connect to PostgreSQL database 'knowledge_base' on localhost:5432
   - Use user 'weixiangzhang' (or set DB_USER environment variable)

2. BASIC SELECTION (Start Here):
   - Run QUERY 1 for simple 15-book fiction selection
   - Results include estimated audio length for TTS planning

3. ADVANCED SELECTION (Recommended):
   - Run QUERY 2 for genre-diverse selection
   - Ensures variety in narrative styles for comprehensive voice testing

4. TEXT SAMPLES:
   - Use QUERY 3 with specific book_id to get text chunks
   - Replace 'book_id = 1' with actual book ID from selection

5. TTS PLANNING:
   - Run QUERY 4 to see books organized by audio length
   - Use QUERY 6 for collection statistics

6. API FUNCTIONS:
   - QUERY 5 uses Dr. Sarah Chen's optimized PostgreSQL functions
   - Provides pagination and advanced filtering

🎤 TTS Testing Strategy:
   - Start with "Short" books for voice calibration
   - Progress to "Medium" and "Long" books for endurance testing
   - Test different genres for voice adaptability
   - Use 3-5 text chunks per book for comprehensive testing

🏛️ Database Schema:
   - books: Main metadata table
   - chunks: Text segments for detailed content
   - authors: Normalized author information

📞 Support:
   - Database issues: Contact Dr. Sarah Chen (DBA Team)
   - Schema documentation: /docs/project_docs/DATABASE_SCHEMA.md
*/