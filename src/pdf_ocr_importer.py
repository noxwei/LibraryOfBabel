#!/usr/bin/env python3
"""
PDF OCR Importer — Integration layer between babel-glm-ocr and LibraryOfBabel.

Handles scanned PDFs that can't be ingested through the standard EPUB pipeline:
1. Detects whether a PDF has extractable native text or is a scanned image
2. Runs OCR via babel-glm-ocr for scanned PDFs (uses Apple Silicon MPS / CUDA)
3. Groups OCR output pages into chapter-like chunks
4. Inserts the book and chunks into the LibraryOfBabel PostgreSQL database

Typical usage
-------------
    from pdf_ocr_importer import PDFOCRImporter

    importer = PDFOCRImporter(db_config={
        "host": "localhost", "dbname": "knowledge_base",
        "user": "postgres", "password": "",
    })
    result = importer.import_pdf(
        "/path/to/scanned_book.pdf",
        metadata={"title": "My Book", "author": "Author Name"},
    )
    print(result)

CLI usage
---------
    python pdf_ocr_importer.py /path/to/scanned.pdf --title "Title" --author "Author"
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class PDFImportResult:
    """Summary of a completed PDF import."""
    pdf_path: str
    book_id: Optional[int] = None
    chunks_inserted: int = 0
    pages_processed: int = 0
    used_ocr: bool = False
    processing_time: float = 0.0
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None and self.book_id is not None

    def __str__(self) -> str:
        if self.success:
            mode = "OCR" if self.used_ocr else "native text"
            return (
                f"Imported '{Path(self.pdf_path).name}' as book_id={self.book_id} "
                f"via {mode}: {self.pages_processed} pages → {self.chunks_inserted} chunks "
                f"({self.processing_time:.1f}s)"
            )
        return f"FAILED '{Path(self.pdf_path).name}': {self.error}"


# ---------------------------------------------------------------------------
# Core importer
# ---------------------------------------------------------------------------

class PDFOCRImporter:
    """
    Imports scanned PDFs into LibraryOfBabel using babel-glm-ocr.

    Parameters
    ----------
    db_config:
        psycopg2-compatible connection dict.
        Defaults to localhost/knowledge_base.
    device:
        "cuda", "mps", or "cpu". Auto-detected when None.
    dpi:
        Rasterisation DPI for scanned pages (150 = fast, 300 = sharper).
    pages_per_chapter:
        How many OCR pages to group into one logical "chapter" for chunking.
        Scanned books rarely have chapter markers, so we use page groups.
    max_new_tokens:
        Token budget per OCR page — increase for very dense pages.
    """

    _DEFAULT_DB = {
        "host": "localhost",
        "dbname": "knowledge_base",
        "user": "postgres",
        "password": "",
        "port": 5432,
    }

    def __init__(
        self,
        db_config: Optional[Dict[str, Any]] = None,
        device: Optional[str] = None,
        dpi: int = 150,
        pages_per_chapter: int = 10,
        max_new_tokens: int = 2048,
    ) -> None:
        self.db_config = {**self._DEFAULT_DB, **(db_config or {})}
        self.device = device
        self.dpi = dpi
        self.pages_per_chapter = pages_per_chapter
        self.max_new_tokens = max_new_tokens

        # Lazy imports so the module loads even if deps are missing on one side
        self._ocr_engine = None
        self._text_chunker = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def import_pdf(
        self,
        pdf_path: str | Path,
        metadata: Optional[Dict[str, str]] = None,
        force_ocr: bool = False,
        page_range: Optional[tuple[int, int]] = None,
    ) -> PDFImportResult:
        """
        Import a single PDF into LibraryOfBabel.

        Parameters
        ----------
        pdf_path:
            Path to the PDF file.
        metadata:
            Optional dict with keys: title, author, publisher, publication_date,
            language, isbn, description. Missing keys get sensible defaults.
        force_ocr:
            Skip the native-text fast-path and always run OCR.
        page_range:
            (start, end) 1-indexed inclusive page range. None = all pages.
        """
        start_time = time.time()
        pdf_path = Path(pdf_path)
        metadata = metadata or {}
        result = PDFImportResult(pdf_path=str(pdf_path))

        if not pdf_path.exists():
            result.error = f"File not found: {pdf_path}"
            return result

        try:
            pages_text, used_ocr = self._extract_text(pdf_path, force_ocr, page_range)
        except Exception as exc:
            result.error = f"Text extraction failed: {exc}"
            logger.exception("Text extraction error for %s", pdf_path)
            return result

        if not pages_text:
            result.error = "No text could be extracted from the PDF"
            return result

        result.pages_processed = len(pages_text)
        result.used_ocr = used_ocr

        # Build the book + chapter structures that LibraryOfBabel expects
        book_metadata, chapters = self._build_structures(pdf_path, metadata, pages_text)

        # Chunk the content
        chunks = self._get_chunker().chunk_book(book_metadata, chapters)

        # Ingest into the database
        try:
            book_id, chunks_inserted = self._ingest(book_metadata, chunks)
            result.book_id = book_id
            result.chunks_inserted = chunks_inserted
        except Exception as exc:
            result.error = f"Database ingestion failed: {exc}"
            logger.exception("Ingestion error for %s", pdf_path)

        result.processing_time = time.time() - start_time
        return result

    # ------------------------------------------------------------------
    # Text extraction
    # ------------------------------------------------------------------

    def _extract_text(
        self,
        pdf_path: Path,
        force_ocr: bool,
        page_range: Optional[tuple[int, int]],
    ) -> tuple[List[tuple[int, str]], bool]:
        """
        Return (list of (page_num, text) pairs, used_ocr flag).

        Fast-path: if the PDF contains embedded text, extract it directly.
        Slow-path: run GLM-Edge-V OCR page by page.
        """
        from babel_glm_ocr.pdf import has_extractable_text, extract_native_text
        from babel_glm_ocr.pdf import pdf_page_images

        if not force_ocr and has_extractable_text(pdf_path):
            logger.info("%s has native text — skipping OCR", pdf_path.name)
            raw_pages = extract_native_text(pdf_path)
            pages: List[tuple[int, str]] = []
            for i, text in enumerate(raw_pages, start=1):
                if page_range:
                    start, end = page_range
                    if i < start:
                        continue
                    if i > end:
                        break
                pages.append((i, text))
            return pages, False

        # OCR path
        logger.info("%s needs OCR — loading model (device=%s)", pdf_path.name, self.device or "auto")
        engine = self._get_ocr_engine()
        if page_range:
            engine.page_range = page_range

        pages = []
        for ocr_page in engine.stream_pdf(pdf_path):
            pages.append((ocr_page.page_number, ocr_page.text))
            logger.info("  OCR page %d complete (%d chars)", ocr_page.page_number, len(ocr_page.text))

        return pages, True

    # ------------------------------------------------------------------
    # Structure building
    # ------------------------------------------------------------------

    def _build_structures(
        self,
        pdf_path: Path,
        metadata: Dict[str, str],
        pages: List[tuple[int, str]],
    ):
        """Build BookMetadata and ChapterInfo objects from raw page text."""
        # Import dataclasses from LibraryOfBabel (same package namespace)
        from epub_processor import BookMetadata, ChapterInfo

        title = metadata.get("title") or pdf_path.stem.replace("_", " ").title()
        author = metadata.get("author", "Unknown")

        # Merge pages into chapter-sized groups
        chapters: List[ChapterInfo] = []
        page_groups = self._group_pages(pages, self.pages_per_chapter)

        for group_idx, group in enumerate(page_groups, start=1):
            page_nums = [p for p, _ in group]
            combined_text = "\n\n".join(text for _, text in group if text.strip())

            if not combined_text.strip():
                continue  # skip blank groups (e.g. image-only pages that gave empty OCR)

            words = combined_text.split()
            chapter = ChapterInfo(
                title=f"Pages {page_nums[0]}–{page_nums[-1]}",
                content=combined_text,
                chapter_number=group_idx,
                section_number=None,
                word_count=len(words),
                file_path=str(pdf_path),
                spine_order=group_idx,
            )
            chapters.append(chapter)

        total_words = sum(c.word_count for c in chapters)

        book_meta = BookMetadata(
            title=title,
            author=author,
            publisher=metadata.get("publisher"),
            publication_date=metadata.get("publication_date"),
            language=metadata.get("language", "english"),
            isbn=metadata.get("isbn"),
            description=metadata.get("description"),
            subject=metadata.get("subject"),
            total_chapters=len(chapters),
            total_words=total_words,
            file_path=str(pdf_path),
        )

        return book_meta, chapters

    @staticmethod
    def _group_pages(
        pages: List[tuple[int, str]], group_size: int
    ) -> List[List[tuple[int, str]]]:
        """Split pages into fixed-size groups."""
        groups = []
        for i in range(0, len(pages), group_size):
            groups.append(pages[i : i + group_size])
        return groups

    # ------------------------------------------------------------------
    # Database ingestion
    # ------------------------------------------------------------------

    def _ingest(self, book_metadata, chunks) -> tuple[int, int]:
        """Insert book + chunks into PostgreSQL. Returns (book_id, chunks_inserted)."""
        import psycopg2
        from database_ingestion import DatabaseIngestor

        book_data = {
            "metadata": {
                "title": book_metadata.title,
                "author": book_metadata.author,
                "publisher": book_metadata.publisher or "",
                "publication_date": book_metadata.publication_date or "",
                "language": book_metadata.language,
                "isbn": book_metadata.isbn or "",
                "description": book_metadata.description or "",
                "total_words": book_metadata.total_words,
                "source_location": book_metadata.file_path,
                "import_source": "pdf_ocr",
            }
        }

        chunks_data = [
            {
                "chunk_id": c.chunk_id,
                "chunk_type": c.chunk_type.value,
                "title": c.title,
                "content": c.content,
                "word_count": c.word_count,
                "character_count": c.character_count,
                "chapter_number": c.chapter_number,
                "section_number": c.section_number,
                "paragraph_number": c.paragraph_number,
                "start_position": c.start_position,
                "end_position": c.end_position,
                "parent_chunk_id": c.parent_chunk_id,
            }
            for c in chunks
        ]

        ingestor = DatabaseIngestor(self.db_config)
        if not ingestor.connect():
            raise RuntimeError("Cannot connect to database")

        try:
            with ingestor.connection:
                cursor = ingestor.connection.cursor()
                book_id = ingestor.insert_book(cursor, book_data)
                if book_id is None:
                    raise RuntimeError("insert_book returned None")
                inserted = ingestor.insert_chunks(cursor, book_id, chunks_data)
            return book_id, inserted
        finally:
            ingestor.disconnect()

    # ------------------------------------------------------------------
    # Lazy component accessors
    # ------------------------------------------------------------------

    def _get_ocr_engine(self):
        if self._ocr_engine is None:
            from babel_glm_ocr import OCREngine
            self._ocr_engine = OCREngine(
                device=self.device,
                dpi=self.dpi,
                max_new_tokens=self.max_new_tokens,
            )
        return self._ocr_engine

    def _get_chunker(self):
        if self._text_chunker is None:
            from text_chunker import TextChunker
            self._text_chunker = TextChunker()
        return self._text_chunker


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Import a scanned PDF into LibraryOfBabel via OCR",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("pdf", help="Path to the PDF file")
    p.add_argument("--title", default=None, help="Book title (defaults to filename)")
    p.add_argument("--author", default="Unknown", help="Book author")
    p.add_argument("--publisher", default=None)
    p.add_argument("--isbn", default=None)
    p.add_argument("--language", default="english")
    p.add_argument("--description", default=None)
    p.add_argument("--device", default=None, choices=["cuda", "mps", "cpu"])
    p.add_argument("--dpi", type=int, default=150, help="Rasterisation DPI for OCR")
    p.add_argument("--pages-per-chapter", type=int, default=10,
                   help="PDF pages to merge into one chapter chunk")
    p.add_argument("--pages", default=None, metavar="START-END",
                   help="Restrict to page range, e.g. 1-50")
    p.add_argument("--force-ocr", action="store_true",
                   help="Always OCR, even if the PDF has native text")
    p.add_argument("--db-host", default="localhost")
    p.add_argument("--db-name", default="knowledge_base")
    p.add_argument("--db-user", default="postgres")
    p.add_argument("--db-password", default="")
    p.add_argument("--db-port", type=int, default=5432)
    p.add_argument("--log-level", default="INFO",
                   choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return p


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    page_range = None
    if args.pages:
        try:
            start, end = args.pages.split("-")
            page_range = (int(start), int(end))
        except ValueError:
            parser.error("--pages must be in START-END format, e.g. 1-50")

    metadata = {
        k: v for k, v in {
            "title": args.title,
            "author": args.author,
            "publisher": args.publisher,
            "isbn": args.isbn,
            "language": args.language,
            "description": args.description,
        }.items() if v is not None
    }

    importer = PDFOCRImporter(
        db_config={
            "host": args.db_host,
            "dbname": args.db_name,
            "user": args.db_user,
            "password": args.db_password,
            "port": args.db_port,
        },
        device=args.device,
        dpi=args.dpi,
        pages_per_chapter=args.pages_per_chapter,
    )

    result = importer.import_pdf(
        args.pdf,
        metadata=metadata,
        force_ocr=args.force_ocr,
        page_range=page_range,
    )

    print(result)
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
