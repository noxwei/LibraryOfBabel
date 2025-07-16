#!/usr/bin/env python3
"""
🚀 MULTIPLE EMBEDDING MODELS DEMO
=================================

Demo script showing how to use multiple embedding models
to create embeddings for the same text content.
"""

import sys
import time
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))
sys.path.append(str(project_root))

from ollama_vector_embedder import OllamaVectorEmbedder
from config.api_config import get_database_config

def demo_multiple_embeddings():
    """Demo using multiple embedding models on the same content"""
    
    print("🚀 MULTIPLE EMBEDDING MODELS DEMO")
    print("=" * 50)
    
    # Sample text from LibraryOfBabel
    demo_text = """
    Artificial intelligence represents one of humanity's greatest achievements 
    and challenges. From philosophical questions about consciousness and free 
    will to practical applications in healthcare, education, and automation,
    AI touches every aspect of our evolving digital society.
    """
    
    models_to_test = ["nomic-embed-text", "bge-m3", "mxbai-embed-large"]
    db_config = get_database_config()
    
    results = {}
    
    for model_name in models_to_test:
        print(f"\n🧠 Testing {model_name}")
        print("-" * 30)
        
        # Initialize embedder with specific model
        embedder = OllamaVectorEmbedder(db_config, embedding_model=model_name)
        
        # Generate embedding
        start_time = time.time()
        embedding = embedder.generate_embedding(demo_text)
        processing_time = (time.time() - start_time) * 1000
        
        if embedding:
            results[model_name] = {
                'dimensions': len(embedding),
                'processing_time_ms': processing_time,
                'sample_values': embedding[:5],
                'success': True
            }
            
            print(f"✅ Success!")
            print(f"📊 Dimensions: {len(embedding)}")
            print(f"⏱️  Time: {processing_time:.1f}ms")
            print(f"🔢 First 3 values: {embedding[:3]}")
        else:
            results[model_name] = {'success': False}
            print(f"❌ Failed!")
    
    # Performance comparison
    print(f"\n📊 PERFORMANCE COMPARISON")
    print("=" * 40)
    
    for model, result in results.items():
        if result['success']:
            speed = f"{result['processing_time_ms']:.1f}ms"
            dims = result['dimensions']
            print(f"{model:20} | {dims:4d} dims | {speed:>8}")
    
    # Similarity check (basic)
    print(f"\n🔍 EMBEDDING ANALYSIS")
    print("=" * 30)
    
    successful_models = [m for m, r in results.items() if r['success']]
    
    if len(successful_models) > 1:
        print(f"✅ Successfully generated {len(successful_models)} different embeddings")
        print(f"📈 Higher dimensions may capture more nuanced meanings")
        print(f"⚡ Faster models better for real-time applications")
        
        # Find fastest and highest dimension model
        fastest = min(successful_models, key=lambda m: results[m]['processing_time_ms'])
        highest_dim = max(successful_models, key=lambda m: results[m]['dimensions'])
        
        print(f"\n🏆 Fastest: {fastest} ({results[fastest]['processing_time_ms']:.1f}ms)")
        print(f"🎯 Highest Dim: {highest_dim} ({results[highest_dim]['dimensions']} dims)")
    
    return results

if __name__ == "__main__":
    demo_multiple_embeddings()
    print(f"\n🎉 Demo complete! Your embedding models are ready for production.")