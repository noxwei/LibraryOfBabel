#!/usr/bin/env python3
"""
🏛️ Batch Genre Classifier - LibraryOfBabel 
===========================================

Test the Advanced Genre Classifier on multiple books and show progress.
Utilizes Dr. Sarah Chen's semantic chunking system for improved accuracy.

Features:
- Test classification on 10 books 
- Progress reporting with detailed results
- Integration with semantic chunks from different book sections
- Performance metrics and confidence scoring
"""

import os
import sys
import time
import psycopg2
import psycopg2.extras
from pathlib import Path

# Add src to path for imports
script_dir = Path(__file__).parent
src_dir = script_dir.parent / 'src'
sys.path.append(str(src_dir))

from advanced_genre_classifier import AdvancedGenreClassifier

def get_test_books(limit=20):
    """Get a sample of books for testing with diverse titles"""
    
    db_config = {
        'host': 'localhost',
        'database': 'knowledge_base',
        'user': 'weixiangzhang',
        'port': 5432
    }
    
    try:
        with psycopg2.connect(**db_config) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Get books that have semantic chunks (from Dr. Sarah Chen's processing)
                cur.execute("""
                    SELECT DISTINCT b.book_id, b.title, b.author, b.genre as current_genre
                    FROM books b
                    INNER JOIN semantic_chunks sc ON b.book_id = sc.book_id
                    WHERE sc.chunk_level = 'medium'
                    AND b.title IS NOT NULL
                    ORDER BY b.book_id
                    LIMIT %s
                """, (limit,))
                
                books = cur.fetchall()
                return list(books)
                
    except Exception as e:
        print(f"❌ Database error: {e}")
        return []

def classify_books_batch(books, classifier):
    """Classify a batch of books and show progress"""
    
    print(f"🧪 Starting batch classification of {len(books)} books...")
    print("🔧 TESTING FIXED CLASSIFICATION SYSTEM - Fiction Override Active!")
    print("=" * 70)
    
    results = []
    total_processing_time = 0
    
    for i, book in enumerate(books, 1):
        print(f"\n📚 [{i}/{len(books)}] Processing: '{book['title']}'")
        print(f"👤 Author: {book['author']}")
        print(f"📂 Current genre: {book['current_genre'] or 'Not set'}")
        
        start_time = time.time()
        
        # Classify the book using semantic chunks
        result = classifier.classify_book(book['book_id'], use_semantic_chunks=True)
        
        processing_time = time.time() - start_time
        total_processing_time += processing_time
        
        if 'error' not in result:
            print(f"🎯 Primary Genre: {result['primary_genre']}")
            if result.get('secondary_genre'):
                print(f"🎯 Secondary Genre: {result['secondary_genre']}")
            if result.get('tertiary_genre'):
                print(f"🎯 Tertiary Genre: {result['tertiary_genre']}")
            print(f"📊 Confidence: {result['confidence']:.3f}")
            print(f"🏛️ LCC Code: {result.get('lcc_code', 'N/A')}")
            print(f"🔧 Methods used: {', '.join(result['classification_methods'])}")
            print(f"🧠 Used semantic chunks: {result['used_semantic_chunks']}")
            print(f"⚡ Processing time: {processing_time:.2f}s")
            
            # Show top 2 detailed analysis results
            if result.get('detailed_analysis'):
                top_analyses = result['detailed_analysis'][:2]
                print(f"🔍 Top genre matches:")
                for analysis in top_analyses:
                    print(f"   • {analysis['genre']}: {analysis['confidence']:.3f} confidence")
                    print(f"     (Keywords: {analysis['keyword_matches']}, Phrases: {analysis['phrase_matches']})")
            
            # Update database
            if classifier.update_book_genre_in_database(result):
                print("✅ Database updated successfully")
            else:
                print("❌ Database update failed")
                
            results.append(result)
        else:
            print(f"❌ Classification failed: {result['error']}")
        
        print("-" * 50)
    
    return results, total_processing_time

def generate_summary_report(results, total_time):
    """Generate a summary report of the batch classification"""
    
    print("\n" + "=" * 70)
    print("📊 BATCH CLASSIFICATION SUMMARY REPORT")
    print("=" * 70)
    
    if not results:
        print("❌ No successful classifications to report")
        return
    
    # Genre distribution
    genre_counts = {}
    confidence_scores = []
    
    for result in results:
        genre = result['final_genre']
        genre_counts[genre] = genre_counts.get(genre, 0) + 1
        confidence_scores.append(result['confidence'])
    
    print(f"📚 Total books classified: {len(results)}")
    print(f"⚡ Total processing time: {total_time:.2f}s")
    print(f"📈 Average processing time: {total_time/len(results):.2f}s per book")
    print(f"📊 Average confidence: {sum(confidence_scores)/len(confidence_scores):.3f}")
    print(f"📊 Confidence range: {min(confidence_scores):.3f} - {max(confidence_scores):.3f}")
    
    print(f"\n🎯 Genre Distribution:")
    for genre, count in sorted(genre_counts.items()):
        percentage = (count / len(results)) * 100
        print(f"  {genre}: {count} books ({percentage:.1f}%)")
    
    print(f"\n🧠 Semantic Chunks Usage:")
    semantic_used = sum(1 for r in results if r['used_semantic_chunks'])
    print(f"  Used semantic chunks: {semantic_used}/{len(results)} books")
    print(f"  Dr. Sarah Chen's system utilization: {(semantic_used/len(results))*100:.1f}%")
    
    print(f"\n🔧 Classification Methods:")
    all_methods = []
    for result in results:
        all_methods.extend(result['classification_methods'])
    
    method_counts = {}
    for method in all_methods:
        method_counts[method] = method_counts.get(method, 0) + 1
    
    for method, count in sorted(method_counts.items()):
        print(f"  {method}: {count} uses")

def main():
    """Main batch classification process"""
    
    print("🏛️ LibraryOfBabel - Batch Genre Classification")
    print("=" * 50)
    print("🧠 Utilizing Dr. Sarah Chen's Advanced Semantic Chunking")
    print("🤖 Powered by Hugging Face Transformers")
    print("📚 Testing on diverse book collection")
    print()
    
    # Initialize classifier
    print("🔧 Initializing Advanced Genre Classifier...")
    classifier = AdvancedGenreClassifier()
    
    # Get test books  
    print("📚 Selecting test books...")
    books = get_test_books(20)
    
    if not books:
        print("❌ No books found for testing")
        return
    
    print(f"✅ Found {len(books)} books for classification")
    
    # Run batch classification
    results, total_time = classify_books_batch(books, classifier)
    
    # Generate summary report
    generate_summary_report(results, total_time)
    
    print(f"\n🎉 Batch classification complete!")
    print(f"📈 THE GREAT ANTI LIBRARY OF BABEL classification enhanced!")

if __name__ == "__main__":
    main()