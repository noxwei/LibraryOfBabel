#!/usr/bin/env python3
"""
🎭 ENHANCED SUBGENRE CLASSIFIER
===============================

Improved classification system with detailed subgenres for better routing.
Replaces overly broad "Fiction" with specific subgenres like "Mystery", "Romance", etc.
"""

import os
import sys
import json
import time
import requests
import psycopg2
from pathlib import Path
from typing import Dict, Optional, Tuple, List

# Add paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))
sys.path.append(str(project_root))

from config.api_config import get_database_config

class EnhancedSubgenreClassifier:
    """
    Enhanced classifier with detailed subgenre taxonomy
    """
    
    def __init__(self):
        self.ollama_base_url = "http://localhost:11434"
        self.db_config = get_database_config()
        
        # ENHANCED GENRE TAXONOMY WITH SUBGENRES
        self.detailed_genres = {
            # Fiction subgenres
            "Literary Fiction": ["literary", "contemporary literature", "literary fiction"],
            "Mystery & Thriller": ["mystery", "thriller", "detective", "crime", "suspense", "noir"],
            "Romance": ["romance", "romantic", "love story"],
            "Historical Fiction": ["historical fiction", "historical novel", "period drama"],
            "Adventure Fiction": ["adventure", "action", "quest"],
            
            # Science Fiction & Fantasy subgenres  
            "Science Fiction": ["science fiction", "sci-fi", "space opera", "cyberpunk", "dystopian"],
            "Fantasy": ["fantasy", "epic fantasy", "urban fantasy", "magical realism"],
            "Dystopian Fiction": ["dystopian", "post-apocalyptic", "utopian"],
            
            # Non-fiction subgenres
            "Philosophy": ["philosophy", "philosophical", "ethics", "metaphysics"],
            "Political Theory": ["political theory", "politics", "government", "democracy"],
            "History": ["history", "historical analysis", "biography", "memoir"],
            "Science & Technology": ["science", "technology", "engineering", "mathematics", "computer science"],
            "Psychology": ["psychology", "neuroscience", "cognitive science", "behavioral"],
            "Business & Economics": ["business", "economics", "finance", "management", "entrepreneurship"],
            "Self-Help & Personal Development": ["self-help", "personal development", "productivity", "lifestyle"],
            
            # Academic & Reference
            "Academic & Scholarly": ["academic", "research", "scholarly", "textbook"],
            "Reference": ["reference", "encyclopedia", "manual", "guide", "handbook"],
            
            # Arts & Culture
            "Arts & Culture": ["art", "music", "film", "cultural studies", "media"],
            "Literature & Criticism": ["literary criticism", "literary theory", "comparative literature"]
        }
        
        # Flatten for easy matching
        self.all_genres = list(self.detailed_genres.keys())

    def get_content_sample(self, book_id: int) -> str:
        """Get content sample for better classification"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT content 
                        FROM chunks 
                        WHERE book_id = %s 
                        ORDER BY chapter_number, section_number 
                        LIMIT 2
                    """, (book_id,))
                    
                    chunks = cur.fetchall()
                    if chunks:
                        content = " ".join([chunk[0] for chunk in chunks])
                        return content[:1500] + "..." if len(content) > 1500 else content
                    
                    return ""
        except Exception:
            return ""

    def classify_with_subgenres(self, title: str, author: str, description: str, content_sample: str) -> Tuple[Optional[str], float, str]:
        """Enhanced classification with subgenre detection"""
        
        # Create comprehensive prompt with subgenres
        genre_list = "\n".join([f"- {genre}" for genre in self.all_genres])
        
        prompt = f"""Classify this book into the MOST SPECIFIC genre from this list:

AVAILABLE GENRES:
{genre_list}

BOOK INFORMATION:
Title: "{title}"
Author: {author}
Description: {description[:400]}
Content Sample: {content_sample[:800]}

ANALYSIS INSTRUCTIONS:
1. Look for specific genre indicators in the title, description, and content
2. Choose the MOST SPECIFIC genre that fits (e.g., "Mystery & Thriller" not just "Fiction")
3. Consider series indicators (e.g., "Mystery Book 6" = Mystery genre)
4. If it's academic/scholarly content, classify as "Academic & Scholarly"
5. If it's clearly non-fiction, choose the appropriate non-fiction category

Respond with EXACTLY ONE genre name from the list above.

GENRE:"""

        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": "magistral",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "max_tokens": 50,
                        "stop": ["\n\n"]
                    }
                },
                timeout=180
            )
            
            if response.status_code == 200:
                result = response.json().get('response', '').strip()
                
                # Find exact genre match
                for genre in self.all_genres:
                    if genre.lower() in result.lower():
                        confidence = 0.9 if genre in result else 0.8
                        return genre, confidence, f"Classified as {genre}"
                
                # Fallback: keyword-based classification
                title_desc = f"{title} {description}".lower()
                
                # Mystery/Thriller indicators
                if any(word in title_desc for word in ["mystery", "thriller", "detective", "crime", "murder", "investigation"]):
                    return "Mystery & Thriller", 0.7, "Keyword-based: Mystery indicators"
                
                # Romance indicators  
                if any(word in title_desc for word in ["romance", "love", "heart", "passion", "wedding"]):
                    return "Romance", 0.7, "Keyword-based: Romance indicators"
                
                # Science Fiction indicators
                if any(word in title_desc for word in ["space", "future", "alien", "robot", "technology", "sci-fi"]):
                    return "Science Fiction", 0.7, "Keyword-based: Sci-fi indicators"
                
                # Fantasy indicators
                if any(word in title_desc for word in ["magic", "dragon", "wizard", "fantasy", "kingdom", "quest"]):
                    return "Fantasy", 0.7, "Keyword-based: Fantasy indicators"
                
                # Philosophy indicators
                if any(word in title_desc for word in ["philosophy", "philosophical", "ethics", "meaning", "existence"]):
                    return "Philosophy", 0.7, "Keyword-based: Philosophy indicators"
                
                # History indicators
                if any(word in title_desc for word in ["history", "historical", "biography", "memoir", "war", "ancient"]):
                    return "History", 0.7, "Keyword-based: History indicators"
                
                # Business indicators
                if any(word in title_desc for word in ["business", "economics", "finance", "management", "entrepreneur"]):
                    return "Business & Economics", 0.7, "Keyword-based: Business indicators"
                
                # Default to Literary Fiction for unclassifiable fiction
                return "Literary Fiction", 0.5, "Default classification"
                
        except Exception as e:
            return None, 0.0, f"Classification error: {e}"

    def update_book_genre(self, book_id: int, genre: str) -> bool:
        """Update book with enhanced genre"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE books 
                        SET genre = %s 
                        WHERE book_id = %s
                    """, (genre, book_id))
                    
                    conn.commit()
                    return cur.rowcount > 0
        except Exception:
            return False

    def reclassify_broad_genres(self):
        """Reclassify books that were too broadly classified"""
        
        print("🎭 ENHANCED SUBGENRE RECLASSIFICATION")
        print("=" * 45)
        print()
        
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    # Find books with overly broad classifications
                    cur.execute("""
                        SELECT book_id, title, author, description
                        FROM books 
                        WHERE genre IN ('Fiction', 'Non-Fiction', 'Literature') 
                        ORDER BY book_id
                    """)
                    
                    books = cur.fetchall()
                    
                    if not books:
                        print("✅ No broadly classified books found")
                        return
                    
                    print(f"📚 Found {len(books)} books with broad classifications")
                    print("🔄 Reclassifying with enhanced subgenres...")
                    print()
                    
                    successful = 0
                    
                    for book_id, title, author, description in books:
                        print(f"📖 Reclassifying book {book_id}: {title[:40]}...")
                        
                        # Get content sample
                        content_sample = self.get_content_sample(book_id)
                        
                        # Enhanced classification
                        genre, confidence, reasoning = self.classify_with_subgenres(
                            title or "", author or "", description or "", content_sample
                        )
                        
                        if genre and confidence > 0.6:
                            if self.update_book_genre(book_id, genre):
                                print(f"   ✅ Updated to: {genre} (confidence: {confidence:.1f})")
                                successful += 1
                            else:
                                print(f"   ❌ Database update failed")
                        else:
                            print(f"   ⚠️  Low confidence: {genre} ({confidence:.1f})")
                        
                        time.sleep(2)  # Be gentle on Magistral
                    
                    print()
                    print(f"🏁 Reclassification complete: {successful}/{len(books)} successful")
                    
        except Exception as e:
            print(f"❌ Reclassification error: {e}")

def main():
    """Enhanced subgenre classification"""
    
    classifier = EnhancedSubgenreClassifier()
    
    print("🎭 ENHANCED SUBGENRE CLASSIFICATION SYSTEM")
    print("=" * 50)
    print()
    print("This will reclassify books with overly broad genres like:")
    print("  • 'Fiction' → 'Mystery & Thriller', 'Romance', etc.")
    print("  • 'Non-Fiction' → 'Philosophy', 'History', etc.")
    print()
    
    response = input("Start enhanced reclassification? (y/N): ").strip().lower()
    
    if response == 'y':
        classifier.reclassify_broad_genres()
    else:
        print("Enhanced classification cancelled")

if __name__ == "__main__":
    main()