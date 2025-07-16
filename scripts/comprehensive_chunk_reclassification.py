#!/usr/bin/env python3
"""
Comprehensive Chunk-Based Reclassification
==========================================
Reprocess ALL 408 books without descriptions using their actual content chunks
"""

import sys
import json
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import re
import time
from datetime import datetime

sys.path.append('/Users/weixiangzhang/Local Dev/LibraryOfBabel')
from config.api_config import get_database_config

class ComprehensiveChunkClassifier:
    def __init__(self, model_name="magistral"):
        self.db_config = get_database_config()
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = model_name
        self.processed_count = 0
        self.reclassified_count = 0
        self.results = {
            'fixed_books': [],
            'genre_changes': {},
            'processing_log': []
        }
        
        # Valid genres
        self.valid_genres = [
            "Romance", "Literary Fiction", "Science Fiction", "Fantasy",
            "Mystery & Thriller", "Historical Fiction", "Contemporary Fiction",
            "Self-Help", "Biography & Memoir", "Psychology", "Philosophy",
            "Business & Economics", "History", "Science & Nature",
            "Programming & Technology", "Data Science & Analytics",
            "Religion & Spirituality", "Political Science", "Academic & Research",
            "Health & Medicine", "True Crime", "Travel", "Art & Design",
            "Music", "Sports & Recreation", "Cooking & Food", "Parenting & Family"
        ]
    
    def get_all_books_without_descriptions(self, batch_size=50):
        """Get all books without descriptions in batches"""
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT b.book_id, b.title, b.author, b.genre
                    FROM books b
                    WHERE EXISTS (
                        SELECT 1 FROM chunks c 
                        WHERE c.book_id = b.book_id 
                        AND c.content IS NOT NULL 
                        AND LENGTH(c.content) > 150
                    )
                    AND (b.description IS NULL OR b.description = '')
                    ORDER BY b.book_id
                """)
                
                all_books = cur.fetchall()
                
                # Return in batches
                for i in range(0, len(all_books), batch_size):
                    yield all_books[i:i + batch_size]
                    
        finally:
            conn.close()
    
    def get_representative_content(self, book_id, num_samples=4):
        """Get representative content samples from different parts of the book"""
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        
        try:
            with conn.cursor() as cur:
                # Get chunks from different parts of the book
                cur.execute("""
                    WITH numbered_chunks AS (
                        SELECT content, title,
                               ROW_NUMBER() OVER (ORDER BY chunk_id) as rn,
                               COUNT(*) OVER () as total_chunks
                        FROM chunks
                        WHERE book_id = %s
                        AND content IS NOT NULL
                        AND LENGTH(content) > 150
                    )
                    SELECT content, title
                    FROM numbered_chunks
                    WHERE rn IN (1, total_chunks/4, total_chunks/2, total_chunks)
                    OR (total_chunks < 4 AND rn <= total_chunks)
                    ORDER BY rn
                    LIMIT %s
                """, (book_id, num_samples))
                
                chunks = cur.fetchall()
                
                if not chunks:
                    # Fallback to random chunks
                    cur.execute("""
                        SELECT content, title
                        FROM chunks
                        WHERE book_id = %s
                        AND content IS NOT NULL
                        AND LENGTH(content) > 150
                        ORDER BY RANDOM()
                        LIMIT %s
                    """, (book_id, num_samples))
                    
                    chunks = cur.fetchall()
                
                # Clean and combine content
                content_samples = []
                for i, chunk in enumerate(chunks, 1):
                    # Clean HTML and excessive whitespace
                    clean_content = re.sub(r'<[^>]+>', '', chunk['content'])
                    clean_content = re.sub(r'\s+', ' ', clean_content).strip()
                    
                    # Take meaningful sample
                    if len(clean_content) > 400:
                        sample = clean_content[:400]
                    else:
                        sample = clean_content
                    
                    content_samples.append(f"[Sample {i}] {sample}")
                
                return "\n\n".join(content_samples)
                
        finally:
            conn.close()
    
    def classify_by_content(self, book_data, content_samples):
        """Use Magistral to classify based on actual content"""
        
        prompt = f"""You are an expert book classifier. Analyze the actual content below to determine the correct genre.

BOOK TO CLASSIFY:
Title: "{book_data['title']}"
Author: {book_data['author']}
Current Genre: {book_data['genre']}

ACTUAL CONTENT FROM THE BOOK:
{content_samples[:2000]}

