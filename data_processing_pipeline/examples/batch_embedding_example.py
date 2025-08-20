#!/usr/bin/env python3
"""
📦 Batch Embedding Processing Example
====================================
Example showing how to process multiple text chunks efficiently.
"""

import sys
import time
import json
from pathlib import Path
from typing import List, Dict

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.append(str(scripts_dir))

from ollama_vector_embedder import OllamaVectorEmbedder

def batch_embedding_example():
    """Example of batch processing embeddings"""
    print("📦 Batch Embedding Processing Example")
    print("=" * 45)
    
    # Database configuration
    db_config = {
        'host': 'localhost',
        'database': 'knowledge_base',
        'user': 'weixiangzhang',
        'port': 5432
    }
    
    # Sample text chunks (simulating book content)
    text_chunks = [
        "In the vast digital library, every possible combination of characters exists somewhere among the endless shelves.",
        "Artificial intelligence has revolutionized how we process and understand human language at unprecedented scales.",
        "The semantic search capabilities allow readers to find relevant passages even when exact keywords don't match.",
        "Vector embeddings capture the deep meaning and context of text in high-dimensional mathematical representations.",
        "PostgreSQL with pgvector extension provides efficient storage and retrieval of these semantic embeddings."
    ]
    
    # Test with BGE-M3 model
    print(f"\n🧠 Processing {len(text_chunks)} chunks with BGE-M3:")
    print("-" * 40)
    
    try:
        # Initialize embedder
        embedder = OllamaVectorEmbedder(db_config, embedding_model="bge-m3")
        
        results = []
        total_start_time = time.time()
        
        for i, chunk in enumerate(text_chunks, 1):
            print(f"Processing chunk {i}/{len(text_chunks)}...")
            
            start_time = time.time()
            embedding = embedder.generate_embedding(chunk)
            processing_time = (time.time() - start_time) * 1000
            
            if embedding:
                result = {
                    'chunk_id': f"example_chunk_{i}",
                    'text_preview': chunk[:50] + "...",
                    'embedding_dimensions': len(embedding),
                    'processing_time_ms': processing_time,
                    'success': True
                }
                print(f"  ✅ {len(embedding)} dims in {processing_time:.1f}ms")
            else:
                result = {
                    'chunk_id': f"example_chunk_{i}",
                    'text_preview': chunk[:50] + "...",
                    'success': False
                }
                print(f"  ❌ Failed")
            
            results.append(result)
            
            # Small delay to avoid overwhelming Ollama
            time.sleep(0.1)
        
        total_time = (time.time() - total_start_time) * 1000
        successful_embeddings = sum(1 for r in results if r['success'])
        
        print(f"\n📊 Batch Processing Summary:")
        print(f"  Total chunks: {len(text_chunks)}")
        print(f"  Successful: {successful_embeddings}")
        print(f"  Failed: {len(text_chunks) - successful_embeddings}")
        print(f"  Total time: {total_time:.1f}ms")
        print(f"  Average per chunk: {total_time / len(text_chunks):.1f}ms")
        
        if successful_embeddings > 0:
            avg_processing_time = sum(r.get('processing_time_ms', 0) for r in results if r['success']) / successful_embeddings
            estimated_hourly_rate = (3600 * 1000) / avg_processing_time
            print(f"  Estimated rate: {estimated_hourly_rate:.0f} embeddings/hour")
        
        # Save results
        output_file = Path(__file__).parent / "batch_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Batch processing error: {e}")
    
    print(f"\n🎉 Batch processing example complete!")

if __name__ == "__main__":
    batch_embedding_example()