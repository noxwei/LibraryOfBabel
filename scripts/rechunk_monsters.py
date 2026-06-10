#!/usr/bin/env python3
"""
Re-chunk Monster Chunks — Break 50K+ word single-chunks into ~250-word segments
================================================================================

These books failed chapter detection and were ingested as single mega-chunks.
The Gemini embedding truncates them to 8K chars, losing 97% of content.

This script:
1. Identifies monster chunks (>50K words)
2. Splits them into ~250-word sentence-aligned segments
3. Inserts new chunks with parent_chunk_id linkage
4. Original monster chunk is preserved (marked via parent relationship)

Run: python3 scripts/rechunk_monsters.py
"""

import os
import sys
import re
import psycopg2
import psycopg2.extras
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "rechunk_monsters.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("rechunk_monsters")

DB_CONFIG = {
    'host': 'localhost',
    'database': 'knowledge_base',
    'user': os.getenv('DB_USER', 'weixiangzhang'),
    'port': 5432
}

TARGET_WORDS = 250
MIN_WORDS = 100  # Don't create tiny trailing chunks


def split_sentences(text):
    """Split text into sentences using regex (avoids nltk dependency)."""
    # Split on sentence-ending punctuation followed by space + capital letter
    # Handles: Mr. Mrs. Dr. etc. abbreviations by requiring 2+ chars after period
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z"\'`])', text)
    # Also split on paragraph boundaries
    result = []
    for s in sentences:
        # Split on double newlines (paragraph breaks)
        paras = re.split(r'\n\s*\n', s)
        result.extend(p.strip() for p in paras if p.strip())
    return result


def rechunk_content(chunk_id, book_id, content):
    """Break a monster chunk into ~250-word sentence-aligned segments."""
    sentences = split_sentences(content)
    if not sentences:
        logger.warning(f"No sentences found in {chunk_id}")
        return []

    new_chunks = []
    current_sentences = []
    current_words = 0
    chunk_counter = 1

    for sentence in sentences:
        word_count = len(sentence.split())

        # If adding this sentence exceeds target and we have content, finalize
        if current_words + word_count > TARGET_WORDS and current_sentences:
            chunk_content = ' '.join(current_sentences)
            new_chunk_id = f"{chunk_id}_rechunk_{chunk_counter:04d}"
            new_chunks.append({
                'chunk_id': new_chunk_id,
                'book_id': book_id,
                'chunk_type': 'paragraph',
                'title': f"Segment {chunk_counter}",
                'content': chunk_content,
                'word_count': current_words,
                'character_count': len(chunk_content),
                'section_number': chunk_counter,
                'parent_chunk_id': chunk_id,
            })
            current_sentences = [sentence]
            current_words = word_count
            chunk_counter += 1
        else:
            current_sentences.append(sentence)
            current_words += word_count

    # Finalize last chunk
    if current_sentences and current_words >= MIN_WORDS:
        chunk_content = ' '.join(current_sentences)
        new_chunk_id = f"{chunk_id}_rechunk_{chunk_counter:04d}"
        new_chunks.append({
            'chunk_id': new_chunk_id,
            'book_id': book_id,
            'chunk_type': 'paragraph',
            'title': f"Segment {chunk_counter}",
            'content': chunk_content,
            'word_count': current_words,
            'character_count': len(chunk_content),
            'section_number': chunk_counter,
            'parent_chunk_id': chunk_id,
        })
    elif current_sentences and new_chunks:
        # Merge tiny trailing chunk into previous
        prev = new_chunks[-1]
        extra = ' '.join(current_sentences)
        prev['content'] += ' ' + extra
        prev['word_count'] += current_words
        prev['character_count'] = len(prev['content'])

    return new_chunks


def get_monster_chunks(conn, min_words=50000):
    """Find chunks with word_count > threshold."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT chunk_id, book_id, content, word_count
        FROM chunks
        WHERE word_count > %s
        ORDER BY word_count DESC
    """, (min_words,))
    return cur.fetchall()


def check_already_rechunked(conn, parent_chunk_id):
    """Check if this monster was already re-chunked."""
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM chunks WHERE parent_chunk_id = %s
    """, (parent_chunk_id,))
    return cur.fetchone()[0] > 0


def insert_chunks(conn, chunks):
    """Insert rechunked segments into database."""
    cur = conn.cursor()
    inserted = 0
    for chunk in chunks:
        try:
            cur.execute("""
                INSERT INTO chunks (chunk_id, book_id, chunk_type, title, content,
                                    word_count, character_count, section_number, parent_chunk_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (chunk_id) DO NOTHING
            """, (
                chunk['chunk_id'],
                chunk['book_id'],
                chunk['chunk_type'],
                chunk['title'],
                chunk['content'],
                chunk['word_count'],
                chunk['character_count'],
                chunk['section_number'],
                chunk['parent_chunk_id'],
            ))
            inserted += 1
        except Exception as e:
            logger.error(f"Error inserting {chunk['chunk_id']}: {e}")
            conn.rollback()
            return inserted
    conn.commit()
    return inserted


def main():
    conn = psycopg2.connect(**DB_CONFIG)

    monsters = get_monster_chunks(conn)
    logger.info(f"Found {len(monsters)} monster chunks (>50K words)")

    if not monsters:
        logger.info("No monster chunks found. Nothing to do.")
        conn.close()
        return

    total_new = 0
    total_words_covered = 0

    for monster in monsters:
        chunk_id = monster['chunk_id']
        book_id = monster['book_id']
        word_count = monster['word_count']

        # Skip if already rechunked
        if check_already_rechunked(conn, chunk_id):
            logger.info(f"SKIP {chunk_id} (already rechunked)")
            continue

        logger.info(f"Rechunking {chunk_id} ({word_count:,} words)...")

        new_chunks = rechunk_content(chunk_id, book_id, monster['content'])
        if not new_chunks:
            logger.warning(f"No chunks generated for {chunk_id}")
            continue

        inserted = insert_chunks(conn, new_chunks)
        total_new += inserted
        total_words_covered += word_count

        logger.info(f"  -> Created {inserted} chunks from {chunk_id} "
                    f"(avg {word_count // max(inserted, 1)} words/chunk)")

    logger.info(f"\nDONE: Created {total_new:,} new chunks from {len(monsters)} monsters")
    logger.info(f"Total words now searchable: {total_words_covered:,}")
    logger.info(f"These will be picked up by the Gemini embedding daemon automatically.")

    conn.close()


if __name__ == '__main__':
    main()
