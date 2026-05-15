#!/usr/bin/env python3
"""
Ollama Re-embed: Fill gaps with nomic-embed-text-v2-moe (local, free)
=====================================================================

Embeds chunks that have NEITHER gemini-embedding-001 nor nomic-embed-text-v2-moe.
Runs locally on M2 Pro, ~7 chunks/sec with batching.

Run: screen -dmS ollama_reembed bash -c 'python3 -u scripts/ollama_reembed_remaining.py > logs/ollama_reembed.log 2>&1'
"""

import os
import sys
import time
import json
import signal
import logging
import psycopg2
import psycopg2.extras
import requests
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "ollama_reembed.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ollama_reembed")

OLLAMA_URL = "http://localhost:11434/api/embed"
MODEL = "nomic-embed-text-v2-moe"
EMBED_MODEL_NAME = "nomic-embed-text-v2-moe"
BATCH_SIZE = 50   # texts per Ollama call (M2 Pro handles this fine)
DB_BATCH = 1000   # chunks to fetch from DB at a time
MAX_TEXT_LEN = 8000
THROTTLE_SECONDS = 0.0  # no throttle for local
NUM_WORKERS = 4   # 4 workers = sweet spot on M2 Pro (6 saturates ANE)

DB_CONFIG = {
    'host': 'localhost',
    'database': 'knowledge_base',
    'user': os.getenv('DB_USER', 'weixiangzhang'),
    'port': 5432
}

shutdown_requested = False
def handle_signal(sig, frame):
    global shutdown_requested
    logger.info("Shutdown requested, finishing current batch...")
    shutdown_requested = True
signal.signal(signal.SIGTERM, handle_signal)


def get_uncovered_chunks(conn, batch_size=DB_BATCH):
    """Get chunks that have neither gemini nor nomic embeddings."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT c.chunk_id, c.book_id, c.content
        FROM chunks c
        WHERE c.content IS NOT NULL AND length(c.content) > 10
          AND NOT EXISTS (SELECT 1 FROM chunk_embeddings ce WHERE ce.chunk_id = c.chunk_id AND ce.embedding_model = 'gemini-embedding-001')
          AND NOT EXISTS (SELECT 1 FROM chunk_embeddings ce WHERE ce.chunk_id = c.chunk_id AND ce.embedding_model = %s)
        ORDER BY c.book_id
        LIMIT %s
    """, (EMBED_MODEL_NAME, batch_size))
    return cur.fetchall()