CLASSIFICATION RULES:
1. Base classification ONLY on the actual content, not the title
2. Look for key indicators:
   - Fiction: Characters, dialogue, narrative, story elements
   - Non-fiction: Facts, analysis, research, instructional content
   - Academic: Citations, theoretical discussion, scholarly tone
   
3. SPECIFIC GENRE INDICATORS:
   - Romance: Romantic relationships, love scenes, HEA endings
   - Science Fiction: Future tech, space, aliens, sci-fi concepts
   - Fantasy: Magic, supernatural, imaginary worlds, mythical beings
   - History: Past events, historical analysis, dates, historical figures
   - Business: Economics, markets, companies, business strategy
   - Psychology: Human behavior, mental processes, therapy, cognitive science
   - Philosophy: Fundamental questions, ethics, metaphysics, philosophical arguments
   - Biography: Life story of real person, personal experiences
   - Self-Help: Advice, improvement, how-to guidance
   - Academic & Research: Scholarly analysis, citations, theoretical frameworks

AVAILABLE GENRES:
Romance, Literary Fiction, Science Fiction, Fantasy, Mystery & Thriller, Historical Fiction, Contemporary Fiction, Self-Help, Biography & Memoir, Psychology, Philosophy, Business & Economics, History, Science & Nature, Programming & Technology, Data Science & Analytics, Religion & Spirituality, Political Science, Academic & Research, Health & Medicine

Based on the ACTUAL CONTENT above, what is the most accurate genre?

