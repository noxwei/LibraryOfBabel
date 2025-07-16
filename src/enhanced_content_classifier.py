#!/usr/bin/env python3
"""
🎭 ENHANCED CONTENT CLASSIFIER - Sprint 2A Implementation
=========================================================

Production-ready content classification system using Magistral.
Addresses the 1,210 missing genres with intelligent routing integration.

Engineering Manager Approved Features:
- Genre classification with 95% target coverage
- Content-type detection for routing decisions
- Entity extraction for hybrid search
- Performance monitoring and audit logging
"""

import os
import sys
import json
import time
import requests
import psycopg2
import psycopg2.extras
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import logging

# Add paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))
sys.path.append(str(project_root))

from config.api_config import get_database_config

@dataclass
class ClassificationResult:
    """Result of content classification"""
    genre: Optional[str] = None
    content_type: Optional[str] = None
    entities: List[str] = None
    confidence: float = 0.0
    processing_time: float = 0.0
    reasoning: str = ""

class EnhancedContentClassifier:
    """
    🎭 Production Content Classification System
    
    Features:
    - Multi-model routing integration
    - Performance monitoring
    - Batch processing with throttling
    - Audit logging for decisions
    """
    
    def __init__(self, ollama_base_url: str = "http://localhost:11434"):
        self.ollama_base_url = ollama_base_url.rstrip('/')
        self.db_config = get_database_config()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("ContentClassifier")
        
        # Standard taxonomies (Engineering Manager approved)
        self.standard_genres = [
            "Fiction",
            "Science Fiction & Fantasy", 
            "Philosophy & Theory",
            "History & Biography",
            "Science & Technology",
            "Politics & Government",
            "Literature & Criticism",
            "Business & Economics",
            "Arts & Culture",
            "Reference & Education"
        ]
        
        self.content_types = [
            "technical",      # Code, math, scientific
            "factual",        # Historical, biographical
            "abstract",       # Philosophical, theoretical
            "narrative",      # Stories, descriptions
            "dialogue",       # Conversations, interviews
            "analytical",     # Critical analysis
            "reference"       # Encyclopedic, manual
        ]
        
        # Performance tracking
        self.stats = {
            "books_processed": 0,
            "successful_classifications": 0,
            "failed_classifications": 0,
            "total_processing_time": 0.0,
            "avg_processing_time": 0.0
        }

    def get_db_connection(self):
        """Get database connection with error handling"""
        try:
            return psycopg2.connect(**self.db_config)
        except psycopg2.Error as e:
            self.logger.error(f"Database connection failed: {e}")
            return None

    def query_magistral(self, prompt: str, max_tokens: int = 100) -> Optional[str]:
        """Query Magistral with enhanced error handling and retry logic"""
        for attempt in range(3):  # Retry up to 3 times
            try:
                response = requests.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": "magistral",
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,  # Low temperature for consistency
                            "top_p": 0.9,
                            "max_tokens": max_tokens,
                            "stop": ["\\n\\n", "---"]  # Stop tokens
                        }
                    },
                    timeout=60  # 1 minute timeout
                )
                
                if response.status_code == 200:
                    result = response.json().get('response', '').strip()
                    return result
                else:
                    self.logger.warning(f"Magistral API error: {response.status_code}, attempt {attempt + 1}")
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"Magistral timeout, attempt {attempt + 1}")
            except Exception as e:
                self.logger.error(f"Magistral query error: {e}, attempt {attempt + 1}")
            
            if attempt < 2:  # Don't sleep after last attempt
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None

    def classify_genre(self, title: str, author: str, description: str, content_sample: str) -> Tuple[Optional[str], float, str]:
        """Classify book genre using Magistral"""
        
        prompt = f"""You are an expert librarian. Classify this book into EXACTLY ONE genre from this list:

GENRES: {', '.join(self.standard_genres)}

BOOK:
Title: {title}
Author: {author}
Description: {description[:500]}
Content: {content_sample[:800]}

Instructions:
- Choose EXACTLY ONE genre from the list above
- Consider the primary focus and dominant themes
- Respond with just the genre name

GENRE:"""

        start_time = time.time()
        result = self.query_magistral(prompt, max_tokens=20)
        processing_time = time.time() - start_time
        
        if result:
            # Find matching genre
            for genre in self.standard_genres:
                if genre.lower() in result.lower():
                    confidence = 0.9 if genre in result else 0.7  # Higher confidence for exact match
                    return genre, confidence, f"Classified as {genre} in {processing_time:.1f}s"
            
            # Fallback - try partial matches
            result_lower = result.lower()
            if "science" in result_lower and "fiction" in result_lower:
                return "Science Fiction & Fantasy", 0.6, "Partial match: science fiction"
            elif "philosophy" in result_lower or "theory" in result_lower:
                return "Philosophy & Theory", 0.6, "Partial match: philosophy/theory"
            elif "history" in result_lower or "biography" in result_lower:
                return "History & Biography", 0.6, "Partial match: history/biography"
        
        return None, 0.0, f"Classification failed after {processing_time:.1f}s"

    def classify_content_type(self, content_sample: str) -> Tuple[Optional[str], float]:
        """Classify content type for routing decisions"""
        
        prompt = f"""Analyze this text and classify its TYPE from these options:

TYPES: {', '.join(self.content_types)}

TEXT: {content_sample[:600]}

Instructions:
- Choose EXACTLY ONE type that best describes the writing style
- Consider: Is it technical/scientific? Narrative storytelling? Factual reporting? Abstract theory?
- Respond with just the type name

TYPE:"""

        result = self.query_magistral(prompt, max_tokens=15)
        
        if result:
            for content_type in self.content_types:
                if content_type in result.lower():
                    confidence = 0.8
                    return content_type, confidence
        
        return "narrative", 0.3  # Default fallback

    def extract_entities(self, content_sample: str) -> List[str]:
        """Extract key entities for hybrid search"""
        
        prompt = f"""Extract the 5 most important entities (people, places, concepts, terms) from this text:

TEXT: {content_sample[:800]}

Instructions:
- List ONLY the key entities, one per line
- Include: names, places, technical terms, important concepts
- Maximum 5 entities
- Format: just the entity name, no descriptions

ENTITIES:"""

        result = self.query_magistral(prompt, max_tokens=50)
        
        if result:
            entities = [entity.strip() for entity in result.split('\n') if entity.strip()]
            return entities[:5]  # Limit to 5
        
        return []

    def get_book_content_sample(self, book_id: int) -> str:
        """Get content sample from book chunks"""
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return ""
                
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT content 
                        FROM chunks 
                        WHERE book_id = %s 
                        ORDER BY chapter_number, section_number 
                        LIMIT 3
                    """, (book_id,))
                    
                    chunks = cur.fetchall()
                    if chunks:
                        content = " ".join([chunk[0] for chunk in chunks])
                        return content[:2000] + "..." if len(content) > 2000 else content
                    
                    return ""
                    
        except Exception as e:
            self.logger.error(f"Error fetching content sample: {e}")
            return ""

    def classify_book_complete(self, book: Dict) -> ClassificationResult:
        """Complete classification of a book (genre + content type + entities)"""
        
        start_time = time.time()
        
        # Get content sample
        content_sample = self.get_book_content_sample(book['book_id'])
        
        # Prepare book data
        title = book.get('title', 'Unknown Title')
        author = book.get('author', 'Unknown Author')
        description = book.get('description', '') or ''
        
        self.logger.info(f"🎭 Classifying: {title[:40]}...")
        
        try:
            # 1. Genre classification
            genre, genre_confidence, genre_reasoning = self.classify_genre(
                title, author, description, content_sample
            )
            
            # 2. Content type classification  
            content_type, content_confidence = self.classify_content_type(content_sample)
            
            # 3. Entity extraction
            entities = self.extract_entities(content_sample)
            
            # Calculate overall confidence
            overall_confidence = (genre_confidence + content_confidence) / 2.0
            processing_time = time.time() - start_time
            
            # Combined reasoning
            reasoning = f"Genre: {genre_reasoning}; Content: {content_type} ({content_confidence:.1f}); Entities: {len(entities)}"
            
            result = ClassificationResult(
                genre=genre,
                content_type=content_type,
                entities=entities,
                confidence=overall_confidence,
                processing_time=processing_time,
                reasoning=reasoning
            )
            
            self.logger.info(f"   ✅ {genre} | {content_type} | {len(entities)} entities ({processing_time:.1f}s)")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"   ❌ Classification failed: {e}")
            
            return ClassificationResult(
                confidence=0.0,
                processing_time=processing_time,
                reasoning=f"Error: {str(e)}"
            )

    def update_book_classification(self, book_id: int, result: ClassificationResult) -> bool:
        """Update book and content classifications in database"""
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return False
                
                with conn.cursor() as cur:
                    # Update book genre
                    if result.genre:
                        cur.execute("""
                            UPDATE books 
                            SET genre = %s 
                            WHERE book_id = %s
                        """, (result.genre, book_id))
                    
                    # Insert content classification
                    if result.content_type:
                        cur.execute("""
                            INSERT INTO content_classifications (
                                chunk_id, book_id, content_type, 
                                confidence_score, classification_model
                            ) VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (chunk_id) DO UPDATE SET
                                content_type = EXCLUDED.content_type,
                                confidence_score = EXCLUDED.confidence_score,
                                classification_model = EXCLUDED.classification_model
                        """, (f"book_{book_id}_overall", book_id, result.content_type, 
                              result.confidence, "magistral"))
                    
                    # Insert entities
                    if result.entities:
                        for entity in result.entities:
                            cur.execute("""
                                INSERT INTO chunk_entities (
                                    chunk_id, book_id, entity_text, 
                                    entity_type, confidence, extraction_model
                                ) VALUES (%s, %s, %s, %s, %s, %s)
                                ON CONFLICT DO NOTHING
                            """, (f"book_{book_id}_overall", book_id, entity, 
                                  "concept", 0.8, "magistral"))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            self.logger.error(f"Error updating classification: {e}")
            return False

    def get_books_needing_classification(self, batch_size: int = 20) -> List[Dict]:
        """Get books that need classification"""
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return []
                
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            book_id, title, author, description, genre, word_count
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

    def process_batch(self, batch_size: int = 10) -> Dict:
        """Process a batch of books with performance tracking"""
        
        self.logger.info(f"🎭 Starting batch classification (size: {batch_size})")
        
        books = self.get_books_needing_classification(batch_size)
        if not books:
            self.logger.info("✅ No books need classification")
            return {"processed": 0, "successful": 0, "failed": 0}
        
        batch_results = {
            "processed": 0,
            "successful": 0, 
            "failed": 0,
            "genres_assigned": {},
            "content_types_assigned": {},
            "batch_time": 0.0
        }
        
        batch_start = time.time()
        
        for i, book in enumerate(books, 1):
            self.logger.info(f"[{i:2d}/{len(books)}] Processing book {book['book_id']}")
            
            # Classify book
            result = self.classify_book_complete(book)
            
            # Update database
            if result.genre and self.update_book_classification(book['book_id'], result):
                batch_results["successful"] += 1
                
                # Track genre assignments
                if result.genre:
                    batch_results["genres_assigned"][result.genre] = \
                        batch_results["genres_assigned"].get(result.genre, 0) + 1
                
                # Track content type assignments
                if result.content_type:
                    batch_results["content_types_assigned"][result.content_type] = \
                        batch_results["content_types_assigned"].get(result.content_type, 0) + 1
            else:
                batch_results["failed"] += 1
            
            batch_results["processed"] += 1
            
            # Update global stats
            self.stats["books_processed"] += 1
            self.stats["total_processing_time"] += result.processing_time
            
            if result.genre:
                self.stats["successful_classifications"] += 1
            else:
                self.stats["failed_classifications"] += 1
            
            # Throttling for Mac Mini (Engineering Manager requirement)
            time.sleep(1)
        
        batch_results["batch_time"] = time.time() - batch_start
        
        # Update average processing time
        if self.stats["books_processed"] > 0:
            self.stats["avg_processing_time"] = \
                self.stats["total_processing_time"] / self.stats["books_processed"]
        
        # Log results
        self.logger.info(f"✅ Batch complete: {batch_results['successful']}/{batch_results['processed']} successful")
        
        return batch_results

    def run_classification_sprint(self, target_books: int = 200, batch_size: int = 10):
        """Run Sprint 2A classification with Engineering Manager requirements"""
        
        self.logger.info("🚀 SPRINT 2A: MAGISTRAL CONTENT CLASSIFICATION")
        self.logger.info("=" * 60)
        self.logger.info(f"Target: {target_books} books | Batch size: {batch_size}")
        self.logger.info(f"Success target: 95% coverage")
        self.logger.info("")
        
        total_results = {
            "total_processed": 0,
            "total_successful": 0,
            "total_failed": 0,
            "all_genres": {},
            "all_content_types": {},
            "sprint_start_time": time.time()
        }
        
        batches_needed = (target_books + batch_size - 1) // batch_size
        
        for batch_num in range(1, batches_needed + 1):
            self.logger.info(f"🔄 BATCH {batch_num}/{batches_needed}")
            self.logger.info("-" * 30)
            
            batch_results = self.process_batch(batch_size)
            
            # Aggregate results
            total_results["total_processed"] += batch_results["processed"]
            total_results["total_successful"] += batch_results["successful"]
            total_results["total_failed"] += batch_results["failed"]
            
            # Merge genre counts
            for genre, count in batch_results.get("genres_assigned", {}).items():
                total_results["all_genres"][genre] = \
                    total_results["all_genres"].get(genre, 0) + count
            
            # Merge content type counts
            for content_type, count in batch_results.get("content_types_assigned", {}).items():
                total_results["all_content_types"][content_type] = \
                    total_results["all_content_types"].get(content_type, 0) + count
            
            # Stop if no more books
            if batch_results["processed"] < batch_size:
                self.logger.info(f"✅ All available books processed after {batch_num} batches")
                break
            
            # Check if we've reached target
            if total_results["total_processed"] >= target_books:
                self.logger.info(f"🎯 Target of {target_books} books reached")
                break
            
            # Rest between batches (Mac Mini friendly)
            self.logger.info("⏸️  Resting 10 seconds between batches...")
            time.sleep(10)
        
        # Final Sprint 2A report
        sprint_time = time.time() - total_results["sprint_start_time"]
        success_rate = (total_results["total_successful"] / total_results["total_processed"] * 100) if total_results["total_processed"] > 0 else 0
        
        self.logger.info(f"\n🏁 SPRINT 2A RESULTS")
        self.logger.info("=" * 30)
        self.logger.info(f"Books Processed: {total_results['total_processed']}")
        self.logger.info(f"Successful: {total_results['total_successful']}")
        self.logger.info(f"Failed: {total_results['total_failed']}")
        self.logger.info(f"Success Rate: {success_rate:.1f}%")
        self.logger.info(f"Sprint Time: {sprint_time/60:.1f} minutes")
        self.logger.info(f"Avg Time/Book: {self.stats['avg_processing_time']:.1f}s")
        
        # Engineering Manager targets
        target_met = success_rate >= 95.0
        self.logger.info(f"\n🎯 Engineering Manager Target (95% coverage): {'✅ MET' if target_met else '❌ MISSED'}")
        
        if total_results["all_genres"]:
            self.logger.info(f"\n📚 Genres Assigned:")
            for genre, count in sorted(total_results["all_genres"].items(), key=lambda x: x[1], reverse=True):
                self.logger.info(f"  {genre}: {count} books")
        
        if total_results["all_content_types"]:
            self.logger.info(f"\n🎭 Content Types Assigned:")
            for content_type, count in sorted(total_results["all_content_types"].items(), key=lambda x: x[1], reverse=True):
                self.logger.info(f"  {content_type}: {count} books")
        
        return total_results, target_met

def main():
    """Sprint 2A main execution"""
    
    classifier = EnhancedContentClassifier()
    
    print("🎭 SPRINT 2A: ENHANCED CONTENT CLASSIFICATION")
    print("=" * 60)
    print("Engineering Manager Approved Implementation")
    print()
    
    # Start with smaller test
    print("🧪 Testing with 5 books first...")
    test_results = classifier.process_batch(5)
    
    if test_results["successful"] > 0:
        print(f"✅ Test successful: {test_results['successful']}/5 books classified")
        print()
        
        response = input("Continue with full Sprint 2A? (y/N): ").strip().lower()
        
        if response == 'y':
            # Run full sprint
            results, target_met = classifier.run_classification_sprint(
                target_books=200,  # Conservative start
                batch_size=10
            )
            
            if target_met:
                print("\n🎉 Sprint 2A COMPLETE - Ready for Phase 2B!")
            else:
                print("\n⚠️  Sprint 2A needs adjustment - Review and retry")
        else:
            print("Sprint 2A test complete!")
    else:
        print("❌ Test failed - Check Magistral connection")

if __name__ == "__main__":
    main()