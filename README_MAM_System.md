# 📚 MAM Audiobook-to-Ebook Automation System

**Transform your 1860+ audiobook collection into searchable ebooks for LibraryOfBabel RAG integration**

## 🎯 Overview

This system automates the process of finding and downloading ebook versions of your audiobooks from MyAnonamouse (MAM), respecting rate limits and providing comprehensive tracking.

### ✨ Key Features

- **📊 Collection Tracking**: Track which of your 1860 audiobooks have ebook versions
- **🤖 Automated Search**: Playwright-powered MAM search automation
- **📈 Web Dashboard**: Beautiful interface to monitor progress
- **⚡ Rate Limiting**: Respects MAM's 100 requests/day limit
- **🔄 Progress Tracking**: Never lose track of what's been searched/downloaded
- **📱 Real-time Updates**: Live statistics and status monitoring

## 📊 Current Status

```
📚 Total Audiobooks: 1,607 (from Plex database)
🔍 Ebooks Found: 0 (ready to search!)
📥 Downloaded: 0
🎯 Coverage: 0% → Target: 80%+
```

## 🚀 Quick Start

### 1. Setup System
```bash
# Run the automated setup
python3 setup_mam_system.py

# Or manual setup:
npm install
python3 audiobook_ebook_tracker.py
```

### 2. Configure MAM Credentials
Edit `.env` file:
```bash
# MAM Credentials (choose one method)
MAM_USERNAME=your_username
MAM_PASSWORD=your_password
# OR
MAM_SESSION_COOKIE=your_session_cookie

# Paths
PLEX_DB_PATH=/Users/weixiangzhang/Local\ Dev/audiobook-metadata-extractor/library_1750488304.db
DOWNLOAD_DIR=./mam_downloads
DB_PATH=./audiobook_ebook_tracker.db

# Limits
MAX_DAILY_DOWNLOADS=95
HEADLESS=false
```

### 3. Start Web Dashboard
```bash
node web_frontend.js
# Open: http://localhost:3000
```

### 4. Run Automated Search
```bash
# Search for 20 books
node mam_playwright_automation.js 20

# Search with different limits
node mam_playwright_automation.js 50
```

## 🗂️ File Structure

```
LibraryOfBabel/
├── 📊 audiobook_ebook_tracker.py     # Database management
├── 🤖 mam_playwright_automation.js   # Automated MAM search/download
├── 🌐 web_frontend.js                # Web dashboard
├── ⚙️ setup_mam_system.py            # Automated setup
├── 📄 .env                           # Configuration
├── 🗄️ audiobook_ebook_tracker.db     # SQLite database
└── 📁 mam_downloads/                 # Downloaded torrents
```

## 📊 Database Schema

### `audiobooks` table
- **album_id**: Unique identifier from Plex
- **title/author**: Book metadata
- **clean_title/clean_author**: Processed for searching
- **duration_hours**: Audiobook length
- **file_size_mb**: Storage requirements

### `ebooks` table
- **audiobook_id**: Links to audiobooks table
- **mam_torrent_id**: MAM torrent identifier
- **match_confidence**: AI-calculated match quality (0-1)
- **download_status**: available/downloading/completed/failed
- **seeders/leechers**: Torrent health

### `search_attempts` table
- **audiobook_id**: Which book was searched
- **search_query**: What query was used
- **results_found**: Number of results returned
- **search_date**: When search occurred

## 🎮 Web Dashboard Features

### 📈 Statistics Overview
- **Total Collection Size**: 1,607 audiobooks
- **Coverage Percentage**: Visual progress bar
- **Search Progress**: Books searched vs remaining
- **Download Status**: Available vs downloaded

### 📚 Book Lists
- **Missing Ebooks**: Audiobooks without ebook matches
- **Matched Books**: Found ebooks with confidence scores
- **Download Queue**: Pending downloads
- **Recent Searches**: Last search attempts

### 🔄 Actions
- **Refresh Data**: Update all statistics
- **Start Search**: Begin automated MAM searching
- **Export Missing**: CSV download of books needing ebooks

## 🤖 Playwright Automation Features

### 🔍 Smart Search
- **Title Cleaning**: Removes "(Unabridged)", "[Audiobook]" artifacts
- **Author Processing**: Handles narrator information
- **Fuzzy Matching**: Handles variations in titles/authors
- **Confidence Scoring**: Rates match quality (0-100%)

### 📥 Download Management
- **Session Persistence**: Saves login sessions
- **Rate Limiting**: Respects 95 requests/day limit
- **Progress Tracking**: Logs all attempts
- **Error Recovery**: Retries failed downloads

### 🎯 Quality Filters
- **Minimum Seeders**: Ensures healthy torrents
- **File Size Validation**: Avoids oversized/undersized files
- **Format Preference**: Prioritizes EPUB over other formats
- **Confidence Threshold**: Only downloads high-confidence matches

## 📊 Usage Examples

