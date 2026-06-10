# Library of Babel

A personal library of 4,945 books, fully embedded and searchable by meaning.

## What it is

Every book is split into ~250-word passages, embedded with vector models, and indexed in PostgreSQL + pgvector. Search queries are embedded in real time via a local Ollama instance, then matched against 2.36 million passage vectors using HNSW indexing.

The entire system runs on a Mac Mini (M2 Pro).

## Numbers

| | |
|---|---|
| Books | 4,945 |
| Passages | 2,361,908 |
| Words | 1.2 billion |
| Embedding coverage | 100% |
| Database size | 112 GB |

## Embedding models

| Model | Dimensions | Coverage |
|---|---|---|
| nomic-embed-text-v2-moe | 768 | 96.4% (primary) |
| bge-m3 | 1024 | 90.2% |
| gemini-embedding-001 | 768 | 47.8% |

Search uses nomic-v2-moe as the primary model. Query embedding runs locally via Ollama.

## Seven modes of inquiry

The API is organized around seven epistemological modes -- none privileged over another:

**i. Meaning** (hermeneutic) -- Semantic search. Paste a passage or describe a theme, find where it resonates.
- `semantic_passages`, `semantic`, `passage`, `concept`, `emotional`

**ii. Reference** (referential) -- Keyword search. You know the word, find the exact match.
- `search`, `count`, `titles`, `books`, `has_results`

**iii. Analysis** (analytic) -- Cross-corpus pattern recognition.
- `discovery`, `style`, `quality`, `author_influence`, `thematic_evolution`, `content_analysis`

**iv. Reading** (exegetic) -- Navigate and read the texts page by page.
- `books`: list, summary, toc, page, random_page, construct

**v. Synthesis** (synthetic) -- Ask a question, get an answer from the corpus.
- `rag`

**vi. Discovery** (aleatory) -- Random pages, mobile shortcuts, serendipity.
- `mobile/random`, `mobile/search`, `mobile/stats`, `mobile/dashboard`

**vii. Instrument** (instrumental) -- The system itself.
- `health`, `info`, `mcp`, `upload`

## Architecture

```
EPUB --> text_chunker.py --> ~250-word passages --> PostgreSQL (chunks table)
                                                        |
                                                  Ollama / Gemini --> embeddings --> chunk_embeddings table
                                                        |
                                                  pgvector HNSW index
                                                        |
                                  Flask API (standardized_production_api.py) --> JSON responses
```

### Stack

- **Database**: PostgreSQL 14 + pgvector (HNSW indexes)
- **API**: Flask (Python 3.13), single-file standardized architecture
- **Embedding**: Ollama (nomic-embed-text-v2-moe) for queries, batch embedding via scripts
- **Frontend**: Static HTML (Newsreader + DM Sans, warm journal aesthetic)
- **Hosting**: Mac Mini M2 Pro, Tailscale for remote access
- **Production**: HTTPS via Let's Encrypt wildcard cert, port 5562

### Key files

```
src/api/standardized_production_api.py    # Main API server
src/api/modules/
  standardized_search.py                  # Search endpoint (16 actions)
  standardized_books.py                   # Books endpoint (6 actions)
  standardized_mcp.py                     # MCP server for Claude Desktop
  standardized_rag.py                     # RAG endpoint
  standardized_mobile.py                  # iOS Shortcuts endpoints
  standardized_upload.py                  # EPUB upload
  standardized_health.py                  # Health + info
  nomic_intelligent_search.py             # Vector search engine (CTE pattern)
  database.py                             # Connection management (120s timeout)
  auth.py                                 # API key auth
  validation.py                           # Parameter validation

src/text_chunker.py                       # Book --> passage chunking
src/advanced_semantic_chunker.py          # Semantic-aware chunking

scripts/
  gemini_reembed_all.py                   # Gemini batch embedding (credits depleted)
  ollama_reembed_parallel.py              # Ollama parallel embedding (DO NOT RUN -- all chunks covered)
  rechunk_monsters.py                     # Re-chunk oversized passages (22,601 segments created)
  chunk_processing_daemon.py              # Background chunking daemon

frontend/out/                             # Static site (warm journal aesthetic)
  index.html                              # Landing page with live search
  api-docs/index.html                     # Interactive API reference (7 sections)
  browse/index.html                       # Book catalog + e-reader (infinite scroll)
  demo/index.html                         # Full search interface (16 modes)
  upload/index.html                       # EPUB upload with drag-and-drop
```

