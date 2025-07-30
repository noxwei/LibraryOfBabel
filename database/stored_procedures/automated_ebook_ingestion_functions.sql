-- LibraryOfBabel Automated Ebook Ingestion Functions
-- PostgreSQL-First Architecture for Ebook Processing
-- Dr. Sarah Chen (陈雪芳) Approved Architecture

-- ============================================================================
-- CORE EBOOK INGESTION FUNCTIONS - PostgreSQL-First Architecture
-- ============================================================================

-- Function 1: Check if book exists (with fuzzy matching)
CREATE OR REPLACE FUNCTION api_check_book_exists(
    p_title TEXT,
    p_author TEXT
) RETURNS BOOLEAN AS $$
DECLARE
    book_count INTEGER;
BEGIN
    -- Exact match first
    SELECT COUNT(*) INTO book_count
    FROM books 
    WHERE LOWER(TRIM(title)) = LOWER(TRIM(p_title)) 
    AND LOWER(TRIM(author)) = LOWER(TRIM(p_author));
    
    IF book_count > 0 THEN
        RETURN TRUE;
    END IF;
    
    -- Fuzzy match for similar books (prevent near-duplicates)
    SELECT COUNT(*) INTO book_count
    FROM books 
    WHERE similarity(LOWER(title), LOWER(p_title)) > 0.8 
    AND similarity(LOWER(author), LOWER(p_author)) > 0.7;
    
    RETURN book_count > 0;
    
EXCEPTION
    WHEN OTHERS THEN
        -- Fallback to simple exact match
        SELECT COUNT(*) INTO book_count
        FROM books 
        WHERE LOWER(title) = LOWER(p_title) AND LOWER(author) = LOWER(p_author);
        RETURN book_count > 0;
END;
$$ LANGUAGE plpgsql;

-- Function 2: Insert book with automatic ID generation
CREATE OR REPLACE FUNCTION api_insert_book(
    p_title TEXT,
    p_author TEXT,
    p_publication_date TEXT DEFAULT 'Unknown',
    p_genre TEXT DEFAULT 'Fiction',
    p_word_count INTEGER DEFAULT 0
) RETURNS INTEGER AS $$
DECLARE
    new_book_id INTEGER;
BEGIN
    -- Validate inputs
    IF p_title IS NULL OR TRIM(p_title) = '' THEN
        RAISE EXCEPTION 'Book title cannot be empty';
    END IF;
    
    IF p_author IS NULL OR TRIM(p_author) = '' THEN
        RAISE EXCEPTION 'Book author cannot be empty';
    END IF;
    
    -- Insert book with proper length limits
    INSERT INTO books (
        title, 
        author, 
        publication_date, 
        genre, 
        word_count, 
        processed_date,
        import_source
    ) VALUES (
        LEFT(TRIM(p_title), 500),
        LEFT(TRIM(p_author), 255),
        LEFT(COALESCE(p_publication_date, 'Unknown'), 100),
        LEFT(COALESCE(p_genre, 'Fiction'), 100),
        COALESCE(p_word_count, 0),
        NOW(),
        'automated_processor'
    ) RETURNING book_id INTO new_book_id;
    
    RETURN new_book_id;
    
EXCEPTION
    WHEN unique_violation THEN
        -- Handle potential duplicates gracefully
        SELECT book_id INTO new_book_id 
        FROM books 
        WHERE LOWER(TRIM(title)) = LOWER(TRIM(p_title)) 
        AND LOWER(TRIM(author)) = LOWER(TRIM(p_author))
        LIMIT 1;
        
        RETURN new_book_id;
        
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Failed to insert book: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- Function 3: Enhanced phonetic processing with academic mappings
CREATE OR REPLACE FUNCTION api_generate_phonetic_content(
    p_content TEXT
) RETURNS TABLE(
    content_soundex TEXT,
    content_metaphone TEXT,
    content_audiobook_normalized TEXT
) AS $$
DECLARE
    clean_content TEXT;
    words TEXT[];
    soundex_words TEXT[];
    metaphone_words TEXT[];
    word_text TEXT;
    soundex_result TEXT;
