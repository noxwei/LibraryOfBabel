-- =============================================================================
-- 🚀 TRIGRAM SEARCH ENHANCEMENTS V2 - SOPHISTICATED SEMANTIC SEARCH
-- =============================================================================
-- Dr. Sarah Chen (陈雪芳) PostgreSQL-First Architecture
-- 
-- APPROACH: Create new enhanced functions to avoid signature conflicts
-- =============================================================================

-- =============================================================================
-- 🎯 NEW: api_shortcuts_search_enhanced WITH TRIGRAM SOPHISTICATION
-- =============================================================================
CREATE OR REPLACE FUNCTION api_shortcuts_search_enhanced(
    p_term TEXT,
    p_limit INTEGER DEFAULT 10
)
RETURNS JSON AS $$
DECLARE
    v_total_results INTEGER := 0;
    v_json_result JSON;
BEGIN
    -- Input validation
    IF p_term IS NULL OR LENGTH(TRIM(p_term)) = 0 THEN
        RETURN json_build_object(
            'success', true,
            'data', json_build_object(
                'query', p_term,
                'total_results', 0,
                'results', '[]'::json
            )
        );
    END IF;
    
    -- Count total results
    SELECT COUNT(DISTINCT c.chunk_id) INTO v_total_results
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE (
        c.search_vector @@ plainto_tsquery('english', p_term)
        OR c.content % p_term  -- TRIGRAM MAGIC
        OR c.content ILIKE '%' || p_term || '%'
        OR b.title ILIKE '%' || p_term || '%'
        OR b.author ILIKE '%' || p_term || '%'
    )
    AND c.content IS NOT NULL
    AND LENGTH(c.content) > 50;
    
    -- Enhanced search with trigram sophistication
    SELECT json_build_object(
        'success', true,
        'data', json_build_object(
            'query', p_term,
            'total_results', v_total_results,
            'search_type', 'enhanced_trigram',
            'results', COALESCE(json_agg(
                json_build_object(
                    'chunk_id', c.chunk_id,
                    'content', LEFT(c.content, 400),
                    'book_id', c.book_id,
                    'title', b.title,
                    'author', b.author,
                    'chunk_type', c.chunk_type,
                    'relevance_score', combined_score,
                    'match_type', match_type,
                    'word_count', c.word_count
                ) ORDER BY combined_score DESC
            ), '[]'::json)
        )
    ) INTO v_json_result
    FROM (
        -- ENHANCED SEARCH COMBINING MULTIPLE APPROACHES
        SELECT DISTINCT
            c.chunk_id,
            c.content,
            c.book_id,
            c.chunk_type,
            c.word_count,
            b.title,
            b.author,
            -- SOPHISTICATED SCORING: Combine multiple search methods
            GREATEST(
                -- Traditional FTS (40% weight)
                COALESCE(ts_rank(c.search_vector, plainto_tsquery('english', p_term)) * 0.4, 0),
                -- Trigram similarity (30% weight) - THE MAGIC!
                COALESCE(similarity(c.content, p_term) * 0.3, 0),
                -- Exact phrase bonus (20% weight)
                CASE WHEN c.content ILIKE '%' || p_term || '%' THEN 0.2 ELSE 0 END,
                -- Title/author relevance (10% weight)
                CASE WHEN b.title ILIKE '%' || p_term || '%' OR b.author ILIKE '%' || p_term || '%' THEN 0.1 ELSE 0 END
            ) as combined_score,
            -- Identify match type for transparency
            CASE 
                WHEN c.content % p_term THEN 'trigram_similarity'
                WHEN c.search_vector @@ plainto_tsquery('english', p_term) THEN 'fulltext_search'
                WHEN c.content ILIKE '%' || p_term || '%' THEN 'exact_match'
                ELSE 'title_author_match'
            END as match_type
        FROM chunks c
        JOIN books b ON c.book_id = b.book_id
        WHERE (
            -- Multi-method search conditions
            c.search_vector @@ plainto_tsquery('english', p_term)  -- Traditional FTS
            OR c.content % p_term  -- TRIGRAM SIMILARITY - finds conceptual matches!
            OR c.content ILIKE '%' || p_term || '%'  -- Exact matches
            OR b.title ILIKE '%' || p_term || '%'  -- Title matches
            OR b.author ILIKE '%' || p_term || '%'  -- Author matches
        )
        AND c.content IS NOT NULL
        AND LENGTH(c.content) > 50  -- Quality filter
        ORDER BY combined_score DESC
        LIMIT p_limit
    ) search_results
    JOIN chunks c ON search_results.chunk_id = c.chunk_id
    JOIN books b ON c.book_id = b.book_id;
    
    RETURN v_json_result;
    
