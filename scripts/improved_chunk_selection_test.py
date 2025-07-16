#!/usr/bin/env python3
"""
Improved Chunk Selection Strategy
================================
Skip front matter and select actual content chunks
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

def is_front_matter(content):
    """Detect if chunk is likely front matter"""
    content_lower = content.lower()
    
    front_matter_indicators = [
        'copyright', 'published', 'isbn', '©', 'all rights reserved',
        'dedication', 'acknowledgments', 'table of contents', 'contents',
        'publisher', 'edition', 'printed in', 'library of congress',
        'first published', 'this book is sold', 'isbn-13', 'isbn-10'
    ]
    
    # If chunk is mostly front matter indicators
    indicator_count = sum(1 for indicator in front_matter_indicators if indicator in content_lower)
    
    # Strong indicators
    if any(strong in content_lower for strong in ['copyright', 'all rights reserved', 'isbn', 'publisher']):
        return True
    
    # Multiple weak indicators
    if indicator_count >= 2:
        return True
    
    # Very short chunks that are just titles/headers
    if len(content.strip()) < 100 and any(word in content_lower for word in ['chapter', 'part', 'introduction']):
        return True
    
    return False

def get_improved_content_sample(book_id):
    """Get content sample skipping front matter"""
    db_config = get_database_config()
    conn = psycopg2.connect(**db_config, cursor_factory=RealDictCursor)
    
    try:
        with conn.cursor() as cur:
            # Get all chunks
            cur.execute("""
                SELECT content, chunk_id
                FROM chunks
                WHERE book_id = %s
                AND content IS NOT NULL
                AND LENGTH(content) > 50
                ORDER BY chunk_id
            """, (book_id,))
            
            all_chunks = cur.fetchall()
            
            # Filter out front matter
            content_chunks = []
            for chunk in all_chunks:
                if not is_front_matter(chunk['content']):
                    content_chunks.append(chunk)
            
            print(f"📊 Total chunks: {len(all_chunks)}")
            print(f"🚫 Front matter filtered: {len(all_chunks) - len(content_chunks)}")
            print(f"✅ Content chunks: {len(content_chunks)}")
            
            if not content_chunks:
                # Fallback to original method if we filtered everything
                content_chunks = all_chunks[-3:] if len(all_chunks) >= 3 else all_chunks
                print("⚠️  Fallback to last chunks")
            
            # Select diverse content chunks
            if len(content_chunks) >= 3:
                # Beginning, middle, end of actual content
                selected = [
                    content_chunks[0],                                    # Early content
                    content_chunks[len(content_chunks) // 2],            # Middle content  
                    content_chunks[-1]                                   # Late content
                ]
            else:
                selected = content_chunks
            
            print(f"🎯 Selected chunks: {len(selected)}")
            
            # Show what we selected
            for i, chunk in enumerate(selected, 1):
                print(f"\n📄 CHUNK {i}:")
                content = re.sub(r'<[^>]+>|\s+', ' ', chunk['content']).strip()[:200]
                print(f"   {content}...")
                
                # Check if it's front matter
                if is_front_matter(chunk['content']):
                    print(f"   ⚠️  Still detected as front matter!")
            
            # Create combined sample
            combined = " ... ".join([
                re.sub(r'<[^>]+>|\s+', ' ', chunk['content']).strip()[:200]
                for chunk in selected
            ])[:600]
            
            print(f"\n🔍 IMPROVED COMBINED SAMPLE:")
            print(f"   {combined}")
            
            return combined
            
    finally:
        conn.close()

def test_improved_selection():
    """Test improved selection on a few books"""
    db_config = get_database_config()
    conn = psycopg2.connect(**db_config, cursor_factory=RealDictCursor)
    
    try:
        with conn.cursor() as cur:
            # Get a few different books
            cur.execute("""
                SELECT b.book_id, b.title, b.author, b.genre
                FROM books b
                WHERE EXISTS (
                    SELECT 1 FROM chunks c WHERE c.book_id = b.book_id
                )
                ORDER BY RANDOM()
                LIMIT 3
            """)
            
            books = cur.fetchall()
            
            for book in books:
                print(f"\n{'='*60}")
                print(f"📚 TESTING: \"{book['title'][:50]}...\" by {book['author']}")
                print(f"🏷️  Current Genre: {book['genre']}")
                print(f"{'='*60}")
                
                get_improved_content_sample(book['book_id'])
                
    finally:
        conn.close()

if __name__ == '__main__':
    test_improved_selection()