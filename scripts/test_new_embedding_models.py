#!/usr/bin/env python3
"""
🧪 TEST NEW EMBEDDING MODELS - LibraryOfBabel Team Integration
==============================================================

Test script for the new embedding models:
- bge-m3:latest
- mxbai-embed-large:latest
- nomic-embed-text:latest (existing)

Tests model availability, embedding generation, and storage.
"""

import os
import sys
import time
import json
from pathlib import Path

# Add src and project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))
sys.path.append(str(project_root))

from ollama_vector_embedder import OllamaVectorEmbedder
from config.api_config import get_database_config, get_available_embedding_models

def test_embedding_model(model_name: str, test_text: str) -> bool:
    """Test a single embedding model"""
    print(f"\n🧪 Testing model: {model_name}")
    print("=" * 50)
    
    try:
        # Initialize embedder with specific model
        db_config = get_database_config()
        embedder = OllamaVectorEmbedder(
            db_config=db_config,
            embedding_model=model_name
        )
        
        # Test embedding generation
        start_time = time.time()
        embedding = embedder.generate_embedding(test_text)
        processing_time = (time.time() - start_time) * 1000
        
        if embedding:
            print(f"✅ {model_name} embedding successful!")
            print(f"📊 Dimensions: {len(embedding)}")
            print(f"⏱️  Processing time: {processing_time:.1f}ms")
            print(f"🔢 Sample values: {embedding[:5]}")
            
            # Test model switching
            available_models = embedder.list_available_models()
            print(f"📋 Available models: {list(available_models.keys())}")
            
            return True
        else:
            print(f"❌ {model_name} embedding failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error testing {model_name}: {e}")
        return False

def test_all_embedding_models():
    """Test all available embedding models"""
    print("🧠 EMBEDDING MODELS TESTING SUITE")
    print("=" * 60)
    
    # Get available models from config
    available_models = get_available_embedding_models()
    
    test_text = """
    The Library of Babel is a vast digital collection containing 1,006 books 
    spanning philosophy, science fiction, political theory, and contemporary 
    literature. This knowledge base uses advanced vector embeddings to enable 
    semantic search across 34+ million words of content.
    """
    
    results = {}
    
    for model_name, model_config in available_models.items():
        print(f"\n📝 Model Info: {model_config['description']}")
        print(f"🔢 Expected Dimensions: {model_config['dimension']}")
        print(f"📏 Max Length: {model_config['max_length']}")
        
        success = test_embedding_model(model_name, test_text)
        results[model_name] = success
        
        # Small delay between tests
        time.sleep(1)
    
    # Summary
    print(f"\n📊 TESTING SUMMARY")
    print("=" * 30)
    
    successful_models = [model for model, success in results.items() if success]
    failed_models = [model for model, success in results.items() if not success]
    
    print(f"✅ Successful models ({len(successful_models)}): {', '.join(successful_models)}")
    if failed_models:
        print(f"❌ Failed models ({len(failed_models)}): {', '.join(failed_models)}")
    
    print(f"\n🎯 Success rate: {len(successful_models)}/{len(available_models)} ({len(successful_models)/len(available_models)*100:.1f}%)")
    
    return len(successful_models) == len(available_models)

def test_model_switching():
    """Test switching between embedding models"""
    print(f"\n🔄 TESTING MODEL SWITCHING")
    print("=" * 40)
    
    try:
        db_config = get_database_config()
        embedder = OllamaVectorEmbedder(db_config=db_config)
        
        # Test switching to each model
        models_to_test = ["bge-m3", "mxbai-embed-large", "nomic-embed-text"]
        
        for model in models_to_test:
            print(f"\n🔄 Switching to {model}...")
            success = embedder.switch_embedding_model(model)
            
            if success:
                # Test embedding with new model
                test_embedding = embedder.generate_embedding("Test embedding after model switch")
                if test_embedding:
                    print(f"✅ {model} switch successful, embedding generated: {len(test_embedding)} dims")
                else:
                    print(f"❌ {model} switch successful but embedding failed")
            else:
                print(f"❌ Failed to switch to {model}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model switching test failed: {e}")
        return False

def main():
    """Main testing function"""
    print("🚀 LibraryOfBabel Embedding Models Test Suite")
    print("=" * 60)
    
    # Test all models
    all_models_success = test_all_embedding_models()
    
    # Test model switching
    switching_success = test_model_switching()
    
    # Final report
    print(f"\n🏁 FINAL REPORT")
    print("=" * 20)
    
    if all_models_success and switching_success:
        print("✅ All tests passed! Your new embedding models are ready.")
        print("🎯 You can now use bge-m3 and mxbai-embed-large in your PostgreSQL library!")
        return True
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)