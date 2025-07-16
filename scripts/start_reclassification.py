#!/usr/bin/env python3
"""
Start Comprehensive Reclassification
===================================
Demo the approach and start the process
"""

import sys
import json
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import re

sys.path.append('/Users/weixiangzhang/Local Dev/LibraryOfBabel')
from config.api_config import get_database_config

def test_single_reclassification():
    """Test the approach on one obvious misclassification"""
    config = get_database_config()
    conn = psycopg2.connect(**config, cursor_factory=RealDictCursor)
    
    try:
        with conn.cursor() as cur:
            # Find an obvious misclassification
            cur.execute("""
                SELECT b.book_id, b.title, b.author, b.genre
                FROM books b
                WHERE b.genre = 'Literary Fiction'
                AND (b.description IS NULL OR b.description = '')
                AND LOWER(b.title) LIKE '%wheel of time%'
                LIMIT 1
            """)
            
            book = cur.fetchone()
            if not book:
                # Fallback to any Literary Fiction without description
                cur.execute("""
                    SELECT b.book_id, b.title, b.author, b.genre
                    FROM books b
                    WHERE b.genre = 'Literary Fiction'
                    AND (b.description IS NULL OR b.description = '')
                    ORDER BY RANDOM()
                    LIMIT 1
                """)
                book = cur.fetchone()
            
            if book:
                print(f"🧪 TESTING CONTENT-BASED CLASSIFICATION")
                print("=" * 50)
                print(f"📖 Book: \"{book['title']}\"")
                print(f"   Author: {book['author']}")
                print(f"   Current Genre: {book['genre']}")
                
                # Get content chunks
                cur.execute("""
                    SELECT content
                    FROM chunks
                    WHERE book_id = %s
                    AND content IS NOT NULL
                    AND LENGTH(content) > 150
                    ORDER BY RANDOM()
                    LIMIT 2
                """, (book['book_id'],))
                
                chunks = cur.fetchall()
                
                if chunks:
                    print(f"\n📄 ACTUAL CONTENT SAMPLES:")
                    for i, chunk in enumerate(chunks, 1):
                        clean_content = re.sub(r'<[^>]+>', '', chunk['content'])
                        clean_content = re.sub(r'\s+', ' ', clean_content).strip()
                        sample = clean_content[:300]
                        print(f"   Sample {i}: {sample}...")
                    
                    # Analyze content type
                    combined = ' '.join([chunk['content'] for chunk in chunks])
                    combined_lower = combined.lower()
                    
                    print(f"\n🔍 CONTENT ANALYSIS:")
                    
                    # Check for clear genre indicators
                    if 'chapter' in combined_lower and any(word in combined_lower for word in ['character', 'dialogue', 'story']):
                        if any(word in combined_lower for word in ['magic', 'wizard', 'fantasy', 'dragon']):
                            suggested_genre = "Fantasy"
                        elif any(word in combined_lower for word in ['space', 'alien', 'future', 'technology']):
                            suggested_genre = "Science Fiction"
                        elif any(word in combined_lower for word in ['love', 'romance', 'heart', 'kiss']):
                            suggested_genre = "Romance"
                        else:
                            suggested_genre = "Literary Fiction"
                    elif any(word in combined_lower for word in ['research', 'study', 'analysis', 'theory']):
                        if any(word in combined_lower for word in ['business', 'economic', 'market']):
                            suggested_genre = "Business & Economics"
                        elif any(word in combined_lower for word in ['psychology', 'behavior', 'mental']):
                            suggested_genre = "Psychology"
                        elif any(word in combined_lower for word in ['history', 'historical', 'century']):
                            suggested_genre = "History"
                        else:
                            suggested_genre = "Academic & Research"
                    else:
                        suggested_genre = "Unknown"
                    
                    print(f"   💡 Content suggests: {suggested_genre}")
                    
                    if suggested_genre != book['genre'] and suggested_genre != "Unknown":
                        print(f"   🚨 MISCLASSIFICATION DETECTED!")
                        print(f"   ✅ Should be: {suggested_genre}")
                        print(f"   ❌ Currently: {book['genre']}")
                        return True
                    else:
                        print(f"   ✅ Classification appears correct")
                        return False
                else:
                    print(f"   ❌ No content chunks found")
                    return False
    finally:
        conn.close()

