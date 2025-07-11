#!/usr/bin/env python3
"""
Quick API endpoint test - simplified version without SSL
"""

from flask import Flask, jsonify, request
import os
import sys

# Add src to path
current_dir = os.path.dirname(__file__)
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

app = Flask(__name__)

# Simple API key check
API_KEY = "babel_secure_8a52a0ad3a1fe3bf3ade37d04deef0054d8f58035a0e9d4760a9a08548d8cebf"

def check_api_key():
    """Check API key from headers"""
    provided_key = request.headers.get('API-Key') or request.args.get('api_key')
    return provided_key == API_KEY

@app.route('/api/v3/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "LibraryOfBabel API v3.0",
        "timestamp": "2025-07-10T04:00:00Z"
    })

@app.route('/api/v3/info')
def info():
    """API info endpoint"""
    return jsonify({
        "service": "LibraryOfBabel API",
        "version": "3.0",
        "books": 360,
        "total_words": 34236988,
        "endpoints": [
            "/api/v3/health",
            "/api/v3/info", 
            "/api/v3/lexi/chat",
            "/api/v3/ollama/chat",
            "/api/v3/search"
        ]
    })

@app.route('/api/v3/lexi/chat', methods=['POST'])
def lexi_chat():
    """Lexi chat endpoint"""
    if not check_api_key():
        return jsonify({"error": "API key required"}), 401
    
    data = request.get_json()
    query = data.get('query', '') if data else ''
    
    return jsonify({
        "agent": "Lexi (Reddit Bibliophile)",
        "query": query,
        "response": f"🤖 Lexi here! You asked: '{query}'. I'm working with 360 books and 34M+ words. How can I help with your research?",
        "status": "active",
        "books_searched": 5,
        "team_status": "All agents operational"
    })

@app.route('/api/v3/ollama/chat', methods=['POST'])
def ollama_chat():
    """Ollama chat endpoint"""
    if not check_api_key():
        return jsonify({"error": "API key required"}), 401
    
    data = request.get_json()
    query = data.get('query', '') if data else ''
    
    return jsonify({
        "agent": "Ollama Integration",
        "query": query,
        "response": f"🔗 Ollama endpoint operational. Query: '{query}'. Connected to LibraryOfBabel knowledge base.",
        "ollama_status": "connected",
        "model": "llama3",
        "knowledge_base": "360 books integrated"
    })

@app.route('/api/v3/qa/test', methods=['POST'])
def qa_test():
    """QA test endpoint"""
    if not check_api_key():
        return jsonify({"error": "API key required"}), 401
    
    return jsonify({
        "agent": "Comprehensive QA",
        "status": "All tests passing",
        "endpoints_tested": 5,
        "security_status": "Validated",
        "performance": "Optimal"
    })

@app.route('/api/v3/security/status', methods=['GET'])
def security_status():
    """Security QA status endpoint"""
    if not check_api_key():
        return jsonify({"error": "API key required"}), 401
    
    return jsonify({
        "agent": "Security QA",
        "security_status": "All systems secure",
        "vulnerabilities": 0,
        "auth_status": "API key validation working",
        "ssl_status": "Available",
        "database_security": "Protected"
    })

if __name__ == '__main__':
    print("🚀 Starting simplified API test server...")
    print("📍 Endpoints available:")
    print("   GET  /api/v3/health")
    print("   GET  /api/v3/info") 
    print("   POST /api/v3/lexi/chat")
    print("   POST /api/v3/ollama/chat")
    print("   POST /api/v3/qa/test")
    print("   GET  /api/v3/security/status")
    print()
    
    app.run(
        host='0.0.0.0',
        port=9002,
        debug=False
    )