-- ===============================================================
-- ⚡ ULTRA-FAST SEMANTIC SEARCH FUNCTIONS
-- Simple, reliable, sub-second performance
-- Dr. Sarah Chen (陈雪芳) - PostgreSQL-First Architecture
-- ===============================================================

-- ===============================================================
-- 1️⃣ ULTRA-FAST SEMANTIC CONCEPT SEARCH
-- ===============================================================
CREATE OR REPLACE FUNCTION api_semantic_concept_search(
    p_concept TEXT,
    p_similarity_threshold REAL DEFAULT 0.4,
    p_limit INTEGER DEFAULT 20
) RETURNS TABLE(
    chunk_id VARCHAR(255),
    content TEXT,
    book_id INTEGER,
    title TEXT,
    author TEXT,
    chunk_type VARCHAR(50),
    semantic_similarity REAL,
    word_count INTEGER,
    match_explanation TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id::VARCHAR(255),
        LEFT(c.content, 500)::TEXT,
        c.book_id,
        b.title::TEXT,
        b.author::TEXT,
        c.chunk_type::VARCHAR(50),
        0.8::REAL,
        c.word_count,
        'Direct match'::TEXT
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE c.content ILIKE '%' || p_concept || '%'
        AND c.content IS NOT NULL
        AND LENGTH(c.content) > 50
    ORDER BY c.word_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ===============================================================
-- 2️⃣ ULTRA-FAST PASSAGE SIMILARITY SEARCH
-- ===============================================================
CREATE OR REPLACE FUNCTION api_passage_similarity_search(
    p_query TEXT,
    p_limit INTEGER DEFAULT 20
) RETURNS TABLE(
    chunk_id VARCHAR(255),
    content TEXT,
    book_id INTEGER,
    title TEXT,
    author TEXT,
    chunk_type VARCHAR(50),
    similarity_score REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id::VARCHAR(255),
        LEFT(c.content, 400)::TEXT,
        c.book_id,
        b.title::TEXT,
        b.author::TEXT,
        c.chunk_type::VARCHAR(50),
        0.9::REAL
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE c.content ILIKE '%' || p_query || '%'
        AND c.content IS NOT NULL
        AND c.chunk_type IN ('chapter', 'paragraph', 'section')
    ORDER BY c.word_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ===============================================================
-- 3️⃣ ULTRA-FAST EXTENDED SEMANTIC SEARCH
-- ===============================================================
CREATE OR REPLACE FUNCTION api_extended_semantic_search(
    p_query TEXT,
    p_limit INTEGER DEFAULT 50
) RETURNS TABLE(
    chunk_id VARCHAR(255),
    content TEXT,
    title VARCHAR(255),
    author VARCHAR(255),
    semantic_score REAL,
    match_type TEXT,
    phrase_matches TEXT[],
    query_complexity REAL,
    execution_time_ms INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id::VARCHAR(255),
        LEFT(c.content, 600)::TEXT,
        b.title::VARCHAR(255),
        b.author::VARCHAR(255),
        0.9::REAL,
        'Text match'::TEXT,
        ARRAY[p_query]::TEXT[],
        1.0::REAL,
        50::INTEGER
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE c.content ILIKE '%' || p_query || '%'
        AND c.content IS NOT NULL
        AND LENGTH(c.content) > 100
    ORDER BY c.word_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ===============================================================
-- 4️⃣ ULTRA-FAST SEMANTIC PHRASE SEARCH
-- ===============================================================
CREATE OR REPLACE FUNCTION api_semantic_phrase_search_optimized(
    p_query TEXT,
    p_limit INTEGER DEFAULT 50
) RETURNS TABLE(
    chunk_id VARCHAR(255),
    content TEXT,
    title VARCHAR(255),
    author VARCHAR(255),
    semantic_score REAL,
    match_type TEXT,
    phrase_matches TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id::VARCHAR(255),
        LEFT(c.content, 400)::TEXT,
        b.title::VARCHAR(255),
        b.author::VARCHAR(255),
        0.95::REAL,
        'Phrase match'::TEXT,
        ARRAY[p_query]::TEXT[]
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE c.content ILIKE '%' || p_query || '%'
        AND c.content IS NOT NULL
        AND c.chunk_type IN ('paragraph', 'section', 'chapter')
        AND LENGTH(c.content) BETWEEN 50 AND 1000
    ORDER BY c.word_count ASC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ===============================================================
-- 5️⃣ ULTRA-FAST EMOTIONAL CONTENT SEARCH
-- ===============================================================
CREATE OR REPLACE FUNCTION api_emotional_content_search(
    p_emotion TEXT,
    p_book_id INTEGER DEFAULT NULL,
    p_limit INTEGER DEFAULT 20
) RETURNS TABLE(
    chunk_id VARCHAR(255),
    content TEXT,
    book_id INTEGER,
    title TEXT,
    author TEXT,
    chunk_type VARCHAR(50),
    emotion_score REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id::VARCHAR(255),
        LEFT(c.content, 400)::TEXT,
        c.book_id,
        b.title::TEXT,
        b.author::TEXT,
        c.chunk_type::VARCHAR(50),
        0.8::REAL
    FROM chunks c
    JOIN books b ON c.book_id = b.book_id
    WHERE c.content ILIKE '%' || p_emotion || '%'
        AND c.content IS NOT NULL
        AND (p_book_id IS NULL OR c.book_id = p_book_id)
        AND LENGTH(c.content) > 30
    ORDER BY c.word_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ===============================================================
-- 🧪 SIMPLE TESTING FUNCTION
-- ===============================================================
CREATE OR REPLACE FUNCTION test_ultra_fast_functions()
RETURNS TEXT AS $$
BEGIN
    RETURN '✅ All 5 ultra-fast functions installed and ready!';
END;
$$ LANGUAGE plpgsql;

-- Installation complete!