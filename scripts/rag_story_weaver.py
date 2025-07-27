#!/usr/bin/env python3
"""
🤖 RAG STORY WEAVER - Ollama Integration 🤖
==========================================

Uses LibraryOfBabel as RAG (Retrieval-Augmented Generation) to feed Ollama
with discovered literary content for AI-powered story generation!

Process:
1. 🎲 Chaos engine discovers random story elements
2. 📚 RAG system retrieves relevant literary content  
3. 🤖 Ollama writes stories based on retrieved knowledge
4. ✨ Pure serendipity meets AI creativity

This will be beautifully chaotic and probably hilariously trash! 😄

Team: RAG Engineers + Chaos Storytellers + Ollama Whisperers
"""

import os
import requests
import json
import time
import random
from datetime import datetime
from typing import Dict, List, Any, Optional
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RAGStoryWeaver:
    """RAG-powered story generation using LibraryOfBabel + Ollama"""
    
    def __init__(self):
        self.babel_config = {
            "api_key": os.getenv("BABEL_API_KEY", "REDACTED_API_KEY"),
            "base_url": os.getenv("BABEL_API_BASE_URL", "https://api.ashortstayinhell.com:5562")
        }
        self.ollama_url = "http://localhost:11434"
        self.model = "llama3.2:3b"  # Available model
        
        self.colors = {
            'RED': '\033[91m', 'GREEN': '\033[92m', 'YELLOW': '\033[93m',
            'BLUE': '\033[94m', 'PURPLE': '\033[95m', 'CYAN': '\033[96m',
            'WHITE': '\033[97m', 'BOLD': '\033[1m', 'END': '\033[0m'
        }
        
        print(f"{self.colors['PURPLE']}{self.colors['BOLD']}")
        print("🤖" * 20)
        print("   RAG STORY WEAVER ACTIVATED")
        print("   Connecting LibraryOfBabel → Ollama")
        print("   Preparing for beautiful chaos...")
        print("🤖" * 20)
        print(f"{self.colors['END']}")
    
    def rag_print(self, message: str, color: str = 'WHITE', intensity: int = 1):
        """Print with RAG formatting"""
        prefix = "⚡" * intensity
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{self.colors[color]}{prefix} [{timestamp}] {message}{self.colors['END']}")
    
    def retrieve_babel_content(self, query: str, search_type: str = "semantic", limit: int = 3) -> List[Dict[str, Any]]:
        """Retrieve content from LibraryOfBabel for RAG"""
        self.rag_print(f"📚 RAG Retrieval: '{query}' (type: {search_type})", 'CYAN', 2)
        
        url = f"{self.babel_config['base_url']}/fuzzy-search"
        params = {
            "api_key": self.babel_config["api_key"],
            "q": query,
            "type": search_type,
            "limit": limit
        }
        
        try:
            response = requests.get(url, params=params, verify=False, timeout=45)
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                self.rag_print(f"✅ Retrieved {len(results)} chunks for RAG context", 'GREEN', 1)
                return results
            else:
                self.rag_print(f"⚠️ RAG retrieval failed: {response.status_code}", 'YELLOW', 1)
                return []
        except Exception as e:
            self.rag_print(f"💥 RAG error: {str(e)}", 'RED', 1)
            return []
    
    def format_rag_context(self, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved content as RAG context for Ollama"""
        if not retrieved_chunks:
            return "No context available."
        
        context_parts = []
        context_parts.append("=== LITERARY KNOWLEDGE BASE ===")
        
        for i, chunk in enumerate(retrieved_chunks, 1):
            title = chunk.get('title', 'Unknown Work')
            author = chunk.get('author', 'Anonymous')
            content = chunk.get('content', '')
            
            context_parts.append(f"\n--- Source {i}: {title} by {author} ---")
            context_parts.append(content[:500] + "..." if len(content) > 500 else content)
        
        context_parts.append("\n=== END KNOWLEDGE BASE ===")
        return "\\n".join(context_parts)
    
    def call_ollama(self, prompt: str, context: str = "") -> str:
        """Call Ollama for story generation"""
        self.rag_print(f"🤖 Calling Ollama ({self.model}) for story generation...", 'PURPLE', 2)
        
        # Construct RAG-enhanced prompt
        full_prompt = f"""You are a creative storyteller. Use the provided literary knowledge base to inspire and inform your writing.

{context}

WRITING TASK: {prompt}

Write a creative, engaging story that draws inspiration from the knowledge base above. Be creative and original while incorporating elements from the provided literary sources. Make it entertaining!

STORY:"""
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.8,
                        "top_p": 0.9,
                        "num_predict": 800  # Limit story length
                    }
                },
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                story = data.get('response', '').strip()
                
                self.rag_print(f"✅ Ollama generated {len(story)} characters", 'GREEN', 1)
                return story
            else:
                self.rag_print(f"💥 Ollama error: {response.status_code}", 'RED', 1)
                return "Story generation failed - the AI refused to cooperate!"
                
        except Exception as e:
            self.rag_print(f"💥 Ollama connection error: {str(e)}", 'RED', 1)
            return f"Story generation crashed spectacularly: {str(e)}"
    
    def generate_chaos_prompts(self) -> List[str]:
        """Generate chaotic story prompts for maximum fun"""
        
        # Random story elements
        characters = ["a time-traveling librarian", "a philosophical robot", "a quantum physicist", 
                     "a mystical cat", "an interdimensional being", "a confused AI", "a rebellious book"]
        
        settings = ["in a library that exists outside time", "on a planet made of pure thought",
                   "inside a computer simulation", "in a world where books are alive",
                   "in the space between realities", "in a city of infinite knowledge"]
        
        conflicts = ["must solve the mystery of disappearing words", "faces an existential crisis",
                    "discovers reality is not what it seems", "must choose between logic and emotion",
                    "encounters their own future self", "must save the universe through storytelling"]
        
        themes = ["the nature of consciousness", "the power of stories", "the meaning of existence",
                 "the relationship between chaos and order", "the illusion of free will",
                 "the intersection of love and knowledge"]
        
        # Generate random combinations
        prompts = []
        for _ in range(5):
            character = random.choice(characters)
            setting = random.choice(settings)
            conflict = random.choice(conflicts)
            theme = random.choice(themes)
            
            prompt = f"Write a short story where {character} {setting} {conflict}. Explore themes of {theme}."
            prompts.append(prompt)
        
        return prompts
    
    def execute_rag_story_generation(self, story_prompt: str, search_queries: List[str]) -> Dict[str, Any]:
        """Execute complete RAG story generation pipeline"""
        
        self.rag_print(f"🎭 Starting RAG story generation...", 'BOLD', 3)
        self.rag_print(f"📝 Prompt: {story_prompt[:100]}...", 'YELLOW', 1)
        
        # Step 1: Retrieve relevant content for each search query
        all_retrieved_content = []
        
        for query in search_queries:
            # Try different search types for maximum chaos
            search_type = random.choice(['semantic', 'fuzzy', 'hybrid'])
            retrieved = self.retrieve_babel_content(query, search_type, limit=2)
            all_retrieved_content.extend(retrieved)
        
        # Step 2: Format as RAG context
        rag_context = self.format_rag_context(all_retrieved_content)
        
        # Step 3: Generate story with Ollama
        generated_story = self.call_ollama(story_prompt, rag_context)
        
        # Step 4: Compile results
        result = {
            "prompt": story_prompt,
            "search_queries": search_queries,
            "retrieved_chunks": len(all_retrieved_content),
            "rag_sources": [chunk.get('title', 'Unknown') for chunk in all_retrieved_content],
            "generated_story": generated_story,
            "generation_timestamp": datetime.now().isoformat()
        }
        
        return result
    
    def extract_search_queries_from_prompt(self, prompt: str) -> List[str]:
        """Extract search queries from story prompt for RAG retrieval"""
        
        # Simple keyword extraction for RAG queries
        import re
        
        # Remove common words and extract meaningful terms
        words = re.findall(r'\\b\\w{4,}\\b', prompt.lower())
        meaningful_words = [w for w in words if w not in ['story', 'write', 'short', 'where', 'must', 'will', 'they', 'their']]
        
        # Create search queries
        queries = []
        
        # Add individual meaningful words
        queries.extend(meaningful_words[:4])
        
        # Add some compound queries
        if len(meaningful_words) >= 2:
            queries.append(f"{meaningful_words[0]} {meaningful_words[1]}")
        
        # Add thematic searches
        queries.extend(["consciousness", "existence", "reality", "philosophy"])
        
        return queries[:6]  # Limit to 6 queries
    
    def display_rag_story_result(self, result: Dict[str, Any]):
        """Display the complete RAG story generation result"""
        
        print(f"\\n{self.colors['BOLD']}{self.colors['BLUE']}")
        print("📚" * 40)
        print("   RAG-GENERATED STORY RESULT")
        print("📚" * 40)
        print(f"{self.colors['END']}")
        
        # Metadata
        self.rag_print(f"📝 Original Prompt: {result['prompt']}", 'YELLOW', 1)
        self.rag_print(f"🔍 Search Queries Used: {', '.join(result['search_queries'])}", 'CYAN', 1)
        self.rag_print(f"📚 Retrieved Chunks: {result['retrieved_chunks']}", 'GREEN', 1)
        self.rag_print(f"📖 RAG Sources: {', '.join(result['rag_sources'][:3])}{'...' if len(result['rag_sources']) > 3 else ''}", 'PURPLE', 1)
        
        # The generated story
        print(f"\\n{self.colors['BOLD']}🤖 OLLAMA-GENERATED STORY:{self.colors['END']}")
        print("─" * 60)
        print(result['generated_story'])
        print("─" * 60)
        
        # Story quality assessment (for fun)
        story_length = len(result['generated_story'])
        if story_length > 500:
            quality = "📝 Epic length!"
        elif story_length > 200:
            quality = "📖 Good story length"
        else:
            quality = "📄 Concise tale"
        
        self.rag_print(f"📊 Story Quality: {quality} ({story_length} characters)", 'GREEN', 1)
    
    def run_rag_chaos_session(self, story_count: int = 3):
        """Run a complete RAG chaos story generation session"""
        
        self.rag_print(f"🎪 INITIATING RAG CHAOS SESSION: {story_count} stories", 'BOLD', 4)
        
        # Generate chaotic prompts
        chaos_prompts = self.generate_chaos_prompts()
        
        generated_stories = []
        
        for i in range(story_count):
            self.rag_print(f"📚 GENERATING RAG STORY {i+1}/{story_count}", 'BOLD', 3)
            print("🌊" * 60)
            
            try:
                # Pick a random chaotic prompt
                prompt = chaos_prompts[i % len(chaos_prompts)]
                
                # Extract search queries for RAG
                search_queries = self.extract_search_queries_from_prompt(prompt)
                
                # Generate story with RAG
                result = self.execute_rag_story_generation(prompt, search_queries)
                generated_stories.append(result)
                
                # Display the result
                self.display_rag_story_result(result)
                
                # Brief pause between stories
                time.sleep(3)
                
            except Exception as e:
                self.rag_print(f"💥 RAG chaos overflow: {str(e)}", 'RED', 2)
        
        # Session summary
        self.rag_print(f"🎭 RAG CHAOS SESSION COMPLETE!", 'BOLD', 4)
        self.rag_print(f"📚 Stories Generated: {len(generated_stories)}", 'GREEN', 2)
        
        total_chunks = sum(s['retrieved_chunks'] for s in generated_stories)
        self.rag_print(f"📖 Total RAG Chunks Used: {total_chunks}", 'CYAN', 2)
        
        unique_sources = set()
        for story in generated_stories:
            unique_sources.update(story['rag_sources'])
        
        self.rag_print(f"📚 Unique Books Referenced: {len(unique_sources)}", 'PURPLE', 2)
        
        return generated_stories
    
    def test_ollama_connection(self):
        """Test if Ollama is available and working"""
        self.rag_print("🧪 Testing Ollama connection...", 'YELLOW', 1)
        
        try:
            # Test basic connection
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [m['name'] for m in models]
                
                self.rag_print(f"✅ Ollama connected! Available models: {', '.join(available_models)}", 'GREEN', 1)
                
                if self.model in available_models:
                    self.rag_print(f"✅ Target model '{self.model}' is available", 'GREEN', 1)
                else:
                    self.rag_print(f"⚠️ Target model '{self.model}' not found. Using first available.", 'YELLOW', 1)
                    if available_models:
                        self.model = available_models[0]
                        self.rag_print(f"🔄 Switched to model: {self.model}", 'CYAN', 1)
                
                return True
            else:
                self.rag_print(f"❌ Ollama connection failed: {response.status_code}", 'RED', 1)
                return False
                
        except Exception as e:
            self.rag_print(f"❌ Ollama connection error: {str(e)}", 'RED', 1)
            return False

def main():
    """Launch the RAG Story Weaver"""
    
    weaver = RAGStoryWeaver()
    
    print(f"\\n{weaver.colors['BOLD']}{weaver.colors['CYAN']}")
    print("🤖 WELCOME TO THE RAG STORY WEAVER! 🤖")
    print("=" * 60)
    print("LibraryOfBabel meets Ollama for chaotic storytelling!")
    print(f"{weaver.colors['END']}")
    
    # Test Ollama connection first
    if not weaver.test_ollama_connection():
        print(f"\\n{weaver.colors['RED']}❌ Ollama not available. Please start Ollama first:{weaver.colors['END']}")
        print("   1. Make sure Ollama is installed")
        print("   2. Run: ollama serve")
        print("   3. Pull a model: ollama pull llama3.2:3b")
        return
    
    # Run the RAG chaos session
    stories = weaver.run_rag_chaos_session(story_count=2)
    
    print(f"\\n{weaver.colors['BOLD']}{weaver.colors['PURPLE']}")
    print("🌟 RAG chaos complete! Your AI has been fed pure literary madness! 🌟")
    print(f"{weaver.colors['END']}")

if __name__ == "__main__":
    main()