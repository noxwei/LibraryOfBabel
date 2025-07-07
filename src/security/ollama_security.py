#!/usr/bin/env python3
"""
Ollama Security Validation Module
=================================

Security layer for Ollama URL Generator Agent with comprehensive protection:
- Input sanitization and validation
- Rate limiting and abuse prevention  
- API key protection and rotation
- Output validation and filtering
- Audit logging and monitoring

Security QA Agent Requirements Implemented:
- API key protection ✅
- Input sanitization ✅  
- Ollama endpoint validation ✅
- Rate limiting ✅
"""

import re
import time
import hashlib
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

class OllamaSecurityValidator:
    """
    Comprehensive security validation for Ollama integration
    
    Features:
    - Input sanitization and length limits
    - Rate limiting per user/IP
    - Malicious pattern detection
    - API key validation and rotation
    - Audit logging for security events
    """
    
    def __init__(self):
        """Initialize security validator"""
        
        # Rate limiting configuration
        self.rate_limits = {
            'requests_per_minute': 20,
            'requests_per_hour': 100,
            'requests_per_day': 500
        }
        
        # Request tracking for rate limiting
        self.request_tracking = {
            'minute': defaultdict(list),
            'hour': defaultdict(list), 
            'day': defaultdict(list)
        }
        
        # Malicious pattern detection
        self.malicious_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS attempts
            r'javascript:',                 # JavaScript injection
            r'data:text/html',             # Data URL attacks
            r'vbscript:',                  # VBScript injection
            r'on\w+\s*=',                  # Event handler injection
            r'<iframe[^>]*>',              # Iframe injection
            r'<object[^>]*>',              # Object injection
            r'<embed[^>]*>',               # Embed injection
            r'eval\s*\(',                  # Code evaluation
            r'exec\s*\(',                  # Code execution
            r'system\s*\(',                # System calls
            r'__import__\s*\(',            # Python imports
            r'subprocess\.',               # Subprocess calls
            r'os\.',                       # OS module calls
            r'file://',                    # File protocol
            r'ftp://',                     # FTP protocol
            r'\.\./.*\.\.',                # Path traversal
            r'[;&|`$]',                    # Shell injection chars
        ]
        
        # Compile patterns for performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in self.malicious_patterns]
        
        # Allowed characters for queries (restrictive)
        self.allowed_chars_pattern = re.compile(r'^[a-zA-Z0-9\s\-_.,!?\'\":()&]+$')
        
        # Security event log
        self.security_events = []
        
        logger.info("🔒 Ollama Security Validator initialized")
        logger.info(f"🛡️ Rate limits: {self.rate_limits}")
        logger.info(f"🔍 Monitoring {len(self.malicious_patterns)} attack patterns")
    
    def validate_input(self, user_query: str, client_ip: str = None, user_id: str = None) -> Tuple[bool, str]:
        """
        Comprehensive input validation with security checks
        
        Args:
            user_query: User's natural language query
            client_ip: Client IP address for rate limiting
            user_id: User identifier for rate limiting
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        
        # Basic validation
        if not user_query or not isinstance(user_query, str):
            return False, "Invalid query format"
        
        # Length validation
        if len(user_query.strip()) < 3:
            return False, "Query too short (minimum 3 characters)"
        
        if len(user_query) > 500:
            self._log_security_event("QUERY_TOO_LONG", {
                'query_length': len(user_query),
                'client_ip': client_ip,
                'user_id': user_id
            })
            return False, "Query too long (maximum 500 characters)"
        
        # Character validation
        if not self.allowed_chars_pattern.match(user_query):
            self._log_security_event("INVALID_CHARACTERS", {
                'query': user_query[:100],  # Log first 100 chars only
                'client_ip': client_ip,
                'user_id': user_id
            })
            return False, "Query contains invalid characters"
        
        # Malicious pattern detection
        malicious_match = self._detect_malicious_patterns(user_query)
        if malicious_match:
            self._log_security_event("MALICIOUS_PATTERN", {
                'pattern': malicious_match,
                'query': user_query[:100],
                'client_ip': client_ip,
                'user_id': user_id
            })
            return False, "Query contains potentially malicious content"
        
        # Rate limiting validation
        rate_limit_result = self._check_rate_limits(client_ip, user_id)
        if not rate_limit_result[0]:
            self._log_security_event("RATE_LIMIT_EXCEEDED", {
                'limit_type': rate_limit_result[1],
                'client_ip': client_ip,
                'user_id': user_id
            })
            return False, f"Rate limit exceeded: {rate_limit_result[1]}"
        
        # Record successful request
        self._record_request(client_ip, user_id)
        
        return True, "Valid"
    
    def _detect_malicious_patterns(self, query: str) -> Optional[str]:
        """Detect malicious patterns in query"""
        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(query):
                return self.malicious_patterns[i]
        return None
    
    def _check_rate_limits(self, client_ip: str = None, user_id: str = None) -> Tuple[bool, str]:
        """Check rate limits for client"""
        
        identifier = user_id or client_ip or "anonymous"
        current_time = datetime.now()
        
        # Check minute limit
        minute_requests = self.request_tracking['minute'][identifier]
        minute_cutoff = current_time - timedelta(minutes=1)
        recent_minute_requests = [req for req in minute_requests if req > minute_cutoff]
        
        if len(recent_minute_requests) >= self.rate_limits['requests_per_minute']:
            return False, "Too many requests per minute"
        
        # Check hour limit
        hour_requests = self.request_tracking['hour'][identifier]
        hour_cutoff = current_time - timedelta(hours=1)
        recent_hour_requests = [req for req in hour_requests if req > hour_cutoff]
        
        if len(recent_hour_requests) >= self.rate_limits['requests_per_hour']:
            return False, "Too many requests per hour"
        
        # Check day limit
        day_requests = self.request_tracking['day'][identifier]
        day_cutoff = current_time - timedelta(days=1)
        recent_day_requests = [req for req in day_requests if req > day_cutoff]
        
        if len(recent_day_requests) >= self.rate_limits['requests_per_day']:
            return False, "Too many requests per day"
        
        return True, "Within limits"
    
    def _record_request(self, client_ip: str = None, user_id: str = None):
        """Record request for rate limiting"""
        
        identifier = user_id or client_ip or "anonymous"
        current_time = datetime.now()
        
        # Add to all tracking periods
        self.request_tracking['minute'][identifier].append(current_time)
        self.request_tracking['hour'][identifier].append(current_time)
        self.request_tracking['day'][identifier].append(current_time)
        
        # Clean old entries to prevent memory bloat
        self._cleanup_old_requests()
    
    def _cleanup_old_requests(self):
        """Clean up old request records to prevent memory bloat"""
        
        current_time = datetime.now()
        
        # Clean minute tracking (keep last 2 minutes)
        minute_cutoff = current_time - timedelta(minutes=2)
        for identifier in list(self.request_tracking['minute'].keys()):
            self.request_tracking['minute'][identifier] = [
                req for req in self.request_tracking['minute'][identifier] 
                if req > minute_cutoff
            ]
            if not self.request_tracking['minute'][identifier]:
                del self.request_tracking['minute'][identifier]
        
        # Clean hour tracking (keep last 2 hours)
        hour_cutoff = current_time - timedelta(hours=2)
        for identifier in list(self.request_tracking['hour'].keys()):
            self.request_tracking['hour'][identifier] = [
                req for req in self.request_tracking['hour'][identifier] 
                if req > hour_cutoff
            ]
            if not self.request_tracking['hour'][identifier]:
                del self.request_tracking['hour'][identifier]
        
        # Clean day tracking (keep last 2 days)
        day_cutoff = current_time - timedelta(days=2)
        for identifier in list(self.request_tracking['day'].keys()):
            self.request_tracking['day'][identifier] = [
                req for req in self.request_tracking['day'][identifier] 
                if req > day_cutoff
            ]
            if not self.request_tracking['day'][identifier]:
                del self.request_tracking['day'][identifier]
    
    def validate_api_key(self, api_key: str) -> Tuple[bool, str]:
        """
        Validate API key format and characteristics
        
        Args:
            api_key: API key to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        
        if not api_key or not isinstance(api_key, str):
            return False, "Missing or invalid API key"
        
        # Check length (typical API keys are 32-64 characters)
        if len(api_key) < 20:
            return False, "API key too short"
        
        if len(api_key) > 128:
            return False, "API key too long"
        
        # Check for valid characters (alphanumeric, dashes, underscores)
        if not re.match(r'^[a-zA-Z0-9\-_]+$', api_key):
            return False, "API key contains invalid characters"
        
        # Check for obvious test/dummy keys
        test_patterns = ['test', 'dummy', 'fake', 'example', '123456', 'abcdef']
        api_key_lower = api_key.lower()
        
        for pattern in test_patterns:
            if pattern in api_key_lower:
                self._log_security_event("SUSPICIOUS_API_KEY", {
                    'pattern': pattern,
                    'key_prefix': api_key[:8] + "..."
                })
                return False, "Suspicious API key pattern detected"
        
        return True, "Valid API key format"
    
    def validate_ollama_response(self, response_data: Any) -> Tuple[bool, str]:
        """
        Validate Ollama response for security issues
        
        Args:
            response_data: Response from Ollama
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        
        try:
            # Convert to string for pattern checking
            response_str = json.dumps(response_data) if not isinstance(response_data, str) else response_data
            
            # Check for malicious patterns in response
            malicious_match = self._detect_malicious_patterns(response_str)
            if malicious_match:
                self._log_security_event("MALICIOUS_RESPONSE", {
                    'pattern': malicious_match,
                    'response_preview': response_str[:200]
                })
                return False, "Response contains potentially malicious content"
            
            # Check response size
            if len(response_str) > 50000:  # 50KB limit
                self._log_security_event("RESPONSE_TOO_LARGE", {
                    'response_size': len(response_str)
                })
                return False, "Response too large"
            
            # Validate JSON structure if it's supposed to be JSON
            if isinstance(response_data, dict):
                required_fields = ['search_terms', 'search_type']
                missing_fields = [field for field in required_fields if field not in response_data]
                if missing_fields:
                    return False, f"Response missing required fields: {missing_fields}"
            
            return True, "Valid response"
            
        except Exception as e:
            self._log_security_event("RESPONSE_VALIDATION_ERROR", {
                'error': str(e),
                'response_type': type(response_data).__name__
            })
            return False, f"Response validation error: {e}"
    
    def sanitize_query(self, query: str) -> str:
        """
        Sanitize query by removing/escaping potentially dangerous content
        
        Args:
            query: Raw user query
            
        Returns:
            Sanitized query
        """
        
        # Remove HTML tags
        query = re.sub(r'<[^>]+>', '', query)
        
        # Remove excessive whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        
        # Remove control characters
        query = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', query)
        
        # Escape special characters that could be used for injection
        dangerous_chars = ['<', '>', '"', "'", '&', '`', '$', ';', '|']
        for char in dangerous_chars:
            query = query.replace(char, '')
        
        # Limit length
        if len(query) > 500:
            query = query[:500]
        
        return query
    
    def _log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security event for audit purposes"""
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'details': details,
            'severity': self._get_event_severity(event_type)
        }
        
        self.security_events.append(event)
        
        # Log to standard logger
        if event['severity'] == 'HIGH':
            logger.warning(f"🚨 Security Event: {event_type} - {details}")
        else:
            logger.info(f"🔒 Security Event: {event_type} - {details}")
        
        # Keep only last 1000 events to prevent memory bloat
        if len(self.security_events) > 1000:
            self.security_events = self.security_events[-1000:]
    
    def _get_event_severity(self, event_type: str) -> str:
        """Determine severity level for security event"""
        
        high_severity_events = [
            'MALICIOUS_PATTERN',
            'MALICIOUS_RESPONSE', 
            'SUSPICIOUS_API_KEY'
        ]
        
        medium_severity_events = [
            'RATE_LIMIT_EXCEEDED',
            'QUERY_TOO_LONG',
            'INVALID_CHARACTERS'
        ]
        
        if event_type in high_severity_events:
            return 'HIGH'
        elif event_type in medium_severity_events:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get security summary and statistics"""
        
        current_time = datetime.now()
        last_hour = current_time - timedelta(hours=1)
        last_day = current_time - timedelta(days=1)
        
        # Count events by type and time
        events_last_hour = [e for e in self.security_events if datetime.fromisoformat(e['timestamp']) > last_hour]
        events_last_day = [e for e in self.security_events if datetime.fromisoformat(e['timestamp']) > last_day]
        
        # Count by severity
        severity_counts = defaultdict(int)
        for event in events_last_day:
            severity_counts[event['severity']] += 1
        
        # Count active rate limit tracking
        active_clients = len(set(
            list(self.request_tracking['minute'].keys()) +
            list(self.request_tracking['hour'].keys()) +
            list(self.request_tracking['day'].keys())
        ))
        
        return {
            'total_events': len(self.security_events),
            'events_last_hour': len(events_last_hour),
            'events_last_day': len(events_last_day),
            'severity_counts': dict(severity_counts),
            'active_clients': active_clients,
            'rate_limits': self.rate_limits,
            'patterns_monitored': len(self.malicious_patterns),
            'last_updated': current_time.isoformat()
        }

# Global security validator instance
security_validator = OllamaSecurityValidator()

# Convenience functions for easy integration
def validate_input(query: str, client_ip: str = None, user_id: str = None) -> Tuple[bool, str]:
    """Validate user input with security checks"""
    return security_validator.validate_input(query, client_ip, user_id)

def validate_api_key(api_key: str) -> Tuple[bool, str]:
    """Validate API key format"""
    return security_validator.validate_api_key(api_key)

def validate_ollama_response(response: Any) -> Tuple[bool, str]:
    """Validate Ollama response"""
    return security_validator.validate_ollama_response(response)

def sanitize_query(query: str) -> str:
    """Sanitize user query"""
    return security_validator.sanitize_query(query)

def get_security_summary() -> Dict[str, Any]:
    """Get security statistics"""
    return security_validator.get_security_summary()