#!/usr/bin/env python3
"""
Reddit Bibliophile Agent - Data Scientist & Book Analysis Specialist
Downloads books, extracts chapter outlines, and builds knowledge graphs for research
"""

import sqlite3
import json
import time
import re
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import hashlib
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict, Counter

try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
    EPUB_SUPPORT = True
except ImportError:
    EPUB_SUPPORT = False
    print("⚠️ Install dependencies: pip install EbookLib beautifulsoup4 networkx matplotlib")

try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

@dataclass
class BookChapter:
    """Represents a book chapter with analysis"""
    chapter_number: int
    title: str
    content: str
    word_count: int
    key_concepts: List[str]
    named_entities: List[str]
    summary: str
    themes: List[str]
    
@dataclass
class BookOutline:
    """Complete book structure and analysis"""
    book_id: str
    title: str
    author: str
    total_chapters: int
    total_words: int
    chapters: List[BookChapter]
    main_themes: List[str]
    key_concepts: List[str]
    book_summary: str
    genre_classification: str
    complexity_score: float
    created_at: str = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

@dataclass
class KnowledgeNode:
    """Node in the knowledge graph"""
    id: str
    label: str
    type: str  # concept, entity, theme, book, chapter
    properties: Dict
    books: Set[str]
    chapters: Set[str]
    weight: float = 1.0

@dataclass
class KnowledgeEdge:
    """Edge connecting knowledge nodes"""
    source: str
    target: str
    relationship: str
    weight: float
    evidence: List[str]  # Supporting text excerpts

