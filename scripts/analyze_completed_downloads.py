#!/usr/bin/env python3
"""
Completed Downloads Analyzer
Analyzes existing ebook downloads and extracts metadata for LibraryOfBabel integration
"""

import os
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime
import hashlib
import re

try:
    import ebooklib
    from ebooklib import epub
    EPUB_SUPPORT = True
except ImportError:
    EPUB_SUPPORT = False
    print("⚠️ ebooklib not available - install with: pip install EbookLib")

try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("⚠️ PyPDF2 not available - install with: pip install PyPDF2")

@dataclass
class EbookMetadata:
    """Extracted ebook metadata"""
    file_path: str
    filename: str
    file_size_mb: float
    format: str
    title: Optional[str] = None
    author: Optional[str] = None
    language: Optional[str] = None
    publisher: Optional[str] = None
    publication_date: Optional[str] = None
    isbn: Optional[str] = None
    description: Optional[str] = None
    page_count: Optional[int] = None
    file_hash: Optional[str] = None
    extraction_timestamp: str = None
    
    def __post_init__(self):
        if not self.extraction_timestamp:
            self.extraction_timestamp = datetime.now().isoformat()

class EbookAnalyzer:
    """Analyzes ebook files and extracts comprehensive metadata"""
    
    def __init__(self, completed_downloads_dir: str, db_path: str = "./audiobook_ebook_tracker.db"):
        self.completed_downloads_dir = Path(completed_downloads_dir)
        self.db_path = db_path
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Supported formats
        self.supported_formats = {
            '.epub': self.analyze_epub,
            '.pdf': self.analyze_pdf,
            '.mobi': self.analyze_mobi,
            '.azw': self.analyze_azw,
            '.txt': self.analyze_txt
        }
    
    def setup_logging(self):
        """Setup logging for analyzer"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ebook_analyzer.log'),
                logging.StreamHandler()
            ]
        )
    
    def analyze_all_downloads(self) -> Dict:
        """Analyze all ebook files in completed downloads directory"""
        self.logger.info(f"🔍 Analyzing ebooks in: {self.completed_downloads_dir}")
        
        if not self.completed_downloads_dir.exists():
            self.logger.error(f"Directory does not exist: {self.completed_downloads_dir}")
            return {"error": "Directory not found", "analyzed_files": []}
        
        # Find all ebook files
        ebook_files = []
        for extension in self.supported_formats.keys():
            ebook_files.extend(self.completed_downloads_dir.rglob(f'*{extension}'))
        
        self.logger.info(f"📚 Found {len(ebook_files)} ebook files")
        
        analyzed_files = []
        analysis_stats = {
            'total_files': len(ebook_files),
            'successful_analysis': 0,
            'failed_analysis': 0,
            'by_format': {},
            'total_size_mb': 0,
            'potential_matches': []
        }
        
        for ebook_file in ebook_files:
            try:
                self.logger.info(f"📖 Analyzing: {ebook_file.name}")
                
                metadata = self.analyze_ebook(ebook_file)
                if metadata:
                    analyzed_files.append(metadata)
                    analysis_stats['successful_analysis'] += 1
                    analysis_stats['total_size_mb'] += metadata.file_size_mb
                    
                    # Track by format
                    format_key = metadata.format.lower()
                    if format_key not in analysis_stats['by_format']:
                        analysis_stats['by_format'][format_key] = 0
                    analysis_stats['by_format'][format_key] += 1
                    
                    # Try to match with audiobooks
                    potential_matches = self.find_audiobook_matches(metadata)
                    if potential_matches:
                        analysis_stats['potential_matches'].extend(potential_matches)
                        self.logger.info(f"🎯 Found {len(potential_matches)} potential audiobook matches")
                
                else:
                    analysis_stats['failed_analysis'] += 1
                    
            except Exception as e:
                self.logger.error(f"❌ Error analyzing {ebook_file.name}: {e}")
                analysis_stats['failed_analysis'] += 1
        
        # Save analysis results
        results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'directory_analyzed': str(self.completed_downloads_dir),
            'statistics': analysis_stats,
            'analyzed_files': [self._metadata_to_dict(meta) for meta in analyzed_files]
        }
        
        output_file = f"ebook_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        self.logger.info(f"💾 Analysis saved to: {output_file}")
        
        if analysis_stats['total_files'] > 0:
            success_rate = analysis_stats['successful_analysis']/analysis_stats['total_files']*100
            self.logger.info(f"📊 Success rate: {analysis_stats['successful_analysis']}/{analysis_stats['total_files']} ({success_rate:.1f}%)")
        else:
            self.logger.info("📊 No files found to analyze")
        
        return results
    
    def analyze_ebook(self, file_path: Path) -> Optional[EbookMetadata]:
        """Analyze single ebook file and extract metadata"""
        try:
            # Basic file info
            file_stats = file_path.stat()
            file_size_mb = file_stats.st_size / (1024 * 1024)
            file_format = file_path.suffix.lower()[1:]  # Remove the dot
            
            # Calculate file hash for deduplication
            file_hash = self.calculate_file_hash(file_path)
            
            # Initialize metadata
            metadata = EbookMetadata(
                file_path=str(file_path),
                filename=file_path.name,
                file_size_mb=file_size_mb,
                format=file_format,
                file_hash=file_hash
            )
            
            # Extract format-specific metadata
            extension = file_path.suffix.lower()
            if extension in self.supported_formats:
                format_analyzer = self.supported_formats[extension]
                metadata = format_analyzer(file_path, metadata)
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error analyzing {file_path.name}: {e}")
            return None
    
    def analyze_epub(self, file_path: Path, metadata: EbookMetadata) -> EbookMetadata:
        """Extract metadata from EPUB file"""
        if not EPUB_SUPPORT:
            self.logger.warning(f"EPUB support not available for {file_path.name}")
            return metadata
        
        try:
            book = epub.read_epub(str(file_path))
            
            # Extract metadata from EPUB
            metadata.title = book.get_metadata('DC', 'title')
            metadata.author = book.get_metadata('DC', 'creator')
            metadata.language = book.get_metadata('DC', 'language')
            metadata.publisher = book.get_metadata('DC', 'publisher')
            metadata.publication_date = book.get_metadata('DC', 'date')
            metadata.description = book.get_metadata('DC', 'description')
            
            # Extract first values if multiple
            if metadata.title and isinstance(metadata.title, list):
                metadata.title = metadata.title[0][0] if metadata.title[0] else None
            if metadata.author and isinstance(metadata.author, list):
                metadata.author = metadata.author[0][0] if metadata.author[0] else None
            if metadata.language and isinstance(metadata.language, list):
                metadata.language = metadata.language[0][0] if metadata.language[0] else None
            if metadata.publisher and isinstance(metadata.publisher, list):
                metadata.publisher = metadata.publisher[0][0] if metadata.publisher[0] else None
            if metadata.publication_date and isinstance(metadata.publication_date, list):
                metadata.publication_date = metadata.publication_date[0][0] if metadata.publication_date[0] else None
            if metadata.description and isinstance(metadata.description, list):
                metadata.description = metadata.description[0][0] if metadata.description[0] else None
            
            # Try to estimate page count from content
            try:
                content_items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
                estimated_pages = len(content_items) * 10  # Rough estimate
                metadata.page_count = estimated_pages
            except:
                pass
                
        except Exception as e:
            self.logger.warning(f"Error extracting EPUB metadata from {file_path.name}: {e}")
        
        return metadata
    
    def analyze_pdf(self, file_path: Path, metadata: EbookMetadata) -> EbookMetadata:
        """Extract metadata from PDF file"""
        if not PDF_SUPPORT:
            self.logger.warning(f"PDF support not available for {file_path.name}")
            return metadata
        
        try:
            with open(file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                # Extract metadata
                if pdf_reader.metadata:
                    metadata.title = pdf_reader.metadata.get('/Title')
                    metadata.author = pdf_reader.metadata.get('/Author')
                    metadata.publisher = pdf_reader.metadata.get('/Producer')
                    
                    # Extract creation date
                    creation_date = pdf_reader.metadata.get('/CreationDate')
                    if creation_date:
                        metadata.publication_date = str(creation_date)
                
                # Page count
                metadata.page_count = len(pdf_reader.pages)
                
        except Exception as e:
            self.logger.warning(f"Error extracting PDF metadata from {file_path.name}: {e}")
        
        return metadata
    
    def analyze_mobi(self, file_path: Path, metadata: EbookMetadata) -> EbookMetadata:
        """Extract metadata from MOBI file (basic file parsing)"""
        try:
            # Basic filename parsing for MOBI files
            # MOBI parsing requires specialized libraries
            filename = file_path.stem
            
            # Try to extract title and author from filename patterns
            # Common patterns: "Title - Author.mobi" or "Author - Title.mobi"
            if ' - ' in filename:
                parts = filename.split(' - ', 1)
                # Heuristic: if first part looks like author name (contains comma or is short)
                if ',' in parts[0] or len(parts[0].split()) <= 2:
                    metadata.author = parts[0]
                    metadata.title = parts[1]
                else:
                    metadata.title = parts[0]
                    metadata.author = parts[1]
            else:
                metadata.title = filename
                
        except Exception as e:
            self.logger.warning(f"Error analyzing MOBI file {file_path.name}: {e}")
        
        return metadata
    
    def analyze_azw(self, file_path: Path, metadata: EbookMetadata) -> EbookMetadata:
        """Extract metadata from AZW file (similar to MOBI)"""
        return self.analyze_mobi(file_path, metadata)  # Similar approach
    
    def analyze_txt(self, file_path: Path, metadata: EbookMetadata) -> EbookMetadata:
        """Extract metadata from TXT file"""
        try:
            # Read first few lines to try to extract title/author
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_lines = [f.readline().strip() for _ in range(10)]
            
            # Look for title in first few lines
            for line in first_lines:
                if line and len(line) < 100:  # Likely title
                    metadata.title = line
                    break
            
            # If no title found, use filename
            if not metadata.title:
                metadata.title = file_path.stem
                
        except Exception as e:
            self.logger.warning(f"Error analyzing TXT file {file_path.name}: {e}")
        
        return metadata
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file for deduplication"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.logger.warning(f"Error calculating hash for {file_path.name}: {e}")
            return None
    
    def find_audiobook_matches(self, ebook_metadata: EbookMetadata) -> List[Dict]:
        """Find potential audiobook matches for ebook"""
        if not ebook_metadata.title or not ebook_metadata.author:
            return []
        
        matches = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clean ebook metadata for matching
                clean_ebook_title = self.clean_for_matching(ebook_metadata.title)
                clean_ebook_author = self.clean_for_matching(ebook_metadata.author)
                
                # Search for similar audiobooks
                search_query = """
                    SELECT album_id, title, author, clean_title, clean_author, duration_hours
                    FROM audiobooks
                    WHERE LOWER(clean_title) LIKE ? OR LOWER(clean_author) LIKE ?
                    OR LOWER(title) LIKE ? OR LOWER(author) LIKE ?
                """
                
                title_pattern = f"%{clean_ebook_title.lower()}%"
                author_pattern = f"%{clean_ebook_author.lower()}%"
                
                cursor.execute(search_query, (title_pattern, author_pattern, title_pattern, author_pattern))
                
                for row in cursor.fetchall():
                    audiobook_id, ab_title, ab_author, ab_clean_title, ab_clean_author, duration = row
                    
                    # Calculate match confidence
                    confidence = self.calculate_match_confidence(
                        clean_ebook_title, clean_ebook_author,
                        ab_clean_title or ab_title, ab_clean_author or ab_author
                    )
                    
                    if confidence > 0.5:  # Only include likely matches
                        matches.append({
                            'audiobook_id': audiobook_id,
                            'audiobook_title': ab_title,
                            'audiobook_author': ab_author,
                            'ebook_title': ebook_metadata.title,
                            'ebook_author': ebook_metadata.author,
                            'match_confidence': confidence,
                            'ebook_file_path': ebook_metadata.file_path
                        })
                
                # Sort by confidence
                matches.sort(key=lambda x: x['match_confidence'], reverse=True)
                
        except Exception as e:
            self.logger.error(f"Error finding audiobook matches: {e}")
        
        return matches[:5]  # Return top 5 matches
    
    def clean_for_matching(self, text: str) -> str:
        """Clean text for better matching"""
        if not text:
            return ""
        
        # Remove common noise
        text = re.sub(r'\\s*\\(.*?\\)', '', text)  # Remove parentheses content
        text = re.sub(r'\\s*\\[.*?\\]', '', text)  # Remove bracket content
        text = re.sub(r'\\s*[:-].*$', '', text)    # Remove subtitle after colon/dash
        text = re.sub(r'\\s+', ' ', text)          # Normalize whitespace
        
        return text.strip()
    
    def calculate_match_confidence(self, ebook_title: str, ebook_author: str, 
                                 audiobook_title: str, audiobook_author: str) -> float:
        """Calculate confidence score for ebook-audiobook match"""
        
        # Tokenize for comparison
        ebook_title_tokens = set(self.clean_for_matching(ebook_title).lower().split())
        ebook_author_tokens = set(self.clean_for_matching(ebook_author).lower().split())
        audiobook_title_tokens = set(self.clean_for_matching(audiobook_title).lower().split())
        audiobook_author_tokens = set(self.clean_for_matching(audiobook_author).lower().split())
        
        # Calculate Jaccard similarity
        title_similarity = self.jaccard_similarity(ebook_title_tokens, audiobook_title_tokens)
        author_similarity = self.jaccard_similarity(ebook_author_tokens, audiobook_author_tokens)
        
        # Weighted combination
        confidence = (title_similarity * 0.7) + (author_similarity * 0.3)
        
        return min(1.0, max(0.0, confidence))
    
    def jaccard_similarity(self, set1: set, set2: set) -> float:
        """Calculate Jaccard similarity between two sets"""
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _metadata_to_dict(self, metadata: EbookMetadata) -> Dict:
        """Convert metadata object to dictionary"""
        return {
            'file_path': metadata.file_path,
            'filename': metadata.filename,
            'file_size_mb': metadata.file_size_mb,
            'format': metadata.format,
            'title': metadata.title,
            'author': metadata.author,
            'language': metadata.language,
            'publisher': metadata.publisher,
            'publication_date': metadata.publication_date,
            'isbn': metadata.isbn,
            'description': metadata.description,
            'page_count': metadata.page_count,
            'file_hash': metadata.file_hash,
            'extraction_timestamp': metadata.extraction_timestamp
        }

def main():
    """Run ebook analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze completed ebook downloads')
    parser.add_argument('--directory', 
                       default='/Users/weixiangzhang/Media Holding Station/Ebooks',
                       help='Directory containing completed downloads')
    parser.add_argument('--db-path', 
                       default='./audiobook_ebook_tracker.db',
                       help='Path to audiobook tracking database')
    
    args = parser.parse_args()
    
    print("📚 Ebook Download Analyzer")
    print("=" * 40)
    
    analyzer = EbookAnalyzer(args.directory, args.db_path)
    results = analyzer.analyze_all_downloads()
    
    print(f"\\n📊 Analysis Summary:")
    print(f"   Total files analyzed: {results['statistics']['total_files']}")
    print(f"   Successful extractions: {results['statistics']['successful_analysis']}")
    print(f"   Failed extractions: {results['statistics']['failed_analysis']}")
    print(f"   Total size: {results['statistics']['total_size_mb']:.1f} MB")
    print(f"   Potential audiobook matches: {len(results['statistics']['potential_matches'])}")
    print(f"   Formats found: {list(results['statistics']['by_format'].keys())}")

if __name__ == "__main__":
    main()