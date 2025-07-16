#!/usr/bin/env python3
"""
Quick Chunk-Based Classification Test
====================================
Test a few books without descriptions to see the actual content
"""

import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import re

sys.path.append('/Users/weixiangzhang/Local Dev/LibraryOfBabel')
from config.api_config import get_database_config

def show_content_samples():
    """Show content samples from books without descriptions"""
    config = get_database_config()
    conn = psycopg2.connect(**config, cursor_factory=RealDictCursor)
    
    try:
        with conn.cursor() as cur:
            # Get Literary Fiction books without descriptions
            cur.execute("""
                SELECT b.book_id, b.title, b.author, b.genre
                FROM books b
                WHERE b.genre = 'Literary Fiction'
                AND (b.description IS NULL OR b.description = '')
                ORDER BY RANDOM()
                LIMIT 5
            """)
            
            books = cur.fetchall()
            
            print(f"📚 CONTENT ANALYSIS: Literary Fiction Books Without Descriptions")
            print("=" * 80)
            
            for book in books:
                print(f"\n📖 Book: \"{book['title']}\" by {book['author']}")
                print(f"   Current Genre: {book['genre']}")
                
                # Get sample chunks
                cur.execute("""
                    SELECT content, title
                    FROM chunks
                    WHERE book_id = %s
                    AND content IS NOT NULL
                    AND LENGTH(content) > 100
                    ORDER BY RANDOM()
                    LIMIT 2
                """, (book['book_id'],))
                
                chunks = cur.fetchall()
                
                if chunks:
                    print("   📄 Content Samples:")
                    for i, chunk in enumerate(chunks, 1):
                        # Clean and show content
                        clean_content = re.sub(r'<[^>]+>', '', chunk['content'])
                        clean_content = re.sub(r'\s+', ' ', clean_content).strip()
                        sample = clean_content[:200]
                        print(f"      Sample {i}: {sample}...")
                    
                    # Analyze content type
                    combined = ' '.join([chunk['content'] for chunk in chunks])
                    combined_lower = combined.lower()
                    
                    # Check for genre indicators
                    print("   🔍 Content Indicators:")
                    
                    if any(word in combined_lower for word in ['business', 'economic', 'market', 'company', 'profit']):
                        print("      🏢 BUSINESS indicators found")
                    
                    if any(word in combined_lower for word in ['data', 'analysis', 'research', 'study', 'statistics']):
                        print("      📊 DATA/RESEARCH indicators found")
                    
                    if any(word in combined_lower for word in ['psychology', 'therapy', 'mental', 'behavior', 'cognitive']):
                        print("      🧠 PSYCHOLOGY indicators found")
                    
                    if any(word in combined_lower for word in ['history', 'historical', 'century', 'war', 'ancient']):
                        print("      🏛️ HISTORY indicators found")
                    
                    if any(word in combined_lower for word in ['science', 'scientific', 'research', 'theory', 'experiment']):
                        print("      🔬 SCIENCE indicators found")
                    
                    if any(word in combined_lower for word in ['magic', 'dragon', 'wizard', 'fantasy', 'spell']):
                        print("      🧙 FANTASY indicators found")
                    
                    if any(word in combined_lower for word in ['space', 'alien', 'future', 'robot', 'technology']):
                        print("      🚀 SCI-FI indicators found")
                    
                    if any(word in combined_lower for word in ['love', 'romance', 'kiss', 'heart', 'relationship']):
                        print("      💕 ROMANCE indicators found")
                    
                    if any(word in combined_lower for word in ['character', 'story', 'novel', 'narrative', 'protagonist']):
                        print("      📖 FICTION indicators found")
                    else:
                        print("      📄 Likely NON-FICTION (no story elements)")
                else:
                    print("   ❌ No content chunks found")
    
    finally:
        conn.close()

def show_problem_summary():
    """Show the scope of the description problem"""
    config = get_database_config()
    conn = psycopg2.connect(**config, cursor_factory=RealDictCursor)
    
    try:
        with conn.cursor() as cur:
            print(f"\n📊 DESCRIPTION PROBLEM SUMMARY")
            print("=" * 50)
            
            # Literary Fiction breakdown
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN description IS NULL OR description = '' THEN 1 END) as no_desc
                FROM books 
                WHERE genre = 'Literary Fiction'
            """)
            litfic = cur.fetchone()
            
            # Romance breakdown  
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN description IS NULL OR description = '' THEN 1 END) as no_desc
                FROM books 
                WHERE genre = 'Romance'
            """)
            romance = cur.fetchone()
            
            print(f"💔 Literary Fiction Problem:")
            print(f"   Total: {litfic['total']} books")
            print(f"   No Description: {litfic['no_desc']} books ({(litfic['no_desc']/litfic['total'])*100:.1f}%)")
            print(f"   ⚠️  73% classified without knowing content!")
            
            print(f"\n💕 Romance Problem:")
            print(f"   Total: {romance['total']} books")
            print(f"   No Description: {romance['no_desc']} books ({(romance['no_desc']/romance['total'])*100:.1f}%)")
            
            print(f"\n🎯 SOLUTION NEEDED:")
            print(f"   Must analyze CONTENT CHUNKS for {litfic['no_desc'] + romance['no_desc']} books")
            print(f"   Current classification based on title/author only = highly inaccurate")
    
    finally:
        conn.close()

if __name__ == '__main__':
    show_problem_summary()
    show_content_samples()