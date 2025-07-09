# 🗄️ PostgreSQL CLI Guide for Library of Babel

## Quick Access Commands

### Connect to Database
```bash
# Connect to local PostgreSQL database
psql -h localhost -U postgres -d library_of_babel

# Or if using environment variables
export PGHOST=localhost
export PGUSER=postgres
export PGDATABASE=library_of_babel
psql
```

### SQLite Database (Linda's Tracking System)
```bash
# Connect to Linda's audiobook-ebook tracker
sqlite3 "/Users/weixiangzhang/Local Dev/LibraryOfBabel/database/data/audiobook_ebook_tracker.db"

# Quick table list
sqlite3 "/Users/weixiangzhang/Local Dev/LibraryOfBabel/database/data/audiobook_ebook_tracker.db" ".tables"
```

## 📚 Core Library Queries

### Books Table (Main PostgreSQL)
```sql
-- Total books in library
SELECT COUNT(*) FROM books;

-- Books by author
SELECT title, author, publication_year FROM books 
WHERE author ILIKE '%martin%' 
ORDER BY publication_year;

-- Recent additions
SELECT title, author, processed_date FROM books 
ORDER BY processed_date DESC 
LIMIT 20;

-- Books without chapters (processing issues)
SELECT b.title, b.author FROM books b
LEFT JOIN chunks c ON b.book_id = c.book_id
WHERE c.book_id IS NULL;

-- Search for specific topics
SELECT title, author FROM books 
WHERE title ILIKE '%history%' OR title ILIKE '%philosophy%';
```

### Chunks Table (Searchable Content)
```sql
-- Total searchable chunks
SELECT COUNT(*) FROM chunks;

-- Chunks per book
SELECT b.title, COUNT(c.chunk_id) as chunk_count
FROM books b
LEFT JOIN chunks c ON b.book_id = c.book_id
GROUP BY b.book_id, b.title
ORDER BY chunk_count DESC;

-- Find content by keyword
SELECT b.title, c.content 
FROM books b
JOIN chunks c ON b.book_id = c.book_id
WHERE c.content ILIKE '%keyword%'
LIMIT 10;
```

## 🔍 Linda's Audiobook-Ebook Tracker

### Available Ebooks
```sql
-- Total available ebooks
SELECT COUNT(*) FROM ebooks WHERE download_status = 'available';

-- Available by author
SELECT ebook_author, COUNT(*) as available_count
FROM ebooks 
WHERE download_status = 'available'
GROUP BY ebook_author
ORDER BY available_count DESC;

-- High-confidence matches
SELECT ebook_title, ebook_author, match_confidence, seeders
FROM ebooks 
WHERE download_status = 'available' 
AND match_confidence >= 0.8
ORDER BY seeders DESC;
```

### Missing Books Analysis
```sql
-- Audiobooks without ebooks
SELECT a.title, a.author, a.clean_title, a.clean_author
FROM audiobooks a
LEFT JOIN ebooks e ON a.album_id = e.audiobook_id
WHERE e.audiobook_id IS NULL
ORDER BY a.title
LIMIT 50;

-- Coverage statistics
SELECT 
    COUNT(*) as total_audiobooks,
    COUNT(DISTINCT e.audiobook_id) as audiobooks_with_ebooks,
    COUNT(*) - COUNT(DISTINCT e.audiobook_id) as audiobooks_without_ebooks,
    ROUND(COUNT(DISTINCT e.audiobook_id) * 100.0 / COUNT(*), 2) as coverage_percentage
FROM audiobooks a
LEFT JOIN ebooks e ON a.album_id = e.audiobook_id;
```

### Download Status
```sql
-- Download queue status
SELECT 
    dq.status,
    COUNT(*) as count
FROM download_queue dq
GROUP BY dq.status;

-- Recent downloads
SELECT e.ebook_title, e.ebook_author, e.download_date
FROM ebooks e
WHERE e.download_status = 'completed'
ORDER BY e.download_date DESC
LIMIT 20;
```

## 🛠️ Maintenance Commands

### Database Health Check
```sql
-- PostgreSQL: Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check for processing errors
SELECT title, author, word_count FROM books 
WHERE word_count < 1000 OR word_count IS NULL;
```

### Search Performance
```sql
-- Full-text search examples
SELECT title, author FROM books 
WHERE to_tsvector('english', title || ' ' || author) @@ to_tsquery('english', 'philosophy & history');

-- Chunk search
SELECT b.title, c.content 
FROM books b
JOIN chunks c ON b.book_id = c.book_id
WHERE to_tsvector('english', c.content) @@ to_tsquery('english', 'artificial & intelligence')
LIMIT 5;
```

## 📊 Analytics Queries

### Library Statistics
```sql
-- Books per year
SELECT publication_year, COUNT(*) as book_count
FROM books 
WHERE publication_year IS NOT NULL
GROUP BY publication_year
ORDER BY publication_year DESC;

-- Genre distribution (if available)
SELECT genre, COUNT(*) as count
FROM books 
WHERE genre IS NOT NULL
GROUP BY genre
ORDER BY count DESC;

-- Average book length
SELECT 
    AVG(word_count) as avg_words,
    MIN(word_count) as min_words,
    MAX(word_count) as max_words
FROM books
WHERE word_count > 0;
```

