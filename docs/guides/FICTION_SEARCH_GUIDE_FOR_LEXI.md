# 🎭 Fiction Book Search Guide for Lexi (Audio Synthesis Agent)

## Overview

Dr. Sarah Chen's comprehensive guide for Lexi to search the PostgreSQL library for fiction books suitable for TTS testing. This guide covers database connection, schema understanding, and practical search examples.

## 📊 Database Schema Quick Reference

### Core Tables
- **`books`** - Main book metadata (titles, authors, genres, word counts)
- **`chunks`** - Text segments for detailed content analysis
- **`authors`** - Normalized author data

### Key Fiction-Related Fields
```sql
-- books table key fields for fiction selection
title VARCHAR(500)          -- Book title
author VARCHAR(255)         -- Author name  
genre VARCHAR(100)          -- Genre classification (e.g., "Fiction", "Literary Fiction")
word_count INTEGER          -- Total words (for TTS time estimation)
description TEXT            -- Book summary/synopsis
publication_year INTEGER    -- Publication date
```

## 🔗 Database Connection Configuration

### Standard Connection Parameters
```python
DB_CONFIG = {
    'host': 'localhost',           # or os.getenv('DB_HOST', 'localhost')
    'database': 'knowledge_base',  # or os.getenv('DB_NAME', 'knowledge_base')
    'user': 'weixiangzhang',      # or os.getenv('DB_USER', 'weixiangzhang')
    'port': 5432                   # or int(os.getenv('DB_PORT', 5432))
}
```

### Python Connection Example
```python
import psycopg2
import psycopg2.extras

def connect_to_database():
    """Establish connection to LibraryOfBabel PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='knowledge_base',
            user='weixiangzhang',
            port=5432
        )
        return conn
    except psycopg2.Error as e:
        print(f"Database connection failed: {e}")
        return None
```

## 🔍 Fiction Book Search Methods

### Method 1: Basic Fiction Genre Filter
```sql
-- Get 15 fiction books ordered by word count (good for TTS variety)
SELECT 
    book_id,
    title,
    author,
    genre,
    word_count,
    description,
    publication_year
FROM books 
WHERE 
    (genre ILIKE '%fiction%' OR genre = 'Fiction')
    AND word_count > 0
ORDER BY word_count DESC
LIMIT 15;
```

### Method 2: Using API Function (Recommended)
```sql
-- Use Dr. Sarah Chen's optimized API function
SELECT * FROM api_list_books(
    1,                    -- page number
    15,                   -- page size (15 books)
    NULL,                 -- search query (null for all)
    NULL,                 -- author filter (null for all)
    'Fiction'             -- genre filter (fiction only)
);
```

### Method 3: Advanced Fiction Subgenre Search
```sql
-- Search for specific fiction subgenres
SELECT 
    book_id,
    title,
    author,
    genre,
    word_count,
    LEFT(description, 200) || '...' as synopsis_preview
FROM books 
WHERE genre IN (
    'Fiction',
    'Literary Fiction', 
    'Science Fiction',
    'Fantasy',
    'Historical Fiction',
    'Contemporary Fiction',
    'Mystery & Thriller'
) 
AND word_count BETWEEN 50000 AND 150000  -- Good size for TTS testing
ORDER BY RANDOM()  -- Random selection for variety
LIMIT 15;
```

### Method 4: Fiction Books with Rich Content
```sql
-- Get fiction books with good descriptions (helpful for TTS context)
SELECT 
    b.book_id,
    b.title,
    b.author,
    b.genre,
    b.word_count,
    b.description,
    COUNT(c.chunk_id) as chunk_count
FROM books b
LEFT JOIN chunks c ON b.book_id = c.book_id
WHERE 
    b.genre ILIKE '%fiction%'
    AND b.description IS NOT NULL 
    AND LENGTH(b.description) > 100
    AND b.word_count > 0
GROUP BY b.book_id, b.title, b.author, b.genre, b.word_count, b.description
HAVING COUNT(c.chunk_id) > 10  -- Ensure books have sufficient chunks
ORDER BY b.word_count DESC
LIMIT 15;
```

## 🎯 Complete Python Implementation for Lexi