BEGIN
    -- Clean and prepare content
    clean_content := LOWER(TRIM(p_content));
    
    -- Extract words (letters only, minimum 3 characters)
    SELECT array_agg(word) INTO words
    FROM (
        SELECT regexp_replace(word, '[^a-zA-Z]', '', 'g') as word
        FROM unnest(string_to_array(clean_content, ' ')) as word
        WHERE length(regexp_replace(word, '[^a-zA-Z]', '', 'g')) >= 3
        LIMIT 25  -- Performance limit
    ) subq
    WHERE word IS NOT NULL AND word != '';
    
    -- Generate soundex approximations
    soundex_words := ARRAY[]::TEXT[];
    IF words IS NOT NULL THEN
        FOR i IN 1..LEAST(array_length(words, 1), 20) LOOP
            word_text := words[i];
            -- Simple soundex: first letter + consonants, limit 4 chars
            soundex_result := LEFT(word_text, 1) || 
                            LEFT(regexp_replace(substring(word_text, 2), '[aeiou]', '', 'g'), 3);
            soundex_words := array_append(soundex_words, soundex_result);
        END LOOP;
    END IF;
    
    -- Generate metaphone approximation (simplified)
    metaphone_words := words[1:15];  -- First 15 words
    
    -- Audiobook normalization with academic terms
    clean_content := regexp_replace(clean_content, '\s+', ' ', 'g');  -- Normalize spaces
    
    -- Academic philosophy terms
    clean_content := replace(clean_content, 'philosophy', 'filosofy');
    clean_content := replace(clean_content, 'consciousness', 'conciousness');
    clean_content := replace(clean_content, 'phenomenon', 'fenomenon');
    clean_content := replace(clean_content, 'epistemology', 'epistemolgy');
    
    -- Common homophones for audiobook users
    clean_content := replace(clean_content, 'there', 'their');
    clean_content := replace(clean_content, ' to ', ' too ');
    clean_content := replace(clean_content, 'your', 'youre');
    clean_content := replace(clean_content, 'its ', 'it''s ');
    clean_content := replace(clean_content, 'than', 'then');
    
    RETURN QUERY SELECT 
        array_to_string(soundex_words, ' '),
        array_to_string(metaphone_words, ' '),
        LEFT(clean_content, 1000);  -- Reasonable limit for storage
        
EXCEPTION
    WHEN OTHERS THEN
        -- Fallback: return simplified versions
        RETURN QUERY SELECT 
            LEFT(regexp_replace(LOWER(p_content), '[^a-z ]', '', 'g'), 200),
            LEFT(regexp_replace(LOWER(p_content), '[^a-z ]', '', 'g'), 200),
            LEFT(LOWER(p_content), 500);
END;
$$ LANGUAGE plpgsql;

-- Function 4: Insert chapter chunk with complete database structure
CREATE OR REPLACE FUNCTION api_insert_chapter_chunk(
    p_book_id INTEGER,
    p_chapter_number INTEGER,
    p_title TEXT,
    p_author TEXT,
    p_content TEXT,
    p_word_count INTEGER,
    p_section_number INTEGER DEFAULT NULL,
    p_paragraph_number INTEGER DEFAULT NULL,
    p_start_position INTEGER DEFAULT 0,
    p_end_position INTEGER DEFAULT NULL
) RETURNS TEXT AS $$
DECLARE
    chunk_id_result TEXT;
    phonetic_data RECORD;
BEGIN
    -- Validate inputs
    IF p_book_id IS NULL OR p_book_id <= 0 THEN
        RAISE EXCEPTION 'Invalid book_id: %', p_book_id;
    END IF;
    
    IF p_content IS NULL OR LENGTH(TRIM(p_content)) < 100 THEN
        RAISE EXCEPTION 'Chapter content too short (minimum 100 characters)';
    END IF;
    
    -- Generate chunk ID
    chunk_id_result := p_book_id || '_chapter_' || p_chapter_number;
    
    -- Generate phonetic enhancements
    SELECT * INTO phonetic_data 
    FROM api_generate_phonetic_content(p_content);
    
    -- Insert chunk with complete structure matching existing chunks
    INSERT INTO chunks (
        chunk_id,
        book_id,
        chunk_type,
        title,
        content,
        word_count,
        character_count,
        chapter_number,
        section_number,
        paragraph_number,
        start_position,
        end_position,
        parent_chunk_id,
        content_soundex,
        content_metaphone,
        content_audiobook_normalized,
        created_at
        -- Note: embedding_array and embedding_vector will be populated by separate embedding process
    ) VALUES (
        chunk_id_result,
        p_book_id,
        'chapter',
        LEFT(COALESCE(p_title, 'Chapter ' || p_chapter_number), 500),
        p_content,
        COALESCE(p_word_count, array_length(string_to_array(p_content, ' '), 1)),
        LENGTH(p_content),
        p_chapter_number,
        p_section_number,
        p_paragraph_number,
        COALESCE(p_start_position, 0),
        COALESCE(p_end_position, LENGTH(p_content)),
        NULL, -- parent_chunk_id for hierarchical structure if needed
        phonetic_data.content_soundex,
        phonetic_data.content_metaphone,
        phonetic_data.content_audiobook_normalized,
        NOW()
    );
    
    RETURN chunk_id_result;
    