def clean_text(text):
    """Pre-clean text for embedding: strip junk that causes Ollama 400s."""
    import unicodedata, re
    # Remove null bytes and control chars
    text = text.replace('\x00', '')
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # Normalize unicode
    text = unicodedata.normalize('NFKC', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def is_junk(text):
    """Skip chunks that have no semantic value."""
    import re
    if len(text.split()) < 5:
        return True
    # Numbers/punctuation only
    if re.match(r'^[\d\s\.\,\-\(\)\[\]\/\:]+$', text):
        return True
    return False


def embed_texts(texts):
    """Batch embed via Ollama."""
    inputs = [clean_text(t)[:MAX_TEXT_LEN] for t in texts]
    resp = requests.post(OLLAMA_URL, json={"model": MODEL, "input": inputs}, timeout=120)
    resp.raise_for_status()
    return resp.json().get("embeddings", [])


def main():
    state_file = LOGS_DIR / "ollama_reembed_state.json"

    # Test Ollama
    logger.info(f"Testing Ollama ({MODEL})...")
    try:
        test = embed_texts(["test"])[0]
        logger.info(f"Ollama OK — {len(test)}-dim vectors")
    except Exception as e:
        logger.error(f"Ollama not reachable: {e}")
        sys.exit(1)

    # Set nice level
    try:
        os.nice(10)
    except OSError:
        pass

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Count remaining
    cur.execute("""
        SELECT COUNT(*) FROM chunks c
        WHERE c.content IS NOT NULL AND length(c.content) > 10
          AND NOT EXISTS (SELECT 1 FROM chunk_embeddings ce WHERE ce.chunk_id = c.chunk_id AND ce.embedding_model = 'gemini-embedding-001')
          AND NOT EXISTS (SELECT 1 FROM chunk_embeddings ce WHERE ce.chunk_id = c.chunk_id AND ce.embedding_model = %s)
    """, (EMBED_MODEL_NAME,))
    remaining = cur.fetchone()[0]
    logger.info(f"Chunks to embed: {remaining:,}")

    stats = {
        'started': datetime.now().isoformat(),
        'embedded': 0,
        'failed': 0,
        'target': remaining,
    }
    t0 = time.time()

    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading
    lock = threading.Lock()

    def process_sub_batch(sub_batch):
        """Embed a sub-batch. On failure, fall back to one-by-one to skip bad chunks."""
        texts = [r['content'] for r in sub_batch]
        try:
            embeddings = embed_texts(texts)
            return sub_batch, embeddings
        except Exception:
            # Fall back to one-by-one to identify bad chunks
            results_rows = []
            results_embs = []
            for row in sub_batch:
                try:
                    embs = embed_texts([row['content'][:MAX_TEXT_LEN]])
                    if embs and embs[0]:
                        results_rows.append(row)
                        results_embs.append(embs[0])
                except Exception:
                    pass  # skip bad chunk
            return results_rows, results_embs if results_rows else None

    while not shutdown_requested:
        rows = get_uncovered_chunks(conn, DB_BATCH)
        if not rows:
            logger.info("All chunks covered!")
            break

        # Filter junk before embedding
        rows = [r for r in rows if not is_junk(r['content'])]
        if not rows:
            continue

        # Split into sub-batches
        sub_batches = [rows[i:i + BATCH_SIZE] for i in range(0, len(rows), BATCH_SIZE)]

        # Process in parallel
        with ThreadPoolExecutor(max_workers=NUM_WORKERS) as pool:
            futures = {pool.submit(process_sub_batch, sb): sb for sb in sub_batches}
            for future in as_completed(futures):
                if shutdown_requested:
                    break
                result = future.result()
                if result is None:
                    stats['failed'] += BATCH_SIZE
                    continue
                sub, embeddings = result
                try:
                    for row, emb in zip(sub, embeddings):
                        if not emb:
                            continue
                        cur.execute("""
                            INSERT INTO chunk_embeddings (chunk_id, book_id, embedding_model, embedding_dimension, embedding_vector)
                            VALUES (%s, %s, %s, %s, %s::vector)
                            ON CONFLICT (chunk_id, embedding_model) DO NOTHING
                        """, (row['chunk_id'], row['book_id'], EMBED_MODEL_NAME, len(emb), str(emb)))
                        stats['embedded'] += 1
                    conn.commit()
                except Exception as e:
                    logger.warning(f"Insert error: {e}")
                    stats['failed'] += len(sub)
                    conn.rollback()

        # Progress
        elapsed = time.time() - t0
        rate = stats['embedded'] / max(elapsed, 1)
        left = remaining - stats['embedded']
        eta_h = left / max(rate, 0.1) / 3600
        logger.info(f"Embedded: {stats['embedded']:,} | Rate: {rate:.1f}/sec | ETA: {eta_h:.1f}h | Failed: {stats['failed']}")
        stats['last_update'] = datetime.now().isoformat()
        with open(state_file, 'w') as f:
            json.dump(stats, f, indent=2)

    conn.close()
    stats['finished'] = datetime.now().isoformat()
    stats['elapsed_seconds'] = round(time.time() - t0, 1)
    with open(state_file, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Done. Embedded {stats['embedded']:,} in {stats['elapsed_seconds']:.0f}s")


if __name__ == '__main__':
    main()
