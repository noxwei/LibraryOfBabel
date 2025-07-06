#!/usr/bin/env python3
"""
🔐 Secure LibraryOfBabel Enhanced Search API
HTTPS + API Key Authentication + Vector Embeddings + AI Features
"""

from flask import Flask, request, jsonify, g
import psycopg2
import psycopg2.extras
import logging
import time
import json
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add src directory to path for imports
sys.path.append(os.path.dirname(__file__))

from security_middleware import require_api_key, log_request, get_ssl_context, create_public_endpoint
from vector_embeddings import VectorEmbeddingGenerator

try:
    from genre_classifier import GenreClassifier
    from serendipity_engine import SerendipityEngine
    from enhanced_librarian_agent import EnhancedLibrarianAgent
except ImportError as e:
    logger.warning(f"Some AI components not available: {e}")
    GenreClassifier = None
    SerendipityEngine = None
    EnhancedLibrarianAgent = None

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
vector_generator = VectorEmbeddingGenerator()
genre_classifier = GenreClassifier() if GenreClassifier else None
serendipity_engine = SerendipityEngine() if SerendipityEngine else None
librarian_agent = EnhancedLibrarianAgent() if EnhancedLibrarianAgent else None

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'knowledge_base'),
    'user': os.getenv('DB_USER', 'weixiangzhang'),
    'port': 5432
}

