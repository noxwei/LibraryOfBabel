#!/usr/bin/env python3
"""
Precision Genre Fix: Address Specific Misclassifications
========================================================

Target specific books that are clearly in wrong categories based on:
- Title patterns
- Author patterns  
- Content analysis
- Known book classifications
"""

import sys
import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.append('/Users/weixiangzhang/Local Dev/LibraryOfBabel')
from config.api_config import get_database_config

class PrecisionGenreFixer:
    def __init__(self):
        self.config = get_database_config()
        self.fixes = []
        
    def apply_fix(self, title_pattern, current_genre, new_genre, reason=""):
        """Apply genre fix based on title pattern"""
        conn = psycopg2.connect(**self.config, cursor_factory=RealDictCursor)
        
        try:
            with conn.cursor() as cur:
                if isinstance(title_pattern, str):
                    # Exact title match
                    cur.execute("""
                        SELECT book_id, title, author, genre
                        FROM books 
                        WHERE LOWER(title) = LOWER(%s) AND genre = %s
                    """, (title_pattern, current_genre))
                else:
                    # Pattern match
                    cur.execute("""
                        SELECT book_id, title, author, genre
                        FROM books 
                        WHERE LOWER(title) LIKE LOWER(%s) AND genre = %s
                    """, (title_pattern, current_genre))
                
                books = cur.fetchall()
                
                for book in books:
                    cur.execute("""
                        UPDATE books SET genre = %s WHERE book_id = %s
                    """, (new_genre, book['book_id']))
                    
                    fix_info = {
                        'title': book['title'],
                        'author': book['author'],
                        'old_genre': current_genre,
                        'new_genre': new_genre,
                        'reason': reason
                    }
                    self.fixes.append(fix_info)
                    print(f"   ✅ \"{book['title']}\" → {new_genre}")
                
                conn.commit()
                return len(books)
                
        except Exception as e:
            print(f"   ❌ Error fixing {title_pattern}: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def fix_romance_misclassifications(self):
        """Fix obvious Romance misclassifications"""
        print("💔 FIXING ROMANCE MISCLASSIFICATIONS")
        print("=" * 50)
        
        romance_fixes = [
            # Self-help books
            ("100+ Ways to Recharge, De-Stress, and Prioritize You!", "Self-Help", "ADHD self-help guide"),
            ("%ways to%", "Self-Help", "Self-help pattern"),
            
            # Memoirs and biographies
            ("A Memoir at the End of Sight", "Biography & Memoir", "Memoir about blindness"),
            ("%memoir%", "Biography & Memoir", "Memoir pattern"),
            
            # Psychology/Health books
            ("Aspergirls", "Psychology", "Book about Asperger's syndrome"),
            
            # Science/Nature books
            ("Air", "Science & Nature", "Science book by William Bryant Logan"),
            
            # Religious/Spiritual books
            ("Abuelita Faith", "Religion & Spirituality", "Religious/spiritual book"),
            ("%faith%", "Religion & Spirituality", "Faith/religion pattern"),
            
            # Science Fiction
            ("A House Between Earth and the Moon%", "Science Fiction", "Space-based sci-fi"),
            ("August Kitko and the Mechas from Space", "Science Fiction", "Mecha sci-fi"),
            ("All Our Wrong Todays", "Science Fiction", "Time travel sci-fi"),
            
            # Literary Fiction (should stay)
            ("A Horse Walks into a Bar", "Literary Fiction", "Comedy/drama by David Grossman"),
            ("A Bookshop in Algiers", "Literary Fiction", "Literary work"),
            ("1968", "Literary Fiction", "Literary work by Karen Tei Yamashita"),
            
            # True Romance (should stay)
            ("A Forever Love (Wanted)", "Romance", "Actual romance novel"),
            ("Ask Me Again", "Romance", "Actual romance novel"),
        ]
        
        total_fixes = 0
        for title_pattern, correct_genre, reason in romance_fixes:
            if correct_genre != "Romance":  # Only fix non-romance books
                fixes = self.apply_fix(title_pattern, "Romance", correct_genre, reason)
                total_fixes += fixes
        
        print(f"\nFixed {total_fixes} Romance misclassifications")
        return total_fixes
    
    def fix_literary_fiction_misclassifications(self):
        """Fix obvious Literary Fiction misclassifications"""
        print("\n📚 FIXING LITERARY FICTION MISCLASSIFICATIONS")
        print("=" * 55)
        
        litfic_fixes = [
            # Science Fiction
            ("Mona Lisa Overdrive", "Science Fiction", "Cyberpunk by William Gibson"),
            ("A Memory Called Empire", "Science Fiction", "Space opera"),
            ("Dune%", "Science Fiction", "Dune series"),
            ("%Marvel%", "Science Fiction", "Marvel comics/books"),
            ("The Walking Dead%", "Science Fiction", "Zombie fiction"),
            ("%Tetris Effect%", "Programming & Technology", "Technology book"),
            
            # Philosophy/Religion
            ("The Analects of Confucius%", "Philosophy", "Classical philosophy"),
            ("Sharing the Divine Pathos", "Religion & Spirituality", "Religious text"),
            
            # Non-fiction/Academic
            ("China Unbound", "Political Science", "Political analysis"),
            ("The Struggle Against Nature%", "History", "Environmental history"),
            ("Forty Years in the Wilderness", "Biography & Memoir", "Memoir"),
            
            # Psychology/Science
            ("Mescaline", "Psychology", "Psychology/neuroscience"),
            
            # Keep as Literary Fiction (actual literary works)
            ("Such a Fun Age", "Literary Fiction", "Contemporary literary fiction"),
            ("Frog", "Literary Fiction", "Literary work by Mo Yan"),
        ]
        
        total_fixes = 0
        for title_pattern, correct_genre, reason in litfic_fixes:
            if correct_genre != "Literary Fiction":  # Only fix non-literary books
                fixes = self.apply_fix(title_pattern, "Literary Fiction", correct_genre, reason)
                total_fixes += fixes
        
        print(f"\nFixed {total_fixes} Literary Fiction misclassifications")
        return total_fixes
    
    def fix_by_author_patterns(self):
        """Fix books by specific authors known for certain genres"""
        print("\n👨‍💼 FIXING BY AUTHOR PATTERNS")
        print("=" * 40)
        
        author_fixes = [
            # Science Fiction authors
            ("William Gibson", "Science Fiction", "Cyberpunk author"),
            ("Arkady Martine", "Science Fiction", "Sci-fi author"),
            ("Robert Kirkman", "Science Fiction", "Comic book author"),
            
            # Philosophy
            ("Confucius", "Philosophy", "Classical philosopher"),
            
            # Self-help/Psychology
            ("Sasha Hamdani", "Self-Help", "ADHD specialist"),
        ]
        
        total_fixes = 0
        conn = psycopg2.connect(**self.config, cursor_factory=RealDictCursor)
        
        try:
            with conn.cursor() as cur:
                for author_pattern, correct_genre, reason in author_fixes:
                    cur.execute("""
                        SELECT book_id, title, author, genre
                        FROM books 
                        WHERE LOWER(author) LIKE LOWER(%s) 
                        AND genre IN ('Romance', 'Literary Fiction')
                    """, (f'%{author_pattern}%',))
                    
                    books = cur.fetchall()
                    
                    for book in books:
                        cur.execute("""
                            UPDATE books SET genre = %s WHERE book_id = %s
                        """, (correct_genre, book['book_id']))
                        
                        fix_info = {
                            'title': book['title'],
                            'author': book['author'],
                            'old_genre': book['genre'],
                            'new_genre': correct_genre,
                            'reason': reason
                        }
                        self.fixes.append(fix_info)
                        print(f"   ✅ \"{book['title']}\" by {book['author']} → {correct_genre}")
                        total_fixes += 1
                
                conn.commit()
                
        except Exception as e:
            print(f"   ❌ Error in author fixes: {e}")
            conn.rollback()
        finally:
            conn.close()
        
        print(f"\nFixed {total_fixes} books by author patterns")
        return total_fixes
    
    def create_missing_genres(self):
        """Create any missing genre categories"""
        print("\n🆕 CREATING MISSING GENRE CATEGORIES")
        print("=" * 40)
        
        # Note: PostgreSQL doesn't require explicit genre creation,
        # but we can track new genres being used
        new_genres = set()
        for fix in self.fixes:
            new_genres.add(fix['new_genre'])
        
        existing_genres = {
            'Romance', 'Literary Fiction', 'Science Fiction', 'Fantasy',
            'Mystery & Thriller', 'History', 'Biography & Memoir',
            'Business & Economics', 'Self-Help', 'Psychology',
            'Philosophy', 'Religion & Spirituality', 'Political Science',
            'Programming & Technology', 'Data Science & Analytics',
            'Science & Medicine', 'Science & Nature'
        }
        
        truly_new = new_genres - existing_genres
        if truly_new:
            print(f"New genre categories introduced:")
            for genre in sorted(truly_new):
                print(f"   • {genre}")
        else:
            print("All genres already exist in the system")
    
    def generate_fix_report(self):
        """Generate comprehensive fix report"""
        print(f"\n📋 PRECISION GENRE FIX REPORT")
        print("=" * 40)
        
        if not self.fixes:
            print("No fixes were applied.")
            return
        
        # Group by old genre
        by_old_genre = {}
        for fix in self.fixes:
            old = fix['old_genre']
            if old not in by_old_genre:
                by_old_genre[old] = []
            by_old_genre[old].append(fix)
        
        print(f"📊 Total Books Fixed: {len(self.fixes)}")
        print()
        
        for old_genre, genre_fixes in by_old_genre.items():
            print(f"📖 {old_genre} → Various Genres ({len(genre_fixes)} books):")
            
            # Group by new genre
            by_new_genre = {}
            for fix in genre_fixes:
                new = fix['new_genre']
                if new not in by_new_genre:
                    by_new_genre[new] = []
                by_new_genre[new].append(fix)
            
            for new_genre, new_fixes in by_new_genre.items():
                print(f"   → {new_genre} ({len(new_fixes)} books)")
                for fix in new_fixes[:3]:  # Show first 3 examples
                    print(f"     • \"{fix['title']}\"")
                if len(new_fixes) > 3:
                    print(f"     • ... and {len(new_fixes)-3} more")
            print()
    
    def show_updated_counts(self):
        """Show updated genre counts"""
        print(f"\n📊 UPDATED GENRE COUNTS")
        print("=" * 30)
        
        conn = psycopg2.connect(**self.config, cursor_factory=RealDictCursor)
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT genre, COUNT(*) as count
                    FROM books 
                    WHERE genre IN ('Romance', 'Literary Fiction', 'Science Fiction', 
                                   'Self-Help', 'Psychology', 'Philosophy',
                                   'Biography & Memoir', 'Religion & Spirituality',
                                   'Political Science', 'Science & Nature')
                    GROUP BY genre
                    ORDER BY count DESC
                """)
                
                results = cur.fetchall()
                
                for row in results:
                    print(f"   • {row['genre']}: {row['count']} books")
                    
        finally:
            conn.close()

def main():
    """Execute precision genre fixes"""
    print("🎯 PRECISION GENRE CLASSIFICATION FIX")
    print("=" * 45)
    print("Targeting specific misclassifications in Romance & Literary Fiction")
    print()
    
    fixer = PrecisionGenreFixer()
    
    # Apply all fixes
    romance_fixes = fixer.fix_romance_misclassifications()
    litfic_fixes = fixer.fix_literary_fiction_misclassifications()
    author_fixes = fixer.fix_by_author_patterns()
    
    # Create missing genres if needed
    fixer.create_missing_genres()
    
    # Generate reports
    fixer.generate_fix_report()
    fixer.show_updated_counts()
    
    total_fixes = romance_fixes + litfic_fixes + author_fixes
    print(f"\n✅ Applied {total_fixes} precision fixes")
    
    return total_fixes > 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)