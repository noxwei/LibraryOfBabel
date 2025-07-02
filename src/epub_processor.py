#!/usr/bin/env python3
"""
EPUB Processor for LibraryOfBabel
=================================

Extracts text content, metadata, and structure from EPUB files.
Handles multiple EPUB format variations with robust error handling.

Author: Librarian Agent
Version: 1.0
"""

import os
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass
from bs4 import BeautifulSoup
import json
from urllib.parse import unquote

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ChapterInfo:
    """Information about a chapter or section."""
    title: str
    content: str
    chapter_number: Optional[int]
    section_number: Optional[int]
    word_count: int
    file_path: str
    spine_order: int

@dataclass
class BookMetadata:
    """Metadata extracted from EPUB."""
    title: str
    author: str
    publisher: Optional[str]
    publication_date: Optional[str]
    language: str
    isbn: Optional[str]
    description: Optional[str]
    subject: Optional[str]
    total_chapters: int
    total_words: int
    file_path: str

class EPUBProcessor:
    """Main EPUB processing class."""
    
    def __init__(self, config_path: str = None):
        """Initialize the processor with optional config."""
        self.config = self._load_config(config_path)
        self.namespaces = {
            'dc': 'http://purl.org/dc/elements/1.1/',
            'opf': 'http://www.idpf.org/2007/opf',
            'xhtml': 'http://www.w3.org/1999/xhtml',
            'epub': 'http://www.idpf.org/2007/ops'
        }
        
    def _load_config(self, config_path: str) -> Dict:
        """Load processing configuration."""
        default_config = {
            'min_chapter_words': 100,
            'max_chapter_words': 50000,
            'skip_elements': ['script', 'style', 'head', 'meta'],
            'text_elements': ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span', 'blockquote'],
            'chapter_indicators': ['chapter', 'ch ', 'part', 'section', 'book'],
            'exclude_files': ['cover', 'toc', 'copyright', 'title', 'contents']
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
                
        return default_config
    
    def process_epub(self, epub_path: str) -> Tuple[BookMetadata, List[ChapterInfo]]:
        """
        Process an EPUB file and extract metadata and content.
        
        Args:
            epub_path: Path to the EPUB file or extracted directory
            
        Returns:
            Tuple of (metadata, list of chapters)
        """
        logger.info(f"Processing EPUB: {epub_path}")
        
        try:
            # Check if it's a directory (extracted EPUB) or ZIP file
            if os.path.isdir(epub_path):
                return self._process_epub_directory(epub_path)
            else:
                return self._process_epub_zip(epub_path)
                
        except Exception as e:
            logger.error(f"Failed to process EPUB {epub_path}: {e}")
            raise
    
    def _process_epub_zip(self, epub_path: str) -> Tuple[BookMetadata, List[ChapterInfo]]:
        """Process EPUB ZIP file."""
        with zipfile.ZipFile(epub_path, 'r') as epub_zip:
            # Find and parse the OPF file
            container_path = 'META-INF/container.xml'
            if container_path not in epub_zip.namelist():
                raise ValueError("Invalid EPUB: Missing container.xml")
            
            container_content = epub_zip.read(container_path)
            opf_path = self._extract_opf_path(container_content)
            
            if not opf_path or opf_path not in epub_zip.namelist():
                raise ValueError("Invalid EPUB: OPF file not found")
            
            opf_content = epub_zip.read(opf_path)
            opf_dir = os.path.dirname(opf_path)
            
            # Parse OPF for metadata and manifest
            metadata, manifest, spine = self._parse_opf(opf_content)
            
            # Extract text content from spine files
            chapters = self._extract_chapters_zip(epub_zip, manifest, spine, opf_dir)
            
            # Create book metadata
            book_metadata = self._create_book_metadata(metadata, chapters, epub_path)
            
            logger.info(f"Successfully processed: {book_metadata.title} by {book_metadata.author}")
            logger.info(f"Extracted {len(chapters)} chapters, {book_metadata.total_words} words")
            
            return book_metadata, chapters
    
    def _process_epub_directory(self, epub_dir: str) -> Tuple[BookMetadata, List[ChapterInfo]]:
        """Process extracted EPUB directory."""
        # Find and parse the OPF file
        container_path = Path(epub_dir, 'META-INF', 'container.xml')
        if not os.path.exists(container_path):
            raise ValueError("Invalid EPUB: Missing container.xml")
        
        with open(container_path, 'rb') as f:
            container_content = f.read()
        
        opf_path = self._extract_opf_path(container_content)
        if not opf_path:
            raise ValueError("Invalid EPUB: Could not find OPF path")
        
        opf_full_path = Path(epub_dir, opf_path)
        if not os.path.exists(opf_full_path):
            raise ValueError("Invalid EPUB: OPF file not found")
        
        with open(opf_full_path, 'rb') as f:
            opf_content = f.read()
        
        opf_dir = os.path.dirname(opf_path)
        
        # Parse OPF for metadata and manifest
        metadata, manifest, spine = self._parse_opf(opf_content)
        
        # Extract text content from spine files
        chapters = self._extract_chapters_dir(epub_dir, manifest, spine, opf_dir)
        
        # Create book metadata
        book_metadata = self._create_book_metadata(metadata, chapters, epub_dir)
        
        logger.info(f"Successfully processed: {book_metadata.title} by {book_metadata.author}")
        logger.info(f"Extracted {len(chapters)} chapters, {book_metadata.total_words} words")
        
        return book_metadata, chapters
    
    def _extract_opf_path(self, container_content: bytes) -> str:
        """Extract OPF file path from container.xml."""
        try:
            root = ET.fromstring(container_content)
            for rootfile in root.findall('.//container:rootfile', {'container': 'urn:oasis:names:tc:opendocument:xmlns:container'}):
                return rootfile.get('full-path')
            
            # Fallback: try without namespace
            root = ET.fromstring(container_content)
            for rootfile in root.findall('.//rootfile'):
                return rootfile.get('full-path')
                
        except ET.ParseError as e:
            logger.error(f"Failed to parse container.xml: {e}")
            
        return None
    
    def _parse_opf(self, opf_content: bytes) -> Tuple[Dict, Dict, List]:
        """Parse OPF file for metadata, manifest, and spine."""
        try:
            root = ET.fromstring(opf_content)
            
            # Extract metadata
            metadata = self._extract_metadata(root)
            
            # Extract manifest (file list)
            manifest = self._extract_manifest(root)
            
            # Extract spine (reading order)
            spine = self._extract_spine(root)
            
            return metadata, manifest, spine
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse OPF file: {e}")
            raise
    
    def _extract_metadata(self, opf_root: ET.Element) -> Dict:
        """Extract metadata from OPF."""
        metadata = {}
        
        # Find metadata element
        metadata_elem = opf_root.find('.//{http://www.idpf.org/2007/opf}metadata')
        if metadata_elem is None:
            metadata_elem = opf_root.find('.//metadata')
        
        if metadata_elem is not None:
            # Dublin Core elements
            for elem in metadata_elem:
                tag = elem.tag.split('}')[-1]  # Remove namespace
                
                if tag in ['title', 'creator', 'publisher', 'date', 'language', 'description', 'subject']:
                    text = elem.text.strip() if elem.text else ''
                    if text:
                        if tag == 'creator':
                            metadata['author'] = text
                        elif tag == 'date':
                            metadata['publication_date'] = text
                        else:
                            metadata[tag] = text
                
                elif tag == 'identifier':
                    # Handle ISBN and other identifiers
                    text = elem.text.strip() if elem.text else ''
                    if text and ('isbn' in text.lower() or 'isbn' in elem.get('scheme', '').lower()):
                        metadata['isbn'] = text
        
        return metadata
    
    def _extract_manifest(self, opf_root: ET.Element) -> Dict:
        """Extract manifest (file list) from OPF."""
        manifest = {}
        
        manifest_elem = opf_root.find('.//{http://www.idpf.org/2007/opf}manifest')
        if manifest_elem is None:
            manifest_elem = opf_root.find('.//manifest')
        
        if manifest_elem is not None:
            for item in manifest_elem.findall('.//{http://www.idpf.org/2007/opf}item'):
                if item is None:
                    item = manifest_elem.findall('.//item')
                    
                item_id = item.get('id')
                href = item.get('href')
                media_type = item.get('media-type', '')
                
                if item_id and href:
                    manifest[item_id] = {
                        'href': href,
                        'media_type': media_type
                    }
        
        return manifest
    
    def _extract_spine(self, opf_root: ET.Element) -> List:
        """Extract spine (reading order) from OPF."""
        spine = []
        
        spine_elem = opf_root.find('.//{http://www.idpf.org/2007/opf}spine')
        if spine_elem is None:
            spine_elem = opf_root.find('.//spine')
        
        if spine_elem is not None:
            for itemref in spine_elem.findall('.//{http://www.idpf.org/2007/opf}itemref'):
                if itemref is None:
                    itemref = spine_elem.findall('.//itemref')
                    
                idref = itemref.get('idref')
                linear = itemref.get('linear', 'yes')
                
                if idref and linear != 'no':
                    spine.append(idref)
        
        return spine
    
    def _extract_chapters_zip(self, epub_zip: zipfile.ZipFile, manifest: Dict, 
                             spine: List, opf_dir: str) -> List[ChapterInfo]:
        """Extract text content from EPUB chapters."""
        chapters = []
        
        for order, item_id in enumerate(spine):
            if item_id not in manifest:
                continue
                
            item_info = manifest[item_id]
            
            # Only process HTML/XHTML files
            if not any(mt in item_info['media_type'] for mt in ['html', 'xhtml']):
                continue
            
            # Construct full path
            file_path = item_info['href']
            if opf_dir:
                file_path = f"{opf_dir}/{file_path}"
            
            # Skip if file should be excluded
            filename = os.path.basename(file_path).lower()
            if any(exclude in filename for exclude in self.config['exclude_files']):
                continue
            
            try:
                # Read and process the file
                if file_path in epub_zip.namelist():
                    content = epub_zip.read(file_path).decode('utf-8', errors='ignore')
                    
                    # Extract text content
                    text_content, title = self._extract_text_from_html(content)
                    
                    # Skip if content is too short
                    word_count = len(text_content.split())
                    if word_count < self.config['min_chapter_words']:
                        continue
                    
                    # Determine chapter number
                    chapter_num = self._extract_chapter_number(title, filename, order)
                    
                    chapter = ChapterInfo(
                        title=title or f"Chapter {order + 1}",
                        content=text_content,
                        chapter_number=chapter_num,
                        section_number=None,
                        word_count=word_count,
                        file_path=file_path,
                        spine_order=order
                    )
                    
                    chapters.append(chapter)
                    
            except Exception as e:
                logger.warning(f"Failed to process file {file_path}: {e}")
                continue
        
        return chapters
    
    def _extract_chapters_dir(self, epub_dir: str, manifest: Dict, 
                             spine: List, opf_dir: str) -> List[ChapterInfo]:
        """Extract text content from EPUB chapters in directory format."""
        chapters = []
        
        for order, item_id in enumerate(spine):
            if item_id not in manifest:
                continue
                
            item_info = manifest[item_id]
            
            # Only process HTML/XHTML files
            if not any(mt in item_info['media_type'] for mt in ['html', 'xhtml']):
                continue
            
            # Construct full path
            file_path = item_info['href']
            if opf_dir:
                file_path = f"{opf_dir}/{file_path}"
            
            full_file_path = Path(epub_dir, file_path)
            
            # Skip if file should be excluded
            filename = os.path.basename(file_path).lower()
            if any(exclude in filename for exclude in self.config['exclude_files']):
                continue
            
            try:
                # Read and process the file
                if os.path.exists(full_file_path):
                    with open(full_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Extract text content
                    text_content, title = self._extract_text_from_html(content)
                    
                    # Skip if content is too short
                    word_count = len(text_content.split())
                    if word_count < self.config['min_chapter_words']:
                        continue
                    
                    # Determine chapter number
                    chapter_num = self._extract_chapter_number(title, filename, order)
                    
                    chapter = ChapterInfo(
                        title=title or f"Chapter {order + 1}",
                        content=text_content,
                        chapter_number=chapter_num,
                        section_number=None,
                        word_count=word_count,
                        file_path=file_path,
                        spine_order=order
                    )
                    
                    chapters.append(chapter)
                    
            except Exception as e:
                logger.warning(f"Failed to process file {file_path}: {e}")
                continue
        
        return chapters
    
    def _extract_text_from_html(self, html_content: str) -> Tuple[str, str]:
        """Extract clean text content from HTML/XHTML."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(self.config['skip_elements']):
                element.decompose()
            
            # Extract title (first h1, h2, or title element)
            title = ""
            for tag in ['h1', 'h2', 'title']:
                title_elem = soup.find(tag)
                if title_elem and title_elem.get_text().strip():
                    title = title_elem.get_text().strip()
                    break
            
            # Extract all text content
            text_content = soup.get_text()
            
            # Clean up text
            text_content = re.sub(r'\s+', ' ', text_content)  # Normalize whitespace
            text_content = text_content.strip()
            
            return text_content, title
            
        except Exception as e:
            logger.warning(f"Failed to extract text from HTML: {e}")
            return "", ""
    
    def _extract_chapter_number(self, title: str, filename: str, order: int) -> Optional[int]:
        """Extract chapter number from title or filename."""
        # Try title first
        if title:
            for indicator in self.config['chapter_indicators']:
                pattern = rf'{indicator}\s*(\d+)'
                match = re.search(pattern, title.lower())
                if match:
                    return int(match.group(1))
        
        # Try filename
        filename_lower = filename.lower()
        for indicator in self.config['chapter_indicators']:
            pattern = rf'{indicator}\s*(\d+)'
            match = re.search(pattern, filename_lower)
            if match:
                return int(match.group(1))
        
        # Look for any number in filename
        number_match = re.search(r'(\d+)', filename)
        if number_match:
            return int(number_match.group(1))
        
        # Fall back to spine order
        return order + 1
    
    def _create_book_metadata(self, metadata: Dict, chapters: List[ChapterInfo], 
                             epub_path: str) -> BookMetadata:
        """Create BookMetadata object from extracted information."""
        total_words = sum(chapter.word_count for chapter in chapters)
        
        return BookMetadata(
            title=metadata.get('title', 'Unknown Title'),
            author=metadata.get('author', 'Unknown Author'),
            publisher=metadata.get('publisher'),
            publication_date=metadata.get('publication_date'),
            language=metadata.get('language', 'en'),
            isbn=metadata.get('isbn'),
            description=metadata.get('description'),
            subject=metadata.get('subject'),
            total_chapters=len(chapters),
            total_words=total_words,
            file_path=epub_path
        )


def main():
    """Main function for command-line usage."""
    if len(sys.argv) != 2:
        print("Usage: python epub_processor.py <epub_file>")
        sys.exit(1)
    
    epub_path = sys.argv[1]
    if not os.path.exists(epub_path):
        print(f"Error: File not found: {epub_path}")
        sys.exit(1)
    
    processor = EPUBProcessor()
    
    try:
        metadata, chapters = processor.process_epub(epub_path)
        
        print(f"\nSuccessfully processed: {metadata.title}")
        print(f"Author: {metadata.author}")
        print(f"Publisher: {metadata.publisher or 'Unknown'}")
        print(f"Language: {metadata.language}")
        print(f"Total chapters: {metadata.total_chapters}")
        print(f"Total words: {metadata.total_words:,}")
        
        print("\nChapters:")
        for i, chapter in enumerate(chapters[:5]):  # Show first 5 chapters
            print(f"  {i+1}. {chapter.title} ({chapter.word_count:,} words)")
        
        if len(chapters) > 5:
            print(f"  ... and {len(chapters) - 5} more chapters")
    
    except Exception as e:
        print(f"Error processing EPUB: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()