-- Convert JSON Embeddings to Native Vector Column for Performance
-- LibraryOfBabel Team: Dr. Sarah Chen (陈雪芳)

-- Update all nomic-embed-text embeddings to populate the native vector column
UPDATE chunk_embeddings 
SET embedding_vector = json_to_vector_768(embedding)
WHERE embedding_model = 'nomic-embed-text' 
    AND embedding IS NOT NULL 
    AND embedding_vector IS NULL;

-- Verify the conversion
SELECT 
    COUNT(*) as total_nomic,
    COUNT(embedding_vector) as native_vectors_populated,
    COUNT(embedding) as json_embeddings
FROM chunk_embeddings ce 
JOIN chunks c ON ce.chunk_id = c.chunk_id 
WHERE ce.embedding_model = 'nomic-embed-text' 
    AND c.chunk_type = 'fullbook';

-- Check a sample to verify the conversion worked
SELECT 
    ce.chunk_id,
    ce.embedding_vector IS NOT NULL as has_native_vector,
    ce.embedding IS NOT NULL as has_json_embedding
FROM chunk_embeddings ce 
JOIN chunks c ON ce.chunk_id = c.chunk_id 
WHERE ce.embedding_model = 'nomic-embed-text' 
    AND c.chunk_type = 'fullbook'
LIMIT 5;