### Processing Status
```sql
-- Books processed today
SELECT COUNT(*) FROM books 
WHERE processed_date::date = CURRENT_DATE;

-- Processing success rate
SELECT 
    COUNT(*) as total_books,
    COUNT(CASE WHEN word_count > 0 THEN 1 END) as processed_successfully,
    ROUND(COUNT(CASE WHEN word_count > 0 THEN 1 END) * 100.0 / COUNT(*), 2) as success_rate
FROM books;
```

## 🔧 Useful CLI One-Liners

### Quick Checks
```bash
# Count total books
psql -d library_of_babel -c "SELECT COUNT(*) FROM books;"

# Find books by author
psql -d library_of_babel -c "SELECT title FROM books WHERE author ILIKE '%tolkien%';"

# Check available ebooks
sqlite3 "/Users/weixiangzhang/Local Dev/LibraryOfBabel/database/data/audiobook_ebook_tracker.db" "SELECT COUNT(*) FROM ebooks WHERE download_status = 'available';"

# Find missing books
sqlite3 "/Users/weixiangzhang/Local Dev/LibraryOfBabel/database/data/audiobook_ebook_tracker.db" "SELECT title FROM audiobooks a LEFT JOIN ebooks e ON a.album_id = e.audiobook_id WHERE e.audiobook_id IS NULL LIMIT 10;"
```

### Export Data
```bash
# Export book list to CSV
psql -d library_of_babel -c "COPY (SELECT title, author, publication_year FROM books ORDER BY author) TO STDOUT WITH CSV HEADER;" > books_export.csv

# Export available ebooks
sqlite3 -header -csv "/Users/weixiangzhang/Local Dev/LibraryOfBabel/database/data/audiobook_ebook_tracker.db" "SELECT ebook_title, ebook_author, seeders FROM ebooks WHERE download_status = 'available' ORDER BY seeders DESC;" > available_ebooks.csv
```

## 🚀 Advanced Queries

### Cross-Database Analysis
```sql
-- Find books in PostgreSQL that match available ebooks
-- (Run this in PostgreSQL)
SELECT b.title, b.author
FROM books b
WHERE EXISTS (
    SELECT 1 FROM ebooks e 
    WHERE e.ebook_title ILIKE '%' || b.title || '%'
    AND e.download_status = 'available'
);
```

### Content Analysis
```sql
-- Find books mentioning specific topics
SELECT DISTINCT b.title, b.author
FROM books b
JOIN chunks c ON b.book_id = c.book_id
WHERE c.content ILIKE '%artificial intelligence%'
   OR c.content ILIKE '%machine learning%'
   OR c.content ILIKE '%neural networks%';

-- Books with high chunk count (detailed processing)
SELECT b.title, b.author, COUNT(c.chunk_id) as chunks
FROM books b
JOIN chunks c ON b.book_id = c.book_id
GROUP BY b.book_id, b.title, b.author
HAVING COUNT(c.chunk_id) > 100
ORDER BY chunks DESC;
```

## 🎯 Quick Reference

### Table Relationships
```
PostgreSQL:
books (360 books) → chunks (10,514 chunks)

SQLite:
audiobooks (5,839) → ebooks (available/downloaded)
                  → search_attempts (search log)
                  → download_queue (download mgmt)
```

### Key Status Values
- **PostgreSQL books**: processed_date indicates successful processing
- **SQLite ebooks**: download_status = 'available'/'downloading'/'completed'/'failed'
- **Match confidence**: 0.0-1.0 (0.8+ recommended for downloads)

### Performance Tips
- Use ILIKE for case-insensitive searches
- Add LIMIT to large queries
- Use indexes on frequently searched columns
- Consider full-text search for content queries

---

## 🤖 Quick Commands Summary

```bash
# Connect to main library
psql -d library_of_babel

# Connect to Linda's tracker
sqlite3 "/Users/weixiangzhang/Local Dev/LibraryOfBabel/database/data/audiobook_ebook_tracker.db"

# Count everything
psql -d library_of_babel -c "SELECT COUNT(*) FROM books;"
sqlite3 "/Users/weixiangzhang/Local Dev/LibraryOfBabel/database/data/audiobook_ebook_tracker.db" "SELECT COUNT(*) FROM ebooks WHERE download_status = 'available';"

# Find missing books
sqlite3 "/Users/weixiangzhang/Local Dev/LibraryOfBabel/database/data/audiobook_ebook_tracker.db" "SELECT title FROM audiobooks a LEFT JOIN ebooks e ON a.album_id = e.audiobook_id WHERE e.audiobook_id IS NULL LIMIT 20;"
```

This guide provides comprehensive access to both the main PostgreSQL library and Linda's audiobook-ebook tracking system for complete library management.