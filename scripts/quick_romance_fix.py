#!/usr/bin/env python3
"""
Quick Romance & Literary Fiction Fix
===================================
Fast targeted fixes for obvious misclassifications
"""

import sys
import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.append('/Users/weixiangzhang/Local Dev/LibraryOfBabel')
from config.api_config import get_database_config

def quick_fix_obvious_misclassifications():
    """Fix obvious misclassifications based on title/description patterns"""
    config = get_database_config()
    conn = psycopg2.connect(**config, cursor_factory=RealDictCursor)
    
    fixes = []
    
    try:
        with conn.cursor() as cur:
            # Fix obvious data/business books marked as Romance
            print("🔍 Finding obvious Romance misclassifications...")
            
            romance_fixes = [
                ("Edible Economics", "Business & Economics"),
                ("Invisible Women: Exposing Data Bias", "Data Science & Analytics"),
                ("Data Smart", "Data Science & Analytics"),
            ]
            
            for title_pattern, correct_genre in romance_fixes:
                cur.execute("""
                    SELECT book_id, title, genre 
                    FROM books 
                    WHERE LOWER(title) LIKE %s AND genre = 'Romance'
                """, (f'%{title_pattern.lower()}%',))
                
                books = cur.fetchall()
                for book in books:
                    cur.execute("""
                        UPDATE books SET genre = %s WHERE book_id = %s
                    """, (correct_genre, book['book_id']))
                    
                    print(f"   ✅ Fixed: \"{book['title']}\" → {correct_genre}")
                    fixes.append(f"Romance → {correct_genre}: {book['title']}")
            
            # Fix obvious tech/business books in Literary Fiction
            print("\n🔍 Finding obvious Literary Fiction misclassifications...")
            
            litfic_fixes = [
                ("data", "Data Science & Analytics"),
                ("economics", "Business & Economics"), 
                ("algorithm", "Programming & Technology"),
                ("programming", "Programming & Technology"),
                ("business", "Business & Economics"),
                ("analysis", "Data Science & Analytics"),
                ("genetics", "Science & Medicine"),
                ("holocaust", "History"),
                ("refugee", "Political Science"),
                ("capitalism", "Business & Economics"),
            ]
            
            for keyword, correct_genre in litfic_fixes:
                cur.execute("""
                    SELECT book_id, title, genre 
                    FROM books 
                    WHERE (LOWER(title) LIKE %s OR LOWER(description) LIKE %s) 
                    AND genre = 'Literary Fiction'
                    LIMIT 5
                """, (f'%{keyword}%', f'%{keyword}%'))
                
                books = cur.fetchall()
                for book in books:
                    # Don't change books that are actually literary fiction
                    if any(word in book['title'].lower() for word in ['novel', 'story', 'stories', 'fiction']):
                        continue
                        
                    cur.execute("""
                        UPDATE books SET genre = %s WHERE book_id = %s
                    """, (correct_genre, book['book_id']))
                    
                    print(f"   ✅ Fixed: \"{book['title']}\" → {correct_genre}")
                    fixes.append(f"Literary Fiction → {correct_genre}: {book['title']}")
            
            conn.commit()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    print(f"\n📊 Quick Fix Summary:")
    print(f"   Total fixes applied: {len(fixes)}")
    for fix in fixes:
        print(f"   • {fix}")
    
    return len(fixes)

def show_updated_distribution():
    """Show updated genre distribution"""
    config = get_database_config()
    conn = psycopg2.connect(**config, cursor_factory=RealDictCursor)
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT genre, COUNT(*) as count
                FROM books 
                WHERE genre IN ('Romance', 'Literary Fiction', 'Data Science & Analytics', 
                               'Business & Economics', 'Programming & Technology')
                GROUP BY genre
                ORDER BY count DESC
            """)
            
            results = cur.fetchall()
            
            print(f"\n📊 Updated Distribution (Key Genres):")
            for row in results:
                print(f"   • {row['genre']}: {row['count']} books")
                
    finally:
        conn.close()

if __name__ == '__main__':
    print("⚡ QUICK ROMANCE & LITERARY FICTION FIX")
    print("=" * 45)
    
    fixes = quick_fix_obvious_misclassifications()
    show_updated_distribution()
    
    print(f"\n✅ Applied {fixes} quick fixes to obvious misclassifications")