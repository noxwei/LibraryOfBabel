#!/usr/bin/env python3
"""
LibraryOfBabel MCP (Model Context Protocol) Integration
======================================================

Dr. Sarah Chen (陈雪芳) - MCP Server Capabilities
Provides MCP server configuration for Claude Desktop integration

MCP Specification: https://modelcontextprotocol.io/
"""

import os
from flask import Blueprint, jsonify, request
from .response_helpers import create_success_response, create_error_response
from .database import get_db
import logging

logger = logging.getLogger(__name__)

# Create MCP blueprint
standardized_mcp_bp = Blueprint('standardized_mcp', __name__)

@standardized_mcp_bp.route('/api/mcp', methods=['GET'])
def mcp_capabilities():
    """
    MCP Server Capabilities Endpoint
    Returns Model Context Protocol configuration for Claude Desktop
    """
    try:
        # Get current API statistics for MCP description
        conn = get_db()
        if not conn:
            book_count = "4,984"
            chunk_count = "2.36M"
        else:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM books")
                book_count = f"{cursor.fetchone()[0]:,}"
                
                cursor.execute("SELECT COUNT(*) FROM chunks")
                chunk_count = f"{cursor.fetchone()[0]:,}"
                
                cursor.close()
                conn.close()
            except Exception as e:
                logger.warning(f"Could not get live stats: {e}")
                book_count = "4,984"
                chunk_count = "2.36M"
        
        # MCP Server Configuration
        mcp_config = {
            "name": "LibraryOfBabel",
            "description": f"Semantic search across {book_count} books with {chunk_count} searchable chunks",
            "version": "1.0.0",
            "baseUrl": "https://api.ashortstayinhell.com:5562",
            "capabilities": [
                "semantic_search",
                "book_navigation", 
                "mobile_optimization",
                "real_time_statistics",
                "postgresql_first_architecture"
            ],
            "tools": [
                {
                    "name": "search_books",
                    "description": "Search across all books with semantic understanding",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "integer", "description": "Max results", "default": 10}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "get_book_info",
                    "description": "Get detailed information about a specific book",
                    "inputSchema": {
                        "type": "object", 
                        "properties": {
                            "book_id": {"type": "integer", "description": "Book ID"},
                            "action": {"type": "string", "enum": ["summary", "toc", "construct"], "default": "summary"}
                        },
                        "required": ["book_id"]
                    }
                },
                {
                    "name": "browse_books",
                    "description": "Browse and list available books",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "description": "Max results", "default": 20},
                            "page": {"type": "integer", "description": "Page number", "default": 1}
                        }
                    }
                },
                {
                    "name": "get_random_content",
                    "description": "Get random titles, authors, or citations",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["title", "author", "citation", "share"], "default": "title"}
                        }
                    }
                }
            ],
            "resources": [
                {
                    "uri": "library://books",
                    "name": "Book Collection",
                    "description": f"Access to {book_count} books in the library"
                },
                {
                    "uri": "library://search",
                    "name": "Semantic Search",
                    "description": f"AI-powered search across {chunk_count} text chunks"
                },
                {
                    "uri": "library://statistics", 
                    "name": "Library Statistics",
                    "description": "Real-time library health and usage metrics"
                }
            ],
            "authentication": {
                "type": "api_key",
                "header": "X-API-Key",
                "required": True,
                "note": "Contact support@ashortstayinhell.com for API access"
            },
            "endpoints": {
                "search": "/api/search?q={query}&limit={limit}",
                "books": "/api/books?action={action}&id={book_id}",
                "browse": "/api/books?action=list&limit={limit}&page={page}",
                "random": "/api/mobile/random?type={type}",
                "health": "/health"
            },
            "claude_desktop_config": {
                "mcpServers": {
                    "LibraryOfBabel": {
                        "command": "python",
                        "args": ["-m", "mcp_client"],
                        "env": {
                            "BABEL_API_URL": "https://api.ashortstayinhell.com:5562",
                            "BABEL_API_KEY": "YOUR_API_KEY_HERE"
                        }
                    }
                }
            }
        }
        
        return create_success_response(mcp_config, message="MCP server capabilities retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting MCP capabilities: {e}")
        return create_error_response("Failed to retrieve MCP capabilities", "INTERNAL_SERVER_ERROR", status_code=500)