### lexi_fiction_selector.py
```python
#!/usr/bin/env python3
"""
Fiction Book Selector for Lexi (Audio Synthesis Agent)
====================================================

Selects 15 diverse fiction books from the LibraryOfBabel PostgreSQL database
for TTS testing and audio synthesis experiments.
"""

import psycopg2
import psycopg2.extras
import json
from typing import List, Dict, Any

class LexiFictionSelector:
    """Fiction book selector specifically designed for Lexi's TTS needs"""
    
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'database': 'knowledge_base', 
            'user': 'weixiangzhang',
            'port': 5432
        }
    
    def connect(self):
        """Establish database connection"""
        try:
            return psycopg2.connect(**self.db_config)
        except psycopg2.Error as e:
            print(f"❌ Database connection failed: {e}")
            return None
    
    def get_fiction_books_for_tts(self, count: int = 15) -> List[Dict[str, Any]]:
        """
        Get fiction books optimized for TTS testing
        
        Criteria:
        - Various fiction subgenres for voice diversity
        - Appropriate word counts (50K-150K words)
        - Good descriptions for context
        - High-quality content (sufficient chunks)
        """
        conn = self.connect()
        if not conn:
            return []
        
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Use the advanced fiction search with TTS optimization
                cur.execute("""
                    SELECT 
                        b.book_id,
                        b.title,
                        b.author,
                        b.genre,
                        b.word_count,
                        b.description,
                        b.publication_year,
                        COUNT(c.chunk_id) as chunk_count,
                        -- TTS-specific metrics
                        CASE 
                            WHEN b.word_count BETWEEN 50000 AND 100000 THEN 'Short (2-4 hours)'
                            WHEN b.word_count BETWEEN 100000 AND 150000 THEN 'Medium (4-6 hours)' 
                            WHEN b.word_count > 150000 THEN 'Long (6+ hours)'
                            ELSE 'Variable'
                        END as estimated_audio_length,
                        
                        -- Genre diversity score
                        CASE b.genre
                            WHEN 'Literary Fiction' THEN 1
                            WHEN 'Science Fiction' THEN 2  
                            WHEN 'Fantasy' THEN 3
                            WHEN 'Historical Fiction' THEN 4
                            WHEN 'Mystery & Thriller' THEN 5
                            ELSE 6
                        END as genre_diversity_score
                        
                    FROM books b
                    LEFT JOIN chunks c ON b.book_id = c.book_id
                    WHERE 
                        (b.genre ILIKE '%fiction%' OR b.genre = 'Fiction')
                        AND b.word_count > 40000  -- Minimum size for meaningful TTS testing
                        AND b.description IS NOT NULL 
                        AND LENGTH(b.description) > 100
                        AND b.title IS NOT NULL
                        AND b.author IS NOT NULL
                    GROUP BY 
                        b.book_id, b.title, b.author, b.genre, 
                        b.word_count, b.description, b.publication_year
                    HAVING COUNT(c.chunk_id) > 5  -- Ensure sufficient content chunks
                    ORDER BY 
                        genre_diversity_score,  -- Ensure genre variety
                        RANDOM()               -- Random selection within each genre
                    LIMIT %s
                """, (count,))
                
                books = cur.fetchall()
                
                # Convert to list of dictionaries for easier handling
                fiction_books = []
                for book in books:
                    fiction_books.append({
                        'book_id': book['book_id'],
                        'title': book['title'],
                        'author': book['author'], 
                        'genre': book['genre'],
                        'word_count': book['word_count'],
                        'description': book['description'][:500] + '...' if len(book['description']) > 500 else book['description'],
                        'publication_year': book['publication_year'],
                        'chunk_count': book['chunk_count'],
                        'estimated_audio_length': book['estimated_audio_length']
                    })
                
                return fiction_books
                
        except Exception as e:
            print(f"❌ Error querying fiction books: {e}")
            return []
        finally:
            conn.close()
    
    def get_sample_text_for_book(self, book_id: int, chunk_limit: int = 3) -> List[str]:
        """Get sample text chunks from a specific book for TTS testing"""
        conn = self.connect()
        if not conn:
            return []
        
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT 
                        chunk_id,
                        title as chunk_title,
                        content,
                        word_count,
                        chapter_number
                    FROM chunks 
                    WHERE 
                        book_id = %s 
                        AND content IS NOT NULL
                        AND word_count BETWEEN 100 AND 500  -- Good size for TTS samples
                    ORDER BY chapter_number, chunk_id
                    LIMIT %s
                """, (book_id, chunk_limit))
                
                chunks = cur.fetchall()
                return [chunk['content'] for chunk in chunks]
                
        except Exception as e:
            print(f"❌ Error getting sample text: {e}")
            return []
        finally:
            conn.close()
    
    def create_tts_selection_report(self) -> Dict[str, Any]:
        """Create comprehensive report of selected fiction books for TTS"""
        fiction_books = self.get_fiction_books_for_tts(15)
        
        if not fiction_books:
            return {"error": "No fiction books found"}
        
        # Organize by genre for variety verification
        by_genre = {}
        total_words = 0
        
        for book in fiction_books:
            genre = book['genre']
            if genre not in by_genre:
                by_genre[genre] = []
            by_genre[genre].append(book)
            total_words += book['word_count']
        
        report = {
            "selection_summary": {
                "total_books": len(fiction_books),
                "total_words": total_words,
                "estimated_total_audio_hours": round(total_words / 25000, 1),  # ~250 words/minute reading
                "genres_represented": list(by_genre.keys()),
                "selection_date": str(datetime.now())
            },
            "books_by_genre": by_genre,
            "all_books": fiction_books,
            "tts_recommendations": {
                "start_with": "Books with 50K-100K words for initial testing",
                "voice_variety": "Different genres will require different narrative voices",
                "sample_strategy": "Use 3-5 chunks per book for comprehensive testing"
            }
        }
        
        return report

def main():
    """Demo usage for Lexi"""
    print("🎭 LibraryOfBabel Fiction Book Selector for Lexi")
    print("=" * 60)
    
    selector = LexiFictionSelector()
    
    # Get fiction books selection
    print("📚 Selecting 15 fiction books for TTS testing...")
    report = selector.create_tts_selection_report()
    
    if "error" in report:
        print(f"❌ Error: {report['error']}")
        return
    
    # Display summary
    summary = report["selection_summary"]
    print(f"✅ Selected {summary['total_books']} fiction books")
    print(f"📊 Total words: {summary['total_words']:,}")
    print(f"🎵 Estimated audio: {summary['estimated_total_audio_hours']} hours")
    print(f"🎭 Genres: {', '.join(summary['genres_represented'])}")
    
    # Show sample books
    print("\n📖 Sample Selection:")
    for i, book in enumerate(report["all_books"][:5], 1):
        print(f"{i}. '{book['title']}' by {book['author']}")
        print(f"   Genre: {book['genre']} | Words: {book['word_count']:,} | {book['estimated_audio_length']}")
    
    # Save detailed report
    with open('/tmp/lexi_fiction_selection.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n💾 Full report saved to: /tmp/lexi_fiction_selection.json")
    print("🎤 Ready for TTS testing!")

if __name__ == "__main__":
    main()
```

