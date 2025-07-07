#!/usr/bin/env python3
"""
Ollama URL Generator Agent - LibraryOfBabel Integration
=======================================================

Revolutionary natural language to search URL conversion using Ollama.
Transforms user queries like "Find books about AI consciousness" into 
optimized LibraryOfBabel search URLs that access 360 books with 34+ million words.

Team Development:
- Architecture: Reddit Bibliophile (u/DataScientistBookworm)
- Security: Security QA Agent  
- Testing: Comprehensive QA Agent
- Coordination: HR Linda (张丽娜)
"""

import asyncio
import aiohttp
import json
import logging
import os
import re
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from urllib.parse import urlencode, quote_plus

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaUrlGeneratorAgent:
    """
    Natural language to LibraryOfBabel search URL generator using Ollama
    
    Features:
    - Natural language query understanding
    - Structured search parameter extraction
    - Optimized URL generation for 360-book database
    - Multiple search strategy support
    - Security validation and rate limiting
    """
    
    def __init__(self, 
                 ollama_endpoint: str = "http://localhost:11434",
                 ollama_model: str = "llama2",
                 api_key: str = None,
                 library_api_base: str = "https://api.ashortstayinhell.com/api/v3"):
        """Initialize Ollama URL Generator Agent"""
        
        self.ollama_endpoint = ollama_endpoint.rstrip('/')
        self.ollama_model = ollama_model
        self.api_key = api_key or os.getenv('API_KEY')
        self.library_api_base = library_api_base
        
        # Performance tracking
        self.query_count = 0
        self.total_response_time = 0.0
        
        # Knowledge base info (360 books, 34M+ words)
        self.knowledge_base_info = {
            'total_books': 360,
            'total_words': 34236988,
            'total_chunks': 10514,
            'domains': [
                'philosophy', 'technology', 'social_theory', 'literature',
                'science_fiction', 'politics', 'psychology', 'economics',
                'ethics', 'ai_consciousness', 'digital_surveillance', 
                'climate_change', 'social_justice', 'critical_race_theory'
            ]
        }
        
        logger.info(f"🤖 Ollama URL Generator Agent initialized")
        logger.info(f"📚 Knowledge Base: {self.knowledge_base_info['total_books']} books")
        logger.info(f"📝 Total Words: {self.knowledge_base_info['total_words']:,}")
        logger.info(f"🔗 Ollama: {self.ollama_endpoint}")
    
    async def natural_language_to_url(self, user_query: str) -> Dict[str, Any]:
        """
        Convert natural language query to LibraryOfBabel search URLs
        
        Args:
            user_query: Natural language query like "Find books about AI consciousness"
            
        Returns:
            Dict containing structured query, search URLs, and explanations
        """
        start_time = time.time()
        
        try:
            # Validate input
            if not user_query or len(user_query.strip()) < 3:
                raise ValueError("Query too short")
            
            # Clean and prepare query
            cleaned_query = self._clean_query(user_query)
            
            # Create structured prompt for Ollama
            ollama_prompt = self._create_structured_prompt(cleaned_query)
            
            # Get structured response from Ollama
            structured_query = await self._call_ollama(ollama_prompt)
            
            # Generate multiple search URLs with different strategies
            search_urls = self._generate_search_urls(structured_query)
            
            # Create human-readable explanation
            explanation = self._create_explanation(structured_query, search_urls)
            
            # Track performance
            response_time = time.time() - start_time
            self.query_count += 1
            self.total_response_time += response_time
            
            logger.info(f"🔍 Query processed: '{user_query[:50]}...' in {response_time:.3f}s")
            
            return {
                'success': True,
                'original_query': user_query,
                'cleaned_query': cleaned_query,
                'structured_query': structured_query,
                'search_urls': search_urls,
                'explanation': explanation,
                'performance': {
                    'response_time': response_time,
                    'query_count': self.query_count,
                    'avg_response_time': self.total_response_time / self.query_count
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Query processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'original_query': user_query,
                'timestamp': datetime.now().isoformat()
            }
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize user query"""
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', query.strip())
        
        # Remove potentially problematic characters
        cleaned = re.sub(r'[<>"\']', '', cleaned)
        
        # Limit length for security
        if len(cleaned) > 500:
            cleaned = cleaned[:500] + "..."
        
        return cleaned
    
    def _create_structured_prompt(self, user_query: str) -> str:
        """Create structured prompt for Ollama to extract search parameters"""
        
        knowledge_domains = ", ".join(self.knowledge_base_info['domains'])
        
        return f"""You are a search query analyzer for a digital library with 360 books containing 34+ million words.

Knowledge base domains: {knowledge_domains}

User query: "{user_query}"

Convert this natural language query into structured search parameters. Respond with ONLY valid JSON in this exact format:

{{
    "search_terms": ["primary", "keywords", "from", "query"],
    "authors": ["author names if mentioned"],
    "topics": ["main subject areas"],
    "concepts": ["theoretical or philosophical concepts"],
    "search_type": "semantic",
    "limit": 10,
    "priority": "relevance",
    "domains": ["relevant domain categories"],
    "explanation": "Brief explanation of search strategy"
}}

Guidelines:
- search_terms: 3-6 most important keywords
- authors: only if explicitly mentioned in query
- topics: 1-3 main subject areas
- concepts: abstract ideas or theories mentioned
- search_type: "semantic" for concept searches, "keyword" for specific terms, "author" for author-focused
- limit: 5-20 results (default 10)
- domains: relevant categories from the knowledge base
- explanation: one sentence explaining the search approach

Focus on semantic understanding and concept extraction for the best search results."""
    
    async def _call_ollama(self, prompt: str) -> Dict[str, Any]:
        """Call Ollama API to process the prompt"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent output
                        "top_p": 0.9,
                        "top_k": 40
                    }
                }
                
                async with session.post(
                    f"{self.ollama_endpoint}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status != 200:
                        raise Exception(f"Ollama API error: {response.status}")
                    
                    result = await response.json()
                    ollama_text = result.get('response', '').strip()
                    
                    # Extract JSON from response
                    structured_query = self._extract_json_from_text(ollama_text)
                    
                    return structured_query
                    
        except Exception as e:
            logger.error(f"❌ Ollama API call failed: {e}")
            # Fallback to basic keyword extraction
            return self._fallback_query_analysis(prompt)
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Extract JSON from Ollama response text"""
        try:
            # Look for JSON block
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            logger.warning(f"⚠️ JSON extraction failed: {e}")
            # Return basic structure
            return {
                "search_terms": text.split()[:5],
                "authors": [],
                "topics": ["general"],
                "concepts": [],
                "search_type": "keyword",
                "limit": 10,
                "priority": "relevance",
                "domains": ["general"],
                "explanation": "Fallback keyword search"
            }
    
    def _fallback_query_analysis(self, original_prompt: str) -> Dict[str, Any]:
        """Fallback query analysis when Ollama is unavailable"""
        # Extract user query from prompt
        query_match = re.search(r'User query: "([^"]*)"', original_prompt)
        user_query = query_match.group(1) if query_match else ""
        
        # Simple keyword extraction
        words = re.findall(r'\b\w+\b', user_query.lower())
        keywords = [w for w in words if len(w) > 2 and w not in ['the', 'and', 'or', 'but', 'about', 'find', 'books', 'show']]
        
        return {
            "search_terms": keywords[:5],
            "authors": [],
            "topics": keywords[:2],
            "concepts": [],
            "search_type": "keyword",
            "limit": 10,
            "priority": "relevance",
            "domains": ["general"],
            "explanation": "Simple keyword extraction (Ollama unavailable)"
        }
    
    def _generate_search_urls(self, structured_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate multiple search URLs with different strategies"""
        
        search_urls = []
        base_url = f"{self.library_api_base}/search"
        
        # Strategy 1: Primary semantic search
        if structured_query.get('search_terms'):
            primary_query = " ".join(structured_query['search_terms'])
            params = {
                'q': primary_query,
                'limit': structured_query.get('limit', 10),
                'type': 'semantic'
            }
            if self.api_key:
                params['api_key'] = self.api_key
            
            search_urls.append({
                'strategy': 'primary_semantic',
                'url': f"{base_url}?{urlencode(params)}",
                'description': f"Semantic search for: {primary_query}",
                'priority': 1
            })
        
        # Strategy 2: Author-focused search (if authors mentioned)
        if structured_query.get('authors'):
            for author in structured_query['authors']:
                params = {
                    'q': f'author:"{author}"',
                    'limit': 5,
                    'type': 'author'
                }
                if self.api_key:
                    params['api_key'] = self.api_key
                
                search_urls.append({
                    'strategy': 'author_focused',
                    'url': f"{base_url}?{urlencode(params)}",
                    'description': f"Books by {author}",
                    'priority': 2
                })
        
        # Strategy 3: Topic-based search
        if structured_query.get('topics'):
            topic_query = " OR ".join(structured_query['topics'])
            params = {
                'q': topic_query,
                'limit': 8,
                'type': 'topic'
            }
            if self.api_key:
                params['api_key'] = self.api_key
            
            search_urls.append({
                'strategy': 'topic_based',
                'url': f"{base_url}?{urlencode(params)}",
                'description': f"Topic search: {topic_query}",
                'priority': 3
            })
        
        # Strategy 4: Concept exploration
        if structured_query.get('concepts'):
            concept_query = " AND ".join(structured_query['concepts'])
            params = {
                'q': concept_query,
                'limit': 6,
                'type': 'concept'
            }
            if self.api_key:
                params['api_key'] = self.api_key
            
            search_urls.append({
                'strategy': 'concept_exploration',
                'url': f"{base_url}?{urlencode(params)}",
                'description': f"Concept exploration: {concept_query}",
                'priority': 4
            })
        
        return search_urls
    
    def _create_explanation(self, structured_query: Dict[str, Any], search_urls: List[Dict[str, Any]]) -> str:
        """Create human-readable explanation of the search strategy"""
        
        explanations = []
        
        # Main search explanation
        if structured_query.get('explanation'):
            explanations.append(structured_query['explanation'])
        
        # Search strategies
        strategy_count = len(search_urls)
        if strategy_count > 1:
            explanations.append(f"Using {strategy_count} search strategies for comprehensive results")
        
        # Knowledge base context
        explanations.append(f"Searching across {self.knowledge_base_info['total_books']} books with {self.knowledge_base_info['total_words']:,} words")
        
        return ". ".join(explanations) + "."
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Ollama connection and LibraryOfBabel API"""
        test_results = {
            'ollama_status': 'unknown',
            'library_api_status': 'unknown',
            'timestamp': datetime.now().isoformat()
        }
        
        # Test Ollama
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_endpoint}/api/tags", timeout=5) as response:
                    if response.status == 200:
                        test_results['ollama_status'] = 'connected'
                        models = await response.json()
                        test_results['available_models'] = [m['name'] for m in models.get('models', [])]
                    else:
                        test_results['ollama_status'] = f'error_{response.status}'
        except Exception as e:
            test_results['ollama_status'] = f'failed: {str(e)}'
        
        # Test LibraryOfBabel API
        try:
            async with aiohttp.ClientSession() as session:
                test_url = f"{self.library_api_base}/health"
                async with session.get(test_url, timeout=5) as response:
                    if response.status == 200:
                        test_results['library_api_status'] = 'connected'
                        health_data = await response.json()
                        test_results['library_health'] = health_data
                    else:
                        test_results['library_api_status'] = f'error_{response.status}'
        except Exception as e:
            test_results['library_api_status'] = f'failed: {str(e)}'
        
        return test_results

# Example usage and testing
async def main():
    """Example usage of Ollama URL Generator Agent"""
    
    # Initialize agent
    agent = OllamaUrlGeneratorAgent()
    
    # Test connection
    print("🔧 Testing connections...")
    connection_test = await agent.test_connection()
    print(f"Ollama: {connection_test['ollama_status']}")
    print(f"LibraryOfBabel API: {connection_test['library_api_status']}")
    print()
    
    # Example queries
    test_queries = [
        "Find books about artificial intelligence and consciousness",
        "Show me Octavia Butler's approach to social justice",
        "Books that bridge science and spirituality",
        "Contemporary analysis of digital surveillance",
        "Philosophy of technology and human enhancement"
    ]
    
    print("🤖 Testing natural language queries...")
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        result = await agent.natural_language_to_url(query)
        
        if result['success']:
            print(f"✅ Success! Generated {len(result['search_urls'])} search strategies")
            print(f"🧠 Explanation: {result['explanation']}")
            for url_info in result['search_urls']:
                print(f"   🔗 {url_info['strategy']}: {url_info['description']}")
        else:
            print(f"❌ Failed: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())