EXCEPTION
    WHEN OTHERS THEN
        -- Fallback to basic search if enhanced search fails
        RETURN json_build_object(
            'success', false,
            'error', 'Enhanced search failed: ' || SQLERRM,
            'fallback', 'basic_search_available'
        );
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 🎯 TESTING FUNCTION: Black Technology Validation
-- =============================================================================
CREATE OR REPLACE FUNCTION test_black_technology_search_enhanced()
RETURNS TABLE(
    test_case TEXT,
    result_count INTEGER,
    top_match TEXT,
    match_type TEXT,
    relevance_score REAL
) AS $$
BEGIN
    -- Test Case 1: "Black technology" 
    RETURN QUERY
    WITH black_tech_results AS (
        SELECT 
            c.chunk_id,
            LEFT(c.content, 200) as content_preview,
            GREATEST(
                COALESCE(ts_rank(c.search_vector, plainto_tsquery('english', 'Black technology')) * 0.4, 0),
                COALESCE(similarity(c.content, 'Black technology') * 0.6, 0)
            ) as score,
            CASE 
                WHEN c.content % 'Black technology' THEN 'trigram'
                ELSE 'fts'
            END as match_method
        FROM chunks c
        WHERE (
            c.search_vector @@ plainto_tsquery('english', 'Black technology')
            OR c.content % 'Black technology'
        )
        AND c.content IS NOT NULL
        ORDER BY score DESC
        LIMIT 1
    )
    SELECT 
        'Black technology'::TEXT as test_case,
        (SELECT COUNT(*) FROM (
            SELECT c.chunk_id FROM chunks c 
            WHERE (c.search_vector @@ plainto_tsquery('english', 'Black technology') OR c.content % 'Black technology')
            AND c.content IS NOT NULL
        ) total_results)::INTEGER,
        (SELECT content_preview FROM black_tech_results LIMIT 1)::TEXT,
        (SELECT match_method FROM black_tech_results LIMIT 1)::TEXT,
        (SELECT score FROM black_tech_results LIMIT 1)::REAL;
    
    -- Test Case 2: "racial bias algorithms"
    RETURN QUERY
    WITH racial_algo_results AS (
        SELECT 
            LEFT(c.content, 200) as content_preview,
            similarity(c.content, 'racial bias algorithms') as score
        FROM chunks c
        WHERE c.content % 'racial bias algorithms'
        AND c.content IS NOT NULL
        ORDER BY score DESC
        LIMIT 1
    )
    SELECT 
        'racial bias algorithms'::TEXT,
        (SELECT COUNT(*) FROM chunks c WHERE c.content % 'racial bias algorithms' AND c.content IS NOT NULL)::INTEGER,
        COALESCE((SELECT content_preview FROM racial_algo_results LIMIT 1), 'No matches found')::TEXT,
        'trigram'::TEXT,
        COALESCE((SELECT score FROM racial_algo_results LIMIT 1), 0.0)::REAL;
        
    -- Test Case 3: "African American tech"
    RETURN QUERY
    WITH aa_tech_results AS (
        SELECT 
            LEFT(c.content, 200) as content_preview,
            similarity(c.content, 'African American tech') as score
        FROM chunks c
        WHERE c.content % 'African American tech'
        AND c.content IS NOT NULL
        ORDER BY score DESC
        LIMIT 1
    )
    SELECT 
        'African American tech'::TEXT,
        (SELECT COUNT(*) FROM chunks c WHERE c.content % 'African American tech' AND c.content IS NOT NULL)::INTEGER,
        COALESCE((SELECT content_preview FROM aa_tech_results LIMIT 1), 'No matches found')::TEXT,
        'trigram'::TEXT,
        COALESCE((SELECT score FROM aa_tech_results LIMIT 1), 0.0)::REAL;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 🎯 DIRECT TRIGRAM TEST FUNCTION  
