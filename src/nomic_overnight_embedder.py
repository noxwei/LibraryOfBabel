#!/usr/bin/env python3
"""
🌙 NOMIC OVERNIGHT EMBEDDER
===========================

Runs nomic embeddings overnight with logging and auto-recovery.
Target: Complete 2.1M chunks in ~12 days (~120 chunks/min)

Usage:
    nohup python3 src/nomic_overnight_embedder.py > logs/nomic_overnight.log 2>&1 &

Monitor:
    tail -f logs/nomic_overnight.log

Stop gracefully:
    kill -SIGINT $(cat logs/nomic_overnight.pid)
"""

import os
import sys
import time
import signal
import requests
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import json

class NomicOvernightEmbedder:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'database': 'knowledge_base',
            'user': 'weixiangzhang',
            'port': 5432
        }

        self.ollama_url = "http://localhost:11434"
        self.model = "nomic-embed-text"
        self.dimension = 768
        self.max_content_length = 8000

        # Optimized for speed while being stable
        self.chunks_per_wave = 200
        self.delay_between_waves = 0.5  # 500ms between waves
        self.delay_on_error = 5.0  # 5s pause on errors

        # Stats
        self.processed = 0
        self.success = 0
        self.errors = 0
        self.consecutive_errors = 0
        self.start_time = None
        self.wave_count = 0
        self.failed_chunks = set()

        # Control
        self.should_stop = False
        self.log_dir = "logs"
        self.pid_file = f"{self.log_dir}/nomic_overnight.pid"
        self.state_file = f"{self.log_dir}/nomic_overnight_state.json"

        # Setup
        os.makedirs(self.log_dir, exist_ok=True)
        self._setup_signal_handlers()
        self._write_pid()

    def _setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self._handle_stop)
        signal.signal(signal.SIGTERM, self._handle_stop)

    def _handle_stop(self, signum, frame):
        print(f"\n🛑 Received stop signal, finishing current wave...")
        self.should_stop = True

    def _write_pid(self):
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))

    def _save_state(self):
        state = {
            'processed': self.processed,
            'success': self.success,
            'errors': self.errors,
            'wave_count': self.wave_count,
            'last_update': datetime.now().isoformat(),
            'start_time': self.start_time.isoformat() if self.start_time else None
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def get_db_connection(self):
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            print(f"❌ DB connection failed: {e}")
            return None

    def get_chunks_missing_nomic(self, limit: int) -> List[Tuple[str, str]]:
        """Get chunks that don't have nomic embeddings yet"""
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return []
                with conn.cursor() as cur:
                    if self.failed_chunks:
                        failed_list = tuple(self.failed_chunks)
                        cur.execute("""
                            SELECT chunk_id, LEFT(content, %s) as content
                            FROM chunks
                            WHERE embedding_nomic IS NULL
                            AND content IS NOT NULL
                            AND LENGTH(content) > 50
                            AND LENGTH(content) <= 8000
                            AND chunk_id NOT IN %s
                            ORDER BY book_id, chunk_id
                            LIMIT %s
                        """, (self.max_content_length, failed_list, limit))
                    else:
                        cur.execute("""
                            SELECT chunk_id, LEFT(content, %s) as content
                            FROM chunks
                            WHERE embedding_nomic IS NULL
                            AND content IS NOT NULL
                            AND LENGTH(content) > 50
                            AND LENGTH(content) <= 8000
                            ORDER BY book_id, chunk_id
                            LIMIT %s
                        """, (self.max_content_length, limit))
                    return cur.fetchall()
        except Exception as e:
            print(f"❌ Query error: {e}")
            return []

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate nomic embedding for text"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=30
            )
            if response.status_code == 200:
                embedding = response.json().get('embedding')
                if embedding and len(embedding) == self.dimension:
                    return embedding
                print(f"⚠️  Embedding response invalid: status=200 but embedding missing or wrong dimension (got {len(embedding) if embedding else 0}, expected {self.dimension})")
            else:
                print(f"⚠️  Embedding API returned status {response.status_code}: {response.text[:200]}")
            return None
        except Exception as e:
            print(f"❌ Embedding API call failed: {e}")
            return None

    def save_embedding(self, chunk_id: str, embedding: List[float]) -> bool:
        """Save nomic embedding to database"""
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return False
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE chunks
                        SET embedding_nomic = %s::vector,
                            embedding_model_used = 'nomic',
                            last_embedding_update = NOW()
                        WHERE chunk_id = %s
                    """, (embedding, chunk_id))
                    conn.commit()
                    return True
        except Exception as e:
            return False

    def process_wave(self) -> Tuple[int, int]:
        """Process one wave of chunks. Returns (success_count, error_count)"""
        chunks = self.get_chunks_missing_nomic(self.chunks_per_wave)

        if not chunks:
            return (0, 0)

        wave_success = 0
        wave_errors = 0

        for chunk_id, content in chunks:
            if self.should_stop:
                break

            embedding = self.generate_embedding(content)

            if embedding:
                if self.save_embedding(chunk_id, embedding):
                    wave_success += 1
                    self.success += 1
                    self.consecutive_errors = 0
                else:
                    wave_errors += 1
                    self.errors += 1
                    self.consecutive_errors += 1
                    self.failed_chunks.add(chunk_id)
            else:
                wave_errors += 1
                self.errors += 1
                self.consecutive_errors += 1
                self.failed_chunks.add(chunk_id)

            self.processed += 1

        return (wave_success, wave_errors)

    def get_remaining_count(self) -> int:
        """Get count of chunks still needing nomic embeddings"""
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return -1
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM chunks WHERE embedding_nomic IS NULL")
                    return cur.fetchone()[0]
        except:
            return -1

    def run(self):
        """Run overnight embedding process"""
        self.start_time = datetime.now()
        initial_remaining = self.get_remaining_count()

        print(f"🌙 NOMIC OVERNIGHT EMBEDDER")
        print(f"=" * 60)
        print(f"📊 Chunks to embed: {initial_remaining:,}")
        print(f"⚙️  Config: {self.chunks_per_wave} chunks/wave, {self.delay_between_waves}s delay")
        print(f"🎯 Target rate: ~120 chunks/min (~2 chunks/sec)")
        print(f"📁 PID file: {self.pid_file}")
        print(f"📋 State file: {self.state_file}")
        print(f"🕐 Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"=" * 60)
        print(f"Stop with: kill -SIGINT $(cat {self.pid_file})")
        print(f"=" * 60 + "\n")
        sys.stdout.flush()

        last_status_time = time.time()
        status_interval = 60  # Print status every minute

        try:
            while not self.should_stop:
                self.wave_count += 1
                wave_start = time.time()

                success, errors = self.process_wave()

                if success == 0 and errors == 0:
                    print(f"✅ No more chunks to process!")
                    break

                # Handle too many consecutive errors with exponential backoff
                if self.consecutive_errors > 10:
                    backoff = min(300, 30 * (2 ** self.consecutive_errors))
                    print(f"⚠️  Too many consecutive errors ({self.consecutive_errors}), pausing {backoff}s...")
                    time.sleep(backoff)
                    continue

                wave_time = time.time() - wave_start
                elapsed = (datetime.now() - self.start_time).total_seconds()
                rate_per_sec = self.success / elapsed if elapsed > 0 else 0
                rate_per_min = rate_per_sec * 60

                # Print status every minute
                if time.time() - last_status_time >= status_interval:
                    remaining = self.get_remaining_count()
                    eta_seconds = remaining / rate_per_sec if rate_per_sec > 0 else 0
                    eta = timedelta(seconds=int(eta_seconds))

                    print(f"📊 [{datetime.now().strftime('%H:%M:%S')}] "
                          f"Embedded: {self.success:,} | "
                          f"Rate: {rate_per_min:.0f}/min | "
                          f"Remaining: {remaining:,} | "
                          f"ETA: {eta} | "
                          f"Errors: {self.errors}")
                    sys.stdout.flush()

                    self._save_state()
                    last_status_time = time.time()

                # Delay between waves (shorter if had errors)
                if errors > 0:
                    time.sleep(self.delay_on_error)
                else:
                    time.sleep(self.delay_between_waves)

        except Exception as e:
            print(f"💥 Unexpected error: {e}")

        # Final stats
        elapsed = (datetime.now() - self.start_time).total_seconds()
        remaining = self.get_remaining_count()
        completed = initial_remaining - remaining

        print(f"\n{'=' * 60}")
        print(f"🌙 OVERNIGHT RUN COMPLETE")
        print(f"{'=' * 60}")
        print(f"✅ Successfully embedded: {self.success:,}")
        print(f"❌ Errors: {self.errors}")
        print(f"⏱️  Total time: {timedelta(seconds=int(elapsed))}")
        print(f"📈 Average rate: {self.success / elapsed * 60:.0f} chunks/minute")
        print(f"📋 Still remaining: {remaining:,}")
        print(f"🎯 Completion: {(completed / initial_remaining * 100):.2f}%")
        print(f"{'=' * 60}")
        sys.stdout.flush()

        self._save_state()

        # Cleanup PID file
        try:
            os.remove(self.pid_file)
        except:
            pass


def main():
    embedder = NomicOvernightEmbedder()
    embedder.run()


if __name__ == "__main__":
    main()
