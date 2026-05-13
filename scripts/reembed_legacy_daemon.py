#!/usr/bin/env python3
"""
Re-embedding Daemon — Migrate legacy embeddings to current models
================================================================

Finds chunks with legacy embeddings (nomic-embed-text v1, mxbai-embed-large)
and generates new embeddings with nomic-embed-text-v2-moe.

Run: nohup python3 scripts/reembed_legacy_daemon.py > logs/reembed.log 2>&1 &

Priority order:
1. nomic-embed-text v1 chunks (157K) — these power semantic search
2. mxbai-embed-large chunks (474K) — secondary
"""

import os
import sys
import time
import json
import logging
import signal
import psycopg2
import psycopg2.extras
import requests
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
PIDS_DIR = PROJECT_ROOT / "pids"
LOGS_DIR.mkdir(exist_ok=True)
PIDS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "reembed.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("reembed")

OLLAMA_URL = "http://localhost:11434/api/embed"
NEW_MODEL = "nomic-embed-text-v2-moe"
BATCH_SIZE = 50
COMMIT_EVERY = 25

# Throttling: pause between each embedding to avoid hogging M2 Pro GPU/ANE.
# 0.0 = full speed (~7 chunks/sec), 0.1 = gentle (~5/sec), 0.5 = slow (~2/sec)
THROTTLE_SECONDS = float(os.getenv('REEMBED_THROTTLE', '0.05'))
# Niceness: renice the process so it yields to interactive work
NICE_LEVEL = int(os.getenv('REEMBED_NICE', '10'))

DB_CONFIG = {
    'host': 'localhost',
    'database': 'knowledge_base',
    'user': os.getenv('DB_USER', 'weixiangzhang'),
    'port': 5432
}

# Chunks that Ollama consistently rejects (encoding issues with CJK text)
# Skip these to avoid wasting thousands of retries
SKIP_CHUNKS = set()
SKIP_FILE = LOGS_DIR / "reembed_skip.txt"

shutdown_requested = False

def handle_signal(sig, frame):
    global shutdown_requested
    logger.info("Shutdown requested, finishing current batch...")
    shutdown_requested = True

signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)


def get_legacy_chunks(conn, legacy_model: str, batch_size: int):
    """Find chunks that have a legacy embedding but no v2-moe embedding."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT ce.chunk_id, ce.book_id, c.content
        FROM chunk_embeddings ce
        JOIN chunks c ON ce.chunk_id = c.chunk_id
        LEFT JOIN chunk_embeddings ce2
            ON ce.chunk_id = ce2.chunk_id AND ce2.embedding_model = %s
        WHERE ce.embedding_model = %s
            AND ce2.chunk_id IS NULL
            AND c.content IS NOT NULL
            AND length(c.content) > 10
        ORDER BY ce.book_id
        LIMIT %s
    """, (NEW_MODEL, legacy_model, batch_size))
    return cur.fetchall()


EMBED_BATCH = int(os.getenv('REEMBED_BATCH', '10'))  # texts per Ollama call


def embed_texts(texts: list) -> list:
    """Generate embeddings for multiple texts in one Ollama call."""
    inputs = [t[:8000] for t in texts]
    resp = requests.post(OLLAMA_URL, json={
        "model": NEW_MODEL,
        "input": inputs
    }, timeout=60)
    resp.raise_for_status()
    return resp.json().get("embeddings", [])


def process_batch(conn, legacy_model: str, stats: dict):
    """Process one batch of legacy chunks using batched Ollama calls."""
    rows = get_legacy_chunks(conn, legacy_model, BATCH_SIZE)
    if not rows:
        return 0

    # Filter out skipped chunks
    valid_rows = [r for r in rows if r['chunk_id'] not in SKIP_CHUNKS and r['content'] and len(r['content'].strip()) > 10]
    if not valid_rows:
        return 0

    cur = conn.cursor()
    embedded = 0

    # Process in sub-batches for Ollama
    for i in range(0, len(valid_rows), EMBED_BATCH):
        if shutdown_requested:
            break

        sub_batch = valid_rows[i:i + EMBED_BATCH]
        texts = [r['content'] for r in sub_batch]

        try:
            embeddings = embed_texts(texts)

            for row, embedding in zip(sub_batch, embeddings):
                if not embedding:
                    stats['skipped'] += 1
                    continue

                cur.execute("""
                    INSERT INTO chunk_embeddings (chunk_id, book_id, embedding_model, embedding_dimension, embedding_vector)
                    VALUES (%s, %s, %s, %s, %s::vector)
                    ON CONFLICT (chunk_id, embedding_model) DO NOTHING
                """, (row['chunk_id'], row['book_id'], NEW_MODEL, len(embedding), str(embedding)))

                embedded += 1
                stats['embedded'] += 1

            conn.commit()

            if THROTTLE_SECONDS > 0:
                time.sleep(THROTTLE_SECONDS)

        except requests.exceptions.RequestException as e:
            # Fall back to one-by-one for this sub-batch to identify bad chunks
            for row in sub_batch:
                try:
                    resp = requests.post(OLLAMA_URL, json={"model": NEW_MODEL, "input": row['content'][:8000]}, timeout=30)
                    resp.raise_for_status()
                    embs = resp.json().get("embeddings", [[]])
                    emb = embs[0] if embs else []
                    if emb:
                        cur.execute("""
                            INSERT INTO chunk_embeddings (chunk_id, book_id, embedding_model, embedding_dimension, embedding_vector)
                            VALUES (%s, %s, %s, %s, %s::vector)
                            ON CONFLICT (chunk_id, embedding_model) DO NOTHING
                        """, (row['chunk_id'], row['book_id'], NEW_MODEL, len(emb), str(emb)))
                        embedded += 1
                        stats['embedded'] += 1
                except Exception:
                    stats['failed'] += 1
                    fail_key = f"_fail_{row['chunk_id']}"
                    stats[fail_key] = stats.get(fail_key, 0) + 1
                    if stats[fail_key] >= 3:
                        SKIP_CHUNKS.add(row['chunk_id'])
                        logger.info(f"Auto-skipping {row['chunk_id']} after {stats[fail_key]} failures")
                        with open(SKIP_FILE, 'a') as f:
                            f.write(f"{row['chunk_id']}\n")
            conn.commit()

        except Exception as e:
            logger.warning(f"Batch error: {e}")
            stats['failed'] += len(sub_batch)
            conn.rollback()

    conn.commit()
    return embedded


