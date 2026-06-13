#!/usr/bin/env python3
"""
🧠 MULTI-GRANULAR CHUNKING DAEMON - Dr. Sarah Chen's Advanced Text Processing
==============================================================================

Revolutionary multi-granular chunking system that creates a precision spectrum
of text embeddings from micro to macro level for optimal search capabilities.

📏 GRANULARITY SPECTRUM:
- SENTENCE Level: 50-300 chars   - Precise factual queries  
- PARAGRAPH Level: 200-1200 chars - Contextual understanding
- SECTION Level: 800-5000 chars   - Thematic comprehension
- CHAPTER Level: 5000+ chars      - Document-level semantics

🎯 INTELLIGENT PROCESSING:
- Advanced NLP sentence/paragraph boundary detection
- Semantic coherence preservation with overlapping windows
- Quality-based chunk validation and optimization
- PostgreSQL-First architecture with ACID compliance  
- Real-time Grafana metrics and progress tracking
- Docker/Kubernetes environment auto-detection

Features:
- Multi-level text decomposition (4 granularity levels)
- Contextual overlap management for search continuity
- Grafana dashboard integration with live metrics
- Database schema evolution with backward compatibility
- Container-aware configuration and deployment
- Production-ready error recovery and retry logic

Dr. Sarah Chen - Database Systems Librarian & Multi-Modal Architecture Specialist
"""

import os
import sys
import json
import time
import signal
import requests
import psutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import psycopg2
import psycopg2.extras
import logging
from concurrent.futures import ThreadPoolExecutor
import threading

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
from chunk_ordering import ContentLocator, chapter_spine_order_sql

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/progressive_chunking_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MultiGranularStats:
    """Multi-granular chunking performance statistics"""
    session_start: str
    last_updated: str
    runtime_seconds: float
    books_processed: int
    books_completed: int
    books_failed: int
    
    # Original chunks processed
    original_chapters_processed: int
    
    # New granular chunks created
    sentence_chunks_created: int
    paragraph_chunks_created: int
    section_chunks_created: int
    
    # Performance metrics
    average_processing_time: float
    chunks_per_second: float
    granularity_expansion_ratio: float
    
    # Current processing
    current_book: Optional[str]
    current_chunk: Optional[str]
    
    # Quality metrics
    success_rate: float
    processing_errors: int
    
    # System metrics
    daemon_pid: int
    environment: str  # host, docker, kubernetes
    memory_usage_mb: float
    
    def total_granular_chunks(self) -> int:
        return self.sentence_chunks_created + self.paragraph_chunks_created + self.section_chunks_created

@dataclass
class GranularChunk:
    """Granular chunk specification"""
    content: str
    chunk_type: str  # sentence, paragraph, section
    parent_chunk_id: int
    chunk_index: int
    char_length: int
    overlap_start: int
    overlap_end: int
    quality_score: float
    processing_metadata: Dict[str, Any]

class ChunkSpec:
    """Specification for chunk granularity levels"""
    def __init__(self, name: str, min_chars: int, max_chars: int, overlap_chars: int, description: str):
        self.name = name
        self.min_chars = min_chars
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars
        self.description = description

