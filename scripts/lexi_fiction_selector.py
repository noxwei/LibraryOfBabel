#!/usr/bin/env python3
"""
🎭 Fiction Book Selector for Lexi (Audio Synthesis Agent)
========================================================

Dr. Sarah Chen's PostgreSQL Fiction Book Selection Tool
Designed specifically for Lexi's TTS testing needs

Features:
- Connects to LibraryOfBabel PostgreSQL database
- Selects 15 diverse fiction books optimized for TTS
- Provides genre variety and word count analysis
- Exports selection for TTS pipeline integration

Usage:
    python3 lexi_fiction_selector.py
    
Database Requirements:
    - PostgreSQL running on localhost:5432
    - Database: knowledge_base
    - User: weixiangzhang (or set DB_USER env var)
"""

import os
import sys
import json
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import List, Dict, Any, Optional

class LexiFictionSelector:
    """
    Dr. Sarah Chen's Fiction Book Selector for Lexi
    Optimized for TTS testing with genre diversity and appropriate content length
    """
    
    def __init__(self):
        print("🎭 Dr. Sarah Chen's Fiction Selector for Lexi")
        print("=" * 60)
        
        # Database configuration (matches LibraryOfBabel standard)
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': int(os.getenv('DB_PORT', 5432))
        }
        
        print(f"🏛️ Database: {self.db_config['database']}@{self.db_config['host']}")
        
    def connect_database(self) -> Optional[psycopg2.extensions.connection]:
        """Establish secure connection to LibraryOfBabel PostgreSQL database"""
        try:
            conn = psycopg2.connect(**self.db_config)
            print("✅ Database connection established")
            return conn
        except psycopg2.Error as e:
            print(f"❌ Database connection failed: {e}")
            print("\n🔧 Troubleshooting:")
            print("   1. Ensure PostgreSQL is running")
            print("   2. Check database name: knowledge_base")
            print("   3. Verify user permissions")
            print("   4. Confirm port 5432 is accessible")
            return None
    
    def test_database_schema(self) -> bool:
        """Verify the database has the expected LibraryOfBabel schema"""
        conn = self.connect_database()
        if not conn:
            return False
            
        try:
            with conn.cursor() as cur:
                # Check for required tables
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('books', 'chunks', 'authors')
                """)
                tables = [row[0] for row in cur.fetchall()]
                
                if len(tables) >= 2:  # At minimum need books and chunks
                    print(f"✅ Schema validated: {', '.join(tables)} tables found")
                    return True
                else:
                    print(f"❌ Schema incomplete: only found {tables}")
                    return False
                    
        except Exception as e:
            print(f"❌ Schema validation failed: {e}")
            return False
        finally:
            conn.close()
    
    def get_fiction_books_for_tts(self, count: int = 15) -> List[Dict[str, Any]]:
        """
        Select fiction books optimized for Lexi's TTS testing
        
        Selection Criteria:
        - Fiction genre (various subgenres for voice diversity)
        - Appropriate word counts (40K+ words for meaningful testing)
        - Quality content (sufficient text chunks)
        - Genre diversity (different narrative styles)
        
        Returns:
            List of fiction books with TTS-relevant metadata
        """
        conn = self.connect_database()
        if not conn:
            return []
        
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                print(f"🔍 Searching for {count} fiction books...")
                
                # Dr. Sarah Chen's simplified fiction selection query
                cur.execute("""
                    SELECT 
                        b.book_id,
                        b.title,
                        b.author,
                        b.genre,
                        b.word_count,
                        b.description,
                        b.publication_year,
                        COALESCE(chunk_stats.chunk_count, 0) as chunk_count,
                        
                        -- TTS-specific metrics
                        CASE 
                            WHEN b.word_count BETWEEN 40000 AND 80000 THEN 'Short (2-3 hours)'
                            WHEN b.word_count BETWEEN 80000 AND 120000 THEN 'Medium (3-5 hours)' 
                            WHEN b.word_count BETWEEN 120000 AND 200000 THEN 'Long (5-8 hours)'
                            WHEN b.word_count > 200000 THEN 'Epic (8+ hours)'
                            ELSE 'Variable'
                        END as estimated_audio_length,
                        
                        -- Estimated reading time for TTS calibration
                        ROUND(b.word_count / 250.0 / 60.0, 1) as estimated_hours
                        
                    FROM books b
                    LEFT JOIN (
                        SELECT book_id, COUNT(*) as chunk_count
                        FROM chunks
                        GROUP BY book_id
                    ) chunk_stats ON b.book_id = chunk_stats.book_id
                    WHERE 
                        -- Fiction genre filter
                        (b.genre ILIKE '%fiction%' 
                         OR b.genre = 'Fiction'
                         OR b.genre ILIKE '%novel%')
                        -- Quality filters
                        AND b.word_count >= 40000  -- Minimum for meaningful TTS testing
                        AND b.title IS NOT NULL 
                        AND b.author IS NOT NULL
                        AND b.author != 'Unknown'
                        -- Content availability
                        AND LENGTH(COALESCE(b.description, '')) > 20
                    ORDER BY 
                        -- Prioritize diverse word counts and good chunk availability
                        CASE 
                            WHEN b.word_count BETWEEN 50000 AND 100000 THEN 1
                            WHEN b.word_count BETWEEN 100000 AND 150000 THEN 2
                            WHEN b.word_count > 150000 THEN 3
                            ELSE 4
                        END,
                        COALESCE(chunk_stats.chunk_count, 0) DESC,
                        RANDOM()
                    LIMIT %s
                """, (count,))
                
                books = cur.fetchall()
                
                if not books:
                    print("⚠️ No fiction books found with current criteria")
                    return []
                
                print(f"✅ Found {len(books)} fiction books")
                
                # Convert to structured data for Lexi
                fiction_selection = []
                for book in books:
                    try:
                        book_data = {
                            'book_id': book['book_id'],
                            'title': book['title'],
                            'author': book['author'],
                            'genre': book['genre'],
                            'word_count': book['word_count'],
                            'estimated_hours': float(book['estimated_hours']) if book['estimated_hours'] else 0.0,
                            'estimated_audio_length': book['estimated_audio_length'],
                            'description': (book['description'][:300] + '...') if book['description'] and len(book['description']) > 300 else (book['description'] or 'No description available'),
                            'publication_year': book['publication_year'],
                            'chunk_count': book['chunk_count'] or 0,
                            'tts_suitability': self._assess_tts_suitability(dict(book))
                        }
                        fiction_selection.append(book_data)
                    except Exception as e:
                        print(f"⚠️ Error processing book {book.get('book_id', 'unknown')}: {e}")
                        continue
                
                return fiction_selection
                
        except Exception as e:
            print(f"❌ Error selecting fiction books: {e}")
            return []
        finally:
            conn.close()
    
    def _assess_tts_suitability(self, book: Dict) -> str:
        """Assess TTS suitability based on book characteristics"""
        word_count = book['word_count']
        chunk_count = book['chunk_count']
        
        if word_count >= 80000 and chunk_count >= 20:
            return "Excellent - Long content, well-structured"
        elif word_count >= 50000 and chunk_count >= 10:
            return "Good - Adequate length and structure" 
        elif word_count >= 40000:
            return "Fair - Minimum viable length"
        else:
            return "Limited - Short content"
    
    def get_sample_text_chunks(self, book_id: int, sample_count: int = 3) -> List[Dict[str, Any]]:
        """Get representative text samples from a book for TTS testing"""
        conn = self.connect_database()
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
                        chapter_number,
                        CASE 
                            WHEN chapter_number <= 2 THEN 'Opening'
                            WHEN chapter_number >= (
                                SELECT MAX(chapter_number) * 0.8 
                                FROM chunks 
                                WHERE book_id = %s AND chapter_number IS NOT NULL
                            ) THEN 'Climax'
                            ELSE 'Middle'
                        END as narrative_section
                    FROM chunks 
                    WHERE 
                        book_id = %s 
                        AND content IS NOT NULL
                        AND word_count BETWEEN 150 AND 400  -- Ideal for TTS samples
                        AND LENGTH(content) > 200
                    ORDER BY 
                        CASE 
                            WHEN chapter_number <= 2 THEN 1
                            WHEN chapter_number >= (
                                SELECT MAX(chapter_number) * 0.8 
                                FROM chunks 
                                WHERE book_id = %s AND chapter_number IS NOT NULL
                            ) THEN 2
                            ELSE 3
                        END,
                        RANDOM()
                    LIMIT %s
                """, (book_id, book_id, book_id, sample_count))
                
                chunks = cur.fetchall()
                return [dict(chunk) for chunk in chunks]
                
        except Exception as e:
            print(f"❌ Error getting text samples: {e}")
            return []
        finally:
            conn.close()
    
    def create_lexi_tts_report(self) -> Dict[str, Any]:
        """Generate comprehensive TTS selection report for Lexi"""
        print("\n📊 Generating TTS Selection Report...")
        
        # Get fiction book selection
        books = self.get_fiction_books_for_tts(15)
        
        if not books:
            return {"error": "No suitable fiction books found"}
        
        # Analyze selection
        total_words = sum(book['word_count'] for book in books)
        total_hours = sum(book['estimated_hours'] for book in books)
        genres = list(set(book['genre'] for book in books))
        
        # Group by audio length for TTS planning
        by_length = {'Short': [], 'Medium': [], 'Long': [], 'Epic': []}
        for book in books:
            length_category = book['estimated_audio_length'].split(' ')[0]
            if length_category in by_length:
                by_length[length_category].append(book)
        
        # Generate report
        report = {
            "lexi_tts_selection": {
                "selection_date": datetime.now().isoformat(),
                "total_books": len(books),
                "total_words": total_words,
                "total_estimated_hours": round(total_hours, 1),
                "average_words_per_book": round(total_words / len(books)),
                "genres_included": genres,
                "length_distribution": {k: len(v) for k, v in by_length.items()},
                "database_source": f"{self.db_config['database']}@{self.db_config['host']}"
            },
            "books_by_length": by_length,
            "complete_selection": books,
            "tts_recommendations": {
                "testing_sequence": [
                    "1. Start with 'Short' books for initial voice calibration",
                    "2. Progress to 'Medium' books for comprehensive testing", 
                    "3. Use 'Long' books for endurance and consistency testing",
                    "4. Test different genres for voice adaptability"
                ],
                "sample_strategy": "Use 3-5 text chunks per book representing opening, middle, and climax sections",
                "voice_considerations": "Different genres may require distinct narrative voices and pacing"
            }
        }
        
        return report
    
    def export_for_tts_pipeline(self, output_file: str = None) -> str:
        """Export selection in format suitable for TTS pipeline integration"""
        report = self.create_lexi_tts_report()
        
        if "error" in report:
            print(f"❌ Export failed: {report['error']}")
            return ""
        
        # Default output location
        if not output_file:
            output_file = f"/tmp/lexi_fiction_selection_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✅ TTS selection exported to: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            return ""

