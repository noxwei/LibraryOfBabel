/**
 * Web Frontend for Audiobook-Ebook Tracker
 * Shows collection status, download progress, and management interface
 */

const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs').promises;

class AudiobookEbookWebApp {
    constructor(config = {}) {
        this.config = {
            port: config.port || 3000,
            dbPath: config.dbPath || './audiobook_ebook_tracker.db',
            host: config.host || 'localhost',
            ...config
        };
        
        this.app = express();
        this.setupMiddleware();
        this.setupRoutes();
    }

    setupMiddleware() {
        this.app.use(express.json());
        this.app.use(express.urlencoded({ extended: true }));
        this.app.use(express.static('public'));
        
        // CORS for development
        this.app.use((req, res, next) => {
            res.header('Access-Control-Allow-Origin', '*');
            res.header('Access-Control-Allow-Headers', 'Content-Type');
            next();
        });
    }

    setupRoutes() {
        // Dashboard - main overview
        this.app.get('/', (req, res) => {
            res.send(this.getDashboardHTML());
        });

        // API: Collection statistics
        this.app.get('/api/stats', async (req, res) => {
            try {
                const stats = await this.getCollectionStats();
                res.json(stats);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });

        // API: Audiobooks without ebooks
        this.app.get('/api/audiobooks/missing', async (req, res) => {
            try {
                const limit = parseInt(req.query.limit) || 50;
                const missing = await this.getAudiobooksWithoutEbooks(limit);
                res.json(missing);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });

        // API: Audiobooks with ebooks
        this.app.get('/api/audiobooks/matched', async (req, res) => {
            try {
                const matched = await this.getAudiobooksWithEbooks();
                res.json(matched);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });

        // API: Recent search attempts
        this.app.get('/api/searches/recent', async (req, res) => {
            try {
                const searches = await this.getRecentSearches();
                res.json(searches);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });

        // API: Download queue status
        this.app.get('/api/downloads/queue', async (req, res) => {
            try {
                const queue = await this.getDownloadQueue();
                res.json(queue);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });

        // API: Search specific audiobook
        this.app.post('/api/search/:albumId', async (req, res) => {
            try {
                const albumId = req.params.albumId;
                const result = await this.searchSingleAudiobook(albumId);
                res.json(result);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });

        // API: Download torrent via RSS
        this.app.post('/api/download/:torrentId', async (req, res) => {
            try {
                const torrentId = req.params.torrentId;
                const result = await this.downloadTorrentRSS(torrentId);
                res.json(result);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });

        // API: Search and download audiobook
        this.app.post('/api/search-download/:albumId', async (req, res) => {
            try {
                const albumId = req.params.albumId;
                const searchResult = await this.searchSingleAudiobook(albumId);
                
                if (searchResult.success && searchResult.matches.length > 0) {
                    const bestMatch = searchResult.matches[0];
                    if (bestMatch.confidence > 0.6) {
                        const downloadResult = await this.downloadTorrentRSS(bestMatch.torrentId);
                        res.json({ 
                            search: searchResult, 
                            download: downloadResult,
                            message: 'Search and download completed'
                        });
                    } else {
                        res.json({ 
                            search: searchResult, 
                            message: 'Low confidence match, download skipped'
                        });
                    }
                } else {
                    res.json({ 
                        search: searchResult, 
                        message: 'No matches found'
                    });
                }
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });

        // API: Check transmission status for torrent
        this.app.get('/api/transmission/:torrentId', async (req, res) => {
            try {
                const torrentId = req.params.torrentId;
                const status = await this.checkTransmissionStatus(torrentId);
                res.json(status);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });

        // API: Batch search and download multiple audiobooks
        this.app.post('/api/batch-download', async (req, res) => {
            try {
                const { limit = 5 } = req.body;
                const result = await this.batchSearchAndDownload(limit);
                res.json(result);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });

        // API: Force refresh database from Plex
        this.app.post('/api/refresh', async (req, res) => {
            try {
                const result = await this.refreshFromPlex();
                res.json(result);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });
    }

    getDashboardHTML() {
        return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LibraryOfBabel - Audiobook/Ebook Tracker</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
            color: white;
        }
        
        .header h1 {
            font-size: 3rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .stat-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .stat-label {
            font-size: 0.9rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .coverage-bar {
            width: 100%;
            height: 10px;
            background: #e0e0e0;
            border-radius: 5px;
            overflow: hidden;
            margin: 15px 0;
        }
        
        .coverage-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 5px;
            transition: width 0.5s ease;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }
        
        .section {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .section h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.4rem;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        
        .book-list {
            max-height: 500px;
            overflow-y: auto;
        }
        
        .book-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            border-bottom: 1px solid #eee;
            transition: background 0.2s ease;
        }
        
        .book-item:hover {
            background: #f8f9fa;
        }
        
        .book-info {
            flex: 1;
        }
        
        .book-title {
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        
        .book-author {
            color: #666;
            font-size: 0.9rem;
        }
        
        .book-duration {
            color: #999;
            font-size: 0.8rem;
            margin-top: 3px;
        }
        
        .status-badge {
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .status-missing {
            background: #ffebee;
            color: #c62828;
        }
        
        .status-available {
            background: #e8f5e8;
            color: #2e7d32;
        }
        
        .status-downloaded {
            background: #e3f2fd;
            color: #1565c0;
        }
        
        .actions {
            margin-top: 30px;
            text-align: center;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 25px;
            cursor: pointer;
            margin: 0 10px;
            font-size: 1rem;
            transition: transform 0.2s ease;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }

        .btn-small {
            padding: 8px 16px;
            font-size: 0.9rem;
            margin: 0 5px;
        }

        .btn-search {
            background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
        }

        .btn-download {
            background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
        }

        .book-actions {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        /* Modal Styles */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }

        .modal-content {
            background-color: white;
            margin: 5% auto;
            padding: 30px;
            border-radius: 15px;
            width: 90%;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }

        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }

        .close:hover {
            color: #000;
        }

        .search-result {
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            transition: background 0.2s ease;
        }

        .search-result:hover {
            background: #f8f9fa;
        }

        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .result-title {
            font-weight: bold;
            color: #333;
            font-size: 1.1rem;
        }

        .result-confidence {
            background: #e3f2fd;
            color: #1565c0;
            padding: 4px 8px;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: bold;
        }

        .result-details {
            color: #666;
            margin: 5px 0;
        }

        .result-stats {
            display: flex;
            gap: 15px;
            margin: 10px 0;
            font-size: 0.9rem;
        }

        .stat-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .loading-inline {
            display: inline-block;
            margin-left: 10px;
            color: #666;
            font-style: italic;
        }
        
        .loading {
            text-align: center;
            color: #666;
            font-style: italic;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4caf50, #45a049);
            transition: width 0.3s ease;
        }
        
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .stats-grid {
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 LibraryOfBabel</h1>
            <p>Audiobook to Ebook Collection Tracker</p>
        </div>
        
        <div class="stats-grid" id="statsGrid">
            <!-- Stats will be loaded here -->
        </div>
        
        <div class="main-content">
            <div class="section">
                <h2>🚫 Missing Ebooks</h2>
                <div class="book-list" id="missingBooks">
                    <div class="loading">Loading audiobooks without ebooks...</div>
                </div>
            </div>
            
            <div class="section">
                <h2>✅ Matched Books</h2>
                <div class="book-list" id="matchedBooks">
                    <div class="loading">Loading matched audiobook-ebook pairs...</div>
                </div>
            </div>
        </div>
        
        <div class="actions">
            <button class="btn" onclick="refreshData()">🔄 Refresh Data</button>
            <button class="btn" onclick="exportMissing()">📄 Export Missing</button>
        </div>
        
        <!-- Giant Batch Download Section -->
        <div style="margin: 40px 0; text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 20px; color: white;">
            <h2 style="margin: 0 0 20px 0; font-size: 2rem;">🚀 Batch Download Center</h2>
            <p style="margin: 0 0 30px 0; font-size: 1.2rem; opacity: 0.9;">
                Automatically search MAM and download ebooks with Transmission integration
            </p>
            <button 
                id="batchDownloadBtn" 
                onclick="startBatchDownload()" 
                style="
                    background: #ffffff;
                    color: #667eea;
                    border: none;
                    padding: 20px 40px;
                    border-radius: 50px;
                    font-size: 1.4rem;
                    font-weight: bold;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    box-shadow: 0 8px 25px rgba(0,0,0,0.2);
                "
                onmouseover="this.style.transform='scale(1.05)'"
                onmouseout="this.style.transform='scale(1)'"
            >
                🎯 Start Batch Download (5 Books)
            </button>
            <div id="batchProgress" style="margin-top: 20px; display: none;">
                <div style="background: rgba(255,255,255,0.2); border-radius: 10px; padding: 15px;">
                    <div id="progressText">Initializing...</div>
                    <div style="background: rgba(255,255,255,0.3); height: 8px; border-radius: 4px; margin: 10px 0;">
                        <div id="progressBar" style="background: #4caf50; height: 100%; border-radius: 4px; width: 0%; transition: width 0.5s ease;"></div>
                    </div>
                    <div id="progressDetails" style="font-size: 0.9rem; opacity: 0.8;"></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Search Results Modal -->
    <div id="searchModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalTitle">Search Results</h2>
                <span class="close" onclick="closeModal()">&times;</span>
            </div>
            <div id="modalContent">
                <!-- Search results will be populated here -->
            </div>
        </div>
    </div>

    <script>
        let currentStats = {};
        
        // Load initial data
        document.addEventListener('DOMContentLoaded', function() {
            loadStats();
            loadMissingBooks();
            loadMatchedBooks();
            
            // Auto-refresh every 30 seconds
            setInterval(loadStats, 30000);
        });
        
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const stats = await response.json();
                currentStats = stats;
                renderStats(stats);
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }
        
        function renderStats(stats) {
            const statsGrid = document.getElementById('statsGrid');
            const coveragePercent = stats.coverage_percentage || 0;
            
            statsGrid.innerHTML = \`
                <div class="stat-card">
                    <div class="stat-number">\${stats.total_audiobooks || 0}</div>
                    <div class="stat-label">Total Audiobooks</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">\${stats.audiobooks_with_ebooks || 0}</div>
                    <div class="stat-label">With Ebooks</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">\${stats.audiobooks_without_ebooks || 0}</div>
                    <div class="stat-label">Missing Ebooks</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">\${stats.total_ebooks_downloaded || 0}</div>
                    <div class="stat-label">Downloaded</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">\${coveragePercent.toFixed(1)}%</div>
                    <div class="stat-label">Coverage</div>
                    <div class="coverage-bar">
                        <div class="coverage-fill" style="width: \${coveragePercent}%"></div>
                    </div>
                </div>
            \`;
        }
        
        async function loadMissingBooks() {
            try {
                const response = await fetch('/api/audiobooks/missing?limit=50');
                const books = await response.json();
                renderMissingBooks(books);
            } catch (error) {
                console.error('Error loading missing books:', error);
                document.getElementById('missingBooks').innerHTML = 
                    '<div class="loading">Error loading missing books</div>';
            }
        }
        
        function renderMissingBooks(books) {
            const container = document.getElementById('missingBooks');
            
            if (books.length === 0) {
                container.innerHTML = '<div class="loading">🎉 All audiobooks have ebook matches!</div>';
                return;
            }
            
            container.innerHTML = books.map(book => \`
                <div class="book-item" id="book-\${book.album_id}">
                    <div class="book-info">
                        <div class="book-title">\${book.title}</div>
                        <div class="book-author">by \${book.author}</div>
                        <div class="book-duration">\${book.duration_hours?.toFixed(1) || 0}h • \${(book.file_size_mb / 1024).toFixed(1) || 0}GB</div>
                    </div>
                    <div class="book-actions">
                        <button class="btn-small btn-search" onclick="searchAndDownload(\${book.album_id})" id="btn-\${book.album_id}">
                            🔍 Search & Download
                        </button>
                        <div class="status-badge status-missing">Missing</div>
                    </div>
                </div>
            \`).join('');
        }
        
        async function loadMatchedBooks() {
            try {
                const response = await fetch('/api/audiobooks/matched');
                const books = await response.json();
                renderMatchedBooks(books);
            } catch (error) {
                console.error('Error loading matched books:', error);
                document.getElementById('matchedBooks').innerHTML = 
                    '<div class="loading">Error loading matched books</div>';
            }
        }
        
        function renderMatchedBooks(books) {
            const container = document.getElementById('matchedBooks');
            
            if (books.length === 0) {
                container.innerHTML = '<div class="loading">No matches found yet</div>';
                return;
            }
            
            container.innerHTML = books.map(book => \`
                <div class="book-item">
                    <div class="book-info">
                        <div class="book-title">\${book.title}</div>
                        <div class="book-author">by \${book.author}</div>
                        <div class="book-duration">
                            \${book.duration_hours?.toFixed(1) || 0}h • 
                            Confidence: \${(book.match_confidence * 100).toFixed(0)}% • 
                            \${book.seeders} seeders
                        </div>
                    </div>
                    <div class="status-badge \${book.download_status === 'completed' ? 'status-downloaded' : 'status-available'}">
                        \${book.download_status === 'completed' ? 'Downloaded' : 'Available'}
                    </div>
                </div>
            \`).join('');
        }
        
        async function refreshData() {
            await Promise.all([
                loadStats(),
                loadMissingBooks(),
                loadMatchedBooks()
            ]);
        }
        
        async function startBatchDownload() {
            const btn = document.getElementById('batchDownloadBtn');
            const progress = document.getElementById('batchProgress');
            const progressText = document.getElementById('progressText');
            const progressBar = document.getElementById('progressBar');
            const progressDetails = document.getElementById('progressDetails');
            
            // Disable button and show progress
            btn.disabled = true;
            btn.innerHTML = '⏳ Processing...';
            progress.style.display = 'block';
            progressText.textContent = 'Starting batch download...';
            progressBar.style.width = '0%';
            progressDetails.textContent = 'Preparing to search and download 5 audiobooks';
            
            try {
                const response = await fetch('/api/batch-download', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ limit: 5 })
                });
                
                if (!response.ok) {
                    throw new Error('Batch download request failed');
                }
                
                const result = await response.json();
                
                // Update progress to 100%
                progressBar.style.width = '100%';
                progressText.textContent = `✅ Batch Download Complete!`;
                progressDetails.innerHTML = `
                    📊 Processed: ${result.processed} books<br>
                    ✅ Successful: ${result.successful} downloads<br>
                    ❌ Failed: ${result.failed} attempts<br>
                    ⏱️ Duration: ${Math.round(result.duration / 1000)}s
                `;
                
                // Show detailed results
                if (result.downloads.length > 0) {
                    const downloadList = result.downloads.map(d => 
                        `📚 ${d.audiobook} → 📖 ${d.ebook} (${Math.round(d.confidence * 100)}%)`
                    ).join('<br>');
                    progressDetails.innerHTML += '<br><br><strong>Downloaded:</strong><br>' + downloadList;
                }
                
                // Re-enable button after delay
                setTimeout(() => {
                    btn.disabled = false;
                    btn.innerHTML = '🎯 Start Batch Download (5 Books)';
                    progress.style.display = 'none';
                    
                    // Refresh the data to show new matches
                    refreshData();
                }, 5000);
                
            } catch (error) {
                progressBar.style.width = '100%';
                progressBar.style.background = '#f44336';
                progressText.textContent = '❌ Batch Download Failed';
                progressDetails.textContent = `Error: ${error.message}`;
                
                // Re-enable button
                setTimeout(() => {
                    btn.disabled = false;
                    btn.innerHTML = '🎯 Start Batch Download (5 Books)';
                    progress.style.display = 'none';
                }, 3000);
            }
        }
        
        async function exportMissing() {
            try {
                const response = await fetch('/api/audiobooks/missing?limit=9999');
                const books = await response.json();
                
                const csvContent = [
                    'Title,Author,Duration Hours,File Size MB,Clean Title,Clean Author',
                    ...books.map(book => \`
                        "\${book.title}","\${book.author}",\${book.duration_hours || 0},\${book.file_size_mb || 0},"\${book.clean_title}","\${book.clean_author}"
                    \`.trim())
                ].join('\\n');
                
                const blob = new Blob([csvContent], { type: 'text/csv' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'missing_ebooks.csv';
                a.click();
                window.URL.revokeObjectURL(url);
            } catch (error) {
                alert('Error exporting missing books: ' + error.message);
            }
        }
    </script>
</body>
</html>
        `;
    }

    async getCollectionStats() {
        return new Promise((resolve, reject) => {
            const db = new sqlite3.Database(this.config.dbPath);
            
            const queries = {
                totalAudiobooks: 'SELECT COUNT(*) as count FROM audiobooks',
                audiobooksWithEbooks: `
                    SELECT COUNT(DISTINCT a.album_id) as count 
                    FROM audiobooks a 
                    INNER JOIN ebooks e ON a.album_id = e.audiobook_id
                `,
                totalEbooksAvailable: 'SELECT COUNT(*) as count FROM ebooks',
                totalEbooksDownloaded: "SELECT COUNT(*) as count FROM ebooks WHERE download_status = 'completed'"
            };
            
            const results = {};
            let pending = Object.keys(queries).length;
            
            Object.entries(queries).forEach(([key, query]) => {
                db.get(query, (err, row) => {
                    if (err) {
                        reject(err);
                        return;
                    }
                    
                    results[key] = row.count;
                    pending--;
                    
                    if (pending === 0) {
                        const total = results.totalAudiobooks;
                        const withEbooks = results.audiobooksWithEbooks;
                        const coverage = total > 0 ? (withEbooks / total * 100) : 0;
                        
                        resolve({
                            total_audiobooks: total,
                            audiobooks_with_ebooks: withEbooks,
                            audiobooks_without_ebooks: total - withEbooks,
                            total_ebooks_available: results.totalEbooksAvailable,
                            total_ebooks_downloaded: results.totalEbooksDownloaded,
                            coverage_percentage: coverage
                        });
                    }
                });
            });
            
            db.close();
        });
    }

    async getAudiobooksWithoutEbooks(limit = 50) {
        return new Promise((resolve, reject) => {
            const db = new sqlite3.Database(this.config.dbPath);
            
            const query = `
                SELECT a.album_id, a.title, a.author, a.clean_title, a.clean_author,
                       a.duration_hours, a.file_size_mb
                FROM audiobooks a
                LEFT JOIN ebooks e ON a.album_id = e.audiobook_id
                WHERE e.audiobook_id IS NULL
                ORDER BY a.title
                LIMIT ?
            `;
            
            db.all(query, [limit], (err, rows) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(rows);
                }
            });
            
            db.close();
        });
    }

    async getAudiobooksWithEbooks() {
        return new Promise((resolve, reject) => {
            const db = new sqlite3.Database(this.config.dbPath);
            
            const query = `
                SELECT a.album_id, a.title, a.author, a.duration_hours,
                       e.ebook_title, e.ebook_author, e.file_format,
                       e.download_status, e.match_confidence, e.seeders
                FROM audiobooks a
                INNER JOIN ebooks e ON a.album_id = e.audiobook_id
                ORDER BY a.title
                LIMIT 100
            `;
            
            db.all(query, (err, rows) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(rows);
                }
            });
            
            db.close();
        });
    }

    async getRecentSearches() {
        return new Promise((resolve, reject) => {
            const db = new sqlite3.Database(this.config.dbPath);
            
            const query = `
                SELECT s.*, a.title, a.author
                FROM search_attempts s
                JOIN audiobooks a ON s.audiobook_id = a.album_id
                ORDER BY s.search_date DESC
                LIMIT 20
            `;
            
            db.all(query, (err, rows) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(rows);
                }
            });
            
            db.close();
        });
    }

    async getDownloadQueue() {
        return new Promise((resolve, reject) => {
            const db = new sqlite3.Database(this.config.dbPath);
            
            const query = `
                SELECT q.*, e.ebook_title, a.title as audiobook_title
                FROM download_queue q
                JOIN ebooks e ON q.ebook_id = e.id
                JOIN audiobooks a ON e.audiobook_id = a.album_id
                ORDER BY q.priority DESC, q.added_date ASC
            `;
            
            db.all(query, (err, rows) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(rows);
                }
            });
            
            db.close();
        });
    }

    async refreshFromPlex() {
        // This would trigger a refresh from the Plex database
        return { message: 'Refresh queued', timestamp: new Date().toISOString() };
    }

    async batchSearchAndDownload(limit = 5) {
        console.log(`🚀 Starting batch search and download for ${limit} audiobooks`);
        
        return new Promise((resolve, reject) => {
            const db = new sqlite3.Database(this.config.dbPath);
            
            // Get audiobooks without ebooks
            const query = `
                SELECT a.album_id, a.title, a.author, a.clean_title, a.clean_author
                FROM audiobooks a
                LEFT JOIN ebooks e ON a.album_id = e.audiobook_id
                WHERE e.audiobook_id IS NULL
                ORDER BY a.title
                LIMIT ?
            `;
            
            db.all(query, [limit], async (err, audiobooks) => {
                if (err) {
                    db.close();
                    reject(err);
                    return;
                }
                
                db.close();
                
                const results = {
                    processed: 0,
                    successful: 0,
                    failed: 0,
                    downloads: [],
                    errors: [],
                    startTime: new Date().toISOString()
                };
                
                console.log(`📚 Processing ${audiobooks.length} audiobooks`);
                
                for (const audiobook of audiobooks) {
                    try {
                        console.log(`[${results.processed + 1}/${audiobooks.length}] Processing: ${audiobook.title}`);
                        
                        // Search for ebook
                        const searchResults = await this.searchMAMForEbook(audiobook);
                        
                        if (searchResults.length > 0) {
                            const bestMatch = searchResults[0];
                            
                            // Save search results to database
                            for (const result of searchResults) {
                                await this.saveEbookResult(audiobook.album_id, result);
                            }
                            
                            // Download if confidence is good
                            if (bestMatch.confidence > 0.6) {
                                console.log(`✨ Good match found (${(bestMatch.confidence * 100).toFixed(0)}%): ${bestMatch.title}`);
                                
                                try {
                                    const downloadResult = await this.downloadTorrentRSS(bestMatch.torrentId);
                                    
                                    results.downloads.push({
                                        audiobook: audiobook.title,
                                        ebook: bestMatch.title,
                                        confidence: bestMatch.confidence,
                                        torrentId: bestMatch.torrentId,
                                        download: downloadResult,
                                        transmission: downloadResult.transmission
                                    });
                                    
                                    results.successful++;
                                    console.log(`✅ Downloaded: ${bestMatch.title}`);
                                    
                                } catch (downloadError) {
                                    console.log(`❌ Download failed: ${downloadError.message}`);
                                    results.errors.push({
                                        audiobook: audiobook.title,
                                        error: downloadError.message,
                                        type: 'download'
                                    });
                                    results.failed++;
                                }
                            } else {
                                console.log(`🤔 Low confidence match (${(bestMatch.confidence * 100).toFixed(0)}%): ${bestMatch.title}`);
                                results.errors.push({
                                    audiobook: audiobook.title,
                                    error: 'Low confidence match',
                                    confidence: bestMatch.confidence,
                                    type: 'low_confidence'
                                });
                                results.failed++;
                            }
                        } else {
                            console.log(`🚫 No matches found for: ${audiobook.title}`);
                            results.errors.push({
                                audiobook: audiobook.title,
                                error: 'No matches found',
                                type: 'no_results'
                            });
                            results.failed++;
                        }
                        
                        results.processed++;
                        
                        // Small delay between requests to be nice to MAM
                        await new Promise(resolve => setTimeout(resolve, 2000));
                        
                    } catch (error) {
                        console.log(`💥 Error processing ${audiobook.title}: ${error.message}`);
                        results.errors.push({
                            audiobook: audiobook.title,
                            error: error.message,
                            type: 'search'
                        });
                        results.failed++;
                        results.processed++;
                    }
                }
                
                results.endTime = new Date().toISOString();
                results.duration = new Date(results.endTime) - new Date(results.startTime);
                
                console.log(`🎉 Batch processing complete: ${results.successful}/${results.processed} successful`);
                resolve(results);
            });
        });
    }

    async searchSingleAudiobook(albumId) {
        return new Promise((resolve, reject) => {
            const db = new sqlite3.Database(this.config.dbPath);
            
            // Get audiobook details
            const query = `
                SELECT album_id, title, author, clean_title, clean_author
                FROM audiobooks 
                WHERE album_id = ?
            `;
            
            db.get(query, [albumId], async (err, audiobook) => {
                if (err) {
                    db.close();
                    reject(err);
                    return;
                }
                
                if (!audiobook) {
                    db.close();
                    resolve({ success: false, message: 'Audiobook not found' });
                    return;
                }
                
                try {
                    // Use MAM API to search for ebook
                    const searchResults = await this.searchMAMForEbook(audiobook);
                    
                    // Save results to database
                    for (const result of searchResults) {
                        await this.saveEbookResult(albumId, result);
                    }
                    
                    db.close();
                    resolve({ 
                        success: true, 
                        audiobook, 
                        matches: searchResults,
                        message: `Found ${searchResults.length} potential matches`
                    });
                    
                } catch (error) {
                    db.close();
                    reject(error);
                }
            });
        });
    }

    async searchMAMForEbook(audiobook) {
        const https = require('https');
        const { URLSearchParams } = require('url');
        
        return new Promise((resolve, reject) => {
            // Build search query
            const searchQuery = `${audiobook.clean_title} ${audiobook.clean_author}`.trim();
            
            const params = new URLSearchParams({
                'tor[text]': searchQuery,
                'tor[srchIn][title]': '1',
                'tor[srchIn][author]': '1',
                'tor[cat][]': '14', // E-Books category
                'tor[sortType]': 'seeders',
                'tor[perpage]': '25'
            });
            
            const options = {
                hostname: 'www.myanonamouse.net',
                path: `/tor/js/loadSearchJSONbasic.php?${params}`,
                method: 'GET',
                headers: {
                    'Cookie': process.env.MAM_SESSION_COOKIE || '',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
            };
            
            const req = https.request(options, (res) => {
                let data = '';
                res.on('data', chunk => data += chunk);
                res.on('end', () => {
                    try {
                        const response = JSON.parse(data);
                        const results = [];
                        
                        if (response.data) {
                            for (const item of response.data) {
                                const confidence = this.calculateMatchConfidence(audiobook, item);
                                
                                results.push({
                                    torrentId: item.id,
                                    title: item.title,
                                    author: item.author || '',
                                    size: parseFloat(item.size) / (1024 * 1024), // MB
                                    seeders: parseInt(item.seeders) || 0,
                                    leechers: parseInt(item.leechers) || 0,
                                    confidence: confidence,
                                    category: item.cat_name,
                                    rssUrl: `https://www.myanonamouse.net/tor/download.php?tid=${item.id}`
                                });
                            }
                        }
                        
                        // Sort by confidence then seeders
                        results.sort((a, b) => {
                            if (b.confidence !== a.confidence) return b.confidence - a.confidence;
                            return b.seeders - a.seeders;
                        });
                        
                        resolve(results);
                        
                    } catch (error) {
                        reject(new Error('Failed to parse MAM response: ' + error.message));
                    }
                });
            });
            
            req.on('error', reject);
            req.setTimeout(30000, () => {
                req.destroy();
                reject(new Error('MAM search timeout'));
            });
            
            req.end();
        });
    }

    calculateMatchConfidence(audiobook, mamResult) {
        const titleSimilarity = this.stringSimilarity(
            audiobook.clean_title.toLowerCase(),
            (mamResult.title || '').toLowerCase()
        );
        
        const authorSimilarity = this.stringSimilarity(
            audiobook.clean_author.toLowerCase(),
            (mamResult.author || '').toLowerCase()
        );
        
        let score = (titleSimilarity * 0.7) + (authorSimilarity * 0.3);
        
        // Bonus for good seeders
        if (parseInt(mamResult.seeders) >= 5) score += 0.1;
        
        // Penalty for very large files (likely scans)
        const sizeMB = parseFloat(mamResult.size) / (1024 * 1024);
        if (sizeMB > 100) score -= 0.1;
        
        return Math.min(1.0, Math.max(0.0, score));
    }

    stringSimilarity(str1, str2) {
        const tokens1 = new Set(str1.match(/\w+/g) || []);
        const tokens2 = new Set(str2.match(/\w+/g) || []);
        
        if (tokens1.size === 0 && tokens2.size === 0) return 1;
        if (tokens1.size === 0 || tokens2.size === 0) return 0;
        
        const intersection = new Set([...tokens1].filter(x => tokens2.has(x)));
        const union = new Set([...tokens1, ...tokens2]);
        
        return intersection.size / union.size;
    }

    async downloadTorrentRSS(torrentId) {
        const fs = require('fs').promises;
        const https = require('https');
        const path = require('path');
        const { exec } = require('child_process');
        const { promisify } = require('util');
        const execAsync = promisify(exec);
        
        return new Promise((resolve, reject) => {
            const downloadUrl = `https://www.myanonamouse.net/tor/download.php?tid=${torrentId}`;
            
            const options = {
                headers: {
                    'Cookie': process.env.MAM_SESSION_COOKIE || '',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
            };
            
            const req = https.get(downloadUrl, options, async (res) => {
                if (res.statusCode !== 200) {
                    reject(new Error(`Download failed: ${res.statusCode}`));
                    return;
                }
                
                const chunks = [];
                res.on('data', chunk => chunks.push(chunk));
                res.on('end', async () => {
                    try {
                        const buffer = Buffer.concat(chunks);
                        const filename = `torrent_${torrentId}_${Date.now()}.torrent`;
                        const filepath = path.join(process.env.DOWNLOAD_DIR || './mam_downloads', filename);
                        
                        // Ensure download directory exists
                        await fs.mkdir(path.dirname(filepath), { recursive: true });
                        
                        // Save torrent file
                        await fs.writeFile(filepath, buffer);
                        
                        // Add to Transmission for automatic downloading
                        const transmissionResult = await this.addToTransmission(filepath, torrentId);
                        
                        // Update database
                        await this.updateDownloadStatus(torrentId, 'downloading', filepath);
                        
                        resolve({
                            success: true,
                            filename,
                            filepath,
                            size: buffer.length,
                            transmission: transmissionResult,
                            message: 'Torrent downloaded and added to Transmission'
                        });
                        
                    } catch (error) {
                        reject(error);
                    }
                });
            });
            
            req.on('error', reject);
            req.setTimeout(30000, () => {
                req.destroy();
                reject(new Error('Download timeout'));
            });
        });
    }

    async addToTransmission(torrentFilePath, torrentId) {
        const { exec } = require('child_process');
        const { promisify } = require('util');
        const execAsync = promisify(exec);
        
        try {
            // Check if transmission-cli is available
            await execAsync('which transmission-remote');
            
            // Configuration from environment or defaults
            const transmissionHost = process.env.TRANSMISSION_HOST || 'localhost';
            const transmissionPort = process.env.TRANSMISSION_PORT || '9091';
            const transmissionUser = process.env.TRANSMISSION_USER || '';
            const transmissionPass = process.env.TRANSMISSION_PASS || '';
            const downloadDir = process.env.EBOOK_DOWNLOAD_DIR || './completed_ebooks';
            
            // Build transmission-remote command
            let cmd = `transmission-remote ${transmissionHost}:${transmissionPort}`;
            
            // Add authentication if provided
            if (transmissionUser && transmissionPass) {
                cmd += ` --auth ${transmissionUser}:${transmissionPass}`;
            }
            
            // Add torrent with download directory
            cmd += ` --add "${torrentFilePath}" --download-dir "${downloadDir}"`;
            
            console.log(`📡 Adding torrent to Transmission: ${torrentId}`);
            const { stdout, stderr } = await execAsync(cmd);
            
            if (stderr && !stderr.includes('success')) {
                throw new Error(`Transmission error: ${stderr}`);
            }
            
            console.log(`✅ Torrent added to Transmission: ${stdout.trim()}`);
            
            // Get torrent info
            const infoCmd = `${cmd.split(' --add')[0]} --list | grep -i "${torrentId}"`;
            let torrentInfo = '';
            try {
                const { stdout: listOutput } = await execAsync(infoCmd);
                torrentInfo = listOutput.trim();
            } catch (e) {
                // Info command failed, but torrent was added
            }
            
            return {
                success: true,
                command: cmd,
                output: stdout.trim(),
                info: torrentInfo,
                downloadDir: downloadDir
            };
            
        } catch (error) {
            console.log(`⚠️ Transmission not available or failed: ${error.message}`);
            
            // Fallback: just save torrent file for manual handling
            return {
                success: false,
                error: error.message,
                fallback: 'Torrent file saved for manual download',
                suggestion: 'Install transmission-cli or configure Transmission daemon'
            };
        }
    }

    async checkTransmissionStatus(torrentId) {
        const { exec } = require('child_process');
        const { promisify } = require('util');
        const execAsync = promisify(exec);
        
        try {
            const transmissionHost = process.env.TRANSMISSION_HOST || 'localhost';
            const transmissionPort = process.env.TRANSMISSION_PORT || '9091';
            const transmissionUser = process.env.TRANSMISSION_USER || '';
            const transmissionPass = process.env.TRANSMISSION_PASS || '';
            
            let cmd = `transmission-remote ${transmissionHost}:${transmissionPort}`;
            
            if (transmissionUser && transmissionPass) {
                cmd += ` --auth ${transmissionUser}:${transmissionPass}`;
            }
            
            cmd += ` --list`;
            
            const { stdout } = await execAsync(cmd);
            
            // Parse transmission list output to find our torrent
            const lines = stdout.split('\n');
            for (const line of lines) {
                if (line.includes(torrentId)) {
                    const parts = line.trim().split(/\s+/);
                    return {
                        id: parts[0],
                        progress: parts[2],
                        status: parts[8],
                        name: parts.slice(9).join(' ')
                    };
                }
            }
            
            return null; // Torrent not found
            
        } catch (error) {
            return { error: error.message };
        }
    }

    async saveEbookResult(audiobookId, result) {
        return new Promise((resolve, reject) => {
            const db = new sqlite3.Database(this.config.dbPath);
            
            const query = `
                INSERT OR REPLACE INTO ebooks (
                    audiobook_id, mam_torrent_id, ebook_title, ebook_author,
                    file_format, file_size_mb, seeders, leechers,
                    match_confidence, download_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            `;
            
            db.run(query, [
                audiobookId,
                result.torrentId,
                result.title,
                result.author,
                'epub', // Default format
                result.size,
                result.seeders,
                result.leechers,
                result.confidence,
                'available'
            ], function(err) {
                db.close();
                if (err) reject(err);
                else resolve(this.lastID);
            });
        });
    }

    async updateDownloadStatus(torrentId, status, filepath = null) {
        return new Promise((resolve, reject) => {
            const db = new sqlite3.Database(this.config.dbPath);
            
            const query = `
                UPDATE ebooks 
                SET download_status = ?, 
                    download_date = datetime('now'),
                    local_file_path = ?
                WHERE mam_torrent_id = ?
            `;
            
            db.run(query, [status, filepath, torrentId], function(err) {
                db.close();
                if (err) reject(err);
                else resolve(this.changes);
            });
        });
    }

    start() {
        this.app.listen(this.config.port, this.config.host, () => {
            console.log(`\n🌐 LibraryOfBabel Web Interface`);
            console.log(`   📍 http://${this.config.host}:${this.config.port}`);
            console.log(`   📊 Database: ${this.config.dbPath}`);
            console.log(`   🚀 Server started successfully\n`);
        });
    }
}

// Start server if run directly
if (require.main === module) {
    const config = {
        port: process.env.PORT || 3000,
        host: process.env.HOST || 'localhost',
        dbPath: process.env.DB_PATH || './audiobook_ebook_tracker.db'
    };
    
    const app = new AudiobookEbookWebApp(config);
    app.start();
}

module.exports = AudiobookEbookWebApp;