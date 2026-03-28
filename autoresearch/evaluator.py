"""
evaluator.py — Recall@K measurement for routing configurations

Connects to the knowledge_base PostgreSQL database and Ollama to:
  1. Classify each validation query using the current routing_config
  2. Embed the query with the selected model
  3. Run a pgvector cosine-similarity search
  4. Check whether any top-K result belongs to an expected genre
  5. Return weighted Recall@K across all pairs

Run standalone to see a full breakdown:
    cd /Users/weixiangzhang/Local_Dev/projects/LibraryOfBabel/autoresearch
    python evaluator.py
"""

from __future__ import annotations

import importlib
import sys
import time
import requests
import psycopg2
import psycopg2.extras
from pathlib import Path
from typing import Optional

# ── paths ─────────────────────────────────────────────────────────────────────
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))          # autoresearch/
sys.path.insert(0, str(HERE.parent))   # LibraryOfBabel/

from validation_pairs import get_validation_pairs

# ── database ──────────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "database": "knowledge_base",
    "user":     "weixiangzhang",
}

OLLAMA_BASE = "http://localhost:11434"

# ── embedding model registry ───────────────────────────────────────────────────
# Active models (Ollama-backed, production)
MODEL_META = {
    "bge": {
        "ollama_name": "bge-m3:latest",
        "dim":         1024,
        "col":         "embedding_vector_bge",
        "model_filter": "bge-m3",
        # Best overall RAG retrieval accuracy (72% Recall@10 on BEIR)
        # MTEB score: 63.0 | Context: 8K tokens | Best for: narrative, semantic search
    },
    "nomic": {
        "ollama_name": "nomic-embed-text:latest",
        "dim":         1536,
        "col":         "embedding_vector",
        "model_filter": "nomic-embed-text",
        # Lightweight, fast fallback | Context: 8K tokens | Best for: general content
    },
    "mxbai": {
        "ollama_name": "mxbai-embed-large:latest",
        "dim":         1024,
        "col":         "embedding_vector_mxbai",
        "model_filter": "mxbai-embed-large",
        # Strong multilingual performance | Context: 512 tokens | Best for: cultural/multilingual
    },
    "arctic": {
        "ollama_name": "snowflake-arctic-embed:latest",
        "dim":         1024,
        "col":         "embedding_vector_arctic",
        "model_filter": "snowflake-arctic-embed",
        # Optimized for factual/technical retrieval | Best for: academic, STEM
    },
    "granite": {
        "ollama_name": "granite-embedding:278m",
        "dim":         384,
        "col":         "embedding_vector_granite",
        "model_filter": "granite-embedding:278m",
        # DEPRECATED: migrated to arctic. Kept for Recall@K comparison experiments only.
    },
}

# ── planned embedding models (not yet integrated) ─────────────────────────────
# EmbeddingGemma (google/embedding-gemma, 308M):
#   - MTEB: #1 ranking for sub-500M models (outperforms bge-m3 in that class)
#   - Context: 2K tokens (LIMITATION for book chunks — max ~1500 words)
#   - Status: Not in Ollama yet. Use via: pip install sentence-transformers
#   - Backend: sentence-transformers or HuggingFace transformers
#   - Suitable for: short query embedding, NOT full chapter/chunk embedding
#   - "gemma3_embed": {"hf_model": "google/embedding-gemma", "dim": 768, "col": "embedding_vector_gemma"}

# ── LLM model registry (for classification tasks) ─────────────────────────────
# Primary: Gemma 3 4B (Ollama: gemma3:4b | MLX: mlx-community/gemma-3-4b-it-4bit)
# - Beats llama3.2:3b on reasoning and comprehension, same ~2-3GB memory footprint
# - MLX throughput on M2 Pro 32GB: ~110 tok/s vs ~89 tok/s for llama3.2:3b via Ollama
# Upgrade path: gemma3:12b (~8GB) or gemma2:27b (~14GB int4) for higher quality


# ── helpers ───────────────────────────────────────────────────────────────────

def load_config():
    """Reload routing_config fresh each call (supports live edits)."""
    import routing_config as rc
    importlib.reload(rc)
    return rc


def classify_query(query: str, rc) -> str:
    """Classify a query text into a content type using the current config."""
    if rc.CLASSIFICATION_STRATEGY in ("always_bge",):
        return "semantic_narrative"
    if rc.CLASSIFICATION_STRATEGY in ("always_nomic",):
        return "general"

    q = query.lower()

    tech_score = sum(1 for kw in rc.TECHNICAL_KEYWORDS if kw in q)
    narr_score = sum(1 for kw in rc.NARRATIVE_KEYWORDS  if kw in q)
    cult_score = sum(1 for kw in rc.CULTURAL_KEYWORDS   if kw in q)

    if rc.CLASSIFICATION_STRATEGY == "genre_first":
        # genre markers in the query text itself take priority
        if any(g in q for g in rc.TECHNICAL_GENRES):
            return "technical_academic"
        if any(g in q for g in rc.NARRATIVE_GENRES):
            return "semantic_narrative"
        if any(g in q for g in rc.CULTURAL_GENRES):
            return "multilingual"

    # fall through to keyword scores
    if tech_score >= rc.TECHNICAL_THRESHOLD and tech_score >= narr_score and tech_score >= cult_score:
        return "technical_academic"
    if narr_score >= rc.NARRATIVE_THRESHOLD and narr_score >= cult_score:
        return "semantic_narrative"
    if cult_score >= rc.CULTURAL_THRESHOLD:
        return "multilingual"
    return "general"