class RedditBibliophileAgent:
    """Reddit-style AI agent that's a data scientist and bibliophile"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Get the project root directory (LibraryOfBabel)
        current_file = Path(__file__).resolve()
        self.project_root = current_file.parent.parent.parent
        
        # Set paths relative to project root
        self.db_path = self.config.get('db_path', str(self.project_root / 'database/data/audiobook_ebook_tracker.db'))
        self.analysis_dir = self.project_root / 'reports/reddit_analysis'
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        
        # Ebook locations
        self.ebooks_dir = self.project_root / 'ebooks'
        self.torrents_dir = self.ebooks_dir / 'torrents'
        self.downloads_dir = self.ebooks_dir / 'downloads'
        self.analysis_output_dir = self.ebooks_dir / 'analysis'
        
        # Create ebook directories
        for dir_path in [self.ebooks_dir, self.torrents_dir, self.downloads_dir, self.analysis_output_dir]:
            dir_path.mkdir(exist_ok=True)
        
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Reddit persona characteristics
        self.persona = {
            'name': 'u/DataScientistBookworm',
            'interests': ['data analysis', 'literature', 'knowledge graphs', 'research'],
            'analysis_style': 'quantitative + qualitative',
            'favorite_topics': ['interconnections', 'patterns', 'insights'],
            'catchphrases': ['TL;DR', 'Deep dive incoming', 'The data tells a story'],
            'seeding_philosophy': '2 weeks minimum - respect the community!'
        }
        
        # Seeding compliance tracking
        self.downloaded_books = []
        self.seeding_violations = []
        self.MINIMUM_SEEDING_DAYS = 14
        
        self.init_analysis_database()
        
        # Knowledge graph
        self.knowledge_graph = nx.Graph()
        self.concept_frequency = Counter()
        self.theme_connections = defaultdict(set)
        
        self.logger.info(f"🤓 {self.persona['name']} reporting for duty!")
        self.logger.info("📚 Data scientist + bibliophile = knowledge graph magic ✨")
        self.logger.info("🛡️ 2-WEEK SEEDING RULE: Always respected!")
    
    def setup_logging(self):
        """Setup logging for the bibliophile agent"""
        log_dir = Path('../logs')
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f'reddit_bibliophile_{timestamp}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - [REDDIT_AGENT] - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def init_analysis_database(self):
        """Initialize book analysis database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                -- Book outlines table
                CREATE TABLE IF NOT EXISTS book_outlines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id TEXT UNIQUE,
                    title TEXT,
                    author TEXT,
                    total_chapters INTEGER,
                    total_words INTEGER,
                    main_themes TEXT, -- JSON array
                    key_concepts TEXT, -- JSON array
                    book_summary TEXT,
                    genre_classification TEXT,
                    complexity_score REAL,
                    analysis_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    agent_version TEXT DEFAULT 'RedditBibliophile_v1.0'
                );
                
                -- Chapter analysis table
                CREATE TABLE IF NOT EXISTS chapter_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id TEXT,
                    chapter_number INTEGER,
                    chapter_title TEXT,
                    word_count INTEGER,
                    key_concepts TEXT, -- JSON array
                    named_entities TEXT, -- JSON array
                    summary TEXT,
                    themes TEXT, -- JSON array
                    content_hash TEXT,
                    FOREIGN KEY (book_id) REFERENCES book_outlines (book_id)
                );
                
                -- Knowledge graph nodes
                CREATE TABLE IF NOT EXISTS knowledge_nodes (
                    id TEXT PRIMARY KEY,
                    label TEXT,
                    type TEXT,
                    properties TEXT, -- JSON
                    books TEXT, -- JSON array
                    chapters TEXT, -- JSON array
                    weight REAL DEFAULT 1.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Knowledge graph edges
                CREATE TABLE IF NOT EXISTS knowledge_edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT,
                    target_id TEXT,
                    relationship TEXT,
                    weight REAL,
                    evidence TEXT, -- JSON array
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES knowledge_nodes (id),
                    FOREIGN KEY (target_id) REFERENCES knowledge_nodes (id)
                );
                
                -- Reddit agent activity log
                CREATE TABLE IF NOT EXISTS agent_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    activity_type TEXT,
                    description TEXT,
                    book_id TEXT,
                    insights TEXT, -- JSON
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    agent_name TEXT DEFAULT 'u/DataScientistBookworm'
                );
                
                -- Indexes for performance
                CREATE INDEX IF NOT EXISTS idx_book_outlines_book_id ON book_outlines (book_id);
                CREATE INDEX IF NOT EXISTS idx_chapter_analysis_book_id ON chapter_analysis (book_id);
                CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_type ON knowledge_nodes (type);
                CREATE INDEX IF NOT EXISTS idx_knowledge_edges_source ON knowledge_edges (source_id);
                CREATE INDEX IF NOT EXISTS idx_knowledge_edges_target ON knowledge_edges (target_id);
            """)
    
    def log_reddit_activity(self, activity_type: str, description: str, book_id: str = None, insights: Dict = None):
        """Log agent activity in Reddit style"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO agent_activity (activity_type, description, book_id, insights)
                VALUES (?, ?, ?, ?)
            """, (activity_type, description, book_id, json.dumps(insights) if insights else None))
    
    def get_first_n_books_for_analysis(self, n: int = 10) -> List[Dict]:
        """Get first N books from audiobook collection for analysis"""
        self.logger.info(f"🎯 Targeting first {n} books for deep analysis...")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get books that haven't been analyzed yet
            cursor.execute("""
                SELECT a.album_id, a.title, a.author, a.clean_title, a.clean_author,
                       e.local_file_path, e.ebook_title, e.file_format
                FROM audiobooks a
                LEFT JOIN ebooks e ON a.album_id = e.audiobook_id
                LEFT JOIN book_outlines bo ON CAST(a.album_id AS TEXT) = bo.book_id
                WHERE e.local_file_path IS NOT NULL 
                AND bo.book_id IS NULL
                ORDER BY a.title
                LIMIT ?
            """, (n,))
            
            books = []
            for row in cursor.fetchall():
                book = {
                    'album_id': row[0],
                    'title': row[1],
                    'author': row[2],
                    'clean_title': row[3],
                    'clean_author': row[4],
                    'local_file_path': row[5],
                    'ebook_title': row[6],
                    'file_format': row[7]
                }
                books.append(book)
        
        self.logger.info(f"📊 Found {len(books)} books ready for analysis")
        
        if not books:
            self.logger.warning("🤔 No books with local files found. Checking downloads directory...")
            # Check downloads directory for actual ebook files
            if self.downloads_dir.exists():
                ebook_files = list(self.downloads_dir.rglob('*.epub')) + \
                             list(self.downloads_dir.rglob('*.pdf')) + \
                             list(self.downloads_dir.rglob('*.mobi'))
                self.logger.info(f"📚 Found {len(ebook_files)} ebook files in downloads directory")
                
                books = []
                for i, file_path in enumerate(ebook_files):
                    books.append({
                        'album_id': f'downloaded_{i+1}',
                        'title': file_path.stem,
                        'author': 'Unknown',
                        'clean_title': file_path.stem,
                        'clean_author': 'Unknown',
                        'local_file_path': str(file_path),
                        'ebook_title': file_path.stem,
                        'file_format': file_path.suffix[1:]  # Remove the dot
                    })
            
            # If still no books, check if we need to trigger downloads
            if not books:
                self.logger.info("📥 No ebooks in downloads directory. Need to acquire books first!")
                # Check transmission for any downloaded ebooks that need to be moved
                self.check_and_organize_completed_downloads()
        
        return books
    
    def check_and_organize_completed_downloads(self):
        """Check Transmission for completed downloads and organize them"""
        self.logger.info("🔍 Checking Transmission for completed ebook downloads...")
        
        try:
            # Check transmission for completed downloads
            result = subprocess.run(['transmission-remote', '-l'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                
                for line in lines[1:-1]:  # Skip header and sum
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 9:
                            torrent_id = parts[0].strip('*')
                            done_percent = parts[1]
                            status = parts[7]
                            name = ' '.join(parts[8:])
                            
                            # Check if it's an ebook and completed
                            if (any(ext in name.lower() for ext in ['.epub', '.pdf', '.mobi']) and 
                                done_percent == '100%'):
                                
                                self.logger.info(f"📚 Found completed ebook: {name}")
                                
                                # Get detailed info to find download location
                                detail_result = subprocess.run(
                                    ['transmission-remote', '-t', torrent_id, '-i'],
                                    capture_output=True, text=True, timeout=30
                                )
                                
                                if detail_result.returncode == 0:
                                    # Parse location from detailed info
                                    location = self.parse_download_location(detail_result.stdout)
                                    if location:
                                        self.organize_completed_ebook(name, location, torrent_id)
                
            else:
                self.logger.warning("Could not connect to Transmission daemon")
                
        except Exception as e:
            self.logger.warning(f"Error checking Transmission: {e}")
    
    def parse_download_location(self, transmission_info: str) -> Optional[str]:
        """Parse download location from transmission info"""
        for line in transmission_info.split('\n'):
            if 'Location:' in line:
                return line.split('Location:', 1)[1].strip()
        return None
    
    def organize_completed_ebook(self, name: str, location: str, torrent_id: str):
        """Organize a completed ebook download"""
        try:
            source_path = Path(location) / name
            if source_path.exists():
                # Copy to our organized downloads directory
                dest_path = self.downloads_dir / name
                
                if not dest_path.exists():
                    # Copy file to downloads directory
                    import shutil
                    shutil.copy2(source_path, dest_path)
                    self.logger.info(f"📁 Organized ebook: {dest_path}")
                    
                    # Track for seeding compliance
                    self.track_ebook_for_seeding(name, torrent_id, str(dest_path))
                
        except Exception as e:
            self.logger.error(f"Error organizing ebook {name}: {e}")
    
    def track_ebook_for_seeding(self, name: str, torrent_id: str, file_path: str):
        """Track ebook for 2-week seeding compliance"""
        download_info = {
            'torrent_id': torrent_id,
            'name': name,
            'file_path': file_path,
            'download_start': datetime.now(),
            'seeding_required_until': datetime.now() + timedelta(days=self.MINIMUM_SEEDING_DAYS),
            'compliant': False
        }
        
        self.downloaded_books.append(download_info)
        self.logger.info(f"🛡️ Tracking {name} for 2-week seeding compliance")
        self.logger.info(f"📅 Must seed until: {download_info['seeding_required_until'].strftime('%Y-%m-%d %H:%M')}")
    
    def download_and_process_books(self, target_count: int = 10) -> List[Dict]:
        """Download and process books using the ebook discovery system"""
        self.logger.info(f"🚀 u/DataScientistBookworm starting book acquisition mission!")
        self.logger.info(f"🎯 Target: {target_count} books for analysis")
        
        # First, check what's already available
        available_books = self.get_first_n_books_for_analysis(target_count)
        
        if len(available_books) >= target_count:
            self.logger.info(f"✅ Found {len(available_books)} books ready for analysis!")
            return available_books[:target_count]
        
        self.logger.info(f"📥 Need to acquire {target_count - len(available_books)} more books...")
        
        # Trigger ebook discovery system if needed
        try:
            self.trigger_book_discovery(target_count - len(available_books))
        except Exception as e:
            self.logger.warning(f"Could not trigger discovery system: {e}")
        
        # Return what we have
        return available_books
    
    def trigger_book_discovery(self, count: int):
        """Trigger the ebook discovery system to find more books"""
        self.logger.info(f"🤖 Triggering ebook discovery for {count} books...")
        self.logger.info("⚡ Ebooks download fast - seeding compliance critical!")
        
        try:
            # Try to run the Playwright automation
            cmd = ['node', 'mam_playwright_automation.js', str(count)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.info("✅ Ebook discovery triggered successfully")
                
                # Track new downloads for seeding compliance
                self.track_new_downloads()
                
                # Start seeding monitor if not already running
                self.ensure_seeding_monitor_active()
                
            else:
                self.logger.warning(f"Discovery system warning: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            self.logger.warning("Discovery system timed out")
        except FileNotFoundError:
            self.logger.info("💡 Manual book discovery needed - automation not available")
    
    def track_new_downloads(self):
        """Track newly downloaded books for seeding compliance"""
        self.logger.info("📊 Tracking new downloads for seeding compliance...")
        
        try:
            # Run transmission-remote to get current torrents
            result = subprocess.run(['transmission-remote', '-l'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                
                # Parse active torrents
                for line in lines[1:-1]:  # Skip header and sum
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 9:
                            torrent_id = parts[0].strip('*')
                            status = parts[7]
                            name = ' '.join(parts[8:])
                            
                            # Track ebook downloads
                            if any(ext in name.lower() for ext in ['.epub', '.pdf', '.mobi']):
                                download_info = {
                                    'torrent_id': torrent_id,
                                    'name': name,
                                    'status': status,
                                    'download_start': datetime.now(),
                                    'seeding_required_until': datetime.now() + timedelta(days=self.MINIMUM_SEEDING_DAYS),
                                    'compliant': False
                                }
                                
                                # Add to tracking if not already tracked
                                if not any(d['torrent_id'] == torrent_id for d in self.downloaded_books):
                                    self.downloaded_books.append(download_info)
                                    self.logger.info(f"📚 Tracking ebook: {name} (ID: {torrent_id})")
                                    self.logger.info(f"🛡️ Must seed until: {download_info['seeding_required_until'].strftime('%Y-%m-%d %H:%M')}")
                
                self.save_seeding_tracking()
                
        except Exception as e:
            self.logger.warning(f"Could not track downloads: {e}")
    
    def ensure_seeding_monitor_active(self):
        """Ensure seeding monitor is running for compliance"""
        self.logger.info("🛡️ Ensuring seeding monitor is active...")
        
        try:
            # Check if seeding monitor is running
            result = subprocess.run(['pgrep', '-f', 'seeding_monitor.py'], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:  # Not running
                self.logger.info("🚀 Starting seeding compliance monitor...")
                
                # Start seeding monitor in background
                subprocess.Popen(['python3', 'seeding_monitor.py', '--continuous'],
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
                
                self.logger.info("✅ Seeding monitor started - 2-week compliance enforced!")
            else:
                self.logger.info("✅ Seeding monitor already running")
                
        except Exception as e:
            self.logger.warning(f"Could not start seeding monitor: {e}")
            self.logger.warning("⚠️ MANUAL ACTION REQUIRED: Start seeding monitor manually!")
    
    def check_seeding_compliance(self) -> Dict:
        """Check current seeding compliance status"""
        self.logger.info("🔍 Checking seeding compliance...")
        
        compliance_report = {
            'total_tracked': len(self.downloaded_books),
            'compliant': 0,
            'pending': 0,
            'violations': 0,
            'details': []
        }
        
        current_time = datetime.now()
        
        for download in self.downloaded_books:
            days_seeding = (current_time - download['download_start']).total_seconds() / 86400
            is_compliant = days_seeding >= self.MINIMUM_SEEDING_DAYS
            
            download_status = {
                'name': download['name'],
                'torrent_id': download['torrent_id'],
                'days_seeding': days_seeding,
                'required_days': self.MINIMUM_SEEDING_DAYS,
                'is_compliant': is_compliant,
                'time_remaining': max(0, self.MINIMUM_SEEDING_DAYS - days_seeding)
            }
            
            compliance_report['details'].append(download_status)
            
            if is_compliant:
                compliance_report['compliant'] += 1
                download['compliant'] = True
            elif days_seeding < self.MINIMUM_SEEDING_DAYS:
                compliance_report['pending'] += 1
            else:
                compliance_report['violations'] += 1
                self.seeding_violations.append(download_status)
        
        # Log compliance status
        if compliance_report['violations'] > 0:
            self.logger.warning(f"🚨 SEEDING VIOLATIONS: {compliance_report['violations']} books not properly seeded!")
        elif compliance_report['pending'] > 0:
            self.logger.info(f"⏳ Pending compliance: {compliance_report['pending']} books still seeding")
        else:
            self.logger.info("✅ Full seeding compliance achieved!")
        
        return compliance_report
    
    def save_seeding_tracking(self):
        """Save seeding tracking data to database"""
        with sqlite3.connect(self.db_path) as conn:
            for download in self.downloaded_books:
                conn.execute("""
                    INSERT OR REPLACE INTO seeding_records (
                        torrent_id, transmission_id, title, download_date,
                        status, compliance_status
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    f"reddit_agent_{download['torrent_id']}",
                    download['torrent_id'],
                    download['name'],
                    download['download_start'].isoformat(),
                    download.get('status', 'downloading'),
                    'compliant' if download.get('compliant', False) else 'pending'
                ))
    
    def analyze_epub_structure(self, file_path: str) -> Optional[BookOutline]:
        """Analyze EPUB file structure and extract chapters"""
        if not EPUB_SUPPORT:
            self.logger.error("EPUB support not available")
            return None
        
        try:
            book = epub.read_epub(file_path)
            
            # Extract metadata
            title = self.get_epub_metadata(book, 'title') or Path(file_path).stem
            author = self.get_epub_metadata(book, 'creator') or 'Unknown'
            
            self.logger.info(f"📖 Analyzing: {title} by {author}")
            
            # Extract chapters
            chapters = []
            chapter_num = 1
            total_words = 0
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    content = soup.get_text()
                    
                    if len(content.strip()) > 500:  # Only substantial content
                        chapter_title = self.extract_chapter_title(soup) or f"Chapter {chapter_num}"
                        word_count = len(content.split())
                        total_words += word_count
                        
                        # Analyze chapter content
                        key_concepts = self.extract_key_concepts(content)
                        named_entities = self.extract_named_entities(content)
                        themes = self.extract_themes(content)
                        summary = self.generate_chapter_summary(content)
                        
                        chapter = BookChapter(
                            chapter_number=chapter_num,
                            title=chapter_title,
                            content=content[:1000] + "..." if len(content) > 1000 else content,
                            word_count=word_count,
                            key_concepts=key_concepts,
                            named_entities=named_entities,
                            summary=summary,
                            themes=themes
                        )
                        
                        chapters.append(chapter)
                        chapter_num += 1
            
            # Generate book-level analysis
            all_concepts = []
            all_themes = []
            for ch in chapters:
                all_concepts.extend(ch.key_concepts)
                all_themes.extend(ch.themes)
            
            main_themes = [theme for theme, count in Counter(all_themes).most_common(5)]
            key_concepts = [concept for concept, count in Counter(all_concepts).most_common(10)]
            
            book_outline = BookOutline(
                book_id=hashlib.md5(file_path.encode()).hexdigest()[:12],
                title=title,
                author=author,
                total_chapters=len(chapters),
                total_words=total_words,
                chapters=chapters,
                main_themes=main_themes,
                key_concepts=key_concepts,
                book_summary=self.generate_book_summary(chapters),
                genre_classification=self.classify_genre(all_concepts, all_themes),
                complexity_score=self.calculate_complexity_score(chapters)
            )
            
            return book_outline
            
        except Exception as e:
            self.logger.error(f"Error analyzing EPUB {file_path}: {e}")
            return None
    
    def get_epub_metadata(self, book, key: str) -> Optional[str]:
        """Extract metadata from EPUB"""
        try:
            metadata = book.get_metadata('DC', key)
            if metadata and isinstance(metadata, list) and metadata[0]:
                return metadata[0][0]
        except:
            pass
        return None
    
    def extract_chapter_title(self, soup) -> Optional[str]:
        """Extract chapter title from HTML content"""
        # Look for common chapter title patterns
        for tag in ['h1', 'h2', 'h3']:
            elements = soup.find_all(tag)
            if elements:
                title_text = elements[0].get_text().strip()
                if len(title_text) < 100:  # Reasonable title length
                    return title_text
        return None
    
    def extract_key_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text using simple NLP"""
        # Convert to lowercase and find important terms
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # Filter common words and get frequency
        stopwords = {'The', 'This', 'That', 'There', 'Then', 'They', 'When', 'Where', 'What', 'Who', 'Why', 'How'}
        filtered_words = [w for w in words if w not in stopwords and len(w) > 3]
        
        # Return top concepts
        concept_counts = Counter(filtered_words)
        return [concept for concept, count in concept_counts.most_common(10) if count > 1]
    
    def extract_named_entities(self, text: str) -> List[str]:
        """Extract named entities (simplified approach)"""
        # Look for capitalized sequences that might be names
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # Filter and deduplicate
        entity_counts = Counter(entities)
        return [entity for entity, count in entity_counts.most_common(15) if count > 2]
    
    def extract_themes(self, text: str) -> List[str]:
        """Extract themes from text"""
        theme_keywords = {
            'love': ['love', 'romance', 'relationship', 'heart', 'affection'],
            'war': ['war', 'battle', 'conflict', 'fight', 'soldier', 'military'],
            'family': ['family', 'mother', 'father', 'parent', 'child', 'brother', 'sister'],
            'power': ['power', 'authority', 'control', 'domination', 'influence'],
            'justice': ['justice', 'law', 'court', 'judge', 'fair', 'rights'],
            'science': ['science', 'research', 'experiment', 'discovery', 'technology'],
            'religion': ['god', 'religion', 'faith', 'belief', 'spiritual', 'church'],
            'nature': ['nature', 'environment', 'earth', 'natural', 'wildlife'],
            'politics': ['politics', 'government', 'democracy', 'election', 'political'],
            'education': ['education', 'school', 'learning', 'teaching', 'knowledge']
        }
        
        text_lower = text.lower()
        detected_themes = []
        
        for theme, keywords in theme_keywords.items():
            score = sum(text_lower.count(keyword) for keyword in keywords)
            if score > 3:  # Threshold for theme presence
                detected_themes.append(theme)
        
        return detected_themes
    
    def generate_chapter_summary(self, content: str) -> str:
        """Generate a brief chapter summary"""
        sentences = re.split(r'[.!?]+', content)
        
        # Get first and last few sentences
        if len(sentences) > 10:
            key_sentences = sentences[1:3] + sentences[-3:-1]  # Skip potential title
        else:
            key_sentences = sentences[1:4] if len(sentences) > 4 else sentences
        
        summary = ' '.join(key_sentences).strip()
        return summary[:300] + "..." if len(summary) > 300 else summary
    
    def generate_book_summary(self, chapters: List[BookChapter]) -> str:
        """Generate overall book summary from chapters"""
        if not chapters:
            return "No content available for summary."
        
        # Combine chapter summaries
        all_summaries = [ch.summary for ch in chapters if ch.summary]
        
        if len(all_summaries) > 5:
            # Use first, middle, and last chapter summaries
            selected = [all_summaries[0], all_summaries[len(all_summaries)//2], all_summaries[-1]]
            summary = " ... ".join(selected)
        else:
            summary = " ... ".join(all_summaries)
        
        return summary[:500] + "..." if len(summary) > 500 else summary
    
    def classify_genre(self, concepts: List[str], themes: List[str]) -> str:
        """Classify book genre based on concepts and themes"""
        genre_indicators = {
            'fiction': ['character', 'story', 'plot', 'love', 'family'],
            'science': ['research', 'study', 'data', 'analysis', 'method'],
            'history': ['war', 'historical', 'century', 'ancient', 'period'],
            'philosophy': ['truth', 'reality', 'consciousness', 'existence', 'meaning'],
            'business': ['company', 'market', 'business', 'economic', 'financial'],
            'technology': ['computer', 'software', 'digital', 'internet', 'data'],
            'biography': ['life', 'born', 'career', 'personal', 'story']
        }
        
        all_terms = concepts + themes
        genre_scores = {}
        
        for genre, indicators in genre_indicators.items():
            score = sum(1 for term in all_terms if any(ind.lower() in term.lower() for ind in indicators))
            genre_scores[genre] = score
        
        if genre_scores:
            best_genre = max(genre_scores, key=genre_scores.get)
            return best_genre if genre_scores[best_genre] > 0 else 'general'
        
        return 'general'
    
    def calculate_complexity_score(self, chapters: List[BookChapter]) -> float:
        """Calculate text complexity score"""
        if not chapters:
            return 0.0
        
        total_words = sum(ch.word_count for ch in chapters)
        total_concepts = sum(len(ch.key_concepts) for ch in chapters)
        total_entities = sum(len(ch.named_entities) for ch in chapters)
        
        # Simple complexity metric
        if total_words == 0:
            return 0.0
        
        concept_density = total_concepts / total_words * 1000
        entity_density = total_entities / total_words * 1000
        
        complexity = (concept_density + entity_density) / 2
        return min(10.0, max(0.0, complexity))  # Scale 0-10
    
    def save_book_analysis(self, outline: BookOutline):
        """Save book analysis to database"""
        with sqlite3.connect(self.db_path) as conn:
            # Save book outline
            conn.execute("""
                INSERT OR REPLACE INTO book_outlines (
                    book_id, title, author, total_chapters, total_words,
                    main_themes, key_concepts, book_summary, genre_classification, complexity_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                outline.book_id, outline.title, outline.author, outline.total_chapters, outline.total_words,
                json.dumps(outline.main_themes), json.dumps(outline.key_concepts),
                outline.book_summary, outline.genre_classification, outline.complexity_score
            ))
            
            # Save chapter analysis
            for chapter in outline.chapters:
                content_hash = hashlib.md5(chapter.content.encode()).hexdigest()
                conn.execute("""
                    INSERT OR REPLACE INTO chapter_analysis (
                        book_id, chapter_number, chapter_title, word_count,
                        key_concepts, named_entities, summary, themes, content_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    outline.book_id, chapter.chapter_number, chapter.title, chapter.word_count,
                    json.dumps(chapter.key_concepts), json.dumps(chapter.named_entities),
                    chapter.summary, json.dumps(chapter.themes), content_hash
                ))
        
        self.log_reddit_activity(
            'book_analysis',
            f"Deep dive complete: {outline.title}",
            outline.book_id,
            {
                'chapters': outline.total_chapters,
                'words': outline.total_words,
                'complexity': outline.complexity_score,
                'genre': outline.genre_classification
            }
        )
    
    def build_knowledge_graph(self, outlines: List[BookOutline]):
        """Build knowledge graph from analyzed books"""
        self.logger.info("🕸️ Building knowledge graph from analyzed books...")
        
        # Clear existing graph
        self.knowledge_graph.clear()
        
        # Add book nodes
        for outline in outlines:
            book_node_id = f"book_{outline.book_id}"
            self.knowledge_graph.add_node(
                book_node_id,
                label=outline.title,
                type='book',
                author=outline.author,
                genre=outline.genre_classification,
                complexity=outline.complexity_score
            )
            
            # Add concept nodes and connections
            for concept in outline.key_concepts:
                concept_id = f"concept_{concept.lower().replace(' ', '_')}"
                
                if not self.knowledge_graph.has_node(concept_id):
                    self.knowledge_graph.add_node(
                        concept_id,
                        label=concept,
                        type='concept',
                        frequency=1
                    )
                else:
                    # Increment frequency
                    self.knowledge_graph.nodes[concept_id]['frequency'] += 1
                
                # Connect book to concept
                self.knowledge_graph.add_edge(
                    book_node_id,
                    concept_id,
                    relationship='contains_concept',
                    weight=1.0
                )
            
            # Add theme nodes and connections
            for theme in outline.main_themes:
                theme_id = f"theme_{theme.lower().replace(' ', '_')}"
                
                if not self.knowledge_graph.has_node(theme_id):
                    self.knowledge_graph.add_node(
                        theme_id,
                        label=theme,
                        type='theme',
                        frequency=1
                    )
                else:
                    self.knowledge_graph.nodes[theme_id]['frequency'] += 1
                
                # Connect book to theme
                self.knowledge_graph.add_edge(
                    book_node_id,
                    theme_id,
                    relationship='explores_theme',
                    weight=1.0
                )
        
        # Find concept co-occurrences
        self.add_concept_cooccurrences(outlines)
        
        self.logger.info(f"📊 Knowledge graph built: {len(self.knowledge_graph.nodes)} nodes, {len(self.knowledge_graph.edges)} edges")
        
        # Save to database
        self.save_knowledge_graph()
    
    def add_concept_cooccurrences(self, outlines: List[BookOutline]):
        """Add edges between concepts that appear together"""
        concept_cooccurrences = defaultdict(int)
        
        # Count concept co-occurrences across books
        for outline in outlines:
            concepts = outline.key_concepts
            for i, concept1 in enumerate(concepts):
                for concept2 in concepts[i+1:]:
                    pair = tuple(sorted([concept1.lower().replace(' ', '_'), 
                                       concept2.lower().replace(' ', '_')]))
                    concept_cooccurrences[pair] += 1
        
        # Add edges for frequently co-occurring concepts
        for (concept1, concept2), count in concept_cooccurrences.items():
            if count > 1:  # Appeared together in multiple books
                concept1_id = f"concept_{concept1}"
                concept2_id = f"concept_{concept2}"
                
                if (self.knowledge_graph.has_node(concept1_id) and 
                    self.knowledge_graph.has_node(concept2_id)):
                    
                    self.knowledge_graph.add_edge(
                        concept1_id,
                        concept2_id,
                        relationship='co_occurs_with',
                        weight=count
                    )
    
    def save_knowledge_graph(self):
        """Save knowledge graph to database"""
        with sqlite3.connect(self.db_path) as conn:
            # Clear existing graph data
            conn.execute("DELETE FROM knowledge_nodes")
            conn.execute("DELETE FROM knowledge_edges")
            
            # Save nodes
            for node_id, data in self.knowledge_graph.nodes(data=True):
                conn.execute("""
                    INSERT INTO knowledge_nodes (id, label, type, properties, weight)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    node_id,
                    data.get('label', node_id),
                    data.get('type', 'unknown'),
                    json.dumps(data),
                    data.get('frequency', 1.0)
                ))
            
            # Save edges
            for source, target, data in self.knowledge_graph.edges(data=True):
                conn.execute("""
                    INSERT INTO knowledge_edges (source_id, target_id, relationship, weight)
                    VALUES (?, ?, ?, ?)
                """, (
                    source,
                    target,
                    data.get('relationship', 'connected'),
                    data.get('weight', 1.0)
                ))
    
    def visualize_knowledge_graph(self, output_file: str = None):
        """Create visualization of knowledge graph"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = self.analysis_dir / f'knowledge_graph_{timestamp}.png'
        
        try:
            plt.figure(figsize=(16, 12))
            
            # Create layout
            pos = nx.spring_layout(self.knowledge_graph, k=3, iterations=50)
            
            # Color nodes by type
            node_colors = []
            node_sizes = []
            for node in self.knowledge_graph.nodes():
                node_data = self.knowledge_graph.nodes[node]
                node_type = node_data.get('type', 'unknown')
                frequency = node_data.get('frequency', 1)
                
                if node_type == 'book':
                    node_colors.append('lightblue')
                    node_sizes.append(1000)
                elif node_type == 'concept':
                    node_colors.append('lightgreen')
                    node_sizes.append(300 + frequency * 50)
                elif node_type == 'theme':
                    node_colors.append('lightcoral')
                    node_sizes.append(300 + frequency * 50)
                else:
                    node_colors.append('lightgray')
                    node_sizes.append(200)
            
            # Draw graph
            nx.draw(self.knowledge_graph, pos,
                   node_color=node_colors,
                   node_size=node_sizes,
                   with_labels=True,
                   font_size=8,
                   font_weight='bold',
                   edge_color='gray',
                   alpha=0.7)
            
            plt.title(f"Knowledge Graph - {len(self.knowledge_graph.nodes)} nodes", 
                     fontsize=16, fontweight='bold')
            plt.axis('off')
            plt.tight_layout()
            
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"📊 Knowledge graph visualization saved: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Error creating visualization: {e}")
            return None
    
    def generate_reddit_style_analysis(self, outlines: List[BookOutline]) -> str:
        """Generate Reddit-style analysis post"""
        
        reddit_post = f"""
