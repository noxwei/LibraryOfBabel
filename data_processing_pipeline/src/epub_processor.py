#!/usr/bin/env python3
"""
Containerized EPUB Processor for BabelProcessorDb Testing
========================================================

Lightweight EPUB processing for testing pipeline.
Extracts text, creates chunks, and prepares for embedding.

Based on LibraryOfBabel standardized API requirements.
"""

import os
import re
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import zipfile
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from urllib.parse import unquote

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class BookMetadata:
    """Simplified book metadata for testing"""
    title: str
    author: str
    publisher: Optional[str] = None
    publication_date: Optional[str] = None
    language: str = "english"
    isbn: Optional[str] = None
    description: Optional[str] = None
    word_count: int = 0

@dataclass
class TextChunk:
    """Text chunk for embedding processing"""
    chunk_id: str
    book_id: int
    chunk_type: str  # 'chapter', 'paragraph', 'sentence'
    title: Optional[str]
    content: str
    word_count: int
    chapter_number: Optional[int] = None
    section_number: Optional[int] = None
    paragraph_number: Optional[int] = None

class EPUBProcessor:
    """Containerized EPUB processor for testing"""
    
    def __init__(self, max_chunks_per_book: int = 1000):
        self.max_chunks_per_book = max_chunks_per_book
        self.processed_books = 0
        
    def process_epub(self, epub_path: Path, book_id: int) -> Tuple[BookMetadata, List[TextChunk]]:
        """
        Process EPUB file and extract metadata + chunks
        
        Args:
            epub_path: Path to EPUB file
            book_id: Database book ID
            
        Returns:
            Tuple of (metadata, chunks)
        """
        logger.info(f"Processing EPUB: {epub_path}")
        
        try:
            with zipfile.ZipFile(epub_path, 'r') as epub_zip:
                # Extract metadata
                metadata = self._extract_metadata(epub_zip)
                metadata.title = metadata.title or epub_path.stem
                
                # Extract text content
                content_files = self._get_content_files(epub_zip)
                raw_chapters = self._extract_chapters(epub_zip, content_files)
                
                # Create chunks
                chunks = self._create_chunks(raw_chapters, book_id, metadata.title)
                
                # Limit chunks for testing
                if len(chunks) > self.max_chunks_per_book:
                    logger.warning(f"Limiting chunks from {len(chunks)} to {self.max_chunks_per_book} for testing")
                    chunks = chunks[:self.max_chunks_per_book]
                
                # Update metadata word count
                metadata.word_count = sum(chunk.word_count for chunk in chunks)
                
                logger.info(f"Extracted {len(chunks)} chunks from {metadata.title}")
                return metadata, chunks
                
        except Exception as e:
            logger.error(f"Error processing {epub_path}: {e}")
            raise
    
    def _extract_metadata(self, epub_zip: zipfile.ZipFile) -> BookMetadata:
        """Extract basic metadata from EPUB"""
        try:
            # Find OPF file
            container_data = epub_zip.read('META-INF/container.xml')
            container_root = ET.fromstring(container_data)
            
            opf_path = None
            for rootfile in container_root.findall('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile'):
                if rootfile.get('media-type') == 'application/oebps-package+xml':
                    opf_path = rootfile.get('full-path')
                    break
            
            if not opf_path:
                logger.warning("No OPF file found, using defaults")
                return BookMetadata(title="Unknown", author="Unknown")
            
            # Parse OPF
            opf_data = epub_zip.read(opf_path)
            opf_root = ET.fromstring(opf_data)
            
            # Extract metadata
            metadata_elem = opf_root.find('.//{http://www.idpf.org/2007/opf}metadata')
            if metadata_elem is None:
                return BookMetadata(title="Unknown", author="Unknown")
            
            # Get title
            title_elem = metadata_elem.find('.//{http://purl.org/dc/elements/1.1/}title')
            title = title_elem.text if title_elem is not None else "Unknown"
            
            # Get author  
            author_elem = metadata_elem.find('.//{http://purl.org/dc/elements/1.1/}creator')
            author = author_elem.text if author_elem is not None else "Unknown"
            
            # Get publisher
            publisher_elem = metadata_elem.find('.//{http://purl.org/dc/elements/1.1/}publisher')
            publisher = publisher_elem.text if publisher_elem is not None else None
            
            # Get description
            description_elem = metadata_elem.find('.//{http://purl.org/dc/elements/1.1/}description')
            description = description_elem.text if description_elem is not None else None
            
            return BookMetadata(
                title=title.strip(),
                author=author.strip(),
                publisher=publisher.strip() if publisher else None,
                description=description.strip() if description else None
            )
            
        except Exception as e:
            logger.warning(f"Error extracting metadata: {e}")
            return BookMetadata(title="Unknown", author="Unknown")
    
    def _get_content_files(self, epub_zip: zipfile.ZipFile) -> List[str]:
        """Get list of content files from EPUB"""
        try:
            # Simple approach - find all HTML/XHTML files
            content_files = []
            for file_path in epub_zip.namelist():
                if file_path.endswith(('.html', '.xhtml', '.htm')) and 'META-INF' not in file_path:
                    content_files.append(file_path)
            
            return sorted(content_files)
            
        except Exception as e:
            logger.error(f"Error getting content files: {e}")
            return []
    
    def _extract_chapters(self, epub_zip: zipfile.ZipFile, content_files: List[str]) -> List[Dict]:
        """Extract chapter content from EPUB files"""
        chapters = []
        
        for i, file_path in enumerate(content_files):
            try:
                file_data = epub_zip.read(file_path)
                soup = BeautifulSoup(file_data, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Extract text
                text = soup.get_text()
                text = re.sub(r'\s+', ' ', text).strip()
                
                if len(text) > 100:  # Skip very short chapters
                    chapters.append({
                        'chapter_number': i + 1,
                        'title': f"Chapter {i + 1}",
                        'content': text,
                        'file_path': file_path
                    })
                    
            except Exception as e:
                logger.warning(f"Error processing file {file_path}: {e}")
                continue
        
        return chapters
    
    def _create_chunks(self, chapters: List[Dict], book_id: int, book_title: str) -> List[TextChunk]:
        """Create text chunks from chapters"""
        chunks = []
        chunk_counter = 0
        
        for chapter in chapters:
            content = chapter['content']
            chapter_num = chapter['chapter_number']
            
            # Split into paragraphs
            paragraphs = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 50]
            
            for para_num, paragraph in enumerate(paragraphs):
                if chunk_counter >= self.max_chunks_per_book:
                    break
                    
                # Create chunk ID
                chunk_id = self._generate_chunk_id(book_id, chapter_num, para_num)
                
                # Count words
                word_count = len(paragraph.split())
                
                if word_count > 10:  # Skip very short paragraphs
                    chunk = TextChunk(
                        chunk_id=chunk_id,
                        book_id=book_id,
                        chunk_type='paragraph',
                        title=f"{book_title} - Chapter {chapter_num}",
                        content=paragraph,
                        word_count=word_count,
                        chapter_number=chapter_num,
                        paragraph_number=para_num + 1
                    )
                    chunks.append(chunk)
                    chunk_counter += 1
            
            if chunk_counter >= self.max_chunks_per_book:
                break
        
        return chunks
    
    def _generate_chunk_id(self, book_id: int, chapter: int, paragraph: int) -> str:
        """Generate unique chunk ID"""
        content = f"book_{book_id}_ch_{chapter}_para_{paragraph}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def get_word_count(self, text: str) -> int:
        """Count words in text"""
        return len(text.split())