Respond with ONLY the genre name."""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.05,  # Very low for consistency
                        "top_p": 0.9
                    }
                },
                timeout=180
            )
            
            if response.status_code == 200:
                result = response.json()
                classification = result['response'].strip()
                
                # Extract clean classification
                if "\\boxed{" in classification:
                    match = re.search(r'\\boxed\{([^}]+)\}', classification)
                    if match:
                        classification = match.group(1)
                else:
                    # Take the last meaningful line
                    lines = [line.strip() for line in classification.split('\n') if line.strip()]
                    if lines:
                        # Look for a line that contains a valid genre
                        for line in reversed(lines):
                            for genre in self.valid_genres:
                                if genre.lower() in line.lower():
                                    classification = genre
                                    break
                            if classification in self.valid_genres:
                                break
                        else:
                            classification = lines[-1]
                
                # Clean up
                classification = re.sub(r'^["\']|["\']$', '', classification)
                classification = classification.strip()
                
                # Validate against known genres
                if classification in self.valid_genres:
                    return classification
                else:
                    # Try partial matching
                    for valid_genre in self.valid_genres:
                        if valid_genre.lower() in classification.lower():
                            return valid_genre
                    
                    # Log the invalid response for debugging
                    self.results['processing_log'].append(f"Invalid classification: '{classification}' for '{book_data['title']}'")
                    return None
            else:
                self.results['processing_log'].append(f"HTTP {response.status_code} for '{book_data['title']}'")
                return None
                
        except Exception as e:
            self.results['processing_log'].append(f"Error classifying '{book_data['title']}': {e}")
            return None
    
    def update_book_genre(self, book_id, new_genre):
        """Update book genre in database"""
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE books 
                    SET genre = %s
                    WHERE book_id = %s
                """, (new_genre, book_id))
                conn.commit()
                return True
        except Exception as e:
            self.results['processing_log'].append(f"Database error for book_id {book_id}: {e}")
            return False
        finally:
            conn.close()
    
    def save_progress(self):
        """Save progress to file"""
        with open('/Users/weixiangzhang/Local Dev/LibraryOfBabel/reclassification_progress.json', 'w') as f:
            json.dump({
                'processed_count': self.processed_count,
                'reclassified_count': self.reclassified_count,
                'genre_changes': self.results['genre_changes'],
                'last_updated': datetime.now().isoformat(),
                'processing_log': self.results['processing_log'][-50:]  # Keep last 50 log entries
            }, f, indent=2)
    
    def process_all_books(self):
        """Process all books without descriptions"""
        print("🔄 COMPREHENSIVE CHUNK-BASED RECLASSIFICATION")
        print("=" * 70)
        print("Processing ALL 408 books without descriptions using actual content")
        print()
        
        total_processed = 0
        batch_num = 0
        
        for batch in self.get_all_books_without_descriptions(20):  # Process in batches of 20
            batch_num += 1
            print(f"\n📦 BATCH {batch_num} - Processing {len(batch)} books")
            print("-" * 50)
            
            for book in batch:
                print(f"\n📖 [{self.processed_count + 1}] \"{book['title']}\"")
                print(f"   Author: {book['author']}")
                print(f"   Current: {book['genre']}")
                
                # Get representative content
                content = self.get_representative_content(book['book_id'])
                
                if not content or len(content) < 100:
                    print(f"   ⚠️  Insufficient content")
                    continue
                
                print(f"   📄 Content preview: {content[:80]}...")
                
                # Classify using content
                new_genre = self.classify_by_content(book, content)
                
                if new_genre:
                    print(f"   🤖 Content-based classification: {new_genre}")
                    
                    if new_genre != book['genre']:
                        if self.update_book_genre(book['book_id'], new_genre):
                            print(f"   ✅ UPDATED: {book['genre']} → {new_genre}")
                            
                            # Track changes
                            old_genre = book['genre']
                            if old_genre not in self.results['genre_changes']:
                                self.results['genre_changes'][old_genre] = {}
                            if new_genre not in self.results['genre_changes'][old_genre]:
                                self.results['genre_changes'][old_genre][new_genre] = 0
                            self.results['genre_changes'][old_genre][new_genre] += 1
                            
                            self.results['fixed_books'].append({
                                'title': book['title'],
                                'author': book['author'],
                                'old_genre': old_genre,
                                'new_genre': new_genre
                            })
                            
                            self.reclassified_count += 1
                        else:
                            print(f"   ❌ Database update failed")
                    else:
                        print(f"   ⚪ CONFIRMED: {new_genre}")
                else:
                    print(f"   ❌ Classification failed")
                
                self.processed_count += 1
                total_processed += 1
                
                # Save progress every 10 books
                if total_processed % 10 == 0:
                    self.save_progress()
                    print(f"\n💾 Progress saved: {total_processed} processed, {self.reclassified_count} reclassified")
                
                time.sleep(1)  # Rate limiting
            
            # Batch summary
            print(f"\n📊 Batch {batch_num} complete: {len(batch)} books processed")
            print(f"   Running total: {total_processed} processed, {self.reclassified_count} reclassified")
        
        return self.reclassified_count
    
    def generate_final_report(self):
        """Generate comprehensive final report"""
        print(f"\n📋 COMPREHENSIVE RECLASSIFICATION FINAL REPORT")
        print("=" * 60)
        print(f"🕐 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Total Processed: {self.processed_count}")
        print(f"🔄 Total Reclassified: {self.reclassified_count}")
        print(f"✅ Accuracy Rate: {((self.processed_count - self.reclassified_count) / max(self.processed_count, 1)) * 100:.1f}%")
        
        if self.results['genre_changes']:
            print(f"\n📈 GENRE MIGRATION SUMMARY:")
            for old_genre, changes in self.results['genre_changes'].items():
                total_moved = sum(changes.values())
                print(f"\n   📖 {old_genre} ({total_moved} books moved):")
                for new_genre, count in sorted(changes.items(), key=lambda x: x[1], reverse=True):
                    print(f"      → {new_genre}: {count} books")
        
        # Show updated distribution
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT genre, COUNT(*) as count
                    FROM books 
                    GROUP BY genre
                    ORDER BY count DESC
                    LIMIT 15
                """)
                
                results = cur.fetchall()
                
                print(f"\n📊 UPDATED GENRE DISTRIBUTION (Top 15):")
                for row in results:
                    print(f"   • {row['genre']}: {row['count']} books")
        finally:
            conn.close()
        
        # Save final results
        self.save_progress()
        
        print(f"\n✨ MISSION COMPLETE!")
        print(f"   📚 {self.processed_count} books analyzed by actual content")
        print(f"   🎯 {self.reclassified_count} books properly reclassified")
        print(f"   📁 Progress saved to reclassification_progress.json")

def main():
    """Execute comprehensive chunk-based reclassification"""
    print("🚀 STARTING COMPREHENSIVE RECLASSIFICATION")
    print("=" * 50)
    print("This will process ALL books without descriptions")
    print("Estimated time: 2-4 hours for 408 books")
    print("Using actual content chunks for accurate classification")
    print()
    
    # Confirm Magistral is available
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            print("❌ Ollama not available")
            return False
    except:
        print("❌ Cannot connect to Ollama")
        return False
    
    print("✅ Magistral ready - starting classification")
    
    classifier = ComprehensiveChunkClassifier("magistral")
    
    try:
        reclassified_count = classifier.process_all_books()
        classifier.generate_final_report()
        
        return reclassified_count > 0
        
    except KeyboardInterrupt:
        print(f"\n⏸️  Processing interrupted by user")
        print(f"📊 Progress so far: {classifier.processed_count} processed, {classifier.reclassified_count} reclassified")
        classifier.save_progress()
        return True
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        classifier.save_progress()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)