#!/usr/bin/env python3
"""
Analyze book completeness for BGE-embedded books.
Identifies books with suspiciously low word counts that might be incomplete.
"""

import psycopg2
import json
from datetime import datetime
from typing import Dict, List, Tuple
import statistics

def connect_db():
    """Connect to the knowledge_base database."""
    return psycopg2.connect(
        dbname="knowledge_base",
        user="weixiangzhang",
        host="localhost"
    )

def analyze_book_completeness(conn) -> Dict:
    """Analyze completeness of books with BGE embeddings."""

    cur = conn.cursor()

    # Get all books with BGE embeddings and their chunk statistics
    query = """
    WITH book_stats AS (
        SELECT
            b.book_id,
            b.title,
            b.author,
            b.genre,
            b.language,
            LENGTH(b.file_path) as path_length,
            COUNT(DISTINCT ce.chunk_id) as chunk_count,
            COUNT(DISTINCT c.chunk_id) as actual_chunks,
            SUM(c.word_count) as total_words,
            SUM(c.character_count) as total_chars,
            AVG(c.word_count) as avg_chunk_words,
            MIN(c.word_count) as min_chunk_words,
            MAX(c.word_count) as max_chunk_words
        FROM books b
        JOIN chunk_embeddings ce ON b.book_id = ce.book_id
        LEFT JOIN chunks c ON ce.chunk_id = c.chunk_id
        WHERE ce.embedding_model = 'bge-m3'
        GROUP BY b.book_id, b.title, b.author, b.genre, b.language, b.file_path
    )
    SELECT * FROM book_stats
    ORDER BY total_words ASC NULLS FIRST
    """

    cur.execute(query)
    books = cur.fetchall()

    # Analyze the data
    results = {
        'total_books': len(books),
        'analysis_date': datetime.now().isoformat(),
        'suspicious_books': [],
        'statistics': {},
        'categories': {
            'empty': [],
            'very_short': [],
            'short': [],
            'normal': [],
            'long': []
        }
    }

    word_counts = []
    chunk_counts = []

    for book in books:
        book_id, title, author, genre, language, path_length, chunk_count, actual_chunks, total_words, total_chars, avg_chunk_words, min_chunk_words, max_chunk_words = book

        # Collect for statistics
        if total_words:
            word_counts.append(total_words)
        if chunk_count:
            chunk_counts.append(chunk_count)

        # Categorize books
        book_info = {
            'book_id': book_id,
            'title': title[:100],  # Truncate long titles
            'author': author,
            'genre': genre,
            'language': language,
            'path_length': path_length,
            'chunk_count': chunk_count,
            'total_words': total_words or 0,
            'total_chars': total_chars or 0,
            'avg_chunk_words': float(avg_chunk_words) if avg_chunk_words else 0
        }

        # Categorize by word count
        if not total_words or total_words == 0:
            results['categories']['empty'].append(book_info)
            results['suspicious_books'].append(book_info)
        elif total_words < 1000:
            results['categories']['very_short'].append(book_info)
            results['suspicious_books'].append(book_info)
        elif total_words < 10000:
            results['categories']['short'].append(book_info)
        elif total_words < 200000:
            results['categories']['normal'].append(book_info)
        else:
            results['categories']['long'].append(book_info)

    # Calculate statistics
    if word_counts:
        results['statistics'] = {
            'word_count': {
                'min': min(word_counts),
                'max': max(word_counts),
                'mean': statistics.mean(word_counts),
                'median': statistics.median(word_counts),
                'stdev': statistics.stdev(word_counts) if len(word_counts) > 1 else 0
            },
            'chunk_count': {
                'min': min(chunk_counts),
                'max': max(chunk_counts),
                'mean': statistics.mean(chunk_counts),
                'median': statistics.median(chunk_counts)
            }
        }

    # Additional analysis for empty books
    cur.execute("""
        SELECT b.book_id, b.title, b.file_path, LENGTH(b.file_path)
        FROM books b
        JOIN chunk_embeddings ce ON b.book_id = ce.book_id
        LEFT JOIN chunks c ON ce.chunk_id = c.chunk_id
        WHERE ce.embedding_model = 'bge-m3'
        AND (c.word_count IS NULL OR c.word_count = 0)
        GROUP BY b.book_id, b.title, b.file_path
        LIMIT 20
    """)

    empty_book_details = cur.fetchall()
    results['empty_book_details'] = [
        {
            'book_id': row[0],
            'title': row[1][:100],
            'file_path': row[2],
            'path_length': row[3]
        }
        for row in empty_book_details
    ]

    cur.close()

    return results

