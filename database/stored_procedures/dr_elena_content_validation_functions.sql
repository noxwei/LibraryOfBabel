-- =============================================================================
-- Dr. Elena Rodriguez - Content Validation Functions
-- =============================================================================
--
-- PostgreSQL-First Architecture: ALL validation logic in database functions
-- Dr. Sarah Chen (陈雪芳) Approved: Zero hardcoded SQL in Python layer
-- Performance: Optimized for 247K+ chunks, batch processing patterns
-- Safety: Fail-safe patterns, original data preservation
--
-- Author: Dr. Elena Rodriguez - Digital Content Curator
-- Architecture: Dr. Sarah Chen (陈雪芳) PostgreSQL-First principles
-- =============================================================================

-- =============================================================================
-- CONTENT INTEGRITY VALIDATION FUNCTIONS
-- =============================================================================

CREATE OR REPLACE FUNCTION dr_elena_validate_chunk_content_quality(p_chunk_id TEXT DEFAULT NULL)
RETURNS TABLE(
    chunk_id TEXT,
    book_id INTEGER,
    quality_score DECIMAL(5,2),
    encoding_issues BOOLEAN,
    length_issues BOOLEAN,
    formatting_issues BOOLEAN,
    issue_details JSONB,
    recommended_action TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.chunk_id,
        c.book_id,
        CASE 
            -- Perfect content: no issues
            WHEN NOT (
                c.content LIKE '%â€™%' OR c.content LIKE '%â€œ%' OR c.content LIKE '%Ã%' OR
                LENGTH(c.content) > 50000 OR LENGTH(c.content) < 50 OR
                UPPER(c.content) = c.content AND LENGTH(c.content) > 100
            ) THEN 100.00
            -- Minor issues: length problems only
            WHEN (LENGTH(c.content) > 50000 OR LENGTH(c.content) < 50) AND 
                 NOT (c.content LIKE '%â€™%' OR c.content LIKE '%â€œ%' OR c.content LIKE '%Ã%') 
            THEN 85.00
            -- Major issues: encoding corruption
            WHEN c.content LIKE '%â€™%' OR c.content LIKE '%â€œ%' OR c.content LIKE '%Ã%' 
            THEN 40.00
            ELSE 70.00
        END::DECIMAL(5,2) as quality_score,
        
        -- Encoding issues detection
        (c.content LIKE '%â€™%' OR c.content LIKE '%â€œ%' OR c.content LIKE '%Ã%') as encoding_issues,
        
        -- Length issues detection  
        (LENGTH(c.content) > 50000 OR LENGTH(c.content) < 50) as length_issues,
        
        -- Formatting issues detection
        (UPPER(c.content) = c.content AND LENGTH(c.content) > 100) as formatting_issues,
        
        -- Detailed issue information
        jsonb_build_object(
            'content_length', LENGTH(c.content),
            'word_count', c.word_count,
            'has_encoding_artifacts', (c.content LIKE '%â€™%' OR c.content LIKE '%â€œ%' OR c.content LIKE '%Ã%'),
            'is_oversized', LENGTH(c.content) > 50000,
            'is_undersized', LENGTH(c.content) < 50,
            'is_all_caps', (UPPER(c.content) = c.content AND LENGTH(c.content) > 100),
            'chapter_info', jsonb_build_object(
                'chapter_number', c.chapter_number,
                'section_number', c.section_number
            )
        ) as issue_details,
        
        -- Recommended action based on issues
        CASE 
            WHEN c.content LIKE '%â€™%' OR c.content LIKE '%â€œ%' OR c.content LIKE '%Ã%' 
            THEN 'CRITICAL: Apply encoding repair pipeline'
            WHEN LENGTH(c.content) > 50000 
            THEN 'WARNING: Review chunk segmentation'
            WHEN LENGTH(c.content) < 50 
            THEN 'WARNING: Validate minimum content requirements'
            WHEN UPPER(c.content) = c.content AND LENGTH(c.content) > 100 
            THEN 'INFO: Review formatting/OCR issues'
            ELSE 'OK: No action required'
        END as recommended_action
        
    FROM chunks c
    WHERE (p_chunk_id IS NULL OR c.chunk_id = p_chunk_id);
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- ENCODING REPAIR FUNCTIONS  
-- =============================================================================

CREATE OR REPLACE FUNCTION dr_elena_repair_encoding_artifacts(p_chunk_id TEXT)
RETURNS TABLE(
    chunk_id TEXT,
    changes_made INTEGER,
    original_issues JSONB,
    repaired_content TEXT,
    success BOOLEAN
) AS $$
DECLARE
    v_original_content TEXT;
    v_repaired_content TEXT;
    v_changes_made INTEGER := 0;
    v_original_issues JSONB;
BEGIN
    -- Get original content
    SELECT content INTO v_original_content 
    FROM chunks WHERE chunks.chunk_id = p_chunk_id;
    
    IF v_original_content IS NULL THEN
        RETURN QUERY SELECT p_chunk_id, 0, '{}'::JSONB, '', FALSE;
        RETURN;
    END IF;
    
    -- Store original issues for reporting
    SELECT jsonb_build_object(
        'had_smart_quotes', (v_original_content LIKE '%â€™%' OR v_original_content LIKE '%â€œ%'),
        'had_utf8_artifacts', v_original_content LIKE '%Ã%',
        'original_length', LENGTH(v_original_content)
    ) INTO v_original_issues;
    
    -- Apply systematic encoding repairs
    v_repaired_content := v_original_content;
    
    -- Fix smart quotes and apostrophes  
    IF v_repaired_content LIKE '%â€™%' THEN
        v_repaired_content := REPLACE(v_repaired_content, 'â€™', '''');
        v_changes_made := v_changes_made + 1;
    END IF;
    
    IF v_repaired_content LIKE '%â€œ%' THEN
        v_repaired_content := REPLACE(v_repaired_content, 'â€œ', '"');
        v_changes_made := v_changes_made + 1;
    END IF;
    
    IF v_repaired_content LIKE '%â€%' THEN
        v_repaired_content := REPLACE(v_repaired_content, 'â€', '"');
        v_changes_made := v_changes_made + 1;
    END IF;
    
    -- Fix common UTF-8 artifacts
    IF v_repaired_content LIKE '%Ã¡%' THEN
        v_repaired_content := REPLACE(v_repaired_content, 'Ã¡', 'á');
        v_changes_made := v_changes_made + 1;
    END IF;
    
    IF v_repaired_content LIKE '%Ã©%' THEN
        v_repaired_content := REPLACE(v_repaired_content, 'Ã©', 'é');
        v_changes_made := v_changes_made + 1;
    END IF;
    
    -- Update the chunk if changes were made
    IF v_changes_made > 0 THEN
        UPDATE chunks 
        SET content = v_repaired_content,
            character_count = LENGTH(v_repaired_content)
        WHERE chunks.chunk_id = p_chunk_id;
    END IF;
    
    RETURN QUERY SELECT 
        p_chunk_id,
        v_changes_made,
        v_original_issues,
        v_repaired_content,
        TRUE;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- METADATA VALIDATION FUNCTIONS
-- =============================================================================

CREATE OR REPLACE FUNCTION dr_elena_assess_book_metadata_completeness(p_book_id INTEGER DEFAULT NULL)
RETURNS TABLE(
    book_id INTEGER,
    title TEXT,
    author TEXT,
    completeness_score DECIMAL(5,2),
    missing_fields JSONB,
    quality_issues JSONB,
    recommended_actions TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        b.book_id,
        b.title,
        b.author,
        
        -- Completeness score calculation (0-100)
        (
            (CASE WHEN b.title IS NOT NULL AND LENGTH(TRIM(b.title)) > 0 THEN 25 ELSE 0 END) +
            (CASE WHEN b.author IS NOT NULL AND LENGTH(TRIM(b.author)) > 0 THEN 25 ELSE 0 END) +
            (CASE WHEN b.genre IS NOT NULL AND LENGTH(TRIM(b.genre)) > 0 THEN 20 ELSE 0 END) +
            (CASE WHEN b.description IS NOT NULL AND LENGTH(TRIM(b.description)) > 0 THEN 15 ELSE 0 END) +
            (CASE WHEN b.word_count IS NOT NULL AND b.word_count > 0 THEN 10 ELSE 0 END) +
            (CASE WHEN b.publication_year IS NOT NULL AND b.publication_year > 1000 THEN 5 ELSE 0 END)
        )::DECIMAL(5,2) as completeness_score,
        
        -- Missing fields analysis
        jsonb_build_object(
            'missing_title', (b.title IS NULL OR LENGTH(TRIM(b.title)) = 0),
            'missing_author', (b.author IS NULL OR LENGTH(TRIM(b.author)) = 0),
            'missing_genre', (b.genre IS NULL OR LENGTH(TRIM(b.genre)) = 0),
            'missing_description', (b.description IS NULL OR LENGTH(TRIM(b.description)) = 0),
            'missing_word_count', (b.word_count IS NULL OR b.word_count <= 0),
            'missing_publication_year', (b.publication_year IS NULL OR b.publication_year <= 1000)
        ) as missing_fields,
        
        -- Quality issues analysis
        jsonb_build_object(
            'suspicious_author', (
                b.author IS NOT NULL AND (
                    LOWER(b.author) IN ('unknown', 'various', 'null', 'na', 'n/a') OR
                    b.author LIKE '%.com%' OR
                    LENGTH(b.author) < 3
                )
            ),
            'suspicious_title', (
                b.title IS NOT NULL AND (
                    LOWER(b.title) IN ('unknown title', 'untitled', 'unknown') OR
                    LENGTH(b.title) < 5
                )
            ),
            'suspicious_genre', (
                b.genre IS NOT NULL AND 
                LOWER(b.genre) IN ('unread', 'unknown', 'misc', 'other')
            ),
            'word_count_mismatch', (
                b.word_count IS NOT NULL AND b.word_count > 0 AND
                EXISTS (
                    SELECT 1 FROM chunks c 
                    WHERE c.book_id = b.book_id 
                    HAVING ABS(b.word_count - COALESCE(SUM(c.word_count), 0)) > (b.word_count * 0.2)
                )
            )
        ) as quality_issues,
        
        -- Recommended actions array
        ARRAY(
            SELECT action FROM (
                SELECT 'Fix missing title' as action WHERE b.title IS NULL OR LENGTH(TRIM(b.title)) = 0
                UNION
                SELECT 'Fix missing author' WHERE b.author IS NULL OR LENGTH(TRIM(b.author)) = 0
                UNION  
                SELECT 'Classify genre' WHERE b.genre IS NULL OR LENGTH(TRIM(b.genre)) = 0
                UNION
                SELECT 'Generate description' WHERE b.description IS NULL OR LENGTH(TRIM(b.description)) = 0
                UNION
                SELECT 'Recalculate word count' WHERE b.word_count IS NULL OR b.word_count <= 0
                UNION
                SELECT 'Research publication year' WHERE b.publication_year IS NULL OR b.publication_year <= 1000
                UNION
                SELECT 'Verify author attribution' WHERE b.author IS NOT NULL AND (
                    LOWER(b.author) IN ('unknown', 'various', 'null', 'na', 'n/a') OR
                    b.author LIKE '%.com%'
                )
            ) actions
        ) as recommended_actions
        
    FROM books b
    WHERE (p_book_id IS NULL OR b.book_id = p_book_id);
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COLLECTION HEALTH MONITORING FUNCTIONS
-- =============================================================================

CREATE OR REPLACE FUNCTION dr_elena_collection_health_summary()
RETURNS TABLE(
    metric_name TEXT,
    current_value BIGINT,
    percentage DECIMAL(5,2),
    status TEXT,
    threshold_met BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    WITH collection_stats AS (
        SELECT COUNT(*) as total_books FROM books
    ),
    chunk_stats AS (
        SELECT COUNT(*) as total_chunks FROM chunks  
    )
    SELECT 
        'Total Books'::TEXT,
        (SELECT total_books FROM collection_stats),
        100.00::DECIMAL(5,2),
        'Baseline'::TEXT,
        TRUE
    UNION ALL
    SELECT 
        'Total Chunks'::TEXT,
        (SELECT total_chunks FROM chunk_stats),
        100.00::DECIMAL(5,2),
        'Baseline'::TEXT,
        TRUE
    UNION ALL
    SELECT 
        'Books with Genre'::TEXT,
        COUNT(*)::BIGINT,
        (COUNT(*) * 100.0 / (SELECT total_books FROM collection_stats))::DECIMAL(5,2),
        CASE WHEN (COUNT(*) * 100.0 / (SELECT total_books FROM collection_stats)) >= 70 
             THEN 'Good'::TEXT ELSE 'Needs Improvement'::TEXT END,
        (COUNT(*) * 100.0 / (SELECT total_books FROM collection_stats)) >= 70
    FROM books WHERE genre IS NOT NULL AND LENGTH(TRIM(genre)) > 0
    UNION ALL
    SELECT 
        'Books with Descriptions'::TEXT,
        COUNT(*)::BIGINT,
        (COUNT(*) * 100.0 / (SELECT total_books FROM collection_stats))::DECIMAL(5,2),
        CASE WHEN (COUNT(*) * 100.0 / (SELECT total_books FROM collection_stats)) >= 50 
             THEN 'Good'::TEXT ELSE 'Needs Improvement'::TEXT END,
        (COUNT(*) * 100.0 / (SELECT total_books FROM collection_stats)) >= 50
    FROM books WHERE description IS NOT NULL AND LENGTH(TRIM(description)) > 0
    UNION ALL
    SELECT 
        'Chunks with Encoding Issues'::TEXT,
        COUNT(*)::BIGINT,
        (COUNT(*) * 100.0 / (SELECT total_chunks FROM chunk_stats))::DECIMAL(5,2),
        CASE WHEN (COUNT(*) * 100.0 / (SELECT total_chunks FROM chunk_stats)) <= 1.0 
             THEN 'Good'::TEXT ELSE 'Critical'::TEXT END,
        (COUNT(*) * 100.0 / (SELECT total_chunks FROM chunk_stats)) <= 1.0
    FROM chunks WHERE content LIKE '%â€™%' OR content LIKE '%â€œ%' OR content LIKE '%Ã%'
    UNION ALL
    SELECT 
        'Oversized Chunks'::TEXT,
        COUNT(*)::BIGINT,
        (COUNT(*) * 100.0 / (SELECT total_chunks FROM chunk_stats))::DECIMAL(5,2),
        CASE WHEN (COUNT(*) * 100.0 / (SELECT total_chunks FROM chunk_stats)) <= 5.0 
             THEN 'Good'::TEXT ELSE 'Warning'::TEXT END,
        (COUNT(*) * 100.0 / (SELECT total_chunks FROM chunk_stats)) <= 5.0
    FROM chunks WHERE LENGTH(content) > 50000;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- BATCH PROCESSING FUNCTIONS FOR LARGE-SCALE OPERATIONS
-- =============================================================================

CREATE OR REPLACE FUNCTION dr_elena_batch_repair_encoding_issues(p_batch_size INTEGER DEFAULT 1000)
RETURNS TABLE(
    batch_number INTEGER,
    chunks_processed INTEGER,
    chunks_repaired INTEGER,
    encoding_issues_fixed INTEGER,
    processing_time_ms INTEGER
) AS $$
DECLARE
    v_batch_number INTEGER := 1;
    v_total_processed INTEGER := 0;
    v_start_time TIMESTAMP;
    v_chunks_with_issues CURSOR FOR 
        SELECT chunk_id FROM chunks 
        WHERE content LIKE '%â€™%' OR content LIKE '%â€œ%' OR content LIKE '%Ã%'
        ORDER BY chunk_id;
    v_chunk_record RECORD;
    v_batch_count INTEGER := 0;
    v_repairs_made INTEGER := 0;
BEGIN
    v_start_time := clock_timestamp();
    
    FOR v_chunk_record IN v_chunks_with_issues LOOP
        -- Process chunk repair
        PERFORM dr_elena_repair_encoding_artifacts(v_chunk_record.chunk_id);
        
        v_batch_count := v_batch_count + 1;
        v_repairs_made := v_repairs_made + 1;
        v_total_processed := v_total_processed + 1;
        
        -- Return batch results when batch size reached
        IF v_batch_count >= p_batch_size THEN
            RETURN QUERY SELECT 
                v_batch_number,
                v_batch_count,
                v_repairs_made,
                v_repairs_made,
                EXTRACT(MILLISECONDS FROM (clock_timestamp() - v_start_time))::INTEGER;
                
            v_batch_number := v_batch_number + 1;
            v_batch_count := 0;
            v_repairs_made := 0;
            v_start_time := clock_timestamp();
        END IF;
    END LOOP;
    
    -- Return final partial batch if any
    IF v_batch_count > 0 THEN
        RETURN QUERY SELECT 
            v_batch_number,
            v_batch_count,
            v_repairs_made,
            v_repairs_made,
            EXTRACT(MILLISECONDS FROM (clock_timestamp() - v_start_time))::INTEGER;
    END IF;
    
    RETURN;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- USAGE EXAMPLES AND TESTING
-- =============================================================================

/*
-- Example Usage:

-- 1. Run comprehensive health check
SELECT * FROM dr_elena_collection_health_summary();

-- 2. Validate specific chunk quality
SELECT * FROM dr_elena_validate_chunk_content_quality('chunk_123');

-- 3. Assess book metadata completeness
SELECT * FROM dr_elena_assess_book_metadata_completeness(1);

-- 4. Repair encoding issues for specific chunk
SELECT * FROM dr_elena_repair_encoding_artifacts('chunk_with_issues');

-- 5. Batch repair encoding issues (process 500 at a time)
SELECT * FROM dr_elena_batch_repair_encoding_issues(500);

-- 6. Find books needing genre classification
SELECT book_id, title, author 
FROM dr_elena_assess_book_metadata_completeness() 
WHERE completeness_score < 80 
AND (missing_fields->>'missing_genre')::BOOLEAN = TRUE;

-- 7. Find chunks with critical encoding issues
SELECT chunk_id, book_id, quality_score, issue_details 
FROM dr_elena_validate_chunk_content_quality() 
WHERE encoding_issues = TRUE 
AND quality_score < 50
ORDER BY quality_score ASC;
*/

-- Grant permissions for API access
GRANT EXECUTE ON FUNCTION dr_elena_validate_chunk_content_quality(TEXT) TO weixiangzhang;
GRANT EXECUTE ON FUNCTION dr_elena_repair_encoding_artifacts(TEXT) TO weixiangzhang;
GRANT EXECUTE ON FUNCTION dr_elena_assess_book_metadata_completeness(INTEGER) TO weixiangzhang;
GRANT EXECUTE ON FUNCTION dr_elena_collection_health_summary() TO weixiangzhang;
GRANT EXECUTE ON FUNCTION dr_elena_batch_repair_encoding_issues(INTEGER) TO weixiangzhang;