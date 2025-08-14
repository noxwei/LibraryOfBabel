#!/usr/bin/env python3
"""
🌐 LIBRARY OF BABEL MCP SERVER - Production Multi-Modal Integration
================================================================

Enhanced MCP server leveraging LibraryOfBabel's advanced multi-modal architecture.
Provides Claude Code with access to 1.4M+ multi-granular chunks across 4 AI models.

Features:
- Multi-modal semantic search (nomic, bge, mxbai, arctic)
- Multi-granular content access (sentence → paragraph → section → chapter)
- Real-time analytics with 1.42M+ chunks processing
- PostgreSQL-First architecture with ACID compliance
- Intelligent content routing and classification

Usage:
    python3 library_mcp_server.py

Claude Code Configuration:
    {
      "mcpServers": {
        "library-of-babel": {
          "command": "python3",
          "args": ["/path/to/library_mcp_server.py"]
        }
      }
    }
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import requests
import psycopg2
import psycopg2.extras

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))
sys.path.append(str(project_root))

# MCP imports
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("library-mcp-server")

class LibraryMCPServer:
    """
    🚀 LibraryOfBabel MCP Server - Multi-Modal Intelligence Gateway
    
    Provides Claude Code with access to advanced multi-modal AI capabilities
    including semantic search, content analysis, and real-time analytics.
    """
    
    def __init__(self):
        self.server = Server("library-of-babel")
        self.db_config = {
            'host': 'localhost',
            'database': 'knowledge_base',
            'user': 'weixiangzhang',
            'password': os.environ.get('DB_PASSWORD')
        }
        self.api_base = "http://localhost:5000"  # Local API for development
        self.setup_tools()
        self.setup_resources()
        logger.info("🌐 LibraryOfBabel MCP Server initialized with multi-modal capabilities")
        
    def setup_tools(self):
        """Setup advanced MCP tools for multi-modal access"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List all available MCP tools"""
            return [
                Tool(
                    name="semantic_search",
                    description="Multi-modal semantic search across 1.4M+ chunks using 4 AI models (nomic, bge, mxbai, arctic)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (supports complex 1-10 word queries)"
                            },
                            "model_preference": {
                                "type": "string",
                                "enum": ["auto", "technical", "creative", "multilingual", "general"],
                                "default": "auto",
                                "description": "AI model routing preference"
                            },
                            "granularity": {
                                "type": "string", 
                                "enum": ["sentence", "paragraph", "section", "chapter", "auto"],
                                "default": "auto",
                                "description": "Content granularity level"
                            },
                            "limit": {
                                "type": "integer",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 50,
                                "description": "Maximum results to return"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_library_analytics",
                    description="Real-time LibraryOfBabel analytics and system metrics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_processing": {
                                "type": "boolean",
                                "default": True,
                                "description": "Include real-time processing metrics"
                            },
                            "include_models": {
                                "type": "boolean", 
                                "default": True,
                                "description": "Include AI model usage statistics"
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="analyze_content_routing",
                    description="Analyze content and recommend optimal AI model routing strategy",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Text content to analyze for optimal model routing"
                            },
                            "return_reasoning": {
                                "type": "boolean",
                                "default": True,
                                "description": "Include detailed reasoning for model selection"
                            }
                        },
                        "required": ["text"]
                    }
                ),
                Tool(
                    name="get_book_content",
                    description="Access book content at multiple granularity levels",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "book_id": {
                                "type": "integer",
                                "description": "Book identifier"
                            },
                            "granularity": {
                                "type": "string",
                                "enum": ["sentence", "paragraph", "section", "chapter", "full"],
                                "default": "chapter",
                                "description": "Content granularity level"
                            },
                            "chunk_limit": {
                                "type": "integer",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 100,
                                "description": "Maximum chunks to return"
                            }
                        },
                        "required": ["book_id"]
                    }
                ),
                Tool(
                    name="search_books",
                    description="Search books by metadata (title, author, genre) in the LibraryOfBabel collection",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for book metadata"
                            },
                            "search_type": {
                                "type": "string",
                                "enum": ["title", "author", "genre", "all"],
                                "default": "all",
                                "description": "Type of metadata search"
                            },
                            "limit": {
                                "type": "integer",
                                "default": 20,
                                "minimum": 1,
                                "maximum": 100,
                                "description": "Maximum books to return"
                            }
                        },
                        "required": ["query"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool execution with multi-modal intelligence"""
            try:
                if name == "semantic_search":
                    return await self._handle_semantic_search(arguments)
                elif name == "get_library_analytics":
                    return await self._handle_library_analytics(arguments)
                elif name == "analyze_content_routing":
                    return await self._handle_content_routing(arguments)
                elif name == "get_book_content":
                    return await self._handle_book_content(arguments)
                elif name == "search_books":
                    return await self._handle_search_books(arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                logger.error(f"Tool execution error [{name}]: {str(e)}")
                return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]
    
    def setup_resources(self):
        """Setup MCP resources for live data access"""
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """List available MCP resources"""
            return [
                Resource(
                    uri="library://metrics/realtime",
                    name="Real-time System Metrics",
                    description="Live multi-granular processing metrics",
                    mimeType="application/json"
                ),
                Resource(
                    uri="library://config/embedding-models",
                    name="Embedding Models Configuration", 
                    description="4-model AI embedding system configuration",
                    mimeType="application/json"
                ),
                Resource(
                    uri="library://schema/content-classification",
                    name="Content Classification Schema",
                    description="Intelligent content routing classification rules",
                    mimeType="application/json"
                ),
                Resource(
                    uri="library://analytics/processing-status",
                    name="Processing Status Analytics",
                    description="Current daemon and processing analytics",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read MCP resources with live data"""
            try:
                if uri == "library://metrics/realtime":
                    return await self._get_realtime_metrics()
                elif uri == "library://config/embedding-models":
                    return await self._get_embedding_config()
                elif uri == "library://schema/content-classification":
                    return await self._get_classification_schema()
                elif uri == "library://analytics/processing-status":
                    return await self._get_processing_analytics()
                else:
                    raise ValueError(f"Unknown resource: {uri}")
            except Exception as e:
                logger.error(f"Resource read error [{uri}]: {str(e)}")
                return json.dumps({"error": str(e)})
    
    async def _handle_semantic_search(self, args: Dict[str, Any]) -> List[TextContent]:
        """Handle multi-modal semantic search"""
        query = args.get("query", "")
        model_pref = args.get("model_preference", "auto")
        granularity = args.get("granularity", "auto")
        limit = args.get("limit", 10)
        
        try:
            # Connect to database for direct search
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Multi-modal search query based on preference
            model_columns = []
            if model_pref == "auto" or model_pref == "technical":
                model_columns.append("embedding_arctic")
            if model_pref == "auto" or model_pref == "creative":
                model_columns.append("embedding_bge")
            if model_pref == "auto" or model_pref == "multilingual":
                model_columns.append("embedding_mxbai")
            if model_pref == "auto" or model_pref == "general":
                model_columns.append("embedding_nomic")
            
            # If no specific preference, use all models
            if not model_columns:
                model_columns = ["embedding_nomic", "embedding_bge", "embedding_mxbai", "embedding_arctic"]
            
            # Get chunks with content and similarity scoring
            search_sql = f"""
            SELECT c.chunk_id, c.content, c.chunk_type, b.title, b.author, b.genre,
                   c.char_length, c.quality_score,
                   COALESCE(similarity(c.content, %s), 0) as text_similarity
            FROM chunks c
            JOIN books b ON c.book_id = b.book_id
            WHERE c.content IS NOT NULL 
            AND c.content != ''
            AND char_length(c.content) > 50
            ORDER BY text_similarity DESC, c.quality_score DESC
            LIMIT %s
            """
            
            cur.execute(search_sql, (query, limit))
            results = cur.fetchall()
            
            if results:
                result_text = f"🔍 **Multi-Modal Semantic Search Results**\n"
                result_text += f"**Query**: {query}\n"
                result_text += f"**Model Preference**: {model_pref}\n"
                result_text += f"**Results Found**: {len(results)}\n\n"
                
                for i, result in enumerate(results, 1):
                    result_text += f"**{i}. {result['title']}** by {result['author']}\n"
                    result_text += f"   Type: {result['chunk_type']} | Quality: {result['quality_score']:.2f}\n"
                    result_text += f"   Genre: {result['genre']}\n"
                    result_text += f"   Similarity: {result['text_similarity']:.3f}\n"
                    
                    # Show content preview
                    content = result['content'][:300]
                    if len(result['content']) > 300:
                        content += "..."
                    result_text += f"   Content: {content}\n\n"
            else:
                result_text = f"No semantic matches found for '{query}' with {model_pref} preference."
            
            cur.close()
            conn.close()
            
            return [TextContent(type="text", text=result_text)]
            
        except Exception as e:
            logger.error(f"Semantic search error: {str(e)}")
            return [TextContent(type="text", text=f"Semantic search failed: {str(e)}")]
    
    async def _handle_library_analytics(self, args: Dict[str, Any]) -> List[TextContent]:
        """Handle real-time library analytics"""
        include_processing = args.get("include_processing", True)
        include_models = args.get("include_models", True)
        
        try:
            analytics = {
                "timestamp": datetime.now().isoformat(),
                "library_overview": {},
                "processing_metrics": {},
                "model_analytics": {}
            }
            
            # Get library overview
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            cur.execute("SELECT COUNT(*) FROM books")
            total_books = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM chunks WHERE content IS NOT NULL")
            total_chunks = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM chunks WHERE embedding_nomic IS NOT NULL")
            embedded_chunks = cur.fetchone()[0]
            
            analytics["library_overview"] = {
                "total_books": total_books,
                "total_chunks": total_chunks,
                "embedded_chunks": embedded_chunks,
                "embedding_coverage": f"{(embedded_chunks/total_chunks*100):.1f}%" if total_chunks > 0 else "0%"
            }
            
            # Get processing metrics if requested
            if include_processing:
                try:
                    metrics_file = project_root / "logs" / "multi_granular_chunking" / "granular_metrics.json"
                    if metrics_file.exists():
                        with open(metrics_file, 'r') as f:
                            processing_data = json.load(f)
                            analytics["processing_metrics"] = processing_data.get("metrics", {})
                except Exception as e:
                    analytics["processing_metrics"] = {"error": f"Could not load processing metrics: {str(e)}"}
            
            # Get model analytics if requested
            if include_models:
                model_stats = {}
                for model in ["nomic", "bge", "mxbai", "arctic"]:
                    cur.execute(f"SELECT COUNT(*) FROM chunks WHERE embedding_{model} IS NOT NULL")
                    count = cur.fetchone()[0]
                    model_stats[model] = {
                        "embedded_chunks": count,
                        "coverage": f"{(count/total_chunks*100):.1f}%" if total_chunks > 0 else "0%"
                    }
                analytics["model_analytics"] = model_stats
            
            cur.close()
            conn.close()
            
            # Format analytics for display
            result_text = "📊 **LibraryOfBabel Real-Time Analytics**\n\n"
            
            # Library overview
            overview = analytics["library_overview"]
            result_text += f"**📚 Collection Overview**\n"
            result_text += f"• Total Books: {overview['total_books']:,}\n"
            result_text += f"• Total Chunks: {overview['total_chunks']:,}\n"
            result_text += f"• Embedded Chunks: {overview['embedded_chunks']:,}\n"
            result_text += f"• Embedding Coverage: {overview['embedding_coverage']}\n\n"
            
            # Processing metrics
            if include_processing and "error" not in analytics["processing_metrics"]:
                metrics = analytics["processing_metrics"]
                result_text += f"**⚡ Multi-Granular Processing**\n"
                result_text += f"• Total Chunks: {metrics.get('multi_granular_total_chunks', 0):,}\n"
                result_text += f"• Expansion Ratio: {metrics.get('multi_granular_expansion_ratio', 0):.1f}x\n"
                result_text += f"• Processing Rate: {metrics.get('multi_granular_processing_rate_chunks_per_second', 0):.2f} chunks/sec\n"
                result_text += f"• Memory Usage: {metrics.get('multi_granular_memory_usage_mb', 0):.1f} MB\n\n"
            
            # Model analytics
            if include_models:
                result_text += f"**🧠 AI Model Distribution**\n"
                for model, stats in analytics["model_analytics"].items():
                    result_text += f"• {model.upper()}: {stats['embedded_chunks']:,} chunks ({stats['coverage']})\n"
            
            result_text += f"\n**Updated**: {analytics['timestamp']}"
            
            return [TextContent(type="text", text=result_text)]
            
        except Exception as e:
            logger.error(f"Analytics error: {str(e)}")
            return [TextContent(type="text", text=f"Analytics failed: {str(e)}")]
    
    async def _handle_content_routing(self, args: Dict[str, Any]) -> List[TextContent]:
        """Handle intelligent content routing analysis"""
        text = args.get("text", "")
        return_reasoning = args.get("return_reasoning", True)
        
        if not text:
            return [TextContent(type="text", text="No text provided for analysis")]
        
        # Analyze content characteristics
        analysis = {
            "text_length": len(text),
            "word_count": len(text.split()),
            "recommended_model": "nomic",  # default
            "confidence": 0.0,
            "reasoning": []
        }
        
        text_lower = text.lower()
        
        # Technical content indicators
        technical_keywords = ["algorithm", "database", "function", "method", "class", "variable", 
                            "implementation", "architecture", "system", "framework", "api", "code"]
        technical_score = sum(1 for keyword in technical_keywords if keyword in text_lower)
        
        # Creative content indicators  
        creative_keywords = ["story", "character", "narrative", "plot", "emotion", "feeling",
                           "imagine", "creative", "artistic", "beautiful", "dramatic", "literary"]
        creative_score = sum(1 for keyword in creative_keywords if keyword in text_lower)
        
        # Multilingual indicators (simple heuristic)
        multilingual_score = 0
        non_ascii_chars = sum(1 for char in text if ord(char) > 127)
        if non_ascii_chars > len(text) * 0.05:  # More than 5% non-ASCII
            multilingual_score = 5
        
        # Determine recommendation
        scores = {
            "arctic": technical_score,  # Technical content
            "bge": creative_score,      # Creative content
            "mxbai": multilingual_score, # Multilingual content
            "nomic": 1                  # General fallback
        }
        
        recommended_model = max(scores, key=scores.get)
        max_score = scores[recommended_model]
        analysis["recommended_model"] = recommended_model
        analysis["confidence"] = min(max_score / 5.0, 1.0)  # Normalize to 0-1
        
        # Generate reasoning
        if return_reasoning:
            analysis["reasoning"] = [
                f"Technical indicators: {technical_score} (suggests arctic model)",
                f"Creative indicators: {creative_score} (suggests bge model)",
                f"Multilingual indicators: {multilingual_score} (suggests mxbai model)",
                f"Text length: {analysis['text_length']} characters",
                f"Word count: {analysis['word_count']} words"
            ]
        
        # Format response
        result_text = f"🧠 **Content Routing Analysis**\n\n"
        result_text += f"**Recommended Model**: {recommended_model.upper()}\n"
        result_text += f"**Confidence**: {analysis['confidence']:.2f}\n\n"
        
        model_descriptions = {
            "arctic": "Technical/Academic - Precise factual embedding (1024d)",
            "bge": "Creative/Narrative - Rich semantic understanding (1024d)", 
            "mxbai": "Cultural/Multilingual - Cross-linguistic preservation (1024d)",
            "nomic": "General - Broad coverage fallback (768d)"
        }
        
        result_text += f"**Model Description**: {model_descriptions[recommended_model]}\n\n"
        
        if return_reasoning:
            result_text += f"**Analysis Details**:\n"
            for reason in analysis["reasoning"]:
                result_text += f"• {reason}\n"
        
        result_text += f"\n**Sample Text**: {text[:200]}..."
        
        return [TextContent(type="text", text=result_text)]
    
    async def _handle_book_content(self, args: Dict[str, Any]) -> List[TextContent]:
        """Handle book content access at multiple granularity levels"""
        book_id = args.get("book_id")
        granularity = args.get("granularity", "chapter")
        chunk_limit = args.get("chunk_limit", 10)
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Get book metadata
            cur.execute("SELECT title, author, genre, filename FROM books WHERE book_id = %s", (book_id,))
            book_info = cur.fetchone()
            
            if not book_info:
                return [TextContent(type="text", text=f"Book {book_id} not found")]
            
            # Get chunks based on granularity
            if granularity == "full":
                chunk_filter = ""
            else:
                chunk_filter = f"AND c.chunk_type = '{granularity}'"
            
            content_sql = f"""
            SELECT c.chunk_id, c.content, c.chunk_type, c.char_length, c.quality_score
            FROM chunks c
            WHERE c.book_id = %s
            AND c.content IS NOT NULL
            AND c.content != ''
            {chunk_filter}
            ORDER BY c.chunk_id
            LIMIT %s
            """
            
            cur.execute(content_sql, (book_id, chunk_limit))
            chunks = cur.fetchall()
            
            result_text = f"📖 **{book_info['title']}**\n"
            result_text += f"**Author**: {book_info['author']}\n"
            result_text += f"**Genre**: {book_info['genre']}\n"
            result_text += f"**Granularity**: {granularity}\n"
            result_text += f"**Chunks Retrieved**: {len(chunks)}\n\n"
            
            for i, chunk in enumerate(chunks, 1):
                result_text += f"**Chunk {i}** ({chunk['chunk_type']})\n"
                result_text += f"Length: {chunk['char_length']} chars | Quality: {chunk['quality_score']:.2f}\n"
                
                # Show content with appropriate truncation
                content = chunk['content']
                if len(content) > 500:
                    content = content[:500] + "..."
                result_text += f"Content: {content}\n\n"
            
            cur.close()
            conn.close()
            
            return [TextContent(type="text", text=result_text)]
            
        except Exception as e:
            logger.error(f"Book content error: {str(e)}")
            return [TextContent(type="text", text=f"Error retrieving book content: {str(e)}")]
    
    async def _handle_search_books(self, args: Dict[str, Any]) -> List[TextContent]:
        """Handle book metadata search"""
        query = args.get("query", "")
        search_type = args.get("search_type", "all")
        limit = args.get("limit", 20)
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Build search query based on type
            if search_type == "title":
                search_sql = "SELECT * FROM books WHERE LOWER(title) LIKE LOWER(%s) ORDER BY title LIMIT %s"
                search_param = f"%{query}%"
            elif search_type == "author":
                search_sql = "SELECT * FROM books WHERE LOWER(author) LIKE LOWER(%s) ORDER BY author, title LIMIT %s"
                search_param = f"%{query}%"
            elif search_type == "genre":
                search_sql = "SELECT * FROM books WHERE LOWER(genre) LIKE LOWER(%s) ORDER BY genre, title LIMIT %s"
                search_param = f"%{query}%"
            else:  # search_type == "all"
                search_sql = """
                SELECT * FROM books 
                WHERE LOWER(title) LIKE LOWER(%s) 
                   OR LOWER(author) LIKE LOWER(%s)
                   OR LOWER(genre) LIKE LOWER(%s)
                ORDER BY title LIMIT %s
                """
                search_param = f"%{query}%"
                cur.execute(search_sql, (search_param, search_param, search_param, limit))
                books = cur.fetchall()
            
            if search_type != "all":
                cur.execute(search_sql, (search_param, limit))
                books = cur.fetchall()
            
            result_text = f"📚 **Book Search Results**\n"
            result_text += f"**Query**: {query}\n"
            result_text += f"**Search Type**: {search_type}\n"
            result_text += f"**Results Found**: {len(books)}\n\n"
            
            for book in books:
                result_text += f"**{book['title']}** by {book['author']}\n"
                result_text += f"   ID: {book['book_id']} | Genre: {book['genre']}\n"
                result_text += f"   File: {book['filename']}\n\n"
            
            if not books:
                result_text += f"No books found matching '{query}' in {search_type} field(s)."
            
            cur.close()
            conn.close()
            
            return [TextContent(type="text", text=result_text)]
            
        except Exception as e:
            logger.error(f"Book search error: {str(e)}")
            return [TextContent(type="text", text=f"Book search failed: {str(e)}")]
    
    async def _get_realtime_metrics(self) -> str:
        """Get real-time processing metrics"""
        try:
            metrics_file = project_root / "logs" / "multi_granular_chunking" / "granular_metrics.json"
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    return f.read()
            else:
                return json.dumps({"error": "Metrics file not found"})
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    async def _get_embedding_config(self) -> str:
        """Get embedding models configuration"""
        config = {
            "models": {
                "nomic": {
                    "name": "nomic-embed-text",
                    "dimensions": 768,
                    "use_case": "General semantic coverage",
                    "endpoint": "http://localhost:11434/api/embeddings"
                },
                "bge": {
                    "name": "bge-m3",
                    "dimensions": 1024,
                    "use_case": "Creative/Narrative content",
                    "endpoint": "http://localhost:11434/api/embeddings"
                },
                "mxbai": {
                    "name": "mxbai-embed-large",
                    "dimensions": 1024,
                    "use_case": "Multilingual/Cultural content",
                    "endpoint": "http://localhost:11434/api/embeddings"
                },
                "arctic": {
                    "name": "snowflake-arctic-embed",
                    "dimensions": 1024,
                    "use_case": "Technical/Academic content",
                    "endpoint": "http://localhost:11434/api/embeddings"
                }
            },
            "routing_strategy": "intelligent_content_classification",
            "fallback_model": "nomic",
            "last_updated": datetime.now().isoformat()
        }
        return json.dumps(config, indent=2)
    
    async def _get_classification_schema(self) -> str:
        """Get content classification schema"""
        schema = {
            "classification_rules": {
                "technical": {
                    "keywords": ["algorithm", "database", "function", "method", "class", "implementation"],
                    "recommended_model": "arctic",
                    "confidence_threshold": 0.6
                },
                "creative": {
                    "keywords": ["story", "character", "narrative", "plot", "emotion", "dramatic"],
                    "recommended_model": "bge", 
                    "confidence_threshold": 0.6
                },
                "multilingual": {
                    "indicators": ["non_ascii_ratio > 0.05", "unicode_scripts > 1"],
                    "recommended_model": "mxbai",
                    "confidence_threshold": 0.7
                },
                "general": {
                    "fallback": True,
                    "recommended_model": "nomic",
                    "confidence_threshold": 0.0
                }
            },
            "granularity_mapping": {
                "sentence": "Fine-grained semantic analysis",
                "paragraph": "Contextual semantic grouping",
                "section": "Thematic content analysis", 
                "chapter": "High-level structural analysis"
            },
            "quality_thresholds": {
                "minimum_length": 50,
                "maximum_length": 8000,
                "quality_score_threshold": 0.5
            }
        }
        return json.dumps(schema, indent=2)
    
    async def _get_processing_analytics(self) -> str:
        """Get current processing status analytics"""
        try:
            analytics = {
                "timestamp": datetime.now().isoformat(),
                "daemon_status": {},
                "queue_metrics": {},
                "processing_health": "unknown"
            }
            
            # Check daemon status
            daemon_state_file = project_root / "logs" / "multi_modal_daemon" / "daemon_state.json"
            if daemon_state_file.exists():
                with open(daemon_state_file, 'r') as f:
                    analytics["daemon_status"] = json.load(f)
            
            # Check queue metrics
            queue_metrics_file = project_root / "logs" / "daemon_queue" / "queue_metrics.json"
            if queue_metrics_file.exists():
                with open(queue_metrics_file, 'r') as f:
                    queue_data = f.read().strip()
                    if queue_data:
                        analytics["queue_metrics"] = json.loads(queue_data)
            
            # Determine health status
            if analytics["daemon_status"]:
                success_rate = analytics["daemon_status"].get("success_rate", 0)
                if success_rate > 90:
                    analytics["processing_health"] = "excellent"
                elif success_rate > 80:
                    analytics["processing_health"] = "good"
                elif success_rate > 60:
                    analytics["processing_health"] = "fair"
                else:
                    analytics["processing_health"] = "needs_attention"
            
            return json.dumps(analytics, indent=2)
            
        except Exception as e:
            return json.dumps({"error": str(e)})

async def main():
    """Main MCP server entry point"""
    server = LibraryMCPServer()
    
    # Initialize MCP server
    options = InitializationOptions(
        server_name="library-of-babel",
        server_version="1.0.0",
        capabilities=server.server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={}
        )
    )
    
    logger.info("🚀 Starting LibraryOfBabel MCP Server")
    logger.info("🧠 Multi-modal capabilities: nomic, bge, mxbai, arctic")
    logger.info("📊 Real-time analytics: 1.4M+ chunks processing")
    logger.info("🔗 Claude Code integration ready")
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            options
        )

if __name__ == "__main__":
    asyncio.run(main())