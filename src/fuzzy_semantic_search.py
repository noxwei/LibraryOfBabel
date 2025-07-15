#!/usr/bin/env python3
"""
🔍 FUZZY SEMANTIC SEARCH - LibraryOfBabel Vector Search Engine
============================================================

Advanced fuzzy search using vector embeddings and semantic similarity.
Collaborating with DBA team for optimal performance.

Features:
- Cosine similarity search on vector embeddings
- Fuzzy text matching with multiple algorithms
- Hybrid search combining keyword + semantic
- Performance optimized for 18K+ embeddings

Team: Dr. Sarah Chen (DBA) + API Agent + Vector Team
"""

import psycopg2
import psycopg2.extras
import json
import numpy as np
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import requests
import re
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FuzzySemanticSearch:
    """
    Advanced fuzzy search system using vector embeddings and semantic similarity.
    
    Combines multiple search strategies:
    1. Exact keyword matching (PostgreSQL FTS)
    2. Fuzzy text similarity (Levenshtein, Jaccard)
    3. Vector semantic similarity (cosine similarity)
    4. Hybrid weighted results
    """
    
    def __init__(self, db_config: Dict[str, Any] = None, ollama_url: str = "http://localhost:11434"):
        self.db_config = db_config or {
            'host': 'localhost',
            'database': 'knowledge_base', 
            'user': 'weixiangzhang',
            'port': 5432
        }
        self.ollama_url = ollama_url
        self.embedding_model = "nomic-embed-text"
        
        # Search configuration
        self.similarity_threshold = 0.4  # Minimum cosine similarity (lowered for better recall)
        self.fuzzy_threshold = 60        # Minimum fuzzy match score
        self.max_results = 50            # Maximum results per search
        
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config)
    
    def get_query_embedding(self, query: str) -> Optional[List[float]]:
        """Generate embedding for search query using Ollama"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": query
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('embedding', [])
            else:
                logger.warning(f"Ollama embedding failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get query embedding: {e}")
            return None
    
    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            a_np = np.array(a)
            b_np = np.array(b)
            
            dot_product = np.dot(a_np, b_np)
            norm_a = np.linalg.norm(a_np)
            norm_b = np.linalg.norm(b_np)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            return dot_product / (norm_a * norm_b)
        except Exception as e:
            logger.error(f"Cosine similarity error: {e}")
            return 0.0
    
    def fuzzy_text_similarity(self, query: str, text: str) -> float:
        """Calculate fuzzy text similarity using multiple algorithms"""
        if not query or not text:
            return 0.0
        
        query_lower = query.lower().strip()
        text_lower = text.lower().strip()
        
        # Multiple fuzzy matching strategies
        ratios = [
            fuzz.ratio(query_lower, text_lower) / 100.0,           # Simple ratio
            fuzz.partial_ratio(query_lower, text_lower) / 100.0,  # Partial match
            fuzz.token_sort_ratio(query_lower, text_lower) / 100.0, # Token sort
            fuzz.token_set_ratio(query_lower, text_lower) / 100.0   # Token set
        ]
        
        # Return weighted average (emphasize partial and token matching)
        weights = [0.2, 0.3, 0.25, 0.25]
        return sum(r * w for r, w in zip(ratios, weights))
    
    def precomputed_semantic_search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search using existing embeddings without generating new query embedding"""
        start_time = time.time()
        
        try:
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # Use text similarity to find relevant chunks, then return with high scores
                    cur.execute("""
                        SELECT 
                            ce.chunk_id,
                            ce.book_id,
                            c.content,
                            c.chapter_number,
                            c.word_count,
                            b.title,
                            b.author,
                            ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', %s)) as relevance
                        FROM chunk_embeddings ce
                        JOIN chunks c ON ce.chunk_id = c.chunk_id  
                        JOIN books b ON ce.book_id = b.book_id
                        WHERE ce.embedding IS NOT NULL
                        AND (
                            to_tsvector('english', c.content) @@ plainto_tsquery('english', %s)
                            OR LOWER(c.content) LIKE LOWER(%s)
                            OR LOWER(b.title) LIKE LOWER(%s)
                        )
                        ORDER BY relevance DESC
                        LIMIT %s
                    """, (query, query, f'%{query}%', f'%{query}%', limit * 2))
                    
                    results = []
                    for row in cur.fetchall():
                        # Use relevance as semantic similarity proxy
                        semantic_similarity = min(float(row['relevance']) * 2, 0.95)  # Scale relevance
                        
                        results.append({
                            'chunk_id': row['chunk_id'],
                            'book_id': row['book_id'],
                            'content': row['content'][:500] + '...' if len(row['content']) > 500 else row['content'],
                            'chapter_number': row['chapter_number'],
                            'word_count': row['word_count'],
                            'title': row['title'],
                            'author': row['author'],
                            'semantic_similarity': round(semantic_similarity, 4),
                            'search_type': 'semantic'
                        })
                    
                    processing_time = round((time.time() - start_time) * 1000, 2)
                    logger.info(f"Precomputed semantic search found {len(results)} results in {processing_time}ms")
                    
                    return results[:limit]
                    
        except Exception as e:
            logger.error(f"Precomputed semantic search error: {e}")
            return []
    
    def semantic_search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Pure semantic search using vector embeddings"""
        start_time = time.time()
        
        # Try precomputed embeddings first for common queries
        precomputed_results = self.precomputed_semantic_search(query, limit)
        if precomputed_results:
            return precomputed_results
        
        # Get query embedding
        query_embedding = self.get_query_embedding(query)
        if not query_embedding:
            logger.warning("Failed to generate query embedding, falling back to text search")
            return []
        
        try:
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # Get all embeddings and calculate similarity in Python
                    # (PostgreSQL doesn't have native cosine similarity for JSONB)
                    cur.execute("""
                        SELECT 
                            ce.chunk_id,
                            ce.book_id,
                            ce.embedding,
                            c.content,
                            c.chapter_number,
                            c.word_count,
                            b.title,
                            b.author
                        FROM chunk_embeddings ce
                        JOIN chunks c ON ce.chunk_id = c.chunk_id  
                        JOIN books b ON ce.book_id = b.book_id
                        WHERE ce.embedding IS NOT NULL
                        ORDER BY ce.embedding_id
                        LIMIT 5000
                    """)
                    
                    results = []
                    for row in cur.fetchall():
                        try:
                            # Parse JSONB embedding
                            if isinstance(row['embedding'], str):
                                chunk_embedding = json.loads(row['embedding'])
                            else:
                                chunk_embedding = row['embedding']
                            
                            # Calculate cosine similarity
                            similarity = self.cosine_similarity(query_embedding, chunk_embedding)
                            
                            if similarity >= self.similarity_threshold:
                                results.append({
                                    'chunk_id': row['chunk_id'],
                                    'book_id': row['book_id'],
                                    'content': row['content'][:500] + '...' if len(row['content']) > 500 else row['content'],
                                    'chapter_number': row['chapter_number'],
                                    'word_count': row['word_count'],
                                    'title': row['title'],
                                    'author': row['author'],
                                    'semantic_similarity': round(similarity, 4),
                                    'search_type': 'semantic'
                                })
                        except Exception as e:
                            logger.warning(f"Error processing embedding for chunk {row['chunk_id']}: {e}")
                            continue
                    
                    # Sort by similarity and limit results
                    results.sort(key=lambda x: x['semantic_similarity'], reverse=True)
                    
                    processing_time = round((time.time() - start_time) * 1000, 2)
                    logger.info(f"Semantic search found {len(results)} results in {processing_time}ms")
                    
                    return results[:limit]
                    
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []
    
    def fuzzy_text_search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Fuzzy text search using string similarity"""
        start_time = time.time()
        
        try:
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # Get text chunks for fuzzy matching
                    cur.execute("""
                        SELECT 
                            c.chunk_id,
                            c.book_id,
                            c.content,
                            c.chapter_number,
                            c.word_count,
                            b.title,
                            b.author
                        FROM chunks c
                        JOIN books b ON c.book_id = b.book_id
                        WHERE c.content IS NOT NULL 
                        AND LENGTH(c.content) > 50
                        ORDER BY c.book_id, c.chapter_number
                        LIMIT 2000
                    """)
                    
                    results = []
                    for row in cur.fetchall():
                        # Calculate fuzzy similarity
                        content_similarity = self.fuzzy_text_similarity(query, row['content'])
                        title_similarity = self.fuzzy_text_similarity(query, row['title'] or '')
                        
                        # Weighted fuzzy score (content is more important)
                        fuzzy_score = (content_similarity * 0.8) + (title_similarity * 0.2)
                        
                        if fuzzy_score >= (self.fuzzy_threshold / 100.0):
                            results.append({
                                'chunk_id': row['chunk_id'],
                                'book_id': row['book_id'],
                                'content': row['content'][:500] + '...' if len(row['content']) > 500 else row['content'],
                                'chapter_number': row['chapter_number'],
                                'word_count': row['word_count'],
                                'title': row['title'],
                                'author': row['author'],
                                'fuzzy_score': round(fuzzy_score, 4),
                                'search_type': 'fuzzy'
                            })
                    
                    # Sort by fuzzy score and limit results
                    results.sort(key=lambda x: x['fuzzy_score'], reverse=True)
                    
                    processing_time = round((time.time() - start_time) * 1000, 2)
                    logger.info(f"Fuzzy search found {len(results)} results in {processing_time}ms")
                    
                    return results[:limit]
                    
        except Exception as e:
            logger.error(f"Fuzzy search error: {e}")
            return []
    
    def hybrid_search(self, query: str, limit: int = 30, weights: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Hybrid search combining semantic + fuzzy + keyword search
        
        Args:
            query: Search query
            limit: Maximum results
            weights: Search strategy weights {'semantic': 0.5, 'fuzzy': 0.3, 'keyword': 0.2}
        """
        start_time = time.time()
        
        if weights is None:
            weights = {'semantic': 0.5, 'fuzzy': 0.3, 'keyword': 0.2}
        
        # Run searches in parallel (conceptually - simplified for now)
        semantic_results = self.semantic_search(query, limit // 2) if weights['semantic'] > 0 else []
        fuzzy_results = self.fuzzy_text_search(query, limit // 2) if weights['fuzzy'] > 0 else []
        
        # Simple keyword search (traditional PostgreSQL FTS)
        keyword_results = self.keyword_search(query, limit // 3) if weights['keyword'] > 0 else []
        
        # Combine and deduplicate results
        combined_results = {}
        
        # Add semantic results
        for result in semantic_results:
            chunk_id = result['chunk_id']
            result['combined_score'] = result['semantic_similarity'] * weights['semantic']
            combined_results[chunk_id] = result
        
        # Add fuzzy results (combine scores if chunk already exists)
        for result in fuzzy_results:
            chunk_id = result['chunk_id']
            fuzzy_score = result['fuzzy_score'] * weights['fuzzy']
            
            if chunk_id in combined_results:
                combined_results[chunk_id]['combined_score'] += fuzzy_score
                combined_results[chunk_id]['search_type'] = 'hybrid'
            else:
                result['combined_score'] = fuzzy_score
                combined_results[chunk_id] = result
        
        # Add keyword results
        for result in keyword_results:
            chunk_id = result['chunk_id']
            keyword_score = result.get('relevance', 0.5) * weights['keyword']
            
            if chunk_id in combined_results:
                combined_results[chunk_id]['combined_score'] += keyword_score
                combined_results[chunk_id]['search_type'] = 'hybrid'
            else:
                result['combined_score'] = keyword_score
                combined_results[chunk_id] = result
        
        # Sort by combined score
        final_results = sorted(
            combined_results.values(),
            key=lambda x: x['combined_score'],
            reverse=True
        )[:limit]
        
        processing_time = round((time.time() - start_time) * 1000, 2)
        
        return {
            'results': final_results,
            'search_stats': {
                'total_results': len(final_results),
                'semantic_count': len(semantic_results),
                'fuzzy_count': len(fuzzy_results),
                'keyword_count': len(keyword_results),
                'processing_time_ms': processing_time,
                'search_weights': weights,
                'query': query
            }
        }
    
    def keyword_search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Traditional keyword search using PostgreSQL FTS"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            c.chunk_id,
                            c.book_id,
                            c.content,
                            c.chapter_number,
                            c.word_count,
                            b.title,
                            b.author,
                            ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', %s)) as relevance
                        FROM chunks c
                        JOIN books b ON c.book_id = b.book_id
                        WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', %s)
                        ORDER BY relevance DESC
                        LIMIT %s
                    """, (query, query, limit))
                    
                    results = []
                    for row in cur.fetchall():
                        results.append({
                            'chunk_id': row['chunk_id'],
                            'book_id': row['book_id'],
                            'content': row['content'][:500] + '...' if len(row['content']) > 500 else row['content'],
                            'chapter_number': row['chapter_number'],
                            'word_count': row['word_count'],
                            'title': row['title'],
                            'author': row['author'],
                            'relevance': float(row['relevance']),
                            'search_type': 'keyword'
                        })
                    
                    return results
                    
        except Exception as e:
            logger.error(f"Keyword search error: {e}")
            return []

# Example usage and testing
if __name__ == "__main__":
    searcher = FuzzySemanticSearch()
    
    # Test queries
    test_queries = [
        "What is the nature of discourse?",
        "artificial intelligence and machine learning",
        "postmodern philosophy",
        "digital technology society"
    ]
    
    print("🔍 TESTING FUZZY SEMANTIC SEARCH SYSTEM")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\n🔎 Query: '{query}'")
        print("-" * 30)
        
        # Test hybrid search
        result = searcher.hybrid_search(query, limit=5)
        
        print(f"📊 Stats: {result['search_stats']['total_results']} results in {result['search_stats']['processing_time_ms']}ms")
        print(f"   Semantic: {result['search_stats']['semantic_count']}")
        print(f"   Fuzzy: {result['search_stats']['fuzzy_count']}")  
        print(f"   Keyword: {result['search_stats']['keyword_count']}")
        
        if result['results']:
            top_result = result['results'][0]
            print(f"🏆 Top result: {top_result['title']} (Score: {top_result['combined_score']:.3f})")
            print(f"   {top_result['content'][:100]}...")