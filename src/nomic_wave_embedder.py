#!/usr/bin/env python3
"""
🌊 NOMIC WAVE EMBEDDER - Gentle batch processing
================================================

Lightweight embedding using nomic-embed-text in controlled waves.
Designed to not overload the system.

Usage:
    python3 nomic_wave_embedder.py [chunks_per_wave] [delay_seconds]

    Default: 100 chunks per wave, 2 second delay between waves

Examples:
    python3 nomic_wave_embedder.py          # 100 chunks, 2s delay
    python3 nomic_wave_embedder.py 50 5     # 50 chunks, 5s delay (gentler)
    python3 nomic_wave_embedder.py 200 1    # 200 chunks, 1s delay (faster)
"""

import sys
import time
import logging
import requests
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

class NomicWaveEmbedder:
    def __init__(self, chunks_per_wave: int = 100, delay_seconds: float = 2.0):
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

        # Wave configuration
        self.chunks_per_wave = chunks_per_wave
        self.delay_seconds = delay_seconds

        # Stats
        self.processed = 0
        self.success = 0
        self.errors = 0
        self.start_time = None
        self.failed_chunks = set()

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
                    params = [self.max_content_length]
                    failed_filter = ""
                    if self.failed_chunks:
                        placeholders = ','.join(['%s'] * len(self.failed_chunks))
                        failed_filter = f"AND chunk_id NOT IN ({placeholders})"
                        params.extend(list(self.failed_chunks))
                    params.append(limit)

                    cur.execute(f"""
                        SELECT chunk_id, LEFT(content, %s) as content
                        FROM chunks
                        WHERE embedding_nomic IS NULL
                        AND content IS NOT NULL
                        AND LENGTH(content) > 50
                        AND LENGTH(content) <= 8000
                        {failed_filter}
                        ORDER BY book_id, chunk_id
                        LIMIT %s
                    """, params)
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
                logger.warning(
                    "Embedding response missing or dimension mismatch: got %s, expected %d",
                    len(embedding) if embedding else None,
                    self.dimension
                )
            else:
                logger.error(
                    "Ollama API returned status %d: %s",
                    response.status_code,
                    response.text[:200]
                )
            return None
        except Exception as e:
            logger.error("Embedding generation failed: %s", e, exc_info=True)
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
            print(f"❌ Save error for {chunk_id}: {e}")
            return False

    def process_wave(self) -> int:
        """Process one wave of chunks"""
        chunks = self.get_chunks_missing_nomic(self.chunks_per_wave)

        if not chunks:
            return 0

        wave_success = 0
        for chunk_id, content in chunks:
            embedding = self.generate_embedding(content)

            if embedding:
                if self.save_embedding(chunk_id, embedding):
                    wave_success += 1
                    self.success += 1
                else:
                    self.errors += 1
            else:
                self.errors += 1

            self.processed += 1

        return wave_success

    def get_remaining_count(self) -> int:
        """Get count of chunks still needing nomic embeddings"""
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return -1
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM chunks WHERE embedding_nomic IS NULL")
                    return cur.fetchone()[0]
        except Exception:
            return -1

    def run(self, max_waves: int = None, max_chunks: int = None, max_minutes: int = None):
        """
        Run wave embedding process

        Args:
            max_waves: Stop after N waves (None = unlimited)
            max_chunks: Stop after N chunks processed (None = unlimited)
            max_minutes: Stop after N minutes (None = unlimited)
        """
        self.start_time = datetime.now()
        wave_count = 0

        remaining = self.get_remaining_count()
        print(f"🌊 NOMIC WAVE EMBEDDER")
        print(f"=" * 50)
        print(f"📊 Chunks missing nomic: {remaining:,}")
        print(f"⚙️  Chunks per wave: {self.chunks_per_wave}")
        print(f"⏱️  Delay between waves: {self.delay_seconds}s")
        print(f"=" * 50)
        print(f"Press Ctrl+C to stop gracefully\n")

        try:
            while True:
                wave_count += 1
                wave_start = time.time()

                success = self.process_wave()

                if success == 0:
                    print(f"✅ No more chunks to process!")
                    break

                wave_time = time.time() - wave_start
                elapsed = (datetime.now() - self.start_time).total_seconds()
                rate = self.success / elapsed if elapsed > 0 else 0

                print(f"🌊 Wave {wave_count}: {success}/{self.chunks_per_wave} embedded | "
                      f"Total: {self.success:,} | Rate: {rate:.1f}/s | "
                      f"Errors: {self.errors}")

                # Check stop conditions
                if max_waves and wave_count >= max_waves:
                    print(f"⏹️  Reached max waves ({max_waves})")
                    break

                if max_chunks and self.processed >= max_chunks:
                    print(f"⏹️  Reached max chunks ({max_chunks})")
                    break

                if max_minutes and elapsed >= max_minutes * 60:
                    print(f"⏹️  Reached max time ({max_minutes} minutes)")
                    break

                # Delay between waves
                time.sleep(self.delay_seconds)

        except KeyboardInterrupt:
            print(f"\n⏹️  Stopped by user")

        # Final stats
        elapsed = (datetime.now() - self.start_time).total_seconds()
        remaining = self.get_remaining_count()

        print(f"\n{'=' * 50}")
        print(f"📊 FINAL STATS")
        print(f"{'=' * 50}")
        print(f"✅ Successfully embedded: {self.success:,}")
        print(f"❌ Errors: {self.errors}")
        print(f"⏱️  Total time: {elapsed:.1f}s")
        print(f"📈 Rate: {self.success / elapsed:.1f} chunks/second")
        print(f"📋 Still remaining: {remaining:,}")


def main():
    # Parse arguments
    chunks_per_wave = 100
    delay_seconds = 2.0

    if len(sys.argv) > 1:
        try:
            chunks_per_wave = int(sys.argv[1])
        except ValueError:
            print(f"Invalid chunks_per_wave: {sys.argv[1]}")
            sys.exit(1)

    if len(sys.argv) > 2:
        try:
            delay_seconds = float(sys.argv[2])
        except ValueError:
            print(f"Invalid delay_seconds: {sys.argv[2]}")
            sys.exit(1)

    embedder = NomicWaveEmbedder(chunks_per_wave, delay_seconds)

    # Run with a 10-minute limit by default for safety
    # Remove max_minutes=10 for unlimited running
    embedder.run(max_minutes=10)


if __name__ == "__main__":
    main()