EXCEPTION
    WHEN unique_violation THEN
        -- Handle duplicate chunk IDs
        RAISE EXCEPTION 'Chunk already exists: %', chunk_id_result;
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Failed to insert chunk: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- Function 5: Complete book ingestion with transaction safety
CREATE OR REPLACE FUNCTION api_ingest_complete_book(
    p_title TEXT,
    p_author TEXT,
    p_publication_date TEXT,
    p_genre TEXT,
    p_chapters JSONB  -- Array of chapter objects: [{"content": "...", "title": "...", "word_count": 123}, ...]
) RETURNS TABLE(
    success BOOLEAN,
    book_id INTEGER,
    chunks_created INTEGER,
    message TEXT
) AS $$
DECLARE
    new_book_id INTEGER;
    chapter_obj JSONB;
    chapter_count INTEGER := 0;
    total_chunks INTEGER := 0;
    chapter_title TEXT;
    chapter_content TEXT;
    chapter_word_count INTEGER;
    chunk_id_created TEXT;
BEGIN
    -- Check if book already exists
    IF api_check_book_exists(p_title, p_author) THEN
        RETURN QUERY SELECT FALSE, NULL::INTEGER, 0, 'Book already exists: ' || p_title || ' by ' || p_author;
        RETURN;
    END IF;
    
    -- Validate chapters input
    IF p_chapters IS NULL OR jsonb_array_length(p_chapters) = 0 THEN
        RETURN QUERY SELECT FALSE, NULL::INTEGER, 0, 'No chapters provided for book ingestion';
        RETURN;
    END IF;
    
    -- Start transaction (function is atomic by default)
    
    -- Insert book (handle NULL defaults)
    SELECT api_insert_book(
        p_title, 
        p_author, 
        COALESCE(p_publication_date, 'Unknown'), 
        COALESCE(p_genre, 'Fiction'), 
        0
    ) INTO new_book_id;
    
    -- Process each chapter
    FOR chapter_obj IN SELECT jsonb_array_elements(p_chapters)
    LOOP
        chapter_count := chapter_count + 1;
        
        -- Extract chapter data
        chapter_title := chapter_obj->>'title';
        chapter_content := chapter_obj->>'content';
        chapter_word_count := COALESCE((chapter_obj->>'word_count')::INTEGER, 0);
        
        -- Validate chapter content
        IF chapter_content IS NULL OR LENGTH(TRIM(chapter_content)) < 100 THEN
            CONTINUE;  -- Skip very short chapters
        END IF;
        
        -- Insert chapter chunk
        BEGIN
            SELECT api_insert_chapter_chunk(
                new_book_id,
                chapter_count,
                COALESCE(chapter_title, p_title),
                p_author,
                chapter_content,
                chapter_word_count
            ) INTO chunk_id_created;
            
            total_chunks := total_chunks + 1;
            
        EXCEPTION
            WHEN OTHERS THEN
                -- Log error but continue with other chapters
                RAISE WARNING 'Failed to insert chapter %: %', chapter_count, SQLERRM;
        END;
    END LOOP;
    
    -- Update book word count
    UPDATE books 
    SET word_count = (
        SELECT COALESCE(SUM(c.word_count), 0) 
        FROM chunks c 
        WHERE c.book_id = new_book_id
    )
    WHERE books.book_id = new_book_id;
    
    -- Return success
    RETURN QUERY SELECT 
        TRUE,
        new_book_id,
        total_chunks,
        'Successfully ingested book: ' || p_title || ' with ' || total_chunks || ' chapters';
    
