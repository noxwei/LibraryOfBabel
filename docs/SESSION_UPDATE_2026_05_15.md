# Session Update: May 14-15, 2026 -- Gemini Nuclear Re-embed + Research Page

## Summary

Migrated the entire LibraryOfBabel embedding pipeline from local Ollama (nomic-embed-text-v2-moe) to Google Gemini API (gemini-embedding-001, 768d). Wrote a batch re-embed script to process all 2.4M chunks. Built a unified Research page on life-dashboard that consolidates search, mind map, and highlights into one tabbed interface. Added "Find in Library" to journal entries and improved semantic search quality across the board.

---

## 1. Gemini Embedding Migration

### What changed

- **Primary embedding model**: `gemini-embedding-001` (Google Cloud, 768d) replaces `nomic-embed-text-v2-moe` (local Ollama, 768d).
- **Query embedding**: All search queries now call the Gemini API directly. No Ollama dependency for search.
- **Upload pipeline**: New book uploads embed via Gemini API first, with Ollama as fallback if no API key is set.
- **Multi-model fallback in search**: Gemini results are returned first. If fewer than `limit` results come back (because the re-embed is still in progress), the system falls back to nomic-v2-moe embeddings via local Ollama to fill the gap. Deduplication by chunk_id prevents duplicates.
- **Environment variable**: `GEMINIAPI_KEY` must be set in `.env` and is passed through `docker-compose.yml`.
- **Query max_length**: Bumped from 500 to 4000 characters in validation.py to support full passage search.
- **Default embedding_model in validation**: Changed from `nomic-embed-text-v2-moe` to `gemini-embedding-001`.

### Search flow (new)

```
User query
  -> Gemini API (gemini-embedding-001, 768d)
  -> pgvector cosine similarity against chunk_embeddings WHERE embedding_model = 'gemini-embedding-001'
  -> If results < limit:
       -> Ollama (nomic-embed-text-v2-moe) for query embedding
       -> pgvector search WHERE embedding_model = 'nomic-embed-text-v2-moe'
       -> Merge + deduplicate
  -> Re-sort by similarity_score
  -> Return results with 300-word previews
```

### Budget and cost

- $25 prepaid on Google Cloud.
- ~$2 test run (small batch) confirmed it works.
- Full send on remaining 2.4M chunks. Batch API: 100 texts per call, 0.3s throttle (~200 RPM Paid Tier 1).
- Estimated ~19 hours for full re-embed at ~31 chunks/sec.

---

## 2. Nuclear Re-embed Script

`/Users/weixiangzhang/Local_Dev/projects/LibraryOfBabel/scripts/gemini_reembed_all.py`

- Batch embeds all chunks that don't have a `gemini-embedding-001` row in `chunk_embeddings`.
- Uses `batchEmbedContents` API endpoint (100 texts per call).
- Rate limit handling: 429 responses trigger exponential backoff (30-60s).
- Graceful shutdown via SIGTERM (finishes current batch, saves state).
- Progress logged to `logs/gemini_reembed.log` and state saved to `logs/gemini_reembed_state.json`.
- Budget cap configurable via `MAX_CHUNKS` (0 = unlimited).
- Truncates texts to 8000 chars before embedding.
- ON CONFLICT DO NOTHING for idempotent re-runs.
- Run in screen session: `screen -S gemini_reembed`.

---

## 3. Semantic Search Improvements

### In life-dashboard's `html_fragments.py` (`_extract_query`)

- **Removed YAKE keyword extraction**: Passages now go directly to Gemini semantic search. Gemini embeddings understand meaning from natural prose; keyword extraction was losing context.
- **Removed audiomark center-extract**: Full transcript is now used. The old logic extracted just the middle third (assuming the audiomark button press caught mid-transcript), but full text gives Gemini better semantic understanding.
- **Truncation**: Capped at 500 words (simple word split), keeping prose intact.

### In `reading_related` endpoint

- **Same-book deduplication**: Results are filtered to max 1 result per unique book title (`seen_titles` set).
- **Minimum similarity threshold**: 0.45 -- passages below this are dropped.
- **Junk preview filtering**: `_is_junk_preview()` catches TOC dumps, front matter, page number sequences.
- **COALESCE chain expanded**: Added `payload->>'text'` and `payload->>'entry_raw'` to the query so journal entries work with "Find in Library".

