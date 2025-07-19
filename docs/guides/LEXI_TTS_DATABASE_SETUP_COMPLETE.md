# 🎭 Lexi TTS Database Setup - Complete Guide

## 📋 Summary for Dr. Sarah Chen → Lexi

Dr. Sarah Chen has successfully prepared the PostgreSQL database access for Lexi (Audio Synthesis Agent) to select fiction books for TTS testing. All tools have been tested and verified working.

## ✅ What's Ready for Lexi

### 🔌 Database Connection Verified
- **Database**: `knowledge_base` on localhost:5432
- **User**: `weixiangzhang`
- **Tables**: `books`, `chunks`, `authors` (all accessible)
- **Fiction Books Available**: 718 total, 672 suitable for TTS (40K+ words)

### 🛠️ Tools Created and Tested

#### 1. **Working Fiction Selector** (Recommended)
```bash
python3 scripts/lexi_working_fiction_selector.py
```
- ✅ **TESTED AND WORKING**
- Selects 15 diverse fiction books
- Provides TTS-specific metrics (estimated audio hours)
- Exports JSON report for pipeline integration
- Handles all edge cases reliably

#### 2. **Database Connection Tester**
```bash
python3 scripts/test_lexi_db_connection.py
```
- ✅ **TESTED AND WORKING**  
- Verifies database connectivity
- Tests fiction book availability
- Validates schema integrity

#### 3. **SQL Query Collection**
```sql
-- Use: scripts/lexi_fiction_queries.sql
SELECT book_id, title, author, genre, word_count 
FROM books 
WHERE genre ILIKE '%fiction%' 
AND word_count >= 40000
ORDER BY word_count DESC
LIMIT 15;
```
- ✅ **TESTED AND WORKING**
- Direct SQL queries for advanced users
- Multiple query variations for different needs

#### 4. **Comprehensive Documentation**
- `docs/guides/FICTION_SEARCH_GUIDE_FOR_LEXI.md` - Complete technical guide
- Database schema explanations
- Connection examples
- TTS-specific considerations

## 🎯 Current Selection Results

**Last Verified**: 2025-07-19 01:24

### 📊 Fiction Books Available for TTS
- **Total Fiction Books**: 718
- **TTS-Suitable (40K+ words)**: 672
- **Sample Selection**: 15 books ranging from 270K-595K words
- **Estimated Audio Content**: 353+ hours
- **Genres**: Science Fiction, Literary Fiction, Historical Fiction, Fantasy

### 📖 Sample Books Selected
1. **Dune Prequel** (594,902 words) - Epic Science Fiction
2. **The Tale of Genji** (451,603 words) - Historical Fiction  
3. **1Q84** (414,169 words) - Science Fiction
4. **Reamde** (400,674 words) - Science Fiction
5. **The Way of Kings** (383,327 words) - Fantasy
...and 10 more epic-length novels

## 🚀 How Lexi Can Use This

### Quick Start (2 minutes)
```bash
# 1. Test connection
python3 scripts/test_lexi_db_connection.py

# 2. Select fiction books  
python3 scripts/lexi_working_fiction_selector.py

# 3. Check output file
ls /tmp/lexi_fiction_selection_*.json
```

### Advanced Usage
```python
# Direct Python integration
import psycopg2
import psycopg2.extras

conn = psycopg2.connect(
    host='localhost',
    database='knowledge_base',
    user='weixiangzhang', 
    port=5432
)

# Get fiction books for TTS
cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
cursor.execute("""
    SELECT book_id, title, author, word_count
    FROM books 
    WHERE genre ILIKE '%fiction%' 
    AND word_count >= 40000
    LIMIT 15
""")
books = cursor.fetchall()
```

### Text Sample Extraction
```sql
-- Get text chunks for TTS testing
SELECT chunk_id, content, word_count, chapter_number
FROM chunks 
WHERE book_id = ? 
AND word_count BETWEEN 150 AND 400
ORDER BY chapter_number
LIMIT 5;
```

## 📞 Support and Troubleshooting

### Common Issues & Solutions

#### ❌ "Connection refused"
```bash
# Check PostgreSQL is running
brew services list | grep postgresql
# or
sudo systemctl status postgresql
```

#### ❌ "Permission denied"
```bash
# Check user exists and has permissions
psql -h localhost -U weixiangzhang -d knowledge_base -c "\l"
```

#### ❌ "No fiction books found"
```sql
-- Verify data exists
SELECT COUNT(*) FROM books WHERE genre ILIKE '%fiction%';
```

### Environment Variables (Optional)
```bash
export DB_HOST=localhost
export DB_NAME=knowledge_base  
export DB_USER=weixiangzhang
export DB_PORT=5432
```

## 🏛️ Database Architecture Notes

### Schema Overview
```
books (main metadata)
├── book_id (PRIMARY KEY)
├── title, author, genre  
├── word_count (for TTS estimation)
├── description, publication_year
└── processed_date

chunks (text segments)  
├── chunk_id (PRIMARY KEY)
├── book_id (FOREIGN KEY → books)
├── content (actual text for TTS)
├── word_count, chapter_number
└── chunk_type (chapter, section, paragraph)

authors (normalized data)
├── author_id (PRIMARY KEY) 
├── name
└── created_at
```

### Performance Optimizations
- **Indexes**: Genre, word_count, author, title (full-text search)
- **Functions**: `api_list_books()` for paginated results
- **Views**: Pre-computed statistics and search-ready data

## 🎤 TTS-Specific Recommendations

### Book Selection Strategy
1. **Start with Medium books** (100K-200K words, 3-8 hours audio)
2. **Test genre variety** (Literary, Sci-Fi, Fantasy, Historical)
3. **Use diverse authors** (different writing styles)
4. **Extract sample chunks** (opening, middle, climax sections)

### Audio Length Planning
- **Short (40K-80K words)**: 2-3 hours - Voice calibration
- **Medium (80K-150K words)**: 3-6 hours - Comprehensive testing
- **Long (150K-300K words)**: 6-12 hours - Endurance testing  
- **Epic (300K+ words)**: 12+ hours - Advanced stress testing

### Voice Considerations by Genre
- **Literary Fiction**: Complex vocabulary, varied sentence structure
- **Science Fiction**: Technical terms, futuristic concepts
- **Fantasy**: Creative names, magical terminology
- **Historical Fiction**: Period-appropriate language

## ✅ Final Verification Checklist

- [x] Database connection established
- [x] Fiction books accessible (718 available)
- [x] Working Python selector created and tested
- [x] SQL queries verified and documented
- [x] Sample selection completed (15 books, 353+ hours)
- [x] Export functionality working (JSON output)
- [x] Error handling implemented
- [x] Documentation complete
- [x] Troubleshooting guide provided

## 🎭 Ready for Lexi!

**Status**: ✅ **COMPLETE AND TESTED**

Lexi can now:
1. Connect to the LibraryOfBabel PostgreSQL database
2. Search and filter fiction books by various criteria
3. Select books optimized for TTS testing (word count, genre diversity)
4. Extract text samples for voice synthesis
5. Export selections for TTS pipeline integration

**Next Steps for Lexi**:
1. Run `python3 scripts/lexi_working_fiction_selector.py`
2. Use the exported JSON file for TTS pipeline
3. Extract text chunks using the provided SQL queries
4. Begin voice synthesis testing with the selected fiction books

---

**Prepared by**: Dr. Sarah Chen (Database Architecture Team)  
**For**: Lexi (Audio Synthesis Agent)  
**Date**: 2025-07-19  
**Database**: LibraryOfBabel PostgreSQL `knowledge_base`  
**Status**: Production Ready ✅