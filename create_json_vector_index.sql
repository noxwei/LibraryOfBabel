-- Create HNSW Index on JSON-to-Vector Conversion for Fast Semantic Search
-- LibraryOfBabel Team: Dr. Sarah Chen (陈雪芳)

-- Create functional HNSW index on JSON embedding conversion for nomic-embed-text
-- This allows us to use HNSW indexing without converting all data upfront
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunk_embeddings_json_nomic_hnsw 
ON chunk_embeddings 
USING hnsw (json_to_vector_768(embedding) vector_cosine_ops)
WHERE embedding_model = 'nomic-embed-text' 
    AND embedding IS NOT NULL;

-- Test the index works with our semantic search pattern
EXPLAIN (ANALYZE, BUFFERS) 
SELECT ce.chunk_id, b.title
FROM chunk_embeddings ce
JOIN chunks c ON ce.chunk_id = c.chunk_id
JOIN books b ON c.book_id = b.book_id
WHERE ce.embedding_model = 'nomic-embed-text'
    AND c.chunk_type = 'fullbook'
    AND ce.embedding IS NOT NULL
ORDER BY json_to_vector_768(ce.embedding) <=> json_to_vector_768('{"0": 0.1, "1": 0.2, "2": 0.3}'::jsonb)
LIMIT 3;