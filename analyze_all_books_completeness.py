#!/usr/bin/env python3
"""
Analyze completeness of ALL books in the database (not just BGE-embedded ones).
"""

import psycopg2
import json
from datetime import datetime
import statistics

def connect_db():
    """Connect to the knowledge_base database."""
    return psycopg2.connect(
        dbname="knowledge_base",
        user="weixiangzhang",
        host="localhost"
    )

def analyze_all_books(conn):
    """Analyze completeness of all books."""

    cur = conn.cursor()

    # Get statistics for ALL books
    query = """
    WITH book_stats AS (
        SELECT
            b.book_id,
            b.title,
            b.author,
            b.genre,
            b.language,
            COUNT(DISTINCT c.chunk_id) as chunk_count,
            SUM(c.word_count) as total_words,
            SUM(c.character_count) as total_chars,
            AVG(c.word_count) as avg_chunk_words,
            EXISTS (
                SELECT 1 FROM chunk_embeddings ce
                WHERE ce.book_id = b.book_id
                AND ce.embedding_model = 'bge-m3'
            ) as has_bge_embedding
        FROM books b
        LEFT JOIN chunks c ON b.book_id = c.book_id
        GROUP BY b.book_id, b.title, b.author, b.genre, b.language
    )
    SELECT * FROM book_stats
    ORDER BY total_words ASC NULLS FIRST
    """

    cur.execute(query)
    books = cur.fetchall()

    results = {
        'total_books': len(books),
        'analysis_date': datetime.now().isoformat(),
        'categories': {
            'no_chunks': [],
            'empty': [],
            'very_short': [],
            'short': [],
            'normal': [],
            'long': []
        },
        'embedding_coverage': {
            'with_bge': {'count': 0, 'word_counts': []},
            'without_bge': {'count': 0, 'word_counts': []}
        }
    }

    for book in books:
        book_id, title, author, genre, language, chunk_count, total_words, total_chars, avg_chunk_words, has_bge = book

        book_info = {
            'book_id': book_id,
            'title': title[:100] if title else 'Unknown',
            'author': author,
            'genre': genre,
            'language': language,
            'chunk_count': chunk_count or 0,
            'total_words': total_words or 0,
            'total_chars': total_chars or 0,
            'has_bge_embedding': has_bge
        }

        # Track embedding coverage
        if has_bge:
            results['embedding_coverage']['with_bge']['count'] += 1
            if total_words:
                results['embedding_coverage']['with_bge']['word_counts'].append(total_words)
        else:
            results['embedding_coverage']['without_bge']['count'] += 1
            if total_words:
                results['embedding_coverage']['without_bge']['word_counts'].append(total_words)

        # Categorize by content
        if not chunk_count or chunk_count == 0:
            results['categories']['no_chunks'].append(book_info)
        elif not total_words or total_words == 0:
            results['categories']['empty'].append(book_info)
        elif total_words < 1000:
            results['categories']['very_short'].append(book_info)
        elif total_words < 10000:
            results['categories']['short'].append(book_info)
        elif total_words < 200000:
            results['categories']['normal'].append(book_info)
        else:
            results['categories']['long'].append(book_info)

    # Calculate statistics for embedding coverage
    for category in ['with_bge', 'without_bge']:
        word_counts = results['embedding_coverage'][category]['word_counts']
        if word_counts:
            results['embedding_coverage'][category]['stats'] = {
                'min': min(word_counts),
                'max': max(word_counts),
                'mean': statistics.mean(word_counts),
                'median': statistics.median(word_counts)
            }

    cur.close()
    return results

