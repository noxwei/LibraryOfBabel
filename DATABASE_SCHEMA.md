# LibraryOfBabel — Database Schema Documentation

Generated: 2026-03-26
Database: `knowledge_base` (PostgreSQL + pgvector)

---

## Table Overview

```
authors  ──┐
           │ (FK: author_id)
books    ──┤
           │ (FK: book_id, ON DELETE CASCADE)
chunks   ──┤
           │ (FK: chunk_id)
chunk_embeddings
```

---

## Core Tables

### `authors`

Normalized author names to avoid duplication across books.

| Column | Type | Constraints |
|--------|------|-------------|
| `author_id` | SERIAL | PRIMARY KEY |
| `name` | VARCHAR(255) | NOT NULL |
| `created_at` | TIMESTAMP | DEFAULT NOW() |

**Indexes:**
- `idx_authors_name` — UNIQUE on `name`

---

### `books`

Book metadata. One row per imported book.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `book_id` | SERIAL | PRIMARY KEY | |
| `title` | VARCHAR(500) | NOT NULL | |
| `author` | VARCHAR(255) | | Denormalized author string |
| `author_id` | INTEGER | FK → `authors(author_id)` | Normalized FK (optional) |
| `publisher` | VARCHAR(255) | | |
| `publication_date` | VARCHAR(100) | | Raw string from source |
| `publication_year` | INTEGER | | Extracted year |
| `language` | VARCHAR(50) | DEFAULT 'english' | |
| `isbn` | VARCHAR(50) | | |
| `description` | TEXT | | |
| `genre` | VARCHAR(100) | | |
| `word_count` | INTEGER | DEFAULT 0 | Auto-updated by trigger |
| `file_path` | VARCHAR(1000) | | Original file location |
| `source_location` | VARCHAR(1000) | | |
| `import_source` | VARCHAR(100) | | e.g. 'calibre', 'epub' |
| `processed_date` | TIMESTAMP | DEFAULT NOW() | |
| `created_at` | TIMESTAMP | DEFAULT NOW() | |
| `metadata` | JSONB | DEFAULT '{}' | Calibre-sourced metadata |

**Indexes:**
- `idx_books_title` — GIN on `to_tsvector('english', title)` (full-text)
- `idx_books_author` — btree on `author`
- `idx_books_author_id` — btree on `author_id`
- `idx_books_publication_year` — btree on `publication_year`
- `idx_books_genre` — btree on `genre`
- `idx_books_word_count` — btree on `word_count`
- `idx_books_import_source` — btree on `import_source`
- `idx_books_processed_date` — btree on `processed_date`
- `idx_books_author_year` — composite on `(author, publication_year)`

**Triggers:**
- `trigger_update_book_word_count` — after INSERT/DELETE on chunks, recalculates `word_count` as sum of chapter chunk word counts

**Notes:**
- `book_id = 0` is a reserved system metadata row

---

### `chunks`

Text segments extracted from books. The main searchable content table.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `chunk_id` | VARCHAR(255) | PRIMARY KEY | |
| `book_id` | INTEGER | FK → `books(book_id)` ON DELETE CASCADE | |
| `chunk_type` | VARCHAR(50) | NOT NULL | `'chapter'`, `'section'`, `'paragraph'` |
| `title` | VARCHAR(500) | | Section/chapter title |
| `content` | TEXT | NOT NULL | Full text content |
| `word_count` | INTEGER | DEFAULT 0 | |
| `character_count` | INTEGER | DEFAULT 0 | |
| `chapter_number` | INTEGER | | |
| `section_number` | INTEGER | | |
| `paragraph_number` | INTEGER | | |
| `start_position` | INTEGER | DEFAULT 0 | Byte offset in source |
| `end_position` | INTEGER | DEFAULT 0 | |
| `parent_chunk_id` | VARCHAR(255) | | Hierarchical nesting |
| `search_vector` | TSVECTOR | | Auto-populated by trigger |
| `created_at` | TIMESTAMP | DEFAULT NOW() | |

**Indexes:**
- `idx_chunks_book_id` — btree on `book_id`
- `idx_chunks_type` — btree on `chunk_type`
- `idx_chunks_chapter` — btree on `chapter_number`
- `idx_chunks_word_count` — btree on `word_count`
- `idx_chunks_parent` — btree on `parent_chunk_id`
- `idx_chunks_search_vector` — GIN on `search_vector` (full-text search)
- `idx_chunks_content_search` — GIN on `to_tsvector('english', content)`
- `idx_chunks_book_type` — composite on `(book_id, chunk_type)`
- `idx_chunks_book_chapter` — composite on `(book_id, chapter_number)`

**Triggers:**
- `trigger_update_search_vector` — before INSERT/UPDATE, sets `search_vector = to_tsvector('english', title || ' ' || content)`

---

### `chunk_embeddings`

Vector embeddings for semantic search. One row per chunk (1:1 with chunks).

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `chunk_id` | VARCHAR(255) | PRIMARY KEY, FK → `chunks(chunk_id)` | |
| `embedding` | JSONB | | Legacy format (still populated) |
| `embedding_vector` | vector(1536) | | nomic-embed-text |
| `embedding_vector_bge` | vector(1024) | | bge-m3 |
| `embedding_vector_granite` | vector(384) | | granite-embedding:278m |
| `embedding_vector_mxbai` | vector(1024) | | mxbai-embed-large |
| `embedding_model` | VARCHAR(100) | | Primary model used |
| `created_at` | TIMESTAMP | DEFAULT NOW() | |

