#!/usr/bin/env python3
"""One-off: embed chunks whose only embeddings are dead models (mxbai/nomic-v1)
with nomic-embed-text-v2-moe, so purging the dead rows never drops coverage.

Single process, single DB connection — safe to run (no zombie connections).
"""

import os
import re
import sys
import unicodedata

import psycopg2
import psycopg2.extras
import requests

OLLAMA_URL = "http://localhost:11434/api/embed"
MODEL = "nomic-embed-text-v2-moe"
BATCH_SIZE = 30
MAX_TEXT_LEN = 8000

DB_CONFIG = {
    'host': 'localhost',
    'database': 'knowledge_base',
    'user': os.getenv('DB_USER', 'weixiangzhang'),
    'port': 5432,
}

DEAD_MODELS = ('mxbai-embed-large', 'nomic-embed-text')


def clean_text(text):
    text = text.replace('\x00', '')
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def embed_batch(texts):
    cleaned = [clean_text(t)[:MAX_TEXT_LEN] for t in texts]
    resp = requests.post(OLLAMA_URL, json={"model": MODEL, "input": cleaned}, timeout=120)
    resp.raise_for_status()
    return resp.json().get("embeddings", [])


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT c.chunk_id, c.book_id, c.content
        FROM chunks c
        WHERE EXISTS (
            SELECT 1 FROM chunk_embeddings ce
            WHERE ce.chunk_id = c.chunk_id AND ce.embedding_model IN %s
        )
        AND NOT EXISTS (
            SELECT 1 FROM chunk_embeddings k
            WHERE k.chunk_id = c.chunk_id AND k.embedding_model NOT IN %s
        )
        AND c.content IS NOT NULL
    """, (DEAD_MODELS, DEAD_MODELS))
    rows = cur.fetchall()
    print(f"{len(rows)} gap chunks to embed")

    done = failed = 0
    consecutive_failures = 0
    for i in range(0, len(rows), BATCH_SIZE):
        sub = rows[i:i + BATCH_SIZE]
        try:
            embeddings = embed_batch([r['content'] for r in sub])
        except Exception as e:
            print(f"batch {i}: embed error {e}", file=sys.stderr)
            consecutive_failures += 1
            if consecutive_failures >= 5:
                print("5 consecutive batch failures - stopping", file=sys.stderr)
                break
            continue
        consecutive_failures = 0
        for row, emb in zip(sub, embeddings):
            if not emb:
                failed += 1
                continue
            cur.execute("""
                INSERT INTO chunk_embeddings (chunk_id, book_id, embedding_model, embedding_dimension, embedding_vector)
                VALUES (%s, %s, %s, %s, %s::vector)
                ON CONFLICT (chunk_id, embedding_model) DO NOTHING
            """, (row['chunk_id'], row['book_id'], MODEL, len(emb), str(emb)))
            done += 1
        conn.commit()
        if (i // BATCH_SIZE) % 10 == 0:
            print(f"progress: {min(i + BATCH_SIZE, len(rows))}/{len(rows)}")

    conn.close()
    print(f"done: {done} embedded, {failed} failed")


if __name__ == '__main__':
    main()