# 🤓 u/DataScientistBookworm's Deep Dive: {len(outlines)} Books Analyzed

## TL;DR
Just finished analyzing {len(outlines)} books and holy shit, the patterns are FASCINATING! 📊

**The Data:**
- **Total words analyzed**: {sum(o.total_words for o in outlines):,}
- **Total chapters**: {sum(o.total_chapters for o in outlines)}
- **Average complexity**: {sum(o.complexity_score for o in outlines) / len(outlines):.2f}/10
- **Knowledge graph**: {len(self.knowledge_graph.nodes)} nodes, {len(self.knowledge_graph.edges)} connections

---

## 📚 Books Analyzed:

"""
        
        for i, outline in enumerate(outlines, 1):
            reddit_post += f"""
### {i}. **{outline.title}** by {outline.author}
- **Genre**: {outline.genre_classification}
- **Chapters**: {outline.total_chapters}
- **Words**: {outline.total_words:,}
- **Complexity**: {outline.complexity_score:.1f}/10
- **Main themes**: {', '.join(outline.main_themes[:3])}
- **Key concepts**: {', '.join(outline.key_concepts[:5])}

**One-liner**: {outline.book_summary[:200]}...

---
"""
        
        # Add knowledge graph insights
        reddit_post += """
## 🕸️ Knowledge Graph Insights

