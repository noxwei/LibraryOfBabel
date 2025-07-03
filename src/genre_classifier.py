#!/usr/bin/env python3
"""
AI-Powered Genre Classification using Vector Embeddings
Automatically classifies book genres based on content analysis
"""

import psycopg2
import psycopg2.extras
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
import os
from vector_embeddings import VectorEmbeddingGenerator
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GenreClassifier:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': 5432
        }
        
        self.embedding_generator = VectorEmbeddingGenerator()
        
        # Genre definitions with example phrases for embedding comparison
        self.genre_definitions = {
            'Science Fiction': [
                "space exploration", "artificial intelligence", "future technology", 
                "aliens", "robots", "time travel", "spacecraft", "dystopian future",
                "cyberpunk", "genetic engineering", "virtual reality"
            ],
            'Fantasy': [
                "magic", "wizards", "dragons", "mythical creatures", "medieval",
                "elves", "dwarves", "spells", "quest", "kingdoms", "sword and sorcery"
            ],
            'Philosophy': [
                "consciousness", "existence", "ethics", "metaphysics", "epistemology",
                "moral philosophy", "ontology", "phenomenology", "dialectic", "being",
                "truth", "knowledge", "reality", "meaning of life"
            ],
            'Literary Fiction': [
                "character development", "human condition", "relationships", "family",
                "coming of age", "love", "loss", "memory", "identity", "society",
                "contemporary life", "psychological depth"
            ],
            'Non-Fiction': [
                "research", "facts", "analysis", "study", "investigation", "biography",
                "history", "science", "documentation", "evidence", "methodology"
            ],
            'Biography/Memoir': [
                "life story", "personal experience", "childhood", "family history",
                "autobiography", "memories", "growing up", "personal journey"
            ],
            'History': [
                "historical events", "past civilizations", "wars", "politics",
                "cultural history", "ancient", "medieval", "modern history",
                "historical analysis", "timeline", "historical figures"
            ],
            'Psychology': [
                "mental processes", "behavior", "cognitive", "psychological study",
                "mind", "emotions", "personality", "therapy", "mental health",
                "human psychology", "psychological theory"
            ],
            'Politics/Social Science': [
                "government", "policy", "democracy", "political theory", "social issues",
                "economics", "capitalism", "socialism", "political analysis",
                "society", "social justice", "inequality"
            ],
            'Technology': [
                "computers", "programming", "software", "digital", "innovation",
                "technical", "engineering", "algorithms", "data", "internet"
            ]
        }
        
        # Pre-compute genre embeddings
        self.genre_embeddings = {}
        self._compute_genre_embeddings()
    
    def _compute_genre_embeddings(self):
        """Pre-compute embeddings for genre definitions"""
        logger.info("Computing genre embeddings...")
        
        for genre, phrases in self.genre_definitions.items():
            combined_text = " ".join(phrases)
            embedding = self.embedding_generator.generate_embedding(combined_text)
            if embedding:
                self.genre_embeddings[genre] = embedding
                logger.info(f"✅ Generated embedding for {genre}")
            else:
                logger.error(f"❌ Failed to generate embedding for {genre}")
    
    def get_book_content_sample(self, book_id: int, sample_size: int = 5) -> str:
        """Get representative content sample from book chunks"""
        conn = psycopg2.connect(**self.db_config)
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT content 
                FROM chunks 
                WHERE book_id = %s 
                ORDER BY chapter_number, chunk_id 
                LIMIT %s
            """, (book_id, sample_size))
            
            chunks = cursor.fetchall()
            
            # Combine chunks into representative sample
            combined_content = " ".join([chunk[0] for chunk in chunks])
            
            # Truncate to reasonable length for embedding
            if len(combined_content) > 8000:
                combined_content = combined_content[:8000]
            
            return combined_content
            
        except psycopg2.Error as e:
            logger.error(f"Error getting book content: {e}")
            return ""
        finally:
            conn.close()
    
    def classify_book_genre(self, book_id: int, title: str = None) -> Tuple[str, float]:
        """Classify a book's genre based on content analysis"""
        logger.info(f"Classifying genre for book {book_id}: {title}")
        
        # Get content sample
        content_sample = self.get_book_content_sample(book_id)
        if not content_sample:
            logger.error(f"No content found for book {book_id}")
            return "Unknown", 0.0
        
        # Generate embedding for book content
        book_embedding = self.embedding_generator.generate_embedding(content_sample)
        if not book_embedding:
            logger.error(f"Failed to generate embedding for book {book_id}")
            return "Unknown", 0.0
        
        # Compare with genre embeddings
        best_genre = "Unknown"
        best_score = 0.0
        
        for genre, genre_embedding in self.genre_embeddings.items():
            similarity = self.embedding_generator.cosine_similarity(book_embedding, genre_embedding)
            
            logger.info(f"  {genre}: {similarity:.4f}")
            
            if similarity > best_score:
                best_score = similarity
                best_genre = genre
        
        logger.info(f"✅ Best match: {best_genre} (score: {best_score:.4f})")
        return best_genre, best_score
    
    def update_book_genre(self, book_id: int, genre: str, confidence: float) -> bool:
        """Update book genre in database"""
        conn = psycopg2.connect(**self.db_config)
        conn.autocommit = True
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE books 
                SET genre = %s, 
                    genre_confidence = %s,
                    genre_updated = NOW()
                WHERE book_id = %s
            """, (genre, float(confidence), book_id))
            
            return cursor.rowcount > 0
            
        except psycopg2.Error as e:
            logger.error(f"Error updating book genre: {e}")
            return False
        finally:
            conn.close()
    
    def classify_all_books(self, min_confidence: float = 0.3) -> Dict[str, int]:
        """Classify genres for all books in database"""
        conn = psycopg2.connect(**self.db_config)
        
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("""
                SELECT book_id, title, author, genre 
                FROM books 
                ORDER BY book_id
            """)
            
            books = cursor.fetchall()
            logger.info(f"Found {len(books)} books to classify")
            
            results = {
                "classified": 0,
                "skipped": 0,
                "errors": 0,
                "updated": 0
            }
            
            for book in books:
                book_id = book['book_id']
                title = book['title']
                current_genre = book['genre']
                
                try:
                    # Classify genre
                    predicted_genre, confidence = self.classify_book_genre(book_id, title)
                    
                    if confidence >= min_confidence:
                        # Update if confidence is good enough
                        if self.update_book_genre(book_id, predicted_genre, confidence):
                            results["updated"] += 1
                            logger.info(f"✅ Updated {title}: {predicted_genre} ({confidence:.3f})")
                        else:
                            results["errors"] += 1
                        
                        results["classified"] += 1
                    else:
                        logger.info(f"⚠️  Low confidence for {title}: {predicted_genre} ({confidence:.3f})")
                        results["skipped"] += 1
                
                except Exception as e:
                    logger.error(f"Error classifying {title}: {e}")
                    results["errors"] += 1
            
            return results
            
        except psycopg2.Error as e:
            logger.error(f"Error classifying books: {e}")
            return {"error": str(e)}
        finally:
            conn.close()
    
    def add_genre_columns_if_missing(self):
        """Add genre confidence columns if they don't exist"""
        conn = psycopg2.connect(**self.db_config)
        conn.autocommit = True
        
        try:
            cursor = conn.cursor()
            
            # Add genre confidence column
            cursor.execute("""
                ALTER TABLE books 
                ADD COLUMN IF NOT EXISTS genre_confidence FLOAT;
            """)
            
            # Add genre updated timestamp
            cursor.execute("""
                ALTER TABLE books 
                ADD COLUMN IF NOT EXISTS genre_updated TIMESTAMP;
            """)
            
            logger.info("✅ Genre classification columns added")
            
        except psycopg2.Error as e:
            logger.error(f"Error adding columns: {e}")
        finally:
            conn.close()
    
    def get_genre_stats(self) -> Dict:
        """Get statistics about genre classification"""
        conn = psycopg2.connect(**self.db_config)
        
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            cursor.execute("""
                SELECT 
                    genre,
                    COUNT(*) as book_count,
                    ROUND(AVG(genre_confidence), 3) as avg_confidence,
                    ROUND(AVG(word_count)) as avg_word_count
                FROM books 
                WHERE genre IS NOT NULL AND genre != ''
                GROUP BY genre 
                ORDER BY book_count DESC
            """)
            
            genre_stats = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT COUNT(*) FROM books")
            total_books = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) FROM books WHERE genre IS NOT NULL AND genre != ''")
            classified_books = cursor.fetchone()['count']
            
            return {
                "total_books": total_books,
                "classified_books": classified_books,
                "classification_rate": round((classified_books / total_books) * 100, 1) if total_books > 0 else 0,
                "genre_breakdown": genre_stats
            }
            
        except psycopg2.Error as e:
            logger.error(f"Error getting stats: {e}")
            return {}
        finally:
            conn.close()


