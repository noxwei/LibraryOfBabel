-- Book Content Processing Functions
-- Dr. Sarah Chen (陈雪芳) PostgreSQL-First Architecture
-- Processes book content into chunks and embeddings

CREATE OR REPLACE FUNCTION api_process_book_content(
    p_book_id INTEGER,
    p_title TEXT,
    p_content TEXT
) RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_chunks_created INTEGER := 0;
    v_chunk_size INTEGER := 1000;
    v_content_length INTEGER;
    v_current_pos INTEGER := 1;
    v_chunk_content TEXT;
    v_chunk_id VARCHAR(255);
    v_chapter_number INTEGER := 1;
    v_chunk_number INTEGER := 1;
BEGIN
    -- Validate inputs
    IF p_book_id IS NULL OR p_content IS NULL OR LENGTH(p_content) < 100 THEN
        RETURN 0;
    END IF;
    
    -- Get content length
    v_content_length := LENGTH(p_content);
    
    -- Process content into chunks
    WHILE v_current_pos <= v_content_length LOOP
        -- Extract chunk content
        v_chunk_content := SUBSTRING(p_content FROM v_current_pos FOR v_chunk_size);
        
        -- Skip very short chunks at the end
        IF LENGTH(v_chunk_content) < 50 THEN
            EXIT;
        END IF;
        
        -- Generate chunk ID
        v_chunk_id := p_book_id || '_' || v_chapter_number || '_' || v_chunk_number;
        
        -- Insert chunk
        INSERT INTO chunks (
            chunk_id,
            book_id,
            chunk_type,
            chapter_number,
            content,
            word_count,
            created_at
        ) VALUES (
            v_chunk_id,
            p_book_id,
            'chapter',
            v_chapter_number,
            v_chunk_content,
            array_length(string_to_array(v_chunk_content, ' '), 1),
            NOW()
        ) ON CONFLICT (chunk_id) DO NOTHING;
        
        -- Check if insert was successful
        IF FOUND THEN
            v_chunks_created := v_chunks_created + 1;
        END IF;
        
        -- Move to next chunk
        v_current_pos := v_current_pos + v_chunk_size;
        v_chunk_number := v_chunk_number + 1;
        
        -- Start new chapter every 20 chunks
        IF v_chunk_number > 20 THEN
            v_chapter_number := v_chapter_number + 1;
            v_chunk_number := 1;
        END IF;
    END LOOP;
    
    -- Update book chunk count
    UPDATE books 
    SET chunk_count = v_chunks_created,
        searchable_chunk_count = v_chunks_created
    WHERE book_id = p_book_id;
    
    RETURN v_chunks_created;
    
EXCEPTION WHEN OTHERS THEN
    -- Log error and return 0
    RAISE WARNING 'Error processing book content for book_id %: %', p_book_id, SQLERRM;
    RETURN 0;
END;
$$;

-- Create book_contents table if it doesn't exist
CREATE TABLE IF NOT EXISTS book_contents (
    book_id INTEGER PRIMARY KEY REFERENCES books(book_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text/plain',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_book_contents_book_id ON book_contents(book_id);