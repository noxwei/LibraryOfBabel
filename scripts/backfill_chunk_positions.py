#!/usr/bin/env python3
"""
Backfill chunks.start_position in true spine order
===================================================

Root cause (2026-06-12): the multi-granular chunking daemon
(daemons/progressive_chunking_daemon.py, commit 00afc6a, ran 2025-08-01/02)
fetched chapter chunks with `ORDER BY c.chunk_id` — a varchar sort — so
'<book>_chapter_10' was processed before '<book>_chapter_2'. The original
version also omitted chunk_id on INSERT, letting the `mg_N` sequence default
freeze that scrambled processing order into the ids. start_position was never
populated by any ingest path, so every consumer that sorted by chunk_id (or
even by numeric mg_ id) read those books out of order.

This script recomputes a book-global start_position for chapter, paragraph
and section chunks:

1. Chapter chunks are put in spine order using the trailing number of their
   chunk_id (assigned by enumerate() over the EPUB spine at ingest; the
   chapter_number column is parsed from titles/filenames and is unreliable).
   If the source EPUB is still on disk (books.file_path), the chapter order
   is verified against the actual EPUB spine and the spine wins on conflict.
2. Each chapter gets a base offset = cumulative length of preceding chapters.
3. Each paragraph/section chunk is located inside its parent chapter content
   (whitespace-normalized, cursor-based) → start_position = base + offset.

Safety:
- DRY-RUN BY DEFAULT. Nothing is written without --apply.
- Books with a match rate below --min-match (default 95%) are NEVER updated.
- Per-book report: chunks matched, match %, mean/max reorder distance.

Usage:
    python3 scripts/backfill_chunk_positions.py                 # dry-run, all books
    python3 scripts/backfill_chunk_positions.py --book 2415     # dry-run, one book
    python3 scripts/backfill_chunk_positions.py --book 2415 --apply
"""

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import psycopg2
import psycopg2.extras

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from chunk_ordering import (  # noqa: E402
    ContentLocator,
    natural_chunk_key,
    normalize_with_map,
    trailing_number,
)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'knowledge_base'),
    'user': os.getenv('DB_USER', 'weixiangzhang'),
    'port': int(os.getenv('DB_PORT', '5432')),
}

CHAPTER_SEPARATOR = 2  # virtual chars between chapters in the global offset


@dataclass
class BookReport:
    book_id: int
    title: str
    chapters: int = 0
    children_total: int = 0
    children_matched: int = 0
    children_fallback: int = 0  # placed at chapter base (content not located)
    order_source: str = 'chunk_id'  # chunk_id | epub | epub_reordered
    epub_note: str = ''
    mean_displacement: float = 0.0
    max_displacement: int = 0
    applied: bool = False
    skipped_reason: str = ''

    @property
    def match_rate(self) -> float:
        if self.children_total == 0:
            return 100.0
        return 100.0 * self.children_matched / self.children_total


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


# ---------------------------------------------------------------------------
# EPUB spine verification
# ---------------------------------------------------------------------------

def resolve_epub_path(file_path: Optional[str]) -> Optional[Path]:
    if not file_path:
        return None
    p = Path(file_path)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return p if p.is_file() else None


def epub_spine_order(epub_path: Path, chapter_rows: List[dict]) -> Optional[Dict[str, int]]:
    """Map chapter chunk_id -> spine index by matching content to the EPUB.

    Returns None if the EPUB cannot be parsed or fewer than 95% of chapters
    match a unique spine position.
    """
    try:
        from epub_processor import EPUBProcessor
        _, epub_chapters = EPUBProcessor().process_epub(str(epub_path))
    except Exception:
        return None
    if not epub_chapters:
        return None

    spine_norms = []
    for ch in epub_chapters:
        norm, _ = normalize_with_map(ch.content or '')
        spine_norms.append(norm)

    mapping: Dict[str, int] = {}
    used = set()
    for row in chapter_rows:
        norm, _ = normalize_with_map(row['content'] or '')
        probe = norm[:200]
        if not probe:
            continue
        for idx, spine_norm in enumerate(spine_norms):
            if idx in used:
                continue
            if probe in spine_norm:
                mapping[row['chunk_id']] = idx
                used.add(idx)
                break

    if len(mapping) < 0.95 * len(chapter_rows):
        return None
    return mapping


# ---------------------------------------------------------------------------
# Per-book processing
# ---------------------------------------------------------------------------