def get_remaining_counts(conn):
    """Count remaining legacy embeddings that need migration."""
    cur = conn.cursor()
    counts = {}
    for model in ['nomic-embed-text', 'mxbai-embed-large']:
        cur.execute("""
            SELECT COUNT(*)
            FROM chunk_embeddings ce
            LEFT JOIN chunk_embeddings ce2
                ON ce.chunk_id = ce2.chunk_id AND ce2.embedding_model = %s
            WHERE ce.embedding_model = %s AND ce2.chunk_id IS NULL
        """, (NEW_MODEL, model))
        counts[model] = cur.fetchone()[0]
    return counts


def save_progress(stats: dict, state_file: Path):
    """Save progress to disk."""
    stats['last_update'] = datetime.now().isoformat()
    with open(state_file, 'w') as f:
        json.dump(stats, f, indent=2)


def main():
    pid_file = PIDS_DIR / "reembed_daemon.pid"
    state_file = LOGS_DIR / "reembed_state.json"

    # Write PID and set process priority
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    try:
        os.nice(NICE_LEVEL)
        logger.info(f"Process niceness set to {NICE_LEVEL}")
    except OSError:
        pass

    # Load skip list from previous runs
    if SKIP_FILE.exists():
        SKIP_CHUNKS.update(line.strip() for line in open(SKIP_FILE) if line.strip())
        logger.info(f"Loaded {len(SKIP_CHUNKS)} chunks to skip")

    logger.info("Re-embedding daemon starting")
    logger.info(f"Model: {NEW_MODEL}")
    logger.info(f"Batch size: {BATCH_SIZE}")

    # Test Ollama
    try:
        test = embed_texts(["test"])[0]
        logger.info(f"Ollama OK — {NEW_MODEL} returns {len(test)}-dim vectors")
    except Exception as e:
        logger.error(f"Ollama not reachable: {e}")
        sys.exit(1)

    conn = psycopg2.connect(**DB_CONFIG)

    # Get initial counts
    counts = get_remaining_counts(conn)
    total = sum(counts.values())
    logger.info(f"Legacy embeddings to migrate: {json.dumps(counts)}")
    logger.info(f"Total: {total:,} chunks")

    stats = {
        'started': datetime.now().isoformat(),
        'embedded': 0,
        'failed': 0,
        'skipped': 0,
        'initial_remaining': counts,
        'total_target': total
    }

    # Phase 1: nomic-embed-text v1 (priority — powers semantic search)
    logger.info("=== Phase 1: Re-embedding nomic-embed-text v1 chunks ===")
    while not shutdown_requested:
        processed = process_batch(conn, 'nomic-embed-text', stats)
        if processed == 0:
            break
        rate = stats['embedded'] / max((time.time() - datetime.fromisoformat(stats['started']).timestamp()), 1)
        remaining = get_remaining_counts(conn).get('nomic-embed-text', 0)
        eta_hours = remaining / max(rate, 0.1) / 3600
        logger.info(f"Phase 1: {stats['embedded']:,} done | {remaining:,} remaining | ~{eta_hours:.1f}h ETA | {rate:.1f} chunks/sec")
        save_progress(stats, state_file)

    # Phase 2: mxbai-embed-large
    if not shutdown_requested:
        logger.info("=== Phase 2: Re-embedding mxbai-embed-large chunks ===")
        while not shutdown_requested:
            processed = process_batch(conn, 'mxbai-embed-large', stats)
            if processed == 0:
                break
            remaining = get_remaining_counts(conn).get('mxbai-embed-large', 0)
            logger.info(f"Phase 2: {stats['embedded']:,} total done | {remaining:,} remaining")
            save_progress(stats, state_file)

    conn.close()
    stats['finished'] = datetime.now().isoformat()
    save_progress(stats, state_file)

    if shutdown_requested:
        logger.info(f"Daemon stopped gracefully. Progress: {stats['embedded']:,} embedded, {stats['failed']:,} failed")
    else:
        logger.info(f"Re-embedding complete! {stats['embedded']:,} embedded, {stats['failed']:,} failed, {stats['skipped']:,} skipped")

    pid_file.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
