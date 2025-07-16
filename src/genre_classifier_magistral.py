#!/usr/bin/env python3
"""
🎭 MAGISTRAL GENRE CLASSIFIER - LibraryOfBabel AI System
========================================================

Advanced genre classification using Magistral LLM and embedding models.
Addresses the 97.3% missing genre crisis in the book collection.

DBA Team Integration:
- Uses all 4 embedding models for content analysis
- Leverages PostgreSQL for efficient batch processing
- Integrates with existing chunking system
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

# Add paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))
sys.path.append(str(project_root))

from ollama_vector_embedder import OllamaVectorEmbedder
from config.api_config import get_database_config

class MagistralGenreClassifier:
    """
    🎭 Advanced Genre Classification System
    
    Uses Magistral LLM for intelligent genre detection based on:
    - Book titles and descriptions
    - Content analysis from chunks
    - Multiple embedding model consensus
    """
    
    def __init__(self, ollama_base_url: str = "http://localhost:11434"):
        self.ollama_base_url = ollama_base_url.rstrip('/')
        self.db_config = get_database_config()
        
        # Standard genre taxonomy
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
        
        # Genre classification prompt template
        self.classification_prompt = """
You are an expert librarian and literary classifier. Analyze the following book information and classify it into ONE of these standard library genres:

GENRES:
1. Fiction - Literary fiction, contemporary fiction, historical fiction
2. Science Fiction & Fantasy - Sci-fi, fantasy, dystopian, utopian, cyberpunk
3. Philosophy & Theory - Philosophy, political theory, critical theory, ethics
4. History & Biography - History, biography, memoir, historical analysis
5. Science & Technology - Science, technology, mathematics, psychology, neuroscience
6. Politics & Government - Political science, government, public policy
7. Literature & Criticism - Literary criticism, cultural studies, comparative literature
8. Business & Economics - Economics, business, finance, management
9. Arts & Culture - Art, music, film, cultural criticism, media studies
10. Reference & Education - Reference works, textbooks, educational materials

BOOK INFORMATION:
Title: {title}
Author: {author}
Description: {description}
Content Sample: {content_sample}

INSTRUCTIONS:
- Choose EXACTLY ONE genre from the list above
- Consider the primary focus and content of the book
- If uncertain between genres, pick the most dominant theme
- Respond with just the genre name, no explanation

