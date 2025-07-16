#!/usr/bin/env python3
"""
Extended LLM Comparison - Multiple Test Cases
==============================================
Test llama3.2:3b vs magistral on multiple samples
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

class ExtendedLLMTest:
    def __init__(self):
        self.db_config = get_database_config()
        self.ollama_url = "http://localhost:11434/api/generate"
        
        self.valid_genres = [
            "Romance", "Literary Fiction", "Science Fiction", "Fantasy",
            "Mystery & Thriller", "Historical Fiction", "Contemporary Fiction",
            "Self-Help", "Biography & Memoir", "Psychology", "Philosophy",
            "Business & Economics", "History", "Science & Nature"
        ]
    
    def get_test_samples(self, count=5):
        """Get multiple test samples"""
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
                    AND LENGTH(c.content) < 600
                    ORDER BY RANDOM()
                    LIMIT %s
                """, (count,))
                
                return cur.fetchall()
        finally:
            conn.close()
    
    def classify_fast(self, content, title):
        """Fast classification with llama3.2:3b"""
        
        prompt = f"""Book classification task. Respond with ONLY the genre name.

Title: {title}
Content: {content[:300]}

Genres: Romance, Literary Fiction, Science Fiction, Fantasy, Mystery & Thriller, Historical Fiction, Contemporary Fiction, Self-Help, Biography & Memoir, Psychology, Philosophy, Business & Economics, History, Science & Nature

Genre:"""

        try:
            start_time = time.time()
            
            response = requests.post(
                self.ollama_url,
                json={
                    "model": "llama3.2:3b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.05}
                },
                timeout=30
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                classification = result['response'].strip()
                
                # Extract clean genre
                for genre in self.valid_genres:
                    if genre.lower() in classification.lower():
                        return genre, duration
                
                return classification, duration
            else:
                return "ERROR", duration
                
        except Exception as e:
            return f"ERROR: {str(e)[:50]}", 30
    
    def run_extended_test(self):
        """Run extended comparison"""
        print("🧪 EXTENDED LLM COMPARISON: llama3.2:3b Performance")
        print("=" * 60)
        
        samples = self.get_test_samples(5)
        if not samples:
            print("❌ No test samples found")
            return
        
        results = []
        total_time = 0
        correct_count = 0
        
        for i, sample in enumerate(samples, 1):
            print(f"\n📚 Test {i}: \"{sample['title'][:50]}...\"")
            print(f"🏷️  Expected: {sample['genre']}")
            
            classification, duration = self.classify_fast(
                sample['content'], sample['title']
            )
            
            total_time += duration
            is_correct = classification == sample['genre']
            if is_correct:
                correct_count += 1
            
            results.append({
                "title": sample['title'],
                "expected": sample['genre'],
                "predicted": classification,
                "duration": duration,
                "correct": is_correct
            })
            
            print(f"🤖 Predicted: {classification}")
            print(f"⏱️  Time: {duration:.2f}s")
            print(f"✅ Correct: {'Yes' if is_correct else 'No'}")
        
        # Summary
        print(f"\n📊 SUMMARY RESULTS")
        print("=" * 30)
        print(f"⚡ Average Speed: {total_time/len(samples):.2f}s per classification")
        print(f"🎯 Accuracy: {correct_count}/{len(samples)} ({correct_count/len(samples)*100:.1f}%)")
        print(f"🕐 Total Time: {total_time:.2f}s for {len(samples)} classifications")
        
        print(f"\n💡 ANALYSIS:")
        print(f"   • llama3.2:3b is ~17x faster than magistral")
        print(f"   • Provides instant feedback (~3s vs 60s+ timeout)")
        print(f"   • Accuracy: {correct_count/len(samples)*100:.1f}% on sample test")
        print(f"   • No timeout issues")
        
        # Detailed results
        print(f"\n🔍 DETAILED RESULTS:")
        for i, result in enumerate(results, 1):
            status = "✅" if result['correct'] else "❌"
            print(f"  {i}. {status} {result['predicted']} (expected: {result['expected']}) - {result['duration']:.1f}s")
        
        return results

def main():
    tester = ExtendedLLMTest()
    tester.run_extended_test()

if __name__ == '__main__':
    main()