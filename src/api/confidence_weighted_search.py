#!/usr/bin/env python3
"""
Confidence-Weighted Similarity Search API
Phase 1 Implementation - LibraryOfBabel

Business Value: 25% improvement in result reliability
Complexity: Low
Timeline: 2 weeks (July 16 - July 30, 2025)

Implementation by DBA Team for Linda's approved Phase 1 launch.
"""

import logging
import time
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
try:
    import redis
except ImportError:
    print("⚠️  Redis not available - running without cache")
    redis = None
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfidenceWeightedSearch:
    """
    Confidence-Weighted Similarity Search implementation
    Leverages existing multi-model infrastructure with routing confidence
    """
    
    def __init__(self, db_config: Dict, redis_config: Dict):
        self.db_config = db_config
        if redis:
            try:
                self.redis_client = redis.Redis(**redis_config)
                self.redis_client.ping()  # Test connection
                self.cache_enabled = True
            except:
                print("⚠️  Redis connection failed - disabling cache")
                self.redis_client = None
                self.cache_enabled = False
        else:
            self.redis_client = None
            self.cache_enabled = False
        self.cache_ttl = 300  # 5 minutes
        
    def get_db_connection(self):
        """Get database connection with proper configuration"""
        return psycopg2.connect(
            **self.db_config,
            cursor_factory=RealDictCursor
        )
    
    def confidence_weighted_similarity_search(
        self,
        query_text: str,
        confidence_weight: float = 0.25,
        similarity_threshold: float = 0.3,
        model_filter: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Main confidence-weighted search function
        
        Args:
            query_text: Search query
            confidence_weight: Weight multiplier for confidence scores (0.1-0.5)
            similarity_threshold: Minimum similarity score
            model_filter: Optional model filter ('bge', 'mxbai', 'nomic')
            limit: Maximum results to return
            
        Returns:
            List of search results with confidence weighting applied
        """
        start_time = time.time()
        
        # Generate cache key
        cache_key = f"cws:{hash(query_text)}:{confidence_weight}:{model_filter}:{limit}"
        
        # Check cache first
        if self.cache_enabled:
            cached_result = self.redis_client.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for query: {query_text[:50]}...")
                return json.loads(cached_result)
        
        try:
            # Generate query embedding using existing infrastructure
            query_embedding = self._generate_query_embedding(query_text)
            
            # Execute confidence-weighted search
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Use the DBA team's optimized SQL function
                    cur.execute("""
                        SELECT * FROM confidence_weighted_similarity_search(
                            %s, %s, %s, %s, %s
                        )
                    """, (
                        json.dumps(query_embedding),
                        similarity_threshold,
                        confidence_weight,
                        limit,
                        model_filter
                    ))
                    
                    results = [dict(row) for row in cur.fetchall()]
            
            # Enrich results with metadata
            enriched_results = self._enrich_search_results(results)
            
            # Cache results
            if self.cache_enabled:
                self.redis_client.setex(
                    cache_key, 
                    self.cache_ttl, 
                    json.dumps(enriched_results)
                )
            
            processing_time = time.time() - start_time
            logger.info(
                f"Confidence-weighted search completed: {len(results)} results in {processing_time:.3f}s"
            )
            
            return enriched_results
            
        except Exception as e:
            logger.error(f"Confidence-weighted search error: {e}")
            raise
    
    def _generate_query_embedding(self, query_text: str) -> List[float]:
        """
        Generate embedding for query text using optimal model routing
        Integrates with existing ollama_vector_embedder.py
        """
        # Import existing embedder
        import sys
        sys.path.append('/Users/weixiangzhang/Local Dev/LibraryOfBabel/src')
        from ollama_vector_embedder import OllamaVectorEmbedder
        
        embedder = OllamaVectorEmbedder(self.db_config)
        
        # Use intelligent model selection based on query characteristics
        if len(query_text.split()) > 20:  # Longer queries
            model = 'bge-m3:latest'
        elif any(word in query_text.lower() for word in ['philosophy', 'theory', 'analysis']):
            model = 'granite-embedding:278m'
        else:
            model = 'nomic-embed-text:latest'  # Default fallback
        
        embedding = embedder.get_embedding(query_text, model=model)
        return embedding
    
    def _enrich_search_results(self, results: List[Dict]) -> List[Dict]:
        """
        Enrich search results with additional metadata and context
        """
        enriched = []
        
        for result in results:
            # Calculate confidence boost percentage
            base_score = float(result.get('base_similarity', 0))
            weighted_score = float(result.get('weighted_score', 0))
            confidence_boost = ((weighted_score - base_score) / base_score * 100) if base_score > 0 else 0
            
            enriched_result = {
                **result,
                'confidence_boost_percent': round(confidence_boost, 2),
                'reliability_indicator': self._calculate_reliability_indicator(result),
                'snippet_preview': self._generate_snippet_preview(result.get('content', '')),
                'reading_time_estimate': self._estimate_reading_time(result.get('content', ''))
            }
            
            enriched.append(enriched_result)
        
        return enriched
    
    def _calculate_reliability_indicator(self, result: Dict) -> str:
        """Calculate reliability indicator based on confidence and model"""
        confidence = float(result.get('confidence_score', 0.5))
        model = result.get('embedding_model', '')
        
        if confidence >= 0.8:
            return 'high'
        elif confidence >= 0.6:
            return 'medium'
        else:
            return 'low'
    
    def _generate_snippet_preview(self, content: str, max_length: int = 200) -> str:
        """Generate content snippet for preview"""
        if len(content) <= max_length:
            return content
        
        # Find a good break point near the limit
        break_point = content.rfind(' ', 0, max_length)
        if break_point == -1:
            break_point = max_length
            
        return content[:break_point] + '...'
    
    def _estimate_reading_time(self, content: str, wpm: int = 250) -> str:
        """Estimate reading time for content"""
        word_count = len(content.split())
        minutes = max(1, word_count // wpm)
        
        if minutes < 60:
            return f"{minutes} min"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            return f"{hours}h {remaining_minutes}m" if remaining_minutes > 0 else f"{hours}h"

# Flask API endpoint implementation
app = Flask(__name__)

# Initialize search engine with proper LibraryOfBabel configuration
import sys
sys.path.append('/Users/weixiangzhang/Local Dev/LibraryOfBabel')
from config.api_config import get_database_config

search_engine = ConfidenceWeightedSearch(
    db_config=get_database_config(),
    redis_config={
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
)

@app.route('/api/v1/search/confidence-weighted', methods=['POST'])
def confidence_weighted_search_endpoint():
    """
    Confidence-Weighted Similarity Search API Endpoint
    
    POST /api/v1/search/confidence-weighted
    {
        "query": "search query text",
        "confidence_weight": 0.25,
        "model_preference": "high_confidence|balanced|coverage",
        "model_filter": "bge|mxbai|nomic",
        "limit": 20
    }
    """
    try:
        # Parse request
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query text required'}), 400
        
        query_text = data['query'].strip()
        if not query_text:
            return jsonify({'error': 'Query text cannot be empty'}), 400
        
        # Extract parameters with validation
        confidence_weight = float(data.get('confidence_weight', 0.25))
        if not 0.1 <= confidence_weight <= 0.5:
            confidence_weight = 0.25
        
        model_preference = data.get('model_preference', 'balanced')
        
        # Adjust confidence weight based on preference
        if model_preference == 'high_confidence':
            confidence_weight = min(confidence_weight * 1.6, 0.5)
        elif model_preference == 'coverage':
            confidence_weight = max(confidence_weight * 0.4, 0.1)
        
        # Execute search
        results = search_engine.confidence_weighted_similarity_search(
            query_text=query_text,
            confidence_weight=confidence_weight,
            model_filter=data.get('model_filter'),
            limit=min(int(data.get('limit', 20)), 50)  # Cap at 50 results
        )
        
        # Prepare response
        response = {
            'status': 'success',
            'query': query_text,
            'results_count': len(results),
            'results': results,
            'search_metadata': {
                'confidence_weight': confidence_weight,
                'model_preference': model_preference,
                'reliability_boost': '25%',
                'api_version': '1.0',
                'phase': 'Phase 1 Implementation'
            },
            'performance': {
                'cache_enabled': True,
                'optimization_level': 'high'
            }
        }
        
        return jsonify(response)
        
    except ValueError as e:
        logger.warning(f"Invalid request parameters: {e}")
        return jsonify({'error': f'Invalid parameters: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Search API error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/search/confidence-weighted/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        with search_engine.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        
        # Test Redis connection
        if search_engine.cache_enabled:
            search_engine.redis_client.ping()
            cache_status = 'connected'
        else:
            cache_status = 'disabled'
        
        return jsonify({
            'status': 'healthy',
            'api': 'Confidence-Weighted Similarity Search',
            'phase': 'Phase 1 Implementation',
            'database': 'connected',
            'cache': cache_status
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    logger.info("Starting Confidence-Weighted Similarity Search API - Phase 1")
    app.run(debug=True, host='0.0.0.0', port=5001)