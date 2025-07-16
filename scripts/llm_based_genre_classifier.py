#!/usr/bin/env python3
"""
LLM-Based Genre Classification System
====================================

Use Ollama models for intelligent genre classification:
- Magistral (14GB) for complex analysis  
- Llama3.2:3b (2GB) for faster processing
- Proper genre definitions and consistent logic
"""

import sys
import json
import time
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import re
from typing import Dict, List, Optional

sys.path.append('/Users/weixiangzhang/Local Dev/LibraryOfBabel')
from config.api_config import get_database_config

class LLMGenreClassifier:
    def __init__(self, model_name="magistral"):
        self.db_config = get_database_config()
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = model_name
        self.processed_count = 0
        self.reclassified_count = 0
        
        # Define proper genre categories with clear criteria
        self.genre_definitions = {
            "Romance": {
                "description": "Fiction focused on romantic relationships with Happily Ever After (HEA) or Happy For Now (HFN) endings",
                "keywords": ["love", "romance", "relationship", "dating", "marriage", "passion", "heart"],
                "examples": ["contemporary romance", "historical romance", "paranormal romance"]
            },
            "Literary Fiction": {
                "description": "Character-driven fiction with literary merit, complex themes, and artistic writing style",
                "keywords": ["literary", "character study", "prose", "human condition", "award-winning"],
                "examples": ["Booker Prize winners", "character-driven narratives", "experimental fiction"]
            },
            "Science Fiction": {
                "description": "Fiction featuring futuristic technology, space travel, aliens, or scientific concepts",
                "keywords": ["space", "future", "technology", "alien", "robot", "cyberpunk", "dystopia"],
                "examples": ["space opera", "cyberpunk", "hard sci-fi", "dystopian fiction"]
            },
            "Fantasy": {
                "description": "Fiction with magical or supernatural elements in imaginary worlds",
                "keywords": ["magic", "dragon", "wizard", "fantasy", "supernatural", "mythical"],
                "examples": ["epic fantasy", "urban fantasy", "magical realism"]
            },
            "Mystery & Thriller": {
                "description": "Fiction focused on solving crimes or creating suspense",
                "keywords": ["murder", "detective", "crime", "mystery", "suspense", "thriller"],
                "examples": ["cozy mystery", "police procedural", "psychological thriller"]
            },
            "Historical Fiction": {
                "description": "Fiction set in the past, recreating historical periods",
                "keywords": ["historical", "period", "war", "ancient", "medieval"],
                "examples": ["WWII fiction", "Victorian era", "ancient Rome"]
            },
            "Biography & Memoir": {
                "description": "Non-fiction accounts of real people's lives",
                "keywords": ["biography", "memoir", "autobiography", "life story"],
                "examples": ["celebrity memoirs", "political biographies", "personal narratives"]
            },
            "Self-Help": {
                "description": "Non-fiction books for personal improvement and development",
                "keywords": ["self-help", "improvement", "success", "habits", "productivity"],
                "examples": ["productivity guides", "relationship advice", "career development"]
            },
            "Business & Economics": {
                "description": "Non-fiction about business, economics, finance, and markets",
                "keywords": ["business", "economics", "finance", "market", "capitalism", "entrepreneurship"],
                "examples": ["business strategy", "economic theory", "financial advice"]
            },
            "Psychology": {
                "description": "Non-fiction about human behavior, mental health, and psychological science",
                "keywords": ["psychology", "mental health", "behavior", "cognitive", "therapy"],
                "examples": ["cognitive science", "behavioral economics", "mental health guides"]
            },
            "Philosophy": {
                "description": "Non-fiction exploring fundamental questions about existence, knowledge, and ethics",
                "keywords": ["philosophy", "ethics", "metaphysics", "existential", "moral"],
                "examples": ["ancient philosophy", "modern ethics", "existentialism"]
            },
            "History": {
                "description": "Non-fiction accounts of past events, periods, and civilizations",
                "keywords": ["history", "historical", "war", "civilization", "ancient", "past"],
                "examples": ["military history", "social history", "ancient civilizations"]
            },
            "Science & Nature": {
                "description": "Non-fiction about scientific discoveries, natural world, and environmental topics",
                "keywords": ["science", "nature", "environment", "biology", "physics", "climate"],
                "examples": ["popular science", "environmental studies", "natural history"]
            },
            "Programming & Technology": {
                "description": "Non-fiction about computer programming, software development, and technology",
                "keywords": ["programming", "code", "software", "algorithm", "computer", "technology"],
                "examples": ["coding tutorials", "software engineering", "tech industry"]
            },
            "Data Science & Analytics": {
                "description": "Non-fiction about data analysis, statistics, and data-driven insights",
                "keywords": ["data", "analytics", "statistics", "machine learning", "analysis"],
                "examples": ["data visualization", "statistical analysis", "big data"]
            }
        }
    
    def create_classification_prompt(self, book_data: Dict) -> str:
        """Create a structured prompt for LLM classification"""
        
        # Build genre options with definitions
        genre_options = ""
        for genre, info in self.genre_definitions.items():
            genre_options += f"\n{genre}: {info['description']}"
        
        prompt = f"""You are a professional book genre classifier. Analyze this book and determine its most accurate genre classification.

BOOK TO CLASSIFY:
Title: "{book_data['title']}"
Author: {book_data['author']}
Description: {book_data.get('description', 'No description available')[:500]}
Content Sample: {book_data.get('content_sample', 'No content available')[:300]}

AVAILABLE GENRES:{genre_options}

CLASSIFICATION RULES:
1. ROMANCE: Must have romantic relationship as PRIMARY plot focus with HEA/HFN ending
2. LITERARY FICTION: Character-driven fiction with artistic merit, NOT a catch-all category
3. NON-FICTION: Prioritize specific categories (Business, Psychology, etc.) over broad ones
4. FICTION vs NON-FICTION: Distinguish clearly between fictional stories and factual content
5. BE SPECIFIC: Choose the most precise category that fits

ANALYSIS PROCESS:
1. Is this fiction or non-fiction?
2. If fiction: What is the primary plot focus?
3. If non-fiction: What is the main subject matter?
4. Which genre best matches the primary content?

Based on the title, description, and content, classify this book into the MOST ACCURATE single genre.

RESPOND WITH ONLY THE GENRE NAME (e.g., "Science Fiction" or "Business & Economics")"""

        return prompt
    
    def get_book_content_sample(self, book_id: int) -> Dict:
        """Get book data including description and content sample"""
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        try:
            with conn.cursor() as cur:
                # Get book details
                cur.execute("""
                    SELECT book_id, title, author, description, genre
                    FROM books 
                    WHERE book_id = %s
                """, (book_id,))
                book_info = cur.fetchone()
                
                if not book_info:
                    return None
                
                # Get content sample from chunks
                cur.execute("""
                    SELECT content
                    FROM chunks 
                    WHERE book_id = %s
                    ORDER BY chunk_id
                    LIMIT 2
                """, (book_id,))
                chunks = cur.fetchall()
                
                # Clean and combine content
                content_sample = ""
                if chunks:
                    for chunk in chunks:
                        if chunk['content']:
                            clean_content = re.sub(r'<[^>]+>', '', chunk['content'])  # Remove HTML
                            content_sample += clean_content[:200] + " "
                
                # Clean description
                description = ""
                if book_info['description']:
                    description = re.sub(r'<[^>]+>', '', book_info['description'])
                
                return {
                    'book_id': book_info['book_id'],
                    'title': book_info['title'],
                    'author': book_info['author'],
                    'description': description,
                    'content_sample': content_sample.strip(),
                    'current_genre': book_info['genre']
                }
        finally:
            conn.close()
    
    def classify_with_llm(self, book_data: Dict) -> Optional[str]:
        """Use LLM to classify the book"""
        prompt = self.create_classification_prompt(book_data)
        
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistency
                        "top_p": 0.9
                    }
                },
                timeout=180  # Increased timeout for Magistral
            )
            
            if response.status_code == 200:
                result = response.json()
                classification = result['response'].strip()
                
                # Clean up the response - handle Magistral's verbose output
                if "**Final Answer:**" in classification:
                    # Extract from Final Answer section
                    classification = classification.split("**Final Answer:**")[-1].strip()
                elif "\\boxed{" in classification:
                    # Extract from boxed answer
                    import re
                    match = re.search(r'\\boxed\{([^}]+)\}', classification)
                    if match:
                        classification = match.group(1)
                else:
                    # Take last line which usually has the answer
                    classification = classification.split('\n')[-1].strip()
                
                # Remove quotes and extra formatting
                classification = re.sub(r'^["\']|["\']$', '', classification)
                classification = classification.strip()
                
                # Validate classification
                if classification in self.genre_definitions:
                    return classification
                else:
                    # Try partial matching for common variations
                    for valid_genre in self.genre_definitions.keys():
                        if valid_genre.lower() in classification.lower():
                            return valid_genre
                    
                    print(f"   ⚠️  Invalid classification: {classification}")
                    return None
            else:
                print(f"   ❌ LLM request failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ LLM error: {e}")
            return None
    
    def update_book_genre(self, book_id: int, new_genre: str) -> bool:
        """Update book genre in database"""
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE books 
                    SET genre = %s
                    WHERE book_id = %s
                """, (new_genre, book_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"   ❌ Database update failed: {e}")
            return False
        finally:
            conn.close()
    
    def test_classification_quality(self, sample_size: int = 10):
        """Test classification quality on a sample"""
        print(f"🧪 TESTING LLM CLASSIFICATION QUALITY ({self.model_name})")
        print("=" * 60)
        
        # Get sample of books from different genres
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT book_id, title, genre
                    FROM books 
                    WHERE genre IN ('Romance', 'Literary Fiction', 'Science Fiction', 'Self-Help')
                    ORDER BY RANDOM()
                    LIMIT %s
                """, (sample_size,))
                
                test_books = cur.fetchall()
        finally:
            conn.close()
        
        print(f"Testing {len(test_books)} books...")
        
        accurate_count = 0
        for book in test_books:
            print(f"\n📖 Testing: \"{book['title']}\"")
            print(f"   Current: {book['genre']}")
            
            # Get book data
            book_data = self.get_book_content_sample(book['book_id'])
            if not book_data:
                continue
            
            # Classify
            new_genre = self.classify_with_llm(book_data)
            if new_genre:
                print(f"   LLM Says: {new_genre}")
                if new_genre == book['genre']:
                    print(f"   ✅ MATCH")
                    accurate_count += 1
                else:
                    print(f"   🔄 DIFFERENT")
            else:
                print(f"   ❌ FAILED")
        
        accuracy = (accurate_count / len(test_books)) * 100
        print(f"\n📊 Accuracy: {accurate_count}/{len(test_books)} ({accuracy:.1f}%)")
        
        return accuracy > 70  # 70% accuracy threshold
    
    def reclassify_problematic_books(self, target_genres: List[str], limit: int = 50):
        """Reclassify books from specific problematic genres"""
        print(f"\n🔄 RECLASSIFYING BOOKS FROM: {', '.join(target_genres)}")
        print("=" * 60)
        
        # Get books from target genres
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        try:
            with conn.cursor() as cur:
                placeholders = ','.join(['%s'] * len(target_genres))
                cur.execute(f"""
                    SELECT book_id, title, author, genre
                    FROM books 
                    WHERE genre IN ({placeholders})
                    ORDER BY RANDOM()
                    LIMIT %s
                """, target_genres + [limit])
                
                books_to_reclassify = cur.fetchall()
        finally:
            conn.close()
        
        print(f"Processing {len(books_to_reclassify)} books...")
        
        for book in books_to_reclassify:
            print(f"\n📚 Processing: \"{book['title']}\"")
            print(f"   Current: {book['genre']}")
            
            # Get enhanced book data
            book_data = self.get_book_content_sample(book['book_id'])
            if not book_data:
                continue
            
            # Classify with LLM
            new_genre = self.classify_with_llm(book_data)
            if not new_genre:
                continue
            
            # Update if different
            if new_genre != book['genre']:
                if self.update_book_genre(book['book_id'], new_genre):
                    print(f"   ✅ {book['genre']} → {new_genre}")
                    self.reclassified_count += 1
                else:
                    print(f"   ❌ Update failed")
            else:
                print(f"   ⚪ Confirmed: {new_genre}")
            
            self.processed_count += 1
            time.sleep(0.5)  # Rate limiting
        
        return self.reclassified_count
    
    def generate_classification_report(self):
        """Generate classification report"""
        print(f"\n📋 LLM CLASSIFICATION REPORT ({self.model_name.upper()})")
        print("=" * 50)
        print(f"📊 Books Processed: {self.processed_count}")
        print(f"🔄 Reclassified: {self.reclassified_count}")
        
        if self.processed_count > 0:
            accuracy = ((self.processed_count - self.reclassified_count) / self.processed_count) * 100
            print(f"✅ Accuracy Rate: {accuracy:.1f}%")
        
        # Show updated distribution
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT genre, COUNT(*) as count
                    FROM books 
                    GROUP BY genre
                    ORDER BY count DESC
                    LIMIT 10
                """)
                
                results = cur.fetchall()
                
                print(f"\n📊 Updated Top Genres:")
                for row in results:
                    print(f"   • {row['genre']}: {row['count']} books")
        finally:
            conn.close()

def main():
    """Execute LLM-based genre classification"""
    print("🤖 LLM-BASED GENRE CLASSIFICATION")
    print("=" * 40)
    
    # Use Magistral for accuracy (as user requested)
    model_name = "magistral"
    print("Using Magistral (14GB) for maximum accuracy")
    
    classifier = LLMGenreClassifier(model_name)
    
    # Test quality first
    print("\n🧪 Testing classification quality...")
    if not classifier.test_classification_quality(5):
        print("❌ Classification quality too low, aborting")
        return False
    
    # Reclassify problematic genres
    target_genres = ["Romance", "Literary Fiction"]
    limit = 30  # Process 30 books for thorough but manageable scope
    
    print(f"\n🎯 Will reclassify {limit} books from Romance & Literary Fiction")
    
    classifier.reclassify_problematic_books(target_genres, limit)
    classifier.generate_classification_report()
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)