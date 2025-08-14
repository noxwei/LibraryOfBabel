-- =============================================================================
-- 🌿 RHIZOMATIC SCI-FI/FANTASY ENHANCEMENT LAYER
-- =============================================================================
-- Dr. Sarah Chen (陈雪芳) PostgreSQL-First Architecture
-- 
-- CONCEPT: Deleuze & Guattari rhizomatic thinking + sci-fi/fantasy imagination
-- APPROACH: Non-linear, interconnected pathways breaking academic boundaries
-- INNOVATION: Multiple entry points, infinite connections, emergent patterns
-- =============================================================================

-- =============================================================================
-- 🌿 RHIZOMATIC EXPRESSION SEARCH FUNCTION
-- =============================================================================
CREATE OR REPLACE FUNCTION chen_rhizomatic_exploration(
    p_seed_concept TEXT,
    p_genre_filter TEXT DEFAULT 'any',
    p_connection_depth INTEGER DEFAULT 3,
    p_limit INTEGER DEFAULT 15
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    title VARCHAR(500),
    author VARCHAR(255),
    content TEXT,
    rhizomatic_path TEXT[],
    connection_strength REAL,
    genre_resonance TEXT,
    emergence_factor REAL
) AS $$
BEGIN
    -- Rhizomatic principle: Any point connects to any other point
    RETURN QUERY
    SELECT 
        c.chunk_id,
        b.title,
        b.author,
        LEFT(c.content, 600) as content,
        -- Rhizomatic pathways: trace non-linear connections
        ARRAY[
            p_seed_concept,
            CASE 
                WHEN c.content ~* 'future|tomorrow|prophecy|vision|dream' THEN 'temporal_fold'
                WHEN c.content ~* 'space|universe|cosmic|infinite|void' THEN 'spatial_expansion'
                WHEN c.content ~* 'magic|ritual|spell|enchant|mystical' THEN 'mystical_channel'
                WHEN c.content ~* 'machine|robot|AI|cyber|digital' THEN 'technological_merge'
                WHEN c.content ~* 'dragon|wizard|quest|hero|legend' THEN 'mythic_journey'
                ELSE 'unexpected_emergence'
            END,
            CASE 
                WHEN c.chunk_type = 'chapter' THEN 'deep_dive'
                WHEN c.chunk_type = 'section' THEN 'surface_ripple'
                ELSE 'boundary_crossing'
            END
        ]::TEXT[] as rhizomatic_path,
        
        -- Connection strength: multiple pathways reinforce each other
        (similarity(c.content, p_seed_concept) * 0.4 +
         ts_rank(c.search_vector, plainto_tsquery('english', p_seed_concept)) * 0.3 +
         CASE 
             WHEN c.content ~* (p_seed_concept || '.*future|fantasy|science.*fiction') THEN 0.2
             WHEN c.content ~* 'rhizome|network|connection|web|pattern' THEN 0.1
             ELSE 0
         END)::REAL as connection_strength,
        
        -- Genre resonance: how does it vibrate across genres?
        CASE 
            WHEN c.content ~* 'science.*fiction|cyberpunk|dystopia|utopia|space.*opera' THEN 'sci_fi_resonance'
            WHEN c.content ~* 'fantasy|magic|dragon|wizard|enchant|mystical' THEN 'fantasy_resonance'  
            WHEN c.content ~* 'horror|gothic|dark|nightmare|terror' THEN 'dark_resonance'
            WHEN c.content ~* 'romance|love|heart|desire|passion' THEN 'emotional_resonance'
            WHEN c.content ~* 'mystery|detective|crime|investigation' THEN 'mystery_resonance'
            ELSE 'genre_transcendence'
        END::TEXT as genre_resonance,
        
        -- Emergence factor: unexpected connections that transcend categories
        (CASE 
            WHEN c.content ~* (p_seed_concept || '.*' || 'quantum|parallel|dimension|reality') THEN 1.0
            WHEN c.content ~* 'emergence|complexity|evolution|transformation' THEN 0.9
            WHEN c.content ~* 'boundary|liminal|threshold|between|beyond' THEN 0.8
            WHEN c.content ~* 'dream|vision|imagination|possibility|potential' THEN 0.7
            ELSE similarity(c.content, 'unexpected connection') * 0.6
        END)::REAL as emergence_factor
        
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE (
        -- Multiple entry points: rhizome has no beginning or end
        c.search_vector @@ plainto_tsquery('english', p_seed_concept)
        OR c.content % p_seed_concept
        OR c.content ~* (p_seed_concept || '.*fiction|fantasy|future|magic|science')
        OR (p_genre_filter != 'any' AND c.content ~* p_genre_filter)
        OR c.content ~* 'rhizome|network|connection|emergence|transcend'
    )
    AND c.content IS NOT NULL
    AND c.word_count BETWEEN 200 AND 1000
    AND (p_genre_filter = 'any' OR c.content ~* p_genre_filter)
    ORDER BY emergence_factor DESC, connection_strength DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 🌌 SCI-FI SPECULATIVE CONNECTIONS FUNCTION  