### In `nomic_intelligent_search.py`

- **Preview bumped from 200 to 300 words**: `intelligent_preview()` now generates 300-word previews ending at the next period.
- **Reading link page estimation fixed**: Was always returning page 1. Now calculates from cumulative word counts of preceding chunks via SQL: `SUM(word_count) WHERE chunk_id < target_chunk_id`.

---

## 4. Research Page (`/research`)

`/Users/weixiangzhang/Local_Dev/projects/life-dashboard/app/static/babel.html`

Unified page replacing both `/serendipity` and `/babel`. Three tabs:

### Search tab
- Full-width textarea (resizable, multi-line).
- Paste passages up to 600+ words.
- Semantic search against 4,945 books via `/api/lob/search`.
- Client-side deduplication by book title.
- Each result shows: title, author, similarity %, 300-word preview.
- Actions per result: "read full passage" (expand), "read in book" (inline paginated reader), "save" (bookmark).

### Mind Map tab
- Pulls last N days (3/7/14/30/90, configurable via dropdown) of journal/audiomark/highlight events.
- Each event is cross-referenced against the library via `/api/babel/mind-map`.
- Shows the source text (expandable) with type badge (Journal/Audiomark/Highlight) and time ago.
- Below each source: matching passages from the library with similarity scores.
- Same deduplication and filtering as reading_related.

### Highlights tab
- Ported from the old serendipity page.
- Book grid showing all highlighted/audiomarked books.
- Click a book to see all passages.
- Each passage has a "Find in Library" button.

### Tab behavior
- Tab state persists via `localStorage` ('babel-tab') and URL hash (`#search`, `#mindmap`, `#highlights`).
- Default tab: `mindmap`.
- `/serendipity` and `/babel` both redirect to `/research`.

---

## 5. Life-Dashboard Integration

### Journal page "Find in Library"

`/Users/weixiangzhang/Local_Dev/projects/life-dashboard/app/static/journal.html`

- Every journal entry with 30+ characters gets a "Find in Library" button.
- Clicking it calls `/api/reading/related?event_id=...&limit=8`.
- Results displayed inline with expand/collapse, inline book reader.

### Bookmark system

Backend endpoints in `html_fragments.py`:

- `POST /api/babel/bookmark` -- saves a discovered passage as a `babel_bookmark` event in the events table. Payload includes title, author, preview, book_id, chunk_id, similarity.
- `GET /api/babel/bookmarks` -- lists saved bookmarks.

### Proxy routes

- `GET /api/lob/search` -- proxies to LoB API at `http://localhost:5564/api/search`.
- `GET /api/lob/toc` -- proxies to LoB TOC endpoint.
- `GET /api/lob/book-page` -- proxies to LoB book page endpoint.

### Navigation

All nav links across 7+ HTML pages updated: "Library" and "Babel" links replaced with single "Research" link pointing to `/research`.

### Route consolidation in `main.py`

- `/research` serves `babel.html`.
- `/serendipity` redirects to `/research`.
- `/babel` redirects to `/research`.

---

## 6. Database State

### chunk_embeddings table (LibraryOfBabel / knowledge_base)

| Model | Dimension | Status |
|---|---|---|
| gemini-embedding-001 | 768 | In progress (~340K+ at session start, targeting 2.36M) |
| nomic-embed-text-v2-moe | 768 | ~430K (legacy, still queryable) |
| bge-m3 | 1024 | ~2.1M (secondary) |

### life-dashboard events table

- 1,559+ events with 768d embeddings.
- New event type: `babel_bookmark`.

### Re-embed daemon

- Running in screen session `gemini_reembed`.
- Rate: ~31 chunks/sec.
- State file: `/Users/weixiangzhang/Local_Dev/projects/LibraryOfBabel/logs/gemini_reembed_state.json`.

---

## 7. Key Files Modified

### LibraryOfBabel project

