#!/usr/bin/env python3
"""
Improved Text Chunker for LibraryOfBabel v2.0
==============================================

Fixes the catastrophic chunking issues:
- NO MORE 5.4 million word chunks
- Proper size limits with token counting
- Sliding window with overlap
- Better hierarchy management

Target chunk sizes:
- Small: 256-512 tokens (~200-400 words)
- Medium: 512-1024 tokens (~400-800 words)
- Large: 1024-2048 tokens (~800-1600 words)

Author: Fixed by Claude Code
Date: 2026-01-12
"""

import re
import logging
import hashlib
from typing import List, Dict, Optional, Tuple, Generator
from dataclasses import dataclass
from enum import Enum
import tiktoken

logger = logging.getLogger(__name__)

class ChunkSize(Enum):
    """Standard chunk sizes for different use cases."""
    SMALL = "small"    # 256-512 tokens for precise retrieval
    MEDIUM = "medium"  # 512-1024 tokens - sweet spot
    LARGE = "large"    # 1024-2048 tokens for context-heavy

@dataclass
class ImprovedChunk:
    """A properly-sized chunk with comprehensive metadata."""
    chunk_id: str
    book_id: int
    chunk_size: ChunkSize
    content: str
    token_count: int
    word_count: int
    character_count: int
    sequence_number: int  # Order within book
    overlap_start: bool   # Has overlap from previous chunk
    overlap_end: bool     # Has overlap to next chunk
    metadata: Dict        # Additional metadata (chapter, section, etc.)

