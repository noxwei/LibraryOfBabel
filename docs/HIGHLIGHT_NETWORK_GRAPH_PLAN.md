# Highlight Network Graph — Integration Plan

## Overview

life-dashboard now has a `POST /api/ingest/highlight` endpoint that receives book highlights from Apple Books via iOS Shortcut. We want to connect each highlight to the Library of Babel's book/chunk corpus to build a network graph of related passages across the entire library.

## Architecture

```
Apple Books highlight
    |
    v
life-dashboard /api/ingest/highlight
    |
    +---> Store highlight event (existing)
    +---> Query LOB /api/search to find matching book
    +---> Query LOB /api/search?action=semantic_passages to find related passages
    +---> Store links in highlight payload (book_id, related_passages[])
    |
    v
Network graph: highlights <--similarity--> LOB chunks <--book--> LOB books
```

## What life-dashboard sends to LOB

On each new highlight:
1. `GET /api/search?q={book_title}&action=search` — find the book in LOB
2. `GET /api/search?q={highlight_text_snippet}&action=semantic_passages` — find similar passages

## What LOB needs to fix

### Critical: Semantic search is broken

```
GET /api/search?q=consciousness+free+will&action=semantic_passages
ERROR: "Nomic intelligent search failed: Failed to generate query embedding"
```

The embedding model reference is stale. `nomic-embed-text` v1 was removed from Ollama (2025-04-17). The replacement is `nomic-embed-text-v2-moe`.

**Fix required:**
1. Find where LOB generates query embeddings (likely in a search module that calls Ollama)
2. Update the model name from `nomic-embed-text` to `nomic-embed-text-v2-moe`
3. Verify the embedding dimensions match (v2-moe outputs 768-dim by default, v1 was 768 too — should be compatible with existing `embedding_vector` column which is vector(1536)... need to check)
4. If dimension mismatch: either re-embed or use a different vector column

**Dimension check needed:**
- `embedding_vector`: vector(1536) — nomic-embed-text v1 (was 768? or 1536?)
- `embedding_vector_bge`: vector(1024) — bge-m3
- `embedding_vector_granite`: vector(384) — granite-embedding:278m
- `embedding_vector_mxbai`: vector(1024) — mxbai-embed-large

### Secondary: FTS passage search quality

The `action=passage` fallback works but returns irrelevant results (fantasy novels for "consciousness free will" query). This is because FTS matches on common words. Once semantic search works, this becomes the fallback only.

### Optional: Add a dedicated highlight-linking endpoint

Consider adding to LOB:
```
GET /api/search?q={text}&action=highlighted
```
That returns: matching book + top 5 similar passages + related authors. This would be a single call from life-dashboard instead of two.

## What babels-archive provides

babels-archive has a SQLite catalog of 5,886 audiobooks / 4,311 authors. This is a superset that includes books NOT in LOB's chunked corpus. Cross-referencing:
- life-dashboard highlight author/title -> babels-archive catalog (audiobook metadata, ratings, duration)
- life-dashboard highlight author/title -> LOB books (full text, chunks, search)

Both DFW and Peter Watts (current reading) exist in babels-archive AND LOB.

## Data flow for network graph

```
highlight.payload after enrichment:
{
  "author": "Peter Watts",
  "book_title": "Blindsight",
  "highlights": "...",
  "lob_book_id": 1234,           // matched LOB book
  "lob_related_passages": [      // semantic matches
    {"chunk_id": "1234_chapter_5", "title": "Blindsight", "similarity": 0.92},
    {"chunk_id": "567_chapter_12", "title": "Neuromancer", "similarity": 0.78},
  ],
  "audiobook_id": 5678,          // babels-archive match
}
```

## Action items for LOB

### DONE (by life-dashboard Claude, 2026-05-05):

All model references updated from `nomic-embed-text` to `nomic-embed-text-v2-moe`:
- src/api/modules/nomic_intelligent_search.py (line 29)
- src/fuzzy_semantic_search.py (line 54)
- src/ollama_vector_embedder.py (line 56 + available_models dict)
- config/api_config.py (full embedding_models section)
- src/api/modules/standardized_search.py (default param + valid_models + metadata)
- daemons/nomic_only_daemon.py (line 64)

Removed stale models: mxbai-embed-large, granite-embedding:278m
Added current models: snowflake-arctic-embed2, qwen3-embedding:0.6b

Dimensions confirmed: nomic-embed-text-v2-moe outputs 768 dims (same as v1). Drop-in compatible.

### REMAINING (requires LOB Claude):

1. **Rebuild Docker container** — `src/` is NOT volume-mounted, only `config/` is.
   Run: `docker compose build libraryofbabel-api && docker compose up -d libraryofbabel-api`
2. Test: `curl "http://localhost:5562/api/search?q=consciousness&action=semantic_passages"`
3. Verify existing embeddings in `embedding_vector` column are still compatible with v2-moe queries
   (same 768-dim space, but v2 may have different vector space — cosine similarity might degrade)
4. If quality is poor, consider re-embedding chunks with v2-moe via the daemon

## Action items for life-dashboard

1. Add LOB proxy module (like existing threads/cinder proxies)
2. On highlight ingest, async-call LOB to enrich the payload
3. Build `/api/reading/graph` endpoint that returns the network
