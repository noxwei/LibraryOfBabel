#!/usr/bin/env python3
"""
Show All Literary Fiction Books
==============================
Display complete listing of 403 Literary Fiction books
"""
import sys
sys.path.append('/Users/weixiangzhang/Local Dev/LibraryOfBabel')
from config.api_config import get_database_config
import psycopg2
from psycopg2.extras import RealDictCursor
import re

def clean_description(desc):
    """Clean HTML tags and limit description length"""
    if not desc:
        return "No description available"
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', desc)
    # Limit length
    if len(clean) > 120:
        clean = clean[:120] + "..."
    return clean.strip()

def show_all_literary_fiction():
    """Show all Literary Fiction books"""
    config = get_database_config()
    conn = psycopg2.connect(**config, cursor_factory=RealDictCursor)
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT book_id, title, author, description
                FROM books 
                WHERE genre = 'Literary Fiction'
                ORDER BY title
            """)
            
            litfic_books = cur.fetchall()
            
            print(f"📚 ALL LITERARY FICTION BOOKS ({len(litfic_books)} total)")
            print("=" * 100)
            
            # Flag suspicious patterns
            suspicious_count = 0
            
            for i, book in enumerate(litfic_books, 1):
                print(f"{i:3d}. \"{book['title']}\"")
                print(f"     Author: {book['author']}")
                print(f"     Description: {clean_description(book['description'])}")
                
                # Flag suspicious ones
                title_lower = book['title'].lower()
                desc_lower = (book['description'] or '').lower()
                
                suspicious_keywords = [
                    'manual', 'guide', 'how to', 'handbook', 'tutorial',
                    'business', 'economics', 'data', 'analysis', 'research',
                    'psychology', 'therapy', 'self-help', 'improvement',
                    'history', 'historical analysis', 'study', 'academic',
                    'science', 'scientific', 'technical', 'programming'
                ]
                
                suspicious_flags = []
                for keyword in suspicious_keywords:
                    if keyword in title_lower or keyword in desc_lower:
                        suspicious_flags.append(keyword)
                
                if suspicious_flags:
                    print(f"     🚨 SUSPICIOUS: {', '.join(suspicious_flags)} - May be non-fiction")
                    suspicious_count += 1
                
                print()
    
    finally:
        conn.close()
    
    print(f"📊 SUMMARY:")
    print(f"   Total Literary Fiction books: {len(litfic_books)}")
    print(f"   Suspicious (likely non-fiction): {suspicious_count}")
    print(f"   Quality ratio: {((len(litfic_books) - suspicious_count) / len(litfic_books)) * 100:.1f}%")

if __name__ == '__main__':
    show_all_literary_fiction()