-- =============================================================================
CREATE OR REPLACE FUNCTION test_trigram_capability()
RETURNS TABLE(
    search_term TEXT,
    trigram_matches INTEGER,
    fts_matches INTEGER,
    combined_matches INTEGER,
    example_match TEXT
) AS $$
BEGIN
    -- Test trigram vs FTS capabilities
    RETURN QUERY
    SELECT 
        'Black technology'::TEXT as search_term,
        (SELECT COUNT(*) FROM chunks WHERE content % 'Black technology')::INTEGER as trigram_matches,
        (SELECT COUNT(*) FROM chunks WHERE search_vector @@ plainto_tsquery('english', 'Black technology'))::INTEGER as fts_matches,
        (SELECT COUNT(*) FROM chunks WHERE (content % 'Black technology' OR search_vector @@ plainto_tsquery('english', 'Black technology')))::INTEGER as combined_matches,
        (SELECT LEFT(content, 150) FROM chunks WHERE content % 'Black technology' ORDER BY similarity(content, 'Black technology') DESC LIMIT 1)::TEXT as example_match;
        
    RETURN QUERY
    SELECT 
        'racial algorithms'::TEXT,
        (SELECT COUNT(*) FROM chunks WHERE content % 'racial algorithms')::INTEGER,
        (SELECT COUNT(*) FROM chunks WHERE search_vector @@ plainto_tsquery('english', 'racial algorithms'))::INTEGER,
        (SELECT COUNT(*) FROM chunks WHERE (content % 'racial algorithms' OR search_vector @@ plainto_tsquery('english', 'racial algorithms')))::INTEGER,
        (SELECT LEFT(content, 150) FROM chunks WHERE content % 'racial algorithms' ORDER BY similarity(content, 'racial algorithms') DESC LIMIT 1)::TEXT;
        
    RETURN QUERY
    SELECT 
        'tech diversity'::TEXT,
        (SELECT COUNT(*) FROM chunks WHERE content % 'tech diversity')::INTEGER,
        (SELECT COUNT(*) FROM chunks WHERE search_vector @@ plainto_tsquery('english', 'tech diversity'))::INTEGER,
        (SELECT COUNT(*) FROM chunks WHERE (content % 'tech diversity' OR search_vector @@ plainto_tsquery('english', 'tech diversity')))::INTEGER,
        (SELECT LEFT(content, 150) FROM chunks WHERE content % 'tech diversity' ORDER BY similarity(content, 'tech diversity') DESC LIMIT 1)::TEXT;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Dr. Sarah Chen PostgreSQL-First Architecture Compliance
-- =============================================================================
COMMENT ON FUNCTION api_shortcuts_search_enhanced(TEXT, INTEGER) IS 
'Dr. Sarah Chen: Enhanced API search with trigram similarity for conceptual matching - v2';

COMMENT ON FUNCTION test_black_technology_search_enhanced() IS 
'Dr. Sarah Chen: Validation function for Black technology conceptual search capability - v2';

COMMENT ON FUNCTION test_trigram_capability() IS 
'Dr. Sarah Chen: Direct trigram vs FTS comparison testing function';

-- =============================================================================
-- 🚀 ENHANCED FUNCTIONS READY FOR TESTING!
-- =============================================================================