-- =============================================================================
CREATE OR REPLACE FUNCTION chen_scifi_speculative_bridges(
    p_current_concept TEXT,
    p_future_projection TEXT DEFAULT 'technological singularity',
    p_limit INTEGER DEFAULT 12
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    title VARCHAR(500),
    content TEXT,
    speculative_bridge TEXT,
    temporal_vector TEXT,
    possibility_score REAL
) AS $$
BEGIN
    -- Sci-fi principle: present concepts extrapolated to future possibilities
    RETURN QUERY
    SELECT 
        c.chunk_id,
        b.title,
        LEFT(c.content, 500) as content,
        
        -- Speculative bridges: how does current concept project into future?
        CASE 
            WHEN c.content ~* (p_current_concept || '.*artificial.*intelligence|AI|robot|machine') 
                THEN 'consciousness_emergence'
            WHEN c.content ~* (p_current_concept || '.*space|universe|cosmic|galactic')
                THEN 'cosmic_expansion'
            WHEN c.content ~* (p_current_concept || '.*genetic|DNA|evolution|biology')
                THEN 'bio_transcendence'
            WHEN c.content ~* (p_current_concept || '.*quantum|physics|reality|dimension')
                THEN 'reality_manipulation'
            WHEN c.content ~* (p_current_concept || '.*time|temporal|chronos|future')
                THEN 'temporal_mastery'
            WHEN c.content ~* (p_current_concept || '.*social|society|culture|human')
                THEN 'social_evolution'
            ELSE 'speculative_emergence'
        END::TEXT as speculative_bridge,
        
        -- Temporal vector: direction of change
        CASE 
            WHEN c.content ~* 'future|tomorrow|next|coming|will.*be|evolution' THEN 'forward_projection'
            WHEN c.content ~* 'past|history|ancient|old|was.*once|devolution' THEN 'backward_reflection'
            WHEN c.content ~* 'now|present|current|today|is.*being' THEN 'present_moment'
            WHEN c.content ~* 'cycle|repeat|return|eternal|loop' THEN 'cyclical_time'
            ELSE 'atemporal_drift'
        END::TEXT as temporal_vector,
        
        -- Possibility score: how likely/powerful is this speculative connection?
        (similarity(c.content, p_current_concept || ' ' || p_future_projection) * 0.5 +
         ts_rank(c.search_vector, plainto_tsquery('english', p_current_concept || ' ' || p_future_projection)) * 0.3 +
         CASE 
             WHEN c.content ~* 'possible|potential|might|could|perhaps|imagine' THEN 0.2
             ELSE 0
         END)::REAL as possibility_score
         
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE (
        c.content ~* (p_current_concept || '.*' || p_future_projection)
        OR (c.search_vector @@ plainto_tsquery('english', p_current_concept) 
            AND c.search_vector @@ plainto_tsquery('english', p_future_projection))
        OR c.content % (p_current_concept || ' ' || p_future_projection)
        OR c.content ~* 'speculation|extrapolation|projection|possibility|future.*scenario'
    )
    AND c.content IS NOT NULL
    AND c.word_count > 100
    ORDER BY possibility_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 🐉 FANTASY MYTHIC RESONANCE FUNCTION
