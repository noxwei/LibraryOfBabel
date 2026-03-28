#!/usr/bin/env python3
"""
🌐 SIMPLE MCP SERVER FOR LIBRARY OF BABEL - Phase 1 Implementation
================================================================

Simplified MCP server that works with existing Flask infrastructure.
Provides basic MCP functionality without external dependencies.

This implements the HTTP-based MCP pattern as outlined in our implementation plan.

Usage:
    python3 simple_mcp_server.py

Then integrate with main Flask API for production deployment.
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import psycopg2
import psycopg2.extras

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simple-mcp-server")

class SimpleMCPServer:
    """
    🚀 Simple MCP Server - Phase 1 Implementation
    
    Provides basic MCP functionality that can be integrated with existing Flask API.
    Focuses on multi-modal semantic search and real-time analytics.
    """
    
    def __init__(self):
        self.name = "library-of-babel"
        self.version = "1.0.0"
        self.db_config = {
            'host': 'localhost',
            'database': 'knowledge_base',
            'user': 'weixiangzhang',
            'password': os.environ.get('DB_PASSWORD')
        }
        logger.info("🌐 Simple MCP Server initialized")
        
    def get_server_info(self) -> Dict[str, Any]:
        """Get MCP server information"""
        return {
            "name": self.name,
            "version": self.version,
            "description": "LibraryOfBabel Multi-Modal MCP Server",
            "capabilities": {
                "tools": True,
                "resources": True,
                "multi_modal_search": True,
                "real_time_analytics": True
            },
            "models_supported": ["nomic", "bge", "mxbai", "arctic"],
            "llm_model": "gemma3:4b",
            "llm_model_mlx": "mlx-community/gemma-3-4b-it-4bit",
            "current_scale": "1.4M+ chunks processing"
        }
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List available MCP tools"""
        return [
            {
                "name": "semantic_search",
                "description": "Multi-modal semantic search across 1.4M+ chunks using 4 AI models",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "model_preference": {
                            "type": "string",
                            "enum": ["auto", "technical", "creative", "multilingual", "general"],
                            "default": "auto"
                        },
                        "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_library_analytics",
                "description": "Real-time LibraryOfBabel analytics and system metrics",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "include_processing": {"type": "boolean", "default": True},
                        "include_models": {"type": "boolean", "default": True}
                    },
                    "required": []
                }
            },
            {
                "name": "analyze_content_routing",
                "description": "Analyze content and recommend optimal AI model routing",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to analyze"},
                        "return_reasoning": {"type": "boolean", "default": True}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "search_books",
                "description": "Search books by metadata in the LibraryOfBabel collection",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "search_type": {
                            "type": "string", 
                            "enum": ["title", "author", "genre", "all"],
                            "default": "all"
                        },
                        "limit": {"type": "integer", "default": 20, "minimum": 1, "maximum": 100}
                    },
                    "required": ["query"]
                }
            }
        ]
    
    def list_resources(self) -> List[Dict[str, Any]]:
        """List available MCP resources"""
        return [
            {
                "uri": "library://metrics/realtime",
                "name": "Real-time System Metrics",
                "description": "Live multi-granular processing metrics",
                "mimeType": "application/json"
            },
            {
                "uri": "library://config/embedding-models",
                "name": "Embedding Models Configuration",
                "description": "4-model AI embedding system configuration", 
                "mimeType": "application/json"
            },
            {
                "uri": "library://analytics/processing-status",
                "name": "Processing Status Analytics",
                "description": "Current daemon and processing analytics",
                "mimeType": "application/json"
            }
        ]
    
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MCP tool"""
        try:
            if name == "semantic_search":
                return self._semantic_search(arguments)
            elif name == "get_library_analytics":
                return self._get_library_analytics(arguments)
            elif name == "analyze_content_routing":
                return self._analyze_content_routing(arguments)
            elif name == "search_books":
                return self._search_books(arguments)
            else:
                return {
                    "content": [{"type": "text", "text": f"Unknown tool: {name}"}],
                    "isError": True
                }
        except Exception as e:
            logger.error(f"Tool execution error [{name}]: {str(e)}")
            return {
                "content": [{"type": "text", "text": f"Error executing {name}: {str(e)}"}],
                "isError": True
            }
    
    def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read MCP resource"""
        try:
            if uri == "library://metrics/realtime":
                return {"content": self._get_realtime_metrics(), "mimeType": "application/json"}
            elif uri == "library://config/embedding-models":
                return {"content": self._get_embedding_config(), "mimeType": "application/json"}
            elif uri == "library://analytics/processing-status":
                return {"content": self._get_processing_analytics(), "mimeType": "application/json"}
            else:
                return {
                    "content": json.dumps({"error": f"Unknown resource: {uri}"}),
                    "mimeType": "application/json"
                }
        except Exception as e:
            logger.error(f"Resource read error [{uri}]: {str(e)}")
            return {
                "content": json.dumps({"error": str(e)}),
                "mimeType": "application/json"
            }
    
    def _semantic_search(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Multi-modal semantic search implementation"""
        query = args.get("query", "")
        model_pref = args.get("model_preference", "auto")
        limit = args.get("limit", 10)
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Enhanced search with content similarity
            search_sql = """
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
            
            result_text = f"🔍 **Multi-Modal Semantic Search**\\n\\n"
            result_text += f"**Query**: {query}\\n"
            result_text += f"**Model Preference**: {model_pref}\\n"
            result_text += f"**Results**: {len(results)} matches\\n\\n"
            
            if results:
                for i, result in enumerate(results, 1):
                    result_text += f"**{i}. {result['title']}** by {result['author']}\\n"
                    result_text += f"   Type: {result['chunk_type']} | Quality: {result['quality_score']:.2f}\\n"
                    result_text += f"   Similarity: {result['text_similarity']:.3f}\\n"
                    
                    # Content preview
                    content = result['content'][:200]
                    if len(result['content']) > 200:
                        content += "..."
                    result_text += f"   Content: {content}\\n\\n"
            else:
                result_text += "No matches found."
            
            cur.close()
            conn.close()
            
            return {"content": [{"type": "text", "text": result_text}]}
            
        except Exception as e:
            logger.error(f"Semantic search error: {str(e)}")
            return {
                "content": [{"type": "text", "text": f"Search failed: {str(e)}"}],
                "isError": True
            }
    
    def _get_library_analytics(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get real-time library analytics"""
        include_processing = args.get("include_processing", True)
        include_models = args.get("include_models", True)
        
        try:
            # Get database statistics
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            cur.execute("SELECT COUNT(*) FROM books")
            total_books = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM chunks WHERE content IS NOT NULL")
            total_chunks = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM chunks WHERE embedding_nomic IS NOT NULL")
            embedded_chunks = cur.fetchone()[0]
            
            result_text = "📊 **LibraryOfBabel Analytics**\\n\\n"
            result_text += f"**📚 Collection**\\n"
            result_text += f"• Books: {total_books:,}\\n"
            result_text += f"• Chunks: {total_chunks:,}\\n"
            result_text += f"• Embedded: {embedded_chunks:,}\\n"
            result_text += f"• Coverage: {(embedded_chunks/total_chunks*100):.1f}%\\n\\n"
            
            # Processing metrics
            if include_processing:
                try:
                    metrics_file = project_root / "logs" / "multi_granular_chunking" / "granular_metrics.json"
                    if metrics_file.exists():
                        with open(metrics_file, 'r') as f:
                            metrics_data = json.load(f)
                            metrics = metrics_data.get("metrics", {})
                            
                            result_text += f"**⚡ Real-Time Processing**\\n"
                            result_text += f"• Total Chunks: {metrics.get('multi_granular_total_chunks', 0):,}\\n"
                            result_text += f"• Expansion: {metrics.get('multi_granular_expansion_ratio', 0):.1f}x\\n"
                            result_text += f"• Rate: {metrics.get('multi_granular_processing_rate_chunks_per_second', 0):.2f}/sec\\n"
                            result_text += f"• Memory: {metrics.get('multi_granular_memory_usage_mb', 0):.1f}MB\\n\\n"
                except Exception as e:
                    result_text += f"**⚡ Processing**: Error loading metrics\\n\\n"
            
            # Model analytics
            if include_models:
                result_text += f"**🧠 AI Models**\\n"
                for model in ["nomic", "bge", "mxbai", "arctic"]:
                    cur.execute(f"SELECT COUNT(*) FROM chunks WHERE embedding_{model} IS NOT NULL")
                    count = cur.fetchone()[0]
                    coverage = (count/total_chunks*100) if total_chunks > 0 else 0
                    result_text += f"• {model.upper()}: {count:,} ({coverage:.1f}%)\\n"
            
            result_text += f"\\n**Updated**: {datetime.now().strftime('%H:%M:%S')}"
            
            cur.close()
            conn.close()
            
            return {"content": [{"type": "text", "text": result_text}]}
            
        except Exception as e:
            logger.error(f"Analytics error: {str(e)}")
            return {
                "content": [{"type": "text", "text": f"Analytics failed: {str(e)}"}],
                "isError": True
            }
    
    def _analyze_content_routing(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content for optimal model routing"""
        text = args.get("text", "")
        return_reasoning = args.get("return_reasoning", True)
        
        if not text:
            return {"content": [{"type": "text", "text": "No text provided"}]}
        
        # Simple content analysis
        text_lower = text.lower()
        
        # Content type indicators
        technical_keywords = ["algorithm", "database", "function", "method", "class", "api"]
        creative_keywords = ["story", "character", "narrative", "emotion", "dramatic"]
        
        technical_score = sum(1 for kw in technical_keywords if kw in text_lower)
        creative_score = sum(1 for kw in creative_keywords if kw in text_lower)
        
        # Simple multilingual detection
        multilingual_score = sum(1 for char in text if ord(char) > 127) / len(text) * 10
        
        # Determine recommendation
        if technical_score > max(creative_score, multilingual_score):
            model = "arctic"
            reason = "Technical content detected"
        elif creative_score > multilingual_score:
            model = "bge"
            reason = "Creative content detected"
        elif multilingual_score > 1:
            model = "mxbai"
            reason = "Multilingual content detected"
        else:
            model = "nomic"
            reason = "General content"
        
        result_text = f"🧠 **Content Routing Analysis**\\n\\n"
        result_text += f"**Recommended Model**: {model.upper()}\\n"
        result_text += f"**Reasoning**: {reason}\\n\\n"
        
        if return_reasoning:
            result_text += f"**Analysis**:\\n"
            result_text += f"• Technical score: {technical_score}\\n"
            result_text += f"• Creative score: {creative_score}\\n"
            result_text += f"• Multilingual score: {multilingual_score:.1f}\\n"
            result_text += f"• Text length: {len(text)} chars\\n\\n"
        
        result_text += f"**Preview**: {text[:100]}..."
        
        return {"content": [{"type": "text", "text": result_text}]}
    
    def _search_books(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search books by metadata"""
        query = args.get("query", "")
        search_type = args.get("search_type", "all")
        limit = args.get("limit", 20)
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Build search query
            if search_type == "title":
                sql = "SELECT * FROM books WHERE LOWER(title) LIKE LOWER(%s) ORDER BY title LIMIT %s"
                params = (f"%{query}%", limit)
            elif search_type == "author":
                sql = "SELECT * FROM books WHERE LOWER(author) LIKE LOWER(%s) ORDER BY author LIMIT %s"
                params = (f"%{query}%", limit)
            elif search_type == "genre":
                sql = "SELECT * FROM books WHERE LOWER(genre) LIKE LOWER(%s) ORDER BY genre LIMIT %s"
                params = (f"%{query}%", limit)
            else:  # all
                sql = """
                SELECT * FROM books 
                WHERE LOWER(title) LIKE LOWER(%s) 
                   OR LOWER(author) LIKE LOWER(%s)
                   OR LOWER(genre) LIKE LOWER(%s)
                ORDER BY title LIMIT %s
                """
                params = (f"%{query}%", f"%{query}%", f"%{query}%", limit)
            
            cur.execute(sql, params)
            books = cur.fetchall()
            
            result_text = f"📚 **Book Search Results**\\n\\n"
            result_text += f"**Query**: {query} ({search_type})\\n"
            result_text += f"**Found**: {len(books)} books\\n\\n"
            
            for book in books:
                result_text += f"**{book['title']}** by {book['author']}\\n"
                result_text += f"   ID: {book['book_id']} | Genre: {book['genre']}\\n\\n"
            
            if not books:
                result_text += "No books found."
            
            cur.close()
            conn.close()
            
            return {"content": [{"type": "text", "text": result_text}]}
            
        except Exception as e:
            logger.error(f"Book search error: {str(e)}")
            return {
                "content": [{"type": "text", "text": f"Search failed: {str(e)}"}],
                "isError": True
            }
    
    def _get_realtime_metrics(self) -> str:
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
    
    def _get_embedding_config(self) -> str:
        """Get embedding models configuration"""
        config = {
            "embedding_models": {
                "nomic":  {"name": "nomic-embed-text",      "dimensions": 768,  "use_case": "General fallback",         "context_tokens": 8192,  "backend": "ollama"},
                "bge":    {"name": "bge-m3",                "dimensions": 1024, "use_case": "Creative/Narrative",       "context_tokens": 8192,  "backend": "ollama", "mteb_score": 63.0, "rag_recall_at_10": "72%"},
                "mxbai":  {"name": "mxbai-embed-large",     "dimensions": 1024, "use_case": "Multilingual/Cultural",    "context_tokens": 512,   "backend": "ollama"},
                "arctic": {"name": "snowflake-arctic-embed", "dimensions": 1024, "use_case": "Technical/Academic",       "context_tokens": 4096,  "backend": "ollama"},
            },
            "llm_models": {
                "gemma3_4b":   {"name": "gemma3:4b",   "use_case": "Classification/Inference", "backend": "ollama", "tok_s_m2pro": "~110", "ram_gb": 3.0},
                "gemma3_4b_mlx": {"name": "mlx-community/gemma-3-4b-it-4bit", "use_case": "Classification/Inference (faster)", "backend": "mlx-lm", "tok_s_m2pro": "~110-130", "ram_gb": 2.5},
                "gemma3_12b":  {"name": "gemma3:12b",  "use_case": "High-quality classification", "backend": "ollama", "tok_s_m2pro": "~40", "ram_gb": 8.0},
                "gemma2_27b":  {"name": "gemma2:27b",  "use_case": "Maximum quality (int4)", "backend": "ollama", "tok_s_m2pro": "~20", "ram_gb": 14.5},
            },
            "planned_embedding_models": {
                "gemma3_embed": {
                    "name": "google/embedding-gemma",
                    "dimensions": 768,
                    "use_case": "General (MTEB #1 sub-500M)",
                    "context_tokens": 2048,
                    "backend": "sentence-transformers",
                    "status": "awaiting_ollama_support",
                    "note": "Outperforms bge-m3 on MTEB for <500M params but 2K context too small for full chapter embedding",
                },
            },
            "routing_strategy": "intelligent_content_classification",
            "last_updated": datetime.now().isoformat()
        }
        return json.dumps(config, indent=2)
    
    def _get_processing_analytics(self) -> str:
        """Get processing status analytics"""
        try:
            analytics = {"timestamp": datetime.now().isoformat()}
            
            # Get daemon status
            daemon_file = project_root / "logs" / "multi_modal_daemon" / "daemon_state.json"
            if daemon_file.exists():
                with open(daemon_file, 'r') as f:
                    analytics["daemon_status"] = json.load(f)
            
            return json.dumps(analytics, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

def main():
    """Test the simple MCP server"""
    server = SimpleMCPServer()
    
    print("🌐 Simple MCP Server Test")
    print("=" * 50)
    
    # Test server info
    info = server.get_server_info()
    print(f"Server: {info['name']} v{info['version']}")
    print(f"Scale: {info['current_scale']}")
    
    # Test tools list
    tools = server.list_tools()
    print(f"\\n🔧 Available Tools: {len(tools)}")
    for tool in tools:
        print(f"• {tool['name']}: {tool['description'][:50]}...")
    
    # Test resources list
    resources = server.list_resources()
    print(f"\\n📊 Available Resources: {len(resources)}")
    for resource in resources:
        print(f"• {resource['name']}")
    
    # Test analytics tool
    print("\\n📈 Testing Analytics Tool...")
    result = server.call_tool("get_library_analytics", {"include_processing": True})
    print("✅ Analytics tool working")
    
    print("\\n🎉 Simple MCP Server ready for integration!")

if __name__ == "__main__":
    main()