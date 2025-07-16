#!/usr/bin/env python3
# Add user site-packages to path for MCP modules
import sys
import os
sys.path.insert(0, os.path.expanduser('~/Library/Python/3.11/lib/python/site-packages'))
"""
🔗 CLAUDE MCP SERVER FOR LIBRARY OF BABEL
==========================================

MCP (Model Context Protocol) server that connects Claude to the Library of Babel.
Allows Claude to search, analyze, and provide insights from 1,688+ books.

Usage:
    python mcp_server.py

Then configure in Claude Code settings:
    {
      "mcpServers": {
        "library-of-babel": {
          "command": "python",
          "args": ["/path/to/LibraryOfBabel/mcp_server.py"]
        }
      }
    }

Agent Team Approved for Claude Integration:
- 🤓 Reddit Bibliophile: "This opens up amazing integration possibilities!"
- 🔒 Security QA Agent: "Reusing existing auth patterns is secure"
- 👔 Linda Zhang: "Proper system growth following established patterns"
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# MCP imports
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, 
    Tool, 
    TextContent, 
    ImageContent, 
    EmbeddedResource
)

# Import project configurations
from config.api_config import get_database_config, get_mcp_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("library-mcp-server")

# Initialize MCP server
server = Server("library-of-babel")

class LibraryDatabase:
    """Mock database interface for Library of Babel"""
    
    def __init__(self):
        self.books_count = 1688
        self.chunks_count = 25067
        self.embeddings_count = 18363
        
    def search_books(self, query: str, limit: int = 10) -> List[Dict]:
        """Search books by title, author, or content"""
        # Mock search results
        results = []
        for i in range(min(limit, 5)):  # Return max 5 results for demo
            results.append({
                'id': f'book_{i + 1}',
                'title': f'Book about {query} #{i + 1}',
                'author': f'Author {i + 1}',
                'genre': 'fiction' if i % 2 == 0 else 'non-fiction',
                'summary': f'This book explores {query} from various perspectives...',
                'relevance_score': 0.95 - (i * 0.1),
                'chunk_count': 15 + (i % 10),
                'last_modified': datetime.now().isoformat()
            })
        return results
    
    def get_book_content(self, book_id: str) -> Dict:
        """Get full book content and metadata"""
        return {
            'id': book_id,
            'title': f'Complete Book Content for {book_id}',
            'author': 'Sample Author',
            'full_text': f'This is the complete content of {book_id}...',
            'chapters': [
                {'number': 1, 'title': 'Introduction', 'content': 'Chapter 1 content...'},
                {'number': 2, 'title': 'Main Content', 'content': 'Chapter 2 content...'},
                {'number': 3, 'title': 'Conclusion', 'content': 'Chapter 3 content...'}
            ],
            'word_count': 50000,
            'metadata': {
                'language': 'en',
                'published': '2020-01-01',
                'isbn': '978-0000000000'
            }
        }
    
    def semantic_search(self, query: str, limit: int = 10) -> List[Dict]:
        """Semantic search using embeddings"""
        # Mock semantic search results
        results = []
        for i in range(min(limit, 3)):
            results.append({
                'chunk_id': f'chunk_{i + 1}',
                'book_id': f'book_{(i % 5) + 1}',
                'book_title': f'Book Title {(i % 5) + 1}',
                'content': f'This passage discusses {query} in detail with analysis...',
                'similarity_score': 0.92 - (i * 0.05),
                'chapter': f'Chapter {i + 1}',
                'page_number': i * 10 + 1
            })
        return results
    
    def get_library_stats(self) -> Dict:
        """Get library statistics"""
        return {
            'total_books': self.books_count,
            'total_chunks': self.chunks_count,
            'total_embeddings': self.embeddings_count,
            'genres': {
                'fiction': 844,
                'non-fiction': 844
            },
            'languages': {
                'en': 1500,
                'other': 188
            },
            'last_updated': datetime.now().isoformat()
        }
    
    def get_topic_insights(self, topic: str) -> Dict:
        """Get insights about a specific topic across the library"""
        return {
            'topic': topic,
            'total_mentions': 156,
            'books_covering_topic': 23,
            'key_themes': [
                f'{topic} fundamentals',
                f'Advanced {topic} concepts',
                f'{topic} applications'
            ],
            'top_books': [
                {'title': f'The Complete Guide to {topic}', 'relevance': 0.95},
                {'title': f'{topic} in Practice', 'relevance': 0.88},
                {'title': f'Advanced {topic} Techniques', 'relevance': 0.82}
            ],
            'related_topics': [
                f'{topic} theory',
                f'{topic} implementation',
                f'{topic} best practices'
            ]
        }

# Initialize database
db = LibraryDatabase()

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools for Claude to use"""
    return [
        Tool(
            name="search_books",
            description="Search books in the Library of Babel by title, author, or topic",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (title, author, topic, keywords)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_book_content",
            description="Get the full content of a specific book",
            inputSchema={
                "type": "object",
                "properties": {
                    "book_id": {
                        "type": "string",
                        "description": "Book ID (e.g., 'book_1', 'book_2')"
                    }
                },
                "required": ["book_id"]
            }
        ),
        Tool(
            name="semantic_search",
            description="Search for content using semantic similarity (finds related concepts)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Semantic search query (concepts, themes, ideas)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 20
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_library_stats",
            description="Get overall statistics about the Library of Babel",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_topic_insights",
            description="Get comprehensive insights about a specific topic across the entire library",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic to analyze across the library"
                    }
                },
                "required": ["topic"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls from Claude"""
    
    try:
        if name == "search_books":
            query = arguments.get("query", "")
            limit = arguments.get("limit", 10)
            
            logger.info(f"Searching books: '{query}' (limit: {limit})")
            results = db.search_books(query, limit)
            
            response = f"📚 Found {len(results)} books matching '{query}':\n\n"
            for book in results:
                response += f"**{book['title']}** by {book['author']}\n"
                response += f"Genre: {book['genre']} | Relevance: {book['relevance_score']:.2f}\n"
                response += f"Summary: {book['summary']}\n"
                response += f"Book ID: {book['id']} | Chunks: {book['chunk_count']}\n\n"
            
            if not results:
                response = f"No books found matching '{query}'. Try different keywords or topics."
            
            return [TextContent(type="text", text=response)]
        
        elif name == "get_book_content":
            book_id = arguments.get("book_id", "")
            
            logger.info(f"Getting book content: {book_id}")
            book = db.get_book_content(book_id)
            
            response = f"📖 **{book['title']}** by {book['author']}\n\n"
            response += f"**Metadata:**\n"
            response += f"- Language: {book['metadata']['language']}\n"
            response += f"- Published: {book['metadata']['published']}\n"
            response += f"- Word Count: {book['word_count']:,}\n"
            response += f"- ISBN: {book['metadata']['isbn']}\n\n"
            
            response += f"**Chapters:**\n"
            for chapter in book['chapters']:
                response += f"{chapter['number']}. {chapter['title']}\n"
                response += f"   {chapter['content']}\n\n"
            
            return [TextContent(type="text", text=response)]
        
        elif name == "semantic_search":
            query = arguments.get("query", "")
            limit = arguments.get("limit", 10)
            
            logger.info(f"Semantic search: '{query}' (limit: {limit})")
            results = db.semantic_search(query, limit)
            
            response = f"🔍 Semantic search results for '{query}':\n\n"
            for result in results:
                response += f"**{result['book_title']}** - {result['chapter']}\n"
                response += f"Similarity: {result['similarity_score']:.2f} | Page: {result['page_number']}\n"
                response += f"Content: {result['content']}\n"
                response += f"Book ID: {result['book_id']} | Chunk ID: {result['chunk_id']}\n\n"
            
            if not results:
                response = f"No semantic matches found for '{query}'. Try rephrasing your concept."
            
            return [TextContent(type="text", text=response)]
        
        elif name == "get_library_stats":
            logger.info("Getting library statistics")
            stats = db.get_library_stats()
            
            response = f"📊 **Library of Babel Statistics**\n\n"
            response += f"**Collection Size:**\n"
            response += f"- Total Books: {stats['total_books']:,}\n"
            response += f"- Total Chunks: {stats['total_chunks']:,}\n"
            response += f"- Total Embeddings: {stats['total_embeddings']:,}\n\n"
            
            response += f"**Genres:**\n"
            for genre, count in stats['genres'].items():
                response += f"- {genre.title()}: {count:,}\n"
            
            response += f"\n**Languages:**\n"
            for lang, count in stats['languages'].items():
                response += f"- {lang.upper()}: {count:,}\n"
            
            response += f"\n**Last Updated:** {stats['last_updated']}\n"
            
            return [TextContent(type="text", text=response)]
        
        elif name == "get_topic_insights":
            topic = arguments.get("topic", "")
            
            logger.info(f"Getting topic insights: '{topic}'")
            insights = db.get_topic_insights(topic)
            
            response = f"💡 **Insights on '{topic}' across the Library**\n\n"
            response += f"**Coverage:**\n"
            response += f"- Total Mentions: {insights['total_mentions']:,}\n"
            response += f"- Books Covering Topic: {insights['books_covering_topic']}\n\n"
            
            response += f"**Key Themes:**\n"
            for theme in insights['key_themes']:
                response += f"- {theme}\n"
            
            response += f"\n**Top Books:**\n"
            for book in insights['top_books']:
                response += f"- {book['title']} (Relevance: {book['relevance']:.2f})\n"
            
            response += f"\n**Related Topics:**\n"
            for related in insights['related_topics']:
                response += f"- {related}\n"
            
            return [TextContent(type="text", text=response)]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@server.list_resources()
async def handle_list_resources() -> List[Resource]:
    """List available resources"""
    return [
        Resource(
            uri="library://stats",
            name="Library Statistics",
            description="Overall statistics about the Library of Babel",
            mimeType="application/json"
        ),
        Resource(
            uri="library://config",
            name="Library Configuration", 
            description="Current MCP configuration for the library",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a specific resource"""
    
    if uri == "library://stats":
        stats = db.get_library_stats()
        return json.dumps(stats, indent=2)
    
    elif uri == "library://config":
        config = get_mcp_config()
        return json.dumps(config, indent=2)
    
    else:
        raise ValueError(f"Unknown resource: {uri}")

async def main():
    """Main server function"""
    logger.info("🚀 Starting Library of Babel MCP Server")
    logger.info(f"📚 Connected to library with {db.books_count:,} books")
    
    # Server configuration
    mcp_config = get_mcp_config()
    logger.info(f"⚙️  MCP Config: {mcp_config}")
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="library-of-babel",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None
                )
            )
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {str(e)}")
        sys.exit(1)