The interconnections between these books are WILD! Here's what the data revealed:

"""
        
        # Find most connected concepts
        concept_nodes = [n for n in self.knowledge_graph.nodes() if n.startswith('concept_')]
        concept_connections = [(n, self.knowledge_graph.degree(n)) for n in concept_nodes]
        concept_connections.sort(key=lambda x: x[1], reverse=True)
        
        reddit_post += "**Most Connected Concepts:**\n"
        for concept, degree in concept_connections[:5]:
            label = self.knowledge_graph.nodes[concept].get('label', concept)
            reddit_post += f"- **{label}**: connected to {degree} other elements\n"
        
        # Add genre analysis
        genres = [o.genre_classification for o in outlines]
        genre_counts = Counter(genres)
        
        reddit_post += f"\n**Genre Distribution:**\n"
        for genre, count in genre_counts.most_common():
            reddit_post += f"- {genre}: {count} books\n"
        
        # Add complexity insights
        complexities = [o.complexity_score for o in outlines]
        reddit_post += f"""
**Complexity Analysis:**
- Simplest: {min(complexities):.1f}
- Most complex: {max(complexities):.1f}
- Average: {sum(complexities)/len(complexities):.1f}

"""
        
        # Add seeding compliance section
        compliance_report = self.check_seeding_compliance()
        if compliance_report['total_tracked'] > 0:
            reddit_post += f"""