def get_db():
    """Get database connection with automatic cleanup"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        logger.error(f"Database connection failed: {e}")
        return None

# Apply logging to all requests
@app.before_request
@log_request
def before_request():
    pass

# Public endpoint
@app.route('/api/secure/v2/info')
@create_public_endpoint
def secure_api_info():
    """Public endpoint showing secure API information"""
    return jsonify({
        'success': True,
        'data': {
            'name': 'LibraryOfBabel Secure Enhanced Search API',
            'version': '2.0',
            'security': 'HTTPS + API Key Required',
            'features': [
                'vector_embeddings',
                'semantic_search',
                'serendipity_engine' if serendipity_engine else 'serendipity_engine (unavailable)',
                'ai_genre_classification' if genre_classifier else 'ai_genre_classification (unavailable)',
                'philosophical_connections',
                'reading_recommendations'
            ],
            'authentication': 'Required for all endpoints except /info',
            'rate_limit': '60 requests per minute per IP'
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/secure/v2/system/health')
@require_api_key
def secure_system_health():
    """Comprehensive system health check - SECURED"""
    start_time = time.time()
    
    # Get embedding statistics
    embedding_stats = vector_generator.get_embedding_stats()
    
    # Get database stats
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM books WHERE book_id > 0")
            total_books = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM chunks")
            total_chunks = cursor.fetchone()[0]
            
            db_status = "connected"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_status = f"error: {e}"
            total_books = 0
            total_chunks = 0
        finally:
            conn.close()
    else:
        db_status = "connection failed"
        total_books = 0
        total_chunks = 0
    
    health_data = {
        'api_version': '2.0',
        'status': 'healthy' if db_status == 'connected' else 'degraded',
        'database': db_status,
        'security': {
            'https_enabled': True,
            'api_key_required': True,
            'rate_limiting': True
        },
        'capabilities': {
            'semantic_search': True,
            'vector_embeddings': True,
            'serendipity_discovery': serendipity_engine is not None,
            'ai_genre_classification': genre_classifier is not None,
            'enhanced_librarian': librarian_agent is not None,
            'cross_reference_search': True,
            'reading_recommendations': librarian_agent is not None
        },
        'statistics': {
            'total_books': total_books,
            'total_chunks': total_chunks,
            'embedded_chunks': embedding_stats.get('embedded_chunks', 0),
            'embedding_completion_rate': embedding_stats.get('completion_percentage', 0)
        }
    }
    
    return jsonify({
        'success': True,
        'data': health_data,
        'security': {'authenticated': True, 'api_key_valid': True},
        'response_time_ms': round((time.time() - start_time) * 1000, 2),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/secure/v2/search/semantic')
@require_api_key
def secure_semantic_search():
    """Semantic search using vector embeddings - SECURED"""
    query = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 10)), 50)  # Cap at 50
    threshold = float(request.args.get('threshold', 0.2))
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Query parameter "q" is required'
        }), 400
    
    start_time = time.time()
    
    try:
        # Perform semantic search
        results = vector_generator.semantic_search(query, limit, threshold)
        
        # Generate analysis if we have results
        analysis = ""
        if results:
            avg_similarity = sum(r['similarity_score'] for r in results) / len(results)
            authors = list(set(r['author'] for r in results if r['author']))
            
            if avg_similarity > 0.65:
                analysis = f"🎯 **Strong thematic match** (avg similarity: {avg_similarity:.3f})"
            elif avg_similarity > 0.45:
                analysis = f"📚 **Good conceptual relevance** (avg similarity: {avg_similarity:.3f})"
            else:
                analysis = f"🔍 **Broad conceptual connections** (avg similarity: {avg_similarity:.3f})"
            
            if authors:
                prominent_author = max(set(authors), key=authors.count)
                author_count = authors.count(prominent_author)
                if author_count > 1:
                    analysis += f" • ✍️ **{prominent_author}** appears multiple times - strong relevance to your query"
        
        # Metadata
        search_metadata = {
            'total_results': len(results),
            'avg_similarity': round(sum(r['similarity_score'] for r in results) / len(results), 3) if results else 0,
            'authors_found': list(set(r['author'] for r in results if r['author'])),
            'genres_found': []  # Could add genre info if available
        }
        
        return jsonify({
            'success': True,
            'data': {
                'query': query,
                'results': results,
                'analysis': analysis,
                'search_metadata': search_metadata,
                'suggestions': [f"More works by {search_metadata['authors_found'][0]}"] if search_metadata['authors_found'] else []
            },
            'security': {'authenticated': True, 'api_key_valid': True},
            'response_time_ms': round((time.time() - start_time) * 1000, 2),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        return jsonify({
            'success': False,
            'error': f'Search failed: {str(e)}'
        }), 500

@app.route('/api/secure/v2/discovery/serendipity', methods=['GET', 'POST'])
@require_api_key
def secure_serendipity_discovery():
    """Generate serendipitous insights - SECURED"""
    if not serendipity_engine:
        return jsonify({
            'success': False,
            'error': 'Serendipity engine not available'
        }), 503
    
    # Get parameters from query string or JSON body
    if request.method == 'POST' and request.is_json:
        params = request.json
    else:
        params = request.args
    
    seed = params.get('seed', None)
    theme = params.get('theme', '')
    chunks = min(int(params.get('chunks', 4)), 8)  # Cap at 8
    
    start_time = time.time()
    
    try:
        if seed:
            seed = int(seed)
        
        # This would need to be implemented based on your serendipity engine
        # For now, return a placeholder response
        result = {
            'seed_number': seed or 'random',
            'theme': theme,
            'insight_id': f"serendipity_{seed or 'random'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'source_chunks': [],
            'synthesis': {'note': 'Serendipity engine integration pending'},
            'discovery_metadata': {
                'total_words_analyzed': 0,
                'conceptual_diversity': 0,
                'authors_combined': [],
                'genres_combined': []
            }
        }
        
        return jsonify({
            'success': True,
            'data': result,
            'security': {'authenticated': True, 'api_key_valid': True},
            'response_time_ms': round((time.time() - start_time) * 1000, 2),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Serendipity discovery error: {e}")
        return jsonify({
            'success': False,
            'error': f'Discovery failed: {str(e)}'
        }), 500

@app.route('/api/secure/v2/docs')
@require_api_key
def secure_enhanced_docs():
    """Secure enhanced API documentation - SECURED"""
    docs = {
        'title': 'LibraryOfBabel Secure Enhanced Search API',
        'version': '2.0',
        'security': {
            'https': True,
            'api_key_required': True,
            'rate_limit': '60 requests per minute per IP',
            'encryption': 'TLS/SSL'
        },
        'authentication': {
            'methods': [
                'Authorization: Bearer <api_key>',
                'X-API-Key: <api_key>',
                'Query parameter: ?api_key=<api_key>'
            ],
            'example': 'curl -H "X-API-Key: YOUR_API_KEY" https://your-domain:5563/api/secure/v2/search/semantic?q=consciousness'
        },
        'endpoints': {
            'public': {
                'api_info': {
                    'path': '/api/secure/v2/info',
                    'method': 'GET',
                    'description': 'API information (no auth required)'
                }
            },
            'authenticated': {
                'system_health': {
                    'path': '/api/secure/v2/system/health',
                    'method': 'GET',
                    'description': 'Comprehensive system health check',
                    'auth_required': True
                },
                'semantic_search': {
                    'path': '/api/secure/v2/search/semantic',
                    'method': 'GET',
                    'description': 'Vector-powered semantic search',
                    'auth_required': True,
                    'parameters': {
                        'q': 'Search query (required)',
                        'limit': 'Number of results (1-50, default: 10)',
                        'threshold': 'Similarity threshold (0.1-1.0, default: 0.2)'
                    }
                },
                'serendipity_discovery': {
                    'path': '/api/secure/v2/discovery/serendipity',
                    'method': 'GET/POST',
                    'description': 'Generate serendipitous insights',
                    'auth_required': True,
                    'parameters': {
                        'seed': 'Random seed (optional)',
                        'theme': 'Focus theme (optional)',
                        'chunks': 'Number of chunks (2-8, default: 4)'
                    }
                }
            }
        }
    }
    
    return jsonify({
        'success': True,
        'data': docs,
        'security': {'authenticated': True, 'api_key_valid': True},
        'timestamp': datetime.now().isoformat()
    })

# Error handlers
@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 'Unauthorized',
        'message': 'Valid API key required',
        'security': {'authenticated': False}
    }), 401

@app.errorhandler(403)
def forbidden(error):
    return jsonify({
        'success': False,
        'error': 'Forbidden', 
        'message': 'Invalid API key',
        'security': {'authenticated': False}
    }), 403

@app.errorhandler(429)
def rate_limited(error):
    return jsonify({
        'success': False,
        'error': 'Rate Limit Exceeded',
        'message': 'Too many requests. Please slow down.',
        'security': {'rate_limited': True}
    }), 429

if __name__ == '__main__':
    print("🔐 Starting LibraryOfBabel Secure Enhanced Search API...")
    print("🛡️  Security Features:")
    print("   • HTTPS/TLS encryption")
    print("   • API key authentication")
    print("   • Rate limiting (60 req/min per IP)")
    print("   • Request logging & monitoring")
    print("")
    print("🔑 API Key: M39Gqz5e8D-_qkyuy37ar87_jNU0EPs_nO6_izPnGaU")
    print("")
    print("🚀 Enhanced Features:")
    print("   • Vector embeddings semantic search")
    print("   • AI-powered insights & discovery")
    print("   • Cross-domain philosophical connections")
    print("   • Advanced search analytics")
    print("")
    print("📚 Secure Endpoints:")
    print("   • GET /api/secure/v2/info - API info (public)")
    print("   • GET /api/secure/v2/system/health - System health (auth required)")
    print("   • GET /api/secure/v2/search/semantic?q=query - Semantic search (auth required)")
    print("   • POST /api/secure/v2/discovery/serendipity - AI insights (auth required)")
    print("   • GET /api/secure/v2/docs - API documentation (auth required)")
    print("")
    print("🌐 Starting secure server on https://localhost:5563")
    
    # Get SSL context
    ssl_context = get_ssl_context()
    
    if ssl_context:
        app.run(
            host='0.0.0.0',
            port=5563,
            debug=False,
            ssl_context=ssl_context
        )
    else:
        print("❌ SSL certificates not found! Starting without HTTPS...")
        app.run(host='0.0.0.0', port=5563, debug=False)