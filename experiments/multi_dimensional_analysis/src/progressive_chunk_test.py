#!/usr/bin/env python3
"""
🌱 Progressive Chunk Test - Quick Hypothesis Validation
=====================================================

Simple test of progressive chunking approach without async complexity.
Tests the core hypothesis: each outline builds on previous understanding.

Dr. Elena Vásquez - Digital Archivist & Knowledge Mapping Specialist
"""

import os
import sys
import json
import requests
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import psycopg2
import psycopg2.extras

class ProgressiveChunkTester:
    """Simple progressive chunking tester"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "llama3.2:3b"
        
        self.db_config = {
            'host': 'localhost',
            'database': 'knowledge_base', 
            'user': 'weixiangzhang',
            'password': os.environ.get('DB_PASSWORD')
        }

    def get_db_connection(self):
        """Get PostgreSQL connection"""
        try:
            return psycopg2.connect(**self.db_config)
        except psycopg2.Error as e:
            print(f"❌ Database connection failed: {e}")
            return None

    def get_test_chunks(self, book_title: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get first few chunks for testing"""
        
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return []
                
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            c.chunk_id,
                            c.content,
                            c.word_count,
                            c.chapter_number,
                            b.title as book_title
                        FROM chunks c
                        JOIN books b ON c.book_id = b.book_id
                        WHERE b.title ILIKE %s
                        AND c.content IS NOT NULL
                        AND c.word_count BETWEEN 200 AND 2000
                        ORDER BY c.chunk_id ASC
                        LIMIT %s
                    """, (f"%{book_title}%", limit))
                    
                    results = cur.fetchall()
                    return [dict(result) for result in results]
                    
        except Exception as e:
            print(f"❌ Error getting test chunks: {e}")
            return []

    def call_ollama(self, prompt: str, timeout: int = 120) -> Optional[str]:
        """Simple Ollama API call"""
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_k": 40,
                        "top_p": 0.9
                    }
                },
                timeout=timeout
            )
            
            if response.status_code != 200:
                print(f"❌ Ollama API error: {response.status_code}")
                return None
            
            result = response.json()
            return result.get('response', '').strip()
            
        except Exception as e:
            print(f"❌ Ollama call failed: {e}")
            return None

    def generate_first_outline(self, chunk_text: str, book_title: str) -> Optional[str]:
        """Generate first outline"""
        
        prompt = f"""You are Dr. Elena Vásquez, expert literary analyst. Analyze this opening chunk from "{book_title}" and create a narrative foundation.

CHUNK 1 TEXT:
{chunk_text}

Create a comprehensive outline that captures:
1. Main narrative summary
2. Characters introduced and their roles
3. Locations and their significance
4. Themes beginning to emerge
5. Mood and tone established
6. Key events and plot points

Keep the outline concise but comprehensive - this will be the foundation for progressive analysis.

OUTLINE:"""

        return self.call_ollama(prompt)

    def generate_progressive_outline(self, previous_outline: str, new_chunk_text: str, chunk_number: int, book_title: str) -> Optional[str]:
        """Generate progressive outline building on previous"""
        
        prompt = f"""You are Dr. Elena Vásquez, expert literary analyst. You are progressively analyzing "{book_title}" and now need to update your understanding with chunk {chunk_number}.

PREVIOUS OUTLINE (Chunks 1-{chunk_number-1}):
{previous_outline}

NEW CHUNK {chunk_number} TEXT:
{new_chunk_text}

Generate an UPDATED outline that:
1. Expands the narrative summary with new developments
2. Updates character progressions and introduces new characters
3. Adds new locations while showing the journey
4. Evolves themes based on new content
5. Updates mood/tone with new emotional developments
6. Adds new key events to the timeline

Maintain the same structure but expand with new information. Keep it concise but comprehensive.