def print_analysis(results):
    """Print analysis results."""

    print("\n" + "="*80)
    print("COMPLETE DATABASE BOOK ANALYSIS")
    print("="*80)
    print(f"Total Books in Database: {results['total_books']}")
    print(f"Analysis Date: {results['analysis_date']}")

    print("\n" + "-"*40)
    print("BOOK CATEGORIES BY WORD COUNT:")
    print("-"*40)

    categories = results['categories']
    print(f"No Chunks: {len(categories['no_chunks'])} books")
    print(f"Empty (0 words): {len(categories['empty'])} books")
    print(f"Very Short (<1K words): {len(categories['very_short'])} books")
    print(f"Short (1K-10K words): {len(categories['short'])} books")
    print(f"Normal (10K-200K words): {len(categories['normal'])} books")
    print(f"Long (>200K words): {len(categories['long'])} books")

    print("\n" + "-"*40)
    print("EMBEDDING COVERAGE:")
    print("-"*40)

    emb = results['embedding_coverage']
    print(f"Books WITH BGE embeddings: {emb['with_bge']['count']}")
    if 'stats' in emb['with_bge']:
        stats = emb['with_bge']['stats']
        print(f"  Word count - Mean: {stats['mean']:,.0f}, Median: {stats['median']:,.0f}")

    print(f"\nBooks WITHOUT BGE embeddings: {emb['without_bge']['count']}")
    if 'stats' in emb['without_bge']:
        stats = emb['without_bge']['stats']
        print(f"  Word count - Mean: {stats['mean']:,.0f}, Median: {stats['median']:,.0f}")

    # Show problematic books
    print("\n" + "-"*40)
    print("PROBLEMATIC BOOKS:")
    print("-"*40)

    problem_books = (categories['no_chunks'] + categories['empty'] +
                     categories['very_short'])

    if problem_books:
        print(f"\n⚠️  Found {len(problem_books)} problematic books:")

        # Group by problem type
        if categories['no_chunks']:
            print(f"\nNO CHUNKS ({len(categories['no_chunks'])} books):")
            for book in categories['no_chunks'][:5]:
                print(f"  - [{book['book_id']}] {book['title']}")
            if len(categories['no_chunks']) > 5:
                print(f"  ... and {len(categories['no_chunks']) - 5} more")

        if categories['empty']:
            print(f"\nEMPTY CONTENT ({len(categories['empty'])} books):")
            for book in categories['empty'][:5]:
                print(f"  - [{book['book_id']}] {book['title']}")
            if len(categories['empty']) > 5:
                print(f"  ... and {len(categories['empty']) - 5} more")

        if categories['very_short']:
            print(f"\nVERY SHORT (<1K words) ({len(categories['very_short'])} books):")
            for book in categories['very_short'][:5]:
                print(f"  - [{book['book_id']}] {book['title']} ({book['total_words']} words)")
            if len(categories['very_short']) > 5:
                print(f"  ... and {len(categories['very_short']) - 5} more")
    else:
        print("✅ No problematic books found!")

    # Non-embedded books analysis
    print("\n" + "-"*40)
    print("NON-EMBEDDED BOOKS ANALYSIS:")
    print("-"*40)

    non_embedded_problems = []
    for book in (categories['no_chunks'] + categories['empty'] +
                 categories['very_short'] + categories['short']):
        if not book['has_bge_embedding']:
            non_embedded_problems.append(book)

    print(f"Books without BGE embeddings: {emb['without_bge']['count']}")
    print(f"Of these, problematic ones: {len(non_embedded_problems)}")

    if non_embedded_problems[:5]:
        print("\nExamples of non-embedded problematic books:")
        for book in non_embedded_problems[:5]:
            print(f"  - [{book['book_id']}] {book['title']} ({book['total_words']} words, {book['chunk_count']} chunks)")

def save_results(results, filename):
    """Save results to JSON."""
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n💾 Detailed results saved to: {filename}")

def main():
    """Main execution."""
    print("Connecting to database...")
    conn = connect_db()

    try:
        print("Analyzing ALL books in database...")
        results = analyze_all_books(conn)

        print_analysis(results)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"all_books_analysis_{timestamp}.json"
        save_results(results, filename)

    finally:
        conn.close()

    print("\n" + "="*80)
    print("Analysis complete!")

if __name__ == "__main__":
    main()