def show_scope_and_plan():
    """Show the scope of work needed"""
    config = get_database_config()
    conn = psycopg2.connect(**config, cursor_factory=RealDictCursor)
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    genre,
                    COUNT(*) as total,
                    COUNT(CASE WHEN description IS NULL OR description = '' THEN 1 END) as no_desc
                FROM books 
                GROUP BY genre
                HAVING COUNT(CASE WHEN description IS NULL OR description = '' THEN 1 END) > 0
                ORDER BY no_desc DESC
            """)
            
            results = cur.fetchall()
            
            print(f"\n📊 COMPREHENSIVE RECLASSIFICATION SCOPE")
            print("=" * 60)
            print(f"{'Genre':<25} {'Total':<8} {'No Desc':<10} {'% No Desc':<10}")
            print("-" * 60)
            
            total_no_desc = 0
            for row in results:
                genre = row['genre'][:24]
                total = row['total']
                no_desc = row['no_desc']
                percent = (no_desc / total) * 100 if total > 0 else 0
                
                print(f"{genre:<25} {total:<8} {no_desc:<10} {percent:<9.1f}%")
                total_no_desc += no_desc
            
            print("-" * 60)
            print(f"TOTAL BOOKS TO REPROCESS: {total_no_desc}")
            
            print(f"\n🎯 RECLASSIFICATION PLAN:")
            print(f"   1. Use Magistral LLM for content analysis")
            print(f"   2. Sample 3-4 chunks from different parts of each book")
            print(f"   3. Classify based on ACTUAL CONTENT, not title")
            print(f"   4. Process in batches of 20 books")
            print(f"   5. Save progress every 10 books")
            print(f"   6. Estimated time: 3-4 hours")
            
            return total_no_desc
    finally:
        conn.close()

def create_background_script():
    """Create a script to run the reclassification in background"""
    script_content = """#!/bin/bash
# Background Reclassification Script
echo "🚀 Starting comprehensive reclassification in background..."
cd "/Users/weixiangzhang/Local Dev/LibraryOfBabel"

# Run with output logging
python3 scripts/comprehensive_chunk_reclassification.py > reclassification.log 2>&1 &

# Get the process ID
PID=$!
echo "📝 Process started with PID: $PID"
echo "📄 Logs saved to: reclassification.log"
echo "💾 Progress saved to: reclassification_progress.json"
echo ""
echo "To monitor progress:"
echo "  tail -f reclassification.log"
echo "  cat reclassification_progress.json"
echo ""
echo "To stop process:"
echo "  kill $PID"

# Save PID for later
echo $PID > reclassification.pid
echo "✅ Reclassification started in background"
"""
    
    with open('/Users/weixiangzhang/Local Dev/LibraryOfBabel/start_reclassification.sh', 'w') as f:
        f.write(script_content)
    
    # Make executable
    import os
    os.chmod('/Users/weixiangzhang/Local Dev/LibraryOfBabel/start_reclassification.sh', 0o755)
    
    print(f"\n🛠️  BACKGROUND SCRIPT CREATED")
    print("=" * 40)
    print(f"📁 Location: start_reclassification.sh")
    print(f"🚀 To start: ./start_reclassification.sh")
    print(f"📊 Monitor: tail -f reclassification.log")
    print(f"💾 Progress: cat reclassification_progress.json")

def main():
    print("🔄 COMPREHENSIVE CHUNK-BASED RECLASSIFICATION SETUP")
    print("=" * 60)
    
    # Test the approach
    test_result = test_single_reclassification()
    
    # Show scope
    total_books = show_scope_and_plan()
    
    # Create background script
    create_background_script()
    
    print(f"\n✅ READY TO PROCESS {total_books} BOOKS")
    print("🎯 This will fix the fundamental classification issue")
    print("📚 All books will be classified by actual content, not titles")

if __name__ == '__main__':
    main()