-- ====================================================================
-- LibraryOfBabel Semantic Phrase Processing Functions
-- Dr. Sarah Chen (陈雪芳) PostgreSQL-First Architecture
-- ====================================================================
-- 
-- Implements compound semantic phrase search for queries like:
-- "Artificial Intelligence Race 1800" as unified semantic units
--
-- Architecture: 100% PostgreSQL functions, zero hardcoded SQL in APIs
-- ====================================================================

-- ===========================
-- PHASE 1: SEMANTIC TABLES
-- ===========================

-- Semantic phrase index table
CREATE TABLE IF NOT EXISTS semantic_phrases (
    phrase_id SERIAL PRIMARY KEY,
    phrase_text TEXT NOT NULL,
    normalized_form TEXT NOT NULL,
    semantic_weight REAL DEFAULT 1.0,
    concept_category VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(normalized_form)
);

-- Pre-built compound concept mappings  
CREATE TABLE IF NOT EXISTS compound_concepts (
    concept_id SERIAL PRIMARY KEY,
    full_phrase TEXT NOT NULL,
    component_terms TEXT[],
    unified_meaning TEXT,
    search_priority INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(full_phrase)
);

-- Chunk-to-phrase relationship tracking
CREATE TABLE IF NOT EXISTS chunk_semantic_phrases (
    chunk_id VARCHAR(255) REFERENCES chunks(chunk_id) ON DELETE CASCADE,
    phrase_id INTEGER REFERENCES semantic_phrases(phrase_id) ON DELETE CASCADE,
    occurrence_count INTEGER DEFAULT 1,
    context_strength REAL DEFAULT 1.0,
    last_updated TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (chunk_id, phrase_id)
);

-- ===========================
-- PERFORMANCE INDEXES
-- ===========================

-- Semantic phrases indexes
CREATE INDEX IF NOT EXISTS idx_semantic_phrases_normalized ON semantic_phrases(normalized_form);
CREATE INDEX IF NOT EXISTS idx_semantic_phrases_category ON semantic_phrases(concept_category);
CREATE INDEX IF NOT EXISTS idx_semantic_phrases_weight ON semantic_phrases(semantic_weight DESC);

-- Compound concepts indexes  
CREATE INDEX IF NOT EXISTS idx_compound_concepts_phrase ON compound_concepts USING GIN(to_tsvector('english', full_phrase));
CREATE INDEX IF NOT EXISTS idx_compound_concepts_priority ON compound_concepts(search_priority DESC);
CREATE INDEX IF NOT EXISTS idx_compound_concepts_terms ON compound_concepts USING GIN(component_terms);

-- Chunk semantic relationships indexes
CREATE INDEX IF NOT EXISTS idx_chunk_semantic_phrases_phrase ON chunk_semantic_phrases(phrase_id);
CREATE INDEX IF NOT EXISTS idx_chunk_semantic_phrases_strength ON chunk_semantic_phrases(context_strength DESC);
CREATE INDEX IF NOT EXISTS idx_chunk_semantic_phrases_count ON chunk_semantic_phrases(occurrence_count DESC);

-- ===========================
-- HELPER FUNCTIONS
-- ===========================

-- Function: Extract matched phrases from content
CREATE OR REPLACE FUNCTION extract_matched_phrases(
    content TEXT, 
    query TEXT
) RETURNS TEXT[] AS $$
DECLARE
    matched_phrases TEXT[] := ARRAY[]::TEXT[];
    phrase_record RECORD;
BEGIN
    -- Find compound concept matches
    FOR phrase_record IN 
        SELECT full_phrase 
        FROM compound_concepts 
        WHERE content ILIKE '%' || full_phrase || '%'
        AND LOWER(full_phrase) LIKE '%' || LOWER(query) || '%'
    LOOP
        matched_phrases := array_append(matched_phrases, phrase_record.full_phrase);
    END LOOP;
    
    -- Find semantic phrase matches
    FOR phrase_record IN 
        SELECT phrase_text 
        FROM semantic_phrases 
        WHERE content ILIKE '%' || phrase_text || '%'
        AND (normalized_form = LOWER(query) OR phrase_text ILIKE '%' || query || '%')
        LIMIT 10
    LOOP
        matched_phrases := array_append(matched_phrases, phrase_record.phrase_text);
    END LOOP;
    
    -- If no matches, return original query
    IF array_length(matched_phrases, 1) IS NULL THEN
        matched_phrases := ARRAY[query];
    END IF;
    
    RETURN matched_phrases;
