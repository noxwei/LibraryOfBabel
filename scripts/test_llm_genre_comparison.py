#!/usr/bin/env python3
"""
LLM Genre Classification Comparison
===================================
Test different LLMs for genre classification accuracy and speed
"""

import sys
import json
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config.api_config import get_database_config

class LLMGenreCompare:
    def __init__(self):
        self.db_config = get_database_config()
        self.ollama_url = "http://localhost:11434/api/generate"
        
        # Test models
        self.models = [
            "llama3.2:3b",     # Fast, lightweight
            "magistral"        # Large, comprehensive
        ]
        
        self.valid_genres = [
            "Romance", "Literary Fiction", "Science Fiction", "Fantasy",
            "Mystery & Thriller", "Historical Fiction", "Contemporary Fiction",
            "Self-Help", "Biography & Memoir", "Psychology", "Philosophy",
            "Business & Economics", "History", "Science & Nature"
        ]
    
    def get_test_chunk(self):
        """Get a small test chunk"""
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT b.book_id, b.title, b.author, b.genre, c.content
                    FROM books b
                    JOIN chunks c ON b.book_id = c.book_id
                    WHERE (b.description IS NULL OR b.description = '')
                    AND c.content IS NOT NULL
                    AND LENGTH(c.content) > 200
                    AND LENGTH(c.content) < 800
                    ORDER BY RANDOM()
                    LIMIT 1
                """)
                
                result = cur.fetchone()
                return result
        finally:
            conn.close()
    
    def classify_with_model(self, model, book_data, content):
        """Test classification with specific model"""
        
        # Create a concise, focused prompt
        prompt = f"""Classify this book excerpt by genre. Respond with ONLY the genre name.

CONTENT:
{content[:400]}

GENRES: Romance, Literary Fiction, Science Fiction, Fantasy, Mystery & Thriller, Historical Fiction, Contemporary Fiction, Self-Help, Biography & Memoir, Psychology, Philosophy, Business & Economics, History, Science & Nature

GENRE:"""

        try:
            start_time = time.time()
            
            response = requests.post(
                self.ollama_url,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1}
                },
                timeout=60
            )
            
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                classification = result['response'].strip()
                
                # Clean response
                for genre in self.valid_genres:
                    if genre.lower() in classification.lower():
                        return genre, end_time - start_time
                
                return classification, end_time - start_time
            else:
                return None, end_time - start_time
                
        except Exception as e:
            return f"ERROR: {e}", 60
    
    def run_comparison(self):
        """Run the comparison test"""
        print("🧪 LLM Genre Classification Comparison")
        print("=" * 50)
        
        # Get test chunk
        test_data = self.get_test_chunk()
        if not test_data:
            print("❌ No test data found")
            return
        
        print(f"📚 Test Book: \"{test_data['title']}\" by {test_data['author']}")
        print(f"🏷️  Current Genre: {test_data['genre']}")
        print(f"📝 Content Preview: {test_data['content'][:150]}...")
        print()
        
        results = {}
        
        for model in self.models:
            print(f"🤖 Testing {model}...")
            
            classification, duration = self.classify_with_model(
                model, test_data, test_data['content']
            )
            
            results[model] = {
                "classification": classification,
                "duration": duration,
                "matches_current": classification == test_data['genre'] if classification in self.valid_genres else False
            }
            
            print(f"   Result: {classification}")
            print(f"   Time: {duration:.2f}s")
            print(f"   Matches current: {'✅' if results[model]['matches_current'] else '❌'}")
            print()
        
        # Summary
        print("📊 COMPARISON SUMMARY")
        print("-" * 30)
        
        fastest = min(results.items(), key=lambda x: x[1]['duration'])
        print(f"⚡ Fastest: {fastest[0]} ({fastest[1]['duration']:.2f}s)")
        
        accurate = [m for m, r in results.items() if r['matches_current']]
        if accurate:
            print(f"🎯 Accurate: {', '.join(accurate)}")
        else:
            print("🎯 Accurate: None matched current classification")
        
        print("\n🔍 DETAILED RESULTS:")
        for model, result in results.items():
            print(f"  {model}:")
            print(f"    Classification: {result['classification']}")
            print(f"    Speed: {result['duration']:.2f}s")
            print(f"    Accuracy: {'✅' if result['matches_current'] else '❌'}")
        
        return results

def main():
    tester = LLMGenreCompare()
    tester.run_comparison()

if __name__ == '__main__':
    main()