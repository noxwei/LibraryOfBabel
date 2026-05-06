"""
LibraryOfBabel API Parameter Validation Middleware
=================================================

Dr. Sarah Chen (陈雪芳) - REST API Standardization
Enforces consistent parameter naming and validation across all endpoints.

Zero tolerance for parameter inconsistencies. Production-ready validation.
"""

import uuid
import logging
from functools import wraps
from flask import request, jsonify
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

# STANDARDIZED PARAMETER NAMES - NO EXCEPTIONS
STANDARD_PARAMS = {
    'query': 'q',           # ALL search queries use q= (never term=)
    'action': 'action',     # Resource actions
    'identifier': 'id',     # All IDs (book_id, chunk_id, etc.)
    'limit': 'limit',       # Pagination limit
    'page': 'page',         # Pagination page (never page_num=)
    'sort': 'sort',         # Sorting parameter
    'filter': 'filter',     # Filtering parameter
    'format': 'format',     # Response format
    'words_per_page': 'words_per_page',  # Dynamic pagination word count
}

# PARAMETER VALIDATION SCHEMAS
PARAM_SCHEMAS = {
    'q': {
        'type': str,
        'min_length': 1,
        'max_length': 500,
        'strip': True
    },
    'action': {
        'type': str,
        'allowed_values': ['list', 'summary', 'search', 'count', 'titles', 'books', 'semantic', 'semantic_passages', 'passage', 'random', 'has_results', 'concept', 'emotional', 'highlighted', 'advanced', 'toc', 'random_page', 'construct', 'page', 'simple', 'discovery', 'style', 'quality', 'author_influence', 'thematic_evolution', 'content_analysis'],
        'default': 'list'
    },
    'id': {
        'type': int,
        'min_value': 1,
        'max_value': 999999
    },
    'limit': {
        'type': int,
        'min_value': 1,
        'max_value': 200,
        'default': 20
    },
    'page': {
        'type': int,
        'min_value': 1,
        'max_value': 10000,
        'default': 1
    },
    'sort': {
        'type': str,
        'allowed_values': ['title', 'author', 'date', 'relevance', 'popularity', 'book_id', 'publication_date', 'word_count', 'alpha_title', 'alpha_author'],
        'default': 'relevance'
    },
    'format': {
        'type': str,
        'allowed_values': ['json', 'simple'],
        'default': 'json'
    },
    'words_per_page': {
        'type': int,
        'min_value': 100,
        'max_value': 2000,
        'default': 1000
    },
    'title': {
        'type': str,
        'min_length': 1,
        'max_length': 500,
        'strip': True
    },
    'author': {
        'type': str,
        'min_length': 1,
        'max_length': 255,
        'strip': True
    },
    'genre': {
        'type': str,
        'min_length': 1,
        'max_length': 100,
        'strip': True
    },
    'description': {
        'type': str,
        'min_length': 1,
        'max_length': 500,
        'strip': True
    },
    'embedding_model': {
        'type': str,
        'allowed_values': ['nomic-embed-text-v2-moe', 'snowflake-arctic-embed2', 'bge-m3'],
        'default': 'nomic-embed-text-v2-moe'
    },
    'ensemble': {
        'type': bool,
        'default': False
    }
}

class ValidationError(Exception):
    """Standard validation error with consistent formatting"""
    def __init__(self, parameter: str, message: str, code: str = "INVALID_PARAMETER"):
        self.parameter = parameter
        self.message = message
        self.code = code
        super().__init__(f"{parameter}: {message}")

