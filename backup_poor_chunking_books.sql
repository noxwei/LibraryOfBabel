-- Backup of 25 books with poor chunking (≤5 chunks)
-- Created: 2026-01-12

-- Books to delete
-- IDs: 3287,3288,3325,3607,3638,3727,3901,4127,4136,4204,4206,4377,4795,4887,4889,4893,4904,4906,4908,4920,4934,4936,4947,4956,5120

-- Count before deletion
SELECT COUNT(*) as total_books_before FROM books;

-- Backup book data
CREATE TEMP TABLE IF NOT EXISTS backup_poor_chunking AS
SELECT * FROM books
WHERE book_id IN (3287,3288,3325,3607,3638,3727,3901,4127,4136,4204,4206,4377,4795,4887,4889,4893,4904,4906,4908,4920,4934,4936,4947,4956,5120);

-- Show what we're deleting
SELECT book_id, title, author FROM backup_poor_chunking ORDER BY book_id;