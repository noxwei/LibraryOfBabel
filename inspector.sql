-- =========================================================
-- LibraryOfBabel: one-shot schema + performance inspector
-- Usage (psql):  \i inspector.sql
-- Optional:      \set term 'The painter is standing a little back from his'
-- =========================================================

\echo '==[ Context ]========================================='
SELECT current_database() AS db, current_schema() AS schema, version();

\echo '==[ Extensions (should include pg_trgm, unaccent) ]==='
\dx

\echo '==[ Schemas ]========================================='
SELECT n.oid, n.nspname AS schema
FROM pg_namespace n
WHERE n.nspname NOT LIKE 'pg_%' AND n.nspname <> 'information_schema'
ORDER BY 2;

\echo '==[ Tables in current search_path ]==================='
SELECT schemaname, tablename, tableowner, hasindexes
FROM pg_tables
WHERE schemaname NOT LIKE 'pg_%' AND schemaname <> 'information_schema'
ORDER BY 1,2;

\echo '==[ Tables (chunks, books) — structure ]=============='
-- If these tables live in a different schema, run: SET search_path TO that_schema, public;
\d+ chunks
\d+ books

\echo '==[ Functions (search-related) ]======================'
-- List user-defined functions; narrow if needed
SELECT n.nspname AS schema, p.proname AS function, pg_get_function_identity_arguments(p.oid) AS args,
       pg_get_function_result(p.oid) AS result_type, l.lanname AS lang
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
JOIN pg_language l ON l.oid = p.prolang
WHERE n.nspname NOT IN ('pg_catalog','information_schema')
ORDER BY 1,2;

\echo '==[ fullbook_passage_search: signature & source ]====='
\df+ fullbook_passage_search
\sf+ fullbook_passage_search

\echo '==[ Row counts & size ]==============================='
WITH
all_chunks AS (SELECT count(*) c FROM chunks),
fullbook AS (SELECT count(*) c FROM chunks WHERE chunk_type = 'fullbook')
SELECT
  (SELECT c FROM all_chunks)     AS total_chunks,
  (SELECT c FROM fullbook)       AS fullbook_chunks,
  round((SELECT c FROM fullbook)::numeric * 100.0 / NULLIF((SELECT c FROM all_chunks),0), 2) AS fullbook_pct;

SELECT
  pg_size_pretty(pg_total_relation_size('chunks')) AS chunks_size,
  pg_size_pretty(pg_total_relation_size('books'))  AS books_size;

\echo '==[ Content stats for fullbook chunks ]==============='
SELECT
  count(*)                              AS rows,
  avg(length(content))::bigint          AS avg_len,
  percentile_cont(0.50) WITHIN GROUP (ORDER BY length(content))::bigint AS p50_len,
  max(length(content))                  AS max_len
FROM chunks
WHERE chunk_type = 'fullbook';

\echo '==[ Indexes on chunks ]==============================='
SELECT schemaname, tablename, indexname, indexdef
FROM pg_indexes
WHERE tablename='chunks'
ORDER BY 1,3;

\echo '==[ Recommended indexes (preview only) ]=============='
\echo '-- Enable once: CREATE EXTENSION IF NOT EXISTS pg_trgm;'
\echo '-- Enable once: CREATE EXTENSION IF NOT EXISTS unaccent;'
\echo '-- Partial GIN on lower(content) for fullbook only:'
\echo '/*'
\echo 'CREATE INDEX IF NOT EXISTS idx_chunks_fullbook_trgm'
\echo 'ON chunks USING gin (lower(content) gin_trgm_ops)'
\echo "WHERE chunk_type = 'fullbook';"
\echo ''
\echo '-- Optional normalized index to ignore accents/whitespace:'
\echo 'CREATE INDEX IF NOT EXISTS idx_chunks_fullbook_trgm_norm'
\echo "ON chunks USING gin ( (regexp_replace(unaccent(lower(content)), '\s+', ' ', 'g')) gin_trgm_ops )"
\echo "WHERE chunk_type = 'fullbook';"
\echo '*/'

\echo '==[ Test term ]======================================='
-- Set a test term if not provided by caller:
\ifndef term
  \set term 'The painter is standing a little back from his'
\endif
SELECT :'term' AS test_term;

\echo '==[ LIKE (baseline) — plan & timing ]================='
EXPLAIN (ANALYZE, BUFFERS, TIMING)
SELECT book_id, POSITION(lower(:'term') IN lower(content)) AS pos
FROM chunks
WHERE chunk_type = 'fullbook'
  AND lower(content) LIKE '%' || lower(:'term') || '%'
ORDER BY pos NULLS LAST
LIMIT 5;

\echo '==[ Normalized match — plan & timing ]================'
EXPLAIN (ANALYZE, BUFFERS, TIMING)
SELECT book_id,
       strpos(
         regexp_replace(unaccent(lower(content)), '\s+', ' ', 'g'),
         regexp_replace(unaccent(lower(:'term')),   '\s+', ' ', 'g')
       ) AS pos_norm
FROM chunks
WHERE chunk_type = 'fullbook'
  AND regexp_replace(unaccent(lower(content)), '\s+', ' ', 'g')
      LIKE '%' || regexp_replace(unaccent(lower(:'term')), '\s+', ' ', 'g') || '%'
ORDER BY pos_norm NULLS LAST
LIMIT 5;

\echo '==[ Snippet extraction (300|300) ]===================='
WITH hit AS (
  SELECT b.title, b.author,
         strpos(lower(c.content), lower(:'term')) AS pos,
         length(c.content) AS L,
         c.content
  FROM chunks c
  JOIN books  b ON b.book_id = c.book_id
  WHERE c.chunk_type = 'fullbook'
    AND lower(c.content) LIKE '%' || lower(:'term') || '%'
  ORDER BY 3
  LIMIT 1
)
SELECT
  title, author, pos,
  SUBSTRING(content FROM GREATEST(1, pos-300) FOR 600) AS context_600
FROM hit;

\echo '==[ Function call (if exists) ]======================='
-- If your function takes (query_text text), adapt schema if needed:
EXPLAIN (ANALYZE, BUFFERS, TIMING)
SELECT *
FROM fullbook_passage_search(:'term')
LIMIT 5;

\echo '==[ Multiple-hit sanity check (first 3 per book) ]===='
WITH matches AS (
  SELECT b.title, b.author,
         strpos(lower(c.content), lower(:'term')) AS pos,
         SUBSTRING(c.content FROM GREATEST(1, strpos(lower(c.content), lower(:'term'))-60) FOR 120) AS around
  FROM chunks c
  JOIN books  b ON b.book_id = c.book_id
  WHERE c.chunk_type = 'fullbook'
    AND lower(c.content) LIKE '%' || lower(:'term') || '%'
)
SELECT *
FROM (
  SELECT *, row_number() OVER (PARTITION BY title ORDER BY pos) AS rn
  FROM matches
) t
WHERE rn <= 3
ORDER BY title, pos;

\echo '==[ Done ]============================================'