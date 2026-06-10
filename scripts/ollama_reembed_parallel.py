#!/usr/bin/env python3
"""
Parallel Ollama Re-embed: Max throughput on M2 Pro
===================================================

Runs multiple worker processes, each with their own DB connection,
all hitting the same Ollama server but with concurrent requests.
Uses multiprocessing to bypass Python GIL.

Run: screen -dmS ollama_reembed bash -c 'python3 -u scripts/ollama_reembed_parallel.py > logs/ollama_reembed.log 2>&1'
"""

import os
import sys
import time
import json
import signal
import logging
import unicodedata
import re
import psycopg2
import psycopg2.extras
import requests
from pathlib import Path
from datetime import datetime
from multiprocessing import Process, Value, Lock
from ctypes import c_long

PROJECT_ROOT = Path(__file__).parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [W%(process)d] %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "ollama_reembed.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ollama_reembed")

OLLAMA_URL = "http://localhost:11434/api/embed"
MODEL = "nomic-embed-text-v2-moe"
BATCH_SIZE = 30
MAX_TEXT_LEN = 8000
NUM_WORKERS = 6

DB_CONFIG = {
    'host': 'localhost',
    'database': 'knowledge_base',
    'user': os.getenv('DB_USER', 'weixiangzhang'),
    'port': 5432
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


def embed_one(text):
    """Embed a single text, return embedding or None."""
    cleaned = clean_text(text)[:MAX_TEXT_LEN]
    try:
        resp = requests.post(OLLAMA_URL, json={"model": MODEL, "input": cleaned}, timeout=60)
        resp.raise_for_status()
        embs = resp.json().get("embeddings", [])
        return embs[0] if embs else None
    except Exception:
        return None


def embed_batch(texts):
    """Batch embed, return list of embeddings."""
    cleaned = [clean_text(t)[:MAX_TEXT_LEN] for t in texts]
    try:
        resp = requests.post(OLLAMA_URL, json={"model": MODEL, "input": cleaned}, timeout=120)
        resp.raise_for_status()
        return resp.json().get("embeddings", [])
    except Exception:
        # Fall back to one-by-one
        return [embed_one(t) for t in texts]


def worker(worker_id, total_workers, embedded_count, failed_count, lock):
    """Each worker processes chunks where chunk_id hash % total_workers == worker_id."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        os.nice(5)
    except OSError:
        pass

    while True:
        # Get a batch of uncovered chunks assigned to this worker
        cur.execute("""
            SELECT c.chunk_id, c.book_id, c.content
            FROM chunks c
            WHERE c.content IS NOT NULL AND length(c.content) > 10
              AND NOT EXISTS (SELECT 1 FROM chunk_embeddings ce WHERE ce.chunk_id = c.chunk_id AND ce.embedding_model = 'nomic-embed-text-v2-moe')
              AND NOT EXISTS (SELECT 1 FROM chunk_embeddings ce WHERE ce.chunk_id = c.chunk_id AND ce.embedding_model = 'gemini-embedding-001')
              AND abs(hashtext(c.chunk_id)) %% %s = %s
            ORDER BY c.book_id
            LIMIT %s
        """, (total_workers, worker_id, BATCH_SIZE * 3))

        rows = cur.fetchall()
        if not rows:
            logger.info(f"Worker {worker_id}: no more chunks")
            break

        # Filter junk
        rows = [r for r in rows if not is_junk(r['content'])]
        if not rows:
            continue

        # Process in batches
        for i in range(0, len(rows), BATCH_SIZE):
            sub = rows[i:i + BATCH_SIZE]
            texts = [r['content'] for r in sub]
            embeddings = embed_batch(texts)

            insert_cur = conn.cursor()
            batch_embedded = 0
            for row, emb in zip(sub, embeddings):
                if not emb:
                    with lock:
                        failed_count.value += 1
                    continue
                try:
                    insert_cur.execute("""
                        INSERT INTO chunk_embeddings (chunk_id, book_id, embedding_model, embedding_dimension, embedding_vector)
                        VALUES (%s, %s, %s, %s, %s::vector)
                        ON CONFLICT (chunk_id, embedding_model) DO NOTHING
                    """, (row['chunk_id'], row['book_id'], MODEL, len(emb), str(emb)))
                    batch_embedded += 1
                except Exception:
                    pass
            conn.commit()

            with lock:
                embedded_count.value += batch_embedded

    conn.close()


def main():
    state_file = LOGS_DIR / "ollama_reembed_state.json"

    # Test Ollama
    logger.info(f"Testing Ollama ({MODEL})...")
    try:
        emb = embed_one("test")
        assert emb and len(emb) == 768
        logger.info(f"Ollama OK — {len(emb)}-dim vectors")
    except Exception as e:
        logger.error(f"Ollama not reachable: {e}")
        sys.exit(1)

    # Count remaining
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM chunks c
        WHERE c.content IS NOT NULL AND length(c.content) > 10
          AND NOT EXISTS (SELECT 1 FROM chunk_embeddings ce WHERE ce.chunk_id = c.chunk_id AND ce.embedding_model = 'nomic-embed-text-v2-moe')
          AND NOT EXISTS (SELECT 1 FROM chunk_embeddings ce WHERE ce.chunk_id = c.chunk_id AND ce.embedding_model = 'gemini-embedding-001')
    """)
    remaining = cur.fetchone()[0]
    conn.close()
    logger.info(f"Chunks to embed: {remaining:,} using {NUM_WORKERS} workers")

    # Shared counters
    embedded_count = Value(c_long, 0)
    failed_count = Value(c_long, 0)
    lock = Lock()

    t0 = time.time()

    # Launch workers
    workers = []
    for wid in range(NUM_WORKERS):
        p = Process(target=worker, args=(wid, NUM_WORKERS, embedded_count, failed_count, lock))
        p.start()
        workers.append(p)

    # Monitor loop
    try:
        while any(w.is_alive() for w in workers):
            time.sleep(30)
            elapsed = time.time() - t0
            rate = embedded_count.value / max(elapsed, 1)
            left = remaining - embedded_count.value
            eta_h = left / max(rate, 0.1) / 3600
            logger.info(f"Total: {embedded_count.value:,} | Rate: {rate:.1f}/sec | ETA: {eta_h:.1f}h | Failed: {failed_count.value}")

            stats = {
                'started': datetime.fromtimestamp(t0).isoformat(),
                'embedded': embedded_count.value,
                'failed': failed_count.value,
                'target': remaining,
                'rate': round(rate, 1),
                'last_update': datetime.now().isoformat(),
            }
            with open(state_file, 'w') as f:
                json.dump(stats, f, indent=2)
    except KeyboardInterrupt:
        logger.info("Shutting down workers...")

    for w in workers:
        w.join(timeout=10)

    elapsed = time.time() - t0
    logger.info(f"Done. Embedded {embedded_count.value:,} in {elapsed:.0f}s ({embedded_count.value/max(elapsed,1):.1f}/sec)")


if __name__ == '__main__':
    main()
