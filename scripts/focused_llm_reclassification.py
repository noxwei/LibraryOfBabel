#!/usr/bin/env python3
"""
Focused LLM Reclassification
===========================
Process just 5-10 books to demonstrate proper LLM-based classification
"""

import sys
import json
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import re
import time

sys.path.append('/Users/weixiangzhang/Local Dev/LibraryOfBabel')
from config.api_config import get_database_config

def classify_book_with_magistral(title, author, description):
    """Use Magistral to classify a single book"""
    
    prompt = f"""You are a professional book genre classifier. Classify this book into the most accurate genre.

BOOK:
Title: "{title}"
Author: {author}
Description: {description[:300]}

GENRES:
- Romance: Fiction focused on romantic relationships with HEA/HFN endings
- Literary Fiction: Character-driven fiction with literary merit and artistic writing
- Science Fiction: Fiction with futuristic technology, space, aliens, or sci-fi concepts  
- Fantasy: Fiction with magic, supernatural elements, or imaginary worlds
- Self-Help: Non-fiction for personal improvement and development
- Biography & Memoir: Non-fiction accounts of real people's lives
- Psychology: Non-fiction about human behavior and mental health
- Business & Economics: Non-fiction about business, economics, and finance
- History: Non-fiction about past events and civilizations
- Philosophy: Non-fiction exploring fundamental questions about existence

RULES:
1. Romance must have romantic relationships as PRIMARY focus
2. Literary Fiction is for artistic/literary works, NOT a catch-all
3. Distinguish fiction vs non-fiction carefully
4. Choose the MOST SPECIFIC category that fits

What is the most accurate genre for this book? Respond with ONLY the genre name."""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "magistral",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1}
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            classification = result['response'].strip()
            
            # Extract final answer from Magistral's verbose response
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
            return classification.strip()
        else:
            return f"Error: {response.status_code}"
            
    except Exception as e:
        return f"Error: {e}"

def get_sample_books():
    """Get sample books from Romance and Literary Fiction"""
    config = get_database_config()
    conn = psycopg2.connect(**config, cursor_factory=RealDictCursor)
    
    try:
        with conn.cursor() as cur:
            # Get obvious misclassifications
            cur.execute("""
                SELECT book_id, title, author, description, genre
                FROM books 
                WHERE (genre = 'Romance' AND (
                    LOWER(title) LIKE '%memoir%' OR
                    LOWER(title) LIKE '%data%' OR 
                    LOWER(title) LIKE '%psychology%' OR
                    LOWER(title) LIKE '%self-help%'
                )) OR (genre = 'Literary Fiction' AND (
                    LOWER(title) LIKE '%business%' OR
                    LOWER(title) LIKE '%history%' OR
                    LOWER(title) LIKE '%science%'
                ))
                ORDER BY RANDOM()
                LIMIT 5
            """)
            
            return cur.fetchall()
                
    finally:
        conn.close()

def update_book_genre(book_id, new_genre):
    """Update book genre in database"""
    config = get_database_config()
    conn = psycopg2.connect(**config, cursor_factory=RealDictCursor)
    
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE books SET genre = %s WHERE book_id = %s", (new_genre, book_id))
            conn.commit()
            return True
    except Exception as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

def main():
    print("🎯 FOCUSED LLM RECLASSIFICATION")
    print("=" * 40)
    print("Using Magistral to reclassify obvious misclassifications")
    print()
    
    # Get sample books
    books = get_sample_books()
    if not books:
        print("No problematic books found!")
        return
    
    print(f"Found {len(books)} books to reclassify:")
    fixes = 0
    
    for book in books:
        print(f"\n📖 Book: \"{book['title']}\"")
        print(f"   Author: {book['author']}")
        print(f"   Current: {book['genre']}")
        
        # Get description sample
        desc = book['description'][:200] if book['description'] else "No description"
        print(f"   Description: {desc}...")
        
        # Classify with LLM
        print("   🤖 Asking Magistral...")
        new_genre = classify_book_with_magistral(book['title'], book['author'], book['description'] or "")
        
        print(f"   🎯 Magistral says: {new_genre}")
        
        # Update if different and valid
        valid_genres = [
            "Romance", "Literary Fiction", "Science Fiction", "Fantasy",
            "Self-Help", "Biography & Memoir", "Psychology", 
            "Business & Economics", "History", "Philosophy"
        ]
        
        if new_genre in valid_genres and new_genre != book['genre']:
            if update_book_genre(book['book_id'], new_genre):
                print(f"   ✅ Updated: {book['genre']} → {new_genre}")
                fixes += 1
            else:
                print(f"   ❌ Failed to update database")
        elif new_genre == book['genre']:
            print(f"   ⚪ Confirmed: {new_genre}")
        else:
            print(f"   ❌ Invalid genre: {new_genre}")
        
        time.sleep(2)  # Rate limiting
    
    print(f"\n📊 Summary: Applied {fixes} fixes out of {len(books)} books")
    
    # Show some updated stats
    config = get_database_config()
    conn = psycopg2.connect(**config, cursor_factory=RealDictCursor)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT genre, COUNT(*) as count
                FROM books 
                WHERE genre IN ('Romance', 'Literary Fiction', 'Self-Help', 'Psychology', 'Biography & Memoir')
                GROUP BY genre
                ORDER BY count DESC
            """)
            
            results = cur.fetchall()
            print(f"\n📊 Updated counts:")
            for row in results:
                print(f"   • {row['genre']}: {row['count']} books")
    finally:
        conn.close()

if __name__ == '__main__':
    main()