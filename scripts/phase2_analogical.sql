-- =============================================================================
-- 🧠 PHASE 2: ANALOGICAL THINKING FUNCTIONS
-- =============================================================================

-- Analogical search function
CREATE OR REPLACE FUNCTION chen_analogical_search(
    p_concept TEXT,
    p_source_domain TEXT DEFAULT '',
    p_target_domain TEXT DEFAULT '',
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    title VARCHAR(500),
    author VARCHAR(255),
    content TEXT,
    analogical_score REAL,
    domain_bridge TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id,
        b.title,
        b.author,
        LEFT(c.content, 500) as content,
        (similarity(c.content, p_concept) * 0.6 + 
         ts_rank(c.search_vector, plainto_tsquery('english', p_concept)) * 0.4)::REAL as analogical_score,
        CASE 
            WHEN c.content ~* (p_source_domain || '.*' || p_target_domain) THEN 'direct_bridge'
            WHEN c.content % (p_concept || ' ' || p_target_domain) THEN 'conceptual_bridge'
            ELSE 'analogical_potential'
        END::TEXT as domain_bridge
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE (
        c.search_vector @@ plainto_tsquery('english', p_concept)
        OR c.content % p_concept
        OR (p_source_domain != '' AND c.content ILIKE '%' || p_source_domain || '%')
        OR (p_target_domain != '' AND c.content ILIKE '%' || p_target_domain || '%')
    )
    AND c.content IS NOT NULL
    AND c.word_count BETWEEN 100 AND 800
    ORDER BY analogical_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Conceptual bridges function
CREATE OR REPLACE FUNCTION chen_find_conceptual_bridges(
    p_domain1 TEXT,
    p_domain2 TEXT,
    p_limit INTEGER DEFAULT 15
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    title VARCHAR(500),
    content TEXT,
    bridge_strength REAL,
    bridge_type TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id,
        b.title,
        LEFT(c.content, 400) as content,
        (CASE 
            WHEN c.content ~* (p_domain1 || '.*' || p_domain2) THEN 1.0
            WHEN c.content ~* (p_domain2 || '.*' || p_domain1) THEN 0.9
            WHEN c.content ILIKE '%' || p_domain1 || '%' AND c.content ILIKE '%' || p_domain2 || '%' THEN 0.8
            ELSE similarity(c.content, p_domain1 || ' ' || p_domain2) * 0.7
        END)::REAL as bridge_strength,
        CASE 
            WHEN c.content ~* (p_domain1 || '.*' || p_domain2) THEN 'sequential_bridge'
            WHEN c.content ILIKE '%' || p_domain1 || '%' AND c.content ILIKE '%' || p_domain2 || '%' THEN 'parallel_bridge'
            ELSE 'conceptual_bridge'
        END::TEXT as bridge_type
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE (
        (c.content ILIKE '%' || p_domain1 || '%' AND c.content ILIKE '%' || p_domain2 || '%')
        OR c.content % (p_domain1 || ' ' || p_domain2)
        OR c.search_vector @@ (plainto_tsquery('english', p_domain1) && plainto_tsquery('english', p_domain2))
    )
    AND c.content IS NOT NULL
    AND c.word_count BETWEEN 150 AND 1000
    ORDER BY bridge_strength DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Analogical patterns function
CREATE OR REPLACE FUNCTION chen_analogical_patterns(
    p_pattern TEXT,
    p_context TEXT DEFAULT '',
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    title VARCHAR(500),
    author VARCHAR(255),
    content TEXT,
    pattern_score REAL,
    analogical_context TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id,
        b.title,
        b.author,
        LEFT(c.content, 600) as content,
        (ts_rank(c.search_vector, plainto_tsquery('english', p_pattern)) * 0.5 +
         similarity(c.content, p_pattern) * 0.3 +
         CASE WHEN p_context != '' AND c.content ILIKE '%' || p_context || '%' THEN 0.2 ELSE 0 END)::REAL as pattern_score,
        CASE 
            WHEN c.chunk_type = 'chapter' THEN 'deep_analysis'
            WHEN c.chunk_type = 'section' THEN 'focused_discussion'
            WHEN c.chunk_type = 'paragraph' THEN 'specific_example'
            ELSE 'contextual_mention'
        END::TEXT as analogical_context
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE (
        c.search_vector @@ plainto_tsquery('english', p_pattern)
        OR c.content % p_pattern
        OR (p_context != '' AND c.content ILIKE '%' || p_context || '%')
    )
    AND c.content IS NOT NULL
    AND c.word_count BETWEEN 100 AND 1200
    ORDER BY pattern_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;