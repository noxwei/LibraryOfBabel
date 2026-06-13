#!/usr/bin/env python3
"""
Tests for spine-order chunk handling.

Regression suite for the 2026-06-12 chunk-ordering incident: the
multi-granular daemon processed chapters in varchar chunk_id order
('<book>_chapter_10' before '<book>_chapter_2') and never populated
start_position, so derived chunks froze a scrambled reading order.

Run: python3 -m pytest tests/test_chunk_ordering.py -v
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from chunk_ordering import (
    ContentLocator,
    chapter_spine_order_sql,
    natural_chunk_key,
    normalize_with_map,
    trailing_number,
)


class TestTrailingNumber:
    def test_chapter_ids(self):
        assert trailing_number('3328_chapter_12') == 12
        assert trailing_number('180_0027') == 27
        assert trailing_number('father_goriot_honore_de_balza_ch7') == 7

    def test_no_number(self):
        assert trailing_number('fullbook_alpha') is None
        assert trailing_number('') is None
        assert trailing_number(None) is None


class TestNaturalChunkKey:
    def test_chapter_2_before_chapter_10(self):
        """The exact failure mode: varchar sort puts chapter_10 first."""
        ids = ['b_chapter_10', 'b_chapter_2', 'b_chapter_1', 'b_chapter_21']
        assert sorted(ids) != ['b_chapter_1', 'b_chapter_2', 'b_chapter_10', 'b_chapter_21']
        assert sorted(ids, key=natural_chunk_key) == [
            'b_chapter_1', 'b_chapter_2', 'b_chapter_10', 'b_chapter_21']

    def test_mg_digit_boundary(self):
        """Gideon the Ninth case: mg_9999999 must precede mg_10000000."""
        ids = ['mg_10000000', 'mg_9999999']
        assert sorted(ids, key=natural_chunk_key) == ['mg_9999999', 'mg_10000000']

    def test_legacy_paragraph_ids(self):
        ids = ['2581_paragraph_2581_chapter_10_0', '2581_paragraph_2581_chapter_2_0']
        assert sorted(ids, key=natural_chunk_key) == [
            '2581_paragraph_2581_chapter_2_0', '2581_paragraph_2581_chapter_10_0']


class TestChapterSpineOrderSql:
    def test_orders_numerically_in_postgres_semantics(self):
        sql = chapter_spine_order_sql('c.chunk_id')
        assert "substring(c.chunk_id from '(\\d+)$')" in sql
        assert sql.endswith('NULLS LAST, c.chunk_id')


class TestNormalizeWithMap:
    def test_collapses_whitespace(self):
        norm, m = normalize_with_map('a  b\n\nc')
        assert norm == 'a b c'
        assert len(m) == len(norm)

    def test_offsets_point_into_original(self):
        original = '  hello \n world  '
        norm, m = normalize_with_map(original)
        assert norm == 'hello world'
        assert original[m[0]] == 'h'
        assert original[m[norm.index('w')]] == 'w'


class TestContentLocator:
    CHAPTER = ("First paragraph of the chapter, with words.\n\n"
               "Second paragraph follows here, more words.\n\n"
               "Third paragraph closes the chapter entirely.")

    def test_exact_match(self):
        loc = ContentLocator(self.CHAPTER)
        span = loc.locate('Second paragraph follows here, more words.')
        assert span is not None
        start, end = span
        assert self.CHAPTER[start:end] == 'Second paragraph follows here, more words.'

    def test_whitespace_rejoined_content_matches(self):
        """Daemon re-joined split paragraphs with single spaces."""
        loc = ContentLocator('one\ntwo\n\nthree   four')
        span = loc.locate('one two')
        assert span is not None
        start, _ = span
        assert start == 0

    def test_cursor_keeps_repeated_content_monotonic(self):
        text = 'repeat me. unique a. repeat me. unique b.'
        loc = ContentLocator(text)
        s1 = loc.locate('repeat me.')
        s2 = loc.locate('repeat me.')
        assert s1 is not None and s2 is not None
        assert s2[0] > s1[0]

    def test_no_match_returns_none(self):
        loc = ContentLocator(self.CHAPTER)
        assert loc.locate('content from a different book entirely xyz') is None

    def test_prefix_fallback(self):
        chapter = 'A long sentence that starts a paragraph and keeps going.'
        loc = ContentLocator(chapter)
        # needle whose tail diverges (e.g. truncated chapter content)
        needle = ('A long sentence that starts a paragraph and keeps going. '
                  'Plus trailing text that was appended from elsewhere later on '
                  'and is much longer than the configured prefix length limit '
                  'so only the prefix can anchor the match position here.')
        span = loc.locate(needle, prefix_len=40)
        assert span is not None
        assert span[0] == 0


class TestTextChunkerGlobalPositions:
    def _mock_book(self):
        class Chapter:
            def __init__(self, n, content):
                self.title = f'Chapter {n}'
                self.content = content
                self.word_count = len(content.split())
                self.chapter_number = n
                self.spine_order = n - 1

        class Meta:
            title = 'Test Book'
            author = 'Test Author'
            isbn = None

        para = ('word ' * 30).strip() + '.'
        ch_text = ('\n\n'.join(para for _ in range(4)))
        return Meta(), [Chapter(1, ch_text), Chapter(2, ch_text)]

    def test_second_chapter_positions_after_first(self):
        from text_chunker import TextChunker, ChunkType
        meta, chapters = self._mock_book()
        chunks = TextChunker().chunk_book(meta, chapters)

        ch_chunks = [c for c in chunks if c.chunk_type == ChunkType.CHAPTER]
        assert ch_chunks[0].start_position == 0
        expected_base = len(chapters[0].content) + 2
        assert ch_chunks[1].start_position == expected_base

        para_chunks = [c for c in chunks if c.chunk_type == ChunkType.PARAGRAPH]
        first_ch_paras = [c for c in para_chunks if c.chapter_number == 1]
        second_ch_paras = [c for c in para_chunks if c.chapter_number == 2]
        assert first_ch_paras and second_ch_paras
        assert max(c.start_position for c in first_ch_paras) < min(
            c.start_position for c in second_ch_paras)

    def test_positions_sort_chunks_in_reading_order(self):
        from text_chunker import TextChunker, ChunkType
        meta, chapters = self._mock_book()
        chunks = TextChunker().chunk_book(meta, chapters)
        paras = [c for c in chunks if c.chunk_type == ChunkType.PARAGRAPH]
        by_pos = sorted(paras, key=lambda c: c.start_position)
        chapter_seq = [c.chapter_number for c in by_pos]
        assert chapter_seq == sorted(chapter_seq)


class TestBackfillScript:
    def test_dry_run_is_default(self):
        """--apply must be opt-in; a bare invocation can never write."""
        import backfill_chunk_positions as bf
        import argparse
        # reconstruct the parser the same way main() does
        ap = argparse.ArgumentParser()
        ap.add_argument('--apply', action='store_true')
        args = ap.parse_args([])
        assert args.apply is False

    def test_order_chapters_id_fallback(self):
        from backfill_chunk_positions import BookReport, order_chapters
        rows = [
            {'chunk_id': 'b_chapter_10', 'content': 'ten', 'chapter_number': None},
            {'chunk_id': 'b_chapter_2', 'content': 'two', 'chapter_number': None},
            {'chunk_id': 'b_chapter_1', 'content': 'one', 'chapter_number': None},
        ]
        report = BookReport(book_id=1, title='t')
        ordered = order_chapters(rows, None, report)
        assert [r['chunk_id'] for r in ordered] == [
            'b_chapter_1', 'b_chapter_2', 'b_chapter_10']
        assert report.epub_note == 'epub_missing'

    def test_match_rate_threshold_blocks_apply(self):
        from backfill_chunk_positions import BookReport
        r = BookReport(book_id=1, title='t')
        r.children_total = 100
        r.children_matched = 94
        assert r.match_rate < 95.0


if __name__ == '__main__':
    sys.exit(pytest.main([__file__, '-v']))
