"""
LibraryOfBabel Standardized Health API
=====================================

Dr. Sarah Chen (陈雪芳) - REST API Standardization
LEVEL 4 UTILITIES: /health, /api/info

CONSOLIDATED FROM:
- /health (3 endpoints)
- /api/v4/health
- /api/v3/health  
- /health/container

ONLY PLACE FOR SYSTEM METADATA - NO VERSION POLLUTION ELSEWHERE
"""

import os
import logging
from flask import Blueprint, jsonify
from .database import execute_pg_function, test_connection, test_container_connectivity
from .response_helpers import (
    create_success_response, create_error_response, init_response_timing
)

logger = logging.getLogger(__name__)
standardized_health_bp = Blueprint('standardized_health', __name__)

@standardized_health_bp.route('/health')
def public_health_check():
    """
    PUBLIC health check endpoint - minimal metadata
    No authentication required for monitoring systems
    """
    try:
        init_response_timing()
        
        # Simple health check
        db_healthy = test_connection()
        
        if db_healthy:
            return jsonify({
                "status": "healthy",
                "database": "connected",
                "timestamp": "2025-08-14T12:00:00Z"
            }), 200
        else:
            return jsonify({
                "status": "unhealthy", 
                "database": "disconnected",
                "timestamp": "2025-08-14T12:00:00Z"
            }), 503
            
    except Exception as e:
        logger.error(f"Public health check error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": "2025-08-14T12:00:00Z"
        }), 503

@standardized_health_bp.route('/api/info')
def system_info():
    """
    SYSTEM INFO - The ONLY endpoint with system metadata
    Contains all the design/architecture info that should not pollute other endpoints
    """
    try:
        init_response_timing()
        
        # Container environment detection
        is_container = os.getenv('RUNNING_IN_CONTAINER', '').lower() == 'true'
        
        # Get comprehensive system stats using PostgreSQL functions
        try:
            collection_health = execute_pg_function('api_shortcuts_collection_health')
            dashboard_stats = execute_pg_function('api_shortcuts_dashboard', False)
        except Exception:
            collection_health = {"status": "database_error"}
            dashboard_stats = {"status": "database_error"}
        
        # Container diagnostics if in container
        container_info = {}
        if is_container:
            container_test = test_container_connectivity()
            container_info = {
                "container_environment": True,
                "connectivity": container_test
            }
        
        system_data = {
            # CORE SYSTEM INFO
            "api_name": "LibraryOfBabel Production API",
            "status": "production_ready",
            "environment": "container" if is_container else "local",
            
            # ARCHITECTURE (only here, not in other endpoints)
            "architecture": "PostgreSQL-First with REST Standardization",
            "design_principles": [
                "Zero hardcoded SQL in application code",
                "All business logic in PostgreSQL functions", 
                "Standardized parameter naming across all endpoints",
                "Unified response schema",
                "Mobile-optimized responses"
            ],
            
            # DESIGNERS (only here, not polluting other endpoints)
            "technical_leads": [
                "Dr. Sarah Chen (陈雪芳) - PostgreSQL-First Architecture",
                "Dr. Elena Rodriguez (IAV) - UX-Optimized Design"
            ],
            
            # CORE CAPABILITIES
            "features": [
                "Standardized REST API hierarchy",
                "PostgreSQL-First design (zero hardcoded SQL)",
                "Extended semantic search (10-word capability)",
                "iOS Shortcuts optimization", 
                "Unified parameter validation",
                "Comprehensive error handling",
                "Container-aware configuration"
            ],
            
            # API STRUCTURE
            "endpoints": {
                "core_resources": [
                    "/api/books - Book management and navigation",
                    "/api/search - All search functionality", 
                    "/api/mobile/* - iOS Shortcuts optimization"
                ],
                "utilities": [
                    "/health - Public health check",
                    "/api/info - System information (this endpoint)"
                ]
            },
            
            # STATISTICS
            "collection_health": collection_health,
            "dashboard": dashboard_stats,
            
            # PERFORMANCE
            "database_functions": [
                "api_list_books",
                "api_shortcuts_book_summary", 
                "api_shortcuts_search_simple",
                "api_semantic_phrase_search_optimized",
                "api_extended_semantic_search",
                "api_shortcuts_collection_health"
            ]
        }
        
        # Add container info if applicable
        if container_info:
            system_data["container"] = container_info
        
        return create_success_response(
            data=system_data,
            message="Complete system information and architecture details"
        )
        
    except Exception as e:
        logger.error(f"System info error: {e}")
        return create_error_response(
            message="Failed to retrieve system information",
            code="SYSTEM_INFO_ERROR",
            status_code=500
        )

