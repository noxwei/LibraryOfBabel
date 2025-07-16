#!/usr/bin/env python3
"""
Analyze Chunk Selection for Genre Classification
================================================
Show exactly what chunks llama3.2:3b is analyzing
"""

import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import re
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config.api_config import get_database_config

def show_chunk_selection_for_book(book_id):
    """Show what chunks are being selected for a specific book"""
    db_config = get_database_config()
    conn = psycopg2.connect(**db_config, cursor_factory=RealDictCursor)
    
    try:
        with conn.cursor() as cur:
            # Get book info
            cur.execute("SELECT title, author, genre FROM books WHERE book_id = %s", (book_id,))
            book = cur.fetchone()
            
            print(f"📚 Book: \"{book['title']}\" by {book['author']}")
            print(f"🏷️  Current Genre: {book['genre']}")
            print()
            
            # Show current chunk selection logic (from daemon)
            cur.execute("""
                WITH numbered_chunks AS (
                    SELECT content, chunk_id,
                           ROW_NUMBER() OVER (ORDER BY chunk_id) as rn,
                           COUNT(*) OVER () as total_chunks
                    FROM chunks
                    WHERE book_id = %s
                    AND content IS NOT NULL
                    AND LENGTH(content) > 100
                )
                SELECT content, chunk_id, rn, total_chunks
                FROM numbered_chunks
                WHERE rn IN (1, GREATEST(total_chunks/3, 1), GREATEST(total_chunks*2/3, 1))
                ORDER BY rn
                LIMIT 3
            """, (book_id,))
            
            chunks = cur.fetchall()
            
            print(f"📊 Total chunks available: {chunks[0]['total_chunks'] if chunks else 0}")
            print(f"🎯 Selected chunks: {len(chunks)}")
            print()
            
            for i, chunk in enumerate(chunks, 1):
                print(f"📄 CHUNK {i} (position {chunk['rn']}/{chunk['total_chunks']}):")
                content = re.sub(r'<[^>]+>|\s+', ' ', chunk['content']).strip()[:300]
                print(f"   {content}...")
                print()
            
            # Combine for final analysis (like daemon does)
            if chunks:
                combined = " ... ".join([
                    re.sub(r'<[^>]+>|\s+', ' ', chunk['content']).strip()[:200]
                    for chunk in chunks
                ])[:600]
                
                print(f"🔍 FINAL COMBINED SAMPLE (what llama3.2:3b sees):")
                print(f"   {combined}")
                print()
                
                # Analyze content type
                content_lower = combined.lower()
                print(f"📋 CONTENT ANALYSIS:")
                
                # Check for front matter indicators
                front_matter_indicators = ['copyright', 'published', 'isbn', 'dedication', 'acknowledgments', 'table of contents']
                front_matter_found = [ind for ind in front_matter_indicators if ind in content_lower]
                if front_matter_found:
                    print(f"   ⚠️  Front matter detected: {', '.join(front_matter_found)}")
                
                # Check for chapter indicators
                chapter_indicators = ['chapter', 'part one', 'part 1', 'prologue', 'epilogue']
                chapter_found = [ind for ind in chapter_indicators if ind in content_lower]
                if chapter_found:
                    print(f"   📖 Chapter structure: {', '.join(chapter_found)}")
                
                # Check for fiction vs non-fiction indicators
                fiction_indicators = ['said', 'dialogue', 'character', 'protagonist', 'story']
                nonfiction_indicators = ['research', 'study', 'analysis', 'according to', 'theory']
                
                fiction_count = sum(1 for ind in fiction_indicators if ind in content_lower)
                nonfiction_count = sum(1 for ind in nonfiction_indicators if ind in content_lower)
                
                print(f"   📚 Fiction indicators: {fiction_count}")
                print(f"   📊 Non-fiction indicators: {nonfiction_count}")
                
    finally:
        conn.close()

def main():
    """Show chunk analysis for a sample book"""
    print("🔍 CHUNK SELECTION ANALYSIS")
    print("=" * 50)
    
    # Get a random book that was recently reclassified
    db_config = get_database_config()
    conn = psycopg2.connect(**db_config, cursor_factory=RealDictCursor)
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT book_id FROM books 
                WHERE genre IN ('Science Fiction', 'Philosophy', 'Fantasy')
                ORDER BY RANDOM() 
                LIMIT 1
            """)
            book = cur.fetchone()
            
            if book:
                show_chunk_selection_for_book(book['book_id'])
            else:
                print("No suitable book found")
                
    finally:
        conn.close()

if __name__ == '__main__':
    main()