-- Delete 856 problematic books (848 no chunks + 8 very short)
-- Created: 2026-01-12

BEGIN;

-- Read the book IDs from file
\set book_ids `cat books_to_delete_ids.txt`

-- Delete from dependent tables first
DELETE FROM chunk_embeddings
WHERE book_id IN (:book_ids);

DELETE FROM chunks
WHERE book_id IN (:book_ids);

DELETE FROM book_contents
WHERE book_id IN (:book_ids);

DELETE FROM book_content_analysis
WHERE book_id IN (:book_ids);

DELETE FROM book_intertextual_relationships
WHERE book_id_source IN (:book_ids)
   OR book_id_target IN (:book_ids);

DELETE FROM book_semantic_clusters
WHERE book_id IN (:book_ids);

DELETE FROM calibre_books
WHERE postgres_book_id IN (:book_ids);

DELETE FROM calibre_file_sync
WHERE book_id IN (:book_ids);

DELETE FROM calibre_metadata_conflicts
WHERE book_id IN (:book_ids);

DELETE FROM calibre_library_sync
WHERE book_id IN (:book_ids);

-- Finally delete the books themselves
DELETE FROM books
WHERE book_id IN (:book_ids);

COMMIT;