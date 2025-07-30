"""
Health Check Module - PostgreSQL-First Architecture
Dr. Sarah Chen (陈雪芳) Design
"""

import logging
from flask import Blueprint, jsonify
from .database import execute_pg_function, test_connection

logger = logging.getLogger(__name__)
health_bp = Blueprint('health', __name__)


@health_bp.route('/health')
def health_check():
    """Public health check endpoint - no auth required"""
    try:
        # Test database connection
        db_healthy = test_connection()
        
        if db_healthy:
            # Get stats using PostgreSQL function
            stats = execute_pg_function('api_shortcuts_collection_health')
            
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'api_version': '4.0-modular-postgresql-first',
                'features': [
                    'PostgreSQL-First architecture',
                    'Modular design',
                    'Extended semantic search',
                    'iOS Shortcuts optimization',
                    'Zero hardcoded SQL'
                ],
                'statistics': stats
            })
        else:
            return jsonify({
                'status': 'unhealthy',
                'database': 'disconnected',
                'error': 'Database connection failed'
            }), 503
            
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'database': 'error',
            'error': str(e)
        }), 503


@health_bp.route('/api/v3/health')
def v3_health_check():
    """V3 Legacy health check"""
    try:
        result = execute_pg_function('api_v3_health')
        return jsonify(result)
    except Exception as e:
        logger.error(f"V3 health check error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@health_bp.route('/api/v4/health')
def v4_health_check():
    """V4 Health check with detailed metrics"""
    try:
        # Get comprehensive health data
        collection_health = execute_pg_function('api_shortcuts_collection_health')
        dashboard_stats = execute_pg_function('api_shortcuts_dashboard', False)
        
        return jsonify({
            'status': 'healthy',
            'api_version': '4.0-modular-postgresql-first',
            'architecture': 'PostgreSQL-First with modular design',
            'database': 'connected',
            'collection_health': collection_health,
            'dashboard': dashboard_stats,
            'features': [
                'Modular architecture',
                'PostgreSQL-First design',
                'Extended semantic search (10-word)',
                'iOS Shortcuts optimization',
                'Authentication middleware',
                'Zero hardcoded SQL queries'
            ]
        })
        
    except Exception as e:
        logger.error(f"V4 health check error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500