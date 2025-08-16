# Database Architecture: Production vs Data Pipeline Separation

## Current Problem
- 485 functions in one schema
- Production API mixed with data pipeline functions
- Potential performance impact from heavy batch processing

## Recommended Solution: Schema Separation

### Schema Structure
```
knowledge_base
├── public (core tables: books, authors, chunks)
├── api (production serving functions only)
├── pipeline (data processing functions)
└── vectors (pgVector extension functions)
```

### Benefits
✅ **Performance**: Production API isolated from heavy processing
✅ **Security**: Can restrict pipeline schema access
✅ **Maintenance**: Clear separation of concerns
✅ **Monitoring**: Easier to track which operations impact performance
✅ **Rollouts**: Deploy pipeline changes without affecting API

### Function Distribution

**api schema (31 functions)**
- `api_shortcuts_search_simple()`
- `api_v3_health()`
- `api_extended_semantic_search()`
- `api_shortcuts_dashboard()`
- All user-facing API endpoints

**pipeline schema (24 functions)**
- `api_ingest_complete_book()`
- `api_process_book_batch()`
- `generate_chunk_embeddings_batch()`
- `batch_classify_content()`
- All book processing functions

**vectors schema (102 functions)**
- `vector()`, `cosine_distance()`, etc.
- pgVector extension functions
- Shared by both API and pipeline

## Implementation Plan

### Phase 1: Create Schema Migration
```sql
-- V004__Schema_separation.sql
CREATE SCHEMA api;
CREATE SCHEMA pipeline;
CREATE SCHEMA vectors;
```

### Phase 2: Move Functions
- Production API → `api` schema
- Data processing → `pipeline` schema  
- Vector functions → `vectors` schema

### Phase 3: Update Applications
- API calls: `SELECT api.api_shortcuts_search_simple()`
- Pipeline: `SELECT pipeline.api_ingest_complete_book()`

### Phase 4: Permissions
```sql
-- Read-only API user
GRANT USAGE ON SCHEMA api TO api_readonly;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA api TO api_readonly;

-- Pipeline worker user
GRANT USAGE ON SCHEMA pipeline TO pipeline_worker;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA pipeline TO pipeline_worker;
```

## Alternative: Separate Database

If you prefer complete isolation:

```
knowledge_base          (production API)
knowledge_pipeline     (data processing)
```

**Pros**: Complete isolation, independent scaling
**Cons**: More complex, need data sync between DBs

## Recommendation

Start with **schema separation** - it's easier to implement and provides good separation while keeping everything in one database for your Mac Mini setup.