@standardized_health_bp.route('/api/health') 
def detailed_health_check():
    """
    DETAILED health check with performance metrics
    For internal monitoring and diagnostics
    """
    try:
        init_response_timing()
        
        is_container = os.getenv('RUNNING_IN_CONTAINER', '').lower() == 'true'
        
        # Comprehensive health check
        db_healthy = test_connection()
        
        if db_healthy:
            # Get detailed health data using PostgreSQL functions
            collection_health = execute_pg_function('api_shortcuts_collection_health')
            
            health_data = {
                "overall_status": "healthy",
                "database": {
                    "status": "connected",
                    "connection_test": "passed"
                },
                "environment": "container" if is_container else "local",
                "collection_health": collection_health,
                "api_status": {
                    "standardized_endpoints": "operational",
                    "parameter_validation": "active",
                    "response_formatting": "unified"
                }
            }
            
            # Add container-specific health if applicable
            if is_container:
                container_test = test_container_connectivity()
                health_data["container"] = {
                    "status": "healthy" if container_test.get('readonly_connection') else "degraded",
                    "connectivity": container_test
                }
            
            return create_success_response(
                data=health_data,
                message="System is healthy and operational"
            )
        else:
            return create_error_response(
                message="Database connection failed",
                code="DATABASE_UNHEALTHY",
                status_code=503
            )
            
    except Exception as e:
        logger.error(f"Detailed health check error: {e}")
        return create_error_response(
            message="Health check failed",
            code="HEALTH_CHECK_ERROR", 
            status_code=503
        )

@standardized_health_bp.route('/health/container')
def container_health_check():
    """
    CONTAINER-specific health check
    Only available in container environments
    """
    try:
        init_response_timing()
        
        is_container = os.getenv('RUNNING_IN_CONTAINER', '').lower() == 'true'
        
        if not is_container:
            return create_error_response(
                message="Container health check only available in container environment",
                code="NOT_CONTAINER_ENVIRONMENT",
                status_code=400
            )
        
        # Comprehensive container health check
        container_test = test_container_connectivity()
        
        container_health = {
            "container_detected": True,
            "database_connectivity": container_test,
            "environment_configuration": {
                "log_path_configured": bool(os.getenv('LOG_PATH')),
                "db_host_configured": bool(os.getenv('DB_HOST')),
                "api_port_configured": bool(os.getenv('API_PORT'))
            },
            "file_system": {
                "log_directory_writable": os.access(os.getenv('LOG_PATH', '/app/logs'), os.W_OK),
                "app_directory_readable": os.access('/app', os.R_OK)
            }
        }
        
        # Determine overall health
        is_healthy = (
            container_test.get('readonly_connection', False) and
            container_health['environment_configuration']['log_path_configured'] and
            container_health['file_system']['log_directory_writable']
        )
        
        status_code = 200 if is_healthy else 503
        
        return create_success_response(
            data={
                "status": "healthy" if is_healthy else "unhealthy",
                "container_health": container_health
            },
            message="Container health assessment complete"
        ), status_code
        
    except Exception as e:
        logger.error(f"Container health check error: {e}")
        return create_error_response(
            message="Container health check failed",
            code="CONTAINER_HEALTH_ERROR",
            status_code=503
        )