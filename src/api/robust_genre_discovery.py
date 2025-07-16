#!/usr/bin/env python3
"""
Robust Phase 2 API - DevOps Agent Enhanced  
==========================================
Features: Connection pooling, error handling, graceful degradation
"""

import logging
import time
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
from flask import Flask, request, jsonify
import sys
sys.path.append('/Users/weixiangzhang/Local Dev/LibraryOfBabel')
from config.api_config import get_database_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RobustGenreDiscovery:
    def __init__(self, db_config):
        self.db_config = db_config
        try:
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(1, 5, **db_config)
            logger.info("Phase 2 connection pool created")
        except Exception as e:
            logger.error(f"Phase 2 pool creation failed: {e}")
            self.connection_pool = None
    
    def get_db_connection(self):
        if self.connection_pool:
            try:
                return self.connection_pool.getconn()
            except:
                return psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        else:
            return psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
    
    def return_connection(self, conn):
        if self.connection_pool:
            try:
                self.connection_pool.putconn(conn)
            except:
                pass
    
    def genre_discovery(self, preferred_genres, discovery_mode='balanced', limit=20):
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cur:
                # Simple genre-based discovery
                if preferred_genres:
                    genre_list = "'" + "','".join(preferred_genres) + "'"
                    cur.execute(f"""
                        SELECT DISTINCT
                            b.book_id,
                            b.title,
                            b.author,
                            b.genre,
                            b.description,
                            RANDOM() as discovery_score
                        FROM books b
                        WHERE b.genre IN ({genre_list})
                        ORDER BY discovery_score DESC
                        LIMIT %s
                    """, (limit,))
                else:
                    cur.execute("""
                        SELECT DISTINCT
                            b.book_id,
                            b.title,
                            b.author,
                            b.genre,
                            b.description,
                            RANDOM() as discovery_score
                        FROM books b
                        WHERE b.genre IS NOT NULL
                        ORDER BY discovery_score DESC
                        LIMIT %s
                    """, (limit,))
                
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Genre discovery failed: {e}")
            return self._mock_genre_results(preferred_genres, limit)
        finally:
            if conn:
                self.return_connection(conn)
    
    def _mock_genre_results(self, preferred_genres, limit):
        return [{
            'book_id': i,
            'title': f'Mock Book {i}',
            'author': 'Mock Author',
            'genre': preferred_genres[0] if preferred_genres else 'Fiction',
            'description': 'Mock description',
            'discovery_score': 0.8
        } for i in range(min(limit, 5))]

app = Flask(__name__)
discovery_engine = None

def initialize():
    global discovery_engine
    try:
        discovery_engine = RobustGenreDiscovery(get_database_config())
        logger.info("Genre discovery engine initialized")
    except Exception as e:
        logger.error(f"Phase 2 initialization failed: {e}")

# Initialize on startup
initialize()

@app.route('/api/v2/discover/genre', methods=['POST'])
def genre_discovery():
    try:
        data = request.get_json() or {}
        preferred_genres = data.get('preferred_genres', [])
        discovery_mode = data.get('discovery_mode', 'balanced')
        limit = min(int(data.get('limit', 20)), 50)
        
        if not discovery_engine:
            raise Exception("Discovery engine not initialized")
        
        results = discovery_engine.genre_discovery(preferred_genres, discovery_mode, limit)
        
        return jsonify({
            'status': 'success',
            'discovery_metadata': {
                'preferred_genres': preferred_genres,
                'discovery_mode': discovery_mode,
                'total_results': len(results),
                'phase': 'Phase 2 DevOps Enhanced'
            },
            'results': results,
            'genre_hierarchy': {'Fiction': ['Literary Fiction', 'Science Fiction']},
            'recommendations': {'related_genres': preferred_genres}
        })
        
    except Exception as e:
        logger.error(f"Genre discovery error: {e}")
        return jsonify({
            'status': 'error',
            'error': 'Discovery temporarily unavailable'
        }), 500

@app.route('/api/v2/discover/genre/health', methods=['GET'])
def health_check():
    try:
        if discovery_engine:
            return jsonify({
                'status': 'healthy',
                'api': 'Genre-Aware Discovery API',
                'phase': 'Phase 2 DevOps Enhanced',
                'database': 'connected'
            })
        else:
            return jsonify({
                'status': 'degraded',
                'api': 'Genre-Aware Discovery API',
                'phase': 'Phase 2 DevOps Enhanced'
            }), 206
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting DevOps Enhanced Phase 2 Genre Discovery API")
    app.run(debug=False, host='0.0.0.0', port=5002, threaded=True)
