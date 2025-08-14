"""
LibraryOfBabel API Response Standardization Helpers
==================================================

Dr. Sarah Chen (陈雪芳) - REST API Standardization
Unified response formatting with zero inconsistencies across all endpoints.

STRICT RESPONSE SCHEMA - NO EXCEPTIONS
"""

import time
import uuid
from datetime import datetime, timezone
from flask import request, jsonify
from typing import Any, Dict, Optional, Union, List

# RESPONSE TIMING TRACKER
response_start_times = {}

def start_response_timer(request_id: str = None) -> str:
    """Start timing response for performance metrics"""
    if not request_id:
        request_id = getattr(request, 'request_id', str(uuid.uuid4()))
    
    response_start_times[request_id] = time.time()
    return request_id

def get_response_time(request_id: str) -> float:
    """Get response time in milliseconds"""
    if request_id in response_start_times:
        elapsed = (time.time() - response_start_times[request_id]) * 1000
        # Clean up to prevent memory leaks
        del response_start_times[request_id]
        return round(elapsed, 2)
    return 0.0

class StandardResponse:
    """
    Production-ready response standardization
    ZERO tolerance for inconsistent response formats
    """
    
    @staticmethod
    def create_success_response(
        data: Union[Dict, List, Any],
        total_count: Optional[int] = None,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        message: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict:
        """
        Create standardized success response
        
        STRICT SCHEMA:
        {
          "success": true,
          "data": object|array,
          "meta": {
            "timestamp": "ISO8601",
            "request_id": "uuid",
            "response_time_ms": number,
            "pagination": {...}
          }
        }
        """
        if not request_id:
            request_id = getattr(request, 'request_id', str(uuid.uuid4()))
        
        response = {
            "success": True,
            "data": data,
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": request_id,
                "response_time_ms": get_response_time(request_id)
            }
        }
        
        # Add pagination metadata if provided
        if any(x is not None for x in [total_count, limit, page]):
            response["meta"]["pagination"] = {}
            if total_count is not None:
                response["meta"]["pagination"]["total_count"] = total_count
            if limit is not None:
                response["meta"]["pagination"]["limit"] = limit
            if page is not None:
                response["meta"]["pagination"]["page"] = page
                if total_count and limit:
                    response["meta"]["pagination"]["total_pages"] = (total_count + limit - 1) // limit
        
        # Add optional message
        if message:
            response["meta"]["message"] = message
        
        return response
    
    @staticmethod
    def create_error_response(
        message: str,
        code: str = "API_ERROR",
        details: Optional[Dict] = None,
        status_code: int = 500,
        request_id: Optional[str] = None
    ) -> tuple:
        """
        Create standardized error response
        
        STRICT ERROR SCHEMA:
        {
          "success": false,
          "error": {
            "code": "string",
            "message": "string",
            "details": object
          },
          "meta": {
            "timestamp": "ISO8601",
            "request_id": "uuid",
            "response_time_ms": number
          }
        }
        """
        if not request_id:
            request_id = getattr(request, 'request_id', str(uuid.uuid4()))
        
        response = {
            "success": False,
            "error": {
                "code": code,
                "message": message
            },
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": request_id,
                "response_time_ms": get_response_time(request_id)
            }
        }
        
        if details:
            response["error"]["details"] = details
        
        return jsonify(response), status_code

# CONVENIENCE FUNCTIONS FOR COMMON RESPONSE PATTERNS

def create_success_response(
    data: Union[Dict, List, Any],
    total_count: Optional[int] = None,
    limit: Optional[int] = None,
    page: Optional[int] = None,
    message: Optional[str] = None,
    status_code: int = 200
) -> tuple:
    """Create standardized success response with JSON formatting"""
    request_id = getattr(request, 'request_id', str(uuid.uuid4()))
    response = StandardResponse.create_success_response(
        data=data,
        total_count=total_count,
        limit=limit,
        page=page,
        message=message,
        request_id=request_id
    )
    return jsonify(response), status_code

def create_error_response(
    message: str,
    code: str = "API_ERROR",
    details: Optional[Dict] = None,
    status_code: int = 500
) -> tuple:
    """Create standardized error response"""
    return StandardResponse.create_error_response(
        message=message,
        code=code,
        details=details,
        status_code=status_code
    )

def create_list_response(
    items: List[Any],
    total_count: Optional[int] = None,
    limit: Optional[int] = None,
    page: Optional[int] = None
) -> tuple:
    """Create standardized list response with pagination"""
    if total_count is None:
        total_count = len(items)
    
    return create_success_response(
        data=items,
        total_count=total_count,
        limit=limit,
        page=page
    )

def create_single_item_response(item: Any, message: Optional[str] = None) -> tuple:
    """Create standardized single item response"""
    return create_success_response(data=item, message=message)

def create_boolean_response(result: bool, message: Optional[str] = None) -> tuple:
    """Create standardized boolean response (for has_results, etc.)"""
    return create_success_response(data=result, message=message)

def create_count_response(count: int) -> tuple:
    """Create standardized count response"""
    return create_success_response(data={"count": count})

# ERROR RESPONSE HELPERS

def create_not_found_response(resource: str = "Resource") -> tuple:
    """Standard 404 response"""
    return create_error_response(
        message=f"{resource} not found",
        code="NOT_FOUND",
        status_code=404
    )

def create_bad_request_response(message: str, details: Optional[Dict] = None) -> tuple:
    """Standard 400 response"""
    return create_error_response(
        message=message,
        code="BAD_REQUEST",
        details=details,
        status_code=400
    )

def create_validation_error_response(parameter: str, message: str) -> tuple:
    """Standard validation error response"""
    return create_error_response(
        message=f"Validation error: {message}",
        code="VALIDATION_ERROR",
        details={"parameter": parameter, "message": message},
        status_code=400
    )

def create_internal_error_response(message: str = "Internal server error") -> tuple:
    """Standard 500 response"""
    return create_error_response(
        message=message,
        code="INTERNAL_SERVER_ERROR",
        status_code=500
    )

# BACKWARD COMPATIBILITY HELPERS

def wrap_legacy_response(legacy_data: Any) -> tuple:
    """
    Wrap legacy response data in new standardized format
    Used during migration period
    """
    # Detect if data is already in new format
    if isinstance(legacy_data, dict) and "success" in legacy_data:
        return jsonify(legacy_data), 200
    
    # Wrap legacy data
    return create_success_response(data=legacy_data)

# MOBILE-OPTIMIZED RESPONSES

def create_mobile_response(data: Any, simplified: bool = True) -> tuple:
    """
    Create mobile-optimized response
    Reduced metadata for iOS Shortcuts compatibility
    """
    if simplified:
        # For iOS Shortcuts - return just the data
        if isinstance(data, dict) and len(data) == 1:
            # Single value responses (like count)
            return jsonify(next(iter(data.values()))), 200
        return jsonify(data), 200
    else:
        # Standard response with full metadata
        return create_success_response(data)

# PERFORMANCE MONITORING

def add_performance_headers(response, start_time: float = None):
    """Add performance headers to response"""
    if start_time:
        response.headers['X-Response-Time'] = f"{(time.time() - start_time) * 1000:.2f}ms"
    
    response.headers['X-API-Version'] = 'standardized'
    response.headers['X-Request-ID'] = getattr(request, 'request_id', 'unknown')
    return response

# RESPONSE MIDDLEWARE

def init_response_timing():
    """Initialize response timing for current request"""
    request_id = getattr(request, 'request_id', str(uuid.uuid4()))
    start_response_timer(request_id)
    return request_id