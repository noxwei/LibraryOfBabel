"""
validation_pairs.py — Ground-truth validation set

Each entry is a dict with:
  query          : the search string
  expected_genres: list of genre strings — a hit means at least one
                   top-K result has a genre containing any of these
  category       : human-readable grouping label
  weight         : importance multiplier (default 1.0)

Genre strings are matched as case-insensitive substrings against the
books.genre column, so "fiction" matches "Science Fiction", "Literary Fiction", etc.

HOW TO EXTEND:
  Add rows to VALIDATION_PAIRS below. The more specific the expected_genres,
  the harder the test. Start broad ("fiction") and tighten once baseline > 0.5.
"""

VALIDATION_PAIRS = [
    # ── Fiction / Narrative ───────────────────────────────────────────────────
    {
        "query": "robots obey humans three laws of robotics",
        "expected_genres": ["fiction", "science fiction", "sci-fi"],
        "category": "sci-fi-specific",
        "weight": 1.5,
    },
    {
        "query": "dystopian society totalitarian government surveillance control",
        "expected_genres": ["fiction", "dystopian", "science fiction"],
        "category": "sci-fi-general",
        "weight": 1.0,
    },
    {
        "query": "hero's journey magical quest fantasy world",
        "expected_genres": ["fantasy", "fiction", "adventure"],
        "category": "fantasy",
        "weight": 1.0,
    },
    {
        "query": "detective murder mystery investigation crime scene",
        "expected_genres": ["mystery", "thriller", "crime", "fiction"],
        "category": "mystery",
        "weight": 1.0,
    },
    {
        "query": "romantic love forbidden relationship passion",
        "expected_genres": ["romance", "fiction", "literary"],
        "category": "romance",
        "weight": 1.0,
    },
    {
        "query": "vampire werewolf supernatural horror darkness",
        "expected_genres": ["horror", "fiction", "fantasy"],
        "category": "horror",
        "weight": 1.0,
    },
    {
        "query": "space exploration colonization alien civilization",
        "expected_genres": ["science fiction", "fiction", "sci-fi"],
        "category": "sci-fi-space",
        "weight": 1.0,
    },

    # ── Technical / Academic ──────────────────────────────────────────────────
    {
        "query": "quantum mechanics wave function particle physics",
        "expected_genres": ["science", "physics", "academic", "nonfiction"],
        "category": "physics",
        "weight": 1.5,
    },
    {
        "query": "machine learning neural network deep learning algorithm",
        "expected_genres": ["technology", "computer", "science", "academic"],
        "category": "ml-ai",
        "weight": 1.5,
    },
    {
        "query": "economic inequality wealth distribution capitalism",
        "expected_genres": ["economics", "business", "nonfiction", "social"],
        "category": "economics",
        "weight": 1.0,
    },
    {
        "query": "evolutionary biology natural selection genetics darwin",
        "expected_genres": ["science", "biology", "academic", "nonfiction"],
        "category": "biology",
        "weight": 1.0,
    },
    {
        "query": "software architecture design patterns programming",
        "expected_genres": ["technology", "computer", "programming", "technical"],
        "category": "software",
        "weight": 1.0,
    },

    # ── Philosophy / Ideas ────────────────────────────────────────────────────
    {
        "query": "meaning of life existentialism freedom choice responsibility",
        "expected_genres": ["philosophy", "academic", "nonfiction"],
        "category": "existentialism",
        "weight": 1.0,
    },
    {
        "query": "ethics morality good evil moral reasoning",
        "expected_genres": ["philosophy", "ethics", "academic"],
        "category": "ethics",
        "weight": 1.0,
    },
    {
        "query": "consciousness mind brain cognitive science",
        "expected_genres": ["philosophy", "science", "psychology", "academic"],
        "category": "consciousness",
        "weight": 1.0,
    },

    # ── History / Culture ─────────────────────────────────────────────────────
    {
        "query": "world war military strategy battles history",
        "expected_genres": ["history", "nonfiction", "military"],
        "category": "history-war",
        "weight": 1.0,
    },
    {
        "query": "ancient civilization empire rome greece egypt",
        "expected_genres": ["history", "archaeology", "nonfiction"],
        "category": "ancient-history",
        "weight": 1.0,
    },
    {
        "query": "biography life story personal memoir",
        "expected_genres": ["biography", "memoir", "nonfiction"],
        "category": "biography",
        "weight": 1.0,
    },
    {
        "query": "culture tradition society anthropology",
        "expected_genres": ["anthropology", "sociology", "history", "cultural"],
        "category": "culture",
        "weight": 1.0,
    },

    # ── Psychology / Self-help ────────────────────────────────────────────────
    {
        "query": "human behavior psychology motivation cognitive bias",
        "expected_genres": ["psychology", "science", "self-help", "nonfiction"],
        "category": "psychology",
        "weight": 1.0,
    },
    {
        "query": "leadership management success habits productivity",
        "expected_genres": ["self-help", "business", "nonfiction"],
        "category": "self-help",
        "weight": 1.0,
    },

    # ── Cross-domain / Hard ───────────────────────────────────────────────────
    {
        "query": "technology society culture impact human connection",
        "expected_genres": ["nonfiction", "technology", "sociology", "culture"],
        "category": "cross-domain",
        "weight": 0.75,
    },
    {
        "query": "power corruption political systems governance",
        "expected_genres": ["nonfiction", "politics", "history", "fiction"],
        "category": "politics",
        "weight": 0.75,
    },
    {
        "query": "climate change environment sustainability future",
        "expected_genres": ["science", "environment", "nonfiction"],
        "category": "environment",
        "weight": 1.0,
    },
]


def get_validation_pairs():
    return VALIDATION_PAIRS


def summary():
    categories = {}
    for p in VALIDATION_PAIRS:
        categories.setdefault(p["category"], 0)
        categories[p["category"]] += 1
    print(f"Total pairs: {len(VALIDATION_PAIRS)}")
    print(f"Categories: {len(categories)}")
    for cat, n in sorted(categories.items()):
        print(f"  {cat}: {n}")


if __name__ == "__main__":
    summary()