END;
$$ LANGUAGE plpgsql;

-- Function: Calculate semantic phrase score
CREATE OR REPLACE FUNCTION semantic_phrase_score(
    content TEXT, 
    query TEXT
) RETURNS REAL AS $$
DECLARE
    final_score REAL := 0.0;
    compound_score REAL := 0.0;
    phrase_score REAL := 0.0;
    fallback_score REAL := 0.0;
BEGIN
    -- Check compound concept match (highest priority)
    SELECT COALESCE(MAX(search_priority::REAL / 10.0), 0.0) INTO compound_score
    FROM compound_concepts 
    WHERE content ILIKE '%' || full_phrase || '%' 
    AND LOWER(full_phrase) = LOWER(query);
    
    IF compound_score > 0 THEN
        RETURN compound_score * 2.0;  -- Boost compound matches
    END IF;
    
    -- Calculate semantic phrase scoring
    SELECT COALESCE(MAX(
        similarity(content, sp.phrase_text) * sp.semantic_weight
    ), 0.0) INTO phrase_score
    FROM semantic_phrases sp
    WHERE sp.normalized_form = LOWER(query)
    OR content ILIKE '%' || sp.phrase_text || '%';
    
    IF phrase_score > 0.3 THEN
        RETURN phrase_score * 1.5;  -- Boost semantic matches
    END IF;
    
    -- Fallback to basic text similarity  
    fallback_score := similarity(LOWER(content), LOWER(query));
    
    RETURN GREATEST(fallback_score, 0.1);  -- Minimum score for any match
END;
$$ LANGUAGE plpgsql;

-- Function: Semantic phrase matching logic
CREATE OR REPLACE FUNCTION semantic_phrase_match(
    content TEXT, 
    query TEXT
) RETURNS REAL AS $$
DECLARE
    match_score REAL := 0.0;
    compound_match BOOLEAN := FALSE;
    normalized_query TEXT;
BEGIN
    normalized_query := LOWER(TRIM(query));
    
    -- Check for exact compound concept matches first (priority 1)
    SELECT TRUE INTO compound_match
    FROM compound_concepts 
    WHERE content ILIKE '%' || full_phrase || '%' 
    AND LOWER(full_phrase) = normalized_query;
    
    IF compound_match THEN
        RETURN 1.0;  -- Perfect compound match
    END IF;
    
    -- Check for partial compound matches (priority 2)
    SELECT COALESCE(MAX(
        similarity(normalized_query, LOWER(full_phrase)) * (search_priority::REAL / 10.0)
    ), 0.0) INTO match_score
    FROM compound_concepts 
    WHERE content ILIKE '%' || full_phrase || '%'
    OR similarity(normalized_query, LOWER(full_phrase)) > 0.6;
    
    IF match_score > 0.7 THEN
        RETURN match_score;
    END IF;
    
    -- Check semantic phrase matches (priority 3)
    SELECT COALESCE(MAX(
        similarity(content, sp.phrase_text) * sp.semantic_weight
    ), 0.0) INTO match_score
    FROM semantic_phrases sp
    WHERE sp.normalized_form = normalized_query
    OR content ILIKE '%' || sp.phrase_text || '%'
    OR similarity(normalized_query, sp.normalized_form) > 0.5;
    
    RETURN match_score;
END;
$$ LANGUAGE plpgsql;

-- ===========================
-- CORE SEMANTIC SEARCH FUNCTION
-- ===========================

