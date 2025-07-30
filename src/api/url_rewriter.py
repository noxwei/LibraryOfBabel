#!/usr/bin/env python3
"""
URL Rewriter for LibraryOfBabel API
===================================

Maps new path-segment endpoints to existing query-parameter endpoints
for backward compatibility and modern API design.
"""

from flask import request, redirect, url_for
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class URLRewriter:
    """URL rewriting layer for endpoint compatibility"""
    
    def __init__(self):
        # Mapping of new path-segment endpoints to query-parameter endpoints
        self.endpoint_mappings = {
            # Random content endpoints
            '/api/shortcuts/random/title': {'endpoint': '/api/shortcuts/random', 'params': {'type': 'title'}},
            '/api/shortcuts/random/author': {'endpoint': '/api/shortcuts/random', 'params': {'type': 'author'}},
            '/api/shortcuts/random/book': {'endpoint': '/api/shortcuts/random', 'params': {'type': 'book', 'include_metadata': 'true'}},
            '/api/shortcuts/random/citation': {'endpoint': '/api/shortcuts/random', 'params': {'type': 'citation'}},
            '/api/shortcuts/random/share-text': {'endpoint': '/api/shortcuts/random', 'params': {'type': 'share-text'}},
            
            # Statistics endpoints
            '/api/shortcuts/books/count': {'endpoint': '/api/shortcuts/stats', 'params': {'metric': 'book_count'}},
            '/api/shortcuts/stats/dashboard': {'endpoint': '/api/shortcuts/stats', 'params': {'metric': 'dashboard'}},
            
            # List endpoints
            '/api/shortcuts/books/title-list': {'endpoint': '/api/shortcuts/lists', 'params': {'type': 'titles'}},
            '/api/shortcuts/books/author-list': {'endpoint': '/api/shortcuts/lists', 'params': {'type': 'authors'}},
            
            # Serendipity endpoints
            '/api/shortcuts/serendipity/random-passage': {'endpoint': '/api/shortcuts/serendipity', 'params': {'action': 'passage'}},
            '/api/shortcuts/serendipity/mixed-authors': {'endpoint': '/api/shortcuts/serendipity', 'params': {'action': 'mixed-authors'}},
            '/api/shortcuts/serendipity/story-starter': {'endpoint': '/api/shortcuts/serendipity', 'params': {'action': 'story-starter'}},
            
            # User endpoints
            '/api/shortcuts/user/reading-progress': {'endpoint': '/api/shortcuts/user', 'params': {'action': 'reading-progress'}},
        }
        
        # Dynamic mappings for search endpoints
        self.search_patterns = [
            {
                'pattern': r'/api/shortcuts/search/([^/]+)/([^/]+)',
                'endpoint': '/api/shortcuts/search',
                'param_mapping': {'term': 1, 'action': 2}
            }
        ]
        
        # Dynamic mappings for book-specific endpoints
        self.book_patterns = [
            {
                'pattern': r'/api/shortcuts/books/(\d+)/summary',
                'endpoint': '/api/shortcuts/books',
                'param_mapping': {'id': 1, 'action': 'summary'}
            },
            {
                'pattern': r'/api/shortcuts/books/(\d+)/construct',
                'endpoint': '/api/shortcuts/books',
                'param_mapping': {'id': 1, 'action': 'construct'}
            },
            {
                'pattern': r'/api/shortcuts/books/(\d+)/toc',
                'endpoint': '/api/shortcuts/books',
                'param_mapping': {'id': 1, 'action': 'toc'}
            },
            {
                'pattern': r'/api/shortcuts/books/(\d+)/page/random',
                'endpoint': '/api/shortcuts/books',
                'param_mapping': {'id': 1, 'page': 'random'}
            },
            {
                'pattern': r'/api/shortcuts/books/(\d+)/page/(\d+)',
                'endpoint': '/api/shortcuts/books',
                'param_mapping': {'id': 1, 'page': 2}
            }
        ]
        
        # Dynamic mappings for theme blend endpoints
        self.theme_patterns = [
            {
                'pattern': r'/api/shortcuts/serendipity/theme-blend/([^/]+)',
                'endpoint': '/api/shortcuts/serendipity',
                'param_mapping': {'action': 'theme-blend', 'theme': 1}
            }
        ]
    
    def rewrite_url(self, path: str) -> dict:
        """Rewrite URL path to query parameters"""
        import re
        
        # Check exact matches first
        if path in self.endpoint_mappings:
            mapping = self.endpoint_mappings[path]
            return {
                'endpoint': mapping['endpoint'],
                'params': mapping['params'].copy()
            }
        
        # Check dynamic patterns
        all_patterns = self.search_patterns + self.book_patterns + self.theme_patterns
        
        for pattern_info in all_patterns:
            match = re.match(pattern_info['pattern'], path)
            if match:
                params = {}
                for param_name, group_index in pattern_info['param_mapping'].items():
                    if isinstance(group_index, int):
                        params[param_name] = match.group(group_index)
                    else:
                        params[param_name] = group_index
                
                return {
                    'endpoint': pattern_info['endpoint'],
                    'params': params
                }
        
        return None
    
    def apply_rewrite(self, app):
        """Apply URL rewriting to Flask app"""
        
        @app.before_request
        def rewrite_request():
            """Rewrite incoming requests"""
            path = request.path
            
            # Skip if already rewritten or is a static file
            if hasattr(request, '_rewritten') or path.startswith('/static/'):
                return
            
            rewrite_info = self.rewrite_url(path)
            if rewrite_info:
                logger.info(f"🔄 Rewriting {path} → {rewrite_info['endpoint']} with params {rewrite_info['params']}")
                
                # Update request path and args
                request.path = rewrite_info['endpoint']
                # Don't try to set endpoint - Flask will handle routing automatically
                
                # Add new parameters to existing args
                for key, value in rewrite_info['params'].items():
                    if key not in request.args:
                        # Create a new ImmutableMultiDict with the additional parameter
                        from werkzeug.datastructures import ImmutableMultiDict
                        new_args = dict(request.args)
                        new_args[key] = value
                        request.args = ImmutableMultiDict(new_args)
                
                # Mark as rewritten
                request._rewritten = True

def create_url_rewriter():
    """Create URL rewriter instance"""
    return URLRewriter() 