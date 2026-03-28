-- Backup of 19 books to be deleted (2 suspicious + 17 short works)
-- Created: 2026-01-12
-- Total books: 19

-- Book IDs to delete:
-- 1866, 2528, 796, 1245, 2530, 1246, 2689, 2569, 2080, 1666, 2549, 2557, 2546, 2525, 1952, 2388, 1187, 1258, 2499

-- Backup book information before deletion
SELECT book_id, title, author, genre, language, created_at
FROM books
WHERE book_id IN (1866, 2528, 796, 1245, 2530, 1246, 2689, 2569, 2080, 1666, 2549, 2557, 2546, 2525, 1952, 2388, 1187, 1258, 2499)
ORDER BY book_id;

-- Count related data before deletion
SELECT
    'books' as table_name, COUNT(*) as count
FROM books
WHERE book_id IN (1866, 2528, 796, 1245, 2530, 1246, 2689, 2569, 2080, 1666, 2549, 2557, 2546, 2525, 1952, 2388, 1187, 1258, 2499)
UNION ALL
SELECT
    'chunks', COUNT(*)
FROM chunks
WHERE book_id IN (1866, 2528, 796, 1245, 2530, 1246, 2689, 2569, 2080, 1666, 2549, 2557, 2546, 2525, 1952, 2388, 1187, 1258, 2499)
UNION ALL
SELECT
    'chunk_embeddings', COUNT(*)
FROM chunk_embeddings
WHERE book_id IN (1866, 2528, 796, 1245, 2530, 1246, 2689, 2569, 2080, 1666, 2549, 2557, 2546, 2525, 1952, 2388, 1187, 1258, 2499)
UNION ALL
SELECT
    'book_contents', COUNT(*)
FROM book_contents
WHERE book_id IN (1866, 2528, 796, 1245, 2530, 1246, 2689, 2569, 2080, 1666, 2549, 2557, 2546, 2525, 1952, 2388, 1187, 1258, 2499);