-- =========================================================================
-- Fix Highlighted Search v2 - Use Proper Schema for Similarity
-- =========================================================================

-- Drop the old function
DROP FUNCTION IF EXISTS api_search_content_with_highlights(TEXT, INTEGER, INTEGER) CASCADE;

-- Create working highlighted search without schema-specific functions
CREATE OR REPLACE FUNCTION api_search_content_with_highlights(
    query_text TEXT,
    result_limit INTEGER DEFAULT 10,
    snippet_length INTEGER DEFAULT 200
) RETURNS JSON
LANGUAGE plpgsql
AS $$
BEGIN
    -- Input validation
    IF query_text IS NULL OR LENGTH(TRIM(query_text)) < 3 THEN
        RETURN json_build_object(
            'success', false,
            'error', 'Search term must be at least 3 characters',
            'results', '[]'::json
        );
    END IF;

    -- Fast search using trigram operator and simple scoring
    RETURN (
        WITH trigram_results AS (
            SELECT
                c.chunk_id::VARCHAR(255),
                c.book_id,
                b.title::VARCHAR(255) as book_title,
                b.author::VARCHAR(255) as book_author,
                c.title::VARCHAR(255) as chunk_title,
                c.chapter_number,
                -- Fast highlighting by replacing matched text
                REPLACE(
                    LEFT(c.content, snippet_length),
                    query_text,
                    '<mark>' || query_text || '</mark>'
                ) as highlighted_snippet,
                -- Simple relevance based on position and length
                CASE 
                    WHEN c.content ILIKE '%' || query_text || '%' THEN 1.0
                    ELSE 0.5
                END as relevance,
                c.word_count
            FROM chunks c
            JOIN books b ON c.book_id = b.book_id
            WHERE c.content % query_text  -- Fast trigram match
                AND c.content IS NOT NULL
                AND LENGTH(c.content) >= 50
            ORDER BY 
                CASE WHEN c.content ILIKE '%' || query_text || '%' THEN 1 ELSE 0 END DESC,
                c.word_count DESC
            LIMIT result_limit
        )
        SELECT json_build_object(
            'success', true,
            'search_type', 'trigram_highlighted_passage',
            'query', query_text,
            'results', COALESCE(json_agg(
                json_build_object(
                    'chunk_id', chunk_id,
                    'book_id', book_id,
                    'book_title', book_title,
                    'book_author', book_author,
                    'chunk_title', chunk_title,
                    'chapter_number', chapter_number,
                    'highlighted_snippet', highlighted_snippet,
                    'relevance', relevance,
                    'word_count', word_count
                )
            ), '[]'::json),
            'total_found', COUNT(*),
            'snippet_length', snippet_length,
            'search_method', 'pg_trgm trigram operator (fast)'
        )
        FROM trigram_results
    );
END;
$$;