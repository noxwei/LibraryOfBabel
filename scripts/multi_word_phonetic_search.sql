-- Multi-Word Phonetic Search Function
-- Enhanced search supporting multiple words with phonetic matching

CREATE OR REPLACE FUNCTION api_multi_word_phonetic_search(
    search_query text,
    search_limit integer DEFAULT 10,
    match_threshold real DEFAULT 0.3
)
RETURNS TABLE(
    chunk_id varchar(255),
    content_preview text,
    title varchar(500),
    author varchar(255),
    word_matches integer,
    total_words integer,
    match_percentage real,
    phonetic_score real,
    match_types text
) AS $$
DECLARE
    words_array text[];
    word_count integer;
BEGIN
    -- Split search query into words
    words_array := string_to_array(lower(trim(search_query)), ' ');
    word_count := array_length(words_array, 1);
    
    RETURN QUERY 
    WITH word_matching AS (
        SELECT 
            c.chunk_id,
            c.content,
            b.title,
            b.author,
            -- Count exact text matches
            (
                SELECT COUNT(*)
                FROM unnest(words_array) AS word
                WHERE c.content ILIKE '%' || word || '%'
            ) as exact_matches,
            -- Count audiobook normalized matches
            (
                SELECT COUNT(*)
                FROM unnest(words_array) AS word
                WHERE c.content_audiobook_normalized ILIKE '%' || word || '%'
            ) as normalized_matches,
            -- Count soundex matches
            (
                SELECT COUNT(*)
                FROM unnest(words_array) AS word
                WHERE c.content_soundex LIKE '%' || soundex(word) || '%'
            ) as soundex_matches,
            -- Count metaphone matches  
            (
                SELECT COUNT(*)
                FROM unnest(words_array) AS word
                WHERE c.content_metaphone LIKE '%' || metaphone(word, 4) || '%'
            ) as metaphone_matches
        FROM chunks c
        JOIN books b ON c.book_id = b.book_id
        WHERE c.content IS NOT NULL
        AND (
            -- At least one word must match in some form
            EXISTS (
                SELECT 1 FROM unnest(words_array) AS word
                WHERE c.content ILIKE '%' || word || '%'
                   OR c.content_audiobook_normalized ILIKE '%' || word || '%'
                   OR c.content_soundex LIKE '%' || soundex(word) || '%'
                   OR c.content_metaphone LIKE '%' || metaphone(word, 4) || '%'
            )
        )
    ),
    scored_results AS (
        SELECT 
            wm.*,
            -- Calculate total matches across all methods
            GREATEST(wm.exact_matches, wm.normalized_matches, wm.soundex_matches, wm.metaphone_matches) as best_word_matches,
            -- Calculate match percentage
            (GREATEST(wm.exact_matches, wm.normalized_matches, wm.soundex_matches, wm.metaphone_matches)::real / word_count::real) as match_ratio,
            -- Calculate weighted score
            (
                wm.exact_matches * 1.0 +
                wm.normalized_matches * 0.9 +
                wm.metaphone_matches * 0.8 +
                wm.soundex_matches * 0.7
            ) / word_count::real as weighted_score,
            -- Determine match types found
            ARRAY_TO_STRING(ARRAY[
                CASE WHEN wm.exact_matches > 0 THEN 'exact' ELSE NULL END,
                CASE WHEN wm.normalized_matches > 0 THEN 'normalized' ELSE NULL END,
                CASE WHEN wm.metaphone_matches > 0 THEN 'metaphone' ELSE NULL END,
                CASE WHEN wm.soundex_matches > 0 THEN 'soundex' ELSE NULL END
            ]::text[], ', ') as match_type_list
        FROM word_matching wm
        WHERE (wm.exact_matches + wm.normalized_matches + wm.soundex_matches + wm.metaphone_matches) > 0
    )
    SELECT 
        sr.chunk_id,
        LEFT(sr.content, 300) as content_preview,
        sr.title,
        sr.author,
        sr.best_word_matches::integer,
        word_count::integer,
        ROUND(sr.match_ratio * 100, 1) as match_percentage,
        ROUND(sr.weighted_score, 3) as phonetic_score,
        sr.match_type_list as match_types
    FROM scored_results sr
    WHERE sr.match_ratio >= match_threshold
    ORDER BY 
        sr.weighted_score DESC,
        sr.best_word_matches DESC,
        sr.match_ratio DESC
    LIMIT search_limit;
END;
$$ LANGUAGE plpgsql;

-- Test queries with increasing complexity
SELECT '=== Testing Multi-Word Phonetic Search ===' as test_header;

-- Test 1: 2 words
SELECT 'Test 1: Two Words' as test_name;
SELECT * FROM api_multi_word_phonetic_search('philosophy consciousness', 3, 0.5);

-- Test 2: 3 words  
SELECT 'Test 2: Three Words' as test_name;
SELECT * FROM api_multi_word_phonetic_search('philosophy consciousness freedom', 3, 0.3);

-- Test 3: 4 words
SELECT 'Test 3: Four Words' as test_name;
SELECT * FROM api_multi_word_phonetic_search('philosophy consciousness freedom democracy', 3, 0.25);

-- Test 4: 5 words
SELECT 'Test 4: Five Words' as test_name;
SELECT * FROM api_multi_word_phonetic_search('philosophy consciousness freedom democracy power', 3, 0.2);

-- Test 5: 6+ words with common misspellings
SELECT 'Test 5: Six Words with Phonetic Variants' as test_name;
SELECT * FROM api_multi_word_phonetic_search('filosofy conciousness there house listen carefully', 3, 0.15);