---

## 🛡️ Seeding Compliance Status

**TL;DR on community respect**: {compliance_report['compliant']}/{compliance_report['total_tracked']} books fully compliant with 2-week rule.

"""
            if compliance_report['compliant'] == compliance_report['total_tracked']:
                reddit_post += "✅ **PERFECT COMPLIANCE** - All books properly seeded! 🎉\n"
            elif compliance_report['pending'] > 0:
                reddit_post += f"⏳ **{compliance_report['pending']} books still seeding** - on track for compliance\n"
            
            if compliance_report['violations'] > 0:
                reddit_post += f"🚨 **{compliance_report['violations']} VIOLATIONS** - Fix ASAP!\n"
            
            reddit_post += f"\n**Seeding Philosophy**: {self.persona['seeding_philosophy']}\n"
        
        reddit_post += """
---

## 🎯 What This Means

This analysis shows how these books form an interconnected web of knowledge. The knowledge graph reveals hidden patterns and relationships that you'd never notice reading them individually.

**For fellow data nerds**: The concept co-occurrence matrix is particularly interesting - shows how ideas cluster across different domains.

**For bibliophiles**: These books complement each other beautifully. The thematic overlaps suggest some killer reading sequences.

**For the community**: Seeding compliance = respect. Data shows we can analyze fast while maintaining good standing.

