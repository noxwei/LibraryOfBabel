#!/usr/bin/env python3
"""Close the nomic-v2-moe coverage gap: embed chunks that have bge/gemini
embeddings but no nomic-v2-moe row (~84K, mostly context-length failures
from the May campaign).

Single process, single DB connection. Batch embed with per-item shrinking
truncation fallback for dense-tokenizing texts.
"""

import os
import re
import unicodedata

import psycopg2
import psycopg2.extras
import requests

OLLAMA_URL = "http://localhost:11434/api/embed"
MODEL = "nomic-embed-text-v2-moe"
BATCH_SIZE = 30
MAX_TEXT_LEN = 8000
FALLBACK_LIMITS = (4000, 2000, 1000, 500)

DB_CONFIG = {
    'host': 'localhost',
    'database': 'knowledge_base',
    'user': os.getenv('DB_USER', 'weixiangzhang'),
    'port': 5432,
}

STOPWORDS_RE = re.compile(r'^[\d\s\.\,\-\(\)\[\]\/\:]+$')


def clean_text(text):
    text = text.replace('\x00', '')
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def is_junk(text):
    if len(text.split()) < 5:
        return True
    if STOPWORDS_RE.match(text):
        return True
    return False


def embed_batch(texts):
    resp = requests.post(OLLAMA_URL, json={"model": MODEL, "input": texts}, timeout=180)
    resp.raise_for_status()
    return resp.json().get("embeddings", [])


def embed_one_shrinking(text):
    for limit in FALLBACK_LIMITS:
        try:
            resp = requests.post(OLLAMA_URL, json={"model": MODEL, "input": text[:limit]}, timeout=60)
            if resp.status_code == 200:
                return resp.json()["embeddings"][0]
        except Exception:
            pass
    return None


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT c.chunk_id, c.book_id, c.content
        FROM chunks c
        WHERE NOT EXISTS (
            SELECT 1 FROM chunk_embeddings ce
            WHERE ce.chunk_id = c.chunk_id AND ce.embedding_model = %s
        )
    """, (MODEL,))
    rows = cur.fetchall()
    print(f"{len(rows)} chunks missing {MODEL}", flush=True)

    junk = embedded = failed = 0
    work = []
    for r in rows:
        text = clean_text(r['content'])
        if is_junk(text):
            junk += 1
            continue
        work.append((r['chunk_id'], r['book_id'], text[:MAX_TEXT_LEN]))
    print(f"{junk} junk skipped, {len(work)} to embed", flush=True)

    insert_sql = """
        INSERT INTO chunk_embeddings (chunk_id, book_id, embedding_model, embedding_dimension, embedding_vector)
        VALUES (%s, %s, %s, %s, %s::vector)
        ON CONFLICT (chunk_id, embedding_model) DO NOTHING
    """

    for i in range(0, len(work), BATCH_SIZE):
        sub = work[i:i + BATCH_SIZE]
        embeddings = None
        try:
            embeddings = embed_batch([t for _, _, t in sub])
        except Exception:
            pass

        if embeddings and len(embeddings) == len(sub):
            for (chunk_id, book_id, _), emb in zip(sub, embeddings):
                if emb:
                    cur.execute(insert_sql, (chunk_id, book_id, MODEL, len(emb), str(emb)))
                    embedded += 1
                else:
                    failed += 1
        else:
            # Batch failed (likely one over-long item) — per-item with shrinking truncation
            for chunk_id, book_id, text in sub:
                emb = embed_one_shrinking(text)
                if emb:
                    cur.execute(insert_sql, (chunk_id, book_id, MODEL, len(emb), str(emb)))
                    embedded += 1
                else:
                    failed += 1
        conn.commit()
        if (i // BATCH_SIZE) % 50 == 0:
            print(f"progress: {min(i + BATCH_SIZE, len(work))}/{len(work)} embedded={embedded} failed={failed}", flush=True)

    conn.close()
    print(f"DONE: embedded={embedded} failed={failed} junk={junk}", flush=True)


if __name__ == '__main__':
    main()
