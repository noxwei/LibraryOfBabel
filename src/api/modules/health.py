"""
Health Check Module - PostgreSQL-First Architecture
Dr. Sarah Chen (陈雪芳) Design
Container-Enhanced by Dr. Elena Rodriguez (IAV)
"""

import os
import logging
from flask import Blueprint, jsonify
from .database import execute_pg_function, test_connection, test_container_connectivity

logger = logging.getLogger(__name__)
health_bp = Blueprint('health', __name__)


@health_bp.route('/health')
def health_check():
    """Public health check endpoint with container awareness - no auth required"""
    try:
        # Container environment detection
        is_container = os.getenv('RUNNING_IN_CONTAINER', '').lower() == 'true'
        
        # Test database connection
        db_healthy = test_connection()
        
        # Container-specific connectivity test
        container_info = {}
        if is_container:
            container_test = test_container_connectivity()
            container_info = {
                'container_environment': True,
                'container_connectivity': {
                    'readonly_connection': container_test.get('readonly_connection', False),
                    'network_latency_ms': container_test.get('network_latency_ms'),
                    'server_version': container_test.get('server_version'),
                    'errors': container_test.get('errors', [])
                }
            }
        
        if db_healthy:
            # Get stats using PostgreSQL function
            stats = execute_pg_function('api_shortcuts_collection_health')
            
            response_data = {
                'status': 'healthy',
                'database': 'connected',
                'api_version': '4.0-modular-postgresql-first-containerized',
                'environment': 'container' if is_container else 'local',
                'features': [
                    'PostgreSQL-First architecture',
                    'Modular design',
                    'Extended semantic search',
                    'iOS Shortcuts optimization',
                    'Zero hardcoded SQL',
                    'Container-aware configuration'
                ],
                'statistics': stats
            }
            
            # Add container-specific information
            if container_info:
                response_data.update(container_info)
            
            return jsonify(response_data)
        else:
            response_data = {
                'status': 'unhealthy',
                'database': 'disconnected',
                'environment': 'container' if is_container else 'local',
                'error': 'Database connection failed'
            }
            
            # Add container debugging info if available
            if container_info:
                response_data.update(container_info)
            
            return jsonify(response_data), 503
            
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'database': 'error',
            'environment': 'container' if os.getenv('RUNNING_IN_CONTAINER', '').lower() == 'true' else 'local',
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
    """V4 Health check with detailed metrics and container awareness"""
    try:
        is_container = os.getenv('RUNNING_IN_CONTAINER', '').lower() == 'true'
        
        # Get comprehensive health data
        collection_health = execute_pg_function('api_shortcuts_collection_health')
        dashboard_stats = execute_pg_function('api_shortcuts_dashboard', False)
        
        response_data = {
            'status': 'healthy',
            'api_version': '4.0-modular-postgresql-first-containerized',
            'architecture': 'PostgreSQL-First with modular design',
            'environment': 'container' if is_container else 'local',
            'database': 'connected',
            'collection_health': collection_health,
            'dashboard': dashboard_stats,
            'features': [
                'Modular architecture',
                'PostgreSQL-First design',
                'Extended semantic search (10-word)',
                'iOS Shortcuts optimization',
                'Authentication middleware',
                'Zero hardcoded SQL queries',
                'Container-aware configuration'
            ]
        }
        
        # Add container-specific diagnostics
        if is_container:
            container_test = test_container_connectivity()
            response_data['container_diagnostics'] = {
                'connectivity_test': container_test,
                'environment_variables': {
                    'log_path': os.getenv('LOG_PATH'),
                    'db_host': os.getenv('DB_HOST'),
                    'api_port': os.getenv('API_PORT'),
                    'cors_origins': os.getenv('CORS_ORIGINS')
                }
            }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"V4 health check error: {e}")
        return jsonify({
            'status': 'error', 
            'message': str(e),
            'environment': 'container' if os.getenv('RUNNING_IN_CONTAINER', '').lower() == 'true' else 'local'
        }), 500


@health_bp.route('/health/container')
def container_health_check():
    """Container-specific health check endpoint"""
    try:
        is_container = os.getenv('RUNNING_IN_CONTAINER', '').lower() == 'true'
        
        if not is_container:
            return jsonify({
                'status': 'not_applicable',
                'message': 'Container health check only available in container environment'
            }), 400
        
        # Comprehensive container health check
        container_test = test_container_connectivity()
        
        # Check critical container resources
        container_health = {
            'container_detected': True,
            'database_connectivity': container_test,
            'environment_configuration': {
                'running_in_container': is_container,
                'log_path_configured': bool(os.getenv('LOG_PATH')),
                'db_host_configured': bool(os.getenv('DB_HOST')),
                'api_port_configured': bool(os.getenv('API_PORT')),
                'cors_configured': bool(os.getenv('CORS_ORIGINS'))
            },
            'file_system': {
                'log_directory_writable': os.access(os.getenv('LOG_PATH', '/app/logs'), os.W_OK),
                'app_directory_readable': os.access('/app', os.R_OK)
            }
        }
        
        # Determine overall health status
        is_healthy = (
            container_test.get('readonly_connection', False) and
            container_health['environment_configuration']['log_path_configured'] and
            container_health['file_system']['log_directory_writable']
        )
        
        status_code = 200 if is_healthy else 503
        
        return jsonify({
            'status': 'healthy' if is_healthy else 'unhealthy',
            'container_health': container_health,
            'recommendations': _get_container_recommendations(container_health) if not is_healthy else []
        }), status_code
        
    except Exception as e:
        logger.error(f"Container health check error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


def _get_container_recommendations(container_health):
    """Generate container-specific troubleshooting recommendations"""
    recommendations = []
    
    if not container_health['database_connectivity'].get('readonly_connection'):
        recommendations.extend([
            'Check PostgreSQL server is running and accessible',
            'Verify DB_HOST environment variable points to correct database server',
            'Ensure PostgreSQL allows connections from Docker network',
            'Check pg_hba.conf configuration for container access'
        ])
    
    if not container_health['environment_configuration']['log_path_configured']:
        recommendations.append('Set LOG_PATH environment variable')
    
    if not container_health['file_system']['log_directory_writable']:
        recommendations.extend([
            'Ensure log directory has write permissions',
            'Check container user permissions for log directory'
        ])
    
    return recommendations