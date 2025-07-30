-- Fixed Multi-Word Phonetic Search Function

CREATE OR REPLACE FUNCTION api_multi_word_phonetic_search(
    search_query text,
    search_limit integer DEFAULT 10
)
RETURNS TABLE(
    chunk_id varchar(255),
    content_preview text,
    title varchar(500),
    author varchar(255),
    word_matches integer,
    total_words integer,
    phonetic_score real,
    match_types text
) AS $$
DECLARE
    words_array text[];
    word_count integer;
BEGIN
    -- Split search query into words and clean them
    words_array := string_to_array(lower(trim(search_query)), ' ');
    word_count := array_length(words_array, 1);
    
    RETURN QUERY 
    WITH word_matching AS (
        SELECT 
            c.chunk_id,
            c.content,
            b.title,
            b.author,
            -- Count matches across different methods
            (
                SELECT COUNT(*)
                FROM unnest(words_array) AS word
                WHERE c.content ILIKE '%' || word || '%'
            ) +
            (
                SELECT COUNT(*)
                FROM unnest(words_array) AS word
                WHERE c.content_audiobook_normalized ILIKE '%' || word || '%'
                  AND c.content NOT ILIKE '%' || word || '%'  -- Don't double-count
            ) as total_matches,
            -- Track match types
            CASE 
                WHEN EXISTS (
                    SELECT 1 FROM unnest(words_array) AS word
                    WHERE c.content ILIKE '%' || word || '%'
                ) THEN 'exact'
                ELSE ''
            END ||
            CASE 
                WHEN EXISTS (
                    SELECT 1 FROM unnest(words_array) AS word
                    WHERE c.content_audiobook_normalized ILIKE '%' || word || '%'
                ) THEN ',normalized'
                ELSE ''
            END as match_type_info
        FROM chunks c
        JOIN books b ON c.book_id = b.book_id
        WHERE c.content IS NOT NULL
        AND (
            EXISTS (
                SELECT 1 FROM unnest(words_array) AS word
                WHERE c.content ILIKE '%' || word || '%'
                   OR c.content_audiobook_normalized ILIKE '%' || word || '%'
            )
        )
    )
    SELECT 
        wm.chunk_id,
        LEFT(wm.content, 250) as content_preview,
        wm.title,
        wm.author,
        wm.total_matches::integer,
        word_count::integer,
        (wm.total_matches::real / word_count::real)::real as phonetic_score,
        TRIM(LEADING ',' FROM wm.match_type_info) as match_types
    FROM word_matching wm
    WHERE wm.total_matches > 0
    ORDER BY 
        wm.total_matches DESC,
        (wm.total_matches::real / word_count::real) DESC
    LIMIT search_limit;
END;
$$ LANGUAGE plpgsql;

-- Test the function with multiple word counts
SELECT '=== Multi-Word Phonetic Search Tests ===' as header;

-- Test 2 words
SELECT 'Test: 2 words - philosophy power' as test_description;
SELECT * FROM api_multi_word_phonetic_search('philosophy power', 3);

-- Test 3 words
SELECT 'Test: 3 words - philosophy consciousness freedom' as test_description;
SELECT * FROM api_multi_word_phonetic_search('philosophy consciousness freedom', 3);

-- Test 4 words
SELECT 'Test: 4 words - philosophy consciousness freedom democracy' as test_description; 
SELECT * FROM api_multi_word_phonetic_search('philosophy consciousness freedom democracy', 3);

-- Test 5 words
SELECT 'Test: 5 words - philosophy consciousness freedom democracy power' as test_description;
SELECT * FROM api_multi_word_phonetic_search('philosophy consciousness freedom democracy power', 3);

-- Test 6 words with phonetic variants
SELECT 'Test: 6 words - filosofy conciousness there house listen carefully' as test_description;
SELECT * FROM api_multi_word_phonetic_search('filosofy conciousness there house listen carefully', 3);

-- Test 7+ words - complex query
SELECT 'Test: 7+ words - human nature society government political freedom individual rights' as test_description;
SELECT * FROM api_multi_word_phonetic_search('human nature society government political freedom individual rights', 3);

-- Performance comparison
SELECT 'Performance test - counting matches by word count' as perf_test;
SELECT 
    CASE 
        WHEN word_count = 2 THEN '2 words'
        WHEN word_count = 3 THEN '3 words' 
        WHEN word_count = 4 THEN '4 words'
        WHEN word_count = 5 THEN '5 words'
        ELSE '6+ words'
    END as word_group,
    COUNT(*) as result_count,
    AVG(phonetic_score) as avg_score
FROM (
    SELECT *, array_length(string_to_array(lower(trim('philosophy power')), ' '), 1) as word_count FROM api_multi_word_phonetic_search('philosophy power', 100)
    UNION ALL
    SELECT *, array_length(string_to_array(lower(trim('philosophy consciousness freedom')), ' '), 1) as word_count FROM api_multi_word_phonetic_search('philosophy consciousness freedom', 100)
    UNION ALL
    SELECT *, array_length(string_to_array(lower(trim('philosophy consciousness freedom democracy')), ' '), 1) as word_count FROM api_multi_word_phonetic_search('philosophy consciousness freedom democracy', 100)
) subq
GROUP BY word_count
ORDER BY word_count;