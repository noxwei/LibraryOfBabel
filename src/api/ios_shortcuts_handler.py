#!/usr/bin/env python3
"""
iOS Shortcuts Handler for LibraryOfBabel API
============================================

Handles mobile-optimized requests from iOS Shortcuts and Siri
Provides concise, voice-friendly responses with intentLabel routing
"""

import json
import logging
import time
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import psycopg2
import psycopg2.extras
import os
import sys
import requests

# Add src directory to path
current_dir = os.path.dirname(__file__)
src_dir = os.path.dirname(current_dir)
sys.path.insert(0, src_dir)

from ollama_url_generator import OllamaUrlGeneratorAgent

logger = logging.getLogger(__name__)

class IOSShortcutsHandler:
    """Handle iOS Shortcuts requests with mobile-optimized responses"""
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.ollama_agent = OllamaUrlGeneratorAgent()
        
        # Lexi personality for mobile voice interaction
        self.lexi_voice_persona = {
            'name': 'Lexi',
            'voice_style': 'concise_friendly',
            'max_response_length': 280,
            'use_emojis': True,
            'greeting_style': 'casual',
            'knowledge_base_size': '363 books',
            'personality_traits': [
                'helpful librarian',
                'data enthusiast', 
                'concise communicator',
                'mobile-first'
            ]
        }
        
        # Intent classification patterns for Shortcuts routing
        self.intent_patterns = {
            'search': ['find', 'search', 'look for', 'show me', 'what about'],
            'recommend': ['recommend', 'suggest', 'what should i read', 'good books'],
            'explain': ['explain', 'what is', 'tell me about', 'define'],
            'summary': ['summarize', 'summary', 'overview', 'brief'],
            'compare': ['compare', 'difference', 'versus', 'vs'],
            'quote': ['quote', 'quotes', 'citation', 'passage'],
            'help': ['help', 'how to', 'instructions', 'guide']
        }
        
        logger.info("🎤 iOS Shortcuts Handler initialized - Lexi Voice Mode ready!")
    
    def validate_mobile_request(self, request_data: Dict) -> Tuple[bool, str]:
        """Validate mobile request structure"""
        if not isinstance(request_data, dict):
            return False, "Request must be JSON object"
        
        required_fields = ['query']
        for field in required_fields:
            if field not in request_data:
                return False, f"Missing required field: {field}"
            if not isinstance(request_data[field], str):
                return False, f"Field {field} must be string"
            if not request_data[field].strip():
                return False, f"Field {field} cannot be empty"
        
        # Optional fields validation
        if 'context' in request_data:
            if not isinstance(request_data['context'], str):
                return False, "Context field must be string"
        
        if 'max_length' in request_data:
            if not isinstance(request_data['max_length'], int):
                return False, "max_length must be integer"
            if request_data['max_length'] < 50 or request_data['max_length'] > 1000:
                return False, "max_length must be between 50 and 1000"
        
        if 'compact' in request_data:
            if not isinstance(request_data['compact'], bool):
                return False, "compact field must be boolean"
        
        return True, "Valid request"
    
    def classify_intent(self, query: str) -> str:
        """Classify user intent for Shortcuts routing"""
        query_lower = query.lower()
        
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                return intent
        
        # Default intent
        return 'search'
    
    def search_knowledge_base(self, query: str, limit: int = 3) -> List[Dict]:
        """Search the knowledge base for relevant content"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    # Use PostgreSQL full-text search
                    cursor.execute("""
                        SELECT 
                            c.book_id,
                            b.title,
                            b.author,
                            c.content,
                            c.chapter_number,
                            ts_rank_cd(to_tsvector('english', c.content), plainto_tsquery('english', %s)) as rank
                        FROM chunks c
                        JOIN books b ON c.book_id = b.book_id
                        WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', %s)
                        ORDER BY rank DESC, c.chapter_number ASC
                        LIMIT %s
                    """, (query, query, limit))
                    
                    results = []
                    for row in cursor.fetchall():
                        results.append({
                            'book_id': row['book_id'],
                            'title': row['title'],
                            'author': row['author'],
                            'content': row['content'],
                            'chapter_number': row['chapter_number'],
                            'relevance_score': float(row['rank'])
                        })
                    
                    return results
                    
        except Exception as e:
            logger.error(f"Knowledge base search error: {e}")
            return []
    
    def generate_lexi_response(self, query: str, search_results: List[Dict], 
                             intent: str, max_length: int = 280, compact: bool = True) -> str:
        """Generate Lexi's mobile-optimized response"""
        
        # Base response based on intent
        if intent == 'help':
            response = "🎤 Hey! I'm Lexi, your AI librarian! Ask me about books, get summaries, or search 363 books instantly! 📚✨"
        elif not search_results:
            response = f"🔍 Hmm, couldn't find much on '{query}' in my 363 books. Try different keywords? 📚"
        else:
            # Generate response based on search results
            if intent == 'search':
                top_result = search_results[0]
                response = f"📖 Found in \"{top_result['title']}\" by {top_result['author']}: {top_result['content'][:150]}..."
            
            elif intent == 'recommend':
                books = list(set([(r['title'], r['author']) for r in search_results]))
                if len(books) == 1:
                    response = f"📚 I recommend \"{books[0][0]}\" by {books[0][1]} - perfect match for your interests!"
                else:
                    book_list = ", ".join([f"\"{b[0]}\"" for b in books[:2]])
                    response = f"📚 Top picks: {book_list}. Want more details on any of these?"
            
            elif intent == 'explain':
                top_result = search_results[0]
                response = f"💡 From \"{top_result['title']}\": {top_result['content'][:200]}..."
            
            elif intent == 'summary':
                response = f"📝 Quick summary from {len(search_results)} sources: {search_results[0]['content'][:180]}..."
            
            elif intent == 'compare':
                if len(search_results) >= 2:
                    response = f"⚖️ Comparison: \"{search_results[0]['title']}\" vs \"{search_results[1]['title']}\" - different perspectives on {query}!"
                else:
                    response = f"⚖️ Found one perspective in \"{search_results[0]['title']}\" - need more sources for comparison."
            
            elif intent == 'quote':
                top_result = search_results[0]
                response = f"💬 Quote from \"{top_result['title']}\": \"{top_result['content'][:150]}...\" - {top_result['author']}"
            
            else:
                # Default search response
                top_result = search_results[0]
                response = f"🔍 Found: \"{top_result['title']}\" by {top_result['author']} - {top_result['content'][:120]}..."
        
        # Truncate if needed
        if len(response) > max_length:
            response = response[:max_length-3] + "..."
        
        return response
    
    def generate_ollama_response(self, query: str, search_results: List[Dict], 
                               intent: str, max_length: int = 280) -> str:
        """Generate response using Ollama for complex queries"""
        try:
            # Prepare context from search results
            context = ""
            if search_results:
                context = "\n".join([f"From \"{r['title']}\" by {r['author']}: {r['content'][:300]}" 
                                   for r in search_results[:2]])
            
            # Create mobile-optimized prompt
            prompt = f"""You are Lexi, a helpful AI librarian. Answer concisely for mobile/voice use.
Query: {query}
Context from books: {context}

Respond in {max_length} chars max, be friendly and helpful. Use emojis sparingly."""
            
            # Call Ollama
            response = self.ollama_agent.generate_response(prompt)
            
            # Truncate if needed
            if len(response) > max_length:
                response = response[:max_length-3] + "..."
            
            return response
            
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            # Fallback to simple response
            return self.generate_lexi_response(query, search_results, intent, max_length)
    
    def process_mobile_request(self, request_data: Dict) -> Dict:
        """Process mobile request and generate iOS Shortcuts compatible response"""
        start_time = time.time()
        
        # Extract request parameters
        query = request_data['query'].strip()
        context = request_data.get('context', 'mobile_ios_shortcuts')
        max_length = request_data.get('max_length', 280)
        compact = request_data.get('compact', True)
        use_ollama = request_data.get('use_ollama', False)
        
        # Classify intent
        intent = self.classify_intent(query)
        
        # Search knowledge base
        search_results = self.search_knowledge_base(query, limit=3)
        
        # Generate response
        if use_ollama and search_results:
            response_text = self.generate_ollama_response(query, search_results, intent, max_length)
        else:
            response_text = self.generate_lexi_response(query, search_results, intent, max_length, compact)
        
        # Calculate processing time
        processing_time = round((time.time() - start_time) * 1000)
        
        # Build iOS Shortcuts compatible response
        response = {
            'success': True,
            'agent': 'lexi_voice_mode',
            'response': response_text,
            'intentLabel': intent,
            'metadata': {
                'query': query,
                'context': context,
                'results_count': len(search_results),
                'processing_time_ms': processing_time,
                'response_length': len(response_text),
                'max_length': max_length,
                'compact_mode': compact,
                'knowledge_base_size': self.lexi_voice_persona['knowledge_base_size']
            },
            'shortcuts_data': {
                'intent': intent,
                'has_results': len(search_results) > 0,
                'book_count': len(set(r['title'] for r in search_results)),
                'can_follow_up': intent in ['search', 'explain', 'recommend'],
                'voice_optimized': True
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Add search results if available
        if search_results and not compact:
            response['search_results'] = [
                {
                    'title': r['title'],
                    'author': r['author'],
                    'excerpt': r['content'][:200] + "..." if len(r['content']) > 200 else r['content'],
                    'relevance': round(r['relevance_score'], 3)
                }
                for r in search_results
            ]
        
        logger.info(f"📱 Mobile request processed: {query[:50]}... -> {intent} ({processing_time}ms)")
        
        return response
    
    def handle_error(self, error_message: str, error_type: str = "validation_error") -> Dict:
        """Handle errors with mobile-friendly responses"""
        return {
            'success': False,
            'error': error_message,
            'error_type': error_type,
            'agent': 'lexi_voice_mode',
            'response': "🤔 Oops! Something went wrong. Try rephrasing your question?",
            'intentLabel': 'error',
            'metadata': {
                'error_occurred': True,
                'error_message': error_message,
                'knowledge_base_size': self.lexi_voice_persona['knowledge_base_size']
            },
            'shortcuts_data': {
                'intent': 'error',
                'has_results': False,
                'voice_optimized': True
            },
            'timestamp': datetime.now().isoformat()
        }

def create_ios_shortcuts_handler(db_config: Dict) -> IOSShortcutsHandler:
    """Factory function to create iOS Shortcuts handler"""
    return IOSShortcutsHandler(db_config)

# Example usage for testing
if __name__ == "__main__":
    # Test configuration
    db_config = {
        'host': 'localhost',
        'database': 'knowledge_base',
        'user': 'weixiangzhang',
        'port': 5432
    }
    
    handler = create_ios_shortcuts_handler(db_config)
    
    # Test request
    test_request = {
        'query': 'find books about artificial intelligence',
        'context': 'mobile_ios_shortcuts',
        'max_length': 280,
        'compact': True
    }
    
    print("🧪 Testing iOS Shortcuts Handler...")
    response = handler.process_mobile_request(test_request)
    print(json.dumps(response, indent=2))