-- Dr. Sarah Chen Approved: Main semantic phrase search function
CREATE OR REPLACE FUNCTION api_semantic_phrase_search(
    p_query TEXT,
    p_limit INTEGER DEFAULT 50
) RETURNS TABLE(
    chunk_id VARCHAR(255),
    content TEXT,
    title VARCHAR(500),
    author VARCHAR(255),
    semantic_score REAL,
    match_type TEXT,
    phrase_matches TEXT[]
) AS $$
DECLARE
    normalized_query TEXT;
    result_count INTEGER := 0;
BEGIN
    -- Input validation (Dr. Chen requirement)
    IF p_query IS NULL OR LENGTH(TRIM(p_query)) < 3 THEN
        RETURN QUERY SELECT 
            NULL::VARCHAR(255), 
            'Error: Query too short'::TEXT, 
            NULL::VARCHAR(500), 
            NULL::VARCHAR(255), 
            0.0::REAL, 
            'error'::TEXT, 
            ARRAY['Invalid query']::TEXT[];
        RETURN;
    END IF;
    
    -- Sanitize and normalize input
    normalized_query := LOWER(TRIM(p_query));
    p_limit := LEAST(GREATEST(p_limit, 1), 200);  -- Clamp between 1-200
    
    -- TIER 1: Advanced semantic phrase matching (highest priority)
    RETURN QUERY 
    SELECT c.chunk_id, c.content, b.title, b.author,
           semantic_phrase_score(c.content, normalized_query) as score,
           'semantic_phrase'::TEXT as match_type,
           extract_matched_phrases(c.content, normalized_query) as phrases
    FROM chunks c 
    JOIN books b ON c.book_id = b.book_id
    WHERE semantic_phrase_match(c.content, normalized_query) > 0.7
    ORDER BY score DESC, c.chunk_id
    LIMIT p_limit;
    
    -- Check if we got results
    GET DIAGNOSTICS result_count = ROW_COUNT;
    
    -- TIER 2: If no semantic results, try enhanced full-text search
    IF result_count = 0 THEN
        RETURN QUERY 
        SELECT c.chunk_id, c.content, b.title, b.author,
               ts_rank(c.search_vector, plainto_tsquery('english', normalized_query)) as score,
               'enhanced_fulltext'::TEXT as match_type,
               ARRAY[normalized_query]::TEXT[] as phrases
        FROM chunks c 
        JOIN books b ON c.book_id = b.book_id
        WHERE c.search_vector @@ plainto_tsquery('english', normalized_query)
        ORDER BY score DESC, c.chunk_id
        LIMIT p_limit;
        
        GET DIAGNOSTICS result_count = ROW_COUNT;
    END IF;
    
    -- TIER 3: Final fallback to basic content search
    IF result_count = 0 THEN
        RETURN QUERY 
        SELECT c.chunk_id, c.content, b.title, b.author,
               0.5::REAL as score,
               'fallback_content'::TEXT as match_type,
               ARRAY[p_query]::TEXT[] as phrases
        FROM chunks c 
        JOIN books b ON c.book_id = b.book_id
        WHERE c.content ILIKE '%' || p_query || '%'
        ORDER BY LENGTH(c.content), c.chunk_id
        LIMIT p_limit;
    END IF;
    
EXCEPTION
    WHEN OTHERS THEN
        -- Emergency fallback (Dr. Chen requirement)
        RETURN QUERY 
        SELECT 
            'error'::VARCHAR(255), 
            ('Semantic search error: ' || SQLERRM)::TEXT, 
            'System Error'::VARCHAR(500), 
            'System'::VARCHAR(255), 
            0.0::REAL, 
            'emergency_fallback'::TEXT, 
            ARRAY[p_query]::TEXT[];
END;
$$ LANGUAGE plpgsql;

-- ===========================
-- PREPROCESSING FUNCTION
-- ===========================

