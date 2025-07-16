#!/usr/bin/env python3
"""
Show Romance and Literary Fiction Books
=======================================
Display detailed listings to verify classifications
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
    if len(clean) > 150:
        clean = clean[:150] + "..."
    return clean.strip()

def show_romance_books():
    """Show all Romance books for verification"""
    config = get_database_config()
    conn = psycopg2.connect(**config, cursor_factory=RealDictCursor)
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT book_id, title, author, description
                FROM books 
                WHERE genre = 'Romance'
                ORDER BY title
            """)
            
            romance_books = cur.fetchall()
            
            print(f"💕 ROMANCE BOOKS ({len(romance_books)} total)")
            print("=" * 80)
            
            for i, book in enumerate(romance_books, 1):
                print(f"{i:3d}. \"{book['title']}\"")
                print(f"     Author: {book['author']}")
                print(f"     Description: {clean_description(book['description'])}")
                print()
                
                # Flag suspicious ones
                title_lower = book['title'].lower()
                desc_lower = (book['description'] or '').lower()
                
                suspicious_keywords = [
                    'data', 'business', 'economics', 'analysis', 'algorithm',
                    'programming', 'technology', 'science', 'research', 'study'
                ]
                
                if any(keyword in title_lower or keyword in desc_lower for keyword in suspicious_keywords):
                    print(f"     🚨 SUSPICIOUS: May not be romance")
                    print()
    
    finally:
        conn.close()

def show_literary_fiction_sample():
    """Show sample of Literary Fiction books"""
    config = get_database_config()
    conn = psycopg2.connect(**config, cursor_factory=RealDictCursor)
    
    try:
        with conn.cursor() as cur:
            # Show a mix: some recent and some random
            cur.execute("""
                (SELECT book_id, title, author, description
                 FROM books 
                 WHERE genre = 'Literary Fiction'
                 ORDER BY book_id DESC
                 LIMIT 20)
                UNION ALL
                (SELECT book_id, title, author, description
                 FROM books 
                 WHERE genre = 'Literary Fiction'
                 ORDER BY RANDOM()
                 LIMIT 20)
                ORDER BY title
                LIMIT 30
            """)
            
            litfic_books = cur.fetchall()
            
            print(f"📚 LITERARY FICTION SAMPLE ({len(litfic_books)} shown of 410 total)")
            print("=" * 80)
            
            for i, book in enumerate(litfic_books, 1):
                print(f"{i:3d}. \"{book['title']}\"")
                print(f"     Author: {book['author']}")
                print(f"     Description: {clean_description(book['description'])}")
                
                # Flag suspicious ones
                title_lower = book['title'].lower()
                desc_lower = (book['description'] or '').lower()
                
                non_fiction_keywords = [
                    'data', 'business', 'economics', 'analysis', 'algorithm',
                    'programming', 'technology', 'research', 'study', 'guide',
                    'how to', 'method', 'technique', 'system'
                ]
                
                if any(keyword in title_lower or keyword in desc_lower for keyword in non_fiction_keywords):
                    print(f"     🚨 SUSPICIOUS: May be non-fiction")
                
                print()
    
    finally:
        conn.close()

def show_genre_quality_check():
    """Show quality metrics for key genres"""
    config = get_database_config()
    conn = psycopg2.connect(**config, cursor_factory=RealDictCursor)
    
    try:
        with conn.cursor() as cur:
            print(f"📊 GENRE QUALITY CHECK")
            print("=" * 40)
            
            # Check for suspicious patterns in Romance
            cur.execute("""
                SELECT COUNT(*) as suspicious_romance
                FROM books 
                WHERE genre = 'Romance'
                AND (LOWER(title) LIKE '%data%' 
                     OR LOWER(title) LIKE '%business%'
                     OR LOWER(title) LIKE '%economics%'
                     OR LOWER(title) LIKE '%algorithm%'
                     OR LOWER(title) LIKE '%programming%'
                     OR LOWER(description) LIKE '%non-fiction%')
            """)
            suspicious_romance = cur.fetchone()['suspicious_romance']
            
            # Check for suspicious patterns in Literary Fiction
            cur.execute("""
                SELECT COUNT(*) as suspicious_litfic
                FROM books 
                WHERE genre = 'Literary Fiction'
                AND (LOWER(title) LIKE '%data%' 
                     OR LOWER(title) LIKE '%business%'
                     OR LOWER(title) LIKE '%how to%'
                     OR LOWER(title) LIKE '%guide%'
                     OR LOWER(title) LIKE '%manual%'
                     OR LOWER(description) LIKE '%non-fiction%')
            """)
            suspicious_litfic = cur.fetchone()['suspicious_litfic']
            
            # Show counts
            cur.execute("SELECT COUNT(*) FROM books WHERE genre = 'Romance'")
            romance_total = cur.fetchone()['count']
            
            cur.execute("SELECT COUNT(*) FROM books WHERE genre = 'Literary Fiction'")
            litfic_total = cur.fetchone()['count']
            
            print(f"💕 Romance Books:")
            print(f"   Total: {romance_total}")
            print(f"   Suspicious: {suspicious_romance} ({(suspicious_romance/romance_total)*100:.1f}%)")
            print(f"   Quality Score: {((romance_total-suspicious_romance)/romance_total)*100:.1f}%")
            
            print(f"\n📚 Literary Fiction Books:")
            print(f"   Total: {litfic_total}")
            print(f"   Suspicious: {suspicious_litfic} ({(suspicious_litfic/litfic_total)*100:.1f}%)")
            print(f"   Quality Score: {((litfic_total-suspicious_litfic)/litfic_total)*100:.1f}%")
    
    finally:
        conn.close()

if __name__ == '__main__':
    print("📖 ROMANCE & LITERARY FICTION BOOK REVIEW")
    print("=" * 50)
    
    # First show quality metrics
    show_genre_quality_check()
    print("\n" + "="*80 + "\n")
    
    # Show all Romance books (since there are only 143)
    show_romance_books()
    print("\n" + "="*80 + "\n")
    
    # Show sample of Literary Fiction (since there are 410)
    show_literary_fiction_sample()