-- =============================================================================
-- ⚡ DR. CHEN PERFORMANCE OPTIMIZATION SUITE
-- =============================================================================
-- Dr. Sarah Chen (陈雪芳) PostgreSQL-First Architecture
-- Ultra-fast optimization for 2.9M chunk dataset
-- =============================================================================

-- =============================================================================
-- 📊 PERFORMANCE INDEXES FOR CHEN FUNCTIONS
-- =============================================================================

-- Ultra-fast trigram index for critical concepts
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chen_ultra_fast_trigram
ON chunks USING gist(content gist_trgm_ops)
WHERE content IS NOT NULL 
AND word_count BETWEEN 100 AND 800
AND (content ~* 'love|power|desire|identity|freedom|hero|magic|AI|robot|future'
     OR content ~* 'philosophy|science|technology|art|mathematics|biology'
     OR content ~* 'queer|gender|sexuality|surveillance|control|resistance');

-- Optimized search vector index with filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chen_search_vector_optimized
ON chunks USING gin(search_vector)
WHERE content IS NOT NULL
AND word_count BETWEEN 100 AND 1000;

-- Word count + content length composite index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chen_word_count_composite
ON chunks(word_count, chunk_type)
INCLUDE (content, search_vector)
WHERE content IS NOT NULL
AND word_count BETWEEN 100 AND 1200;

-- =============================================================================
-- 🚀 OPTIMIZED RHIZOMATIC FUNCTIONS
-- =============================================================================