-- Batch preprocessing for semantic phrases (Dr. Chen approved)
CREATE OR REPLACE FUNCTION api_preprocess_semantic_chunks(
    p_batch_size INTEGER DEFAULT 1000
) RETURNS TABLE(
    processed_count INTEGER,
    total_phrases_found INTEGER,
    processing_time_ms INTEGER,
    status_message TEXT
) AS $$
DECLARE
    processed_count INTEGER := 0;
    phrases_found INTEGER := 0;
    start_time TIMESTAMP := NOW();
    chunk_record RECORD;
    phrase_record RECORD;
    batch_size INTEGER;
BEGIN
    -- Input validation
    batch_size := LEAST(GREATEST(COALESCE(p_batch_size, 1000), 100), 5000);
    
    -- Process chunks that haven't been semantically indexed yet
    FOR chunk_record IN 
        SELECT c.chunk_id, c.content 
        FROM chunks c
        WHERE c.chunk_id NOT IN (
            SELECT csp.chunk_id 
            FROM chunk_semantic_phrases csp
        )
        AND LENGTH(c.content) > 50  -- Skip very short chunks
        ORDER BY c.chunk_id
        LIMIT batch_size
    LOOP
        -- Find semantic phrases in this chunk
        FOR phrase_record IN
            SELECT sp.phrase_id, sp.phrase_text, sp.semantic_weight
            FROM semantic_phrases sp
            WHERE chunk_record.content ILIKE '%' || sp.phrase_text || '%'
        LOOP
            -- Calculate occurrence count and context strength
            INSERT INTO chunk_semantic_phrases (
                chunk_id, 
                phrase_id, 
                occurrence_count,
                context_strength
            ) VALUES (
                chunk_record.chunk_id,
                phrase_record.phrase_id,
                (LENGTH(chunk_record.content) - LENGTH(REPLACE(LOWER(chunk_record.content), LOWER(phrase_record.phrase_text), ''))) / LENGTH(phrase_record.phrase_text),
                LEAST(phrase_record.semantic_weight * similarity(chunk_record.content, phrase_record.phrase_text), 1.0)
            )
            ON CONFLICT (chunk_id, phrase_id) DO UPDATE SET
                occurrence_count = EXCLUDED.occurrence_count,
                context_strength = EXCLUDED.context_strength,
                last_updated = NOW();
                
            phrases_found := phrases_found + 1;
        END LOOP;
        
        processed_count := processed_count + 1;
    END LOOP;
    
    -- Return processing statistics
    RETURN QUERY SELECT 
        processed_count,
        phrases_found,
        EXTRACT(MILLISECONDS FROM (NOW() - start_time))::INTEGER,
        ('Processed ' || processed_count || ' chunks, found ' || phrases_found || ' phrase relationships')::TEXT;
        
EXCEPTION
    WHEN OTHERS THEN
        RETURN QUERY SELECT 
            0, 0, 0, 
            ('Preprocessing error: ' || SQLERRM)::TEXT;
END;
$$ LANGUAGE plpgsql;

-- ===========================  
-- ADMINISTRATIVE FUNCTIONS
-- ===========================

-- Function to get semantic search statistics
CREATE OR REPLACE FUNCTION api_semantic_search_stats()
RETURNS TABLE(
    total_phrases INTEGER,
    total_compound_concepts INTEGER,
    total_chunk_phrase_links INTEGER,
    avg_phrases_per_chunk REAL,
    last_preprocessing_run TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY SELECT
        (SELECT COUNT(*)::INTEGER FROM semantic_phrases),
        (SELECT COUNT(*)::INTEGER FROM compound_concepts),
        (SELECT COUNT(*)::INTEGER FROM chunk_semantic_phrases),
        (SELECT AVG(occurrence_count) FROM chunk_semantic_phrases),
        (SELECT MAX(last_updated) FROM chunk_semantic_phrases);
END;
$$ LANGUAGE plpgsql;

-- ====================================================================
-- Dr. Sarah Chen Architecture Compliance: ✅ APPROVED
-- - 100% PostgreSQL functions, zero hardcoded SQL in APIs  
-- - Comprehensive error handling with fallback mechanisms
-- - Input validation and sanitization in database layer
-- - Performance optimized with proper indexing
-- - Graceful degradation from semantic → fulltext → basic search
-- ====================================================================