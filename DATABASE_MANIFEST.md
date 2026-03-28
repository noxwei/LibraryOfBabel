# LibraryOfBabel — Database SQL Manifest

Generated: 2026-03-26
Database: `knowledge_base` (PostgreSQL + pgvector)
Migration system: **Flyway** (`flyway/sql/`)

---

## Deployment Order (Fresh Install)

Run these in order on a **new/empty** database only.

```
1. flyway/sql/V001__Initial_schema.sql        -- Core tables: authors, books, chunks, chunk_embeddings
2. flyway/sql/V002__Core_api_functions.sql    -- Core API stored functions
3. flyway/sql/V003__Selective_cleanup.sql     -- Data hygiene (sentence chunks removal)
4. flyway/sql/V004__Schema_separation.sql     -- Move functions into api/pipeline/vectors schemas
5. flyway/sql/V005__Move_functions.sql        -- Final function placement
6. flyway/sql/V006__Production_function_backup.sql  -- Backup function snapshots
```

**Do NOT run** `database/schema/schema.sql` against production — it contains DROP TABLE CASCADE and is guarded.

---

## Flyway Rollback Migrations

These are emergency rollbacks, executed by Flyway only — never run manually.

```
flyway/sql/U001__Rollback_initial_schema.sql    -- Drops authors, books, chunks
flyway/sql/U002__Rollback_core_api_functions.sql -- Drops chunk_embeddings, API functions
flyway/sql/U003__Rollback_selective_cleanup.sql  -- Reverses cleanup
flyway/sql/U004__Rollback_schema_separation.sql  -- Drops api/pipeline/vectors schemas
flyway/sql/U005__Rollback_move_functions.sql     -- Reverses function moves
flyway/sql/U006__Rollback_production_backup.sql  -- Drops function_backups schema
```

---

## Schema Initialization (Dev/Test Only)

| File | Purpose | DANGER |
|------|---------|--------|
| `database/schema/schema.sql` | Full schema reset for dev/test DBs | **DROP TABLE CASCADE** — blocked on `knowledge_base` by safety guard |

---

## Post-Schema SQL (Apply After Migrations)