def order_chapters(chapter_rows: List[dict], epub_path: Optional[Path],
                   report: BookReport) -> List[dict]:
    """Return chapter rows in spine order."""
    by_id = sorted(
        chapter_rows,
        key=lambda r: (
            trailing_number(r['chunk_id']) if trailing_number(r['chunk_id']) is not None else float('inf'),
            r['chunk_id'],
        ),
    )

    if epub_path is None:
        report.epub_note = 'epub_missing'
        return by_id

    mapping = epub_spine_order(epub_path, chapter_rows)
    if mapping is None:
        report.epub_note = 'epub_unmatched'
        return by_id

    matched = [r for r in chapter_rows if r['chunk_id'] in mapping]
    unmatched = [r for r in chapter_rows if r['chunk_id'] not in mapping]
    by_spine = sorted(matched, key=lambda r: mapping[r['chunk_id']])
    # Unmatched chapters (e.g. too short for the EPUB parser) keep their
    # id-derived relative order, appended at the end.
    by_spine += sorted(unmatched, key=lambda r: natural_chunk_key(r['chunk_id']))

    if [r['chunk_id'] for r in by_spine] == [r['chunk_id'] for r in by_id]:
        report.order_source = 'epub'
    else:
        report.order_source = 'epub_reordered'
    return by_spine


def child_sort_key(row: dict):
    """Within-chapter derivation order: numeric-aware chunk_id order.

    mg_ ids are sequence-assigned in derivation order within a chapter;
    legacy ids carry the derivation index as their trailing number.
    """
    return natural_chunk_key(row['chunk_id'])


