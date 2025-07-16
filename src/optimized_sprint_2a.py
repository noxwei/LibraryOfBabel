#!/usr/bin/env python3
"""
🚀 OPTIMIZED SPRINT 2A - Post-Warm-up Implementation
===================================================

Engineering Manager optimized version with:
- 3-minute timeout per book (warm Magistral)
- Single book processing for better resource management
- Parallel fallback option for M2 Pro's 10-core architecture
"""

import os
import sys
import json
import time
import requests
import psycopg2
import psycopg2.extras
from typing import Dict, Optional, Tuple
from pathlib import Path
import logging

# Set optimized environment
os.environ["OLLAMA_TIMEOUT"] = "180"  # 3 minutes per book

# Add paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))
sys.path.append(str(project_root))

from config.api_config import get_database_config

class OptimizedSprintClassifier:
    """
    🚀 Optimized Sprint 2A Classifier
    
    Post-warm-up optimizations:
    - Extended timeouts for warm Magistral
    - Single-book processing
    - Resource-aware batching
    """
    
    def __init__(self):
        self.ollama_base_url = "http://localhost:11434"
        self.db_config = get_database_config()
        
        # Optimized timeouts for warm Magistral
        self.timeout_seconds = 180  # 3 minutes per book
        self.short_timeout = 60     # For simple queries
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("OptimizedClassifier")
        
        self.standard_genres = [
            "Fiction", "Science Fiction & Fantasy", "Philosophy & Theory",
            "History & Biography", "Science & Technology", "Politics & Government",
            "Literature & Criticism", "Business & Economics", "Arts & Culture", "Reference & Education"
        ]

    def get_db_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(**self.db_config)
        except psycopg2.Error as e:
            self.logger.error(f"Database connection failed: {e}")
            return None

    def query_magistral_optimized(self, prompt: str, timeout: int = None) -> Optional[str]:
        """Optimized Magistral query for warm model"""
        timeout = timeout or self.timeout_seconds
        
        try:
            self.logger.debug(f"Querying Magistral (timeout: {timeout}s)...")
            start_time = time.time()
            
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": "magistral",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "max_tokens": 50,  # Keep responses concise
                        "stop": ["\\n\\n", "NEXT:", "---"]
                    }
                },
                timeout=timeout
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json().get('response', '').strip()
                self.logger.debug(f"Magistral responded in {duration:.1f}s")
                return result
            else:
                self.logger.error(f"Magistral API error: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            self.logger.warning(f"Magistral timeout after {timeout}s")
            return None
        except Exception as e:
            self.logger.error(f"Magistral query error: {e}")
            return None

    def classify_genre_fast(self, title: str, author: str, description: str) -> Tuple[Optional[str], float]:
        """Fast genre classification for warm Magistral"""
        
        # Streamlined prompt for speed
        prompt = f"""Classify this book into ONE genre:

Genres: Fiction, Science Fiction & Fantasy, Philosophy & Theory, History & Biography, Science & Technology, Politics & Government, Literature & Criticism, Business & Economics, Arts & Culture, Reference & Education

Book: "{title}" by {author}
Description: {description[:300]}

Genre:"""

        result = self.query_magistral_optimized(prompt, self.short_timeout)
        
        if result:
            # Quick genre matching
            result_lower = result.lower()
            for genre in self.standard_genres:
                if genre.lower() in result_lower:
                    confidence = 0.9 if genre in result else 0.7
                    return genre, confidence
            
            # Fast fallback matching
            if "science" in result_lower and "fiction" in result_lower:
                return "Science Fiction & Fantasy", 0.6
            elif "philosophy" in result_lower or "theory" in result_lower:
                return "Philosophy & Theory", 0.6
            elif "history" in result_lower or "biography" in result_lower:
                return "History & Biography", 0.6
            elif "technology" in result_lower or "science" in result_lower:
                return "Science & Technology", 0.6
        
        return None, 0.0

    def classify_content_type_fast(self, content_sample: str) -> str:
        """Fast content type classification"""
        
        # Simple heuristics for speed
        content_lower = content_sample.lower()
        
        # Technical indicators
        if any(word in content_lower for word in ['algorithm', 'function', 'theorem', 'equation', 'method']):
            return "technical"
        
        # Dialogue indicators
        if content_sample.count('"') > 5 or content_sample.count("'") > 5:
            return "dialogue"
        
        # Abstract/philosophical indicators
        if any(word in content_lower for word in ['concept', 'theory', 'philosophy', 'abstract', 'meaning']):
            return "abstract"
        
        # Default to narrative
        return "narrative"

    def get_book_sample_fast(self, book_id: int) -> str:
        """Fast content sample retrieval"""
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return ""
                
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT content 
                        FROM chunks 
                        WHERE book_id = %s 
                        LIMIT 1
                    """, (book_id,))
                    
                    chunk = cur.fetchone()
                    if chunk:
                        return chunk[0][:1000]  # First 1000 chars
                    
                    return ""
                    
        except Exception as e:
            self.logger.error(f"Error fetching sample: {e}")
            return ""

    def process_single_book(self, book: Dict) -> Dict:
        """Process a single book with optimized approach"""
        
        book_id = book['book_id']
        title = book.get('title', 'Unknown')[:50]
        
        self.logger.info(f"📚 Processing book {book_id}: {title}")
        
        start_time = time.time()
        
        try:
            # Fast classification
            genre, confidence = self.classify_genre_fast(
                book.get('title', ''),
                book.get('author', ''),
                book.get('description', '') or ''
            )
            
            processing_time = time.time() - start_time
            
            if genre and confidence > 0.5:
                # Update database
                with self.get_db_connection() as conn:
                    if conn:
                        with conn.cursor() as cur:
                            cur.execute("""
                                UPDATE books 
                                SET genre = %s 
                                WHERE book_id = %s
                            """, (genre, book_id))
                            conn.commit()
                
                self.logger.info(f"   ✅ {genre} (confidence: {confidence:.1f}, {processing_time:.1f}s)")
                
                return {
                    "success": True,
                    "genre": genre,
                    "confidence": confidence,
                    "processing_time": processing_time
                }
            else:
                self.logger.warning(f"   ❌ Classification failed (confidence: {confidence:.1f})")
                return {
                    "success": False,
                    "processing_time": processing_time
                }
                
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"   ❌ Error: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": processing_time
            }

    def get_books_batch(self, batch_size: int = 10) -> list:
        """Get books needing classification"""
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return []
                
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT book_id, title, author, description, word_count
                        FROM books 
                        WHERE (
                            genre IS NULL 
                            OR genre = '' 
                            OR TRIM(genre) = ''
                            OR genre IN ('none', 'book', 'cj5', '公众号：古德猫宁李', 'chenjin5.com沉金书屋')
                        )
                        ORDER BY word_count DESC NULLS LAST
                        LIMIT %s
                    """, (batch_size,))
                    
                    return [dict(row) for row in cur.fetchall()]
                    
        except Exception as e:
            self.logger.error(f"Error fetching books: {e}")
            return []

    def run_optimized_sprint(self, target_books: int = 50):
        """Run optimized Sprint 2A with warm Magistral"""
        
        self.logger.info("🚀 OPTIMIZED SPRINT 2A - POST-WARM-UP")
        self.logger.info("=" * 50)
        self.logger.info(f"Target: {target_books} books")
        self.logger.info(f"Timeout: {self.timeout_seconds}s per book")
        self.logger.info(f"Strategy: Single-book processing")
        self.logger.info("")
        
        # Get books to process
        books = self.get_books_batch(target_books)
        
        if not books:
            self.logger.info("✅ No books need classification")
            return
        
        self.logger.info(f"📚 Found {len(books)} books to process")
        self.logger.info("")
        
        # Process books one by one
        results = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "genres_assigned": {},
            "total_time": 0,
            "avg_time_per_book": 0
        }
        
        sprint_start = time.time()
        
        for i, book in enumerate(books, 1):
            print(f"[{i:2d}/{len(books)}] ", end="")
            
            # Process single book
            result = self.process_single_book(book)
            
            results["processed"] += 1
            results["total_time"] += result["processing_time"]
            
            if result["success"]:
                results["successful"] += 1
                genre = result["genre"]
                results["genres_assigned"][genre] = results["genres_assigned"].get(genre, 0) + 1
            else:
                results["failed"] += 1
            
            # Brief pause for Mac Mini thermal management
            time.sleep(2)
        
        # Calculate final metrics
        sprint_duration = time.time() - sprint_start
        results["avg_time_per_book"] = results["total_time"] / results["processed"] if results["processed"] > 0 else 0
        success_rate = (results["successful"] / results["processed"] * 100) if results["processed"] > 0 else 0
        
        # Final report
        self.logger.info("")
        self.logger.info("🏁 OPTIMIZED SPRINT 2A RESULTS")
        self.logger.info("=" * 35)
        self.logger.info(f"Books Processed: {results['processed']}")
        self.logger.info(f"Successful: {results['successful']}")
        self.logger.info(f"Failed: {results['failed']}")
        self.logger.info(f"Success Rate: {success_rate:.1f}%")
        self.logger.info(f"Sprint Duration: {sprint_duration/60:.1f} minutes")
        self.logger.info(f"Avg Time/Book: {results['avg_time_per_book']:.1f}s")
        
        # Engineering Manager target check
        target_met = success_rate >= 85.0  # Adjusted for optimized run
        self.logger.info(f"\n🎯 Target (85% success): {'✅ MET' if target_met else '❌ MISSED'}")
        
        if results["genres_assigned"]:
            self.logger.info(f"\n📚 Genres Assigned:")
            for genre, count in sorted(results["genres_assigned"].items(), key=lambda x: x[1], reverse=True):
                self.logger.info(f"  {genre}: {count} books")
        
        return results, target_met

def main():
    """Optimized Sprint 2A execution"""
    
    print("🚀 OPTIMIZED SPRINT 2A - WARM MAGISTRAL")
    print("=" * 50)
    print("✅ Magistral is warm and ready")
    print("⚡ Optimized timeouts and processing")
    print()
    
    classifier = OptimizedSprintClassifier()
    
    # Test with 5 books first
    print("🧪 Testing with 5 books...")
    results, success = classifier.run_optimized_sprint(5)
    
    if success:
        print(f"\n✅ Test successful! Ready for larger batch.")
        
        response = input("Continue with 50 books? (y/N): ").strip().lower()
        if response == 'y':
            classifier.run_optimized_sprint(50)
    else:
        print(f"\n⚠️  Test needs tuning - review results above")

if __name__ == "__main__":
    main()