-- =============================================================================
CREATE OR REPLACE FUNCTION chen_fantasy_mythic_resonance(
    p_archetype TEXT,
    p_mythic_layer TEXT DEFAULT 'hero_journey',
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    title VARCHAR(500), 
    author VARCHAR(255),
    content TEXT,
    mythic_resonance TEXT,
    archetypal_depth REAL,
    symbolic_density REAL
) AS $$
BEGIN
    -- Fantasy principle: archetypal patterns manifest across cultures and stories
    RETURN QUERY
    SELECT 
        c.chunk_id,
        b.title,
        b.author,
        LEFT(c.content, 550) as content,
        
        -- Mythic resonance: what archetypal pattern does this express?
        CASE 
            WHEN c.content ~* (p_archetype || '.*quest|journey|search|seeking') THEN 'quest_pattern'
            WHEN c.content ~* (p_archetype || '.*transformation|change|becoming|metamorphosis') THEN 'transformation_pattern'
            WHEN c.content ~* (p_archetype || '.*death|rebirth|renewal|resurrection') THEN 'death_rebirth_pattern'
            WHEN c.content ~* (p_archetype || '.*wisdom|knowledge|learning|teaching') THEN 'wisdom_pattern'
            WHEN c.content ~* (p_archetype || '.*love|beloved|heart|union') THEN 'love_pattern'
            WHEN c.content ~* (p_archetype || '.*power|strength|magic|force') THEN 'power_pattern'
            WHEN c.content ~* (p_archetype || '.*shadow|dark|hidden|secret') THEN 'shadow_pattern'
            ELSE 'emergent_pattern'
        END::TEXT as mythic_resonance,
        
        -- Archetypal depth: how deep does the pattern go?
        (similarity(c.content, p_archetype) * 0.4 +
         CASE 
             WHEN c.content ~* 'myth|legend|story|tale|archetype|pattern' THEN 0.3
             WHEN c.content ~* 'symbol|metaphor|allegory|represent|signify' THEN 0.2
             WHEN c.content ~* 'universal|eternal|timeless|ancient|primal' THEN 0.1
             ELSE 0
         END)::REAL as archetypal_depth,
        
        -- Symbolic density: richness of symbolic content
        (CASE 
             WHEN c.content ~* 'dragon|phoenix|unicorn|grail|sword|crown|tree.*life' THEN 1.0
             WHEN c.content ~* 'circle|spiral|cross|star|moon|sun|fire|water' THEN 0.9
             WHEN c.content ~* 'threshold|bridge|door|gate|path|mountain|cave' THEN 0.8
             WHEN c.content ~* 'mirror|mask|key|book|ring|crystal|staff' THEN 0.7
             ELSE similarity(c.content, 'symbolic meaning') * 0.6
         END)::REAL as symbolic_density
         
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE (
        c.search_vector @@ plainto_tsquery('english', p_archetype)
        OR c.content % p_archetype
        OR c.content ~* (p_archetype || '.*fantasy|myth|legend|magic|fairy.*tale')
        OR (p_mythic_layer != 'hero_journey' AND c.content ~* p_mythic_layer)
        OR c.content ~* 'archetype|symbol|myth|legend|pattern|universal'
    )
    AND c.content IS NOT NULL
    AND c.word_count > 75
    ORDER BY symbolic_density DESC, archetypal_depth DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 🌀 RHIZOMATIC GENRE TRANSCENDENCE FUNCTION
