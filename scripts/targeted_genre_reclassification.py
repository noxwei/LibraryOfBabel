#!/usr/bin/env python3
"""
Targeted Genre Reclassification: Romance & Literary Fiction
============================================================

Reprocess misclassified books using enhanced content analysis:
- Use book descriptions + small content chunks 
- Apply more precise genre classification
- Focus on data/business books incorrectly marked as Romance
- Break down overly broad Literary Fiction category
"""

import sys
import json
import time
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import re

sys.path.append('/Users/weixiangzhang/Local Dev/LibraryOfBabel')
from config.api_config import get_database_config

class TargetedGenreReclassifier:
    def __init__(self):
        self.db_config = get_database_config()
        self.magistral_url = "http://localhost:11434/api/generate"
        self.processed_count = 0
        self.reclassified_count = 0
        self.results = {
            'romance_fixes': [],
            'litfic_refinements': [],
            'new_genres_discovered': set()
        }
    
    def get_enhanced_content_sample(self, book_id):
        """Get book description + small content chunks for analysis"""
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        try:
            with conn.cursor() as cur:
                # Get book details with description
                cur.execute("""
                    SELECT title, author, description, genre
                    FROM books 
                    WHERE book_id = %s
                """, (book_id,))
                book_info = cur.fetchone()
                
                if not book_info:
                    return None
                
                # Get small content chunks (first 2-3 chunks for context)
                cur.execute("""
                    SELECT content
                    FROM chunks 
                    WHERE book_id = %s
                    ORDER BY chunk_id
                    LIMIT 3
                """, (book_id,))
                chunks = cur.fetchall()
                
                # Combine description + sample content
                content_sample = ""
                
                if book_info['description']:
                    # Clean HTML tags from description
                    description = re.sub(r'<[^>]+>', '', book_info['description'])
                    content_sample += f"Description: {description}\n\n"
                
                if chunks:
                    content_sample += "Content Sample:\n"
                    for i, chunk in enumerate(chunks):
                        if chunk['content']:
                            # Take first 200 chars of each chunk
                            sample = chunk['content'][:200].strip()
                            content_sample += f"[Chunk {i+1}] {sample}...\n"
                
                return {
                    'book_id': book_id,
                    'title': book_info['title'],
                    'author': book_info['author'],
                    'current_genre': book_info['genre'],
                    'content_sample': content_sample[:1500]  # Limit to 1500 chars
                }
        finally:
            conn.close()
    
    def classify_with_enhanced_prompt(self, book_data):
        """Use Magistral with enhanced prompt for precise classification"""
        
        enhanced_prompt = f"""You are a precision book genre classifier. Analyze this book using BOTH the description and content samples to determine the most accurate, specific genre.

Title: "{book_data['title']}"
Author: {book_data['author']}
Current Genre: {book_data['current_genre']}

{book_data['content_sample']}

CLASSIFICATION GUIDELINES:
1. ROMANCE: Only if the primary plot focuses on romantic relationships and love stories
2. LITERARY FICTION: Only for character-driven narratives with literary merit, NOT catch-all category
3. Be SPECIFIC: Use precise genres like "Business & Economics", "Data Science", "Programming", "Self-Help", etc.
4. For technical/data books: Use appropriate non-fiction categories
5. For academic books: Use specific academic fields

AVAILABLE GENRES:
- Business & Economics (for business, economics, market analysis)
- Data Science & Analytics (for data analysis, statistics, data visualization)
- Programming & Technology (for coding, software development)
- Self-Help & Personal Development
- Psychology & Behavioral Science
- History (specific periods if relevant)
- Science Fiction (only if fictional with sci-fi elements)
- Fantasy (only if fictional with fantasy elements)  
- Mystery & Thriller (only if mystery/suspense plot)
- Biography & Memoir
- Political Science & Philosophy
- Academic & Research
- Health & Medicine
- Contemporary Fiction (modern realistic fiction)
- Historical Fiction (fiction set in past)

Based on the description and content samples, what is the MOST ACCURATE, SPECIFIC genre for this book?

Respond with ONLY the genre name, nothing else."""

        try:
            response = requests.post(
                self.magistral_url,
                json={
                    "model": "magistral",
                    "prompt": enhanced_prompt,
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                new_genre = result['response'].strip()
                
                # Clean up the response
                new_genre = re.sub(r'^["\']|["\']$', '', new_genre)  # Remove quotes
                new_genre = new_genre.split('\n')[0]  # Take first line only
                
                return new_genre
            else:
                print(f"   ❌ Magistral error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Classification error: {e}")
            return None
    
    def update_book_genre(self, book_id, new_genre, old_genre):
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
    
    def reprocess_romance_books(self):
        """Reprocess suspicious Romance classifications"""
        print("🔄 REPROCESSING ROMANCE BOOKS")
        print("=" * 40)
        
        # Find suspicious Romance books
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT book_id, title, author
                    FROM books 
                    WHERE genre = 'Romance'
                    AND (LOWER(title) LIKE '%data%' 
                         OR LOWER(description) LIKE '%data%'
                         OR LOWER(title) LIKE '%business%'
                         OR LOWER(title) LIKE '%economics%'
                         OR LOWER(title) LIKE '%analysis%'
                         OR LOWER(title) LIKE '%science%'
                         OR LOWER(title) LIKE '%algorithm%'
                         OR LOWER(title) LIKE '%programming%'
                         OR LOWER(title) LIKE '%technology%')
                    ORDER BY book_id
                """)
                suspect_books = cur.fetchall()
        finally:
            conn.close()
        
        print(f"Found {len(suspect_books)} suspicious Romance classifications")
        
        for book in suspect_books:
            print(f"\n📖 Processing: \"{book['title']}\" (ID: {book['book_id']})")
            
            # Get enhanced content
            book_data = self.get_enhanced_content_sample(book['book_id'])
            if not book_data:
                continue
            
            # Classify with enhanced prompt
            new_genre = self.classify_with_enhanced_prompt(book_data)
            if not new_genre:
                continue
            
            # Update if different
            if new_genre != 'Romance' and new_genre != book_data['current_genre']:
                if self.update_book_genre(book['book_id'], new_genre, 'Romance'):
                    print(f"   ✅ Romance → {new_genre}")
                    self.results['romance_fixes'].append({
                        'book_id': book['book_id'],
                        'title': book['title'],
                        'old_genre': 'Romance',
                        'new_genre': new_genre
                    })
                    self.results['new_genres_discovered'].add(new_genre)
                    self.reclassified_count += 1
                else:
                    print(f"   ❌ Failed to update")
            else:
                print(f"   ⚪ Confirmed: {new_genre}")
            
            self.processed_count += 1
            time.sleep(1)  # Rate limiting
    
    def refine_literary_fiction(self, limit=50):
        """Refine overly broad Literary Fiction classifications"""
        print(f"\n🔄 REFINING LITERARY FICTION (processing {limit} books)")
        print("=" * 50)
        
        # Get recent Literary Fiction books that might be misclassified
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT book_id, title, author
                    FROM books 
                    WHERE genre = 'Literary Fiction'
                    AND (LOWER(title) LIKE '%data%'
                         OR LOWER(title) LIKE '%business%'
                         OR LOWER(title) LIKE '%economics%'
                         OR LOWER(title) LIKE '%science%'
                         OR LOWER(title) LIKE '%programming%'
                         OR LOWER(title) LIKE '%analysis%'
                         OR LOWER(title) LIKE '%technology%'
                         OR LOWER(title) LIKE '%psychology%'
                         OR LOWER(title) LIKE '%philosophy%'
                         OR LOWER(title) LIKE '%history%'
                         OR LOWER(description) LIKE '%non-fiction%')
                    ORDER BY book_id DESC
                    LIMIT %s
                """, (limit,))
                litfic_books = cur.fetchall()
        finally:
            conn.close()
        
        print(f"Found {len(litfic_books)} Literary Fiction books for review")
        
        for book in litfic_books:
            print(f"\n📚 Processing: \"{book['title']}\" (ID: {book['book_id']})")
            
            # Get enhanced content
            book_data = self.get_enhanced_content_sample(book['book_id'])
            if not book_data:
                continue
            
            # Classify with enhanced prompt
            new_genre = self.classify_with_enhanced_prompt(book_data)
            if not new_genre:
                continue
            
            # Update if more specific
            if new_genre != 'Literary Fiction' and new_genre != book_data['current_genre']:
                if self.update_book_genre(book['book_id'], new_genre, 'Literary Fiction'):
                    print(f"   ✅ Literary Fiction → {new_genre}")
                    self.results['litfic_refinements'].append({
                        'book_id': book['book_id'],
                        'title': book['title'],
                        'old_genre': 'Literary Fiction',
                        'new_genre': new_genre
                    })
                    self.results['new_genres_discovered'].add(new_genre)
                    self.reclassified_count += 1
                else:
                    print(f"   ❌ Failed to update")
            else:
                print(f"   ⚪ Confirmed: {new_genre}")
            
            self.processed_count += 1
            time.sleep(1)  # Rate limiting
    
    def generate_report(self):
        """Generate reclassification report"""
        print(f"\n📋 TARGETED RECLASSIFICATION REPORT")
        print("=" * 50)
        print(f"📊 Total Processed: {self.processed_count}")
        print(f"🔄 Reclassified: {self.reclassified_count}")
        print(f"✅ Success Rate: {(self.reclassified_count/max(self.processed_count,1))*100:.1f}%")
        
        if self.results['romance_fixes']:
            print(f"\n💘 Romance Fixes ({len(self.results['romance_fixes'])}):")
            for fix in self.results['romance_fixes']:
                print(f"   • \"{fix['title']}\" → {fix['new_genre']}")
        
        if self.results['litfic_refinements']:
            print(f"\n📖 Literary Fiction Refinements ({len(self.results['litfic_refinements'])}):")
            for ref in self.results['litfic_refinements']:
                print(f"   • \"{ref['title']}\" → {ref['new_genre']}")
        
        if self.results['new_genres_discovered']:
            print(f"\n🆕 New Genres Discovered:")
            for genre in sorted(self.results['new_genres_discovered']):
                print(f"   • {genre}")
        
        return self.reclassified_count > 0

def main():
    """Execute targeted genre reclassification"""
    print("🎯 TARGETED GENRE RECLASSIFICATION")
    print("=" * 40)
    print("Focusing on Romance & Literary Fiction misclassifications")
    print("Using descriptions + content chunks for precision")
    print()
    
    classifier = TargetedGenreReclassifier()
    
    # Step 1: Fix obvious Romance misclassifications
    classifier.reprocess_romance_books()
    
    # Step 2: Refine Literary Fiction category
    classifier.refine_literary_fiction(30)  # Process 30 books
    
    # Step 3: Generate report
    success = classifier.generate_report()
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)