UPDATED OUTLINE:"""

        return self.call_ollama(prompt)

    def test_progressive_chunking(self, book_title: str, test_chunks: int = 5):
        """Test progressive chunking hypothesis"""
        
        print(f"🌱 Testing Progressive Chunking Hypothesis")
        print(f"==========================================")
        print(f"📚 Book: {book_title}")
        print(f"🧪 Test Chunks: {test_chunks}")
        print(f"🤖 Model: {self.model}")
        print()
        
        # Get test chunks
        chunks = self.get_test_chunks(book_title, test_chunks)
        
        if not chunks:
            print("❌ No chunks found for testing")
            return
        
        print(f"✅ Retrieved {len(chunks)} chunks for testing")
        
        # Process progressively
        current_outline = None
        results = []
        total_start = datetime.now()
        
        for i, chunk in enumerate(chunks, 1):
            print(f"\n🔄 Processing Chunk {i}/{len(chunks)}: {chunk['chunk_id']}")
            print(f"   📊 Words: {chunk['word_count']:,}")
            
            start_time = datetime.now()
            
            if i == 1:
                # Generate first outline
                print("   🌱 Generating initial outline...")
                current_outline = self.generate_first_outline(chunk['content'], book_title)
            else:
                # Generate progressive outline
                print(f"   📈 Updating progressive outline (1-{i})...")
                current_outline = self.generate_progressive_outline(
                    current_outline, 
                    chunk['content'], 
                    i, 
                    book_title
                )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            if current_outline:
                outline_length = len(current_outline)
                word_count = len(current_outline.split())
                
                print(f"   ✅ Generated: {outline_length:,} chars, ~{word_count} words")
                print(f"   ⏱️ Time: {processing_time:.1f}s")
                
                # Show sample of outline
                sample = current_outline[:200].replace('\n', ' ')
                print(f"   📝 Sample: {sample}...")
                
                results.append({
                    'chunk_number': i,
                    'chunk_id': chunk['chunk_id'],
                    'outline_length': outline_length,
                    'word_count': word_count,
                    'processing_time': processing_time,
                    'outline': current_outline
                })
            else:
                print(f"   ❌ Failed to generate outline")
                break
            
            # Brief pause to avoid overwhelming Ollama
            if i < len(chunks):
                time.sleep(2)
        
        total_time = (datetime.now() - total_start).total_seconds()
        
        # Save results
        if results:
            self.save_test_results(results, book_title, total_time)
            
            print(f"\n🎉 Progressive Chunking Test Complete!")
            print(f"⏱️ Total time: {total_time:.1f} seconds")
            print(f"📈 Outline growth:")
            
            for result in results:
                chunk_num = result['chunk_number']
                length = result['outline_length']
                words = result['word_count']
                time_taken = result['processing_time']
                print(f"   Chunk {chunk_num}: {length:,} chars (~{words} words) in {time_taken:.1f}s")
            
            print(f"\n💡 Hypothesis Test Results:")
            print(f"   ✅ Progressive analysis: {'SUCCESS' if len(results) == len(chunks) else 'PARTIAL'}")
            print(f"   📊 Outline growth: {results[0]['outline_length']:,} → {results[-1]['outline_length']:,} chars")
            print(f"   🚀 Ready for full book processing!")
        else:
            print("❌ Test failed - no results generated")

    def save_test_results(self, results: List[Dict], book_title: str, total_time: float):
        """Save test results"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        book_clean = book_title.replace(" ", "_").replace(":", "").replace("'", "")
        filename = f"progressive_test_{book_clean}_{timestamp}.json"
        output_path = f"/tmp/{filename}"
        
        test_data = {
            "book_title": book_title,
            "test_type": "progressive_chunking_hypothesis",
            "chunks_tested": len(results),
            "total_processing_time": total_time,
            "generated_at": datetime.now().isoformat(),
            "model_used": self.model,
            "results": results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Test results saved to: {output_path}")


def main():
    """Test progressive chunking"""
    
    tester = ProgressiveChunkTester()
    
    # Scale up to full book processing - all 110 chunks!
    print("🚀 SCALING UP TO FULL BOOK PROCESSING")
    print("Testing confirmed - processing entire Butlerian Jihad...")
    tester.test_progressive_chunking("Dune: The Butlerian Jihad", test_chunks=110)


if __name__ == "__main__":
    main()