-- =============================================================================
CREATE OR REPLACE FUNCTION chen_genre_transcendence(
    p_starting_point TEXT,
    p_max_connections INTEGER DEFAULT 8
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    title VARCHAR(500),
    content TEXT,
    transcendence_path TEXT[],
    genre_fusion TEXT,
    boundary_dissolution REAL
) AS $$
BEGIN
    -- Rhizomatic principle: break down artificial boundaries between genres
    RETURN QUERY
    SELECT 
        c.chunk_id,
        b.title,
        LEFT(c.content, 400) as content,
        
        -- Transcendence path: how does it move between/beyond genres?
        ARRAY[
            p_starting_point,
            CASE 
                WHEN c.content ~* 'science.*fantasy|fantasy.*science|magic.*technology' THEN 'scifi_fantasy_fusion'
                WHEN c.content ~* 'horror.*romance|romance.*horror|love.*terror' THEN 'horror_romance_fusion'
                WHEN c.content ~* 'mystery.*fantasy|fantasy.*mystery|magic.*detective' THEN 'mystery_fantasy_fusion'
                WHEN c.content ~* 'literary.*scifi|scifi.*literary|speculative.*fiction' THEN 'literary_scifi_fusion'
                WHEN c.content ~* 'philosophy.*fantasy|fantasy.*philosophy|wisdom.*magic' THEN 'philosophy_fantasy_fusion'
                ELSE 'pure_transcendence'
            END,
            'genre_boundary_crossed'
        ]::TEXT[] as transcendence_path,
        
        -- Genre fusion: what new form emerges?
        CASE 
            WHEN c.content ~* 'science.*fantasy|magic.*technology|enchanted.*machine' THEN 'technomancy'
            WHEN c.content ~* 'urban.*fantasy|fantasy.*city|magic.*modern' THEN 'urban_mysticism'
            WHEN c.content ~* 'space.*fantasy|fantasy.*space|magic.*cosmos' THEN 'cosmic_fantasy'
            WHEN c.content ~* 'time.*fantasy|fantasy.*time|magic.*temporal' THEN 'temporal_mysticism'
            WHEN c.content ~* 'psychological.*fantasy|fantasy.*mind|magic.*consciousness' THEN 'psycho_fantasy'
            ELSE 'genre_synthesis'
        END::TEXT as genre_fusion,
        
        -- Boundary dissolution: how completely does it transcend categories?
        (CASE 
             WHEN c.content ~* 'transcend|beyond|boundary|limit|category|genre|form' THEN 1.0
             WHEN c.content ~* 'between|liminal|threshold|border|edge|margin' THEN 0.9
             WHEN c.content ~* 'hybrid|fusion|blend|merge|synthesis|combination' THEN 0.8
             WHEN c.content ~* 'new.*form|innovative|experimental|unprecedented' THEN 0.7
             ELSE similarity(c.content, 'boundary crossing') * 0.6
         END)::REAL as boundary_dissolution
         
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE (
        c.search_vector @@ plainto_tsquery('english', p_starting_point)
        OR c.content % p_starting_point
        OR c.content ~* 'genre|boundary|transcend|fusion|hybrid|synthesis'
        OR c.content ~* 'science.*fantasy|fantasy.*science|magic.*technology'
        OR c.content ~* 'urban.*fantasy|space.*fantasy|psychological.*fantasy'
    )
    AND c.content IS NOT NULL
    AND c.word_count > 90
    ORDER BY boundary_dissolution DESC
    LIMIT p_max_connections;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 🌿 Dr. Sarah Chen PostgreSQL-First Architecture Compliance
-- =============================================================================
COMMENT ON FUNCTION chen_rhizomatic_exploration(TEXT, TEXT, INTEGER, INTEGER) IS 
'Dr. Sarah Chen: Rhizomatic sci-fi/fantasy exploration with non-linear pathways';

COMMENT ON FUNCTION chen_scifi_speculative_bridges(TEXT, TEXT, INTEGER) IS 
'Dr. Sarah Chen: Sci-fi speculative bridge discovery for future projections';

COMMENT ON FUNCTION chen_fantasy_mythic_resonance(TEXT, TEXT, INTEGER) IS 
'Dr. Sarah Chen: Fantasy archetypal pattern recognition with mythic depth';

COMMENT ON FUNCTION chen_genre_transcendence(TEXT, INTEGER) IS 
'Dr. Sarah Chen: Genre boundary transcendence with rhizomatic connections';

-- =============================================================================
-- 🌀 RHIZOMATIC SCI-FI/FANTASY LAYER COMPLETE!
-- =============================================================================
-- 
-- 🎉 RHIZOMATIC ENHANCEMENT ACTIVATED!
--
-- New Functions:
-- - chen_rhizomatic_exploration() - Non-linear pathway discovery
-- - chen_scifi_speculative_bridges() - Future possibility projection  
-- - chen_fantasy_mythic_resonance() - Archetypal pattern recognition
-- - chen_genre_transcendence() - Boundary dissolution and fusion
--
-- Usage Examples:
-- SELECT * FROM chen_rhizomatic_exploration('artificial intelligence', 'sci_fi', 3, 10);
-- SELECT * FROM chen_scifi_speculative_bridges('consciousness', 'technological singularity', 8);
-- SELECT * FROM chen_fantasy_mythic_resonance('hero', 'transformation', 6);
-- SELECT * FROM chen_genre_transcendence('magic technology', 5);
--
-- 🌿 Rhizomatic thinking: Multiple entry points, infinite connections!
-- 🌌 Sci-fi speculation: Present concepts → Future possibilities!
-- 🐉 Fantasy resonance: Archetypal patterns across all stories!
-- 🌀 Genre transcendence: Break boundaries, create new forms!
-- =============================================================================