# 📊 MAM Audiobook-Ebook Tracker Database Schema

## Overview

The database tracks relationships between audiobooks (from Plex) and their corresponding ebooks (from MAM), including search attempts, download status, and queue management.

## 🗄️ Database Tables

### Core Tables

#### `audiobooks` - Master audiobook collection
```sql
CREATE TABLE audiobooks (
    album_id INTEGER PRIMARY KEY,          -- Unique identifier from Plex
    title TEXT NOT NULL,                   -- Original audiobook title
    author TEXT NOT NULL,                  -- Original author name
    release_date TEXT,                     -- Publication date
    summary TEXT,                          -- Book description/summary
    duration_hours REAL,                   -- Total audiobook length in hours
    file_path TEXT,                        -- Path to audiobook files
    file_size_mb REAL,                     -- Total file size in megabytes
    clean_title TEXT,                      -- Processed title for searching
    clean_author TEXT,                     -- Processed author for searching
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### `ebooks` - MAM ebook search results and downloads
```sql
CREATE TABLE ebooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audiobook_id INTEGER,                  -- Links to audiobooks.album_id
    mam_torrent_id TEXT UNIQUE,           -- MAM torrent identifier
    ebook_title TEXT NOT NULL,            -- Ebook title from MAM
    ebook_author TEXT NOT NULL,           -- Ebook author from MAM
    file_format TEXT,                     -- epub, pdf, mobi, etc.
    file_size_mb REAL,                    -- Ebook file size
    seeders INTEGER,                      -- Current seeders on MAM
    leechers INTEGER,                     -- Current leechers on MAM
    match_confidence REAL,                -- AI confidence score (0.0-1.0)
    discovered_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    download_status TEXT DEFAULT 'available', -- Status: available/downloading/completed/failed
    download_date DATETIME,               -- When download completed
    local_file_path TEXT,                 -- Path to downloaded ebook
    torrent_file_path TEXT,               -- Path to .torrent file
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (audiobook_id) REFERENCES audiobooks (album_id)
);
```

#### `search_attempts` - Log of all MAM searches
```sql
CREATE TABLE search_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audiobook_id INTEGER,                 -- Which audiobook was searched
    search_query TEXT,                    -- Query string used
    results_found INTEGER,               -- Number of results returned
    search_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    search_engine TEXT DEFAULT 'MAM',    -- Search source
    FOREIGN KEY (audiobook_id) REFERENCES audiobooks (album_id)
);
```

#### `download_queue` - Manage download priorities
```sql
CREATE TABLE download_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ebook_id INTEGER,                     -- Links to ebooks.id
    priority INTEGER DEFAULT 5,          -- Download priority (1=high, 10=low)
    added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_date DATETIME,               -- When download began
    completed_date DATETIME,             -- When download finished
    status TEXT DEFAULT 'queued',       -- queued/downloading/completed/failed
    error_message TEXT,                  -- Error details if failed
    retry_count INTEGER DEFAULT 0,      -- Number of retry attempts
    FOREIGN KEY (ebook_id) REFERENCES ebooks (id)
);
```

#### `collection_stats` - Cached statistics
```sql
CREATE TABLE collection_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    total_audiobooks INTEGER,
    audiobooks_with_ebooks INTEGER,
    audiobooks_without_ebooks INTEGER,
    total_ebooks_available INTEGER,
    total_ebooks_downloaded INTEGER,
    coverage_percentage REAL,
    last_calculated DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 🔗 Relationships Diagram

```
┌─────────────────┐
│   audiobooks    │
│  (5,839 books)  │
├─────────────────┤
│ album_id (PK)   │
│ title           │
│ author          │
│ clean_title     │
│ clean_author    │
│ duration_hours  │
│ file_size_mb    │
└─────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐    ┌─────────────────┐
│     ebooks      │    │ search_attempts │
│ (MAM results)   │    │  (search log)   │
├─────────────────┤    ├─────────────────┤
│ id (PK)         │    │ id (PK)         │
│ audiobook_id(FK)│◄──┤ audiobook_id(FK)│
│ mam_torrent_id  │    │ search_query    │
│ ebook_title     │    │ results_found   │
│ ebook_author    │    │ search_date     │
│ match_confidence│    └─────────────────┘
│ download_status │
│ local_file_path │
└─────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐
│ download_queue  │
│ (queue mgmt)    │
├─────────────────┤
│ id (PK)         │
│ ebook_id (FK)   │
│ priority        │
│ status          │
│ retry_count     │
└─────────────────┘
```

## 📈 Key Metrics & Queries

### Current Collection Status
```sql
-- Total audiobooks vs ebooks coverage
SELECT 
    COUNT(*) as total_audiobooks,
    COUNT(DISTINCT e.audiobook_id) as audiobooks_with_ebooks,
    COUNT(*) - COUNT(DISTINCT e.audiobook_id) as audiobooks_without_ebooks,
    ROUND(COUNT(DISTINCT e.audiobook_id) * 100.0 / COUNT(*), 2) as coverage_percentage
FROM audiobooks a
LEFT JOIN ebooks e ON a.album_id = e.audiobook_id;
```

