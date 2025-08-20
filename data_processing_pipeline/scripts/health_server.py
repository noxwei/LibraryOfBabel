#!/usr/bin/env python3
"""
Health Check Server for BabelProcessorDb Pipeline
================================================

Simple Flask server for monitoring pipeline health and status.
Provides endpoints for Docker health checks and monitoring.
"""

import os
import sys
import json
import logging
from flask import Flask, jsonify
from datetime import datetime

# Add src to Python path
sys.path.insert(0, '/app/src')

from database_manager import DatabaseManager
from embedding_generator import EmbeddingGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Global components
db_manager = None
embedding_generator = None

def init_components():
    """Initialize components"""
    global db_manager, embedding_generator
    try:
        db_manager = DatabaseManager()
        embedding_generator = EmbeddingGenerator(max_workers=1)
        logger.info("Health server components initialized")
    except Exception as e:
        logger.error(f"Error initializing components: {e}")

@app.route('/health')
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'babel-processor-test'
    })

@app.route('/health/database')
def database_health():
    """Database connectivity check"""
    if not db_manager:
        return jsonify({
            'status': 'error',
            'message': 'Database manager not initialized'
        }), 500
    
    try:
        connected = db_manager.test_connection()
        return jsonify({
            'status': 'healthy' if connected else 'unhealthy',
            'database_connected': connected,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/health/ollama')
def ollama_health():
    """Ollama connectivity check"""
    if not embedding_generator:
        return jsonify({
            'status': 'error',
            'message': 'Embedding generator not initialized'
        }), 500
    
    try:
        ollama_status = embedding_generator.test_ollama_connection()
        healthy_instances = sum(1 for status in ollama_status.values() if status)
        
        return jsonify({
            'status': 'healthy' if healthy_instances > 0 else 'unhealthy',
            'healthy_instances': healthy_instances,
            'total_instances': len(ollama_status),
            'instance_status': ollama_status,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/health/detailed')
def detailed_health():
    """Comprehensive health check"""
    health_data = {
        'timestamp': datetime.now().isoformat(),
        'service': 'babel-processor-test',
        'overall_status': 'healthy'
    }
    
    # Database health
    try:
        if db_manager:
            db_connected = db_manager.test_connection()
            health_data['database'] = {
                'status': 'healthy' if db_connected else 'unhealthy',
                'connected': db_connected
            }
            
            if db_connected:
                stats = db_manager.get_processing_stats()
                health_data['database']['stats'] = stats
        else:
            health_data['database'] = {'status': 'error', 'message': 'Not initialized'}
            health_data['overall_status'] = 'unhealthy'
    except Exception as e:
        health_data['database'] = {'status': 'error', 'message': str(e)}
        health_data['overall_status'] = 'unhealthy'
    
    # Ollama health
    try:
        if embedding_generator:
            ollama_status = embedding_generator.test_ollama_connection()
            healthy_instances = sum(1 for status in ollama_status.values() if status)
            
            health_data['ollama'] = {
                'status': 'healthy' if healthy_instances > 0 else 'unhealthy',
                'healthy_instances': healthy_instances,
                'total_instances': len(ollama_status),
                'instances': ollama_status
            }
            
            if healthy_instances == 0:
                health_data['overall_status'] = 'degraded'
        else:
            health_data['ollama'] = {'status': 'error', 'message': 'Not initialized'}
    except Exception as e:
        health_data['ollama'] = {'status': 'error', 'message': str(e)}
    
    # Environment info
    health_data['environment'] = {
        'db_name': os.getenv('DB_NAME', 'unknown'),
        'db_host': os.getenv('DB_HOST', 'unknown'),
        'ollama_base_url': os.getenv('OLLAMA_BASE_URL', 'unknown'),
        'pipeline_mode': os.getenv('PIPELINE_MODE', 'unknown'),
        'max_workers': os.getenv('MAX_WORKERS', 'unknown')
    }
    
    # Set appropriate status code
    status_code = 200
    if health_data['overall_status'] == 'unhealthy':
        status_code = 503
    elif health_data['overall_status'] == 'degraded':
        status_code = 200  # Still operational
    
    return jsonify(health_data), status_code

@app.route('/stats')
def get_stats():
    """Get processing statistics"""
    if not db_manager:
        return jsonify({'error': 'Database manager not initialized'}), 500
    
    try:
        processing_stats = db_manager.get_processing_stats()
        embedding_stats = db_manager.get_embedding_stats()
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'processing': processing_stats,
            'embeddings': embedding_stats
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/config')
def get_config():
    """Get pipeline configuration"""
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'environment': {
            'db_name': os.getenv('DB_NAME'),
            'db_host': os.getenv('DB_HOST'),
            'ollama_base_url': os.getenv('OLLAMA_BASE_URL'),
            'pipeline_mode': os.getenv('PIPELINE_MODE'),
            'max_workers': os.getenv('MAX_WORKERS'),
            'max_books': os.getenv('MAX_BOOKS'),
            'max_chunks_per_book': os.getenv('MAX_CHUNKS_PER_BOOK')
        },
        'paths': {
            'epubs_dir': '/app/data/epubs',
            'logs_dir': '/app/data/logs',
            'output_dir': '/app/data/output'
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'timestamp': datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'timestamp': datetime.now().isoformat()
    }), 500

def main():
    """Main entry point"""
    # Initialize components
    init_components()
    
    # Get port from environment
    port = int(os.getenv('HEALTH_CHECK_PORT', 8080))
    
    logger.info(f"Starting health check server on port {port}")
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )

if __name__ == '__main__':
    main()