#!/usr/bin/env python3
"""
Ultimate Library Reclassification Daemon
========================================
Reprocess ALL 1,243 books with llama3.2:3b + improved chunk selection
- Skips front matter completely
- Focuses on actual book content
- Fast, accurate, and comprehensive
"""

import sys
import json
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import re
import time
import signal
import atexit
import os
from datetime import datetime
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config.api_config import get_database_config

class UltimateLibraryReclassificationDaemon:
    def __init__(self):
        self.db_config = get_database_config()
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = "llama3.2:3b"  # Fast, accurate model
        
        # State file for persistence
        self.state_file = project_root / "daemons" / "ultimate_library_state.json"
        self.log_file = project_root / "daemons" / "ultimate_library.log"
        self.pid_file = project_root / "daemons" / "ultimate_library.pid"
        
        # Initialize state
        self.state = {
            "processed_books": [],
            "processed_count": 0,
            "reclassified_count": 0,
            "confirmed_count": 0,
            "failed_count": 0,
            "front_matter_filtered_count": 0,
            "current_batch": 0,
            "total_books": 0,
            "start_time": None,
            "last_update": None,
            "status": "initializing",
            "genre_changes": {},
            "errors": [],
            "accuracy_stats": {}
        }
        
        # Load existing state if available
        self.load_state()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Valid genres with enhanced list
        self.valid_genres = [
            "Romance", "Literary Fiction", "Science Fiction", "Fantasy",
            "Mystery & Thriller", "Historical Fiction", "Contemporary Fiction",
            "Self-Help", "Biography & Memoir", "Psychology", "Philosophy",
            "Business & Economics", "History", "Science & Nature",
            "Programming & Technology", "Data Science & Analytics",
            "Religion & Spirituality", "Political Science", "Academic & Research",
            "Health & Medicine", "True Crime", "Travel", "Art & Design"
        ]
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        atexit.register(self.cleanup)
        
        # Write PID file
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))
    
    def load_state(self):
        """Load previous state if exists"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    saved_state = json.load(f)
                    self.state.update(saved_state)
                    print(f"📂 Loaded previous state: {self.state['processed_count']} books processed")
            except Exception as e:
                print(f"⚠️  Could not load previous state: {e}")
    
    def save_state(self):
        """Save current state"""
        self.state["last_update"] = datetime.now().isoformat()
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.state["status"] = "stopping"
        self.save_state()
        sys.exit(0)
    
    def cleanup(self):
        """Cleanup on exit"""
        if self.pid_file.exists():
            self.pid_file.unlink()
        self.save_state()
    
    def is_front_matter(self, content):
        """Advanced front matter detection"""
        content_lower = content.lower().strip()
        
        # Strong front matter indicators
        strong_indicators = [
            'copyright', '©', 'all rights reserved', 'published by',
            'isbn', 'library of congress', 'cataloging', 'first published',
            'this book is sold', 'reproduction or translation', 'without permission',
            'printed in', 'designed by', 'cover design', 'jacket design'
        ]
        
        # Moderate indicators
        moderate_indicators = [
            'dedication', 'acknowledgments', 'acknowledgement', 'table of contents',
            'contents', 'index', 'bibliography', 'notes', 'about the author',
            'also by', 'other books', 'praise for', 'advance praise'
        ]
        
        # Weak indicators (need multiple)
        weak_indicators = [
            'publisher', 'edition', 'printing', 'version', 'imprint'
        ]
        
        # Check for strong indicators (any one triggers)
        for indicator in strong_indicators:
            if indicator in content_lower:
                return True
        
        # Check for moderate indicators (1-2 trigger)
        moderate_count = sum(1 for indicator in moderate_indicators if indicator in content_lower)
        if moderate_count >= 1:
            return True
        
        # Check for weak indicators (need multiple)
        weak_count = sum(1 for indicator in weak_indicators if indicator in content_lower)
        if weak_count >= 2:
            return True
        
        # Very short chunks that are just structural
        if len(content.strip()) < 150:
            structural_words = ['chapter', 'part', 'section', 'book', 'volume', 'preface', 'foreword', 'introduction']
            if any(word in content_lower for word in structural_words) and len(content.strip().split()) < 20:
                return True
        
        # Mostly numbers/dates/codes (catalog info)
        if re.search(r'^\s*[\d\-\.\s]+$', content) or re.search(r'isbn[\d\-\s]+', content_lower):
            return True
        
        return False
    
    def is_actual_content(self, content):
        """Verify this is actual book content"""
        content_clean = re.sub(r'<[^>]+>', '', content).strip()
        
        # Must have reasonable length
        if len(content_clean) < 100:
            return False
        
        # Check for narrative/content indicators
        content_indicators = [
            # Fiction indicators
            'said', 'asked', 'replied', 'thought', 'looked', 'walked', 'felt',
            'character', 'protagonist', 'story', 'narrative', 'dialogue',
            # Non-fiction indicators  
            'research', 'study', 'analysis', 'theory', 'evidence', 'argument',
            'according', 'however', 'therefore', 'furthermore', 'moreover',
            # General content indicators
            'because', 'although', 'while', 'when', 'where', 'what', 'how', 'why'
        ]
        
        indicator_count = sum(1 for indicator in content_indicators if indicator in content.lower())
        
        # Should have some content indicators
        return indicator_count >= 2
    
    def get_all_books_to_process(self):
        """Get ALL books in the library for comprehensive reclassification"""
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        
        try:
            with conn.cursor() as cur:
                # Get all books not yet processed
                if self.state["processed_books"]:
                    processed_ids = tuple(self.state["processed_books"])
                    if len(processed_ids) == 1:
                        processed_condition = f"AND b.book_id != {processed_ids[0]}"
                    else:
                        processed_condition = f"AND b.book_id NOT IN {processed_ids}"
                else:
                    processed_condition = ""
                
                cur.execute(f"""
                    SELECT b.book_id, b.title, b.author, b.genre
                    FROM books b
                    WHERE EXISTS (
                        SELECT 1 FROM chunks c 
                        WHERE c.book_id = b.book_id 
                        AND c.content IS NOT NULL 
                        AND LENGTH(c.content) > 100
                    )
                    {processed_condition}
                    ORDER BY b.book_id
                """)
                
                return cur.fetchall()
        finally:
            conn.close()
    
    def get_optimized_content_sample(self, book_id):
        """Get optimized content sample avoiding front matter completely"""
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        
        try:
            with conn.cursor() as cur:
                # Get all chunks ordered by position
                cur.execute("""
                    SELECT content, chunk_id
                    FROM chunks
                    WHERE book_id = %s
                    AND content IS NOT NULL
                    AND LENGTH(content) > 50
                    ORDER BY chunk_id
                """, (book_id,))
                
                all_chunks = cur.fetchall()
                
                # Filter out front matter
                content_chunks = []
                front_matter_count = 0
                
                for chunk in all_chunks:
                    if self.is_front_matter(chunk['content']):
                        front_matter_count += 1
                    elif self.is_actual_content(chunk['content']):
                        content_chunks.append(chunk)
                
                self.state["front_matter_filtered_count"] += front_matter_count
                
                # Ensure we have actual content
                if not content_chunks:
                    # Fallback: take chunks from middle/end, avoiding first few
                    fallback_start = max(len(all_chunks) // 4, 3)
                    content_chunks = all_chunks[fallback_start:fallback_start + 5]
                
                # Select diverse content chunks strategically
                if len(content_chunks) >= 4:
                    # Early, early-middle, late-middle, late content
                    selected = [
                        content_chunks[0],                                          # Early content
                        content_chunks[len(content_chunks) // 3],                  # Early-middle
                        content_chunks[len(content_chunks) * 2 // 3],              # Late-middle
                        content_chunks[-1]                                         # Late content
                    ]
                elif len(content_chunks) >= 2:
                    # Beginning and end
                    selected = [content_chunks[0], content_chunks[-1]]
                else:
                    selected = content_chunks
                
                # Create optimized sample
                samples = []
                for chunk in selected:
                    # Clean and extract meaningful content
                    clean_content = re.sub(r'<[^>]+>', '', chunk['content'])
                    clean_content = re.sub(r'\s+', ' ', clean_content).strip()
                    
                    # Take a substantial sample
                    if len(clean_content) > 250:
                        sample = clean_content[:250]
                    else:
                        sample = clean_content
                    
                    samples.append(sample)
                
                return " ... ".join(samples)[:800]  # Generous content sample
                
        finally:
            conn.close()
    
    
    def analyze_book_structure_intelligence(self, book_id):
        """Advanced structure analysis for enhanced classification"""
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        
        try:
            with conn.cursor() as cur:
                # Get first 6 chunks for structure analysis (front matter + early content)
                cur.execute("""
                    SELECT content, chunk_id
                    FROM chunks
                    WHERE book_id = %s
                    AND content IS NOT NULL
                    ORDER BY chunk_id
                    LIMIT 6
                """, (book_id,))
                
                chunks = cur.fetchall()
                
                structure_intelligence = {
                    "academic_score": 0.0,
                    "fiction_score": 0.0,
                    "genre_hints": [],
                    "confidence_boost": 0.0
                }
                
                for chunk in chunks:
                    content_lower = chunk['content'].lower()
                    
                    # Academic indicators (increase confidence for non-fiction)
                    academic_indicators = [
                        'bibliography', 'references', 'index', 'table of contents', 
                        'research', 'study', 'analysis', 'methodology', 'hypothesis',
                        'citations', 'notes', 'appendix', 'works cited'
                    ]
                    
                    academic_count = sum(1 for indicator in academic_indicators if indicator in content_lower)
                    structure_intelligence["academic_score"] += academic_count * 0.1
                    
                    # Fiction indicators (increase confidence for fiction)
                    fiction_indicators = [
                        'chapter', 'character', 'dialogue', 'protagonist', 'plot',
                        'story', 'narrative', 'novel', 'fiction', 'characters'
                    ]
                    
                    fiction_count = sum(1 for indicator in fiction_indicators if indicator in content_lower)
                    structure_intelligence["fiction_score"] += fiction_count * 0.05
                    
                    # Specific genre hints
                    if any(word in content_lower for word in ['biography', 'memoir', 'life story', 'autobiography']):
                        structure_intelligence["genre_hints"].append("Biography & Memoir")
                    
                    if any(word in content_lower for word in ['history', 'historical', 'century', 'timeline']):
                        structure_intelligence["genre_hints"].append("History")
                    
                    if any(word in content_lower for word in ['psychology', 'psychological', 'therapy', 'mental']):
                        structure_intelligence["genre_hints"].append("Psychology")
                    
                    if any(word in content_lower for word in ['philosophy', 'philosophical', 'theory', 'ethics']):
                        structure_intelligence["genre_hints"].append("Philosophy")
                    
                    if any(word in content_lower for word in ['business', 'economics', 'market', 'finance']):
                        structure_intelligence["genre_hints"].append("Business & Economics")
                    
                    if any(word in content_lower for word in ['science fiction', 'sci-fi', 'future', 'technology', 'space']):
                        structure_intelligence["genre_hints"].append("Science Fiction")
                    
                    if any(word in content_lower for word in ['fantasy', 'magic', 'magical', 'dragon', 'wizard']):
                        structure_intelligence["genre_hints"].append("Fantasy")
                
                # Calculate confidence boost based on structural clarity
                if structure_intelligence["academic_score"] > 0.3:
                    structure_intelligence["confidence_boost"] = 0.2
                elif structure_intelligence["fiction_score"] > 0.3:
                    structure_intelligence["confidence_boost"] = 0.15
                
                return structure_intelligence
                
        finally:
            conn.close()


    def classify_with_structure_intelligence(self, book_data, content, structure_intel):
        """Classification enhanced with structural intelligence"""
        
        # Build structure context
        structure_context = ""
        if structure_intel["academic_score"] > 0.2:
            structure_context = "STRUCTURE: Academic/research book with bibliography, references, or scholarly apparatus. "
        elif structure_intel["fiction_score"] > 0.2:
            structure_context = "STRUCTURE: Narrative fiction with chapters and story elements. "
        
        if structure_intel["genre_hints"]:
            most_common_hint = max(set(structure_intel["genre_hints"]), key=structure_intel["genre_hints"].count)
            structure_context += f"STRONG STRUCTURAL INDICATOR: {most_common_hint}. "
        
        prompt = f"""You are an expert book classifier using both content and structural analysis.

