-- =============================================================================
-- 🧠 LIBRARYOFBABEL SPECIALIZED EMBEDDING SEARCH FUNCTIONS 
-- =============================================================================
-- Dr. Sarah Chen (陈雪芳) - PostgreSQL-First Architecture
-- 
-- UNLEASH THE POWER: 5 Specialized Embedding Types × 393K Vectors Each
-- 1. semantic_search_function() - General meaning and context
-- 2. factual_search_function() - Facts, data, concrete information  
-- 3. topical_search_function() - Subject matter and themes
-- 4. stylistic_search_function() - Writing style and tone
-- 5. temporal_search_function() - Time-related concepts and sequences
--
-- PostgreSQL-First Design: Zero hardcoded SQL in application code!
-- =============================================================================

-- Enable vector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================================================
-- 🎯 1. SEMANTIC SEARCH FUNCTION - General meaning and context
-- =============================================================================
CREATE OR REPLACE FUNCTION semantic_search_chunks(
    query_text TEXT,
    limit_results INTEGER DEFAULT 20,
    similarity_threshold FLOAT DEFAULT 0.1
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    content_preview TEXT,
    chunk_type VARCHAR(50),
    similarity_score FLOAT,
    character_count INTEGER,
    word_count INTEGER
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id,
        LEFT(c.content, 300) as content_preview,
        c.chunk_type,
        GREATEST(0.0, 1.0 - (s.embedding <-> (
            SELECT embedding FROM semantic_embeddings 
            WHERE chunk_id = (
                SELECT chunk_id FROM chunks 
                WHERE content IS NOT NULL 
                AND to_tsvector('english', content) @@ plainto_tsquery('english', query_text)
                ORDER BY ts_rank(to_tsvector('english', content), plainto_tsquery('english', query_text)) DESC
                LIMIT 1
            )
        ))) as similarity_score,
        c.character_count,
        c.word_count
    FROM semantic_embeddings s
    JOIN chunks c ON s.chunk_id = c.chunk_id
    WHERE c.content IS NOT NULL
    AND s.embedding <-> (
        SELECT embedding FROM semantic_embeddings 
        WHERE chunk_id = (
            SELECT chunk_id FROM chunks 
            WHERE content IS NOT NULL 
            AND to_tsvector('english', content) @@ plainto_tsquery('english', query_text)
            ORDER BY ts_rank(to_tsvector('english', content), plainto_tsquery('english', query_text)) DESC
            LIMIT 1
        )
    ) <= (2.0 - similarity_threshold)
    ORDER BY similarity_score DESC
    LIMIT limit_results;
    
EXCEPTION
    WHEN OTHERS THEN
        -- Fallback to text search if vector search fails
        RETURN QUERY
        SELECT 
            c.chunk_id,
            LEFT(c.content, 300) as content_preview,
            c.chunk_type,
            ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', query_text)) as similarity_score,
            c.character_count,
            c.word_count
        FROM chunks c
        WHERE c.content IS NOT NULL
        AND to_tsvector('english', c.content) @@ plainto_tsquery('english', query_text)
        ORDER BY similarity_score DESC
        LIMIT limit_results;
END;
$$;

-- =============================================================================
-- 📊 2. FACTUAL SEARCH FUNCTION - Facts, data, concrete information
-- =============================================================================
CREATE OR REPLACE FUNCTION factual_search_chunks(
    query_text TEXT,
    limit_results INTEGER DEFAULT 20,
    similarity_threshold FLOAT DEFAULT 0.15
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    content_preview TEXT,
    chunk_type VARCHAR(50),
    factual_score FLOAT,
    character_count INTEGER,
    word_count INTEGER
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id,
        LEFT(c.content, 300) as content_preview,
        c.chunk_type,
        GREATEST(0.0, 1.0 - (f.embedding <-> (
            SELECT embedding FROM factual_embeddings 
            WHERE chunk_id = (
                SELECT chunk_id FROM chunks 
                WHERE content IS NOT NULL 
                AND (content ~* '\d+|data|fact|statistic|number|percent|study|research|evidence'
                     OR to_tsvector('english', content) @@ plainto_tsquery('english', query_text))
                ORDER BY ts_rank(to_tsvector('english', content), plainto_tsquery('english', query_text)) DESC
                LIMIT 1
            )
        ))) as factual_score,
        c.character_count,
        c.word_count
    FROM factual_embeddings f
    JOIN chunks c ON f.chunk_id = c.chunk_id
    WHERE c.content IS NOT NULL
    AND f.embedding <-> (
        SELECT embedding FROM factual_embeddings 
        WHERE chunk_id = (
            SELECT chunk_id FROM chunks 
            WHERE content IS NOT NULL 
            AND (content ~* '\d+|data|fact|statistic|number|percent|study|research|evidence'
                 OR to_tsvector('english', content) @@ plainto_tsquery('english', query_text))
            ORDER BY ts_rank(to_tsvector('english', content), plainto_tsquery('english', query_text)) DESC
            LIMIT 1
        )
    ) <= (2.0 - similarity_threshold)
    ORDER BY factual_score DESC
    LIMIT limit_results;
    
EXCEPTION
    WHEN OTHERS THEN
        -- Fallback to text search with factual bias
        RETURN QUERY
        SELECT 
            c.chunk_id,
            LEFT(c.content, 300) as content_preview,
            c.chunk_type,
            ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', query_text)) as factual_score,
            c.character_count,
            c.word_count
        FROM chunks c
        WHERE c.content IS NOT NULL
        AND (content ~* '\d+|data|fact|statistic|number|percent|study|research|evidence'
             OR to_tsvector('english', c.content) @@ plainto_tsquery('english', query_text))
        ORDER BY factual_score DESC
        LIMIT limit_results;
END;
$$;

-- =============================================================================
-- 🏷️ 3. TOPICAL SEARCH FUNCTION - Subject matter and themes
-- =============================================================================
CREATE OR REPLACE FUNCTION topical_search_chunks(
    query_text TEXT,
    limit_results INTEGER DEFAULT 20,
    similarity_threshold FLOAT DEFAULT 0.12
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    content_preview TEXT,
    chunk_type VARCHAR(50),
    topic_score FLOAT,
    character_count INTEGER,
    word_count INTEGER
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id,
        LEFT(c.content, 300) as content_preview,
        c.chunk_type,
        GREATEST(0.0, 1.0 - (t.embedding <-> (
            SELECT embedding FROM topical_embeddings 
            WHERE chunk_id = (
                SELECT chunk_id FROM chunks 
                WHERE content IS NOT NULL 
                AND to_tsvector('english', content) @@ plainto_tsquery('english', query_text)
                ORDER BY ts_rank(to_tsvector('english', content), plainto_tsquery('english', query_text)) DESC
                LIMIT 1
            )
        ))) as topic_score,
        c.character_count,
        c.word_count
    FROM topical_embeddings t
    JOIN chunks c ON t.chunk_id = c.chunk_id
    WHERE c.content IS NOT NULL
    AND t.embedding <-> (
        SELECT embedding FROM topical_embeddings 
        WHERE chunk_id = (
            SELECT chunk_id FROM chunks 
            WHERE content IS NOT NULL 
            AND to_tsvector('english', content) @@ plainto_tsquery('english', query_text)
            ORDER BY ts_rank(to_tsvector('english', content), plainto_tsquery('english', query_text)) DESC
            LIMIT 1
        )
    ) <= (2.0 - similarity_threshold)
    ORDER BY topic_score DESC
    LIMIT limit_results;
    
EXCEPTION
    WHEN OTHERS THEN
        -- Fallback to text search
        RETURN QUERY
        SELECT 
            c.chunk_id,
            LEFT(c.content, 300) as content_preview,
            c.chunk_type,
            ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', query_text)) as topic_score,
            c.character_count,
            c.word_count
        FROM chunks c
        WHERE c.content IS NOT NULL
        AND to_tsvector('english', c.content) @@ plainto_tsquery('english', query_text)
        ORDER BY topic_score DESC
        LIMIT limit_results;
END;
$$;

-- =============================================================================
-- 🎨 4. STYLISTIC SEARCH FUNCTION - Writing style and tone
-- =============================================================================
CREATE OR REPLACE FUNCTION stylistic_search_chunks(
    query_text TEXT,
    limit_results INTEGER DEFAULT 20,
    similarity_threshold FLOAT DEFAULT 0.1
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    content_preview TEXT,
    chunk_type VARCHAR(50),
    style_score FLOAT,
    character_count INTEGER,
    word_count INTEGER
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id,
        LEFT(c.content, 300) as content_preview,
        c.chunk_type,
        GREATEST(0.0, 1.0 - (st.embedding <-> (
            SELECT embedding FROM stylistic_embeddings 
            WHERE chunk_id = (
                SELECT chunk_id FROM chunks 
                WHERE content IS NOT NULL 
                AND (content ~* 'literary|poetic|formal|informal|academic|casual|dramatic|humorous'
                     OR to_tsvector('english', content) @@ plainto_tsquery('english', query_text))
                ORDER BY ts_rank(to_tsvector('english', content), plainto_tsquery('english', query_text)) DESC
                LIMIT 1
            )
        ))) as style_score,
        c.character_count,
        c.word_count
    FROM stylistic_embeddings st
    JOIN chunks c ON st.chunk_id = c.chunk_id
    WHERE c.content IS NOT NULL
    AND st.embedding <-> (
        SELECT embedding FROM stylistic_embeddings 
        WHERE chunk_id = (
            SELECT chunk_id FROM chunks 
            WHERE content IS NOT NULL 
            AND (content ~* 'literary|poetic|formal|informal|academic|casual|dramatic|humorous'
                 OR to_tsvector('english', content) @@ plainto_tsquery('english', query_text))
            ORDER BY ts_rank(to_tsvector('english', content), plainto_tsquery('english', query_text)) DESC
            LIMIT 1
        )
    ) <= (2.0 - similarity_threshold)
    ORDER BY style_score DESC
    LIMIT limit_results;
    
EXCEPTION
    WHEN OTHERS THEN
        -- Fallback to text search with style bias
        RETURN QUERY
        SELECT 
            c.chunk_id,
            LEFT(c.content, 300) as content_preview,
            c.chunk_type,
            ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', query_text)) as style_score,
            c.character_count,
            c.word_count
        FROM chunks c
        WHERE c.content IS NOT NULL
        AND (content ~* 'literary|poetic|formal|informal|academic|casual|dramatic|humorous'
             OR to_tsvector('english', c.content) @@ plainto_tsquery('english', query_text))
        ORDER BY style_score DESC
        LIMIT limit_results;
END;
$$;

-- =============================================================================
-- ⏰ 5. TEMPORAL SEARCH FUNCTION - Time-related concepts and sequences
-- =============================================================================
CREATE OR REPLACE FUNCTION temporal_search_chunks(
    query_text TEXT,
    limit_results INTEGER DEFAULT 20,
    similarity_threshold FLOAT DEFAULT 0.1
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    content_preview TEXT,
    chunk_type VARCHAR(50),
    temporal_score FLOAT,
    character_count INTEGER,
    word_count INTEGER
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id,
        LEFT(c.content, 300) as content_preview,
        c.chunk_type,
        GREATEST(0.0, 1.0 - (temp.embedding <-> (
            SELECT embedding FROM temporal_embeddings 
            WHERE chunk_id = (
                SELECT chunk_id FROM chunks 
                WHERE content IS NOT NULL 
                AND (content ~* 'time|when|before|after|during|timeline|sequence|history|future|past|now|then|first|last|next|previous'
                     OR to_tsvector('english', content) @@ plainto_tsquery('english', query_text))
                ORDER BY ts_rank(to_tsvector('english', content), plainto_tsquery('english', query_text)) DESC
                LIMIT 1
            )
        ))) as temporal_score,
        c.character_count,
        c.word_count
    FROM temporal_embeddings temp
    JOIN chunks c ON temp.chunk_id = c.chunk_id
    WHERE c.content IS NOT NULL
    AND temp.embedding <-> (
        SELECT embedding FROM temporal_embeddings 
        WHERE chunk_id = (
            SELECT chunk_id FROM chunks 
            WHERE content IS NOT NULL 
            AND (content ~* 'time|when|before|after|during|timeline|sequence|history|future|past|now|then|first|last|next|previous'
                 OR to_tsvector('english', content) @@ plainto_tsquery('english', query_text))
            ORDER BY ts_rank(to_tsvector('english', content), plainto_tsquery('english', query_text)) DESC
            LIMIT 1
        )
    ) <= (2.0 - similarity_threshold)
    ORDER BY temporal_score DESC
    LIMIT limit_results;
    
EXCEPTION
    WHEN OTHERS THEN
        -- Fallback to text search with temporal bias
        RETURN QUERY
        SELECT 
            c.chunk_id,
            LEFT(c.content, 300) as content_preview,
            c.chunk_type,
            ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', query_text)) as temporal_score,
            c.character_count,
            c.word_count
        FROM chunks c
        WHERE c.content IS NOT NULL
        AND (content ~* 'time|when|before|after|during|timeline|sequence|history|future|past|now|then|first|last|next|previous'
             OR to_tsvector('english', c.content) @@ plainto_tsquery('english', query_text))
        ORDER BY temporal_score DESC
        LIMIT limit_results;
END;
$$;

-- =============================================================================
-- 🎯 6. UNIFIED MULTI-DIMENSIONAL SEARCH FUNCTION
-- =============================================================================
CREATE OR REPLACE FUNCTION multi_dimensional_search(
    query_text TEXT,
    search_types TEXT[] DEFAULT ARRAY['semantic', 'factual', 'topical', 'stylistic', 'temporal'],
    limit_per_type INTEGER DEFAULT 10,
    overall_limit INTEGER DEFAULT 50
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    content_preview TEXT,
    chunk_type VARCHAR(50),
    search_type TEXT,
    score FLOAT,
    character_count INTEGER,
    word_count INTEGER
) 
LANGUAGE plpgsql
AS $$
DECLARE
    search_type_item TEXT;
BEGIN
    -- Create temporary table to collect results
    CREATE TEMP TABLE IF NOT EXISTS temp_multi_search_results (
        chunk_id VARCHAR(255),
        content_preview TEXT,
        chunk_type VARCHAR(50),
        search_type TEXT,
        score FLOAT,
        character_count INTEGER,
        word_count INTEGER
    );
    
    -- Clear any existing results
    DELETE FROM temp_multi_search_results;
    
    -- Execute each search type
    FOREACH search_type_item IN ARRAY search_types
    LOOP
        CASE search_type_item
            WHEN 'semantic' THEN
                INSERT INTO temp_multi_search_results
                SELECT *, 'semantic' as search_type FROM semantic_search_chunks(query_text, limit_per_type);
                
            WHEN 'factual' THEN
                INSERT INTO temp_multi_search_results
                SELECT *, 'factual' as search_type FROM factual_search_chunks(query_text, limit_per_type);
                
            WHEN 'topical' THEN
                INSERT INTO temp_multi_search_results
                SELECT *, 'topical' as search_type FROM topical_search_chunks(query_text, limit_per_type);
                
            WHEN 'stylistic' THEN
                INSERT INTO temp_multi_search_results
                SELECT *, 'stylistic' as search_type FROM stylistic_search_chunks(query_text, limit_per_type);
                
            WHEN 'temporal' THEN
                INSERT INTO temp_multi_search_results
                SELECT *, 'temporal' as search_type FROM temporal_search_chunks(query_text, limit_per_type);
        END CASE;
    END LOOP;
    
    -- Return unified results, deduplicated and sorted by score
    RETURN QUERY
    SELECT DISTINCT ON (t.chunk_id)
        t.chunk_id,
        t.content_preview,
        t.chunk_type,
        t.search_type,
        t.score,
        t.character_count,
        t.word_count
    FROM temp_multi_search_results t
    ORDER BY t.chunk_id, t.score DESC
    LIMIT overall_limit;
    
    -- Clean up
    DROP TABLE IF EXISTS temp_multi_search_results;
    
END;
$$;

-- =============================================================================
-- 📊 7. EMBEDDING SYSTEM STATUS FUNCTION
-- =============================================================================
CREATE OR REPLACE FUNCTION get_embedding_system_status()
RETURNS TABLE(
    embedding_type TEXT,
    vector_count BIGINT,
    table_size TEXT,
    index_count INTEGER,
    last_updated TIMESTAMP
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'semantic' as embedding_type,
        COUNT(*) as vector_count,
        pg_size_pretty(pg_total_relation_size('semantic_embeddings')) as table_size,
        (SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'semantic_embeddings')::INTEGER as index_count,
        NOW() as last_updated
    FROM semantic_embeddings
    
    UNION ALL
    
    SELECT 
        'factual' as embedding_type,
        COUNT(*) as vector_count,
        pg_size_pretty(pg_total_relation_size('factual_embeddings')) as table_size,
        (SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'factual_embeddings')::INTEGER as index_count,
        NOW() as last_updated
    FROM factual_embeddings
    
    UNION ALL
    
    SELECT 
        'topical' as embedding_type,
        COUNT(*) as vector_count,
        pg_size_pretty(pg_total_relation_size('topical_embeddings')) as table_size,
        (SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'topical_embeddings')::INTEGER as index_count,
        NOW() as last_updated
    FROM topical_embeddings
    
    UNION ALL
    
    SELECT 
        'stylistic' as embedding_type,
        COUNT(*) as vector_count,
        pg_size_pretty(pg_total_relation_size('stylistic_embeddings')) as table_size,
        (SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'stylistic_embeddings')::INTEGER as index_count,
        NOW() as last_updated
    FROM stylistic_embeddings
    
    UNION ALL
    
    SELECT 
        'temporal' as embedding_type,
        COUNT(*) as vector_count,
        pg_size_pretty(pg_total_relation_size('temporal_embeddings')) as table_size,
        (SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'temporal_embeddings')::INTEGER as index_count,
        NOW() as last_updated
    FROM temporal_embeddings;
END;
$$;

-- =============================================================================
-- 🚀 GRANT PERMISSIONS AND CREATE INDEXES FOR PERFORMANCE
-- =============================================================================

-- Grant execute permissions (adjust user as needed)
-- GRANT EXECUTE ON FUNCTION semantic_search_chunks(TEXT, INTEGER, FLOAT) TO your_api_user;
-- GRANT EXECUTE ON FUNCTION factual_search_chunks(TEXT, INTEGER, FLOAT) TO your_api_user;
-- GRANT EXECUTE ON FUNCTION topical_search_chunks(TEXT, INTEGER, FLOAT) TO your_api_user;
-- GRANT EXECUTE ON FUNCTION stylistic_search_chunks(TEXT, INTEGER, FLOAT) TO your_api_user;
-- GRANT EXECUTE ON FUNCTION temporal_search_chunks(TEXT, INTEGER, FLOAT) TO your_api_user;
-- GRANT EXECUTE ON FUNCTION multi_dimensional_search(TEXT, TEXT[], INTEGER, INTEGER) TO your_api_user;
-- GRANT EXECUTE ON FUNCTION get_embedding_system_status() TO your_api_user;

-- =============================================================================
-- 🎯 8. PRODUCTION PHASE FILTERING - Dr. Sarah Chen PostgreSQL-First Architecture
-- =============================================================================
CREATE OR REPLACE FUNCTION get_phase_1_2_chunks_for_embedding(
    batch_size INTEGER DEFAULT 1000,
    embedding_type TEXT DEFAULT 'all'
)
RETURNS TABLE(
    chunk_id VARCHAR(255),
    content TEXT,
    chunk_type VARCHAR(50),
    character_count INTEGER,
    word_count INTEGER,
    book_id INTEGER,
    chapter_number INTEGER,
    section_number INTEGER
) 
LANGUAGE plpgsql
AS $$
BEGIN
    -- PRODUCTION STRATEGY: Phase 1 (chapters) + Phase 2 (sections) ONLY
    -- Total target: 601K chunks (248K chapters + 353K sections)
    -- Exclude paragraphs (1.3M) and sentences (10M+) for production launch
    
    IF embedding_type = 'semantic' THEN
        RETURN QUERY
        SELECT 
            c.chunk_id,
            c.content,
            c.chunk_type,
            c.character_count,
            c.word_count,
            c.book_id,
            c.chapter_number,
            c.section_number
        FROM chunks c
        WHERE c.chunk_type IN ('chapter', 'section')
        AND c.content IS NOT NULL
        AND c.character_count > 50
        AND NOT EXISTS (
            SELECT 1 FROM semantic_embeddings se 
            WHERE se.chunk_id = c.chunk_id
        )
        ORDER BY 
            CASE WHEN c.chunk_type = 'chapter' THEN 1 ELSE 2 END,
            c.book_id, 
            c.chapter_number NULLS LAST,
            c.section_number NULLS LAST
        LIMIT batch_size;
        
    ELSIF embedding_type = 'factual' THEN
        RETURN QUERY
        SELECT 
            c.chunk_id,
            c.content,
            c.chunk_type,
            c.character_count,
            c.word_count,
            c.book_id,
            c.chapter_number,
            c.section_number
        FROM chunks c
        WHERE c.chunk_type IN ('chapter', 'section')
        AND c.content IS NOT NULL
        AND c.character_count > 50
        AND NOT EXISTS (
            SELECT 1 FROM factual_embeddings fe 
            WHERE fe.chunk_id = c.chunk_id
        )
        ORDER BY 
            CASE WHEN c.chunk_type = 'chapter' THEN 1 ELSE 2 END,
            c.book_id, 
            c.chapter_number NULLS LAST,
            c.section_number NULLS LAST
        LIMIT batch_size;
        
    ELSIF embedding_type = 'topical' THEN
        RETURN QUERY
        SELECT 
            c.chunk_id,
            c.content,
            c.chunk_type,
            c.character_count,
            c.word_count,
            c.book_id,
            c.chapter_number,
            c.section_number
        FROM chunks c
        WHERE c.chunk_type IN ('chapter', 'section')
        AND c.content IS NOT NULL
        AND c.character_count > 50
        AND NOT EXISTS (
            SELECT 1 FROM topical_embeddings te 
            WHERE te.chunk_id = c.chunk_id
        )
        ORDER BY 
            CASE WHEN c.chunk_type = 'chapter' THEN 1 ELSE 2 END,
            c.book_id, 
            c.chapter_number NULLS LAST,
            c.section_number NULLS LAST
        LIMIT batch_size;
        
    ELSIF embedding_type = 'stylistic' THEN
        RETURN QUERY
        SELECT 
            c.chunk_id,
            c.content,
            c.chunk_type,
            c.character_count,
            c.word_count,
            c.book_id,
            c.chapter_number,
            c.section_number
        FROM chunks c
        WHERE c.chunk_type IN ('chapter', 'section')
        AND c.content IS NOT NULL
        AND c.character_count > 50
        AND NOT EXISTS (
            SELECT 1 FROM stylistic_embeddings ste 
            WHERE ste.chunk_id = c.chunk_id
        )
        ORDER BY 
            CASE WHEN c.chunk_type = 'chapter' THEN 1 ELSE 2 END,
            c.book_id, 
            c.chapter_number NULLS LAST,
            c.section_number NULLS LAST
        LIMIT batch_size;
        
    ELSIF embedding_type = 'temporal' THEN
        RETURN QUERY
        SELECT 
            c.chunk_id,
            c.content,
            c.chunk_type,
            c.character_count,
            c.word_count,
            c.book_id,
            c.chapter_number,
            c.section_number
        FROM chunks c
        WHERE c.chunk_type IN ('chapter', 'section')
        AND c.content IS NOT NULL
        AND c.character_count > 50
        AND NOT EXISTS (
            SELECT 1 FROM temporal_embeddings tem 
            WHERE tem.chunk_id = c.chunk_id
        )
        ORDER BY 
            CASE WHEN c.chunk_type = 'chapter' THEN 1 ELSE 2 END,
            c.book_id, 
            c.chapter_number NULLS LAST,
            c.section_number NULLS LAST
        LIMIT batch_size;
        
    ELSE
        -- Default: return chunks missing from ANY embedding type
        RETURN QUERY
        SELECT 
            c.chunk_id,
            c.content,
            c.chunk_type,
            c.character_count,
            c.word_count,
            c.book_id,
            c.chapter_number,
            c.section_number
        FROM chunks c
        WHERE c.chunk_type IN ('chapter', 'section')
        AND c.content IS NOT NULL
        AND c.character_count > 50
        AND (
            NOT EXISTS (SELECT 1 FROM semantic_embeddings se WHERE se.chunk_id = c.chunk_id)
            OR NOT EXISTS (SELECT 1 FROM factual_embeddings fe WHERE fe.chunk_id = c.chunk_id)
            OR NOT EXISTS (SELECT 1 FROM topical_embeddings te WHERE te.chunk_id = c.chunk_id)
            OR NOT EXISTS (SELECT 1 FROM stylistic_embeddings ste WHERE ste.chunk_id = c.chunk_id)
            OR NOT EXISTS (SELECT 1 FROM temporal_embeddings tem WHERE tem.chunk_id = c.chunk_id)
        )
        ORDER BY 
            CASE WHEN c.chunk_type = 'chapter' THEN 1 ELSE 2 END,
            c.book_id, 
            c.chapter_number NULLS LAST,
            c.section_number NULLS LAST
        LIMIT batch_size;
    END IF;
    
EXCEPTION
    WHEN OTHERS THEN
        -- Fallback: return any unprocessed chapter/section chunks
        RETURN QUERY
        SELECT 
            c.chunk_id,
            c.content,
            c.chunk_type,
            c.character_count,
            c.word_count,
            c.book_id,
            c.chapter_number,
            c.section_number
        FROM chunks c
        WHERE c.chunk_type IN ('chapter', 'section')
        AND c.content IS NOT NULL
        AND c.character_count > 50
        ORDER BY c.chunk_id
        LIMIT batch_size;
END;
$$;

-- =============================================================================
-- 📊 PHASE 1+2 PROGRESS TRACKING FUNCTION
-- =============================================================================
CREATE OR REPLACE FUNCTION get_phase_1_2_progress()
RETURNS TABLE(
    phase TEXT,
    chunk_type TEXT,
    total_chunks BIGINT,
    semantic_completed BIGINT,
    factual_completed BIGINT,
    topical_completed BIGINT,
    stylistic_completed BIGINT,
    temporal_completed BIGINT,
    overall_completion_percent NUMERIC(5,2)
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'Phase 1' as phase,
        'chapter' as chunk_type,
        COUNT(*) as total_chunks,
        COUNT(se.chunk_id) as semantic_completed,
        COUNT(fe.chunk_id) as factual_completed,
        COUNT(te.chunk_id) as topical_completed,
        COUNT(ste.chunk_id) as stylistic_completed,
        COUNT(tem.chunk_id) as temporal_completed,
        CASE 
            WHEN COUNT(*) = 0 THEN 0.00
            ELSE ROUND(
                (COUNT(se.chunk_id) + COUNT(fe.chunk_id) + COUNT(te.chunk_id) + 
                 COUNT(ste.chunk_id) + COUNT(tem.chunk_id))::NUMERIC / 
                (COUNT(*) * 5) * 100, 2
            )
        END as overall_completion_percent
    FROM chunks c
    LEFT JOIN semantic_embeddings se ON c.chunk_id = se.chunk_id
    LEFT JOIN factual_embeddings fe ON c.chunk_id = fe.chunk_id
    LEFT JOIN topical_embeddings te ON c.chunk_id = te.chunk_id
    LEFT JOIN stylistic_embeddings ste ON c.chunk_id = ste.chunk_id
    LEFT JOIN temporal_embeddings tem ON c.chunk_id = tem.chunk_id
    WHERE c.chunk_type = 'chapter'
    AND c.content IS NOT NULL
    AND c.character_count > 50
    
    UNION ALL
    
    SELECT 
        'Phase 2' as phase,
        'section' as chunk_type,
        COUNT(*) as total_chunks,
        COUNT(se.chunk_id) as semantic_completed,
        COUNT(fe.chunk_id) as factual_completed,
        COUNT(te.chunk_id) as topical_completed,
        COUNT(ste.chunk_id) as stylistic_completed,
        COUNT(tem.chunk_id) as temporal_completed,
        CASE 
            WHEN COUNT(*) = 0 THEN 0.00
            ELSE ROUND(
                (COUNT(se.chunk_id) + COUNT(fe.chunk_id) + COUNT(te.chunk_id) + 
                 COUNT(ste.chunk_id) + COUNT(tem.chunk_id))::NUMERIC / 
                (COUNT(*) * 5) * 100, 2
            )
        END as overall_completion_percent
    FROM chunks c
    LEFT JOIN semantic_embeddings se ON c.chunk_id = se.chunk_id
    LEFT JOIN factual_embeddings fe ON c.chunk_id = fe.chunk_id
    LEFT JOIN topical_embeddings te ON c.chunk_id = te.chunk_id
    LEFT JOIN stylistic_embeddings ste ON c.chunk_id = ste.chunk_id
    LEFT JOIN temporal_embeddings tem ON c.chunk_id = tem.chunk_id
    WHERE c.chunk_type = 'section'
    AND c.content IS NOT NULL
    AND c.character_count > 50;
END;
$$;

-- =============================================================================
-- ✅ INSTALLATION COMPLETE!
-- =============================================================================
-- 
-- 🎉 YOU NOW HAVE 5 SPECIALIZED EMBEDDING SEARCH FUNCTIONS!
--
-- Usage Examples:
-- SELECT * FROM semantic_search_chunks('artificial intelligence', 10);
-- SELECT * FROM factual_search_chunks('statistics data research', 15);  
-- SELECT * FROM topical_search_chunks('machine learning', 20);
-- SELECT * FROM stylistic_search_chunks('poetic literary writing', 10);
-- SELECT * FROM temporal_search_chunks('timeline historical sequence', 10);
-- SELECT * FROM multi_dimensional_search('quantum physics', ARRAY['semantic','factual'], 5, 25);
-- SELECT * FROM get_embedding_system_status();
--
-- 🚀 READY TO ROCK! AHHHHHHHH! 🚀
-- =============================================================================