def main():
    """Main execution for Lexi's fiction book selection"""
    print("🎤 LibraryOfBabel Fiction Book Selector")
    print("🏛️ Dr. Sarah Chen (Database Architecture)")
    print("🎭 Designed for Lexi (Audio Synthesis Agent)")
    print("=" * 60)
    
    # Initialize selector
    selector = LexiFictionSelector()
    
    # Test database connection and schema
    print("\n🔧 Database Validation...")
    if not selector.test_database_schema():
        print("❌ Database validation failed. Cannot proceed.")
        sys.exit(1)
    
    # Generate TTS selection report
    print("\n📚 Selecting Fiction Books for TTS Testing...")
    report = selector.create_lexi_tts_report()
    
    if "error" in report:
        print(f"❌ Selection failed: {report['error']}")
        sys.exit(1)
    
    # Display summary
    summary = report["lexi_tts_selection"]
    print(f"\n✅ TTS Fiction Selection Complete!")
    print(f"📊 Books selected: {summary['total_books']}")
    print(f"📝 Total words: {summary['total_words']:,}")
    print(f"🎵 Estimated audio: {summary['total_estimated_hours']} hours")
    print(f"🎭 Genres: {len(summary['genres_included'])}")
    
    # Show length distribution
    print(f"\n📏 Length Distribution:")
    for length, count in summary["length_distribution"].items():
        if count > 0:
            print(f"   {length}: {count} books")
    
    # Display sample selection
    print(f"\n📖 Sample Books Selected:")
    for i, book in enumerate(report["complete_selection"][:5], 1):
        print(f"{i:2}. '{book['title']}' by {book['author']}")
        print(f"     📊 {book['word_count']:,} words | {book['estimated_audio_length']} | {book['genre']}")
    
    if len(report["complete_selection"]) > 5:
        print(f"     ... and {len(report['complete_selection']) - 5} more books")
    
    # Export for TTS pipeline
    print(f"\n💾 Exporting for TTS Pipeline...")
    export_file = selector.export_for_tts_pipeline()
    
    if export_file:
        print(f"\n🚀 Ready for TTS Testing!")
        print(f"📁 Selection file: {export_file}")
        print(f"🎤 Lexi can now process these {summary['total_books']} fiction books")
        
        # Show TTS recommendations
        print(f"\n💡 TTS Testing Recommendations:")
        for rec in report["tts_recommendations"]["testing_sequence"]:
            print(f"   {rec}")
    
    print(f"\n🎉 Fiction book selection complete!")
    print(f"🏛️ Database queries optimized by Dr. Sarah Chen")

if __name__ == "__main__":
    main()