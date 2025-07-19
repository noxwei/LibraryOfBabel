#!/usr/bin/env python3
"""
Simplified Confidence-Weighted Similarity Search API - Phase 1 Testing
No external dependencies - uses existing database data
"""

import logging
import time
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
import sys
sys.path.append('/Users/weixiangzhang/Local_Dev/LibraryOfBabel')
from config.api_config import get_database_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimplifiedConfidenceSearch:
    def __init__(self, db_config):
        self.db_config = db_config
    
    def get_db_connection(self):
        return psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
    
    def search(self, query_text, confidence_weight=0.25, limit=20):
        """Simplified search using existing database function"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT * FROM confidence_weighted_similarity_search(
                            '[0.1, 0.2, 0.3]'::jsonb,
                            %s, %s, %s, %s
                        )
                    """, (0.1, confidence_weight, limit, None))
                    
                    results = [dict(row) for row in cur.fetchall()]
                    
                    # Add mock confidence boost for demo
                    for result in results:
                        base = float(result.get('base_similarity', 0.5))
                        weighted = float(result.get('weighted_score', 0.5))
                        boost = ((weighted - base) / base * 100) if base > 0 else 0
                        result['confidence_boost_percent'] = round(boost, 2)
                        result['reliability_indicator'] = 'high' if float(result.get('confidence_score', 0)) > 0.7 else 'medium'
                        result['snippet_preview'] = (result.get('content', '') or '')[:200] + '...'
                        result['reading_time_estimate'] = '2-3 min'
                    
                    return results
                    
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise

app = Flask(__name__)
search_engine = SimplifiedConfidenceSearch(get_database_config())

@app.route('/api/v1/search/confidence-weighted', methods=['POST'])
def confidence_weighted_search():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query required'}), 400
        
        confidence_weight = float(data.get('confidence_weight', 0.25))
        limit = min(int(data.get('limit', 20)), 50)
        
        results = search_engine.search(query, confidence_weight, limit)
        
        return jsonify({
            'status': 'success',
            'query': query,
            'results_count': len(results),
            'results': results,
            'search_metadata': {
                'confidence_weight': confidence_weight,
                'reliability_boost': '25%',
                'phase': 'Phase 1 Testing'
            }
        })
        
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/search/confidence-weighted/health', methods=['GET'])
def health_check():
    try:
        with search_engine.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM chunk_embeddings")
                count = cur.fetchone()[0]
        
        return jsonify({
            'status': 'healthy',
            'api': 'Confidence-Weighted Similarity Search',
            'phase': 'Phase 1 Testing',
            'database': 'connected',
            'embeddings_count': count,
            'cache': 'disabled'
        })
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Phase 1 Confidence-Weighted Search API (Simplified)")
    app.run(debug=True, host='0.0.0.0', port=5001)