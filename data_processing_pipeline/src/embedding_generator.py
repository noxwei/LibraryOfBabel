#!/usr/bin/env python3
"""
Embedding Generator for BabelProcessorDb Testing
===============================================

Limited-scale embedding generation using NOMIC and BGE-M3 models.
Connects to multiple Ollama instances with rate limiting for testing.

Based on multi-ollama architecture from LibraryOfBabel production.
"""

import os
import json
import time
import logging
import requests
import itertools
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Configure logging
logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """
    Limited-scale embedding generator for testing
    Supports NOMIC (768d) and BGE-M3 (1024d) models
    """
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = min(max_workers, 4)  # Limit for testing
        
        # Ollama URLs - use host.docker.internal for container
        base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.ollama_urls = [
            base_url,
            base_url.replace(':11434', ':11435'),
            base_url.replace(':11434', ':11436')
        ]
        
        # Round-robin URL selection
        self.url_pool = itertools.cycle(self.ollama_urls)
        
        # Rate limiting
        self.request_delay = 0.5  # 500ms between requests
        self.last_request_time = 0
        self.request_lock = threading.Lock()
        
        # Model configurations
        self.models = {
            'nomic-embed-text': {
                'dimensions': 768,
                'max_length': 8000
            },
            'bge-m3': {
                'dimensions': 1024,
                'max_length': 8192
            }
        }
        
        logger.info(f"Embedding generator initialized with {self.max_workers} workers")
        logger.info(f"Ollama URLs: {self.ollama_urls}")
    
    def test_ollama_connection(self) -> Dict[str, bool]:
        """Test connectivity to all Ollama instances"""
        results = {}
        
        for url in self.ollama_urls:
            try:
                response = requests.get(f"{url}/api/ps", timeout=10)
                results[url] = response.status_code == 200
                logger.info(f"Ollama {url}: {'✓' if results[url] else '✗'}")
            except Exception as e:
                results[url] = False
                logger.warning(f"Ollama {url}: Failed - {e}")
        
        return results
    
    def generate_embeddings(self, chunks: List[Dict], model_name: str) -> List[Dict]:
        """
        Generate embeddings for chunks using specified model
        
        Args:
            chunks: List of chunk dictionaries with 'chunk_id' and 'content'
            model_name: Model name ('nomic-embed-text' or 'bge-m3')
            
        Returns:
            List of embedding dictionaries
        """
        if not chunks:
            return []
        
        if model_name not in self.models:
            raise ValueError(f"Unsupported model: {model_name}")
        
        logger.info(f"Generating {model_name} embeddings for {len(chunks)} chunks")
        
        embeddings = []
        failed_chunks = []
        
        # Process chunks with limited workers
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit tasks
            future_to_chunk = {
                executor.submit(self._generate_single_embedding, chunk, model_name): chunk
                for chunk in chunks
            }
            
            # Collect results
            for future in as_completed(future_to_chunk):
                chunk = future_to_chunk[future]
                try:
                    embedding_data = future.result()
                    if embedding_data:
                        embeddings.append(embedding_data)
                    else:
                        failed_chunks.append(chunk['chunk_id'])
                except Exception as e:
                    logger.error(f"Error generating embedding for chunk {chunk['chunk_id']}: {e}")
                    failed_chunks.append(chunk['chunk_id'])
        
        success_rate = len(embeddings) / len(chunks) * 100 if chunks else 0
        logger.info(f"Generated {len(embeddings)}/{len(chunks)} embeddings ({success_rate:.1f}% success)")
        
        if failed_chunks:
            logger.warning(f"Failed chunks: {failed_chunks[:5]}{'...' if len(failed_chunks) > 5 else ''}")
        
        return embeddings
    
    def _generate_single_embedding(self, chunk: Dict, model_name: str) -> Optional[Dict]:
        """Generate embedding for single chunk with rate limiting"""
        
        # Rate limiting
        with self.request_lock:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.request_delay:
                time.sleep(self.request_delay - elapsed)
            self.last_request_time = time.time()
        
        # Get next URL from pool
        url = next(self.url_pool)
        
        try:
            # Prepare content (truncate if too long)
            content = chunk['content']
            max_length = self.models[model_name]['max_length']
            if len(content) > max_length:
                content = content[:max_length]
                logger.debug(f"Truncated content for chunk {chunk['chunk_id']}")
            
            # Make embedding request
            response = requests.post(
                f"{url}/api/embeddings",
                json={
                    "model": model_name,
                    "prompt": content
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding_vector = result.get('embedding')
                
                if embedding_vector and len(embedding_vector) == self.models[model_name]['dimensions']:
                    return {
                        'chunk_id': chunk['chunk_id'],
                        'embedding_model': model_name,
                        'embedding_vector': embedding_vector
                    }
                else:
                    logger.error(f"Invalid embedding dimensions for {chunk['chunk_id']}")
                    return None
            else:
                logger.error(f"Ollama request failed for {chunk['chunk_id']}: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout generating embedding for {chunk['chunk_id']}")
            return None
        except Exception as e:
            logger.error(f"Error generating embedding for {chunk['chunk_id']}: {e}")
            return None
    
    def check_model_availability(self, model_name: str) -> bool:
        """Check if model is available on any Ollama instance"""
        for url in self.ollama_urls:
            try:
                response = requests.get(f"{url}/api/ps", timeout=10)
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    if any(model.get('name', '').startswith(model_name) for model in models):
                        logger.info(f"Model {model_name} found on {url}")
                        return True
            except Exception as e:
                logger.debug(f"Error checking {url}: {e}")
                continue
        
        logger.warning(f"Model {model_name} not found on any Ollama instance")
        return False
    
    def load_model(self, model_name: str) -> bool:
        """Load model on all available Ollama instances"""
        success_count = 0
        
        for url in self.ollama_urls:
            try:
                response = requests.post(
                    f"{url}/api/pull",
                    json={"name": model_name},
                    timeout=300  # 5 minutes for model loading
                )
                if response.status_code == 200:
                    success_count += 1
                    logger.info(f"Loaded {model_name} on {url}")
                else:
                    logger.warning(f"Failed to load {model_name} on {url}: {response.status_code}")
            except Exception as e:
                logger.error(f"Error loading {model_name} on {url}: {e}")
        
        return success_count > 0
    
    def get_embedding_stats(self) -> Dict:
        """Get current embedding generation stats"""
        return {
            'max_workers': self.max_workers,
            'ollama_urls': self.ollama_urls,
            'supported_models': list(self.models.keys()),
            'rate_limit_delay': self.request_delay
        }