BOOK: "{book_data['title']}" by {book_data['author']}
CURRENT: {book_data['genre']}

{structure_context}

CONTENT SAMPLE:
{content}

AVAILABLE GENRES:
Romance, Literary Fiction, Science Fiction, Fantasy, Mystery & Thriller, Historical Fiction, Contemporary Fiction, Self-Help, Biography & Memoir, Psychology, Philosophy, Business & Economics, History, Science & Nature, Programming & Technology, Academic & Research, Religion & Spirituality, Political Science

ENHANCED CLASSIFICATION RULES:
1. Use BOTH content and structural indicators for maximum accuracy
2. Academic structure (bibliography, index, references) strongly suggests non-fiction
3. Chapter-based narrative structure suggests fiction genres
4. Respect structural hints but prioritize actual content
5. Choose the most specific and accurate genre

Based on both content analysis and structural intelligence, what is the correct genre?

GENRE:"""

        try:
            start_time = time.time()
            
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.05, "top_p": 0.9}
                },
                timeout=25
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                classification = result['response'].strip()
                
                # Enhanced genre extraction with structure confidence
                classification_lines = [line.strip() for line in classification.split('\n') if line.strip()]
                
                for line in classification_lines:
                    for genre in self.valid_genres:
                        if genre.lower() == line.lower() or genre.lower() in line.lower():
                            # Apply structure confidence boost
                            confidence = 1.0 + structure_intel["confidence_boost"]
                            return genre, duration, confidence
                
                # Fallback
                if classification_lines:
                    return classification_lines[0], duration, 1.0
                
                return classification, duration, 1.0
            else:
                return None, duration, 0.0
                
        except Exception as e:
            self.logger.error(f"Enhanced classification error: {e}")
            return None, 25, 0.0

    def classify_with_llama_optimized(self, book_data, content):
        """Optimized classification with enhanced prompt"""
        
        prompt = f"""You are an expert book classifier. Analyze this book's actual content to determine the correct genre.

