#!/usr/bin/env python3
"""
Chunk Ordering Utilities
========================

Shared helpers for keeping chunks in true spine (reading) order.

Background (2026-06-12 root-cause): the multi-granular chunking daemon
fetched chapter chunks with `ORDER BY c.chunk_id` — a *varchar* sort — so
`<book>_chapter_10` was processed before `<book>_chapter_2`. The granular
INSERTs originally omitted chunk_id (DB default assigned sequential `mg_N`
ids) and never populated start_position, so the scrambled processing order
became the only "order" the corpus had. These helpers provide:

- trailing_number / natural_chunk_key: numeric-aware chunk_id ordering
- normalize_with_map: whitespace-normalized text with offset map back to
  the original string
- ContentLocator: cursor-based substring location of derived chunk content
  inside its parent chapter content (tolerant of whitespace re-joins)
- CHAPTER_SPINE_SQL: SQL fragment that orders chapter chunks by the
  trailing number of their chunk_id (assigned by enumerate() over the EPUB
  spine at ingest — the trustworthy order; the chapter_number column is
  parsed from titles/filenames and is NOT reliable)

Author: Librarian Agent
"""

import re
from typing import List, Optional, Tuple

# Chapter chunk ids end in the spine ordinal assigned at ingest time
# (enumerate over EPUB spine): e.g. "3328_chapter_12", "180_0027",
# "father_goriot_honore_de_balza_ch7".
_TRAILING_NUM_RE = re.compile(r'(\d+)$')

# SQL expression: trailing number of a chunk_id as bigint (NULL if none).
TRAILING_NUM_SQL = r"NULLIF(substring({col} from '(\d+)$'), '')::bigint"


def chapter_spine_order_sql(col: str = 'chunk_id') -> str:
    """ORDER BY fragment putting chapter chunks in spine order."""
    return f"{TRAILING_NUM_SQL.format(col=col)} NULLS LAST, {col}"


def trailing_number(chunk_id: str) -> Optional[int]:
    """Extract the trailing integer of a chunk_id (spine ordinal), if any."""
    if not chunk_id:
        return None
    m = _TRAILING_NUM_RE.search(chunk_id)
    return int(m.group(1)) if m else None


def natural_chunk_key(chunk_id: str) -> Tuple:
    """Sort key that orders embedded integers numerically.

    '2581_paragraph_2581_chapter_2_0' < '2581_paragraph_2581_chapter_10_0'
    and 'mg_9999999' < 'mg_10000000'.
    """
    parts = re.split(r'(\d+)', chunk_id or '')
    return tuple(int(p) if p.isdigit() else p for p in parts)


def normalize_with_map(text: str) -> Tuple[str, List[int]]:
    """Collapse whitespace runs to single spaces, keeping an offset map.

    Returns (normalized_text, offset_map) where offset_map[i] is the index
    in the ORIGINAL text of normalized character i.
    """
    norm_chars: List[str] = []
    offset_map: List[int] = []
    pending_space = False
    for i, ch in enumerate(text):
        if ch.isspace():
            if norm_chars:
                pending_space = True
            continue
        if pending_space:
            norm_chars.append(' ')
            # map the space to the position of the char that follows it
            offset_map.append(i)
            pending_space = False
        norm_chars.append(ch)
        offset_map.append(i)
    return ''.join(norm_chars), offset_map


class ContentLocator:
    """Locate derived chunk content inside its parent chapter content.

    Chunk content may have been re-joined with single spaces (the daemon
    split on paragraph boundaries and re-joined words), so matching is done
    on whitespace-normalized text and mapped back to original offsets.

    A moving cursor keeps repeated/overlapping content monotonic when
    chunks are presented in their original derivation order.
    """

    def __init__(self, haystack: str):
        self.haystack = haystack
        self.norm, self.offset_map = normalize_with_map(haystack)
        self.cursor = 0

    def locate(self, needle: str, prefix_len: int = 120) -> Optional[Tuple[int, int]]:
        """Return (start, end) offsets of needle in the original haystack.

        Tries, in order: full normalized match from the cursor, full match
        from the start, then a prefix match (first `prefix_len` normalized
        chars) from the cursor and from the start. Returns None if nothing
        matches.
        """
        norm_needle, _ = normalize_with_map(needle)
        if not norm_needle:
            return None

        candidates = [norm_needle]
        if len(norm_needle) > prefix_len:
            candidates.append(norm_needle[:prefix_len])

        for cand in candidates:
            for search_from in (self.cursor, 0):
                idx = self.norm.find(cand, search_from)
                if idx != -1:
                    start = self.offset_map[idx]
                    end_norm = min(idx + len(norm_needle), len(self.offset_map)) - 1
                    end = self.offset_map[end_norm] + 1
                    self.cursor = idx + 1
                    return start, end
        return None
