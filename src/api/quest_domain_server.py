#!/usr/bin/env python3
"""
⚔️ Quest Domain Vector Search Server - Port 5572
Mystical mode vector search with adventure-driven knowledge discovery
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
import random

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from vector_embeddings import VectorEmbeddingGenerator
from enhanced_librarian_agent import EnhancedLibrarianAgent

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AI components
vector_generator = VectorEmbeddingGenerator()
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

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route('/api/quest/search', methods=['GET', 'POST'])
def quest_vector_search():
    """Quest Domain Vector Search - Mystical mode with adventure-driven discovery"""
    start_time = time.time()
    
    try:
        # Parse request
        if request.method == 'POST':
            data = request.get_json() or {}
            query = data.get('query', '')
            limit = data.get('limit', 10)
            mode = data.get('mode', 'mystical')
            seeker_mode = data.get('seekermode', None)
        else:
            query = request.args.get('q', '')
            limit = int(request.args.get('limit', 10))
            mode = request.args.get('mode', 'mystical')
            seeker_mode = request.args.get('seekermode', None)
        
        if not query:
            return jsonify({
                "error": "Query required",
                "quest_domain": "The quest requires a guiding question",
                "suggestion": "Provide a query to begin your knowledge adventure"
            }), 400
        
        # Special seeker mode handling
        if seeker_mode == "the_librarian_who_knows":
            # Enhanced search with librarian agent
            results = librarian_agent.semantic_search_with_analysis(query, limit)
            quest_enhancement = {
                "seeker_activated": True,
                "librarian_guidance": "The Librarian Who Knows guides your quest",
                "enhanced_analysis": True,
                "domain_power": "quest_enhanced_with_seeker"
            }
        else:
            # Standard quest domain search
            results = vector_generator.semantic_search(query, limit, similarity_threshold=0.2)
            quest_enhancement = {
                "seeker_activated": False,
                "domain_power": "quest_standard",
                "similarity_threshold": 0.2
            }
        
        # Quest domain enhancements
        quest_results = []
        adventure_themes = ["discovery", "mystery", "wisdom", "enlightenment", "journey"]
        
        for i, result in enumerate(results):
            quest_result = {
                "chunk_id": result.get('chunk_id'),
                "title": result['title'],
                "author": result['author'],
                "similarity_score": result.get('similarity_score', 0.0),
                "relevance_rank": result.get('similarity_score', 0.0),
                "content_preview": result.get('content_preview', ''),
                "quest_domain_metrics": {
                    "adventure_relevance": result.get('similarity_score', 0.0) * 1.1,
                    "knowledge_quest_level": i + 1,
                    "mystical_factor": random.uniform(0.6, 0.95),
                    "quest_theme": random.choice(adventure_themes)
                },
                "domain": "quest",
                "power_level": mode,
                "quest_position": f"Stage {i + 1} of {len(results)}"
            }
            quest_results.append(quest_result)
        
        response_time = time.time() - start_time
        
        response = {
            "query_metadata": {
                "query": query,
                "domain": "quest",
                "port": 5572,
                "mode": mode,
                "timestamp": datetime.utcnow().isoformat(),
                "response_time_ms": round(response_time * 1000, 2),
                "seeker_mode": seeker_mode
            },
            "results": quest_results,
            "quest_domain_status": {
                "total_results": len(quest_results),
                "adventure_power": "mystical",
                "knowledge_depth": "quest-driven",
                "search_mode": mode,
                **quest_enhancement
            },
            "domain_message": "⚔️ Quest Domain: Your adventure through knowledge begins",
            "available_modes": ["mystical", "precise", "enhanced", "adventure"],
            "quest_guidance": "Each result is a step in your knowledge journey"
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Quest domain search failed: {e}")
        return jsonify({
            "error": "Quest domain search failed",
            "quest_message": "The adventure encountered an obstacle",
            "details": str(e)
        }), 500

@app.route('/api/quest/health', methods=['GET'])
def quest_health():
    """Quest domain health check"""
    try:
        db = get_db()
        if not db:
            return jsonify({"status": "error", "message": "Database connection failed"}), 500
        
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM chunks WHERE embedding_array IS NOT NULL")
        embedded_count = cursor.fetchone()[0]
        
        return jsonify({
            "status": "quest_domain_operational",
            "domain": "quest",
            "port": 5572,
            "adventure_power": "mystical",
            "embedded_chunks": embedded_count,
            "available_modes": ["mystical", "precise", "enhanced", "adventure"],
            "special_seekers": ["the_librarian_who_knows"],
            "quest_message": "⚔️ Ready for your knowledge adventure"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "domain": "quest",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     ⚔️ QUEST DOMAIN VECTOR SEARCH ⚔️                        ║
║                       Port 5572 - Mystical Knowledge                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

⚔️ QUEST DOMAIN CAPABILITIES:
   • Mystical mode vector search with adventure themes
   • Knowledge quest discovery with guided exploration
   • The Librarian Who Knows seeker mode available
   • Adventure-driven similarity analysis
   • Mystical, precise, enhanced, and adventure modes

🌐 ENDPOINTS:
   • GET/POST /api/quest/search - Quest domain vector search
   • GET      /api/quest/health - Quest domain status

🎯 USAGE:
   curl "http://localhost:5572/api/quest/search?q=metaphysics&mode=mystical"
   curl "http://localhost:5572/api/quest/search?q=reality&seekermode=the_librarian_who_knows"

⚔️ Your adventure through knowledge begins!
    """)
    
    app.run(host='0.0.0.0', port=5574, debug=False)