## 🎵 TTS-Specific Considerations

### Word Count Guidelines
- **Short books (50K-100K words)**: 2-4 hours audio, good for initial testing
- **Medium books (100K-150K words)**: 4-6 hours audio, comprehensive testing  
- **Long books (150K+ words)**: 6+ hours audio, endurance testing

### Genre Variety for Voice Testing
- **Literary Fiction**: Sophisticated vocabulary, varied sentence structure
- **Science Fiction**: Technical terms, future concepts
- **Fantasy**: Creative names, magical terminology
- **Historical Fiction**: Period-appropriate language
- **Mystery/Thriller**: Suspenseful pacing, dialogue-heavy

### Sample Text Selection
```sql
-- Get diverse text samples from a book
SELECT 
    content,
    word_count,
    chapter_number,
    CASE 
        WHEN chapter_number <= 3 THEN 'Opening'
        WHEN chapter_number >= (SELECT MAX(chapter_number) * 0.8 FROM chunks WHERE book_id = X) THEN 'Climax'
        ELSE 'Middle'
    END as narrative_section
FROM chunks 
WHERE book_id = ? 
AND word_count BETWEEN 200 AND 400
ORDER BY chapter_number
LIMIT 10;
```

## 🚀 Quick Start for Lexi

### 1. Test Database Connection
```bash
python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(host='localhost', database='knowledge_base', user='weixiangzhang', port=5432)
    print('✅ Database connection successful!')
    conn.close()
except Exception as e:
    print(f'❌ Connection failed: {e}')
"
```

### 2. Quick Fiction Book Query
```sql
-- Simple 15 fiction books query
SELECT book_id, title, author, word_count 
FROM books 
WHERE genre ILIKE '%fiction%' 
LIMIT 15;
```

### 3. Use the Python Script
```bash
python3 lexi_fiction_selector.py
```

## 📞 Support

For database issues or advanced queries, consult:
- **Dr. Sarah Chen (DBA Team)**: PostgreSQL optimization and advanced queries
- **Database Schema**: `/docs/project_docs/DATABASE_SCHEMA.md`
- **API Functions**: `phase1_postgresql_functions_fixed.sql`

---
*Guide prepared by Dr. Sarah Chen for Lexi's TTS fiction book selection needs*