-- Enhanced Phonetic Search Function - Dr. Sarah Chen
-- ==================================================
-- Ultra-fast phonetic search with intelligent scoring and match classification
-- Target: Sub-second response times with comprehensive phonetic matching

-- Drop existing function if it exists
DROP FUNCTION IF EXISTS api_ultra_fast_phonetic_search(text, integer, real);

-- Create the enhanced phonetic search function
CREATE OR REPLACE FUNCTION api_ultra_fast_phonetic_search(
    search_query text,
    search_limit integer DEFAULT 10,
    phonetic_threshold real DEFAULT 0.3
)
RETURNS TABLE(
    chunk_id varchar(255),
    content_preview text,
    title varchar(500),
    author varchar(255),
    book_id integer,
    phonetic_score real,
    match_type text,
    confidence_level text
) AS $$
DECLARE
    query_soundex text;
    query_metaphone text;
BEGIN
    -- Pre-compute phonetic representations of search query
    query_soundex := soundex(search_query);
    query_metaphone := metaphone(search_query, 6);
    
    RETURN QUERY 
    WITH phonetic_matches AS (
        SELECT 
            c.chunk_id,
            c.content,
            b.title,
            b.author,
            c.book_id,
            -- Advanced phonetic scoring algorithm
            GREATEST(
                -- Exact text match (highest priority)
                ts_rank_cd(
                    to_tsvector('english', c.content), 
                    plainto_tsquery('english', search_query)
                ) * 1.0,
                -- Audiobook normalized match (high priority)
                COALESCE(
                    ts_rank_cd(
                        to_tsvector('english', c.content_audiobook_normalized), 
                        plainto_tsquery('english', search_query)
                    ), 0
                ) * 0.9,
                -- Soundex similarity (phonetic matching)
                COALESCE(
                    similarity(c.content_soundex, query_soundex), 0
                ) * 0.75,
                -- Metaphone similarity (advanced phonetic)
                COALESCE(
                    similarity(c.content_metaphone, query_metaphone), 0
                ) * 0.8,
                -- Trigram similarity fallback
                COALESCE(
                    similarity(c.content, search_query), 0
                ) * 0.6
            ) as calculated_score,
            -- Determine match type for debugging and optimization
            CASE 
                WHEN to_tsvector('english', c.content) @@ plainto_tsquery('english', search_query) THEN 'exact_text'
                WHEN COALESCE(to_tsvector('english', c.content_audiobook_normalized), 'empty'::tsvector) @@ plainto_tsquery('english', search_query) THEN 'audiobook_normalized'
                WHEN COALESCE(similarity(c.content_soundex, query_soundex), 0) > phonetic_threshold THEN 'soundex_phonetic'
                WHEN COALESCE(similarity(c.content_metaphone, query_metaphone), 0) > phonetic_threshold THEN 'metaphone_phonetic'
                WHEN COALESCE(similarity(c.content, search_query), 0) > phonetic_threshold THEN 'trigram_similarity'
                ELSE 'low_confidence'
            END as match_classification
        FROM chunks c
        JOIN books b ON c.book_id = b.book_id
        WHERE (
            -- Use our optimized indexes for maximum performance
            to_tsvector('english', c.content) @@ plainto_tsquery('english', search_query)
            OR COALESCE(to_tsvector('english', c.content_audiobook_normalized), 'empty'::tsvector) @@ plainto_tsquery('english', search_query)
            OR COALESCE(similarity(c.content_soundex, query_soundex), 0) > phonetic_threshold
            OR COALESCE(similarity(c.content_metaphone, query_metaphone), 0) > phonetic_threshold
            OR COALESCE(similarity(c.content, search_query), 0) > phonetic_threshold
        )
        AND c.content IS NOT NULL
        AND LENGTH(c.content) > 10  -- Filter out very short chunks
    ),
    scored_results AS (
        SELECT 
            pm.*,
            -- Confidence level based on score and match type
            CASE 
                WHEN pm.calculated_score > 0.8 THEN 'high'
                WHEN pm.calculated_score > 0.5 THEN 'medium'
                WHEN pm.calculated_score > phonetic_threshold THEN 'low'
                ELSE 'very_low'
            END as confidence_classification
        FROM phonetic_matches pm
        WHERE pm.calculated_score > phonetic_threshold
    )
    SELECT 
        sr.chunk_id,
        -- Create smart content preview with search term highlighting context
        CASE 
            WHEN LENGTH(sr.content) <= 300 THEN sr.content
            ELSE LEFT(sr.content, 200) || '...'
        END as content_preview,
        sr.title,
        sr.author,
        sr.book_id,
        sr.calculated_score::real as phonetic_score,
        sr.match_classification as match_type,
        sr.confidence_classification as confidence_level
    FROM scored_results sr
    ORDER BY 
        sr.calculated_score DESC,
        -- Secondary sort by match type preference
        CASE sr.match_classification
            WHEN 'exact_text' THEN 1
            WHEN 'audiobook_normalized' THEN 2  
            WHEN 'metaphone_phonetic' THEN 3
            WHEN 'soundex_phonetic' THEN 4
            WHEN 'trigram_similarity' THEN 5
            ELSE 6
        END,
        sr.book_id
    LIMIT search_limit;
    
END;
$$ LANGUAGE plpgsql;

-- Create optimized author search function
CREATE OR REPLACE FUNCTION api_fast_author_phonetic_search(
    author_query text,
    search_limit integer DEFAULT 10
)
RETURNS TABLE(
    author varchar(255),
    book_count bigint,
    similarity_score real,
    match_type text
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        b.author,
        COUNT(*) as book_count,
        GREATEST(
            similarity(b.author, author_query),
            COALESCE(similarity(soundex(b.author), soundex(author_query)), 0) * 0.8,
            COALESCE(similarity(metaphone(b.author, 4), metaphone(author_query, 4)), 0) * 0.9
        ) as similarity_score,
        CASE 
            WHEN similarity(b.author, author_query) > 0.6 THEN 'exact_similarity'
            WHEN similarity(soundex(b.author), soundex(author_query)) > 0.3 THEN 'soundex_match'
            WHEN similarity(metaphone(b.author, 4), metaphone(author_query, 4)) > 0.3 THEN 'metaphone_match'
            ELSE 'trigram_match'
        END as match_type
    FROM books b
    WHERE (
        similarity(b.author, author_query) > 0.2
        OR similarity(soundex(b.author), soundex(author_query)) > 0.2
        OR similarity(metaphone(b.author, 4), metaphone(author_query, 4)) > 0.2
    )
    AND b.author IS NOT NULL
    GROUP BY b.author
    ORDER BY similarity_score DESC
    LIMIT search_limit;
END;
$$ LANGUAGE plpgsql;

-- Performance testing query
-- Run this to test the new function performance
/*
SELECT 
    'Function deployed successfully' as status,
    COUNT(*) as total_functions
FROM information_schema.routines 
WHERE routine_name IN ('api_ultra_fast_phonetic_search', 'api_fast_author_phonetic_search');
*/