### Check Collection Status
```bash
python3 audiobook_ebook_tracker.py
```
Output:
```
=== Collection Statistics ===
Total Audiobooks: 1607
Audiobooks with Ebooks: 0
Audiobooks without Ebooks: 1607
Coverage: 0.0%
```

### Run Automated Search (Limited)
```bash
# Search 10 books for testing
node mam_playwright_automation.js 10
```

### Run Full Daily Batch
```bash
# Use full daily quota (95 searches)
node mam_playwright_automation.js 95
```

### Monitor via Web Interface
```bash
# Start dashboard
node web_frontend.js

# View real-time progress at:
# http://localhost:3000
```

## 📈 Expected Results

### Daily Progress (95 searches/day)
- **Week 1**: ~665 searches (40% of collection)
- **Week 2**: ~1330 searches (80% of collection) 
- **Week 3**: Complete initial sweep

### Match Rate Estimates
- **High Confidence (>0.8)**: ~60% of books
- **Medium Confidence (0.6-0.8)**: ~25% of books
- **Low/No Matches**: ~15% of books

### Download Expectations
With good matches and healthy torrents:
- **Daily Downloads**: 50-70 ebooks
- **Total Time**: 3-4 weeks for 80%+ coverage
- **Final Collection**: 1200+ ebook/audiobook pairs

## 🔧 Configuration Options

### Search Behavior
```javascript
// In mam_playwright_automation.js
const config = {
    headless: false,          // Show browser for debugging
    slowMo: 1000,            // Slow down automation
    timeout: 30000,          // Request timeout
    maxDailyDownloads: 95,   // Rate limit
    confidenceThreshold: 0.6  // Minimum match quality
};
```

### Database Optimization
```python
# In audiobook_ebook_tracker.py
# Indexes automatically created for:
# - Title/author searches
# - Status filtering  
# - Download tracking
```

## 🛡️ Rate Limiting & Ethics

### MAM Rate Limits
- **API Requests**: 100/day maximum
- **Buffer**: Use 95/day for safety
- **Tracking**: Automatic request counting
- **Reset**: Daily limit resets at midnight UTC

### Best Practices
- **Respect Limits**: Never exceed daily quotas
- **Good Ratio**: Maintain proper seed ratios
- **Personal Use**: Only for your own collection
- **Session Security**: Keep login credentials secure

## 🐛 Troubleshooting

### Common Issues

#### "Rate limit reached"
```bash
# Check remaining requests
node -e "
const fs = require('fs');
const log = JSON.parse(fs.readFileSync('mam_request_log.json', 'utf8'));
const today = new Date().toISOString().split('T')[0];
const todayReqs = log.filter(r => r.date === today);
console.log('Requests today:', todayReqs.length, '/ 95');
"
```

#### "Login failed"
- Check MAM credentials in `.env`
- Verify session cookie is current
- Try manual login first

#### "Database locked"
- Close all connections to SQLite database
- Restart web frontend
- Check for zombie processes

#### "No results found"
- Check MAM site status
- Verify search categories (E-Books = 14)
- Try manual search for same book

### Debug Mode
```bash
# Run with debug logging
DEBUG=true node mam_playwright_automation.js 5

# Show browser during automation
HEADLESS=false node mam_playwright_automation.js 5
```

## 📊 Performance Monitoring

### Key Metrics
- **Search Success Rate**: >90% expected
- **Match Confidence**: Average >0.7
- **Download Success**: >95% for healthy torrents
- **Processing Speed**: ~2-3 seconds per search

### Optimization Tips
- **Batch Processing**: Use full daily quotas
- **Peak Hours**: Avoid MAM maintenance times
- **Connection**: Stable internet required
- **Storage**: Ensure adequate disk space

## 🎯 Integration with LibraryOfBabel

Once ebooks are downloaded:

### 1. Extract Text Content
```bash
# Convert ebooks to text for RAG system
python3 process_ebooks_for_rag.py
```

### 2. Build Vector Database
```bash
# Create embeddings for semantic search
python3 build_vector_database.py
```

### 3. Enable AI Queries
```bash
# Query across 1000+ books
python3 query_library.py "What does Foucault say about surveillance capitalism?"
```

## 🎉 Success Metrics

### Target Goals
- **80% Coverage**: 1,285+ audiobooks with ebook matches
- **1,200+ Downloads**: High-quality ebook collection
- **<3 weeks**: Complete initial collection sweep
- **RAG Integration**: Searchable knowledge base operational

### Quality Indicators
- **High Match Confidence**: >70% matches above 0.8 confidence
- **Healthy Downloads**: >95% successful torrent downloads
- **Complete Metadata**: Full title/author/summary extraction
- **Search Efficiency**: <5% false positives

---

## 🚀 Ready to Start?

1. **Run Setup**: `python3 setup_mam_system.py`
2. **Configure MAM**: Edit `.env` with credentials
3. **Start Dashboard**: `node web_frontend.js`
4. **Begin Search**: `node mam_playwright_automation.js 20`

**Transform your audiobook collection into a searchable AI-powered library!** 📚🤖

---

*Built for LibraryOfBabel - Personal Knowledge Base Indexing System*