| File | Change |
|---|---|
| `src/api/modules/nomic_intelligent_search.py` | Gemini API for query embedding, multi-model fallback search, 300-word previews, reading link page estimation fix |
| `src/api/modules/standardized_upload.py` | Upload embedding pipeline uses Gemini API (fallback Ollama) |
| `src/api/modules/validation.py` | Query max_length 500->4000, default embedding_model changed to gemini-embedding-001 |
| `config/api_settings.json` | Default model set to gemini-embedding-001, added provider/api fields |
| `docker-compose.yml` | GEMINIAPI_KEY environment variable passthrough |
| `scripts/gemini_reembed_all.py` | New: batch re-embed script for all 2.4M chunks |
| `src/api/modules/standardized_rag.py` | New: standardized RAG module (untracked) |

### life-dashboard project

| File | Change |
|---|---|
| `app/static/babel.html` | New: unified Research page with Search/Mind Map/Highlights tabs |
| `app/routes/html_fragments.py` | Added mind-map, bookmark, search proxy, radar endpoints; removed YAKE from _extract_query; added same-book dedup and 0.45 threshold |
| `app/main.py` | Added /research route, /serendipity and /babel redirects |
| `app/static/journal.html` | Added "Find in Library" button on journal entries with inline results and book reader |
| `app/static/serendipity.html` | Updated nav links to Research; improved semantic search (removed YAKE); added inline book reader |

---

## 8. Architecture Changes

```
BEFORE:
  Query -> Ollama (nomic-embed-text-v2-moe, local) -> pgvector -> results
  Upload -> Ollama embed -> chunk_embeddings

AFTER:
  Query -> Gemini API (cloud, gemini-embedding-001) -> pgvector -> results
    Fallback: if Gemini < limit results, also query nomic-v2-moe via local Ollama
  Upload -> Gemini API embed (fallback: Ollama) -> chunk_embeddings
```

Key dependency: `GEMINIAPI_KEY` environment variable required. Set in:
- `/Users/weixiangzhang/Local_Dev/projects/LibraryOfBabel/.env`
- Passed through `docker-compose.yml` as `GEMINIAPI_KEY=${GEMINIAPI_KEY}`

---

## 9. Remaining Work

- **Re-embed completion**: The gemini_reembed_all.py daemon is still running. Full 2.4M chunks estimated at ~19 hours. Check progress: `cat /Users/weixiangzhang/Local_Dev/projects/LibraryOfBabel/logs/gemini_reembed_state.json`
- **Docker rebuild**: After re-embed completes, rebuild the Docker container to pick up all code changes. Run `./production_api_service.sh restart`.
- **Production deployment**: Update production API at api.ashortstayinhell.com:5562 with Gemini changes. Ensure GEMINIAPI_KEY is in the production .env.
- **Theme Explorer** (planned): Cluster highlights by semantic similarity, show theme groups on the Research page.
- **Reading Radar** (planned): Recommend next books based on recent journal/highlight/audiomark interests. Backend endpoint exists at `/api/babel/radar` but no frontend tab yet.
- **Remove legacy embedding models**: Once Gemini re-embed is 100% complete, consider dropping nomic-v2-moe and bge-m3 embeddings to save disk space. The fallback logic in nomic_intelligent_search.py can be simplified.
- **MCP server update**: The babel-mcp-server container may need a rebuild to pick up any API changes.

---

## 10. How to Resume

1. Check re-embed progress:
   ```bash
   cat /Users/weixiangzhang/Local_Dev/projects/LibraryOfBabel/logs/gemini_reembed_state.json
   screen -r gemini_reembed
   ```

2. If re-embed is done, rebuild production:
   ```bash
   cd /Users/weixiangzhang/Local_Dev/projects/LibraryOfBabel
   ./production_api_service.sh restart
   ```

3. Verify search works on both models:
   ```bash
   curl "http://localhost:5564/api/search?q=consciousness+and+free+will&action=semantic_passages&limit=5"
   ```

4. Key config files to check:
   - `/Users/weixiangzhang/Local_Dev/projects/LibraryOfBabel/.env` (GEMINIAPI_KEY)
   - `/Users/weixiangzhang/Local_Dev/projects/LibraryOfBabel/config/api_settings.json` (model config)
   - `/Users/weixiangzhang/Local_Dev/projects/LibraryOfBabel/docker-compose.yml` (env passthrough)
