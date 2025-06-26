#!/usr/bin/env python3
"""
Text Chunker for LibraryOfBabel
===============================

Creates hierarchical text chunks from extracted EPUB content:
- Primary chunks: Chapter-level (2,000-5,000 words)
- Secondary chunks: Section-level (500-1,500 words)  
- Micro chunks: Paragraph-level (50-200 words)

Author: Librarian Agent
Version: 1.0
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ChunkType(Enum):
    """Types of text chunks."""
    CHAPTER = "chapter"
    SECTION = "section"
    PARAGRAPH = "paragraph"

@dataclass
class TextChunk:
    """A chunk of text with metadata."""
    chunk_id: str
    book_id: str
    chunk_type: ChunkType
    title: str
    content: str
    word_count: int
    character_count: int
    chapter_number: Optional[int]
    section_number: Optional[int]
    paragraph_number: Optional[int]
    start_position: int
    end_position: int
    parent_chunk_id: Optional[str] = None

class TextChunker:
    """Creates hierarchical text chunks from book content."""
    
    def __init__(self, config: Dict = None):
        """Initialize with optional configuration."""
        self.config = config or {
            'chapter_min_words': 2000,
            'chapter_max_words': 5000,
            'section_min_words': 500,
            'section_max_words': 1500,
            'paragraph_min_words': 50,
            'paragraph_max_words': 200,
            'sentence_min_length': 10,
            'overlap_words': 50  # Overlap between chunks for context
        }
        
        # Patterns for identifying section breaks
        self.section_patterns = [
            r'\n\s*[IVX]+\.?\s*\n',  # Roman numerals
            r'\n\s*\d+\.?\s*\n',     # Arabic numerals
            r'\n\s*[A-Z][A-Z\s]{2,}\n',  # ALL CAPS headers
            r'\n\s*\*\s*\*\s*\*\s*\n',   # Asterisk breaks
            r'\n\s*—+\s*\n',        # Em dash breaks
            r'\n\s*#+\s+',          # Markdown-style headers
        ]
    
    def chunk_book(self, book_metadata, chapters: List) -> List[TextChunk]:
        """
        Create hierarchical chunks from a book's chapters.
        
        Args:
            book_metadata: Book metadata object
            chapters: List of ChapterInfo objects
            
        Returns:
            List of TextChunk objects
        """
        logger.info(f"Creating chunks for: {book_metadata.title}")
        
        all_chunks = []
        book_id = self._generate_book_id(book_metadata)
        
        for chapter in chapters:
            chapter_chunks = self._chunk_chapter(chapter, book_id)
            all_chunks.extend(chapter_chunks)
        
        logger.info(f"Created {len(all_chunks)} chunks total")
        return all_chunks
    
    def _generate_book_id(self, book_metadata) -> str:
        """Generate a unique book ID."""
        # Use ISBN if available, otherwise create from title and author
        if book_metadata.isbn:
            return f"isbn_{book_metadata.isbn.replace('-', '').replace(' ', '')}"
        
        # Create ID from title and author
        title_part = re.sub(r'[^\w\s]', '', book_metadata.title)[:20]
        author_part = re.sub(r'[^\w\s]', '', book_metadata.author)[:15]
        title_part = re.sub(r'\s+', '_', title_part.strip())
        author_part = re.sub(r'\s+', '_', author_part.strip())
        
        return f"{title_part}_{author_part}".lower()
    
    def _chunk_chapter(self, chapter, book_id: str) -> List[TextChunk]:
        """Create chunks from a single chapter."""
        chunks = []
        
        # Start with chapter-level chunk
        chapter_chunk = self._create_chapter_chunk(chapter, book_id)
        chunks.append(chapter_chunk)
        
        # Create section-level chunks if chapter is large enough
        if chapter.word_count > self.config['chapter_max_words']:
            section_chunks = self._create_section_chunks(chapter, book_id, chapter_chunk.chunk_id)
            chunks.extend(section_chunks)
        
        # Create paragraph-level chunks
        paragraph_chunks = self._create_paragraph_chunks(chapter, book_id, chapter_chunk.chunk_id)
        chunks.extend(paragraph_chunks)
        
        return chunks
    
    def _create_chapter_chunk(self, chapter, book_id: str) -> TextChunk:
        """Create a chapter-level chunk."""
        chunk_id = f"{book_id}_ch{chapter.chapter_number or chapter.spine_order}"
        
        return TextChunk(
            chunk_id=chunk_id,
            book_id=book_id,
            chunk_type=ChunkType.CHAPTER,
            title=chapter.title,
            content=chapter.content,
            word_count=chapter.word_count,
            character_count=len(chapter.content),
            chapter_number=chapter.chapter_number,
            section_number=None,
            paragraph_number=None,
            start_position=0,
            end_position=len(chapter.content)
        )
    
    def _create_section_chunks(self, chapter, book_id: str, parent_chunk_id: str) -> List[TextChunk]:
        """Create section-level chunks from a chapter."""
        sections = self._split_into_sections(chapter.content)
        chunks = []
        
        for i, (section_title, section_content, start_pos, end_pos) in enumerate(sections):
            word_count = len(section_content.split())
            
            # Skip sections that are too small
            if word_count < self.config['section_min_words']:
                continue
            
            chunk_id = f"{parent_chunk_id}_s{i+1}"
            
            chunk = TextChunk(
                chunk_id=chunk_id,
                book_id=book_id,
                chunk_type=ChunkType.SECTION,
                title=section_title or f"Section {i+1}",
                content=section_content,
                word_count=word_count,
                character_count=len(section_content),
                chapter_number=chapter.chapter_number,
                section_number=i+1,
                paragraph_number=None,
                start_position=start_pos,
                end_position=end_pos,
                parent_chunk_id=parent_chunk_id
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def _create_paragraph_chunks(self, chapter, book_id: str, parent_chunk_id: str) -> List[TextChunk]:
        """Create paragraph-level chunks from a chapter."""
        paragraphs = self._split_into_paragraphs(chapter.content)
        chunks = []
        
        current_chunk_content = []
        current_chunk_words = 0
        chunk_start_pos = 0
        chunk_counter = 1
        
        for para_text, para_start, para_end in paragraphs:
            para_words = len(para_text.split())
            
            # Skip very short paragraphs
            if para_words < 10:
                continue
            
            # Check if adding this paragraph would exceed max words
            if (current_chunk_words + para_words > self.config['paragraph_max_words'] 
                and current_chunk_content):
                
                # Create chunk from current content
                chunk = self._create_paragraph_chunk(
                    current_chunk_content, book_id, parent_chunk_id, 
                    chapter.chapter_number, chunk_counter, chunk_start_pos
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_content = self._get_overlap_content(current_chunk_content)
                current_chunk_content = overlap_content + [para_text]
                current_chunk_words = sum(len(text.split()) for text in current_chunk_content)
                chunk_counter += 1
                chunk_start_pos = para_start - len(' '.join(overlap_content))
                
            else:
                # Add paragraph to current chunk
                if not current_chunk_content:
                    chunk_start_pos = para_start
                    
                current_chunk_content.append(para_text)
                current_chunk_words += para_words
        
        # Create final chunk if there's remaining content
        if current_chunk_content:
            chunk = self._create_paragraph_chunk(
                current_chunk_content, book_id, parent_chunk_id,
                chapter.chapter_number, chunk_counter, chunk_start_pos
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_paragraph_chunk(self, content_list: List[str], book_id: str, 
                               parent_chunk_id: str, chapter_num: Optional[int], 
                               chunk_num: int, start_pos: int) -> TextChunk:
        """Create a single paragraph chunk."""
        content = ' '.join(content_list)
        word_count = len(content.split())
        
        chunk_id = f"{parent_chunk_id}_p{chunk_num}"
        
        return TextChunk(
            chunk_id=chunk_id,
            book_id=book_id,
            chunk_type=ChunkType.PARAGRAPH,
            title=f"Paragraph {chunk_num}",
            content=content,
            word_count=word_count,
            character_count=len(content),
            chapter_number=chapter_num,
            section_number=None,
            paragraph_number=chunk_num,
            start_position=start_pos,
            end_position=start_pos + len(content),
            parent_chunk_id=parent_chunk_id
        )
    
    def _split_into_sections(self, text: str) -> List[Tuple[str, str, int, int]]:
        """Split text into sections based on formatting patterns."""
        sections = []
        current_pos = 0
        
        # Find all section breaks
        breaks = []
        for pattern in self.section_patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                breaks.append((match.start(), match.end(), match.group().strip()))
        
        # Sort breaks by position
        breaks.sort(key=lambda x: x[0])
        
        # Create sections
        for i, (break_start, break_end, break_text) in enumerate(breaks):
            # Section content is from current position to break
            if current_pos < break_start:
                section_content = text[current_pos:break_start].strip()
                
                if section_content:
                    # Extract section title from break text or first line
                    section_title = self._extract_section_title(break_text, section_content)
                    
                    sections.append((
                        section_title,
                        section_content,
                        current_pos,
                        break_start
                    ))
            
            current_pos = break_end
        
        # Add final section
        if current_pos < len(text):
            final_content = text[current_pos:].strip()
            if final_content:
                sections.append((
                    "Final Section",
                    final_content,
                    current_pos,
                    len(text)
                ))
        
        # If no sections found, treat entire text as one section
        if not sections:
            sections.append((
                "Full Chapter",
                text.strip(),
                0,
                len(text)
            ))
        
        return sections
    
    def _extract_section_title(self, break_text: str, content: str) -> str:
        """Extract a title for a section."""
        # Clean break text
        title = re.sub(r'[^\w\s]', ' ', break_text).strip()
        
        if title and len(title) > 2:
            return title
        
        # Extract first line of content as title
        first_line = content.split('\n')[0].strip()
        if len(first_line) < 100:  # Reasonable title length
            return first_line
        
        return "Section"
    
    def _split_into_paragraphs(self, text: str) -> List[Tuple[str, int, int]]:
        """Split text into paragraphs."""
        # Split on double newlines or similar paragraph breaks
        paragraph_pattern = r'\n\s*\n'
        
        paragraphs = []
        current_pos = 0
        
        for match in re.finditer(paragraph_pattern, text):
            # Get paragraph content
            para_content = text[current_pos:match.start()].strip()
            
            if para_content and len(para_content.split()) >= 5:  # Minimum paragraph length
                paragraphs.append((
                    para_content,
                    current_pos,
                    match.start()
                ))
            
            current_pos = match.end()
        
        # Add final paragraph
        if current_pos < len(text):
            final_para = text[current_pos:].strip()
            if final_para and len(final_para.split()) >= 5:
                paragraphs.append((
                    final_para,
                    current_pos,
                    len(text)
                ))
        
        # If no clear paragraphs, split by sentence groups
        if not paragraphs:
            paragraphs = self._split_by_sentences(text)
        
        return paragraphs
    
    def _split_by_sentences(self, text: str) -> List[Tuple[str, int, int]]:
        """Split text by sentence groups when paragraph detection fails."""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        paragraphs = []
        current_group = []
        current_words = 0
        start_pos = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            sentence_words = len(sentence.split())
            
            # Group sentences into paragraph-sized chunks
            if (current_words + sentence_words > self.config['paragraph_max_words'] 
                and current_group):
                
                # Create paragraph from current group
                para_content = ' '.join(current_group)
                para_end = start_pos + len(para_content)
                
                paragraphs.append((para_content, start_pos, para_end))
                
                # Start new group
                current_group = [sentence]
                current_words = sentence_words
                start_pos = para_end + 1
                
            else:
                current_group.append(sentence)
                current_words += sentence_words
        
        # Add final group
        if current_group:
            para_content = ' '.join(current_group)
            paragraphs.append((
                para_content,
                start_pos,
                start_pos + len(para_content)
            ))
        
        return paragraphs
    
    def _get_overlap_content(self, content_list: List[str]) -> List[str]:
        """Get overlap content from the end of current chunk."""
        if not content_list:
            return []
        
        overlap_words = 0
        overlap_content = []
        
        # Take sentences from the end until we reach overlap limit
        for text in reversed(content_list):
            words = len(text.split())
            if overlap_words + words <= self.config['overlap_words']:
                overlap_content.insert(0, text)
                overlap_words += words
            else:
                break
        
        return overlap_content


def main():
    """Test the chunker with sample text."""
    # Sample chapter for testing
    sample_text = """
    Chapter 1: The Beginning
    
    This is the first paragraph of our sample chapter. It contains some meaningful content
    that we can use to test our chunking algorithm.
    
    This is the second paragraph. It continues the narrative and provides more content
    for our testing purposes.
    
    Section A: A New Beginning
    
    Here we have a new section with its own content. This section contains multiple
    paragraphs that should be chunked appropriately.
    
    Another paragraph in section A. This helps us test how the chunker handles
    section-level organization.
    """
    
    # Mock chapter object
    class MockChapter:
        def __init__(self):
            self.title = "Chapter 1: The Beginning"
            self.content = sample_text
            self.word_count = len(sample_text.split())
            self.chapter_number = 1
            self.spine_order = 0
    
    # Mock metadata
    class MockMetadata:
        def __init__(self):
            self.title = "Test Book"
            self.author = "Test Author"
            self.isbn = None
    
    chunker = TextChunker()
    metadata = MockMetadata()
    chapter = MockChapter()
    
    chunks = chunker.chunk_book(metadata, [chapter])
    
    print(f"Created {len(chunks)} chunks:")
    for chunk in chunks:
        print(f"  {chunk.chunk_type.value}: {chunk.title} ({chunk.word_count} words)")


if __name__ == "__main__":
    main()