### Download Success Rates
```sql
-- Download success by confidence threshold
SELECT 
    CASE 
        WHEN match_confidence >= 0.8 THEN 'High (80%+)'
        WHEN match_confidence >= 0.6 THEN 'Medium (60-80%)'
        ELSE 'Low (<60%)'
    END as confidence_level,
    COUNT(*) as total_matches,
    SUM(CASE WHEN download_status = 'completed' THEN 1 ELSE 0 END) as completed_downloads,
    ROUND(SUM(CASE WHEN download_status = 'completed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate
FROM ebooks
GROUP BY confidence_level
ORDER BY MIN(match_confidence) DESC;
```

### Search Efficiency
```sql
-- Search attempts vs results found
SELECT 
    AVG(results_found) as avg_results_per_search,
    COUNT(*) as total_searches,
    SUM(CASE WHEN results_found > 0 THEN 1 ELSE 0 END) as searches_with_results,
    ROUND(SUM(CASE WHEN results_found > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as search_success_rate
FROM search_attempts
WHERE search_date >= date('now', '-30 days');
```

## 🎯 Data Flow

### 1. Initial Import
```
Plex Database → audiobooks table (5,839 records)
```

### 2. Search Process
```
audiobooks → MAM API Search → ebooks table + search_attempts log
```

### 3. Download Process
```
ebooks → Torrent Download → Transmission → local_file_path update
```

### 4. Queue Management
```
ebooks → download_queue → batch processing → status updates
```

## 📊 Performance Indexes

```sql
-- Essential indexes for fast queries
CREATE INDEX idx_audiobooks_title ON audiobooks (clean_title);
CREATE INDEX idx_audiobooks_author ON audiobooks (clean_author);
CREATE INDEX idx_ebooks_audiobook ON ebooks (audiobook_id);
CREATE INDEX idx_ebooks_status ON ebooks (download_status);
CREATE INDEX idx_ebooks_confidence ON ebooks (match_confidence);
CREATE INDEX idx_search_attempts_audiobook ON search_attempts (audiobook_id);
CREATE INDEX idx_search_attempts_date ON search_attempts (search_date);
CREATE INDEX idx_download_queue_status ON download_queue (status);
CREATE INDEX idx_download_queue_priority ON download_queue (priority);
```

## 🔍 Common Queries for Claude Code

### Find audiobooks without ebooks
```sql
SELECT a.album_id, a.title, a.author, a.clean_title, a.clean_author
FROM audiobooks a
LEFT JOIN ebooks e ON a.album_id = e.audiobook_id
WHERE e.audiobook_id IS NULL
ORDER BY a.title
LIMIT 50;
```

### Get best ebook matches for audiobook
```sql
SELECT * FROM ebooks 
WHERE audiobook_id = ? 
ORDER BY match_confidence DESC, seeders DESC
LIMIT 5;
```

### Check recent search activity
```sql
SELECT sa.search_date, a.title, sa.search_query, sa.results_found
FROM search_attempts sa
JOIN audiobooks a ON sa.audiobook_id = a.album_id
WHERE sa.search_date >= date('now', '-1 day')
ORDER BY sa.search_date DESC;
```

### Download queue status
```sql
SELECT 
    dq.status,
    COUNT(*) as count,
    GROUP_CONCAT(a.title, '; ') as sample_titles
FROM download_queue dq
JOIN ebooks e ON dq.ebook_id = e.id
JOIN audiobooks a ON e.audiobook_id = a.album_id
GROUP BY dq.status;
```

## 🚨 Data Integrity Notes

1. **Unique Constraints**: `mam_torrent_id` must be unique to prevent duplicate downloads
2. **Foreign Keys**: All relationships use proper foreign key constraints
3. **Confidence Scores**: Always between 0.0 and 1.0
4. **Status Values**: 
   - `download_status`: 'available', 'downloading', 'completed', 'failed'
   - `queue status`: 'queued', 'downloading', 'completed', 'failed'
5. **Date Formats**: All dates stored as ISO 8601 strings for SQLite compatibility

## 🔄 Maintenance Queries

### Cleanup old search attempts (keep last 30 days)
```sql
DELETE FROM search_attempts 
WHERE search_date < date('now', '-30 days');
```

### Update statistics cache
```sql
INSERT INTO collection_stats (
    total_audiobooks, audiobooks_with_ebooks, audiobooks_without_ebooks,
    total_ebooks_available, total_ebooks_downloaded, coverage_percentage
)
SELECT 
    (SELECT COUNT(*) FROM audiobooks),
    (SELECT COUNT(DISTINCT audiobook_id) FROM ebooks),
    (SELECT COUNT(*) FROM audiobooks) - (SELECT COUNT(DISTINCT audiobook_id) FROM ebooks),
    (SELECT COUNT(*) FROM ebooks),
    (SELECT COUNT(*) FROM ebooks WHERE download_status = 'completed'),
    (SELECT COUNT(DISTINCT audiobook_id) FROM ebooks) * 100.0 / (SELECT COUNT(*) FROM audiobooks);
```

This schema supports the complete MAM audiobook-to-ebook automation workflow with proper relationships, performance optimization, and data integrity.