class MultiGranularChunkingDaemon:
    """
    🚀 Dr. Sarah Chen's Multi-Granular Chunking Daemon
    
    Creates precision spectrum of text embeddings by decomposing existing chunks 
    into sentence → paragraph → section → chapter granularities for optimal search.
    """
    
    def __init__(self):
        self.running = False
        self.current_book = None
        self.current_chunk = None
        
        # Auto-detect environment and configure database
        self.environment = self.detect_environment()
        self.db_config = self.get_database_config()
        
        # Multi-granular chunk specifications
        self.chunk_specs = {
            "sentence": ChunkSpec(
                name="sentence",
                min_chars=50,
                max_chars=300,
                overlap_chars=20,
                description="Sentence-level chunks for precise factual queries"
            ),
            "paragraph": ChunkSpec(
                name="paragraph", 
                min_chars=200,
                max_chars=1200,
                overlap_chars=50,
                description="Paragraph-level chunks for contextual understanding"
            ),
            "section": ChunkSpec(
                name="section",
                min_chars=800,
                max_chars=5000,
                overlap_chars=200,
                description="Section-level chunks for thematic comprehension"
            )
        }
        
        # Processing configuration - TURBO MODE ACTIVATED!
        self.batch_size = 50  # Books per batch (5x increase for performance)
        self.retry_attempts = 3
        self.save_interval = 100  # Save state every 100 chunks (reduce I/O)
        
        # Logging setup
        self.setup_logging()
        
        # State tracking
        self.session_start = datetime.now()
        self.stats = MultiGranularStats(
            session_start=self.session_start.isoformat(),
            last_updated=datetime.now().isoformat(),
            runtime_seconds=0.0,
            books_processed=0,
            books_completed=0,
            books_failed=0,
            original_chapters_processed=0,
            sentence_chunks_created=0,
            paragraph_chunks_created=0,
            section_chunks_created=0,
            average_processing_time=0.0,
            chunks_per_second=0.0,
            granularity_expansion_ratio=0.0,
            current_book=None,
            current_chunk=None,
            success_rate=0.0,
            processing_errors=0,
            daemon_pid=os.getpid(),
            environment=self.environment,
            memory_usage_mb=0.0
        )
        
        # State and metrics files
        self.daemon_dir = Path('logs/multi_granular_chunking')
        self.daemon_dir.mkdir(parents=True, exist_ok=True)
        
        self.state_file = self.daemon_dir / 'daemon_state.json'
        self.metrics_file = self.daemon_dir / 'granular_metrics.json'
        
        # Graceful shutdown handling
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("🧠 Multi-Granular Chunking Daemon initialized")
        logger.info(f"📊 Environment: {self.environment}")
        logger.info(f"🔗 Database: {self.db_config['host']}:{self.db_config.get('port', 5432)}")
        logger.info(f"📏 Granularity levels: {list(self.chunk_specs.keys())}")
        
    def detect_environment(self) -> str:
        """Auto-detect runtime environment"""
        if os.environ.get('RUNNING_IN_CONTAINER') or os.path.exists('/var/run/secrets/kubernetes.io'):
            return "kubernetes"
        elif os.path.exists('/.dockerenv'):
            return "docker"
        else:
            return "host"
            
    def get_database_config(self) -> Dict[str, Any]:
        """Get environment-specific database configuration"""
        if self.environment == "kubernetes":
            return {
                'host': os.environ.get('DB_HOST', 'postgres-service'),
                'port': int(os.environ.get('DB_PORT', 5432)),
                'database': os.environ.get('DB_NAME', 'knowledge_base'), 
                'user': os.environ.get('DB_USER', 'weixiangzhang'),
                'password': os.environ.get('DB_PASSWORD')
            }
        elif self.environment == "docker":
            return {
                'host': os.environ.get('DB_HOST', 'host.docker.internal'),
                'port': int(os.environ.get('DB_PORT', 5432)),
                'database': os.environ.get('DB_NAME', 'knowledge_base'),
                'user': os.environ.get('DB_USER', 'weixiangzhang'), 
                'password': os.environ.get('DB_PASSWORD')
            }
        else:
            return {
                'host': 'localhost',
                'port': 5432,
                'database': 'knowledge_base',
                'user': os.environ.get('DB_USER', 'weixiangzhang'),
                'password': os.environ.get('DB_PASSWORD')
            }
            
    def setup_logging(self):
        """Setup environment-specific logging"""
        log_file = self.daemon_dir / 'daemon.log' if hasattr(self, 'daemon_dir') else Path('/tmp/multi_granular_daemon.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

    def _signal_handler(self, signum, frame):
        """Handle graceful shutdown"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.running = False
        
    def split_into_sentences(self, text: str) -> List[str]:
        """Advanced sentence splitting using regex patterns"""
        import re
        
        # Advanced sentence boundary detection
        sentence_pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\!|\?)\s+'
        sentences = re.split(sentence_pattern, text)
        
        # Clean and filter sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            # Filter out noise and ensure minimum quality
            if (len(sentence) >= 30 and 
                not sentence.isupper() and 
                sentence.count(' ') >= 3 and
                not sentence.startswith(('Fig.', 'Table', 'Chapter', 'Page'))):
                cleaned_sentences.append(sentence)
                
        return cleaned_sentences
        
    def split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into logical paragraphs"""
        import re
        
        # Split on paragraph boundaries
        paragraph_pattern = r'\n\s*\n|\r\n\s*\r\n'
        paragraphs = re.split(paragraph_pattern, text)
        
        # Clean and validate paragraphs
        cleaned_paragraphs = []
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if len(paragraph) >= 100 and paragraph.count('.') >= 2:
                cleaned_paragraphs.append(paragraph)
                
        return cleaned_paragraphs
        
    def create_overlapping_chunks(self, text: str, spec: ChunkSpec) -> List[GranularChunk]:
        """Create overlapping chunks with quality scoring"""
        chunks = []
        words = text.split()
        
        if len(text) <= spec.max_chars:
            if len(text) >= spec.min_chars:
                chunk = GranularChunk(
                    content=text,
                    chunk_type=spec.name,
                    parent_chunk_id=0,  # Will be set by caller
                    chunk_index=0,
                    char_length=len(text),
                    overlap_start=0,
                    overlap_end=0,
                    quality_score=self.calculate_chunk_quality(text),
                    processing_metadata={"method": "single_chunk"}
                )
                return [chunk]
            else:
                return []
        
        start = 0
        chunk_index = 0
        
        while start < len(words):
            # Build chunk within size limits
            chunk_words = []
            current_length = 0
            end = start
            
            while end < len(words) and current_length < spec.max_chars:
                word = words[end]
                if current_length + len(word) + 1 <= spec.max_chars:
                    chunk_words.append(word)
                    current_length += len(word) + 1
                    end += 1
                else:
                    break
                    
            chunk_text = " ".join(chunk_words)
            
            if len(chunk_text) >= spec.min_chars:
                # Calculate overlap boundaries
                overlap_words = max(1, spec.overlap_chars // 6)
                overlap_start = max(0, len(chunk_words) - overlap_words) if chunk_index > 0 else 0
                overlap_end = min(overlap_words, len(chunk_words)) if end < len(words) else 0
                
                chunk = GranularChunk(
                    content=chunk_text,
                    chunk_type=spec.name,
                    parent_chunk_id=0,  # Will be set by caller
                    chunk_index=chunk_index,
                    char_length=len(chunk_text),
                    overlap_start=overlap_start,
                    overlap_end=overlap_end,
                    quality_score=self.calculate_chunk_quality(chunk_text),
                    processing_metadata={
                        "method": "overlapping_window",
                        "word_count": len(chunk_words),
                        "position": f"{start}-{end}"
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
                
            # Move to next position with overlap
            overlap_words = max(1, spec.overlap_chars // 6)
            start = max(start + 1, end - overlap_words)
            
            if start >= len(words):
                break
                
        return chunks
        
    def calculate_chunk_quality(self, text: str) -> float:
        """Calculate quality score for a chunk (0.0 to 1.0)"""
        score = 0.0
        
        # Length score (optimal range)
        length_score = min(1.0, len(text) / 500)  # Normalized to 500 chars
        score += length_score * 0.3
        
        # Sentence completeness
        sentence_endings = text.count('.') + text.count('!') + text.count('?')
        sentence_score = min(1.0, sentence_endings / 3)  # Up to 3 sentences
        score += sentence_score * 0.4
        
        # Word density
        words = text.split()
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        word_score = max(0.0, min(1.0, (avg_word_length - 2) / 6))  # 2-8 char words
        score += word_score * 0.2
        
        # Content richness (varied punctuation, capitalization)
        richness_score = 0.0
        if any(c.isupper() for c in text):
            richness_score += 0.3
        if any(c in text for c in ',:;()[]'):
            richness_score += 0.3
        if not text.isupper() and not text.islower():
            richness_score += 0.4
        score += richness_score * 0.1
        
        return min(1.0, score)
        
    def save_granular_metrics(self):
        """Save Grafana-compatible metrics"""
        try:
            runtime = (datetime.now() - self.session_start).total_seconds()
            
            # Update stats
            self.stats.runtime_seconds = runtime
            self.stats.last_updated = datetime.now().isoformat()
            self.stats.memory_usage_mb = psutil.Process().memory_info().rss / 1024 / 1024
            
            # Calculate performance metrics
            if runtime > 0:
                self.stats.chunks_per_second = self.stats.original_chapters_processed / runtime
                
            if self.stats.original_chapters_processed > 0:
                self.stats.granularity_expansion_ratio = (
                    self.stats.total_granular_chunks() / self.stats.original_chapters_processed
                )
                
            # Grafana metrics (Prometheus format)
            grafana_metrics = {
                "timestamp": datetime.now().isoformat(),
                "metrics": {
                    "multi_granular_books_processed": self.stats.books_processed,
                    "multi_granular_chapters_processed": self.stats.original_chapters_processed,
                    "multi_granular_sentences_created": self.stats.sentence_chunks_created,
                    "multi_granular_paragraphs_created": self.stats.paragraph_chunks_created,
                    "multi_granular_sections_created": self.stats.section_chunks_created,
                    "multi_granular_total_chunks": self.stats.total_granular_chunks(),
                    "multi_granular_expansion_ratio": self.stats.granularity_expansion_ratio,
                    "multi_granular_processing_rate_chunks_per_second": self.stats.chunks_per_second,
                    "multi_granular_success_rate_percent": self.stats.success_rate,
                    "multi_granular_memory_usage_mb": self.stats.memory_usage_mb,
                    "multi_granular_daemon_uptime_seconds": runtime
                },
                "labels": {
                    "environment": self.stats.environment,
                    "daemon": "multi_granular_chunking",
                    "instance": f"daemon_{self.stats.daemon_pid}"
                }
            }
            
            # Save metrics for Grafana
            with open(self.metrics_file, 'w') as f:
                json.dump(grafana_metrics, f, indent=2)
                
            # Save daemon state
            with open(self.state_file, 'w') as f:
                json.dump(asdict(self.stats), f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    def get_db_connection(self):
        """Get PostgreSQL connection"""
        try:
            return psycopg2.connect(**self.db_config)
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            return None

    def get_books_for_processing(self) -> List[Dict[str, Any]]:
        """Get books that need progressive chunking"""
        
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return []
                
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # Get books with sufficient chunks for processing
                    cur.execute("""
                        SELECT 
                            b.book_id,
                            b.title,
                            b.author,
                            COUNT(c.chunk_id) as chunk_count,
                            COUNT(CASE WHEN c.progressive_outline IS NOT NULL THEN 1 END) as processed_chunks
                        FROM books b
                        JOIN chunks c ON b.book_id = c.book_id
                        WHERE c.content IS NOT NULL
                        AND c.word_count BETWEEN 200 AND 2000
                        GROUP BY b.book_id, b.title, b.author
                        HAVING COUNT(c.chunk_id) >= 10
                        AND COUNT(CASE WHEN c.progressive_outline IS NOT NULL THEN 1 END) < COUNT(c.chunk_id)
                        ORDER BY COUNT(c.chunk_id) DESC
                    """)
                    
                    results = cur.fetchall()
                    return [dict(result) for result in results]
                    
        except Exception as e:
            logger.error(f"Error getting books for processing: {e}")
            return []

    def get_book_chunks(self, book_id: str) -> List[Dict[str, Any]]:
        """Get ordered chunks for a book"""
        
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return []
                
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            c.chunk_id,
                            c.content,
                            c.word_count,
                            c.chapter_number,
                            c.progressive_outline
                        FROM chunks c
                        WHERE c.book_id = %s
                        AND c.content IS NOT NULL
                        AND c.word_count BETWEEN 200 AND 2000
                        ORDER BY c.start_position ASC, c.chunk_id ASC
                    """, (book_id,))
                    
                    results = cur.fetchall()
                    return [dict(result) for result in results]
                    
        except Exception as e:
            logger.error(f"Error getting book chunks: {e}")
            return []

    def add_progressive_outline_column(self):
        """Add progressive_outline column to chunks table if not exists"""
        
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return False
                
                with conn.cursor() as cur:
                    cur.execute("""
                        ALTER TABLE chunks 
                        ADD COLUMN IF NOT EXISTS progressive_outline JSONB;
                    """)
                    
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS chunks_progressive_outline_idx 
                        ON chunks USING gin (progressive_outline)
                        WHERE progressive_outline IS NOT NULL;
                    """)
                    
                    conn.commit()
                    logger.info("Progressive outline column added to chunks table")
                    return True
                    
        except Exception as e:
            logger.error(f"Error adding progressive outline column: {e}")
            return False

    def call_ollama(self, prompt: str, timeout: int = 180) -> Optional[str]:
        """Call Ollama API with retry logic"""
        
        for attempt in range(self.retry_attempts):
            try:
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_k": 40,
                            "top_p": 0.9
                        }
                    },
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('response', '').strip()
                else:
                    logger.warning(f"Ollama API returned {response.status_code}, attempt {attempt + 1}")
                    
            except Exception as e:
                logger.error(f"Ollama call failed (attempt {attempt + 1}): {e}")
                
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.backoff_delay)
        
        return None

    def process_chapter_into_granularities(
        self,
        chapter_id: int,
        chapter_content: str,
        book_id: int,
        chapter_base: int = 0,
        chapter_number: Optional[int] = None
    ) -> Dict[str, int]:
        """Process a chapter into multiple granularity levels.

        chapter_base is the cumulative character offset of this chapter
        within the book (in spine order), so every granular chunk gets a
        book-global start_position and (book_id, start_position) is the
        true reading order.
        """

        results = {"sentence": 0, "paragraph": 0, "section": 0}
        
        try:
            # Process sentences
            sentences = self.split_into_sentences(chapter_content)
            sentence_chunks = []
            for sentence in sentences:
                if len(sentence) >= self.chunk_specs["sentence"].min_chars:
                    chunk = GranularChunk(
                        content=sentence,
                        chunk_type="sentence",
                        parent_chunk_id=chapter_id,
                        chunk_index=len(sentence_chunks),
                        char_length=len(sentence),
                        overlap_start=0,
                        overlap_end=0,
                        quality_score=self.calculate_chunk_quality(sentence),
                        processing_metadata={"method": "sentence_split", "source": "chapter"}
                    )
                    sentence_chunks.append(chunk)
                    
            # Process paragraphs
            paragraphs = self.split_into_paragraphs(chapter_content)
            paragraph_chunks = []
            for paragraph in paragraphs:
                chunks = self.create_overlapping_chunks(paragraph, self.chunk_specs["paragraph"])
                for chunk in chunks:
                    chunk.parent_chunk_id = chapter_id
                    chunk.chunk_type = "paragraph"
                paragraph_chunks.extend(chunks)
                
            # Process sections (overlapping chunks of full content)
            section_chunks = self.create_overlapping_chunks(chapter_content, self.chunk_specs["section"])
            for chunk in section_chunks:
                chunk.parent_chunk_id = chapter_id
                chunk.chunk_type = "section"
                
            # Insert into database. Each granularity gets its own locator
            # (moving cursor) so overlapping/repeated content stays monotonic.
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    for granularity, chunk_list in (
                        ("sentence", sentence_chunks),
                        ("paragraph", paragraph_chunks),
                        ("section", section_chunks),
                    ):
                        locator = ContentLocator(chapter_content)
                        for i, chunk in enumerate(chunk_list):
                            chunk_id = f"{book_id}_{granularity}_{chapter_id}_{i}"
                            span = locator.locate(chunk.content)
                            if span is not None:
                                start_pos = chapter_base + span[0]
                                end_pos = chapter_base + span[1]
                            else:
                                # Unlocatable content still lands inside the
                                # right chapter for ordering purposes.
                                start_pos = chapter_base
                                end_pos = chapter_base + len(chunk.content)
                            cur.execute("""
                                INSERT INTO chunks (chunk_id, book_id, content, chunk_type, parent_chunk_id,
                                                    word_count, chapter_number, start_position, end_position, created_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                            """, (chunk_id, book_id, chunk.content, chunk.chunk_type, str(chunk.parent_chunk_id),
                                  len(chunk.content.split()), chapter_number, start_pos, end_pos))
                        results[granularity] = len(chunk_list)

                    conn.commit()
                    
        except Exception as e:
            logger.error(f"Error processing chapter {chapter_id}: {e}")
            self.stats.processing_errors += 1
            
        return results

    def get_chapters_for_processing(self) -> List[Dict[str, Any]]:
        """Get chapter chunks that need multi-granular processing.

        IMPORTANT: chapters MUST be ordered by the numeric trailing part of
        their chunk_id (the spine ordinal assigned at ingest), NOT by the raw
        varchar chunk_id. The old `ORDER BY c.chunk_id` sorted
        '<book>_chapter_10' before '<book>_chapter_2' and scrambled the
        reading order of every multi-granular chunk created on 2025-08-01/02.
        chapter_base is the cumulative character offset of the chapter within
        its book, so granular chunks get book-global start_position values.
        """
        spine_order = chapter_spine_order_sql('chunk_id')
        try:
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(f"""
                        WITH chapters AS (
                            SELECT chunk_id, book_id, content, chapter_number,
                                   COALESCE(SUM(LENGTH(content) + 2) OVER (
                                       PARTITION BY book_id
                                       ORDER BY {spine_order}
                                       ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
                                   ), 0) AS chapter_base
                            FROM chunks
                            WHERE chunk_type = 'chapter'
                            AND content IS NOT NULL
                        )
                        SELECT c.chunk_id, c.book_id, c.content, c.chapter_number,
                               c.chapter_base, b.title
                        FROM chapters c
                        JOIN books b ON c.book_id = b.book_id
                        WHERE LENGTH(c.content) > 500
                        AND NOT EXISTS (
                            SELECT 1 FROM chunks gc
                            WHERE gc.parent_chunk_id = c.chunk_id
                            AND gc.chunk_type IN ('sentence', 'paragraph', 'section')
                        )
                        ORDER BY c.book_id, {chapter_spine_order_sql('c.chunk_id')}
                        LIMIT %s
                    """, (self.batch_size,))

                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting chapters: {e}")
            return []

    def run(self):
        """Main daemon execution loop"""
        self.running = True
        logger.info("🚀 Multi-Granular Chunking Daemon Started")
        logger.info("📏 Creating sentence → paragraph → section granularities")
        logger.info(f"🎯 Target: Transform 247,911 chapters into 1.2M+ granular chunks")
        
        # Write PID file
        pid_file = Path('pids/multi_granular_daemon.pid')
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
        
        try:
            # Save initial metrics
            self.save_granular_metrics()
            logger.info("✅ Multi-Granular Chunking Daemon ready for processing")
            
            while self.running:
                chapters = self.get_chapters_for_processing()
                
                if not chapters:
                    logger.info("🎉 All chapters processed! Multi-granular chunking complete!")
                    break
                
                logger.info(f"📚 Processing {len(chapters)} chapters...")
                
                for chapter in chapters:
                    if not self.running:
                        break
                    
                    chapter_id = chapter['chunk_id']
                    book_id = chapter['book_id'] 
                    content = chapter['content']
                    title = chapter['title']
                    
                    self.stats.current_book = title
                    self.stats.current_chunk = str(chapter_id)
                    
                    logger.info(f"🔄 Processing chapter {chapter_id} from '{title}'")
                    
                    start_time = time.time()
                    results = self.process_chapter_into_granularities(
                        chapter_id, content, book_id,
                        chapter_base=chapter.get('chapter_base', 0) or 0,
                        chapter_number=chapter.get('chapter_number')
                    )
                    processing_time = time.time() - start_time
                    
                    # Update stats
                    self.stats.original_chapters_processed += 1
                    self.stats.sentence_chunks_created += results.get('sentence', 0)
                    self.stats.paragraph_chunks_created += results.get('paragraph', 0) 
                    self.stats.section_chunks_created += results.get('section', 0)
                    
                    total_created = sum(results.values())
                    logger.info(f"✅ Chapter {chapter_id}: {total_created} chunks created "
                               f"({results['sentence']} sentences, {results['paragraph']} paragraphs, "
                               f"{results['section']} sections) in {processing_time:.1f}s")
                    
                    # Save metrics every 10 chapters
                    if self.stats.original_chapters_processed % 10 == 0:
                        self.save_granular_metrics()
                        expansion_ratio = (self.stats.total_granular_chunks() / 
                                         self.stats.original_chapters_processed if self.stats.original_chapters_processed > 0 else 0)
                        logger.info(f"📊 Progress: {self.stats.original_chapters_processed} chapters → "
                                   f"{self.stats.total_granular_chunks()} granular chunks "
                                   f"(expansion: {expansion_ratio:.1f}x)")
                    
                    # TURBO: Removed artificial delay for maximum performance
                    # time.sleep(0.5)  # Disabled for speed
                
                # Save state after each batch
                self.save_granular_metrics()
                
                if self.running and chapters:
                    # TURBO: Removed batch delay for maximum throughput
                    # time.sleep(2)  # Disabled for speed
                    pass  # Continue processing without delay
                
        except KeyboardInterrupt:
            logger.info("🛑 Daemon stopped by user")
        except Exception as e:
            logger.error(f"💥 Daemon error: {e}")
        finally:
            logger.info("🧹 Multi-Granular Chunking Daemon shutdown")
            self.save_granular_metrics()
            
            # Remove PID file
            if pid_file.exists():
                pid_file.unlink()
                
            self.print_final_report()
            
    def print_final_report(self):
        """Print comprehensive final processing report"""
        runtime = (datetime.now() - self.session_start).total_seconds()
        
        report = f"""
================================================================================
🧠 MULTI-GRANULAR CHUNKING DAEMON - FINAL REPORT  
================================================================================
📚 Chapters Processed: {self.stats.original_chapters_processed:,}
🔄 Total Processing Time: {runtime:.1f} seconds ({runtime/3600:.2f} hours)

📏 GRANULAR CHUNKS CREATED:
    🔸 Sentence Level: {self.stats.sentence_chunks_created:,} chunks
    🔹 Paragraph Level: {self.stats.paragraph_chunks_created:,} chunks  
    🔶 Section Level: {self.stats.section_chunks_created:,} chunks
    
📊 TOTAL NEW CHUNKS: {self.stats.total_granular_chunks():,}
📈 Granularity Expansion: {self.stats.granularity_expansion_ratio:.1f}x

⚡ PERFORMANCE METRICS:
    Processing Rate: {self.stats.chunks_per_second:.2f} chapters/second
    Average Chapter Time: {self.stats.average_processing_time:.2f} seconds
    Success Rate: {self.stats.success_rate:.1f}%
    Memory Usage: {self.stats.memory_usage_mb:.1f} MB

🎯 PRECISION SEARCH CAPABILITIES ENABLED!
    Micro → Macro: sentence → paragraph → section → chapter
    Search Granularity: 4 levels of precision targeting
    Embedding Ready: Compatible with Arctic/BGE/MxBai/Nomic models
================================================================================
        """
        
        logger.info(report)

# All old methods removed - using new multi-granular implementation above


def main():
    """Start the multi-granular chunking daemon"""
    
    daemon = MultiGranularChunkingDaemon()
    daemon.run()
    
# Test the daemon initialization
def test_daemon():
    """Test daemon initialization and configuration"""
    daemon = MultiGranularChunkingDaemon()
    logger.info("🧪 Testing daemon configuration...")
    logger.info(f"📊 Environment: {daemon.environment}")
    logger.info(f"🔗 Database: {daemon.db_config}")
    logger.info(f"📏 Chunk specs: {[spec.name for spec in daemon.chunk_specs.values()]}")
    logger.info("✅ Daemon configuration test complete")
    
    # Test text processing
    sample_text = """This is a sample sentence for testing. This is another sentence with more content to analyze. 
    
    This is a new paragraph with different content. It contains multiple sentences and should be processed differently from the first paragraph.
    
    This is a third paragraph that represents a larger section of text. It has even more content and represents what might be considered a section-level chunk in our granular processing system."""
    
    logger.info("🧪 Testing text processing...")
    sentences = daemon.split_into_sentences(sample_text)
    paragraphs = daemon.split_into_paragraphs(sample_text)
    
    logger.info(f"📄 Sentences found: {len(sentences)}")
    logger.info(f"📚 Paragraphs found: {len(paragraphs)}")
    
    # Test chunk creation
    for spec_name, spec in daemon.chunk_specs.items():
        chunks = daemon.create_overlapping_chunks(sample_text, spec)
        logger.info(f"🔸 {spec_name} chunks: {len(chunks)} (avg quality: {sum(c.quality_score for c in chunks)/len(chunks) if chunks else 0:.2f})")
    
    logger.info("✅ Text processing test complete")


if __name__ == "__main__":
    main()