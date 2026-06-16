#!/usr/bin/env python3
"""
Block-aware paragraph ingester for LibraryOfBabel.

The legacy path (EPUBProcessor -> TextChunker) collapses all whitespace
(`re.sub(r'\\s+', ' ')`) BEFORE chunking, so paragraph boundaries are gone and
the "paragraph" chunker emits a handful of ~15k-word monster blobs (this is
what produced the 100%-capture anomaly books: Battle of Corrin = 69 chunks,
Princess of Dune = 45). Those read terribly in the reading room and embed
poorly.

This ingester instead extracts text block-by-block (the same approach the
life-dashboard upload path uses), then groups consecutive blocks into
~150-word `paragraph` chunks with a small overlap, matching the bulk corpus
(~150 words/chunk). Embeddings are left NULL for the batch daemon to fill in.

Usage:
    python3.13 scripts/ingest_epub_paragraphs.py <epub_path> \
        --title "God Emperor of Dune" --author "Frank Herbert" [--genre Fiction] [--dry-run]

Title/author should be the catalog (Plex) names so the life-dashboard reading
room's resolve_lob_book() matches them.
"""
import os
import re
import sys
import argparse
import zipfile
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import psycopg2

DB = {"dbname": "knowledge_base", "user": "weixiangzhang", "host": "localhost", "port": 5432}

TARGET_WORDS = 150          # aim per paragraph chunk (corpus median ~150)
MAX_WORDS = 200             # hard cap before forcing a new chunk
OVERLAP_WORDS = 25          # small context overlap between chunks
BLOCK_TAGS = ["p", "div", "blockquote", "section", "h1", "h2", "h3", "h4", "h5", "h6", "li"]


def _opf_path(zf):
    root = ET.fromstring(zf.read("META-INF/container.xml"))
    ns = {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}
    rf = root.find(".//c:rootfile", ns)
    if rf is None:
        rf = root.find(".//rootfile")
    return rf.get("full-path")


def _spine_docs(zf, opf, opf_dir):
    root = ET.fromstring(zf.read(opf))
    OPF = "{http://www.idpf.org/2007/opf}"
    manifest = {it.get("id"): it.get("href") for it in root.iter(f"{OPF}item")}
    media = {it.get("id"): it.get("media-type", "") for it in root.iter(f"{OPF}item")}
    docs = []
    for ref in root.iter(f"{OPF}itemref"):
        if ref.get("linear", "yes") == "no":
            continue
        iid = ref.get("idref")
        href = manifest.get(iid)
        if not href or not any(x in media.get(iid, "") for x in ("html", "xhtml")):
            continue
        docs.append(f"{opf_dir}/{href}" if opf_dir else href)
    return docs


def extract_paragraphs(epub_path):
    """Block-level paragraphs in spine order. Skips containers that hold other
    blocks (avoid double-counting), drops empties/pure-numbers, dedups long
    repeats per document."""
    paras = []
    with zipfile.ZipFile(epub_path) as zf:
        opf = _opf_path(zf)
        opf_dir = os.path.dirname(opf)
        names = set(zf.namelist())
        for doc in _spine_docs(zf, opf, opf_dir):
            if doc not in names:
                continue
            soup = BeautifulSoup(zf.read(doc).decode("utf-8", "ignore"), "html.parser")
            for bad in soup(["script", "style"]):
                bad.decompose()
            seen = set()
            for el in soup.find_all(BLOCK_TAGS):
                if el.find(BLOCK_TAGS):           # not a leaf block — skip
                    continue
                text = re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
                if len(text) < 2 or text.isdigit():
                    continue
                if len(text) >= 40:               # dedup only long lines
                    if text in seen:
                        continue
                    seen.add(text)
                paras.append(text)
    return paras