**pgvector HNSW Indexes (partial indexes by model):**

| Index | Column | Model filter | Algorithm | Distance |
|-------|--------|-------------|-----------|----------|
| `idx_embeddings_nomic_hnsw` | `embedding_vector` | `embedding_model = 'nomic-embed-text'` | HNSW | cosine |
| `idx_embeddings_bge_hnsw` | `embedding_vector_bge` | `embedding_model = 'bge-m3'` | HNSW | cosine |
| `idx_embeddings_granite_hnsw` | `embedding_vector_granite` | `embedding_model = 'granite-embedding:278m'` | HNSW | cosine |
| `idx_embeddings_mxbai_hnsw` | `embedding_vector_mxbai` | `embedding_model = 'mxbai-embed-large'` | HNSW | cosine |

All indexes created with `CONCURRENTLY IF NOT EXISTS`.

---

## Calibre Integration Tables

Added via `database/dr_sarah_chen_calibre_linkage_schema.sql`.

### `calibre_books`
Maps Calibre library entries to `books` table rows.
- `calibre_id`, `book_id` (FK), `calibre_title`, `calibre_authors`, `file_hash`, `sync_status`, `last_synced_at`

### `calibre_file_sync`
Tracks file sync state between Calibre library and the database.

### `calibre_metadata_conflicts`
Records conflicts when Calibre metadata differs from database metadata.

### `calibre_library_sync`
Overall sync run history (start/end time, books processed, errors).

---

## Views

### `v_book_stats`
Per-book statistics: total chunks, chapter/section/paragraph counts.

```sql
SELECT book_id, title, author, publication_year, word_count,
       total_chunks, chapter_chunks, section_chunks, paragraph_chunks
FROM v_book_stats;
```

### `v_search_ready`
Chunks with non-null `search_vector`, joined with book metadata — the fast path for FTS queries.

```sql
SELECT chunk_id, book_id, book_title, book_author, publication_year,
       chunk_type, chunk_title, content, word_count, chapter_number, search_vector
FROM v_search_ready;
```

---

## Key Relationships

```
authors (1) ──────── (N) books              via author_id
books   (1) ──────── (N) chunks             via book_id (CASCADE DELETE)
chunks  (1) ──────── (0..1) chunk_embeddings via chunk_id

books   (1) ──────── (0..1) calibre_books   via book_id
chunks  (N) ──────── (M) other chunks       via parent_chunk_id (self-ref hierarchy)
```

---

## Search Architecture (3-Tier Fallback)

Implemented in `database/optimization/semantic_fallback_mechanisms.sql`:

```
1. Native vector search   → Uses HNSW index (<=> operator), fastest
2. JSONB vector search    → Converts JSONB embedding on-the-fly, slower
3. FTS fallback           → Full-text search via search_vector, always works
```

Search functions expose unified interface; tier selection is automatic based on data availability.

---

## pgvector Configuration Notes

- Extension: `pgvector` (must be installed before `CREATE EXTENSION IF NOT EXISTS vector`)
- Recommended `postgresql.conf` settings:
  ```
  shared_buffers = 4GB
  effective_cache_size = 16GB
  maintenance_work_mem = 1GB      # Critical for HNSW index builds
  work_mem = 256MB
  random_page_cost = 1.1          # SSD-tuned
  effective_io_concurrency = 200
  ```
- For 247K+ chunks with 4 embedding models, HNSW beats IVFFlat for recall/speed tradeoff
- Partial indexes (filtered by `embedding_model`) keep each index tight and avoid null-vector penalty

---

## Database Users / Roles

Configured via `database/schema/create_readonly_user.sql`:

| Role | Access | Used by |
|------|--------|---------|
| `libraryofbabel_api_readonly` | SELECT only, `SET TRANSACTION READ ONLY` | Production API (Flask) |
| `libraryofbabel_admin` | Full access | Maintenance operations |
| `weixiangzhang` | Owner (superuser) | Local dev |

---

## Stored Procedure Namespacing

After V004 migration, functions are grouped into PostgreSQL schemas:

| Schema | Purpose | Example functions |
|--------|---------|-------------------|
| `api.*` | Public-facing API functions | `api_shortcuts_search_simple`, `api_semantic_ensemble_search` |
| `pipeline.*` | Ingestion pipeline functions | `api_process_epub_book`, `api_batch_embed_chunks` |
| `vectors.*` | Vector search functions | `fast_vector_similarity_search`, `jsonb_to_vector` |
| `public.*` | Legacy / catch-all | Older functions not yet migrated |

---

## Known Schema Hazards (Resolved)

| Issue | File | Status |
|-------|------|--------|
| `DROP TABLE IF EXISTS chunks/authors/books CASCADE` with no production guard | `database/schema/schema.sql:27-29` | **Fixed 2026-03-26** — wrapped in `DO $$ BEGIN IF current_database() IN ('knowledge_base') THEN RAISE EXCEPTION ... END IF; END $$` |
| No ordered deployment manifest | (none) | **Fixed 2026-03-26** — `DATABASE_MANIFEST.md` created |
| `function_name` interpolated in f-string in `database.py:194` | `src/api/modules/database.py` | **Not a real risk** — all call sites use hardcoded string literals, never user input |