These files add features on top of the migrated schema. They are idempotent (`CREATE OR REPLACE`, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`).

### Stored Procedures (apply in this order)
```
database/stored_procedures/api_core_procedures.sql            -- System health, basic search
database/stored_procedures/book_content_processing.sql        -- Book ingestion logic
database/stored_procedures/automated_ebook_ingestion_functions.sql  -- EPUB pipeline
database/stored_procedures/semantic_phrase_functions.sql       -- Phrase-level search
database/stored_procedures/extended_semantic_phrase_functions.sql   -- Extended phrase search
database/stored_procedures/extended_semantic_functions.sql     -- Semantic search (base)
database/stored_procedures/extended_semantic_functions_fixed.sql    -- Fixed version (use this)
database/stored_procedures/extended_semantic_final.sql         -- Final semantic bundle
database/stored_procedures/semantic_api_enhancement_functions.sql   -- API enhancements
database/stored_procedures/dr_elena_content_validation_functions.sql    -- Content validation
database/stored_procedures/dr_elena_description_enhancement_functions.sql -- Description AI
database/stored_procedures/dr_marcus_calibre_sync_functions.sql      -- Calibre sync
database/stored_procedures/dr_sarah_chen_robust_calibre_linkage_functions.sql -- Calibre fuzzy match
```

### Calibre Integration Schema
```
database/dr_sarah_chen_calibre_linkage_schema.sql        -- Calibre tables + indexes
database/dr_sarah_chen_calibre_metadata_architecture.sql -- metadata JSONB column on books
database/dr_sarah_chen_robust_calibre_linkage.sql        -- Fuzzy match helper functions
```

### Vector / pgvector Indexes (HNSW)
```
database/optimization/vector_indexing_optimization.sql   -- Add vector columns + HNSW indexes
database/optimization/vector_performance_optimization.sql -- Tuning (work_mem, parallel)
database/optimization/vector_optimization_fixed.sql      -- Fixed HNSW creation (use this)
```

### Search Optimization
```
database/optimization/10word_semantic_indexing_strategy.sql  -- 10-word phrase indexes
database/optimization/semantic_fallback_mechanisms.sql        -- 3-tier fallback search
database/optimization/cross_reference_optimization.sql        -- Cross-book references
database/optimization/quote_search_optimization.sql           -- Quote search tuning
database/schema/search_optimization.sql                       -- FTS tuning
database/schema/fix_hybrid_search.sql                         -- Hybrid search fix
```

### Other Schema Extensions
```
database/schema/create_readonly_user.sql              -- readonly role (run once)
database/schema/multi_model_routing_schema.sql        -- Multi-model routing tables
database/schema/hybrid_knowledge_graph_schema.sql     -- Knowledge graph tables
database/schema/agent_social_media_schema.sql         -- Agent social media tables
database/schema/download_pipeline.sql                 -- Download tracking
database/schema/hr_schema.sql                         -- HR tables (unused?)
database/schema/phase1_postgresql_functions.sql       -- Phase 1 functions (superseded)
database/schema/phase1_postgresql_functions_fixed.sql -- Fixed version
database/functions/intelligent_routing_functions.sql  -- Routing functions
```

### Misc Column Additions
```
database/add_md5_hash_column.sql   -- md5_hash column on books (deduplication)
```

---

## Utility / One-Time Scripts

These were run manually for specific operations. **Not repeatable without side effects.**

| File | What it did | Safe to re-run? |
|------|-------------|-----------------|
| `scripts/nuclear_data_migration.sql` | Copies books+chunks to `knowledge_base_clean` via dblink | No — use on empty target only |
| `scripts/nuclear_migration_fixed.sql` | Fixed version of above (correct column mapping) | No |
| `scripts/direct_clean_db.sql` | CSV copy of embedded books to `knowledge_with_embeds` | No |
| `sql/emergency_embedding_migration.sql` | Migrates embeddings to native vector columns | No — already applied |
| `sql/safe_batch_migration.sql` | Batched embedding migration | No — already applied |
| `sql/lightning_fast_migration.sql` | Fast bulk migration | No — already applied |
| `metadata_cleanup.sql` | Cleaned up book metadata fields | One-time |
| `metadata_cleanup_refined.sql` | Refined cleanup pass | One-time |
| `scripts/batch_sentence_removal.sql` | Removed sentence-type chunks | One-time |
| `scripts/batched_sentence_removal.sql` | Batched version of above | One-time |
| `scripts/phonetic_optimization_phase1.sql` | Phonetic search indexes | One-time |
| `scripts/enhanced_phonetic_search_function.sql` | Phonetic function updates | Idempotent (CREATE OR REPLACE) |
| `scripts/foucauldian_queer_enhancement.sql` | Thematic tag enhancement | One-time |
| `scripts/rhizomatic_enhancement.sql` | Thematic tag enhancement | One-time |

---

## Test / Verification Scripts

Not for deployment — query-only verification.

```
temp_cleanup/test_scripts/test_all_stored_procedures.sql
temp_cleanup/test_scripts/test_sql_procedures.sql
temp_cleanup/test_scripts/test_sql_procedures_fast.sql
scripts/quick_sql_test.sql
scripts/quick_test_verification.sql
scripts/simple_optimization_report.sql
scripts/phonetic_performance_report.sql
inspector.sql
```

---

## Archive (Do Not Use)

Superseded files, kept for reference only:

```
archive/scripts_old_20250730/        -- Old phonetic/vector scripts from pre-Aug 2025
archive/2025_Q3_august_cleanup/      -- Development SQL from Aug 2025 cleanup
temp_cleanup/sql_temp/               -- Temp scripts from shortcut function work
sql/archive_redundant_functions.sql  -- Archived redundant functions
```

---

## Dangerous Statement Inventory

| File | Statement | Context | Safe? |
|------|-----------|---------|-------|
| `database/schema/schema.sql:27-29` | `DROP TABLE IF EXISTS chunks/authors/books CASCADE` | Fresh install only | **Guarded** — blocked on `knowledge_base` by DO block |
| `flyway/sql/U001__Rollback_initial_schema.sql:18-20` | `DROP TABLE IF EXISTS chunks/books/authors CASCADE` | Flyway rollback only | OK — Flyway-controlled |
| `flyway/sql/U002__Rollback_core_api_functions.sql:15` | `DROP TABLE IF EXISTS chunk_embeddings CASCADE` | Flyway rollback only | OK — Flyway-controlled |
| `flyway/sql/U004__Rollback_schema_separation.sql:79-81` | `DROP SCHEMA IF EXISTS api/pipeline/vectors CASCADE` | Flyway rollback only | OK — Flyway-controlled |
| `flyway/sql/U006__Rollback_production_backup.sql:14` | `DROP SCHEMA IF EXISTS function_backups CASCADE` | Flyway rollback only | OK — Flyway-controlled |
| `sql/specialized_embedding_functions.sql:461` | `DROP TABLE IF EXISTS temp_multi_search_results` | Inside function body, temp table | OK — temp only |
| `sql/emergency_embedding_migration.sql:32` | `DROP TABLE IF EXISTS emergency_chunks_embedding_backup` | Inside function, backup table | OK — backup table |

**No bare DROP TABLE on production-scope tables outside of controlled contexts.**

---

## SQL File Count Summary

| Directory | File Count | Type |
|-----------|-----------|------|
| `flyway/sql/` | 12 | Versioned migrations + rollbacks |
| `database/schema/` | 12 | Schema definitions |
| `database/stored_procedures/` | 13 | Stored procedures |
| `database/optimization/` | 7 | Indexes and tuning |
| `database/functions/` | 1 | Routing functions |
| `database/` (root) | 5 | Calibre integration |
| `scripts/` | 18 | One-time / utility |
| `sql/` | ~20 | Migration and search functions |
| `temp_cleanup/` | 9 | Temp scripts |
| `archive/` | 10 | Superseded |
| **Total** | **~107** | |

---

## Flyway Status

Config: `flyway/conf/flyway.conf`

```
flyway.validateOnMigrate=true   ✓
flyway.cleanDisabled=true       ✓  (prevents accidental DROP SCHEMA PUBLIC)
flyway.baselineOnMigrate=true   ✓
```

To check migration status:
```bash
flyway -configFiles=flyway/conf/flyway.conf info
```

To apply pending migrations:
```bash
flyway -configFiles=flyway/conf/flyway.conf migrate
```
