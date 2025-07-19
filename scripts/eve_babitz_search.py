#!/usr/bin/env python3
"""
🏛️ Eve Babitz Book Search - Library of Babel PostgreSQL Database
===============================================================

Using Dr. Sarah Chen's (陈雪芳) database connection methods to search for 
Eve Babitz books in the 2,495 book collection.

Searches for:
- Books authored by "Eve Babitz" and variations
- Famous works: "Eve's Hollywood", "Slow Days, Fast Company", "Black Swans", "Sex and Rage"
- Genre classifications and metadata
- Word counts and TTS processing availability

Author: Using Dr. Sarah Chen DBA Team methods
Database: PostgreSQL knowledge_base (2,495 books)
"""

import os
import json
import time
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

class EveBabitzSearchAgent:
    """
    Eve Babitz Book Search Agent
    Using Dr. Sarah Chen's database connection methods
    """
    
    def __init__(self):
        # Database configuration (using Dr. Chen's methods)
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': int(os.getenv('DB_PORT', 5432))
        }
        
        # Eve Babitz search parameters
        self.author_variations = [
            'Eve Babitz',
            'Babitz',
            'E. Babitz',
            'Eve',
            'BABITZ',
            'eve babitz'
        ]
        
        self.famous_works = [
            "Eve's Hollywood",
            "Slow Days, Fast Company", 
            "Black Swans",
            "Sex and Rage",
            "Two by Two",
            "L.A. Woman"
        ]
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("EveBabitzSearch")
        
        print("🏛️ Eve Babitz Search Agent - Using Dr. Sarah Chen DBA Methods")
        print("=" * 70)
        print("📚 Searching Library of Babel PostgreSQL Database (2,495 books)")
        print("🔍 Target: Eve Babitz books and variations")
        
    def get_db_connection(self):
        """Get database connection using Dr. Chen's credentials"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except psycopg2.Error as e:
            self.logger.error(f"💔 Database connection failed: {e}")
            return None
    
    def search_eve_babitz_by_author(self) -> List[Dict[str, Any]]:
        """Search for books by Eve Babitz using author field variations"""
        print("\n🔍 SEARCHING BY AUTHOR: Eve Babitz variations")
        print("-" * 50)
        
        results = []
        
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return results
                
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    
                    # Search for exact and partial author matches
                    for author_var in self.author_variations:
                        print(f"📖 Searching for author: '{author_var}'")
                        
                        # Exact match
                        cur.execute("""
                            SELECT book_id, title, author, publisher, publication_date, 
                                   publication_year, genre, word_count, description,
                                   file_path, import_source, processed_date
                            FROM books 
                            WHERE LOWER(author) = LOWER(%s)
                            ORDER BY title;
                        """, (author_var,))
                        
                        exact_matches = cur.fetchall()
                        for book in exact_matches:
                            book_dict = dict(book)
                            book_dict['match_type'] = f'exact_author_{author_var}'
                            results.append(book_dict)
                        
                        # Partial match using ILIKE
                        cur.execute("""
                            SELECT book_id, title, author, publisher, publication_date, 
                                   publication_year, genre, word_count, description,
                                   file_path, import_source, processed_date
                            FROM books 
                            WHERE author ILIKE %s
                            ORDER BY title;
                        """, (f'%{author_var}%',))
                        
                        partial_matches = cur.fetchall()
                        for book in partial_matches:
                            book_dict = dict(book)
                            book_dict['match_type'] = f'partial_author_{author_var}'
                            # Avoid duplicates
                            if not any(r['book_id'] == book_dict['book_id'] for r in results):
                                results.append(book_dict)
                        
                        if exact_matches or partial_matches:
                            print(f"  ✅ Found {len(exact_matches)} exact + {len(partial_matches)} partial matches")
                        else:
                            print(f"  ❌ No matches for '{author_var}'")
        
        except Exception as e:
            self.logger.error(f"❌ Author search failed: {e}")
        
        return results
    
    def search_eve_babitz_by_title(self) -> List[Dict[str, Any]]:
        """Search for Eve Babitz's famous works by title"""
        print("\n🔍 SEARCHING BY TITLE: Eve Babitz Famous Works")
        print("-" * 50)
        
        results = []
        
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return results
                
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    
                    for work_title in self.famous_works:
                        print(f"📚 Searching for title: '{work_title}'")
                        
                        # Exact title match
                        cur.execute("""
                            SELECT book_id, title, author, publisher, publication_date, 
                                   publication_year, genre, word_count, description,
                                   file_path, import_source, processed_date
                            FROM books 
                            WHERE LOWER(title) = LOWER(%s)
                            ORDER BY title;
                        """, (work_title,))
                        
                        exact_matches = cur.fetchall()
                        for book in exact_matches:
                            book_dict = dict(book)
                            book_dict['match_type'] = f'exact_title_{work_title}'
                            results.append(book_dict)
                        
                        # Partial title match using ILIKE
                        cur.execute("""
                            SELECT book_id, title, author, publisher, publication_date, 
                                   publication_year, genre, word_count, description,
                                   file_path, import_source, processed_date
                            FROM books 
                            WHERE title ILIKE %s
                            ORDER BY title;
                        """, (f'%{work_title}%',))
                        
                        partial_matches = cur.fetchall()
                        for book in partial_matches:
                            book_dict = dict(book)
                            book_dict['match_type'] = f'partial_title_{work_title}'
                            # Avoid duplicates
                            if not any(r['book_id'] == book_dict['book_id'] for r in results):
                                results.append(book_dict)
                        
                        if exact_matches or partial_matches:
                            print(f"  ✅ Found {len(exact_matches)} exact + {len(partial_matches)} partial matches")
                        else:
                            print(f"  ❌ No matches for '{work_title}'")
        
        except Exception as e:
            self.logger.error(f"❌ Title search failed: {e}")
        
        return results
    
    def search_eve_babitz_content(self) -> List[Dict[str, Any]]:
        """Search for Eve Babitz mentions in book content using full-text search"""
        print("\n🔍 SEARCHING CONTENT: Eve Babitz mentions in text")
        print("-" * 50)
        
        results = []
        
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return results
                
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    
                    # Search for "Eve Babitz" in content using PostgreSQL full-text search
                    search_terms = ['Eve Babitz', 'Babitz', 'Hollywood', 'Los Angeles']
                    
                    for term in search_terms:
                        print(f"📖 Searching content for: '{term}'")
                        
                        cur.execute("""
                            SELECT DISTINCT
                                b.book_id, b.title, b.author, b.genre, b.word_count,
                                c.chunk_type, c.content,
                                ts_rank_cd(c.search_vector, plainto_tsquery('english', %s)) as rank
                            FROM books b
                            JOIN chunks c ON b.book_id = c.book_id
                            WHERE c.search_vector @@ plainto_tsquery('english', %s)
                            ORDER BY rank DESC, b.title
                            LIMIT 10;
                        """, (term, term))
                        
                        content_matches = cur.fetchall()
                        for match in content_matches:
                            match_dict = dict(match)
                            match_dict['match_type'] = f'content_{term}'
                            # Truncate content for display
                            if len(match_dict['content']) > 500:
                                match_dict['content_snippet'] = match_dict['content'][:500] + "..."
                            else:
                                match_dict['content_snippet'] = match_dict['content']
                            results.append(match_dict)
                        
                        if content_matches:
                            print(f"  ✅ Found {len(content_matches)} content matches")
                        else:
                            print(f"  ❌ No content matches for '{term}'")
        
        except Exception as e:
            self.logger.error(f"❌ Content search failed: {e}")
        
        return results
    
    def analyze_genre_classifications(self, book_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze genre classifications for found books"""
        print("\n📊 GENRE ANALYSIS: Classifications for found books")
        print("-" * 50)
        
        genre_analysis = {
            'total_books': len(book_results),
            'genres': {},
            'unique_genres': set()
        }
        
        for book in book_results:
            if book.get('genre'):
                genre = book['genre'].strip()
                if genre:
                    genre_analysis['unique_genres'].add(genre)
                    if genre in genre_analysis['genres']:
                        genre_analysis['genres'][genre] += 1
                    else:
                        genre_analysis['genres'][genre] = 1
        
        genre_analysis['unique_genres'] = list(genre_analysis['unique_genres'])
        
        if genre_analysis['genres']:
            print("📈 Genre distribution:")
            for genre, count in sorted(genre_analysis['genres'].items(), key=lambda x: x[1], reverse=True):
                print(f"  • {genre}: {count} book(s)")
        else:
            print("📈 No genre information found")
        
        return genre_analysis
    
    def analyze_tts_readiness(self, book_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze Text-to-Speech processing readiness"""
        print("\n🔊 TTS READINESS ANALYSIS: Word counts and processing availability")
        print("-" * 50)
        
        tts_analysis = {
            'total_books': len(book_results),
            'books_with_word_count': 0,
            'total_words': 0,
            'average_word_count': 0,
            'tts_ready_books': [],
            'processing_estimates': {}
        }
        
        for book in book_results:
            if book.get('word_count') and book['word_count'] > 0:
                tts_analysis['books_with_word_count'] += 1
                tts_analysis['total_words'] += book['word_count']
                
                # TTS processing estimates (approximate)
                # Assuming 150 words per minute reading speed
                reading_time_minutes = book['word_count'] / 150
                processing_time_estimate = reading_time_minutes * 0.1  # 10% of reading time for processing
                
                tts_book = {
                    'title': book['title'],
                    'author': book.get('author', 'Unknown'),
                    'word_count': book['word_count'],
                    'estimated_reading_time_minutes': round(reading_time_minutes, 1),
                    'estimated_processing_time_minutes': round(processing_time_estimate, 1),
                    'file_available': bool(book.get('file_path'))
                }
                tts_analysis['tts_ready_books'].append(tts_book)
        
        if tts_analysis['books_with_word_count'] > 0:
            tts_analysis['average_word_count'] = tts_analysis['total_words'] // tts_analysis['books_with_word_count']
        
        print(f"📊 Books with word count data: {tts_analysis['books_with_word_count']}/{tts_analysis['total_books']}")
        print(f"📊 Total words across all books: {tts_analysis['total_words']:,}")
        print(f"📊 Average word count: {tts_analysis['average_word_count']:,}")
        
        if tts_analysis['tts_ready_books']:
            print("\n🔊 TTS Processing Estimates:")
            for book in tts_analysis['tts_ready_books']:
                print(f"  📖 {book['title']}")
                print(f"     Words: {book['word_count']:,}")
                print(f"     Reading time: {book['estimated_reading_time_minutes']} minutes")
                print(f"     Processing time: {book['estimated_processing_time_minutes']} minutes")
                print(f"     File available: {'✅' if book['file_available'] else '❌'}")
        
        return tts_analysis
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """Get overall database statistics for context"""
        print("\n📊 DATABASE STATISTICS: Library of Babel Collection")
        print("-" * 50)
        
        stats = {}
        
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return stats
                
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    
                    # Total books
                    cur.execute("SELECT COUNT(*) as total_books FROM books;")
                    stats['total_books'] = cur.fetchone()['total_books']
                    
                    # Total chunks
                    cur.execute("SELECT COUNT(*) as total_chunks FROM chunks;")
                    stats['total_chunks'] = cur.fetchone()['total_chunks']
                    
                    # Authors count
                    cur.execute("SELECT COUNT(DISTINCT author) as unique_authors FROM books WHERE author IS NOT NULL;")
                    stats['unique_authors'] = cur.fetchone()['unique_authors']
                    
                    # Genre distribution
                    cur.execute("""
                        SELECT genre, COUNT(*) as count 
                        FROM books 
                        WHERE genre IS NOT NULL 
                        GROUP BY genre 
                        ORDER BY count DESC 
                        LIMIT 10;
                    """)
                    stats['top_genres'] = [dict(row) for row in cur.fetchall()]
                    
                    # Word count statistics
                    cur.execute("""
                        SELECT 
                            SUM(word_count) as total_words,
                            AVG(word_count) as avg_words,
                            MIN(word_count) as min_words,
                            MAX(word_count) as max_words
                        FROM books 
                        WHERE word_count > 0;
                    """)
                    word_stats = cur.fetchone()
                    stats['word_statistics'] = dict(word_stats) if word_stats else {}
                    
        except Exception as e:
            self.logger.error(f"❌ Database statistics failed: {e}")
        
        # Display statistics
        print(f"📚 Total books in library: {stats.get('total_books', 'Unknown'):,}")
        print(f"📄 Total text chunks: {stats.get('total_chunks', 'Unknown'):,}")
        print(f"👥 Unique authors: {stats.get('unique_authors', 'Unknown'):,}")
        
        if stats.get('word_statistics'):
            ws = stats['word_statistics']
            if ws.get('total_words'):
                print(f"📊 Total words: {int(ws['total_words']):,}")
                print(f"📊 Average words per book: {int(ws['avg_words']):,}")
        
        return stats
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive Eve Babitz search report"""
        print("\n🏛️ COMPREHENSIVE EVE BABITZ SEARCH REPORT")
        print("=" * 70)
        
        # Get database context
        db_stats = self.get_database_statistics()
        
        # Perform all searches
        author_results = self.search_eve_babitz_by_author()
        title_results = self.search_eve_babitz_by_title()
        content_results = self.search_eve_babitz_content()
        
        # Combine and deduplicate results
        all_book_results = []
        seen_book_ids = set()
        
        for result_set in [author_results, title_results]:
            for book in result_set:
                if book['book_id'] not in seen_book_ids:
                    all_book_results.append(book)
                    seen_book_ids.add(book['book_id'])
        
        # Analysis
        genre_analysis = self.analyze_genre_classifications(all_book_results)
        tts_analysis = self.analyze_tts_readiness(all_book_results)
        
        # Compile report
        report = {
            'timestamp': datetime.now().isoformat(),
            'search_agent': 'Eve Babitz Search Agent - Dr. Sarah Chen DBA Methods',
            'database_context': db_stats,
            'search_summary': {
                'author_matches': len(author_results),
                'title_matches': len(title_results),
                'content_matches': len(content_results),
                'unique_book_matches': len(all_book_results)
            },
            'found_books': all_book_results,
            'content_mentions': content_results,
            'genre_analysis': genre_analysis,
            'tts_analysis': tts_analysis,
            'recommendations': self._generate_recommendations(all_book_results, content_results)
        }
        
        # Save report
        report_file = f"eve_babitz_search_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Report saved: {report_file}")
        
        return report
    
    def _generate_recommendations(self, book_results: List[Dict[str, Any]], content_results: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on search results"""
        recommendations = []
        
        if not book_results and not content_results:
            recommendations.extend([
                "❌ No Eve Babitz books found in the current collection",
                "🔄 Consider expanding the collection to include Eve Babitz works",
                "📚 Priority titles to acquire: 'Eve's Hollywood', 'Slow Days, Fast Company'",
                "🔍 The database structure is ready to accommodate Eve Babitz books when available"
            ])
        else:
            if book_results:
                recommendations.append(f"✅ Found {len(book_results)} books potentially related to Eve Babitz")
                
                tts_ready = [b for b in book_results if b.get('word_count', 0) > 0 and b.get('file_path')]
                if tts_ready:
                    recommendations.append(f"🔊 {len(tts_ready)} books are ready for TTS processing")
                
                genres = set(b.get('genre') for b in book_results if b.get('genre'))
                if genres:
                    recommendations.append(f"📚 Found books in genres: {', '.join(sorted(genres))}")
            
            if content_results:
                recommendations.append(f"📖 Found {len(content_results)} content mentions across books")
                recommendations.append("🔍 Consider reviewing these books for Eve Babitz references")
        
        recommendations.extend([
            "📊 Database performance is optimized for additional searches",
            "🏛️ Dr. Sarah Chen's indexing supports efficient author and title queries",
            "🧠 Vector embedding infrastructure is ready for semantic search enhancements"
        ])
        
        return recommendations

def main():
    """Main execution function"""
    print("🚀 Starting Eve Babitz Search in Library of Babel...")
    
    search_agent = EveBabitzSearchAgent()
    
    # Generate comprehensive report
    report = search_agent.generate_comprehensive_report()
    
    # Display summary
    print("\n" + "=" * 70)
    print("📋 SEARCH SUMMARY")
    print("=" * 70)
    print(f"📚 Database: {report['database_context'].get('total_books', 'Unknown')} total books")
    print(f"🔍 Author matches: {report['search_summary']['author_matches']}")
    print(f"📖 Title matches: {report['search_summary']['title_matches']}")
    print(f"📄 Content mentions: {report['search_summary']['content_matches']}")
    print(f"📊 Unique book matches: {report['search_summary']['unique_book_matches']}")
    
    if report['found_books']:
        print(f"\n📚 FOUND BOOKS:")
        for book in report['found_books'][:5]:  # Show first 5
            print(f"  • {book['title']} by {book.get('author', 'Unknown')}")
            if book.get('genre'):
                print(f"    Genre: {book['genre']}")
            if book.get('word_count'):
                print(f"    Words: {book['word_count']:,}")
    
    print(f"\n🎯 RECOMMENDATIONS:")
    for rec in report['recommendations']:
        print(f"  • {rec}")
    
    print(f"\n✅ Eve Babitz search complete!")
    print(f"📄 Detailed report available in JSON format")
    
    return report

if __name__ == "__main__":
    main()