BOOK: "{book_data['title']}" by {book_data['author']}
CURRENT CLASSIFICATION: {book_data['genre']}

ACTUAL BOOK CONTENT:
{content}

AVAILABLE GENRES:
Romance, Literary Fiction, Science Fiction, Fantasy, Mystery & Thriller, Historical Fiction, Contemporary Fiction, Self-Help, Biography & Memoir, Psychology, Philosophy, Business & Economics, History, Science & Nature, Programming & Technology, Academic & Research, Religion & Spirituality, Political Science

CLASSIFICATION RULES:
1. ANALYZE THE ACTUAL CONTENT, not just the title
2. Fiction = characters, dialogue, narrative plot, storytelling
3. Non-fiction = facts, analysis, research, instruction, theory
4. Choose the MOST SPECIFIC and ACCURATE genre
5. If unsure between two genres, pick the more specific one

Based on the actual content above, what is the correct genre?

GENRE:"""

        try:
            start_time = time.time()
            
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.05, "top_p": 0.9}
                },
                timeout=25  # Fast model
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                classification = result['response'].strip()
                
                # Enhanced genre extraction
                classification_lines = [line.strip() for line in classification.split('\n') if line.strip()]
                
                # Try to find exact genre match
                for line in classification_lines:
                    for genre in self.valid_genres:
                        if genre.lower() == line.lower() or genre.lower() in line.lower():
                            return genre, duration
                
                # Fallback: check for partial matches in any line
                for line in classification_lines:
                    for genre in self.valid_genres:
                        if genre.lower().split()[0] in line.lower():  # Match first word
                            return genre, duration
                
                # Return first non-empty line for manual review
                if classification_lines:
                    return classification_lines[0], duration
                
                return classification, duration
            else:
                return None, duration
                
        except Exception as e:
            self.logger.error(f"Classification error: {e}")
            return None, 25
    
    def update_book_genre(self, book_id, new_genre):
        """Update book genre in database"""
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE books SET genre = %s WHERE book_id = %s", (new_genre, book_id))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Database error: {e}")
            return False
        finally:
            conn.close()
    
    
    def process_book(self, book):
        """Process a single book with structure intelligence"""
        try:
            self.logger.info(f"📚 Processing: \"{book['title'][:50]}...\" by {book['author']}")
            
            # Get structure intelligence
            structure_intel = self.analyze_book_structure_intelligence(book['book_id'])
            
            # Get optimized content
            content = self.get_optimized_content_sample(book['book_id'])
            if not content or len(content) < 80:
                self.logger.warning(f"❌ Insufficient content for {book['title']}")
                return "insufficient_content"
            
            # Classify with structure intelligence
            new_genre, duration, confidence = self.classify_with_structure_intelligence(book, content, structure_intel)
            if not new_genre:
                self.logger.warning(f"❌ Classification failed for {book['title']}")
                return "classification_failed"
            
            confidence_indicator = "🔥" if confidence > 1.1 else "🎯"
            self.logger.info(f"{confidence_indicator} Classification: {new_genre} ({duration:.1f}s, confidence: {confidence:.2f})")
            
            # Log structure insights
            if structure_intel["genre_hints"]:
                hints = list(set(structure_intel["genre_hints"]))[:2]
                self.logger.info(f"📋 Structure hints: {', '.join(hints)}")
            
            # Update if different
            if new_genre != book['genre']:
                if new_genre in self.valid_genres:
                    if self.update_book_genre(book['book_id'], new_genre):
                        self.logger.info(f"✅ UPDATED: {book['genre']} → {new_genre}")
                        
                        # Track changes
                        old_genre = book['genre']
                        if old_genre not in self.state['genre_changes']:
                            self.state['genre_changes'][old_genre] = {}
                        if new_genre not in self.state['genre_changes'][old_genre]:
                            self.state['genre_changes'][old_genre][new_genre] = 0
                        self.state['genre_changes'][old_genre][new_genre] += 1
                        
                        return "reclassified"
                    else:
                        return "update_failed"
                else:
                    self.logger.warning(f"⚠️  Invalid genre returned: {new_genre}")
                    return "invalid_genre"
            else:
                self.logger.info(f"✅ CONFIRMED: {new_genre}")
                return "confirmed"
                
        except Exception as e:
            self.logger.error(f"💥 Error processing {book['title']}: {e}")
            return "error"

    def run(self):
        """Main daemon loop with ultimate optimization"""
        self.logger.info("🚀 ULTIMATE LIBRARY RECLASSIFICATION DAEMON STARTING")
        self.logger.info("📚 Reprocessing ALL books with llama3.2:3b + optimized chunk selection")
        self.logger.info("🔥 Skipping front matter, focusing on actual content")
        self.logger.info("=" * 90)
        
        # Initialize
        if not self.state["start_time"]:
            self.state["start_time"] = datetime.now().isoformat()
        
        self.state["status"] = "running"
        
        # Get all books
        books_to_process = self.get_all_books_to_process()
        self.state["total_books"] = len(books_to_process) + len(self.state["processed_books"])
        
        self.logger.info(f"📊 Found {len(books_to_process)} books to process")
        self.logger.info(f"📈 Progress: {len(self.state['processed_books'])}/{self.state['total_books']} completed")
        
        if not books_to_process:
            self.logger.info("🎉 ALL BOOKS PROCESSED - ULTIMATE DAEMON COMPLETE!")
            self.state["status"] = "completed"
            self.save_state()
            return
        
        # Estimate completion time
        estimated_seconds = len(books_to_process) * 1.0  # ~1s per book with optimization
        estimated_minutes = estimated_seconds / 60
        self.logger.info(f"⏱️  Estimated completion: {estimated_minutes:.1f} minutes")
        self.logger.info(f"🎯 Expected accuracy: 85-90% with optimized chunk selection")
        
        # Process books in larger batches for efficiency
        batch_size = 25
        for i in range(0, len(books_to_process), batch_size):
            batch = books_to_process[i:i + batch_size]
            self.state["current_batch"] += 1
            
            batch_start_time = time.time()
            self.logger.info(f"📦 Processing batch {self.state['current_batch']} ({len(batch)} books)")
            
            for book in batch:
                result = self.process_book(book)
                
                # Update counters
                self.state["processed_books"].append(book['book_id'])
                self.state["processed_count"] += 1
                
                if result == "reclassified":
                    self.state["reclassified_count"] += 1
                elif result == "confirmed":
                    self.state["confirmed_count"] += 1
                elif result in ["error", "classification_failed", "update_failed", "invalid_genre"]:
                    self.state["failed_count"] += 1
                    self.state["errors"].append({
                        "book_id": book['book_id'],
                        "title": book['title'],
                        "error": result,
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Progress update every 10 books
                if self.state["processed_count"] % 10 == 0:
                    progress_pct = (self.state["processed_count"] / self.state["total_books"]) * 100
                    accuracy_pct = ((self.state["reclassified_count"] + self.state["confirmed_count"]) / 
                                  self.state["processed_count"]) * 100
                    self.logger.info(f"📊 Progress: {self.state['processed_count']}/{self.state['total_books']} ({progress_pct:.1f}%) | Accuracy: {accuracy_pct:.1f}%")
                
                # Save state every 15 books
                if self.state["processed_count"] % 15 == 0:
                    self.save_state()
                
                time.sleep(0.4)  # Optimized rate limiting
            
            # Batch complete
            batch_duration = time.time() - batch_start_time
            books_per_second = len(batch) / batch_duration
            self.logger.info(f"✅ Batch {self.state['current_batch']} complete ({books_per_second:.1f} books/sec)")
            self.logger.info(f"🚫 Front matter filtered: {self.state['front_matter_filtered_count']} chunks")
            self.save_state()
        
        # Final completion
        total_success = self.state['reclassified_count'] + self.state['confirmed_count']
        final_accuracy = (total_success / self.state['processed_count']) * 100
        
        self.logger.info("🎉 ULTIMATE LIBRARY RECLASSIFICATION COMPLETE!")
        self.logger.info("=" * 60)
        self.logger.info(f"📊 FINAL STATISTICS:")
        self.logger.info(f"   📚 Total processed: {self.state['processed_count']}")
        self.logger.info(f"   ✅ Reclassified: {self.state['reclassified_count']}")
        self.logger.info(f"   ✅ Confirmed accurate: {self.state['confirmed_count']}")
        self.logger.info(f"   ❌ Failed: {self.state['failed_count']}")
        self.logger.info(f"   🚫 Front matter filtered: {self.state['front_matter_filtered_count']} chunks")
        self.logger.info(f"   🎯 Final accuracy: {final_accuracy:.1f}%")
        
        improvement_rate = (self.state['reclassified_count'] / self.state['processed_count']) * 100
        self.logger.info(f"   📈 Improvement rate: {improvement_rate:.1f}%")
        
        self.state["status"] = "completed"
        self.state["completion_time"] = datetime.now().isoformat()
        self.state["final_accuracy"] = final_accuracy
        self.save_state()

def main():
    """Start the ultimate daemon"""
    daemon = UltimateLibraryReclassificationDaemon()
    
    try:
        daemon.run()
    except KeyboardInterrupt:
        daemon.logger.info("🛑 Daemon stopped by user")
    except Exception as e:
        daemon.logger.error(f"💥 Daemon crashed: {e}")
        daemon.state["status"] = "crashed"
        daemon.save_state()
    finally:
        daemon.cleanup()

if __name__ == '__main__':
    main()