class ImprovedTextChunker:
    """Creates properly-sized chunks with token limits."""

    def __init__(self, chunk_size: ChunkSize = ChunkSize.MEDIUM):
        """
        Initialize with target chunk size.

        Args:
            chunk_size: Target size for chunks (SMALL, MEDIUM, or LARGE)
        """
        self.chunk_size = chunk_size

        # Token limits by size
        self.token_limits = {
            ChunkSize.SMALL: (256, 512),
            ChunkSize.MEDIUM: (512, 1024),
            ChunkSize.LARGE: (1024, 2048)
        }

        # Get limits for chosen size
        self.min_tokens, self.max_tokens = self.token_limits[chunk_size]

        # Overlap configuration (20% of min size)
        self.overlap_tokens = int(self.min_tokens * 0.2)

        # Initialize tokenizer (using cl100k_base for GPT-3.5/4)
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            logger.warning("Tiktoken not available, using word-based approximation")
            self.tokenizer = None

        # Sentence splitter pattern
        self.sentence_pattern = re.compile(
            r'(?<=[.!?])\s+(?=[A-Z])|'  # Standard sentence breaks
            r'(?<=[.!?])\s*\n+|'         # Sentence breaks with newlines
            r'\n\n+'                      # Paragraph breaks
        )

    def chunk_book(self, book_id: int, content: str,
                   existing_chunks: Optional[int] = None) -> List[ImprovedChunk]:
        """
        Create properly-sized chunks from book content.

        Args:
            book_id: Database book ID
            content: Full text content of the book
            existing_chunks: Number of existing chunks (for incremental updates)

        Returns:
            List of ImprovedChunk objects
        """
        if not content:
            logger.warning(f"Empty content for book {book_id}")
            return []

        logger.info(f"Chunking book {book_id} with {len(content)} characters")

        # Clean and normalize content
        content = self._normalize_text(content)

        # Split into sentences for better boundaries
        sentences = self._split_sentences(content)

        # Create chunks with proper size limits
        chunks = list(self._create_chunks(book_id, sentences, existing_chunks or 0))

        logger.info(f"Created {len(chunks)} chunks for book {book_id}")
        return chunks

    def _normalize_text(self, text: str) -> str:
        """Normalize text for consistent chunking."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Normalize quotes and dashes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        text = text.replace('—', '--').replace('–', '-')

        return text.strip()

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Use regex pattern to find sentence boundaries
        sentences = self.sentence_pattern.split(text)

        # Clean up and filter
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Approximation: 1 token ≈ 0.75 words
            return int(len(text.split()) / 0.75)

    def _create_chunks(self, book_id: int, sentences: List[str],
                      start_sequence: int = 0) -> Generator[ImprovedChunk, None, None]:
        """
        Create chunks from sentences with proper size limits.

        Yields:
            ImprovedChunk objects
        """
        if not sentences:
            return

        current_chunk = []
        current_tokens = 0
        sequence_number = start_sequence
        overlap_buffer = []  # Sentences to include in next chunk for overlap

        for i, sentence in enumerate(sentences):
            sentence_tokens = self._count_tokens(sentence)

            # Skip sentences that are too large (shouldn't happen but safety check)
            if sentence_tokens > self.max_tokens:
                logger.warning(f"Sentence with {sentence_tokens} tokens exceeds max, splitting")
                # Split the sentence into smaller parts
                words = sentence.split()
                words_per_chunk = int(self.max_tokens * 0.75)  # Approximate

                for j in range(0, len(words), words_per_chunk):
                    chunk_words = words[j:j + words_per_chunk]
                    chunk_text = ' '.join(chunk_words)

                    yield self._create_chunk_object(
                        book_id=book_id,
                        content=chunk_text,
                        sequence_number=sequence_number,
                        overlap_start=False,
                        overlap_end=False
                    )
                    sequence_number += 1
                continue

            # Check if adding this sentence would exceed max tokens
            if current_tokens + sentence_tokens > self.max_tokens:
                # Create chunk from current content
                if current_chunk:
                    chunk_content = ' '.join(current_chunk)

                    # Determine overlap
                    overlap_start = sequence_number > start_sequence
                    overlap_end = i < len(sentences) - 1

                    yield self._create_chunk_object(
                        book_id=book_id,
                        content=chunk_content,
                        sequence_number=sequence_number,
                        overlap_start=overlap_start,
                        overlap_end=overlap_end
                    )

                    sequence_number += 1

                    # Prepare overlap buffer (last ~20% of current chunk)
                    if overlap_end and current_chunk:
                        overlap_size = max(1, len(current_chunk) // 5)
                        overlap_buffer = current_chunk[-overlap_size:]

                # Start new chunk with overlap
                current_chunk = overlap_buffer + [sentence]
                current_tokens = self._count_tokens(' '.join(current_chunk))
                overlap_buffer = []
            else:
                # Add sentence to current chunk
                current_chunk.append(sentence)
                current_tokens += sentence_tokens

                # Check if we've reached optimal size
                if current_tokens >= self.min_tokens and i < len(sentences) - 1:
                    # Look ahead - if next sentence would exceed max, create chunk now
                    next_tokens = self._count_tokens(sentences[i + 1]) if i + 1 < len(sentences) else 0

                    if current_tokens + next_tokens > self.max_tokens:
                        chunk_content = ' '.join(current_chunk)

                        yield self._create_chunk_object(
                            book_id=book_id,
                            content=chunk_content,
                            sequence_number=sequence_number,
                            overlap_start=sequence_number > start_sequence,
                            overlap_end=True
                        )

                        sequence_number += 1

                        # Prepare overlap
                        overlap_size = max(1, len(current_chunk) // 5)
                        overlap_buffer = current_chunk[-overlap_size:]
                        current_chunk = []
                        current_tokens = 0

        # Create final chunk if there's remaining content
        if current_chunk:
            chunk_content = ' '.join(current_chunk)

            yield self._create_chunk_object(
                book_id=book_id,
                content=chunk_content,
                sequence_number=sequence_number,
                overlap_start=sequence_number > start_sequence,
                overlap_end=False
            )

    def _create_chunk_object(self, book_id: int, content: str,
                           sequence_number: int, overlap_start: bool,
                           overlap_end: bool) -> ImprovedChunk:
        """Create a chunk object with metadata."""
        # Generate unique chunk ID
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        chunk_id = f"v2_{book_id}_{sequence_number}_{content_hash}"

        # Count metrics
        token_count = self._count_tokens(content)
        word_count = len(content.split())
        character_count = len(content)

        # Extract metadata (could be enhanced with NER, topic extraction, etc.)
        metadata = {
            'has_dialogue': '"' in content or "'" in content,
            'has_numbers': any(c.isdigit() for c in content),
            'avg_sentence_length': word_count / max(1, content.count('.') + content.count('!') + content.count('?')),
        }

        return ImprovedChunk(
            chunk_id=chunk_id,
            book_id=book_id,
            chunk_size=self.chunk_size,
            content=content,
            token_count=token_count,
            word_count=word_count,
            character_count=character_count,
            sequence_number=sequence_number,
            overlap_start=overlap_start,
            overlap_end=overlap_end,
            metadata=metadata
        )


def analyze_current_chunks(conn):
    """Analyze current chunking issues in the database."""
    import psycopg2

    cur = conn.cursor()

    # Get statistics on current chunks
    cur.execute("""
        SELECT
            COUNT(*) as total_chunks,
            AVG(word_count) as avg_words,
            MIN(word_count) as min_words,
            MAX(word_count) as max_words,
            STDDEV(word_count) as stddev_words,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY word_count) as median_words,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY word_count) as p95_words
        FROM chunks
    """)

    stats = cur.fetchone()
    print("\n📊 CURRENT CHUNKING STATISTICS")
    print("=" * 60)
    print(f"Total chunks: {stats[0]:,}")
    print(f"Average words: {stats[1]:,.0f}")
    print(f"Median words: {stats[5]:,.0f}")
    print(f"Min words: {stats[2]:,}")
    print(f"Max words: {stats[3]:,}")
    print(f"95th percentile: {stats[6]:,.0f} words")
    print(f"Std deviation: {stats[4]:,.0f}")

    # Find problematic books
    cur.execute("""
        SELECT
            b.book_id,
            b.title,
            COUNT(c.chunk_id) as chunks,
            MAX(c.word_count) as max_chunk_words
        FROM books b
        JOIN chunks c ON b.book_id = c.book_id
        GROUP BY b.book_id, b.title
        HAVING MAX(c.word_count) > 100000
        ORDER BY max_chunk_words DESC
        LIMIT 10
    """)

    print("\n⚠️  BOOKS WITH HUGE CHUNKS (>100K words)")
    print("-" * 60)
    for book_id, title, chunks, max_words in cur.fetchall():
        print(f"[{book_id}] {title[:50]}: {max_words:,} words in largest chunk")

    cur.close()


def estimate_new_chunking(conn, sample_size: int = 10):
    """Estimate results of new chunking strategy."""
    import psycopg2

    cur = conn.cursor()

    # Get sample of books
    cur.execute("""
        SELECT
            b.book_id,
            b.title,
            SUM(c.word_count) as total_words
        FROM books b
        JOIN chunks c ON b.book_id = c.book_id
        GROUP BY b.book_id, b.title
        ORDER BY RANDOM()
        LIMIT %s
    """, (sample_size,))

    books = cur.fetchall()

    print(f"\n🔬 ESTIMATING NEW CHUNKING ON {sample_size} BOOKS")
    print("=" * 60)

    total_new_chunks = 0

    for book_id, title, total_words in books:
        # Estimate chunks for each size
        small_chunks = total_words / 300  # ~300 words per small chunk
        medium_chunks = total_words / 600  # ~600 words per medium chunk
        large_chunks = total_words / 1200  # ~1200 words per large chunk

        print(f"\n{title[:50]}... ({total_words:,} words)")
        print(f"  Small chunks: ~{small_chunks:.0f}")
        print(f"  Medium chunks: ~{medium_chunks:.0f}")
        print(f"  Large chunks: ~{large_chunks:.0f}")

        total_new_chunks += medium_chunks  # Using medium as default

    # Extrapolate to full library
    avg_chunks_per_book = total_new_chunks / sample_size
    total_books = 4932
    estimated_total_chunks = avg_chunks_per_book * total_books

    print(f"\n📈 PROJECTION FOR FULL LIBRARY")
    print("-" * 60)
    print(f"Average chunks per book (medium): {avg_chunks_per_book:.0f}")
    print(f"Estimated total chunks: {estimated_total_chunks:,.0f}")
    print(f"Current total chunks: 2,366,122")
    print(f"Change: {(estimated_total_chunks/2366122 - 1)*100:+.1f}%")

    cur.close()


if __name__ == "__main__":
    import psycopg2

    # Connect to database
    conn = psycopg2.connect(
        dbname="knowledge_base",
        user="weixiangzhang",
        host="localhost"
    )

    try:
        # Analyze current state
        analyze_current_chunks(conn)

        # Estimate new chunking
        estimate_new_chunking(conn, sample_size=20)

    finally:
        conn.close()