def get_embedding(text: str, model_key: str, timeout: int = 60) -> Optional[list[float]]:
    """Call Ollama /api/embeddings and return the vector."""
    meta = MODEL_META[model_key]
    try:
        r = requests.post(
            f"{OLLAMA_BASE}/api/embeddings",
            json={"model": meta["ollama_name"], "prompt": text},
            timeout=timeout,
        )
        r.raise_for_status()
        return r.json().get("embedding")
    except Exception as e:
        print(f"  [embedding error] {model_key}: {e}")
        return None


def vector_search(embedding: list[float], model_key: str, k: int, conn) -> list[dict]:
    """Run pgvector cosine-similarity search; return top-k book records."""
    meta = MODEL_META[model_key]
    col  = meta["col"]
    dim  = meta["dim"]

    # Truncate/pad embedding to match column dimension
    if len(embedding) > dim:
        embedding = embedding[:dim]
    elif len(embedding) < dim:
        embedding = embedding + [0.0] * (dim - len(embedding))

    vec_literal = "[" + ",".join(f"{v:.8f}" for v in embedding) + "]"

    sql = f"""
        SELECT
            b.book_id,
            b.title,
            b.author,
            COALESCE(b.genre, '') AS genre,
            1 - (ce.{col} <=> %s::vector) AS similarity
        FROM chunk_embeddings ce
        JOIN chunks c  ON c.chunk_id  = ce.chunk_id
        JOIN books  b  ON b.book_id   = c.book_id
        WHERE ce.{col} IS NOT NULL
        ORDER BY ce.{col} <=> %s::vector
        LIMIT %s;
    """
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (vec_literal, vec_literal, k))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        print(f"  [db error]: {e}")
        conn.rollback()
        return []


def is_genre_hit(result_genre: str, expected_genres: list[str]) -> bool:
    """Return True if result_genre contains any expected genre string."""
    rg = result_genre.lower()
    return any(eg.lower() in rg for eg in expected_genres)


# ── main evaluation ───────────────────────────────────────────────────────────

def evaluate(verbose: bool = False) -> dict:
    """
    Run full Recall@K evaluation using current routing_config.

    Returns:
        {
            "recall_at_k":     float,   # primary metric (higher = better)
            "weighted_recall":  float,  # recall weighted by pair.weight
            "k":               int,
            "n_pairs":         int,
            "hits":            int,
            "model_usage":     dict,    # model_key → count
            "pair_results":    list,    # per-pair breakdown
            "duration_s":      float,
        }
    """
    rc      = load_config()
    pairs   = get_validation_pairs()
    k       = rc.RECALL_K
    t0      = time.time()

    hits        = 0
    total_w     = 0.0
    weighted_ok = 0.0
    model_usage: dict[str, int] = {}
    pair_results = []

    try:
        conn = psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        raise RuntimeError(f"Cannot connect to database: {e}")

    for pair in pairs:
        query           = pair["query"]
        expected_genres = pair["expected_genres"]
        weight          = pair.get("weight", 1.0)

        # 1. classify → model selection
        if rc.CLASSIFICATION_STRATEGY == "always_bge":
            model_key = "bge"
        elif rc.CLASSIFICATION_STRATEGY == "always_nomic":
            model_key = "nomic"
        else:
            content_type = classify_query(query, rc)
            model_key    = rc.MODEL_MAPPING.get(content_type, "nomic")

        model_usage[model_key] = model_usage.get(model_key, 0) + 1

        # 2. embed
        embedding = get_embedding(query, model_key)
        if embedding is None:
            pair_results.append({
                "query": query, "model": model_key, "hit": False,
                "error": "embedding failed", "weight": weight,
            })
            total_w += weight
            continue

        # 3. search
        results = vector_search(embedding, model_key, k, conn)

        # 4. check hit
        hit = any(is_genre_hit(r["genre"], expected_genres) for r in results)
        if hit:
            hits += 1
            weighted_ok += weight
        total_w += weight

        if verbose:
            status = "HIT" if hit else "miss"
            genre_sample = [r["genre"] for r in results[:3]]
            print(f"  [{status}] {query[:55]:<55} → {model_key}  genres={genre_sample}")

        pair_results.append({
            "query":      query,
            "model":      model_key,
            "hit":        hit,
            "weight":     weight,
            "top_books":  [r["title"] for r in results[:3]],
            "top_genres": [r["genre"] for r in results[:3]],
        })

    conn.close()
    duration = time.time() - t0

    recall    = hits / len(pairs) if pairs else 0.0
    w_recall  = weighted_ok / total_w if total_w > 0 else 0.0

    return {
        "recall_at_k":     round(recall,   4),
        "weighted_recall": round(w_recall, 4),
        "k":               k,
        "n_pairs":         len(pairs),
        "hits":            hits,
        "model_usage":     model_usage,
        "pair_results":    pair_results,
        "duration_s":      round(duration, 1),
    }


def check_ollama() -> bool:
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def check_db() -> bool:
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.close()
        return True
    except Exception:
        return False


# ── standalone run ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Checking prerequisites...")
    if not check_ollama():
        print("ERROR: Ollama is not running at", OLLAMA_BASE)
        print("  Start it with:  ollama serve")
        sys.exit(1)
    if not check_db():
        print("ERROR: Cannot connect to knowledge_base PostgreSQL")
        sys.exit(1)
    print("OK: Ollama + DB reachable\n")

    results = evaluate(verbose=True)
    print(f"\n{'='*60}")
    print(f"Recall@{results['k']}:       {results['recall_at_k']:.4f}  ({results['hits']}/{results['n_pairs']} hits)")
    print(f"Weighted Recall: {results['weighted_recall']:.4f}")
    print(f"Model usage:     {results['model_usage']}")
    print(f"Duration:        {results['duration_s']}s")
    print(f"{'='*60}")
