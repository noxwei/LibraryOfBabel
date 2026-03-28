"""
routing_config.py — MUTABLE CONFIG

This is the file the experiment loop modifies between runs.
The loop reads ROUTING_CONFIG, evaluates Recall@K, then either
keeps or reverts this file based on whether recall improved.

Do NOT edit by hand during a running experiment.
"""

# ── LLM model for classification and query analysis ───────────────────────────
# Ollama: pull with `ollama pull gemma3:4b`
# MLX (Apple Silicon, ~2.5x faster): mlx-community/gemma-3-4b-it-4bit via mlx-lm
# Fallback: "llama3.2:3b" (smaller, lower quality)
# Large option: "gemma3:12b" (~8GB, higher reasoning quality)
LLM_MODEL = "gemma3:4b"
LLM_MODEL_MLX = "mlx-community/gemma-3-4b-it-4bit"

# ── Model assignment by content type ──────────────────────────────────────────
# Keys must match the content types returned by classify_query()
# Values must be one of: "bge", "nomic", "mxbai", "arctic"
# Planned: "gemma3_embed" (EmbeddingGemma 308M, MTEB SOTA sub-500M) — awaiting Ollama support
MODEL_MAPPING = {
    "technical_academic": "bge",
    "semantic_narrative": "bge",
    "multilingual":       "mxbai",
    "general":            "nomic",
}

# ── Query classification thresholds ───────────────────────────────────────────
# Minimum keyword hits needed to trigger a non-general classification
TECHNICAL_THRESHOLD = 2
NARRATIVE_THRESHOLD = 2
CULTURAL_THRESHOLD  = 2

# ── Classification strategy ───────────────────────────────────────────────────
# "genre_first"   : genre keywords win ties
# "keyword_first" : raw keyword count wins ties
# "always_bge"    : bypass classification, always use BGE
# "always_nomic"  : bypass classification, always use nomic
CLASSIFICATION_STRATEGY = "genre_first"

# ── Search parameters ─────────────────────────────────────────────────────────
RECALL_K        = 10    # how many results to retrieve per query
SIMILARITY_MIN  = 0.0   # cosine distance threshold (0.0 = no filter)

# ── Content-type keyword lists ─────────────────────────────────────────────────
TECHNICAL_KEYWORDS = [
    "technology", "science", "research", "analysis", "theory", "methodology",
    "academic", "scholarly", "technical", "engineering", "mathematics",
    "physics", "chemistry", "biology", "computer", "algorithm", "quantum",
    "neural", "statistical", "empirical", "hypothesis",
]

NARRATIVE_KEYWORDS = [
    "story", "novel", "fiction", "fantasy", "adventure", "romance",
    "character", "plot", "narrative", "tale", "saga", "epic", "dystopian",
    "protagonist", "mystery", "thriller", "detective", "hero", "journey",
]

CULTURAL_KEYWORDS = [
    "culture", "cultural", "international", "global", "world", "foreign",
    "translation", "history", "memoir", "biography", "travel", "ethnography",
    "civilization", "society", "tradition", "heritage", "colonial",
]

TECHNICAL_GENRES = [
    "philosophy", "science", "technology", "academic", "business", "economics",
    "mathematics", "computer science", "engineering",
]
NARRATIVE_GENRES = [
    "fiction", "fantasy", "science fiction", "romance", "literary",
    "mystery", "thriller", "horror", "adventure",
]
CULTURAL_GENRES = [
    "history", "cultural", "biography", "memoir", "travel",
    "sociology", "anthropology",
]