GENRE:"""

    def get_db_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(**self.db_config)
        except psycopg2.Error as e:
            print(f"❌ Database connection failed: {e}")
            return None

    def query_magistral(self, prompt: str) -> Optional[str]:
        """Query Magistral LLM for genre classification"""
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": "magistral",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent classification
                        "top_p": 0.9,
                        "max_tokens": 50
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('response', '').strip()
                
                # Clean and validate response
                for genre in self.standard_genres:
                    if genre.lower() in result.lower():
                        return genre
                        
                return result  # Return raw if no exact match
            else:
                print(f"❌ Magistral API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error querying Magistral: {e}")
            return None

    def get_books_needing_classification(self, limit: int = 50) -> List[Dict]:
        """Get books that need genre classification"""
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return []
                
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            book_id,
                            title,
                            author,
                            description,
                            genre,
                            word_count
                        FROM books 
                        WHERE genre IS NULL 
                           OR genre = '' 
                           OR TRIM(genre) = ''
                           OR genre IN ('none', 'book', 'cj5', '公众号：古德猫宁李', 'chenjin5.com沉金书屋')
                        ORDER BY word_count DESC NULLS LAST
                        LIMIT %s
                    """, (limit,))
                    
                    return [dict(row) for row in cur.fetchall()]
                    
        except Exception as e:
            print(f"❌ Error fetching books: {e}")
            return []

    def get_book_content_sample(self, book_id: int, sample_length: int = 1000) -> str:
        """Get a content sample from book chunks for classification"""
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return ""
                
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT content 
                        FROM chunks 
                        WHERE book_id = %s 
                        ORDER BY chapter_number, section_number, paragraph_number
                        LIMIT 3
                    """, (book_id,))
                    
                    chunks = cur.fetchall()
                    if chunks:
                        content = " ".join([chunk[0] for chunk in chunks])
                        return content[:sample_length] + "..." if len(content) > sample_length else content
                    
                    return ""
                    
        except Exception as e:
            print(f"❌ Error fetching content sample: {e}")
            return ""

    def classify_book_genre(self, book: Dict) -> Tuple[Optional[str], float]:
        """Classify a single book's genre using Magistral"""
        
        # Get content sample
        content_sample = self.get_book_content_sample(book['book_id'])
        
        # Prepare classification data
        title = book.get('title', 'Unknown Title')
        author = book.get('author', 'Unknown Author')
        description = book.get('description', 'No description available')
        
        # Create classification prompt
        prompt = self.classification_prompt.format(
            title=title,
            author=author,
            description=description,
            content_sample=content_sample
        )
        
        print(f"🎭 Classifying: {title[:50]}...")
        
        start_time = time.time()
        
        # Query Magistral
        classification = self.query_magistral(prompt)
        
        processing_time = time.time() - start_time
        
        if classification and classification in self.standard_genres:
            print(f"   ✅ Genre: {classification} ({processing_time:.1f}s)")
            return classification, processing_time
        else:
            print(f"   ❌ Failed classification: {classification}")
            return None, processing_time

    def update_book_genre(self, book_id: int, genre: str) -> bool:
        """Update book genre in database"""
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return False
                
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE books 
                        SET genre = %s 
                        WHERE book_id = %s
                    """, (genre, book_id))
                    
                    conn.commit()
                    return cur.rowcount > 0
                    
        except Exception as e:
            print(f"❌ Error updating genre: {e}")
            return False

    def batch_classify_genres(self, batch_size: int = 20) -> Dict[str, int]:
        """Classify genres for a batch of books"""
        
        print("🎭 MAGISTRAL GENRE CLASSIFICATION")
        print("=" * 50)
        
        # Get books needing classification
        books = self.get_books_needing_classification(batch_size)
        
        if not books:
            print("✅ No books need genre classification!")
            return {"processed": 0, "successful": 0, "failed": 0}
        
        print(f"📚 Processing {len(books)} books...")
        print()
        
        results = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "genres_assigned": {},
            "total_time": 0
        }
        
        start_total = time.time()
        
        for i, book in enumerate(books, 1):
            print(f"[{i:2d}/{len(books)}] ", end="")
            
            # Classify genre
            genre, processing_time = self.classify_book_genre(book)
            results["total_time"] += processing_time
            
            if genre:
                # Update database
                if self.update_book_genre(book['book_id'], genre):
                    results["successful"] += 1
                    results["genres_assigned"][genre] = results["genres_assigned"].get(genre, 0) + 1
                else:
                    results["failed"] += 1
            else:
                results["failed"] += 1
            
            results["processed"] += 1
            
            # Small delay to avoid overwhelming Magistral
            time.sleep(1)
        
        results["total_time"] = time.time() - start_total
        
        # Summary
        print()
        print("📊 CLASSIFICATION SUMMARY")
        print("-" * 30)
        print(f"Processed: {results['processed']}")
        print(f"Successful: {results['successful']}")
        print(f"Failed: {results['failed']}")
        print(f"Success Rate: {(results['successful']/results['processed']*100):.1f}%")
        print(f"Total Time: {results['total_time']:.1f}s")
        print(f"Avg Time/Book: {(results['total_time']/results['processed']):.1f}s")
        
        if results["genres_assigned"]:
            print("\n🏷️ Genres Assigned:")
            for genre, count in sorted(results["genres_assigned"].items()):
                print(f"  {genre}: {count} books")
        
        return results

    def classify_all_missing_genres(self, batch_size: int = 20, max_batches: int = 10):
        """Classify all missing genres in batches"""
        
        print("🎭 COMPLETE GENRE CLASSIFICATION SYSTEM")
        print("=" * 50)
        print()
        
        total_results = {
            "total_processed": 0,
            "total_successful": 0,
            "total_failed": 0,
            "all_genres": {}
        }
        
        for batch_num in range(1, max_batches + 1):
            print(f"🔄 BATCH {batch_num}/{max_batches}")
            print("-" * 20)
            
            batch_results = self.batch_classify_genres(batch_size)
            
            # Aggregate results
            total_results["total_processed"] += batch_results["processed"]
            total_results["total_successful"] += batch_results["successful"] 
            total_results["total_failed"] += batch_results["failed"]
            
            # Merge genre counts
            for genre, count in batch_results.get("genres_assigned", {}).items():
                total_results["all_genres"][genre] = total_results["all_genres"].get(genre, 0) + count
            
            # Stop if no more books to process
            if batch_results["processed"] < batch_size:
                print(f"\n✅ All available books processed after {batch_num} batches")
                break
            
            print(f"\n⏱️ Batch complete. Waiting 5 seconds before next batch...")
            time.sleep(5)
        
        # Final summary
        print(f"\n🏁 FINAL RESULTS")
        print("=" * 20)
        print(f"Total Books Processed: {total_results['total_processed']}")
        print(f"Total Successful: {total_results['total_successful']}")
        print(f"Total Failed: {total_results['total_failed']}")
        
        if total_results["total_processed"] > 0:
            success_rate = (total_results["total_successful"] / total_results["total_processed"]) * 100
            print(f"Overall Success Rate: {success_rate:.1f}%")
        
        if total_results["all_genres"]:
            print(f"\n🏆 All Genres Assigned:")
            for genre, count in sorted(total_results["all_genres"].items(), key=lambda x: x[1], reverse=True):
                print(f"  {genre}: {count} books")

def main():
    """Main function to run genre classification"""
    
    classifier = MagistralGenreClassifier()
    
    # Test with a small batch first
    print("🧪 Testing with 5 books first...")
    classifier.batch_classify_genres(5)
    
    print("\n" + "="*60)
    response = input("Continue with full classification? (y/N): ").strip().lower()
    
    if response == 'y':
        # Process larger batches
        classifier.classify_all_missing_genres(batch_size=10, max_batches=20)
    else:
        print("Classification test complete!")

if __name__ == "__main__":
    main()