def main():
    """Main function for genre classification"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI-Powered Genre Classification")
    parser.add_argument("--classify-all", action="store_true", help="Classify all books")
    parser.add_argument("--book-id", type=int, help="Classify specific book")
    parser.add_argument("--stats", action="store_true", help="Show genre statistics")
    parser.add_argument("--min-confidence", type=float, default=0.3, help="Minimum confidence threshold")
    
    args = parser.parse_args()
    
    classifier = GenreClassifier()
    
    # Ensure database has necessary columns
    classifier.add_genre_columns_if_missing()
    
    if args.stats:
        stats = classifier.get_genre_stats()
        print(f"📊 Genre Classification Statistics:")
        print(f"   Total books: {stats.get('total_books', 0)}")
        print(f"   Classified: {stats.get('classified_books', 0)}")
        print(f"   Classification rate: {stats.get('classification_rate', 0)}%")
        print(f"\n📚 Genre Breakdown:")
        for genre_info in stats.get('genre_breakdown', []):
            print(f"   {genre_info['genre']}: {genre_info['book_count']} books "
                  f"(confidence: {genre_info['avg_confidence']})")
    
    elif args.classify_all:
        print("🤖 Starting AI genre classification for all books...")
        results = classifier.classify_all_books(args.min_confidence)
        print(f"✅ Classification complete!")
        print(f"   Classified: {results.get('classified', 0)}")
        print(f"   Updated: {results.get('updated', 0)}")
        print(f"   Skipped: {results.get('skipped', 0)}")
        print(f"   Errors: {results.get('errors', 0)}")
    
    elif args.book_id:
        genre, confidence = classifier.classify_book_genre(args.book_id)
        print(f"📖 Book {args.book_id}: {genre} (confidence: {confidence:.3f})")
        if confidence >= args.min_confidence:
            classifier.update_book_genre(args.book_id, genre, confidence)
            print("✅ Genre updated in database")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()