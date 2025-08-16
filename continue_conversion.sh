#!/bin/bash
# Continue batch conversion of embeddings
# LibraryOfBabel Team: Dr. Sarah Chen (陈雪芳)

echo "Starting batch conversion of nomic embeddings..."

for i in {1..50}; do
    echo "Batch $i: Converting 100 embeddings..."
    
    psql "host=localhost port=5432 dbname=knowledge_base user=weixiangzhang" -c "
        UPDATE chunk_embeddings 
        SET embedding_vector = json_to_vector_768(embedding) 
        WHERE embedding_id IN (
            SELECT ce.embedding_id 
            FROM chunk_embeddings ce 
            JOIN chunks c ON ce.chunk_id = c.chunk_id 
            WHERE ce.embedding_model = 'nomic-embed-text' 
                AND c.chunk_type = 'fullbook' 
                AND ce.embedding IS NOT NULL 
                AND ce.embedding_vector IS NULL 
            LIMIT 100
        );
    "
    
    # Check progress
    converted=$(psql "host=localhost port=5432 dbname=knowledge_base user=weixiangzhang" -t -c "
        SELECT COUNT(ce.embedding_vector) 
        FROM chunk_embeddings ce 
        JOIN chunks c ON ce.chunk_id = c.chunk_id 
        WHERE ce.embedding_model = 'nomic-embed-text' 
            AND c.chunk_type = 'fullbook' 
            AND ce.embedding_vector IS NOT NULL;
    " | xargs)
    
    echo "Progress: $converted/4956 embeddings converted"
    
    # If all done, break
    if [ "$converted" -ge 4956 ]; then
        echo "Conversion complete!"
        break
    fi
    
    # Small delay
    sleep 1
done

echo "Final check..."
psql "host=localhost port=5432 dbname=knowledge_base user=weixiangzhang" -c "
    SELECT 
        COUNT(*) as total,
        COUNT(ce.embedding_vector) as native_vectors,
        ROUND(COUNT(ce.embedding_vector) * 100.0 / COUNT(*), 1) as percent_converted
    FROM chunk_embeddings ce 
    JOIN chunks c ON ce.chunk_id = c.chunk_id 
    WHERE ce.embedding_model = 'nomic-embed-text' 
        AND c.chunk_type = 'fullbook';
"