def print_analysis(results: Dict):
    """Print analysis results in a readable format."""

    print("\n" + "="*80)
    print("BOOK COMPLETENESS ANALYSIS REPORT")
    print("="*80)
    print(f"Analysis Date: {results['analysis_date']}")
    print(f"Total Books Analyzed: {results['total_books']}")

    print("\n" + "-"*40)
    print("BOOK CATEGORIES BY WORD COUNT:")
    print("-"*40)

    categories = results['categories']
    print(f"Empty (0 words): {len(categories['empty'])} books")
    print(f"Very Short (<1K words): {len(categories['very_short'])} books")
    print(f"Short (1K-10K words): {len(categories['short'])} books")
    print(f"Normal (10K-200K words): {len(categories['normal'])} books")
    print(f"Long (>200K words): {len(categories['long'])} books")

    if results['statistics']:
        stats = results['statistics']
        print("\n" + "-"*40)
        print("WORD COUNT STATISTICS:")
        print("-"*40)
        print(f"Minimum: {stats['word_count']['min']:,.0f} words")
        print(f"Maximum: {stats['word_count']['max']:,.0f} words")
        print(f"Mean: {stats['word_count']['mean']:,.0f} words")
        print(f"Median: {stats['word_count']['median']:,.0f} words")
        print(f"Std Dev: {stats['word_count']['stdev']:,.0f} words")

    print("\n" + "-"*40)
    print("SUSPICIOUS BOOKS (Empty or <1K words):")
    print("-"*40)

    if results['suspicious_books']:
        print(f"Found {len(results['suspicious_books'])} suspicious books:")
        for i, book in enumerate(results['suspicious_books'][:10], 1):
            print(f"\n{i}. {book['title']}")
            print(f"   Author: {book['author']}")
            print(f"   Words: {book['total_words']:,}")
            print(f"   Chunks: {book['chunk_count']}")
            print(f"   Path Length: {book['path_length']} chars" if book['path_length'] else "   Path Length: Unknown")
    else:
        print("No suspicious books found!")

    if len(results['suspicious_books']) > 10:
        print(f"\n... and {len(results['suspicious_books']) - 10} more suspicious books")

    print("\n" + "-"*40)
    print("RECOMMENDATIONS:")
    print("-"*40)

    empty_count = len(categories['empty'])
    very_short_count = len(categories['very_short'])

    if empty_count > 0:
        print(f"⚠️  {empty_count} books have NO word count data - chunks may be missing content")
    if very_short_count > 0:
        print(f"⚠️  {very_short_count} books have <1K words - likely incomplete or corrupted")

    if empty_count + very_short_count > 0:
        print("\nSuggested actions:")
        print("1. Check if chunk content is properly stored in database")
        print("2. Verify original EPUB files are complete")
        print("3. Re-process suspicious books through the pipeline")
    else:
        print("✅ All books appear to have complete content!")

def save_results(results: Dict, filename: str):
    """Save detailed results to JSON file."""
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n💾 Detailed results saved to: {filename}")

def main():
    """Main execution function."""
    print("Connecting to database...")
    conn = connect_db()

    try:
        print("Analyzing book completeness...")
        results = analyze_book_completeness(conn)

        # Print analysis
        print_analysis(results)

        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"book_completeness_analysis_{timestamp}.json"
        save_results(results, filename)

        # Quick SQL check for specific issues
        cur = conn.cursor()
        print("\n" + "-"*40)
        print("QUICK DATABASE CHECK:")
        print("-"*40)

        # Check if chunks have content
        cur.execute("""
            SELECT
                COUNT(*) as total_chunks,
                COUNT(CASE WHEN content IS NULL OR content = '' THEN 1 END) as empty_content,
                COUNT(CASE WHEN word_count IS NULL OR word_count = 0 THEN 1 END) as zero_words
            FROM chunks
            WHERE chunk_id IN (
                SELECT DISTINCT chunk_id
                FROM chunk_embeddings
                WHERE embedding_model = 'bge-m3'
            )
        """)

        chunk_check = cur.fetchone()
        print(f"Total chunks with BGE embeddings: {chunk_check[0]:,}")
        print(f"Chunks with empty content: {chunk_check[1]:,}")
        print(f"Chunks with zero word count: {chunk_check[2]:,}")

        cur.close()

    finally:
        conn.close()

    print("\n" + "="*80)
    print("Analysis complete!")

if __name__ == "__main__":
    main()