def group_into_chunks(paras):
    """Group consecutive paragraphs into ~TARGET_WORDS chunks with overlap.
    Returns list of (content, word_count, char_count, start_position)."""
    chunks = []
    buf, buf_words = [], 0
    char_cursor = 0
    for p in paras:
        pw = len(p.split())
        if buf and buf_words + pw > MAX_WORDS:
            content = " ".join(buf)
            chunks.append((content, buf_words, len(content), char_cursor))
            char_cursor += len(content) + 1
            # carry an overlap tail into the next chunk
            tail, tw = [], 0
            for s in reversed(buf):
                tail.insert(0, s)
                tw += len(s.split())
                if tw >= OVERLAP_WORDS:
                    break
            buf, buf_words = tail[:], sum(len(s.split()) for s in tail)
        buf.append(p)
        buf_words += pw
        if buf_words >= TARGET_WORDS and buf_words <= MAX_WORDS:
            content = " ".join(buf)
            chunks.append((content, buf_words, len(content), char_cursor))
            char_cursor += len(content) + 1
            tail, tw = [], 0
            for s in reversed(buf):
                tail.insert(0, s)
                tw += len(s.split())
                if tw >= OVERLAP_WORDS:
                    break
            buf, buf_words = tail[:], sum(len(s.split()) for s in tail)
    if buf_words > 0:
        content = " ".join(buf)
        chunks.append((content, buf_words, len(content), char_cursor))
    # keep only chunks with real content (>= 50 words, matches corpus floor)
    return [c for c in chunks if c[1] >= 50]


def book_exists(cur, title, author):
    cur.execute("SELECT book_id FROM books WHERE lower(title)=lower(%s) AND lower(author)=lower(%s)",
                (title, author))
    return cur.fetchone()


def ingest(epub_path, title, author, genre, dry_run):
    paras = extract_paragraphs(epub_path)
    chunks = group_into_chunks(paras)
    # true book length = unique paragraph words (chunk sums double-count overlap)
    total_words = sum(len(p.split()) for p in paras)
    print(f"  extracted {len(paras)} blocks -> {len(chunks)} paragraph chunks, {total_words:,} words")
    if not chunks:
        print("  ABORT: no chunks produced")
        return None
    ws = sorted(c[1] for c in chunks)
    print(f"  chunk words min/median/max: {ws[0]}/{ws[len(ws)//2]}/{ws[-1]}")
    if dry_run:
        print("  [dry-run] not writing to DB")
        return None

    conn = psycopg2.connect(**DB)
    try:
        with conn, conn.cursor() as cur:
            if book_exists(cur, title, author):
                print(f"  SKIP: '{title}' by {author} already in corpus")
                return None
            cur.execute(
                """INSERT INTO books (title, author, genre, word_count, import_source, processed_date)
                   VALUES (%s,%s,%s,%s,'paragraph_ingest',now()) RETURNING book_id""",
                (title[:500], author[:255], (genre or "Fiction")[:100], total_words))
            book_id = cur.fetchone()[0]
            for seq, (content, wc, cc, sp) in enumerate(chunks, 1):
                cur.execute(
                    """INSERT INTO chunks
                       (chunk_id, book_id, chunk_type, title, content, word_count,
                        character_count, start_position, search_vector)
                       VALUES (%s,%s,'paragraph',%s,%s,%s,%s,%s,
                               to_tsvector('english', %s))""",
                    (f"{book_id}_paragraph_{seq:05d}", book_id, title[:500],
                     content, wc, cc, sp, content))
            # word_count set here (not the INSERT) — set in the same statement
            # that reliably persists chunk_count.
            cur.execute("UPDATE books SET word_count=%s, chunk_count=%s, searchable_chunk_count=%s WHERE book_id=%s",
                        (total_words, len(chunks), len(chunks), book_id))
        print(f"  OK: book_id={book_id}, {len(chunks)} chunks inserted (embeddings pending)")
        return book_id
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("epub")
    ap.add_argument("--title", required=True)
    ap.add_argument("--author", required=True)
    ap.add_argument("--genre", default="Fiction")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if not os.path.isfile(a.epub):
        sys.exit(f"not found: {a.epub}")
    print(f"Ingesting: {a.title} by {a.author}")
    ingest(a.epub, a.title, a.author, a.genre, a.dry_run)


if __name__ == "__main__":
    main()
