-- Simple Phonetic Search Test
-- Optimized version for testing performance

-- Create a simplified phonetic search function for testing
CREATE OR REPLACE FUNCTION api_simple_phonetic_test(
    search_query text,
    search_limit integer DEFAULT 10
)
RETURNS TABLE(
    chunk_id varchar(255),
    content_preview text,
    title varchar(500),
    author varchar(255),
    match_score real,
    match_type text
) AS $$
BEGIN
    RETURN QUERY 
    SELECT 
        c.chunk_id,
        LEFT(c.content, 200) as content_preview,
        b.title,
        b.author,
        -- Simple scoring based on text search
        CASE 
            WHEN c.content ILIKE '%' || search_query || '%' THEN 1.0
            WHEN c.content_audiobook_normalized ILIKE '%' || lower(search_query) || '%' THEN 0.8
            ELSE 0.5
        END::real as match_score,
        CASE 
            WHEN c.content ILIKE '%' || search_query || '%' THEN 'exact_text'
            WHEN c.content_audiobook_normalized ILIKE '%' || lower(search_query) || '%' THEN 'audiobook_normalized'
            ELSE 'phonetic_match'
        END as match_type
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE (
        c.content ILIKE '%' || search_query || '%'
        OR c.content_audiobook_normalized ILIKE '%' || lower(search_query) || '%'
    )
    AND c.content IS NOT NULL
    ORDER BY match_score DESC
    LIMIT search_limit;
END;
$$ LANGUAGE plpgsql;

-- Test the simple function
SELECT 
    'Simple Phonetic Test' as test_name,
    COUNT(*) as result_count
FROM api_simple_phonetic_test('philosophy', 10);

-- Show actual results
SELECT 
    chunk_id,
    LEFT(content_preview, 80) as short_preview,
    author,
    match_score,
    match_type
FROM api_simple_phonetic_test('philosophy', 5);