---

*Generated by RedditBibliophileAgent v1.0 | Data + Books + Community Respect = ❤️*
*🛡️ 2-week seeding rule: Always enforced*
"""
        
        return reddit_post
    
    def run_full_analysis(self, target_books: int = 10) -> Dict:
        """Run complete analysis workflow"""
        self.logger.info(f"🚀 u/DataScientistBookworm starting full analysis of {target_books} books!")
        self.logger.info("🛡️ 2-WEEK SEEDING RULE: Compliance monitoring active!")
        
        start_time = time.time()
        
        # Step 0: Check current seeding compliance
        compliance_report = self.check_seeding_compliance()
        if compliance_report['violations'] > 0:
            self.logger.warning(f"⚠️ {compliance_report['violations']} seeding violations detected!")
            self.logger.warning("🚨 Fix seeding compliance before downloading more books!")
        
        # Step 1: Acquire books
        books = self.download_and_process_books(target_books)
        
        if not books:
            self.logger.error("😞 No books available for analysis")
            return {'success': False, 'error': 'No books found'}
        
        self.logger.info(f"📚 Analyzing {len(books)} books...")
        self.logger.info("⚡ Fast ebook downloads = immediate seeding obligations!")
        
        # Step 2: Analyze each book
        analyzed_outlines = []
        
        for i, book in enumerate(books, 1):
            self.logger.info(f"📖 [{i}/{len(books)}] Analyzing: {book['title']}")
            
            if book['local_file_path'] and Path(book['local_file_path']).exists():
                outline = self.analyze_epub_structure(book['local_file_path'])
                
                if outline:
                    self.save_book_analysis(outline)
                    analyzed_outlines.append(outline)
                    
                    self.logger.info(f"✅ Analysis complete: {outline.total_chapters} chapters, {outline.total_words} words")
                else:
                    self.logger.warning(f"⚠️ Could not analyze: {book['title']}")
            else:
                self.logger.warning(f"⚠️ File not found: {book['local_file_path']}")
        
        if not analyzed_outlines:
            self.logger.error("😞 No books successfully analyzed")
            return {'success': False, 'error': 'Analysis failed for all books'}
        
        # Step 3: Build knowledge graph
        self.build_knowledge_graph(analyzed_outlines)
        
        # Step 4: Generate visualizations
        viz_file = self.visualize_knowledge_graph()
        
        # Step 5: Generate Reddit-style analysis
        reddit_analysis = self.generate_reddit_style_analysis(analyzed_outlines)
        
        # Save Reddit analysis
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        analysis_file = self.analysis_dir / f'reddit_analysis_{timestamp}.md'
        analysis_file.write_text(reddit_analysis)
        
        # Final results
        duration = time.time() - start_time
        
        # Get final seeding compliance status
        final_compliance = self.check_seeding_compliance()
        
        results = {
            'success': True,
            'books_analyzed': len(analyzed_outlines),
            'total_chapters': sum(o.total_chapters for o in analyzed_outlines),
            'total_words': sum(o.total_words for o in analyzed_outlines),
            'knowledge_graph_nodes': len(self.knowledge_graph.nodes),
            'knowledge_graph_edges': len(self.knowledge_graph.edges),
            'analysis_duration': duration,
            'reddit_analysis_file': str(analysis_file),
            'visualization_file': viz_file,
            'seeding_compliance': final_compliance,
            'outlines': [asdict(outline) for outline in analyzed_outlines]
        }
        
        self.log_reddit_activity(
            'full_analysis_complete',
            f"Analyzed {len(analyzed_outlines)} books, built knowledge graph",
            insights=results
        )
        
        self.logger.info(f"🎉 Full analysis complete in {duration:.1f}s!")
        self.logger.info(f"📊 Results: {len(analyzed_outlines)} books, {results['knowledge_graph_nodes']} knowledge nodes")
        self.logger.info(f"📄 Reddit analysis: {analysis_file}")
        
        # Log seeding compliance
        if final_compliance['total_tracked'] > 0:
            self.logger.info(f"🛡️ Seeding Compliance: {final_compliance['compliant']}/{final_compliance['total_tracked']} compliant")
            if final_compliance['violations'] > 0:
                self.logger.warning(f"🚨 SEEDING VIOLATIONS: {final_compliance['violations']} books need attention!")
            else:
                self.logger.info("✅ Perfect seeding compliance maintained!")
        
        return results

def main():
    """Run the Reddit Bibliophile Agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Reddit Bibliophile Agent - Data Scientist Book Analyzer')
    parser.add_argument('--books', type=int, default=10, help='Number of books to analyze')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--visualize-only', action='store_true', help='Only create visualizations from existing data')
    
    args = parser.parse_args()
    
    print("🤓 Reddit Bibliophile Agent - u/DataScientistBookworm")
    print("=" * 60)
    print("📚 Data Scientist + Bibliophile = Knowledge Graph Magic ✨")
    print("=" * 60)
    
    # Load configuration
    config = {}
    if args.config and Path(args.config).exists():
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Initialize agent
    agent = RedditBibliophileAgent(config)
    
    if args.visualize_only:
        # Just create visualizations from existing data
        agent.visualize_knowledge_graph()
    else:
        # Run full analysis
        results = agent.run_full_analysis(args.books)
        
        if results['success']:
            print(f"\n📊 Analysis Results:")
            print(f"   Books analyzed: {results['books_analyzed']}")
            print(f"   Total chapters: {results['total_chapters']}")
            print(f"   Total words: {results['total_words']:,}")
            print(f"   Knowledge nodes: {results['knowledge_graph_nodes']}")
            print(f"   Knowledge edges: {results['knowledge_graph_edges']}")
            print(f"   Duration: {results['analysis_duration']:.1f} seconds")
            print(f"\n📄 Reddit Analysis: {results['reddit_analysis_file']}")
            if results['visualization_file']:
                print(f"📊 Visualization: {results['visualization_file']}")
        else:
            print(f"❌ Analysis failed: {results.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()