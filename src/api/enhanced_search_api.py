#!/usr/bin/env python3
"""
🚀 Enhanced LibraryOfBabel Search API with Vector Embeddings
Comprehensive API integrating semantic search, serendipity engine, and AI insights
Port 5560 - Full AI-powered knowledge discovery system
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
import threading

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from vector_embeddings import VectorEmbeddingGenerator
from genre_classifier import GenreClassifier
from serendipity_engine import SerendipityEngine
from enhanced_librarian_agent import EnhancedLibrarianAgent

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AI components
vector_generator = VectorEmbeddingGenerator()
genre_classifier = GenreClassifier()
serendipity_engine = SerendipityEngine()
librarian_agent = EnhancedLibrarianAgent()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'knowledge_base'),
    'user': os.getenv('DB_USER', 'weixiangzhang'),
    'port': 5432
}

def get_db():
    """Get database connection with automatic cleanup"""
    if 'db' not in g:
        try:
            g.db = psycopg2.connect(**DB_CONFIG)
            g.db.autocommit = True
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            return None
    return g.db

def close_db_connection(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.teardown_appcontext
def close_db(error):
    close_db_connection()

def format_api_response(data: Any, success: bool = True, message: str = None, 
                       response_time: float = None) -> Dict:
    """Standard API response format"""
    response = {
        "success": success,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data
    }
    
    if message:
        response["message"] = message
    
    if response_time:
        response["response_time_ms"] = round(response_time * 1000, 2)
    
    return response

# ============================================================================
# VECTOR SEARCH ENDPOINTS
# ============================================================================

@app.route('/api/v2/search/semantic', methods=['GET', 'POST'])
def semantic_search():
    """Enhanced semantic search using vector embeddings"""
    start_time = time.time()
    
    try:
        if request.method == 'POST':
            data = request.get_json() or {}
            query = data.get('query', '')
            limit = data.get('limit', 10)
            similarity_threshold = data.get('similarity_threshold', 0.2)
            include_analysis = data.get('include_analysis', True)
        else:
            query = request.args.get('q', '')
            limit = int(request.args.get('limit', 10))
            similarity_threshold = float(request.args.get('threshold', 0.2))
            include_analysis = request.args.get('analysis', 'true').lower() == 'true'
        
        if not query:
            return jsonify(format_api_response(
                None, False, "Query parameter required"
            )), 400
        
        if include_analysis:
            # Use enhanced librarian agent for full analysis
            result = librarian_agent.semantic_search_with_analysis(query, limit)
        else:
            # Use basic vector search
            results = vector_generator.semantic_search(query, limit, similarity_threshold)
            result = {
                "query": query,
                "results": results,
                "metadata": {
                    "total_results": len(results),
                    "similarity_threshold": similarity_threshold
                }
            }
        
        response_time = time.time() - start_time
        return jsonify(format_api_response(result, True, None, response_time))
        
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        return jsonify(format_api_response(
            None, False, f"Search failed: {str(e)}"
        )), 500

@app.route('/api/v2/search/cross-reference', methods=['POST'])
def cross_reference_search():
    """Find philosophical connections between concepts"""
    start_time = time.time()
    
    try:
        data = request.get_json() or {}
        concept1 = data.get('concept1', '')
        concept2 = data.get('concept2', '')
        
        if not concept1 or not concept2:
            return jsonify(format_api_response(
                None, False, "Both concept1 and concept2 required"
            )), 400
        
        result = librarian_agent.find_philosophical_connections(concept1, concept2)
        
        response_time = time.time() - start_time
        return jsonify(format_api_response(result, True, None, response_time))
        
    except Exception as e:
        logger.error(f"Cross-reference search failed: {e}")
        return jsonify(format_api_response(
            None, False, f"Cross-reference search failed: {str(e)}"
        )), 500

# ============================================================================
# SERENDIPITY AND DISCOVERY ENDPOINTS
# ============================================================================

@app.route('/api/v2/discovery/serendipity', methods=['GET', 'POST'])
def serendipitous_insight():
    """Generate serendipitous insights from random chunks"""
    start_time = time.time()
    
    try:
        if request.method == 'POST':
            data = request.get_json() or {}
            seed_number = data.get('seed')
            num_chunks = data.get('chunks', 4)
            focus_theme = data.get('theme')
        else:
            seed_number = request.args.get('seed', type=int)
            num_chunks = int(request.args.get('chunks', 4))
            focus_theme = request.args.get('theme')
        
        # Validate parameters
        if seed_number and not (1 <= seed_number <= 999):
            return jsonify(format_api_response(
                None, False, "Seed must be between 1 and 999"
            )), 400
        
        if not (2 <= num_chunks <= 8):
            return jsonify(format_api_response(
                None, False, "Chunks must be between 2 and 8"
            )), 400
        
        insight = serendipity_engine.generate_serendipitous_insight(
            seed_number, num_chunks, focus_theme
        )
        
        response_time = time.time() - start_time
        return jsonify(format_api_response(insight, True, None, response_time))
        
    except Exception as e:
        logger.error(f"Serendipity generation failed: {e}")
        return jsonify(format_api_response(
            None, False, f"Serendipity generation failed: {str(e)}"
        )), 500

@app.route('/api/v2/discovery/insight-series', methods=['POST'])
def insight_series():
    """Generate a series of serendipitous insights"""
    start_time = time.time()
    
    try:
        data = request.get_json() or {}
        num_insights = data.get('count', 3)
        focus_theme = data.get('theme')
        
        if not (1 <= num_insights <= 10):
            return jsonify(format_api_response(
                None, False, "Count must be between 1 and 10"
            )), 400
        
        insights = serendipity_engine.generate_insight_series(num_insights, focus_theme)
        
        result = {
            "series_metadata": {
                "total_insights": len(insights),
                "focus_theme": focus_theme,
                "generation_method": "random_serendipity"
            },
            "insights": insights
        }
        
        response_time = time.time() - start_time
        return jsonify(format_api_response(result, True, None, response_time))
        
    except Exception as e:
        logger.error(f"Insight series generation failed: {e}")
        return jsonify(format_api_response(
            None, False, f"Insight series generation failed: {str(e)}"
        )), 500

@app.route('/api/v2/discovery/hidden-gems', methods=['GET'])
def hidden_gems():
    """Discover hidden connections in the library"""
    start_time = time.time()
    
    try:
        num_gems = int(request.args.get('count', 2))
        
        if not (1 <= num_gems <= 5):
            return jsonify(format_api_response(
                None, False, "Count must be between 1 and 5"
            )), 400
        
        gems = serendipity_engine.find_library_hidden_gems(num_gems)
        
        result = {
            "discovery_metadata": {
                "gems_found": len(gems),
                "discovery_method": "maximum_diversity_sampling"
            },
            "hidden_gems": gems
        }
        
        response_time = time.time() - start_time
        return jsonify(format_api_response(result, True, None, response_time))
        
    except Exception as e:
        logger.error(f"Hidden gems discovery failed: {e}")
        return jsonify(format_api_response(
            None, False, f"Hidden gems discovery failed: {str(e)}"
        )), 500

@app.route('/api/v2/discovery/explore-concept', methods=['POST'])
def explore_concept():
    """Explore conceptual space around an anchor concept"""
    start_time = time.time()
    
    try:
        data = request.get_json() or {}
        anchor_concept = data.get('concept', '')
        exploration_depth = data.get('depth', 3)
        
        if not anchor_concept:
            return jsonify(format_api_response(
                None, False, "Concept parameter required"
            )), 400
        
        if not (1 <= exploration_depth <= 6):
            return jsonify(format_api_response(
                None, False, "Depth must be between 1 and 6"
            )), 400
        
        exploration = serendipity_engine.explore_conceptual_space(
            anchor_concept, exploration_depth
        )
        
        response_time = time.time() - start_time
        return jsonify(format_api_response(exploration, True, None, response_time))
        
    except Exception as e:
        logger.error(f"Concept exploration failed: {e}")
        return jsonify(format_api_response(
            None, False, f"Concept exploration failed: {str(e)}"
        )), 500

# ============================================================================
# AI ANALYSIS ENDPOINTS
# ============================================================================

@app.route('/api/v2/analysis/author', methods=['GET'])
def analyze_author():
    """Analyze author relationships and themes"""
    start_time = time.time()
    
    try:
        author_name = request.args.get('name', '')
        
        if not author_name:
            return jsonify(format_api_response(
                None, False, "Author name parameter required"
            )), 400
        
        analysis = librarian_agent.analyze_author_relationships(author_name)
        
        response_time = time.time() - start_time
        return jsonify(format_api_response(analysis, True, None, response_time))
        
    except Exception as e:
        logger.error(f"Author analysis failed: {e}")
        return jsonify(format_api_response(
            None, False, f"Author analysis failed: {str(e)}"
        )), 500

@app.route('/api/v2/recommendations/reading-path', methods=['POST'])
def reading_path():
    """Generate personalized reading recommendations"""
    start_time = time.time()
    
    try:
        data = request.get_json() or {}
        starting_interest = data.get('interest', '')
        depth_level = data.get('depth', 'medium')
        
        if not starting_interest:
            return jsonify(format_api_response(
                None, False, "Starting interest required"
            )), 400
        
        if depth_level not in ['light', 'medium', 'deep']:
            return jsonify(format_api_response(
                None, False, "Depth must be 'light', 'medium', or 'deep'"
            )), 400
        
        recommendations = librarian_agent.recommend_reading_path(
            starting_interest, depth_level
        )
        
        response_time = time.time() - start_time
        return jsonify(format_api_response(recommendations, True, None, response_time))
        
    except Exception as e:
        logger.error(f"Reading path generation failed: {e}")
        return jsonify(format_api_response(
            None, False, f"Reading path generation failed: {str(e)}"
        )), 500

@app.route('/api/v2/classification/genre', methods=['GET', 'POST'])
def genre_classification():
    """AI-powered genre classification"""
    start_time = time.time()
    
    try:
        if request.method == 'POST':
            data = request.get_json() or {}
            book_id = data.get('book_id')
            reclassify_all = data.get('reclassify_all', False)
            min_confidence = data.get('min_confidence', 0.3)
        else:
            book_id = request.args.get('book_id', type=int)
            reclassify_all = request.args.get('reclassify_all', 'false').lower() == 'true'
            min_confidence = float(request.args.get('min_confidence', 0.3))
        
        if reclassify_all:
            # Reclassify all books
            results = genre_classifier.classify_all_books(min_confidence)
        elif book_id:
            # Classify specific book
            genre, confidence = genre_classifier.classify_book_genre(book_id)
            if confidence >= min_confidence:
                genre_classifier.update_book_genre(book_id, genre, confidence)
                results = {
                    "book_id": book_id,
                    "predicted_genre": genre,
                    "confidence": confidence,
                    "updated": True
                }
            else:
                results = {
                    "book_id": book_id,
                    "predicted_genre": genre,
                    "confidence": confidence,
                    "updated": False,
                    "reason": f"Confidence {confidence:.3f} below threshold {min_confidence}"
                }
        else:
            # Get classification statistics
            results = genre_classifier.get_genre_stats()
        
        response_time = time.time() - start_time
        return jsonify(format_api_response(results, True, None, response_time))
        
    except Exception as e:
        logger.error(f"Genre classification failed: {e}")
        return jsonify(format_api_response(
            None, False, f"Genre classification failed: {str(e)}"
        )), 500

# ============================================================================
# SYSTEM STATUS AND METADATA ENDPOINTS
# ============================================================================

@app.route('/api/v2/system/health', methods=['GET'])
def enhanced_health_check():
    """Comprehensive system health check"""
    start_time = time.time()
    
    try:
        db = get_db()
        if not db:
            return jsonify(format_api_response(
                None, False, "Database connection failed"
            )), 500
        
        cursor = db.cursor()
        
        # Get comprehensive statistics
        stats = {}
        
        # Book statistics
        cursor.execute("SELECT COUNT(*) FROM books")
        stats["total_books"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM books WHERE genre IS NOT NULL")
        stats["classified_books"] = cursor.fetchone()[0]
        
        # Chunk statistics
        cursor.execute("SELECT COUNT(*) FROM chunks")
        stats["total_chunks"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM chunks WHERE embedding_array IS NOT NULL")
        stats["embedded_chunks"] = cursor.fetchone()[0]
        
        # Calculate completion rates
        stats["embedding_completion_rate"] = round(
            (stats["embedded_chunks"] / max(stats["total_chunks"], 1)) * 100, 2
        )
        stats["classification_completion_rate"] = round(
            (stats["classified_books"] / max(stats["total_books"], 1)) * 100, 2
        )
        
        # System capabilities
        capabilities = {
            "semantic_search": stats["embedded_chunks"] > 0,
            "genre_classification": stats["classified_books"] > 0,
            "serendipity_discovery": stats["embedded_chunks"] > 10,
            "cross_reference_search": stats["embedded_chunks"] > 0,
            "author_analysis": stats["total_books"] > 0,
            "reading_recommendations": stats["embedded_chunks"] > 0
        }
        
        response_time = time.time() - start_time
        
        health_data = {
            "status": "healthy",
            "database": "connected",
            "statistics": stats,
            "capabilities": capabilities,
            "api_version": "2.0",
            "features": [
                "vector_embeddings",
                "semantic_search", 
                "serendipity_engine",
                "ai_genre_classification",
                "philosophical_connections",
                "reading_recommendations"
            ]
        }
        
        return jsonify(format_api_response(health_data, True, None, response_time))
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify(format_api_response(
            None, False, f"Health check failed: {str(e)}"
        )), 500

@app.route('/api/v2/system/stats', methods=['GET'])
def enhanced_stats():
    """Enhanced system statistics with AI insights"""
    start_time = time.time()
    
    try:
        # Get library stats from librarian agent
        library_stats = librarian_agent.get_library_stats()
        
        # Get genre classification stats
        genre_stats = genre_classifier.get_genre_stats()
        
        # Get embedding stats
        embedding_stats = vector_generator.get_embedding_stats()
        
        combined_stats = {
            "library_overview": library_stats,
            "genre_classification": genre_stats,
            "vector_embeddings": embedding_stats,
            "ai_capabilities": {
                "models_available": ["nomic-embed-text", "llama3.1:8b"],
                "serendipity_seeds": 999,
                "max_insight_chunks": 8,
                "similarity_threshold_range": [0.1, 1.0]
            }
        }
        
        response_time = time.time() - start_time
        return jsonify(format_api_response(combined_stats, True, None, response_time))
        
    except Exception as e:
        logger.error(f"Enhanced stats failed: {e}")
        return jsonify(format_api_response(
            None, False, f"Enhanced stats failed: {str(e)}"
        )), 500

# ============================================================================
# API DOCUMENTATION ENDPOINT
# ============================================================================

@app.route('/api/v2/docs', methods=['GET'])
def api_documentation():
    """API documentation and endpoint reference"""
    docs = {
        "api_version": "2.0",
        "description": "LibraryOfBabel Enhanced Search API with Vector Embeddings and AI Insights",
        "base_url": "http://localhost:5560",
        "endpoints": {
            "search": {
                "semantic_search": {
                    "path": "/api/v2/search/semantic",
                    "methods": ["GET", "POST"],
                    "description": "Semantic search using vector embeddings",
                    "parameters": {
                        "query": "Search query (required)",
                        "limit": "Number of results (1-50, default: 10)",
                        "threshold": "Similarity threshold (0.1-1.0, default: 0.2)",
                        "analysis": "Include AI analysis (true/false, default: true)"
                    }
                },
                "cross_reference": {
                    "path": "/api/v2/search/cross-reference",
                    "methods": ["POST"],
                    "description": "Find philosophical connections between concepts",
                    "parameters": {
                        "concept1": "First concept (required)",
                        "concept2": "Second concept (required)"
                    }
                }
            },
            "discovery": {
                "serendipity": {
                    "path": "/api/v2/discovery/serendipity",
                    "methods": ["GET", "POST"],
                    "description": "Generate serendipitous insights from random chunks",
                    "parameters": {
                        "seed": "Random seed 1-999 (optional)",
                        "chunks": "Number of chunks 2-8 (default: 4)",
                        "theme": "Focus theme (optional)"
                    }
                },
                "insight_series": {
                    "path": "/api/v2/discovery/insight-series",
                    "methods": ["POST"],
                    "description": "Generate series of insights",
                    "parameters": {
                        "count": "Number of insights 1-10 (default: 3)",
                        "theme": "Focus theme (optional)"
                    }
                },
                "hidden_gems": {
                    "path": "/api/v2/discovery/hidden-gems",
                    "methods": ["GET"],
                    "description": "Discover hidden connections",
                    "parameters": {
                        "count": "Number of gems 1-5 (default: 2)"
                    }
                },
                "explore_concept": {
                    "path": "/api/v2/discovery/explore-concept",
                    "methods": ["POST"],
                    "description": "Explore conceptual space around anchor concept",
                    "parameters": {
                        "concept": "Anchor concept (required)",
                        "depth": "Exploration depth 1-6 (default: 3)"
                    }
                }
            },
            "analysis": {
                "author": {
                    "path": "/api/v2/analysis/author",
                    "methods": ["GET"],
                    "description": "Analyze author relationships and themes",
                    "parameters": {
                        "name": "Author name (required)"
                    }
                },
                "reading_path": {
                    "path": "/api/v2/recommendations/reading-path",
                    "methods": ["POST"],
                    "description": "Generate personalized reading recommendations",
                    "parameters": {
                        "interest": "Starting interest (required)",
                        "depth": "Difficulty level: light/medium/deep (default: medium)"
                    }
                },
                "genre_classification": {
                    "path": "/api/v2/classification/genre",
                    "methods": ["GET", "POST"],
                    "description": "AI-powered genre classification",
                    "parameters": {
                        "book_id": "Specific book ID (optional)",
                        "reclassify_all": "Reclassify all books (true/false)",
                        "min_confidence": "Minimum confidence 0.1-1.0 (default: 0.3)"
                    }
                }
            },
            "system": {
                "health": {
                    "path": "/api/v2/system/health",
                    "methods": ["GET"],
                    "description": "Comprehensive system health check"
                },
                "stats": {
                    "path": "/api/v2/system/stats",
                    "methods": ["GET"],
                    "description": "Enhanced system statistics with AI insights"
                }
            }
        },
        "example_requests": {
            "semantic_search": "GET /api/v2/search/semantic?q=consciousness&limit=5",
            "serendipity": "POST /api/v2/discovery/serendipity {\"seed\": 42, \"theme\": \"freedom\"}",
            "author_analysis": "GET /api/v2/analysis/author?name=Foucault",
            "reading_path": "POST /api/v2/recommendations/reading-path {\"interest\": \"philosophy\", \"depth\": \"medium\"}"
        }
    }
    
    return jsonify(format_api_response(docs, True, "API Documentation"))

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify(format_api_response(
        None, False, "Endpoint not found. See /api/v2/docs for available endpoints"
    )), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify(format_api_response(
        None, False, "Internal server error"
    )), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify(format_api_response(
        None, False, "Bad request - check your parameters"
    )), 400

# ============================================================================
# MAIN APPLICATION
# ============================================================================

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                  🚀 LibraryOfBabel Enhanced Search API v2.0                  ║
║                    Vector Embeddings + AI-Powered Discovery                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

🔥 **ENHANCED CAPABILITIES:**
   • Semantic Search with Vector Embeddings (1,286 chunks ready)
   • Serendipitous Insight Discovery (999 unique seeds)
   • AI-Powered Genre Classification (35 books classified)
   • Philosophical Cross-Reference Search
   • Reading Path Recommendations
   • Hidden Gems Discovery

🌐 **API ENDPOINTS:**
   • GET  /api/v2/docs - Complete API documentation
   • GET  /api/v2/system/health - System health & capabilities
   • GET  /api/v2/search/semantic?q=query - Semantic search
   • POST /api/v2/discovery/serendipity - Random insight generation
   • GET  /api/v2/analysis/author?name=author - Author analysis
   • POST /api/v2/recommendations/reading-path - Reading recommendations

🎯 **EXAMPLE REQUESTS:**
   curl "http://localhost:5560/api/v2/search/semantic?q=consciousness&limit=5"
   curl -X POST http://localhost:5560/api/v2/discovery/serendipity -d '{"seed":42,"theme":"freedom"}'
   curl "http://localhost:5560/api/v2/analysis/author?name=Foucault"

🤖 Ready for AI-powered knowledge discovery!
    """)
    
    app.run(host='0.0.0.0', port=5560, debug=False)