class ParameterValidator:
    """Production-ready parameter validation with zero tolerance for inconsistencies"""
    
    @staticmethod
    def validate_parameter(name: str, value: Any, schema: Dict) -> Any:
        """Validate single parameter against schema"""
        if value is None:
            if 'default' in schema:
                return schema['default']
            elif schema.get('required', False):
                raise ValidationError(name, f"Required parameter '{name}' is missing", "MISSING_REQUIRED")
            return None
        
        # Type validation
        expected_type = schema.get('type', str)
        if expected_type == int:
            try:
                value = int(value)
            except (ValueError, TypeError):
                raise ValidationError(name, f"Parameter '{name}' must be an integer", "INVALID_TYPE")
        
        elif expected_type == str:
            if not isinstance(value, str):
                value = str(value)
            if schema.get('strip', False):
                value = value.strip()
        
        elif expected_type == bool:
            if isinstance(value, bool):
                pass  # Already boolean
            elif isinstance(value, str):
                if value.lower() in ('true', '1', 'yes', 'on'):
                    value = True
                elif value.lower() in ('false', '0', 'no', 'off'):
                    value = False
                else:
                    raise ValidationError(name, f"Parameter '{name}' must be a boolean (true/false)", "INVALID_TYPE")
            elif isinstance(value, int):
                value = bool(value)
            else:
                raise ValidationError(name, f"Parameter '{name}' must be a boolean", "INVALID_TYPE")
        
        # String validation
        if expected_type == str and value:
            if 'min_length' in schema and len(value) < schema['min_length']:
                raise ValidationError(name, f"Parameter '{name}' must be at least {schema['min_length']} characters", "TOO_SHORT")
            
            if 'max_length' in schema and len(value) > schema['max_length']:
                raise ValidationError(name, f"Parameter '{name}' must be no more than {schema['max_length']} characters", "TOO_LONG")
            
            if 'allowed_values' in schema and value not in schema['allowed_values']:
                raise ValidationError(name, f"Parameter '{name}' must be one of: {', '.join(schema['allowed_values'])}", "INVALID_VALUE")
        
        # Integer validation
        if expected_type == int:
            if 'min_value' in schema and value < schema['min_value']:
                raise ValidationError(name, f"Parameter '{name}' must be at least {schema['min_value']}", "TOO_SMALL")
            
            if 'max_value' in schema and value > schema['max_value']:
                raise ValidationError(name, f"Parameter '{name}' must be no more than {schema['max_value']}", "TOO_LARGE")
        
        return value
    
    @staticmethod
    def validate_request_params(required_params: List[str] = None, 
                              optional_params: List[str] = None) -> Dict[str, Any]:
        """
        Validate all request parameters against standardized schemas
        
        Args:
            required_params: List of required parameter names
            optional_params: List of optional parameter names
            
        Returns:
            Dict of validated parameters
            
        Raises:
            ValidationError: If any parameter fails validation
        """
        required_params = required_params or []
        optional_params = optional_params or []
        all_params = required_params + optional_params
        
        validated = {}
        errors = []
        
        # Check for legacy parameter names and reject them
        # Allow page_num for book page action specifically
        action = request.args.get('action', '')
        if action == 'page':
            legacy_params = {'term', 'book_id', 'chunk_id', 'search_type'}
        else:
            legacy_params = {'term', 'page_num', 'book_id', 'chunk_id', 'search_type'}
        
        found_legacy = set(request.args.keys()) & legacy_params
        if found_legacy:
            legacy_list = ', '.join(found_legacy)
            raise ValidationError('legacy_parameters', 
                                f"Legacy parameters detected: {legacy_list}. Use standardized names: {STANDARD_PARAMS}", 
                                "LEGACY_PARAMETERS")
        
        # Validate each parameter
        for param_name in all_params:
            if param_name not in PARAM_SCHEMAS:
                logger.warning(f"No validation schema for parameter: {param_name}")
                continue
            
            raw_value = request.args.get(param_name)
            schema = PARAM_SCHEMAS[param_name].copy()
            
            # Mark required parameters
            if param_name in required_params:
                schema['required'] = True
            
            try:
                validated[param_name] = ParameterValidator.validate_parameter(param_name, raw_value, schema)
            except ValidationError as e:
                errors.append(e)
        
        # Check for unexpected parameters
        allowed_params = set(all_params) | {'api_key'}  # api_key allowed for auth
        
        # Allow page_num for book page action specifically
        if action == 'page':
            allowed_params.add('page_num')
            
        provided_params = set(request.args.keys())
        unexpected = provided_params - allowed_params
        
        if unexpected:
            unexpected_list = ', '.join(unexpected)
            errors.append(ValidationError('unexpected_parameters', 
                                        f"Unexpected parameters: {unexpected_list}", 
                                        "UNEXPECTED_PARAMETERS"))
        
        if errors:
            # Return first error (most important)
            raise errors[0]
        
        return validated

def validate_params(*required_params, **optional_params_with_defaults):
    """
    Decorator for endpoint parameter validation
    
    Usage:
        @validate_params('q', 'action', limit=20, page=1)
        def search_endpoint():
            params = request.validated_params  # Access validated parameters
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Extract optional parameters
                optional_params = list(optional_params_with_defaults.keys())
                
                # Validate parameters
                validated = ParameterValidator.validate_request_params(
                    required_params=list(required_params),
                    optional_params=optional_params
                )
                
                # Apply defaults from decorator
                for param, default in optional_params_with_defaults.items():
                    if validated.get(param) is None:
                        validated[param] = default
                
                # Attach to request for use in endpoint
                request.validated_params = validated
                
                # Generate request ID for tracing
                request.request_id = str(uuid.uuid4())
                
                return func(*args, **kwargs)
                
            except ValidationError as e:
                from .response_helpers import create_error_response
                return create_error_response(
                    message=e.message,
                    code=e.code,
                    status_code=400
                )
            except Exception as e:
                logger.error(f"Validation error in {func.__name__}: {e}")
                from .response_helpers import create_error_response
                return create_error_response(
                    message="Parameter validation failed",
                    code="VALIDATION_ERROR", 
                    status_code=400
                )
        
        return wrapper
    return decorator

# Helper functions for common validation patterns
def validate_search_params():
    """Standard validation for search endpoints"""
    return ParameterValidator.validate_request_params(
        required_params=['q'],
        optional_params=['action', 'limit', 'page', 'sort', 'format']
    )

def validate_book_params():
    """Standard validation for book endpoints"""
    return ParameterValidator.validate_request_params(
        optional_params=['id', 'action', 'limit', 'page']
    )

def validate_list_params():
    """Standard validation for list endpoints"""
    return ParameterValidator.validate_request_params(
        optional_params=['limit', 'page', 'sort', 'format']
    )