def process_book(conn, book_id: int, min_match: float, apply: bool) -> BookReport:
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT title, file_path FROM books WHERE book_id = %s", (book_id,))
    book = cur.fetchone()
    report = BookReport(book_id=book_id, title=(book['title'] if book else '?') or '?')
    if not book:
        report.skipped_reason = 'book_not_found'
        return report

    cur.execute("""
        SELECT chunk_id, content, chapter_number
        FROM chunks
        WHERE book_id = %s AND chunk_type = 'chapter' AND content IS NOT NULL
    """, (book_id,))
    chapter_rows = cur.fetchall()
    report.chapters = len(chapter_rows)
    if not chapter_rows:
        report.skipped_reason = 'no_chapter_chunks'
        return report

    cur.execute("""
        SELECT chunk_id, parent_chunk_id, content, chunk_type, start_position
        FROM chunks
        WHERE book_id = %s AND chunk_type IN ('paragraph', 'section')
          AND content IS NOT NULL
    """, (book_id,))
    child_rows = cur.fetchall()
    report.children_total = len(child_rows)
    if not child_rows:
        report.skipped_reason = 'no_child_chunks'
        return report

    epub_path = resolve_epub_path(book['file_path'])
    ordered_chapters = order_chapters(chapter_rows, epub_path, report)

    # Chapter base offsets in spine order
    chapter_base: Dict[str, int] = {}
    offset = 0
    for ch in ordered_chapters:
        chapter_base[ch['chunk_id']] = offset
        offset += len(ch['content']) + CHAPTER_SEPARATOR

    children_by_parent: Dict[str, List[dict]] = {}
    orphans: List[dict] = []
    for row in child_rows:
        parent = row['parent_chunk_id']
        if parent in chapter_base:
            children_by_parent.setdefault(parent, []).append(row)
        else:
            orphans.append(row)

    # Locate every child inside its parent chapter
    new_positions: Dict[str, tuple] = {}  # chunk_id -> (start, end)
    for ch in ordered_chapters:
        kids = children_by_parent.get(ch['chunk_id'])
        if not kids:
            continue
        base = chapter_base[ch['chunk_id']]
        # one locator per chunk_type: paragraphs and sections each sweep the
        # chapter monotonically in their own derivation order
        by_type: Dict[str, List[dict]] = {}
        for k in kids:
            by_type.setdefault(k['chunk_type'], []).append(k)
        for kids_of_type in by_type.values():
            locator = ContentLocator(ch['content'])
            for k in sorted(kids_of_type, key=child_sort_key):
                span = locator.locate(k['content'])
                if span is not None:
                    new_positions[k['chunk_id']] = (base + span[0], base + span[1])
                    report.children_matched += 1
                else:
                    new_positions[k['chunk_id']] = (base, base + len(k['content']))
                    report.children_fallback += 1

    # Orphans count against the match rate but are never positioned
    # (their parent is not a chapter chunk of this book).

    if report.match_rate < min_match:
        report.skipped_reason = f'match_rate {report.match_rate:.1f}% < {min_match}%'
        return report

    # Reorder distance: old order (numeric-aware chunk_id) vs new order
    placed = [r for r in child_rows if r['chunk_id'] in new_positions]
    old_order = sorted(placed, key=lambda r: natural_chunk_key(r['chunk_id']))
    new_order = sorted(placed, key=lambda r: (new_positions[r['chunk_id']][0],
                                              natural_chunk_key(r['chunk_id'])))
    old_rank = {r['chunk_id']: i for i, r in enumerate(old_order)}
    displacements = [abs(old_rank[r['chunk_id']] - i) for i, r in enumerate(new_order)]
    if displacements:
        report.mean_displacement = sum(displacements) / len(displacements)
        report.max_displacement = max(displacements)

    if apply:
        wcur = conn.cursor()
        # chapters first: base offsets become their global start_position
        chapter_updates = [
            (chapter_base[ch['chunk_id']],
             chapter_base[ch['chunk_id']] + len(ch['content']),
             ch['chunk_id'])
            for ch in ordered_chapters
        ]
        psycopg2.extras.execute_batch(wcur, """
            UPDATE chunks SET start_position = %s, end_position = %s
            WHERE chunk_id = %s
        """, chapter_updates, page_size=500)
        child_updates = [
            (start, end, chunk_id)
            for chunk_id, (start, end) in new_positions.items()
        ]
        psycopg2.extras.execute_batch(wcur, """
            UPDATE chunks SET start_position = %s, end_position = %s
            WHERE chunk_id = %s
        """, child_updates, page_size=500)
        conn.commit()
        report.applied = True

    return report


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def candidate_books(conn, only_books: Optional[List[int]], limit: Optional[int]) -> List[int]:
    cur = conn.cursor()
    if only_books:
        return only_books
    sql = """
        SELECT DISTINCT book_id FROM chunks
        WHERE chunk_type IN ('paragraph', 'section')
        ORDER BY book_id
    """
    if limit:
        sql += f" LIMIT {int(limit)}"
    cur.execute(sql)
    return [r[0] for r in cur.fetchall()]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--apply', action='store_true',
                    help='write start_position updates (default: dry-run)')
    ap.add_argument('--book', type=int, action='append',
                    help='restrict to one or more book_ids (repeatable)')
    ap.add_argument('--min-match', type=float, default=95.0,
                    help='minimum %% of child chunks located to allow apply (default 95)')
    ap.add_argument('--limit', type=int, default=None,
                    help='process at most N books (dry-run sampling)')
    ap.add_argument('--quiet', action='store_true', help='only print summary + problem books')
    args = ap.parse_args()

    conn = get_conn()
    books = candidate_books(conn, args.book, args.limit)
    mode = 'APPLY' if args.apply else 'DRY-RUN'
    print(f"[{mode}] processing {len(books)} book(s), min-match {args.min_match}%\n")

    reports: List[BookReport] = []
    for i, book_id in enumerate(books, 1):
        try:
            rep = process_book(conn, book_id, args.min_match, args.apply)
        except Exception as e:
            conn.rollback()
            rep = BookReport(book_id=book_id, title='?')
            rep.skipped_reason = f'error: {e}'
        reports.append(rep)
        line = (f"book {rep.book_id:>5}  ch={rep.chapters:<4} "
                f"chunks={rep.children_total:<6} match={rep.match_rate:6.1f}%  "
                f"disp(mean/max)={rep.mean_displacement:8.1f}/{rep.max_displacement:<6} "
                f"order={rep.order_source:<14} "
                f"{'APPLIED' if rep.applied else (rep.skipped_reason or 'ok')}  "
                f"{rep.title[:48]}")
        if not args.quiet or rep.skipped_reason or rep.applied:
            print(line)
        if i % 200 == 0:
            print(f"-- progress: {i}/{len(books)}")

    ok = [r for r in reports if not r.skipped_reason]
    skipped = [r for r in reports if r.skipped_reason]
    scrambled = [r for r in ok if r.max_displacement > 0]
    applied = [r for r in reports if r.applied]
    print("\n==== SUMMARY ====")
    print(f"books processed:        {len(reports)}")
    print(f"eligible (>= min-match): {len(ok)}")
    print(f"  with reordering:      {len(scrambled)}")
    print(f"skipped:                {len(skipped)}")
    for reason in sorted({r.skipped_reason.split(' ')[0] for r in skipped if r.skipped_reason}):
        n = sum(1 for r in skipped if r.skipped_reason.startswith(reason))
        print(f"  {reason}: {n}")
    print(f"applied:                {len(applied)}")
    if not args.apply:
        print("\nDry-run only. Re-run with --apply (ideally with --book) to write changes.")

    conn.close()


if __name__ == '__main__':
    main()
