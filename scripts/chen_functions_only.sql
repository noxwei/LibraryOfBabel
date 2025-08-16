-- =============================================================================
-- ⚡ OPTIMIZED CHEN FUNCTIONS (NO INDEXES)
-- =============================================================================

-- Ultra-fast rhizomatic exploration
CREATE OR REPLACE FUNCTION chen_rhizomatic_exploration_fast(
    p_seed_concept TEXT,
    p_genre_filter TEXT DEFAULT 'any',
    p_limit INTEGER DEFAULT 5
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    title VARCHAR(500),
    content TEXT,
    connection_strength REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id,
        b.title,
        LEFT(c.content, 300) as content,
        ts_rank(c.search_vector, plainto_tsquery('english', p_seed_concept))::REAL as connection_strength
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE c.search_vector @@ plainto_tsquery('english', p_seed_concept)
    AND c.content IS NOT NULL
    AND c.word_count BETWEEN 200 AND 600
    AND (p_genre_filter = 'any' OR c.content ~* p_genre_filter)
    ORDER BY connection_strength DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Ultra-fast Foucauldian analysis
CREATE OR REPLACE FUNCTION chen_foucauldian_power_fast(
    p_power_concept TEXT,
    p_limit INTEGER DEFAULT 5
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    title VARCHAR(500),
    content TEXT,
    power_score REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id,
        b.title,
        LEFT(c.content, 300) as content,
        ts_rank(c.search_vector, plainto_tsquery('english', p_power_concept))::REAL as power_score
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE c.search_vector @@ plainto_tsquery('english', p_power_concept)
    AND c.content IS NOT NULL
    AND c.word_count BETWEEN 200 AND 600
    AND c.content ~* 'power|control|surveillance|discipline'
    ORDER BY power_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Lightning-fast search
CREATE OR REPLACE FUNCTION chen_lightning_search(
    p_concept TEXT,
    p_limit INTEGER DEFAULT 3
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    title VARCHAR(500),
    content TEXT,
    relevance REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id,
        b.title,
        LEFT(c.content, 250) as content,
        ts_rank(c.search_vector, plainto_tsquery('english', p_concept))::REAL as relevance
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE c.search_vector @@ plainto_tsquery('english', p_concept)
    AND c.content IS NOT NULL
    AND c.word_count BETWEEN 200 AND 500
    ORDER BY relevance DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;