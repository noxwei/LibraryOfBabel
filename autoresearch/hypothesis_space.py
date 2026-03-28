"""
hypothesis_space.py — Ordered list of routing configs to try

Each entry is a complete routing_config override dict.
The experiment loop iterates through this list in order,
keeping a config if recall improves and reverting otherwise.

Add new hypotheses at the end; don't reorder — the loop tracks
its position by index and saves it in state.json.
"""

HYPOTHESES = [
    # ── 0: BASELINE — matches routing_config.py defaults ─────────────────────
    {
        "name": "baseline",
        "description": "Default: BGE for tech+narrative, mxbai for cultural, nomic for general",
        "MODEL_MAPPING": {
            "technical_academic": "bge",
            "semantic_narrative": "bge",
            "multilingual":       "mxbai",
            "general":            "nomic",
        },
        "CLASSIFICATION_STRATEGY": "genre_first",
        "TECHNICAL_THRESHOLD": 2,
        "NARRATIVE_THRESHOLD": 2,
        "CULTURAL_THRESHOLD":  2,
        "RECALL_K": 10,
    },

    # ── 1: Always BGE ─────────────────────────────────────────────────────────
    {
        "name": "always_bge",
        "description": "Use BGE for every query — skip classification entirely",
        "MODEL_MAPPING": {
            "technical_academic": "bge",
            "semantic_narrative": "bge",
            "multilingual":       "bge",
            "general":            "bge",
        },
        "CLASSIFICATION_STRATEGY": "always_bge",
        "TECHNICAL_THRESHOLD": 2,
        "NARRATIVE_THRESHOLD": 2,
        "CULTURAL_THRESHOLD":  2,
        "RECALL_K": 10,
    },

    # ── 2: Always nomic ───────────────────────────────────────────────────────
    {
        "name": "always_nomic",
        "description": "Use nomic for every query — simpler, lower latency",
        "MODEL_MAPPING": {
            "technical_academic": "nomic",
            "semantic_narrative": "nomic",
            "multilingual":       "nomic",
            "general":            "nomic",
        },
        "CLASSIFICATION_STRATEGY": "always_nomic",
        "TECHNICAL_THRESHOLD": 2,
        "NARRATIVE_THRESHOLD": 2,
        "CULTURAL_THRESHOLD":  2,
        "RECALL_K": 10,
    },

    # ── 3: Always mxbai ───────────────────────────────────────────────────────
    {
        "name": "always_mxbai",
        "description": "Use mxbai for every query",
        "MODEL_MAPPING": {
            "technical_academic": "mxbai",
            "semantic_narrative": "mxbai",
            "multilingual":       "mxbai",
            "general":            "mxbai",
        },
        "CLASSIFICATION_STRATEGY": "always_bge",  # reuse bypass logic
        "TECHNICAL_THRESHOLD": 2,
        "NARRATIVE_THRESHOLD": 2,
        "CULTURAL_THRESHOLD":  2,
        "RECALL_K": 10,
    },

    # ── 4: Keyword-first classification ───────────────────────────────────────
    {
        "name": "keyword_first",
        "description": "Classify by keyword score, not genre labels",
        "MODEL_MAPPING": {
            "technical_academic": "bge",
            "semantic_narrative": "bge",
            "multilingual":       "mxbai",
            "general":            "nomic",
        },
        "CLASSIFICATION_STRATEGY": "keyword_first",
        "TECHNICAL_THRESHOLD": 2,
        "NARRATIVE_THRESHOLD": 2,
        "CULTURAL_THRESHOLD":  2,
        "RECALL_K": 10,
    },

    # ── 5: Lower keyword thresholds (1 hit triggers classification) ───────────
    {
        "name": "low_thresholds",
        "description": "Trigger classification with 1 keyword match instead of 2",
        "MODEL_MAPPING": {
            "technical_academic": "bge",
            "semantic_narrative": "bge",
            "multilingual":       "mxbai",
            "general":            "nomic",
        },
        "CLASSIFICATION_STRATEGY": "genre_first",
        "TECHNICAL_THRESHOLD": 1,
        "NARRATIVE_THRESHOLD": 1,
        "CULTURAL_THRESHOLD":  1,
        "RECALL_K": 10,
    },

    # ── 6: Higher thresholds (3 hits required) ────────────────────────────────
    {
        "name": "high_thresholds",
        "description": "Require 3 keyword matches — more queries fall to 'general'",
        "MODEL_MAPPING": {
            "technical_academic": "bge",
            "semantic_narrative": "bge",
            "multilingual":       "mxbai",
            "general":            "nomic",
        },
        "CLASSIFICATION_STRATEGY": "genre_first",
        "TECHNICAL_THRESHOLD": 3,
        "NARRATIVE_THRESHOLD": 3,
        "CULTURAL_THRESHOLD":  3,
        "RECALL_K": 10,
    },

    # ── 7: BGE for technical, mxbai for narrative ─────────────────────────────
    {
        "name": "bge_tech_mxbai_narrative",
        "description": "Swap narrative model to mxbai for richer contextual recall",
        "MODEL_MAPPING": {
            "technical_academic": "bge",
            "semantic_narrative": "mxbai",
            "multilingual":       "mxbai",
            "general":            "nomic",
        },
        "CLASSIFICATION_STRATEGY": "genre_first",
        "TECHNICAL_THRESHOLD": 2,
        "NARRATIVE_THRESHOLD": 2,
        "CULTURAL_THRESHOLD":  2,
        "RECALL_K": 10,
    },

    # ── 8: nomic for technical, bge for narrative ─────────────────────────────
    {
        "name": "nomic_tech_bge_narrative",
        "description": "nomic for technical (broader coverage), bge for narrative",
        "MODEL_MAPPING": {
            "technical_academic": "nomic",
            "semantic_narrative": "bge",
            "multilingual":       "mxbai",
            "general":            "nomic",
        },
        "CLASSIFICATION_STRATEGY": "genre_first",
        "TECHNICAL_THRESHOLD": 2,
        "NARRATIVE_THRESHOLD": 2,
        "CULTURAL_THRESHOLD":  2,
        "RECALL_K": 10,
    },

    # ── 9: Increase K to 20 ───────────────────────────────────────────────────
    {
        "name": "k20_baseline",
        "description": "Wider retrieval window K=20 with baseline routing",
        "MODEL_MAPPING": {
            "technical_academic": "bge",
            "semantic_narrative": "bge",
            "multilingual":       "mxbai",
            "general":            "nomic",
        },
        "CLASSIFICATION_STRATEGY": "genre_first",
        "TECHNICAL_THRESHOLD": 2,
        "NARRATIVE_THRESHOLD": 2,
        "CULTURAL_THRESHOLD":  2,
        "RECALL_K": 20,
    },

    # ── 10: K=5 (tighter eval) ────────────────────────────────────────────────
    {
        "name": "k5_always_bge",
        "description": "Stricter Recall@5 with always-BGE routing",
        "MODEL_MAPPING": {
            "technical_academic": "bge",
            "semantic_narrative": "bge",
            "multilingual":       "bge",
            "general":            "bge",
        },
        "CLASSIFICATION_STRATEGY": "always_bge",
        "TECHNICAL_THRESHOLD": 2,
        "NARRATIVE_THRESHOLD": 2,
        "CULTURAL_THRESHOLD":  2,
        "RECALL_K": 5,
    },

    # ── 11: mxbai for everything except narratives ────────────────────────────
    {
        "name": "mxbai_heavy",
        "description": "mxbai handles technical+cultural; bge handles narrative",
        "MODEL_MAPPING": {
            "technical_academic": "mxbai",
            "semantic_narrative": "bge",
            "multilingual":       "mxbai",
            "general":            "mxbai",
        },
        "CLASSIFICATION_STRATEGY": "keyword_first",
        "TECHNICAL_THRESHOLD": 1,
        "NARRATIVE_THRESHOLD": 2,
        "CULTURAL_THRESHOLD":  1,
        "RECALL_K": 10,
    },

    # ── 12: nomic as fallback, lower thresholds ───────────────────────────────
    {
        "name": "nomic_fallback_low",
        "description": "Low thresholds + nomic as broad fallback",
        "MODEL_MAPPING": {
            "technical_academic": "bge",
            "semantic_narrative": "bge",
            "multilingual":       "mxbai",
            "general":            "nomic",
        },
        "CLASSIFICATION_STRATEGY": "keyword_first",
        "TECHNICAL_THRESHOLD": 1,
        "NARRATIVE_THRESHOLD": 1,
        "CULTURAL_THRESHOLD":  2,
        "RECALL_K": 10,
    },

    # ── 13: bge for general fallback (not nomic) ──────────────────────────────
    {
        "name": "bge_as_general_fallback",
        "description": "Replace nomic fallback with bge — higher quality at higher cost",
        "MODEL_MAPPING": {
            "technical_academic": "bge",
            "semantic_narrative": "bge",
            "multilingual":       "mxbai",
            "general":            "bge",
        },
        "CLASSIFICATION_STRATEGY": "genre_first",
        "TECHNICAL_THRESHOLD": 2,
        "NARRATIVE_THRESHOLD": 2,
        "CULTURAL_THRESHOLD":  2,
        "RECALL_K": 10,
    },

    # ── 14: Aggressive classification — everything to its specialist ──────────
    {
        "name": "full_specialist_routing",
        "description": "Every content type routed to its intended specialist model",
        "MODEL_MAPPING": {
            "technical_academic": "granite",
            "semantic_narrative": "bge",
            "multilingual":       "mxbai",
            "general":            "nomic",
        },
        "CLASSIFICATION_STRATEGY": "genre_first",
        "TECHNICAL_THRESHOLD": 2,
        "NARRATIVE_THRESHOLD": 2,
        "CULTURAL_THRESHOLD":  2,
        "RECALL_K": 10,
    },
]
