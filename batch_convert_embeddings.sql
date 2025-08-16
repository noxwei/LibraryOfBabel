-- Batch Convert JSON Embeddings to Native Vector Column
-- LibraryOfBabel Team: Dr. Sarah Chen (陈雪芳)

-- Check current status
SELECT 
    COUNT(*) as total_nomic,
    COUNT(ce.embedding_vector) as native_populated,
    COUNT(ce.embedding) as json_populated,
    COUNT(*) - COUNT(ce.embedding_vector) as need_conversion
FROM chunk_embeddings ce 
JOIN chunks c ON ce.chunk_id = c.chunk_id 
WHERE ce.embedding_model = 'nomic-embed-text' 
    AND c.chunk_type = 'fullbook';

-- Create batch conversion function to avoid timeouts
CREATE OR REPLACE FUNCTION convert_embeddings_batch(batch_size integer DEFAULT 100)
RETURNS text
LANGUAGE plpgsql
AS $$
DECLARE
    converted_count integer := 0;
    total_converted integer := 0;
    batch_start_time timestamp;
BEGIN
    LOOP
        batch_start_time := clock_timestamp();
        
        -- Convert one batch
        WITH batch_ids AS (
            SELECT ce.embedding_id
            FROM chunk_embeddings ce
            JOIN chunks c ON ce.chunk_id = c.chunk_id
            WHERE ce.embedding_model = 'nomic-embed-text'
                AND c.chunk_type = 'fullbook'
                AND ce.embedding IS NOT NULL
                AND ce.embedding_vector IS NULL
            LIMIT batch_size
        )
        UPDATE chunk_embeddings 
        SET embedding_vector = json_to_vector_768(embedding)
        WHERE embedding_id IN (SELECT embedding_id FROM batch_ids);
        
        GET DIAGNOSTICS converted_count = ROW_COUNT;
        total_converted := total_converted + converted_count;
        
        -- Log progress
        RAISE NOTICE 'Batch completed: % embeddings converted in % ms (Total: %)', 
            converted_count, 
            EXTRACT(milliseconds FROM clock_timestamp() - batch_start_time),
            total_converted;
        
        -- Exit if no more rows to convert
        EXIT WHEN converted_count = 0;
        
        -- Small delay to avoid overwhelming the system
        PERFORM pg_sleep(0.1);
    END LOOP;
    
    RETURN 'Conversion complete: ' || total_converted || ' embeddings converted to native vector format';
END;
$$;

-- Start the batch conversion (this will run in chunks to avoid timeouts)
SELECT convert_embeddings_batch(50);