### Database schema

```sql
-- Core tables
books (book_id, title, author, genre, word_count, ...)
chunks (chunk_id, book_id, chunk_type, content, word_count, parent_chunk_id, ...)
chunk_embeddings (chunk_id, book_id, embedding_model, embedding_dimension, embedding_vector)

-- Vector indexes
idx_chunk_embeddings_hnsw       -- HNSW cosine index (all models, 12 GB)
idx_embeddings_bge_hnsw_1024    -- HNSW for bge-m3 1024d (15 GB)

-- The chunks table has 39 indexes (some legacy). Run ANALYZE chunks after bulk operations.
-- pg_trgm extension is in semantic_archive schema, not public.
```

## Running

### Production (port 5562)

```bash
./production_api_service.sh restart
```

### Staging (port 5564)

```bash
PYTHONPATH="src" python3.13 src/api/standardized_production_api.py
```

Note: Use `python3.13` (has Flask), not `python3` (3.14, no Flask).

### Authentication

API key via `X-API-Key` header. Health endpoints are public. `localhost` bypasses auth.

## API quick reference

```bash
# Semantic passage search
curl "localhost:5564/api/search?q=the+moral+weight+of+idleness&action=semantic_passages&limit=5"

# List books by genre
curl "localhost:5564/api/books?action=list&limit=20&genre=Philosophy"

# Read a page
curl "localhost:5564/api/books?action=page&id=100&page_num=1"

# RAG -- ask the library
curl "localhost:5564/api/rag?q=What+do+the+books+say+about+power+and+knowledge"

# Health
curl "localhost:5564/api/health"
```

Full interactive API reference at `/api-docs/`

## Website

| Page | URL | Description |
|---|---|---|
| Landing | `/` | Search + seven modes overview |
| Browse | `/browse/` | Book catalog, genre filters, infinite scroll, e-reader |
| Search | `/demo/` | All 16 search modes |
| API Docs | `/api-docs/` | Interactive reference with "Try it" |
| Upload | `/upload/` | EPUB drag-and-drop upload |

## Integrations

### MCP (Claude Desktop)

MCP server at `/api/mcp` enables natural language queries against the library from Claude Desktop.

### Life Dashboard (:4500/research)

Highlights and audiomarks from reading are cross-referenced against the library:
- **Find in Library** -- passage-level semantic search (prose mode, no NLP condensation)
- **Mind Map** -- auto-clusters recent reading, finds library connections
- **Themes** -- groups reading into book-based clusters with YAKE sublabels
- **Reading Radar** -- recommends unread books based on recent patterns
- **Search bar** -- two modes: Prose (raw passage) and Keywords (spaCy NLP extract)

### iOS Shortcuts

Mobile-optimized endpoints at `/api/mobile/*` for random quotes, quick search, stats widgets.

## Operational notes

- **Never leave ollama_reembed_parallel.py running** when all chunks are covered. It creates zombie DB connections that thrash disk I/O and block all queries.
- **Statement timeout** is 120s (set in database.py). Vector search uses CTE pattern (HNSW first, then JOIN) to stay under this limit.
- **Gemini credits are depleted**. The search pipeline skips Gemini and goes straight to Ollama for query embedding.
- **Cost lesson**: Use average word count (510) for cost estimates, not median (210). The long tail of monster chunks makes avg >> median.
- Run `ANALYZE chunks;` after killing zombie queries or bulk operations.
- Check for zombie connections: `SELECT count(*) FROM pg_stat_activity WHERE state='active';`
