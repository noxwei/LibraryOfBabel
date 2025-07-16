#!/usr/bin/env python3
"""
🤖 AUTONOMOUS GENRE CLASSIFICATION DAEMON
==========================================

Persistent daemon for classifying 1,210 missing book genres.
Designed to run independently with:
- Resume capability across restarts
- Progress tracking and logging
- Graceful start/stop controls
- Error recovery and retries

Usage:
    python3 daemons/genre_classification_daemon.py start
    python3 daemons/genre_classification_daemon.py stop
    python3 daemons/genre_classification_daemon.py status
    python3 daemons/genre_classification_daemon.py resume
"""

import os
import sys
import json
import time
import signal
import atexit
import logging
import requests
import psycopg2
import psycopg2.extras
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import threading

# Add paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))
sys.path.append(str(project_root))

from config.api_config import get_database_config

class GenreClassificationDaemon:
    """
    🤖 Autonomous Genre Classification Daemon
    
    Features:
    - Persistent state management
    - Resume from last position
    - Progress tracking
    - Error recovery
    - Graceful shutdown
    """
    
    def __init__(self):
        self.daemon_dir = project_root / "daemons"
        self.state_file = self.daemon_dir / "genre_daemon_state.json"
        self.log_file = self.daemon_dir / "genre_daemon.log"
        self.pid_file = self.daemon_dir / "genre_daemon.pid"
        
        # Ensure daemon directory exists
        self.daemon_dir.mkdir(exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("GenreDaemon")
        
        # Configuration
        self.ollama_base_url = "http://localhost:11434"
        self.db_config = get_database_config()
        self.running = False
        self.paused = False
        
        # Processing parameters - OPTIMIZED FOR OVERNIGHT ACCURACY
        self.batch_size = 1  # Process one book at a time for content analysis
        self.delay_between_books = 2  # Longer delay for thorough processing
        self.retry_attempts = 3
        self.retry_delay = 10  # Seconds between retries
        
        # Quality assurance with Lexi verification
        self.verification_interval = 50  # Verify every 50 books with Lexi
        self.lexi_verifications = []  # Track verification results
        
        # Standard genre taxonomy
        # EXPANDED GENRE TAXONOMY - BREAKING DOWN LITERARY FICTION
        self.standard_genres = [
            # FICTION GENRES (much more specific to avoid Literary Fiction catch-all)
            "Mystery & Thriller", "Romance", "Science Fiction", "Fantasy", 
            "Historical Fiction", "Contemporary Fiction", "Dystopian Fiction",
            "Magical Realism", "Coming of Age", "Women's Fiction", "Literary Fiction",
            "Adventure", "Horror", "Young Adult", "Graphic Novel", "Memoir Fiction",
            
            # NON-FICTION GENRES (comprehensive)  
            "Ethics & Moral Philosophy", "Existentialism", "Political Philosophy", 
            "Philosophy of Mind", "Metaphysics", "Epistemology", "Continental Philosophy",
            "Analytic Philosophy", "Ancient Philosophy", "Eastern Philosophy", "Philosophy",
            "History", "Biography & Memoir", "Science & Technology",
            "Psychology", "Political Science", "Business & Economics",
            "Self-Help", "Health & Wellness", "Religion & Spirituality",
            "Arts & Culture", "Academic", "Reference", "Travel", "True Crime",
            "Essays & Criticism", "Cultural Studies", "Social Commentary"
        ]
        
        # Smart keyword patterns for instant classification
        self.keyword_patterns = {
            "Mystery & Thriller": [
                r"\bmystery\b", r"\bthriller\b", r"\bdetective\b", r"\bcrime\b", 
                r"\bmurder\b", r"\binvestigation\b", r"\bsuspense\b", r"\bnoir\b",
                r"mystery book \d+", r"detective series", r"\bwhodunit\b"
            ],
            "Romance": [
                r"\bromance\b", r"\blove story\b", r"\bheart\b", r"\bpassion\b",
                r"\bwedding\b", r"\bmarriage\b", r"love affair", r"romantic"
            ],
            "Science Fiction": [
                r"\bsci-?fi\b", r"\bspace\b", r"\bfuture\b", r"\balien\b", 
                r"\brobot\b", r"\btechnology\b", r"\bgalaxy\b", r"\bplanet\b",
                r"science fiction", r"\bcyber\b"
            ],
            "Dystopian Fiction": [
                r"\bdystopian\b", r"\bdystopia\b", r"\bpost-apocalyptic\b", r"\btotalitarian\b",
                r"\bauthoritarian\b", r"\bsurvival\b.*\bworld\b"
            ],
            "Fantasy": [
                r"\bfantasy\b", r"\bmagic\b", r"\bdragon\b", r"\bwizard\b", r"\bwitch\b", r"\bwitches\b",
                r"\bkingdom\b", r"\bquest\b", r"\bmythical\b", r"\bepic\b", r"\bdiscworld\b",
                r"\bsorcer\b", r"\bspell\b", r"\benchant\b", r"\bmage\b", r"\bpaladin\b",
                r"\belves\b", r"\bdwarves\b", r"\borcs\b", r"\bgoblins\b", r"\bfae\b",
                r"\bspells\b", r"\bcloaks\b", r"\btower\b.*\bchronicles\b", r"\briyria\b"
            ],
            "Historical Fiction": [
                r"historical fiction", r"\bvictorian\b", r"\bmedieval\b", r"\bworld war\b",
                r"\bcivil war\b", r"\bregency\b", r"\bperiod drama\b"
            ],
            "Contemporary Fiction": [
                r"contemporary fiction", r"\bmodern life\b", r"\burban\b.*\bstory\b",
                r"\bfamily saga\b", r"\brelationships\b"
            ],
            "Coming of Age": [
                r"coming of age", r"\bteen\b.*\bstory\b", r"\badolescent\b", 
                r"\byoung adult\b", r"\bgrowing up\b"
            ],
            "Women's Fiction": [
                r"women's fiction", r"\bmotherhood\b", r"\bsisterhood\b",
                r"\bfeminist\b.*\bnovel\b", r"\bwomen's lives\b"
            ],
            "Magical Realism": [
                r"magical realism", r"\bmagical elements\b", r"\bsurreal\b.*\bfiction\b"
            ],
            "Business & Economics": [
                r"\bbusiness\b", r"\beconomics\b", r"\bfinance\b", r"\bmanagement\b",
                r"\bentrepreneur\b", r"\bstartup\b", r"\bmarket\b", r"\binvest\b",
                r"deep work", r"productivity", r"\bstrategy\b"
            ],
            "Ethics & Moral Philosophy": [
                r"\bethics\b", r"\bmoral philosophy\b", r"\bmorality\b", r"\bmoral\b.*\btheory\b",
                r"\bvirtue ethics\b", r"\butilitarianism\b", r"\bdeontology\b", r"\bjustice\b"
            ],
            "Existentialism": [
                r"\bexistentialism\b", r"\bexistentialist\b", r"\bsartre\b", r"\bcamus\b",
                r"\bkierkegaard\b", r"\bheidegger\b", r"\bangst\b", r"\bauthenticity\b",
                r"\babsurd\b", r"\bexistence\b.*\bessence\b"
            ],
            "Political Philosophy": [
                r"political philosophy", r"\bpolitical theory\b", r"\bstate\b.*\bnature\b",
                r"\bsocial contract\b", r"\bliberalism\b", r"\bconservatism\b", r"\banarchy\b"
            ],
            "Philosophy of Mind": [
                r"philosophy of mind", r"\bconsciousness\b", r"\bmind-body\b", r"\bqualia\b",
                r"\bfree will\b", r"\bdeterminism\b", r"\bdualism\b", r"\bmaterialism\b"
            ],
            "Metaphysics": [
                r"\bmetaphysics\b", r"\bontology\b", r"\bbeing\b.*\btime\b", r"\breality\b",
                r"\bsubstance\b", r"\bcausation\b", r"\bnecessity\b"
            ],
            "Continental Philosophy": [
                r"continental philosophy", r"\bphenomenology\b", r"\bhermeneutics\b",
                r"\bpostmodernism\b", r"\bderrida\b", r"\bfoucault\b", r"\bdeleuze\b"
            ],
            "Ancient Philosophy": [
                r"ancient philosophy", r"\bplato\b", r"\baristotle\b", r"\bsocrates\b",
                r"\bstoicism\b", r"\bepicureanism\b", r"\baristotelianism\b"
            ],
            "Eastern Philosophy": [
                r"eastern philosophy", r"\bbuddhism\b", r"\btaoism\b", r"\bconfucianism\b",
                r"\bzen\b", r"\bhinduism\b", r"\bvedanta\b"
            ],
            "Philosophy": [
                r"\bphilosophy\b", r"\bphilosophical\b", r"\bphilosopher\b"
            ],
            "History": [
                r"\bhistory\b", r"\bhistorical\b", r"\bwar\b", r"\bancient\b", r"\bcentury\b"
            ],
            "Biography & Memoir": [
                r"\bbiography\b", r"\bmemoir\b", r"\bautobiography\b", r"\blife of\b"
            ],
            "Self-Help": [
                r"self-help", r"personal development", r"self improvement",
                r"habits", r"mindset", r"success", r"motivation"
            ],
            "Psychology": [
                r"\bpsychology\b", r"\bneuroscience\b", r"\bcognitive\b", 
                r"\bbehavioral\b", r"\bmind\b", r"\bbrain\b"
            ],
            "Cultural Studies": [
                r"cultural studies", r"\brace\b.*\bstudies\b", r"\bgender studies\b",
                r"\bidentity\b.*\bpolitics\b", r"\bsocial justice\b"
            ],
            "Social Commentary": [
                r"social commentary", r"\bsocial criticism\b", r"\bpolitical commentary\b",
                r"\bcultural criticism\b", r"\bsocial issues\b"
            ]
        }
        
        # Daemon state
        self.state = self.load_state()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        atexit.register(self.cleanup)

    def load_state(self) -> Dict:
        """Load daemon state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.logger.info(f"Loaded state: {state['books_processed']} books processed")
                    return state
            except Exception as e:
                self.logger.error(f"Failed to load state: {e}")
        
        # Default state
        return {
            "books_processed": 0,
            "books_successful": 0,
            "books_failed": 0,
            "last_book_id": None,
            "session_start": datetime.now().isoformat(),
            "total_runtime": 0,
            "genres_assigned": {},
            "failed_book_ids": [],
            "daemon_version": "1.0"
        }

    def save_state(self):
        """Save current daemon state"""
        try:
            self.state["last_updated"] = datetime.now().isoformat()
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")

    def write_pid(self):
        """Write daemon PID to file"""
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
        except Exception as e:
            self.logger.error(f"Failed to write PID: {e}")

    def read_pid(self) -> Optional[int]:
        """Read daemon PID from file"""
        try:
            if self.pid_file.exists():
                with open(self.pid_file, 'r') as f:
                    return int(f.read().strip())
        except Exception as e:
            self.logger.error(f"Failed to read PID: {e}")
        return None

    def is_running(self) -> bool:
        """Check if daemon is already running"""
        pid = self.read_pid()
        if pid:
            try:
                os.kill(pid, 0)  # Check if process exists
                return True
            except OSError:
                # Process doesn't exist, remove stale PID file
                self.pid_file.unlink(missing_ok=True)
        return False

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    def cleanup(self):
        """Cleanup on daemon shutdown"""
        self.save_state()
        self.pid_file.unlink(missing_ok=True)
        self.logger.info("Daemon shutdown complete")

    def get_db_connection(self):
        """Get database connection with retry logic"""
        for attempt in range(3):
            try:
                return psycopg2.connect(**self.db_config)
            except psycopg2.Error as e:
                self.logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(5)
        return None

    def query_magistral(self, prompt: str) -> Optional[str]:
        """Query Magistral with error handling"""
        for attempt in range(self.retry_attempts):
            try:
                response = requests.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": "magistral",
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "top_p": 0.9,
                            "max_tokens": 15,  # Shorter response = faster
                            "stop": ["\\n", ":"]  # Stop early
                        }
                    },
                    timeout=45  # 45 seconds (optimized prompt)
                )
                
                if response.status_code == 200:
                    return response.json().get('response', '').strip()
                else:
                    self.logger.warning(f"Magistral API error: {response.status_code}, attempt {attempt + 1}")
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"Magistral timeout, attempt {attempt + 1}")
            except Exception as e:
                self.logger.warning(f"Magistral error: {e}, attempt {attempt + 1}")
            
            if attempt < self.retry_attempts - 1:
                time.sleep(self.retry_delay)
        
        return None

    def quick_keyword_classify(self, title: str, description: str) -> Optional[str]:
        """Ultra-fast keyword-based classification"""
        
        text = f"{title} {description}".lower()
        
        # Check each genre's keywords
        for genre, patterns in self.keyword_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return genre
        
        return None

    def smart_title_analysis(self, title: str) -> Optional[str]:
        """Analyze title for obvious genre indicators"""
        
        title_lower = title.lower()
        
        # Fantasy indicators (PRIORITY: catch obvious fantasy first)
        if re.search(r"\bdiscworld\b", title_lower):
            return "Fantasy"
        if re.search(r"\bwitch\b|\bwitches\b|\bwizard\b|\bmagic\b", title_lower):
            return "Fantasy"
        if re.search(r"\bpaladin\b|\bmage\b|\bsorcer\b", title_lower):
            return "Fantasy"
        if re.search(r"\bdragon\b|\belves\b|\bdwarves\b", title_lower):
            return "Fantasy"
        
        # Mystery/Thriller indicators
        if re.search(r"mystery book \d+", title_lower):
            return "Mystery & Thriller"
        if re.search(r"\bjack reacher\b", title_lower):
            return "Mystery & Thriller"
        
        # Romance indicators  
        if re.search(r"romance novel|love story", title_lower):
            return "Romance"
        
        # Business indicators
        if "summarized for busy people" in title_lower:
            return "Business & Economics"
        
        # Self-help indicators
        if re.search(r"\bguide to\b|\bhow to\b|\bsecrets of\b", title_lower):
            return "Self-Help"
        
        # History indicators
        if re.search(r"\bhistory of\b|\bbiography of\b", title_lower):
            return "History"
        
        return None

    def get_content_sample(self, book_id: int) -> str:
        """Get a small content sample from the book chunks for better classification"""
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return ""
                
                with conn.cursor() as cur:
                    # Get first few chunks (up to 500 chars total)
                    cur.execute("""
                        SELECT chunk_text 
                        FROM chunk_embeddings 
                        WHERE book_id = %s 
                        ORDER BY chunk_index 
                        LIMIT 3
                    """, (book_id,))
                    
                    chunks = cur.fetchall()
                    if chunks:
                        # Combine first few chunks, truncate to reasonable size
                        content = ' '.join([chunk[0] for chunk in chunks])
                        return content[:500]  # 500 chars ≈ 100 tokens
                    return ""
                    
        except Exception as e:
            self.logger.warning(f"Failed to get content sample for book {book_id}: {e}")
            return ""

    def lightweight_magistral_classify(self, title: str, author: str, description: str) -> Tuple[Optional[str], float]:
        """Lightweight Magistral classification using minimal text"""
        
        # Trim description to first 120 chars for speed
        short_desc = (description or "")[:120] + "..." if len(description or "") > 120 else (description or "")
        
        # Ultra-concise prompt - targeting 60 tokens total
        prompt = f"""Classify this book into ONE genre:

Book: "{title}" by {author}
{short_desc}

Genres: Mystery & Thriller, Romance, Science Fiction, Fantasy, Literary Fiction, Historical Fiction, Philosophy, History, Biography & Memoir, Psychology, Political Science, Business & Economics, Self-Help, Academic, Arts & Culture

Genre:"""

        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": "magistral",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "max_tokens": 15,  # Very short response
                        "stop": ["\n", ":"]
                    }
                },
                timeout=45  # 45 seconds max
            )
            
            if response.status_code == 200:
                result = response.json().get('response', '').strip()
                
                # Handle Magistral's thinking mode
                if result and result.startswith('<think>'):
                    return None, 0.0
                
                # Find exact match
                for genre in self.standard_genres:
                    if genre.lower() in result.lower():
                        return genre, 0.8
                
                return None, 0.0
                
        except Exception:
            return None, 0.0

    def enhanced_magistral_classify(self, book_id: int, title: str, author: str, description: str) -> Tuple[Optional[str], float]:
        """Enhanced classification using content sampling for better accuracy"""
        
        # Get content sample for better context
        content_sample = self.get_content_sample(book_id)
        
        # Create enhanced prompt with content sample
        prompt = f"""Classify this book into ONE specific genre based on all available information:

Title: "{title}"
Author: {author}
Description: {description[:200]}...
Content Sample: {content_sample}

Available Genres:
- Mystery & Thriller (detective stories, crime, suspense)
- Romance (love stories, romantic relationships)  
- Science Fiction (futuristic, space, technology, aliens)
- Fantasy (magic, wizards, mythical creatures, alternate worlds)
- Literary Fiction (character-driven, realistic contemporary/historical)
- Historical Fiction (set in past eras)
- Philosophy (philosophical texts, ethics, meaning)
- History (historical events, biographies of historical figures)
- Biography & Memoir (life stories, autobiographies)
- Psychology (mind, behavior, mental health)
- Political Science (politics, government, political theory)
- Business & Economics (business, finance, economics)
- Self-Help (personal development, how-to guides)
- Academic (scholarly works, textbooks)
- Arts & Culture (art, music, cultural criticism)

Genre:"""

        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": "magistral",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "max_tokens": 20,
                        "stop": ["\n", ":"]
                    }
                },
                timeout=120  # Longer timeout for content analysis
            )
            
            if response.status_code == 200:
                result = response.json().get('response', '').strip()
                
                # Handle Magistral's thinking mode
                if result and result.startswith('<think>'):
                    return None, 0.0
                
                # Clean and match result
                clean_result = result.strip('.,!?:;"\'()[]{}').strip()
                
                # Find exact match
                for genre in self.standard_genres:
                    if genre.lower() in clean_result.lower():
                        return genre, 0.9  # Higher confidence with content
                
                return None, 0.0
                
        except Exception as e:
            self.logger.warning(f"Enhanced classification failed: {e}")
            return None, 0.0

    def lexi_verify_classification(self, book: Dict, assigned_genre: str) -> Dict:
        """Use Lexi (Story Generation AI) to verify genre classification"""
        
        book_id = book['book_id']
        title = book.get('title', '') or ''
        author = book.get('author', '') or ''
        description = book.get('description', '') or ''
        content_sample = self.get_content_sample(book_id)
        
        # Enhanced verification prompt for Lexi
        prompt = f"""🔍 GENRE VERIFICATION TASK

As Lexi, the advanced Story Generation AI, please verify if this genre classification is accurate:

BOOK DETAILS:
Title: "{title}"
Author: {author}
Description: {description[:300]}...
Content Sample: {content_sample}

ASSIGNED GENRE: {assigned_genre}

AVAILABLE GENRES:
Mystery & Thriller, Romance, Science Fiction, Fantasy, Literary Fiction, Historical Fiction, Philosophy, History, Biography & Memoir, Psychology, Political Science, Business & Economics, Self-Help, Academic, Arts & Culture

VERIFICATION ANALYSIS:
1. Is the assigned genre "{assigned_genre}" correct? (YES/NO)
2. If NO, what genre would be more accurate?
3. Confidence level (1-10)?
4. Brief reasoning?

Response format:
CORRECT: [YES/NO]
SUGGESTED: [Genre if different]
CONFIDENCE: [1-10]
REASONING: [Brief explanation]"""

        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": "magistral",  # Using Magistral as Lexi
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "max_tokens": 100,
                        "stop": ["END"]
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json().get('response', '').strip()
                
                verification = {
                    "book_id": book_id,
                    "title": title[:50],
                    "assigned_genre": assigned_genre,
                    "lexi_response": result,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Parse Lexi's response
                if "CORRECT: YES" in result.upper():
                    verification["status"] = "CONFIRMED"
                elif "CORRECT: NO" in result.upper():
                    verification["status"] = "DISPUTED"
                else:
                    verification["status"] = "UNCLEAR"
                
                return verification
                
        except Exception as e:
            self.logger.warning(f"Lexi verification failed for book {book_id}: {e}")
            
        return {
            "book_id": book_id,
            "title": title[:50], 
            "assigned_genre": assigned_genre,
            "status": "VERIFICATION_FAILED",
            "timestamp": datetime.now().isoformat()
        }

    def classify_book_genre(self, book: Dict) -> Tuple[Optional[str], str, float]:
        """Fast book classification with multi-tier approach"""
        
        title = book.get('title', '') or ''
        author = book.get('author', '') or ''
        description = book.get('description', '') or ''
        
        start_time = time.time()
        
        # Tier 1: Smart title analysis (instant)
        genre = self.smart_title_analysis(title)
        if genre:
            processing_time = time.time() - start_time
            return genre, "Smart title analysis", processing_time
        
        # Tier 2: Keyword classification (instant)
        genre = self.quick_keyword_classify(title, description)
        if genre:
            processing_time = time.time() - start_time
            return genre, "Keyword-based", processing_time
        
        # Tier 3: Enhanced content-aware Magistral (15-30 seconds for accuracy)
        book_id = book['book_id']
        genre, confidence = self.enhanced_magistral_classify(book_id, title, author, description)
        processing_time = time.time() - start_time
        
        if genre and confidence > 0.8:
            return genre, "Enhanced content analysis", processing_time
        
        # Tier 4: Enhanced fallback matching based on content
        content_text = f"{title} {description}".lower()
        if "mystery" in content_text or "detective" in content_text or "crime" in content_text:
            return "Mystery & Thriller", "Content fallback", processing_time
        elif "romance" in content_text or "love" in content_text:
            return "Romance", "Content fallback", processing_time
        elif "science" in content_text and "fiction" in content_text:
            return "Science Fiction", "Content fallback", processing_time
        elif "fantasy" in content_text or "magic" in content_text:
            return "Fantasy", "Content fallback", processing_time
        elif "philosophy" in content_text or "philosophical" in content_text:
            return "Philosophy", "Content fallback", processing_time
        elif "history" in content_text or "historical" in content_text:
            return "History", "Content fallback", processing_time
        elif "biography" in content_text or "memoir" in content_text:
            return "Biography & Memoir", "Content fallback", processing_time
        elif "psychology" in content_text or "psychological" in content_text:
            return "Psychology", "Content fallback", processing_time
        elif "business" in content_text or "economics" in content_text:
            return "Business & Economics", "Content fallback", processing_time
        elif "self-help" in content_text or "self help" in content_text:
            return "Self-Help", "Content fallback", processing_time
        
        # Final fallback: Literary Fiction
        return "Literary Fiction", "Default fallback", processing_time


    def update_book_genre(self, book_id: int, genre: str) -> bool:
        """Update book genre in database"""
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return False
                
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE books 
                        SET genre = %s 
                        WHERE book_id = %s
                    """, (genre, book_id))
                    
                    conn.commit()
                    return cur.rowcount > 0
                    
        except Exception as e:
            self.logger.error(f"Failed to update book {book_id}: {e}")
            return False

    def get_next_books(self) -> List[Dict]:
        """Get next batch of books to process"""
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return []
                
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # Get books that need classification, excluding failed ones
                    where_clause = """
                        WHERE (
                            genre IS NULL 
                            OR genre = '' 
                            OR TRIM(genre) = ''
                            OR genre IN ('none', 'book', 'cj5', '公众号：古德猫宁李', 'chenjin5.com沉金书屋')
                        )
                    """
                    
                    # Exclude previously failed books
                    if self.state["failed_book_ids"]:
                        failed_ids = ','.join(map(str, self.state["failed_book_ids"]))
                        where_clause += f" AND book_id NOT IN ({failed_ids})"
                    
                    # Resume from last position
                    if self.state["last_book_id"]:
                        where_clause += f" AND book_id > {self.state['last_book_id']}"
                    
                    cur.execute(f"""
                        SELECT book_id, title, author, description, word_count
                        FROM books 
                        {where_clause}
                        ORDER BY book_id ASC
                        LIMIT %s
                    """, (self.batch_size,))
                    
                    return [dict(row) for row in cur.fetchall()]
                    
        except Exception as e:
            self.logger.error(f"Failed to fetch books: {e}")
            return []

    def process_books(self):
        """Main processing loop"""
        
        self.logger.info("🤖 Starting autonomous genre classification")
        self.logger.info(f"📊 Progress: {self.state['books_processed']} books processed")
        
        consecutive_failures = 0
        max_consecutive_failures = 10
        
        while self.running:
            if self.paused:
                time.sleep(10)
                continue
            
            # Get next books to process
            books = self.get_next_books()
            
            if not books:
                self.logger.info("✅ No more books to process - daemon complete!")
                self.running = False
                break
            
            # Process each book
            for book in books:
                if not self.running:
                    break
                
                book_id = book['book_id']
                title = book.get('title', 'Unknown')[:40]
                
                self.logger.info(f"📚 Processing book {book_id}: {title}")
                
                start_time = time.time()
                
                # Classify genre using multi-tier approach
                genre, method, processing_time = self.classify_book_genre(book)
                
                if genre:
                    # Update database
                    if self.update_book_genre(book_id, genre):
                        self.state["books_successful"] += 1
                        self.state["genres_assigned"][genre] = self.state["genres_assigned"].get(genre, 0) + 1
                        print(f"   ✅ {genre} | {method} | {processing_time:.1f}s")
                        consecutive_failures = 0
                    else:
                        self.logger.error(f"   ❌ Failed to update database")
                        self.state["books_failed"] += 1
                        self.state["failed_book_ids"].append(book_id)
                        consecutive_failures += 1
                else:
                    print(f"   ❌ Classification failed ({processing_time:.1f}s)")
                    self.state["books_failed"] += 1
                    self.state["failed_book_ids"].append(book_id)
                    consecutive_failures += 1
                
                # Update state
                self.state["books_processed"] += 1
                self.state["last_book_id"] = book_id
                self.state["total_runtime"] += processing_time
                
                # Lexi verification every 50 books
                if genre and self.state["books_processed"] % self.verification_interval == 0:
                    print(f"   🔍 Lexi verification checkpoint...")
                    verification = self.lexi_verify_classification(book, genre)
                    self.lexi_verifications.append(verification)
                    
                    status_emoji = {"CONFIRMED": "✅", "DISPUTED": "⚠️", "UNCLEAR": "❓", "VERIFICATION_FAILED": "❌"}
                    print(f"   {status_emoji.get(verification['status'], '❓')} Lexi: {verification['status']}")
                
                # Save state periodically
                if self.state["books_processed"] % 5 == 0:
                    self.save_state()
                    success_rate = (self.state["books_successful"] / self.state["books_processed"] * 100)
                    self.logger.info(f"📊 Progress: {self.state['books_processed']} books, {success_rate:.1f}% success rate")
                
                # Check for too many consecutive failures
                if consecutive_failures >= max_consecutive_failures:
                    self.logger.error(f"Too many consecutive failures ({consecutive_failures}), pausing for 5 minutes...")
                    time.sleep(300)  # 5 minute pause
                    consecutive_failures = 0
                
                # Delay between books (Mac Mini thermal management)
                if self.running:
                    time.sleep(self.delay_between_books)
        
        # Final save
        self.save_state()
        self.logger.info("🏁 Processing session complete")

    def start(self):
        """Start the daemon"""
        if self.is_running():
            print("❌ Daemon is already running")
            return False
        
        print("🚀 Starting Genre Classification Daemon...")
        
        # Write PID file
        self.write_pid()
        
        # Set running flag
        self.running = True
        
        try:
            # Start processing
            self.process_books()
        except Exception as e:
            self.logger.error(f"Daemon crashed: {e}")
            return False
        finally:
            self.cleanup()
        
        return True

    def stop(self):
        """Stop the daemon"""
        pid = self.read_pid()
        if not pid:
            print("❌ Daemon is not running")
            return False
        
        try:
            print(f"🛑 Stopping daemon (PID: {pid})...")
            os.kill(pid, signal.SIGTERM)
            
            # Wait for graceful shutdown
            for _ in range(10):
                time.sleep(1)
                if not self.is_running():
                    print("✅ Daemon stopped gracefully")
                    return True
            
            # Force kill if necessary
            print("⚠️  Forcing daemon shutdown...")
            os.kill(pid, signal.SIGKILL)
            self.pid_file.unlink(missing_ok=True)
            print("✅ Daemon stopped forcefully")
            return True
            
        except ProcessLookupError:
            print("❌ Daemon process not found")
            self.pid_file.unlink(missing_ok=True)
            return False
        except Exception as e:
            print(f"❌ Error stopping daemon: {e}")
            return False

    def status(self):
        """Show daemon status"""
        print("📊 GENRE CLASSIFICATION DAEMON STATUS")
        print("=" * 45)
        
        # Check if running
        if self.is_running():
            pid = self.read_pid()
            print(f"Status: ✅ Running (PID: {pid})")
        else:
            print("Status: ⭕ Stopped")
        
        # Show progress
        state = self.load_state()
        print(f"Books Processed: {state['books_processed']}")
        print(f"Successful: {state['books_successful']}")
        print(f"Failed: {state['books_failed']}")
        
        if state['books_processed'] > 0:
            success_rate = (state['books_successful'] / state['books_processed'] * 100)
            print(f"Success Rate: {success_rate:.1f}%")
            
            avg_time = state['total_runtime'] / state['books_processed']
            print(f"Avg Time/Book: {avg_time:.1f}s")
        
        if state['genres_assigned']:
            print("\n📚 Genres Assigned:")
            for genre, count in sorted(state['genres_assigned'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {genre}: {count} books")
        
        # Show Lexi verification summary
        if hasattr(self, 'lexi_verifications') and self.lexi_verifications:
            print(f"\n🔍 Lexi Verification Summary ({len(self.lexi_verifications)} samples):")
            confirmed = sum(1 for v in self.lexi_verifications if v['status'] == 'CONFIRMED')
            disputed = sum(1 for v in self.lexi_verifications if v['status'] == 'DISPUTED') 
            unclear = sum(1 for v in self.lexi_verifications if v['status'] == 'UNCLEAR')
            failed = sum(1 for v in self.lexi_verifications if v['status'] == 'VERIFICATION_FAILED')
            
            print(f"  ✅ Confirmed: {confirmed}")
            print(f"  ⚠️  Disputed: {disputed}")
            print(f"  ❓ Unclear: {unclear}")
            print(f"  ❌ Failed: {failed}")
            
            if len(self.lexi_verifications) > 0:
                accuracy = (confirmed / len(self.lexi_verifications)) * 100
                print(f"  📊 Lexi Accuracy: {accuracy:.1f}%")
        
        print(f"\nLog File: {self.log_file}")
        print(f"State File: {self.state_file}")

    def pause(self):
        """Pause daemon processing"""
        self.paused = True
        self.logger.info("⏸️  Daemon paused")

    def resume(self):
        """Resume daemon processing"""
        self.paused = False
        self.logger.info("▶️  Daemon resumed")

def main():
    """Main daemon control interface"""
    
    if len(sys.argv) < 2:
        print("Usage: python3 genre_classification_daemon.py {start|stop|status|pause|resume}")
        sys.exit(1)
    
    daemon = GenreClassificationDaemon()
    command = sys.argv[1].lower()
    
    if command == "start":
        daemon.start()
    elif command == "stop":
        daemon.stop()
    elif command == "status":
        daemon.status()
    elif command == "pause":
        daemon.pause()
    elif command == "resume":
        daemon.resume()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: start, stop, status, pause, resume")
        sys.exit(1)

if __name__ == "__main__":
    main()