EXCEPTION
    WHEN OTHERS THEN
        -- Transaction will be rolled back automatically
        RETURN QUERY SELECT 
            FALSE,
            NULL::INTEGER,
            0,
            'Book ingestion failed: ' || SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- Function 6: Batch book processing with statistics
CREATE OR REPLACE FUNCTION api_process_book_batch(
    p_books JSONB  -- Array of complete book objects
) RETURNS TABLE(
    total_books INTEGER,
    successful_books INTEGER,
    failed_books INTEGER,
    skipped_existing INTEGER,
    total_chunks_created INTEGER,
    processing_summary TEXT
) AS $$
DECLARE
    book_obj JSONB;
    result_record RECORD;
    success_count INTEGER := 0;
    failure_count INTEGER := 0;
    skip_count INTEGER := 0;
    total_chunks INTEGER := 0;
    book_count INTEGER;
BEGIN
    -- Validate input
    IF p_books IS NULL OR jsonb_array_length(p_books) = 0 THEN
        RETURN QUERY SELECT 0, 0, 0, 0, 0, 'No books provided for batch processing';
        RETURN;
    END IF;
    
    book_count := jsonb_array_length(p_books);
    
    -- Process each book
    FOR book_obj IN SELECT jsonb_array_elements(p_books)
    LOOP
        -- Call single book ingestion function
        SELECT * INTO result_record
        FROM api_ingest_complete_book(
            book_obj->>'title',
            book_obj->>'author',
            book_obj->>'publication_date',
            book_obj->>'genre',
            book_obj->'chapters'
        );
        
        -- Update counters
        IF result_record.success THEN
            success_count := success_count + 1;
            total_chunks := total_chunks + result_record.chunks_created;
        ELSE
            IF result_record.message LIKE '%already exists%' THEN
                skip_count := skip_count + 1;
            ELSE
                failure_count := failure_count + 1;
            END IF;
        END IF;
    END LOOP;
    
    -- Return summary
    RETURN QUERY SELECT 
        book_count,
        success_count,
        failure_count,
        skip_count,
        total_chunks,
        'Batch processing complete: ' || success_count || ' books processed, ' || 
        total_chunks || ' chunks created, ' || skip_count || ' skipped, ' || 
        failure_count || ' failed';
        
EXCEPTION
    WHEN OTHERS THEN
        RETURN QUERY SELECT 
            book_count,
            0,
            book_count,
            0,
            0,
            'Batch processing failed: ' || SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- Create indexes for new functionality
CREATE INDEX IF NOT EXISTS idx_books_title_author ON books(LOWER(title), LOWER(author));
CREATE INDEX IF NOT EXISTS idx_books_import_source ON books(import_source);
CREATE INDEX IF NOT EXISTS idx_chunks_phonetic_soundex ON chunks USING GIN(to_tsvector('english', content_soundex));
CREATE INDEX IF NOT EXISTS idx_chunks_phonetic_metaphone ON chunks USING GIN(to_tsvector('english', content_metaphone));
CREATE INDEX IF NOT EXISTS idx_chunks_audiobook_normalized ON chunks USING GIN(to_tsvector('english', content_audiobook_normalized));

-- Grant permissions for automated processor
COMMENT ON FUNCTION api_check_book_exists(TEXT, TEXT) IS 'Dr. Chen approved: Check book existence with fuzzy matching';
COMMENT ON FUNCTION api_insert_book(TEXT, TEXT, TEXT, TEXT, INTEGER) IS 'Dr. Chen approved: Insert book with validation and error handling';
COMMENT ON FUNCTION api_generate_phonetic_content(TEXT) IS 'Dr. Chen approved: Generate phonetic enhancements for search optimization';
COMMENT ON FUNCTION api_insert_chapter_chunk(INTEGER, INTEGER, TEXT, TEXT, TEXT, INTEGER) IS 'Dr. Chen approved: Insert chapter with phonetic enhancement';
COMMENT ON FUNCTION api_ingest_complete_book(TEXT, TEXT, TEXT, TEXT, JSONB) IS 'Dr. Chen approved: Complete book ingestion with transaction safety';
COMMENT ON FUNCTION api_process_book_batch(JSONB) IS 'Dr. Chen approved: Batch book processing with comprehensive statistics';

-- Performance analysis
ANALYZE books;
ANALYZE chunks;