-- Ultra-fast rhizomatic exploration
CREATE OR REPLACE FUNCTION chen_rhizomatic_exploration_fast(
    p_seed_concept TEXT,
    p_genre_filter TEXT DEFAULT 'any',
    p_connection_depth INTEGER DEFAULT 2,
    p_limit INTEGER DEFAULT 8
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    title VARCHAR(500),
    author VARCHAR(255),
    content TEXT,
    rhizomatic_path TEXT[],
    connection_strength REAL,
    genre_resonance TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id,
        b.title,
        b.author,
        LEFT(c.content, 400) as content,
        ARRAY[p_seed_concept, 'fast_connection']::TEXT[] as rhizomatic_path,
        (similarity(c.content, p_seed_concept) * 0.7 +
         ts_rank(c.search_vector, plainto_tsquery('english', p_seed_concept)) * 0.3)::REAL as connection_strength,
        CASE 
            WHEN c.content ~* 'science.*fiction|cyberpunk|dystopia' THEN 'sci_fi_resonance'
            WHEN c.content ~* 'fantasy|magic|dragon|wizard' THEN 'fantasy_resonance'  
            ELSE 'genre_transcendence'
        END::TEXT as genre_resonance
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE (
        c.search_vector @@ plainto_tsquery('english', p_seed_concept)
        OR c.content % p_seed_concept
    )
    AND c.content IS NOT NULL
    AND c.word_count BETWEEN 200 AND 800
    AND (p_genre_filter = 'any' OR c.content ~* p_genre_filter)
    ORDER BY connection_strength DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Ultra-fast Foucauldian power analysis
CREATE OR REPLACE FUNCTION chen_foucauldian_power_analysis_fast(
    p_power_concept TEXT,
    p_surveillance_type TEXT DEFAULT 'control',
    p_limit INTEGER DEFAULT 6
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    title VARCHAR(500),
    content TEXT,
    power_mechanism TEXT,
    surveillance_intensity REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id,
        b.title,
        LEFT(c.content, 350) as content,
        CASE 
            WHEN c.content ~* (p_power_concept || '.*discipline|surveillance|control') THEN 'disciplinary_power'
            WHEN c.content ~* (p_power_concept || '.*knowledge|discourse') THEN 'power_knowledge'
            WHEN c.content ~* (p_power_concept || '.*body|bodies') THEN 'biopower'
            ELSE 'sovereign_power'
        END::TEXT as power_mechanism,
        (CASE 
            WHEN c.content ~* 'surveillance|monitor|watch|observe' THEN 1.0
            WHEN c.content ~* 'control|manage|regulate|govern' THEN 0.8
            ELSE similarity(c.content, 'power control') * 0.6
        END)::REAL as surveillance_intensity
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE (
        c.search_vector @@ plainto_tsquery('english', p_power_concept)
        OR c.content % p_power_concept
        OR c.content ~* (p_power_concept || '.*power|control|surveillance')
    )
    AND c.content IS NOT NULL
    AND c.word_count BETWEEN 150 AND 800
    ORDER BY surveillance_intensity DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Ultra-fast analogical search
CREATE OR REPLACE FUNCTION chen_analogical_search_fast(
    p_concept TEXT,
    p_source_domain TEXT DEFAULT '',
    p_target_domain TEXT DEFAULT '',
    p_limit INTEGER DEFAULT 8
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    title VARCHAR(500),
    content TEXT,
    analogical_score REAL,
    domain_bridge TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id,
        b.title,
        LEFT(c.content, 400) as content,
        (ts_rank(c.search_vector, plainto_tsquery('english', p_concept)) * 0.6 + 
         similarity(c.content, p_concept) * 0.4)::REAL as analogical_score,
        CASE 
            WHEN p_source_domain != '' AND p_target_domain != '' 
                AND c.content ~* (p_source_domain || '.*' || p_target_domain) THEN 'direct_bridge'
            WHEN c.content % (p_concept || ' ' || COALESCE(p_target_domain, '')) THEN 'conceptual_bridge'
            ELSE 'analogical_potential'
        END::TEXT as domain_bridge
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE (
        c.search_vector @@ plainto_tsquery('english', p_concept)
        OR c.content % p_concept
        OR (p_source_domain != '' AND c.content ILIKE '%' || p_source_domain || '%')
    )
    AND c.content IS NOT NULL
    AND c.word_count BETWEEN 150 AND 800
    ORDER BY analogical_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- ⚡ ULTRA-FAST SIMPLIFIED FUNCTIONS
-- =============================================================================

-- Lightning-fast concept search (< 100ms target)
CREATE OR REPLACE FUNCTION chen_lightning_search(
    p_concept TEXT,
    p_limit INTEGER DEFAULT 5
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    title VARCHAR(500),
    content TEXT,
    relevance_score REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id,
        b.title,
        LEFT(c.content, 300) as content,
        ts_rank(c.search_vector, plainto_tsquery('english', p_concept))::REAL as relevance_score
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE c.search_vector @@ plainto_tsquery('english', p_concept)
    AND c.content IS NOT NULL
    AND c.word_count BETWEEN 200 AND 600
    ORDER BY relevance_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Ultra-fast critical theory search
CREATE OR REPLACE FUNCTION chen_critical_theory_fast(
    p_theory_concept TEXT,
    p_limit INTEGER DEFAULT 5
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    title VARCHAR(500),
    content TEXT,
    theory_resonance TEXT,
    relevance REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id,
        b.title,
        LEFT(c.content, 350) as content,
        CASE 
            WHEN c.content ~* (p_theory_concept || '.*power|control|surveillance') THEN 'foucauldian'
            WHEN c.content ~* (p_theory_concept || '.*queer|gender|sexuality') THEN 'queer_theory'
            WHEN c.content ~* (p_theory_concept || '.*desire|transgress|taboo') THEN 'psychoanalytic'
            ELSE 'general_critical'
        END::TEXT as theory_resonance,
        ts_rank(c.search_vector, plainto_tsquery('english', p_theory_concept))::REAL as relevance
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE c.search_vector @@ plainto_tsquery('english', p_theory_concept)
    AND c.content IS NOT NULL
    AND c.word_count BETWEEN 200 AND 700
    AND (c.content ~* 'power|desire|identity|freedom|control|resistance|queer|gender')
    ORDER BY relevance DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 📊 PERFORMANCE STATISTICS UPDATE
-- =============================================================================

-- Update all table statistics for optimization
ANALYZE chunks;
ANALYZE books;

-- Update PostgreSQL query planner statistics
UPDATE pg_stat_user_tables SET n_tup_upd = n_tup_upd + 1 WHERE relname = 'chunks';

-- =============================================================================
-- 🎯 CHEN OPTIMIZATION SUMMARY
-- =============================================================================

COMMENT ON FUNCTION chen_rhizomatic_exploration_fast(TEXT, TEXT, INTEGER, INTEGER) IS 
'Dr. Sarah Chen: Ultra-fast rhizomatic exploration (target: <500ms)';

COMMENT ON FUNCTION chen_foucauldian_power_analysis_fast(TEXT, TEXT, INTEGER) IS 
'Dr. Sarah Chen: Ultra-fast Foucauldian analysis (target: <300ms)';

COMMENT ON FUNCTION chen_analogical_search_fast(TEXT, TEXT, TEXT, INTEGER) IS 
'Dr. Sarah Chen: Ultra-fast analogical search (target: <400ms)';

COMMENT ON FUNCTION chen_lightning_search(TEXT, INTEGER) IS 
'Dr. Sarah Chen: Lightning-fast concept search (target: <100ms)';

COMMENT ON FUNCTION chen_critical_theory_fast(TEXT, INTEGER) IS 
'Dr. Sarah Chen: Ultra-fast critical theory search (target: <200ms)';

-- =============================================================================
-- ⚡ OPTIMIZATION COMPLETE!
-- =============================================================================