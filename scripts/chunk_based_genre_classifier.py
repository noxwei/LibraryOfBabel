#!/usr/bin/env python3
"""
Chunk-Based Genre Classification
===============================
For books without descriptions, use Ollama to classify genre by sampling random chunks
"""

import sys
import json
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import re
import random
import time

sys.path.append('/Users/weixiangzhang/Local Dev/LibraryOfBabel')
from config.api_config import get_database_config

class ChunkBasedClassifier:
    def __init__(self, model_name="magistral"):
        self.db_config = get_database_config()
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = model_name
        self.processed_count = 0
        self.reclassified_count = 0
        
        # Valid genres
        self.valid_genres = [
            "Romance", "Literary Fiction", "Science Fiction", "Fantasy",
            "Mystery & Thriller", "Historical Fiction", "Contemporary Fiction",
            "Self-Help", "Biography & Memoir", "Psychology", "Philosophy",
            "Business & Economics", "History", "Science & Nature",
            "Programming & Technology", "Data Science & Analytics",
            "Religion & Spirituality", "Political Science"
        ]
    
    def get_books_without_descriptions(self, current_genre=None, limit=50):
        """Get books that have no description but have chunks"""
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        
        try:
            with conn.cursor() as cur:
                if current_genre:
                    # Focus on specific genre
                    cur.execute("""
                        SELECT b.book_id, b.title, b.author, b.genre
                        FROM books b
                        WHERE EXISTS (
                            SELECT 1 FROM chunks c 
                            WHERE c.book_id = b.book_id 
                            AND c.content IS NOT NULL 
                            AND LENGTH(c.content) > 200
                        )
                        AND (b.description IS NULL OR b.description = '')
                        AND b.genre = %s
                        ORDER BY RANDOM()
                        LIMIT %s
                    """, (current_genre, limit))
                else:
                    # All books without descriptions
                    cur.execute("""
                        SELECT b.book_id, b.title, b.author, b.genre
                        FROM books b
                        WHERE EXISTS (
                            SELECT 1 FROM chunks c 
                            WHERE c.book_id = b.book_id 
                            AND c.content IS NOT NULL 
                            AND LENGTH(c.content) > 200
                        )
                        AND (b.description IS NULL OR b.description = '')
                        ORDER BY RANDOM()
                        LIMIT %s
                    """, (limit,))
                
                return cur.fetchall()
        finally:
            conn.close()
    
    def get_random_chunks(self, book_id, num_chunks=3):
        """Get random chunks from a book for analysis"""
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        
        try:
            with conn.cursor() as cur:
                # Get random chunks with substantial content
                cur.execute("""
                    SELECT content, title
                    FROM chunks
                    WHERE book_id = %s
                    AND content IS NOT NULL
                    AND LENGTH(content) > 150
                    ORDER BY RANDOM()
                    LIMIT %s
                """, (book_id, num_chunks))
                
                chunks = cur.fetchall()
                
                # Clean and combine chunks
                combined_content = ""
                for i, chunk in enumerate(chunks, 1):
                    # Clean HTML and formatting
                    clean_content = re.sub(r'<[^>]+>', '', chunk['content'])
                    clean_content = re.sub(r'\s+', ' ', clean_content).strip()
                    
                    # Take first 300 characters of each chunk
                    sample = clean_content[:300]
                    combined_content += f"[Sample {i}] {sample}\n\n"
                
                return combined_content.strip()
        finally:
            conn.close()
    
    def classify_by_chunks(self, book_data, content_samples):
        """Use Ollama to classify genre based on content chunks"""
        
        prompt = f"""You are a professional book genre classifier. Analyze this book's content to determine its genre.

BOOK INFORMATION:
Title: "{book_data['title']}"
Author: {book_data['author']}
Current Classification: {book_data['genre']}

CONTENT SAMPLES FROM THE BOOK:
{content_samples}

AVAILABLE GENRES:
• Romance - Fiction focused on romantic relationships with HEA/HFN endings
• Literary Fiction - Character-driven fiction with literary merit and artistic writing
• Science Fiction - Fiction with futuristic technology, space, aliens, or sci-fi concepts
• Fantasy - Fiction with magic, supernatural elements, or imaginary worlds
• Mystery & Thriller - Fiction focused on solving crimes or creating suspense
• Historical Fiction - Fiction set in the past, recreating historical periods
• Contemporary Fiction - Modern realistic fiction set in present day
• Self-Help - Non-fiction for personal improvement and development
• Biography & Memoir - Non-fiction accounts of real people's lives
• Psychology - Non-fiction about human behavior and mental health
• Philosophy - Non-fiction exploring fundamental questions about existence
• Business & Economics - Non-fiction about business, economics, and finance
• History - Non-fiction about past events and civilizations
• Science & Nature - Non-fiction about scientific discoveries and natural world
• Programming & Technology - Non-fiction about computer programming and technology
• Data Science & Analytics - Non-fiction about data analysis and statistics
• Religion & Spirituality - Non-fiction about religious or spiritual topics
• Political Science - Non-fiction about politics, government, and political theory

CLASSIFICATION RULES:
1. Base classification on the ACTUAL CONTENT, not just the title
2. Look for key indicators in the writing style and subject matter
3. Fiction vs Non-fiction: Is this telling a story or providing information?
4. If fiction, what's the primary genre elements (romance, sci-fi, fantasy, etc.)?
5. If non-fiction, what's the main subject area?
6. Choose the MOST SPECIFIC category that fits the content

Based on the content samples above, what is the most accurate genre classification?

Respond with ONLY the genre name (e.g., "Science Fiction" or "Psychology")"""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9
                    }
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                classification = result['response'].strip()
                
                # Extract classification from Ollama response
                if "\\boxed{" in classification:
                    match = re.search(r'\\boxed\{([^}]+)\}', classification)
                    if match:
                        classification = match.group(1)
                else:
                    # Take the last meaningful line
                    lines = [line.strip() for line in classification.split('\n') if line.strip()]
                    classification = lines[-1] if lines else classification
                
                # Clean up
                classification = re.sub(r'^["\']|["\']$', '', classification)
                classification = classification.strip()
                
                # Validate against known genres
                if classification in self.valid_genres:
                    return classification
                else:
                    # Try partial matching
                    for valid_genre in self.valid_genres:
                        if valid_genre.lower() in classification.lower():
                            return valid_genre
                    
                    print(f"   ⚠️  Invalid classification: '{classification}'")
                    return None
            else:
                print(f"   ❌ Ollama request failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Classification error: {e}")
            return None
    
    def update_book_genre(self, book_id, new_genre):
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
    
    def process_books_by_chunks(self, target_genre="Literary Fiction", limit=20):
        """Process books without descriptions using chunk analysis"""
        print(f"📚 CHUNK-BASED CLASSIFICATION: {target_genre}")
        print("=" * 60)
        
        # Get books without descriptions
        books = self.get_books_without_descriptions(target_genre, limit)
        
        if not books:
            print(f"No books found in {target_genre} without descriptions")
            return 0
        
        print(f"Found {len(books)} books in {target_genre} without descriptions")
        print("Analyzing content chunks for proper classification...\n")
        
        for book in books:
            print(f"📖 Processing: \"{book['title']}\"")
            print(f"   Author: {book['author']}")
            print(f"   Current: {book['genre']}")
            
            # Get content samples
            content_samples = self.get_random_chunks(book['book_id'], 3)
            
            if not content_samples or len(content_samples) < 100:
                print(f"   ⚠️  Insufficient content for analysis")
                continue
            
            print(f"   📄 Content sample: {content_samples[:100]}...")
            
            # Classify using content
            new_genre = self.classify_by_chunks(book, content_samples)
            
            if new_genre:
                print(f"   🤖 Ollama classification: {new_genre}")
                
                if new_genre != book['genre']:
                    if self.update_book_genre(book['book_id'], new_genre):
                        print(f"   ✅ Updated: {book['genre']} → {new_genre}")
                        self.reclassified_count += 1
                    else:
                        print(f"   ❌ Failed to update")
                else:
                    print(f"   ⚪ Confirmed: {new_genre}")
            else:
                print(f"   ❌ Classification failed")
            
            self.processed_count += 1
            print()
            time.sleep(1)  # Rate limiting
        
        return self.reclassified_count
    
    def show_books_without_descriptions_stats(self):
        """Show statistics about books without descriptions"""
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        
        try:
            with conn.cursor() as cur:
                # Count books without descriptions by genre
                cur.execute("""
                    SELECT 
                        b.genre,
                        COUNT(*) as total_books,
                        COUNT(CASE WHEN b.description IS NULL OR b.description = '' THEN 1 END) as no_description,
                        COUNT(CASE WHEN c.book_id IS NOT NULL THEN 1 END) as has_chunks
                    FROM books b
                    LEFT JOIN (SELECT DISTINCT book_id FROM chunks WHERE content IS NOT NULL) c 
                        ON b.book_id = c.book_id
                    GROUP BY b.genre
                    HAVING COUNT(CASE WHEN b.description IS NULL OR b.description = '' THEN 1 END) > 0
                    ORDER BY no_description DESC
                """)
                
                results = cur.fetchall()
                
                print("📊 BOOKS WITHOUT DESCRIPTIONS BY GENRE")
                print("=" * 60)
                print(f"{'Genre':<25} {'Total':<8} {'No Desc':<8} {'Has Chunks':<12} {'%':<6}")
                print("-" * 60)
                
                total_no_desc = 0
                for row in results:
                    genre = row['genre'][:24]
                    total = row['total_books']
                    no_desc = row['no_description']
                    has_chunks = row['has_chunks']
                    percent = (no_desc / total) * 100 if total > 0 else 0
                    
                    print(f"{genre:<25} {total:<8} {no_desc:<8} {has_chunks:<12} {percent:<5.1f}%")
                    total_no_desc += no_desc
                
                print("-" * 60)
                print(f"TOTAL BOOKS WITHOUT DESCRIPTIONS: {total_no_desc}")
                
        finally:
            conn.close()

def main():
    """Execute chunk-based genre classification"""
    print("📚 CHUNK-BASED GENRE CLASSIFICATION")
    print("=" * 45)
    print("Classifying books without descriptions using content chunks")
    print()
    
    classifier = ChunkBasedClassifier("magistral")
    
    # Show statistics first
    classifier.show_books_without_descriptions_stats()
    
    print("\n" + "="*60 + "\n")
    
    # Process Literary Fiction books without descriptions
    literary_fixes = classifier.process_books_by_chunks("Literary Fiction", 15)
    
    print(f"\n📋 SUMMARY:")
    print(f"   Books processed: {classifier.processed_count}")
    print(f"   Reclassified: {classifier.reclassified_count}")
    
    if classifier.processed_count > 0:
        accuracy = ((classifier.processed_count - classifier.reclassified_count) / classifier.processed_count) * 100
        print(f"   Accuracy rate: {accuracy:.1f}%")
    
    return classifier.reclassified_count > 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)