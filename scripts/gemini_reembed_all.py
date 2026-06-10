#!/usr/bin/env python3
"""
Nuclear Re-embed: ALL chunks via Google Gemini embedding API (FREE)
===================================================================

Embeds all 2.4M chunks using gemini-embedding-001 (768d).
Batch API: 100 texts per call, ~1500 RPM free tier.

Run: python3 scripts/gemini_reembed_all.py
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
        logging.FileHandler(LOGS_DIR / "gemini_reembed.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("gemini_reembed")

API_KEY = os.getenv("GEMINIAPI_KEY", "AIzaSyDEM8pPz_z59Xjr_WTNknKnunPgjqLpDW0")
MODEL = "gemini-embedding-001"
EMBED_MODEL_NAME = "gemini-embedding-001"
BATCH_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:batchEmbedContents?key={API_KEY}"
OUTPUT_DIM = 768
BATCH_SIZE = 100  # max texts per batch call
DB_BATCH = 2000   # chunks to fetch from DB at a time
MAX_TEXT_LEN = 8000  # truncate longer texts
# Paid Tier 1: ~200 RPM. 0.5s between calls = ~120/min (safe margin).
THROTTLE_SECONDS = 0.5
# Budget cap: stop after this many chunks (0 = unlimited)
MAX_CHUNKS = 0  # unlimited — full send

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
# Don't catch SIGINT — let nohup handle it so background runs don't get interrupted


def get_unembedded_chunks(conn, batch_size=DB_BATCH):
    """Get chunks that don't have a gemini embedding yet."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT c.chunk_id, c.book_id, c.content
        FROM chunks c
        LEFT JOIN chunk_embeddings ce
            ON c.chunk_id = ce.chunk_id AND ce.embedding_model = %s
        WHERE ce.chunk_id IS NULL
            AND c.content IS NOT NULL
            AND length(c.content) > 10
            AND length(c.content) < 100000
            AND NOT EXISTS (
                SELECT 1 FROM chunk_embeddings ce2
                WHERE ce2.chunk_id = c.chunk_id
                AND ce2.embedding_model = 'nomic-embed-text-v2-moe'
            )
        ORDER BY c.book_id
        LIMIT %s
    """, (EMBED_MODEL_NAME, batch_size))
    return cur.fetchall()


def clean_text(text):
    """Pre-clean text to minimize bad embeddings and API errors."""
    import unicodedata
    # Remove null bytes and control chars
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # Normalize unicode (CJK, accents, ligatures)
    text = unicodedata.normalize('NFKC', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove excessive punctuation runs (e.g. "...........")
    text = re.sub(r'([.\-_=*#~])\1{4,}', r'\1\1\1', text)
    return text


def is_junk(text):
    """Skip chunks with no semantic value."""
    words = text.split()
    if len(words) < 5:
        return True
    # Numbers/punctuation only
    if re.match(r'^[\d\s\.\,\-\(\)\[\]\/\:\;]+$', text):
        return True
    # Mostly digits (page number dumps, indices)
    digit_ratio = sum(c.isdigit() for c in text) / max(len(text), 1)
    if digit_ratio > 0.4:
        return True
    return False


import re

def batch_embed(texts: list) -> list:
    """Call Gemini batch embed API. Returns list of embedding vectors."""
    requests_body = []
    for text in texts:
        cleaned = clean_text(text)[:MAX_TEXT_LEN]
        requests_body.append({
            "model": f"models/{MODEL}",
            "content": {"parts": [{"text": cleaned}]},
            "outputDimensionality": OUTPUT_DIM
        })

    resp = requests.post(BATCH_URL, json={"requests": requests_body}, timeout=60)

    if resp.status_code == 429:
        # Check if credits depleted vs rate limit
        try:
            err_msg = resp.json().get("error", {}).get("message", "")
        except Exception:
            err_msg = ""

        if "credits are depleted" in err_msg or "prepayment" in err_msg.lower():
            logger.error("CREDITS DEPLETED — stopping immediately to avoid wasting money")
            raise SystemExit("Credits depleted")

        # Genuine rate limit — back off once, don't retry more than once
        retry_delay = 30
        try:
            for detail in resp.json().get("error", {}).get("details", []):
                if "retryDelay" in str(detail):
                    delay_str = detail.get("retryDelay", "30s")
                    retry_delay = int(delay_str.replace("s", "")) + 5
        except Exception:
            pass
        logger.warning(f"Rate limited, waiting {retry_delay}s...")
        time.sleep(retry_delay)
        resp = requests.post(BATCH_URL, json={"requests": requests_body}, timeout=60)

        # If still 429 after one retry, don't keep burning credits
        if resp.status_code == 429:
            logger.error("Still rate limited after retry — pausing 5 min")
            time.sleep(300)
            return []  # skip this batch, don't raise

    resp.raise_for_status()
    data = resp.json()
    embeddings = data.get("embeddings", [])
    return [e.get("values", []) for e in embeddings]


def insert_embeddings(conn, rows, embeddings):
    """Insert embeddings into chunk_embeddings table."""
    cur = conn.cursor()
    inserted = 0
    for row, emb in zip(rows, embeddings):
        if not emb:
            continue
        cur.execute("""
            INSERT INTO chunk_embeddings (chunk_id, book_id, embedding_model, embedding_dimension, embedding_vector)
            VALUES (%s, %s, %s, %s, %s::vector)
            ON CONFLICT (chunk_id, embedding_model) DO NOTHING
        """, (row['chunk_id'], row['book_id'], EMBED_MODEL_NAME, len(emb), str(emb)))
        inserted += 1
    conn.commit()
    return inserted


def get_progress(conn):
    """Get counts for progress reporting."""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM chunks WHERE content IS NOT NULL AND length(content) > 10")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM chunk_embeddings WHERE embedding_model = %s", (EMBED_MODEL_NAME,))
    done = cur.fetchone()[0]
    return total, done


def main():
    state_file = LOGS_DIR / "gemini_reembed_state.json"

    # Test API (with retry for rate limit cooldown)
    for attempt in range(5):
        try:
            logger.info(f"Testing Gemini API (attempt {attempt+1})...")
            test_embs = batch_embed(["test"])
            if test_embs and test_embs[0]:
                logger.info(f"Gemini API OK — {len(test_embs[0])}-dim vectors")
                break
        except Exception as e:
            logger.warning(f"Test failed: {e}, waiting 60s...")
            time.sleep(60)
    else:
        logger.error("Gemini API test failed after 5 attempts")
        sys.exit(1)

    conn = psycopg2.connect(**DB_CONFIG)
    total, already_done = get_progress(conn)
    remaining = total - already_done
    logger.info(f"Total chunks: {total:,} | Already embedded: {already_done:,} | Remaining: {remaining:,}")

    stats = {
        'started': datetime.now().isoformat(),
        'total_target': total,
        'already_done_at_start': already_done,
        'embedded_this_run': 0,
        'failed': 0,
        'api_calls': 0,
    }
    t0 = time.time()

    consecutive_failures = 0
    MAX_CONSECUTIVE_FAILURES = 5  # circuit breaker: stop after 5 failed batches in a row

    while not shutdown_requested:
        if MAX_CHUNKS and stats['embedded_this_run'] >= MAX_CHUNKS:
            logger.info(f"Budget cap reached: {stats['embedded_this_run']:,} chunks")
            break
        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            logger.error(f"Circuit breaker: {consecutive_failures} consecutive failures — stopping to avoid wasting credits")
            break
        rows = get_unembedded_chunks(conn, DB_BATCH)
        if not rows:
            logger.info("All chunks embedded!")
            break

        # Process in sub-batches of BATCH_SIZE for API
        for i in range(0, len(rows), BATCH_SIZE):
            if shutdown_requested:
                break

            sub_batch = [r for r in rows[i:i + BATCH_SIZE] if not is_junk(r['content'])]
            if not sub_batch:
                continue
            texts = [r['content'] for r in sub_batch]

            try:
                embeddings = batch_embed(texts)
                stats['api_calls'] += 1
                inserted = insert_embeddings(conn, sub_batch, embeddings)
                stats['embedded_this_run'] += inserted
                consecutive_failures = 0
                time.sleep(THROTTLE_SECONDS)

            except requests.exceptions.HTTPError as e:
                if '429' in str(e):
                    logger.warning("Rate limit hit, backing off 60s...")
                    time.sleep(60)
                    # Retry this batch
                    try:
                        embeddings = batch_embed(texts)
                        stats['api_calls'] += 1
                        inserted = insert_embeddings(conn, sub_batch, embeddings)
                        stats['embedded_this_run'] += inserted
                        consecutive_failures = 0
                        time.sleep(THROTTLE_SECONDS)
                    except Exception as e2:
                        logger.error(f"Retry failed: {e2}")
                        stats['failed'] += len(sub_batch)
                        consecutive_failures += 1
                else:
                    logger.error(f"API error: {e}")
                    stats['failed'] += len(sub_batch)
                    consecutive_failures += 1

            except Exception as e:
                logger.error(f"Batch error: {e}")
                stats['failed'] += len(sub_batch)
                consecutive_failures += 1

        # Progress report every DB_BATCH
        elapsed = time.time() - t0
        rate = stats['embedded_this_run'] / max(elapsed, 1)
        _, current_done = get_progress(conn)
        current_remaining = total - current_done
        eta_min = current_remaining / max(rate, 0.1) / 60

        logger.info(
            f"Progress: {current_done:,}/{total:,} ({current_done/total*100:.1f}%) | "
            f"This run: {stats['embedded_this_run']:,} | "
            f"Rate: {rate:.0f} chunks/sec | "
            f"ETA: {eta_min:.1f} min | "
            f"API calls: {stats['api_calls']}"
        )

        # Save state
        stats['last_update'] = datetime.now().isoformat()
        stats['current_done'] = current_done
        stats['remaining'] = current_remaining
        with open(state_file, 'w') as f:
            json.dump(stats, f, indent=2)

    conn.close()
    stats['finished'] = datetime.now().isoformat()
    stats['elapsed_seconds'] = round(time.time() - t0, 1)
    with open(state_file, 'w') as f:
        json.dump(stats, f, indent=2)

    if shutdown_requested:
        logger.info(f"Stopped gracefully. Embedded {stats['embedded_this_run']:,} this run.")
    else:
        logger.info(f"DONE! Embedded {stats['embedded_this_run']:,} chunks in {stats['elapsed_seconds']:.0f}s")


if __name__ == '__main__':
    main()
