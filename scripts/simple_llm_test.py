#!/usr/bin/env python3
"""
Simple LLM Classification Test
=============================
Test Magistral with a single book classification
"""

import sys
import json
import requests
import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.append('/Users/weixiangzhang/Local Dev/LibraryOfBabel')
from config.api_config import get_database_config

def test_single_classification():
    """Test classification on a single obvious book"""
    
    # Test with an obvious romance novel
    test_prompt = """You are a book genre classifier. Analyze this book:

Title: "Ask Me Again"
Author: Gina L. Maxwell  
Description: The friend zone has never felt so hot. When Trish Howell's boyfriend of ten years dumps her unexpectedly, she heads back to her hometown for the summer.

Available genres: Romance, Literary Fiction, Science Fiction, Fantasy, Mystery & Thriller, Self-Help, Business & Economics, Psychology, History, Biography & Memoir

This is clearly about romantic relationships. What genre is this book?

Respond with ONLY the genre name."""

    print("🧪 Testing Magistral with obvious romance book...")
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "magistral",
                "prompt": test_prompt,
                "stream": False,
                "options": {"temperature": 0.1}
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            classification = result['response'].strip()
            print(f"✅ Magistral responded: '{classification}'")
            
            if "Romance" in classification:
                print("✅ Correct classification!")
                return True
            else:
                print("❌ Incorrect classification")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def get_sample_romance_book():
    """Get a sample romance book from database"""
    config = get_database_config()
    conn = psycopg2.connect(**config, cursor_factory=RealDictCursor)
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT book_id, title, author, description
                FROM books 
                WHERE genre = 'Romance' 
                AND description IS NOT NULL
                ORDER BY RANDOM()
                LIMIT 1
            """)
            
            book = cur.fetchone()
            if book:
                print(f"📖 Sample book: \"{book['title']}\" by {book['author']}")
                desc = book['description'][:200] + "..." if len(book['description']) > 200 else book['description']
                print(f"   Description: {desc}")
                return book
            else:
                print("❌ No romance books found")
                return None
                
    finally:
        conn.close()

if __name__ == '__main__':
    print("🤖 SIMPLE LLM CLASSIFICATION TEST")
    print("=" * 40)
    
    # Test 1: Hardcoded obvious case
    if test_single_classification():
        print("\n🎯 Magistral is working correctly!")
        
        # Test 2: Real database book
        print("\n📚 Testing with real database book...")
        book = get_sample_romance_book()
        
        if book:
            print("✅ Ready for full classification run")
        else:
            print("❌ Database issue")
    else:
        print("\n❌ Magistral not working properly")