/**
 * MAM Playwright Automation
 * Automates MyAnonamouse ebook search and download with session management
 */

const { chromium } = require('playwright');
const fs = require('fs').promises;
const path = require('path');
const sqlite3 = require('sqlite3').verbose();

// Load environment variables
require('dotenv').config();

class MAMPlaywrightAutomation {
    constructor(config = {}) {
        this.config = {
            headless: config.headless || false,
            slowMo: config.slowMo || 1000,
            timeout: config.timeout || 30000,
            downloadDir: config.downloadDir || './mam_downloads',
            sessionFile: config.sessionFile || './mam_session.json',
            dbPath: config.dbPath || './audiobook_ebook_tracker.db',
            maxDailyDownloads: config.maxDailyDownloads || 95,
            ...config
        };
        
        this.browser = null;
        this.page = null;
        this.session = null;
        this.dailyDownloadCount = 0;
    }

    async init() {
        // Create download directory
        await fs.mkdir(this.config.downloadDir, { recursive: true });
        
        // Load session if exists
        await this.loadSession();
        
        // Launch browser
        this.browser = await chromium.launch({
            headless: this.config.headless,
            slowMo: this.config.slowMo
        });
        
        const context = await this.browser.newContext({
            downloadPath: this.config.downloadDir,
            acceptDownloads: true
        });
        
        this.page = await context.newPage();
        this.page.setDefaultTimeout(this.config.timeout);
        
        // Load cookies if session exists
        if (this.session && this.session.cookies) {
            await context.addCookies(this.session.cookies);
        }
        
        console.log('🚀 MAM Playwright automation initialized');
    }

    async loadSession() {
        try {
            const sessionData = await fs.readFile(this.config.sessionFile, 'utf8');
            this.session = JSON.parse(sessionData);
            console.log('📱 Loaded existing MAM session');
        } catch (error) {
            console.log('🆕 No existing session found, will need to login');
            this.session = null;
        }
    }

    async saveSession() {
        if (!this.page) return;
        
        const cookies = await this.page.context().cookies();
        this.session = {
            cookies,
            timestamp: new Date().toISOString()
        };
        
        await fs.writeFile(this.config.sessionFile, JSON.stringify(this.session, null, 2));
        console.log('💾 Session saved');
    }

    async setSessionCookie(cookieValue) {
        console.log('🍪 Setting MAM session cookie...');
        
        await this.page.context().addCookies([{
            name: 'mam_id',
            value: cookieValue,
            domain: '.myanonamouse.net',
            path: '/',
            httpOnly: true,
            secure: true
        }]);
        
        // Test if session works
        await this.page.goto('https://www.myanonamouse.net/');
        
        try {
            await this.page.waitForSelector('.user-menu', { timeout: 10000 });
            console.log('✅ Session cookie authentication successful');
            await this.saveSession();
            return true;
        } catch (error) {
            console.log('❌ Session cookie expired or invalid');
            console.log('   Please update MAM_SESSION_COOKIE in .env file');
            return false;
        }
    }

    async checkSessionValid() {
        console.log('🔍 Checking if existing session is still valid...');
        
        try {
            await this.page.goto('https://www.myanonamouse.net/');
            await this.page.waitForSelector('.user-menu', { timeout: 5000 });
            console.log('✅ Existing session is still valid');
            return true;
        } catch (error) {
            console.log('⚠️ No valid session found, will need to login');
            return false;
        }
    }

    async login(username, password) {
        console.log('🔐 Logging into MAM...');
        
        try {
            // Go directly to login page
            await this.page.goto('https://www.myanonamouse.net/login.php');
            
            // Wait for login form
            await this.page.waitForSelector('#usernamelogin', { timeout: 10000 });
            console.log('📝 Login form found');
            
            // Fill login form
            await this.page.fill('#usernamelogin', username);
            await this.page.fill('#passwordlogin', password);
            console.log('✍️ Credentials entered');
            
            // Submit login
            await this.page.click('input[type="submit"][value="Login"]');
            console.log('📤 Login form submitted');
            
            // Wait for login success - look for user menu or dashboard
            try {
                await this.page.waitForSelector('.user-menu, #user-menu, .navbar-nav', { timeout: 15000 });
                console.log('✅ Login successful');
                await this.saveSession();
                return true;
            } catch (error) {
                console.log('❌ Login failed - could not find user menu');
                
                // Check if we're on an error page
                const pageContent = await this.page.content();
                if (pageContent.includes('error') || pageContent.includes('failed') || pageContent.includes('invalid')) {
                    console.log('🚫 Login error detected on page');
                }
                
                return false;
            }
            
        } catch (error) {
            console.error('❌ Login process failed:', error.message);
            return false;
        }
    }

    async searchEbook(title, author) {
        console.log(`🔍 Searching for: "${title}" by ${author}`);
        
        // Navigate to browse page
        await this.page.goto('https://www.myanonamouse.net/tor/browse.php');
        await this.page.waitForSelector('#browse');
        
        // Set search parameters
        const searchQuery = `${title} ${author}`.trim();
        
        // Fill search form
        await this.page.fill('input[name="tor[text]"]', searchQuery);
        
        // Select E-Books category (category 14)
        await this.page.selectOption('select[name="tor[cat][]"]', '14');
        
        // Set sort by seeders
        await this.page.selectOption('select[name="tor[sortType]"]', 'seeders');
        
        // Submit search
        await this.page.click('input[type="submit"][value="Browse Torrents"]');
        
        // Wait for results
        await this.page.waitForSelector('.torrentTable, .no-results', { timeout: 10000 });
        
        // Parse search results
        const results = await this.parseSearchResults(title, author);
        
        console.log(`📊 Found ${results.length} potential matches`);
        return results;
    }

    async parseSearchResults(originalTitle, originalAuthor) {
        const results = [];
        
        try {
            // Check if no results
            const noResults = await this.page.$('.no-results');
            if (noResults) {
                return results;
            }
            
            // Get all torrent rows
            const torrentRows = await this.page.$$('.torrentTable tr.torrent_row');
            
            for (const row of torrentRows) {
                try {
                    // Extract torrent information
                    const titleElement = await row.$('.torrent-title a');
                    const authorElement = await row.$('.torrent-author');
                    const seedersElement = await row.$('.seeders');
                    const sizeElement = await row.$('.size');
                    const downloadElement = await row.$('.download-link');
                    
                    if (!titleElement || !downloadElement) continue;
                    
                    const title = await titleElement.textContent();
                    const author = authorElement ? await authorElement.textContent() : '';
                    const seeders = seedersElement ? parseInt(await seedersElement.textContent()) : 0;
                    const sizeText = sizeElement ? await sizeElement.textContent() : '';
                    const downloadHref = await downloadElement.getAttribute('href');
                    
                    // Calculate match confidence
                    const confidence = this.calculateMatchConfidence(
                        originalTitle, originalAuthor, title, author
                    );
                    
                    // Parse file size
                    const sizeMB = this.parseFileSize(sizeText);
                    
                    // Extract torrent ID from download link
                    const torrentIdMatch = downloadHref.match(/tid=(\d+)/);
                    const torrentId = torrentIdMatch ? torrentIdMatch[1] : null;
                    
                    if (torrentId && confidence > 0.3) {
                        results.push({
                            torrentId,
                            title: title.trim(),
                            author: author.trim(),
                            seeders,
                            sizeMB,
                            confidence,
                            downloadUrl: `https://www.myanonamouse.net${downloadHref}`
                        });
                    }
                } catch (error) {
                    console.log('⚠️ Error parsing torrent row:', error.message);
                }
            }
            
            // Sort by confidence, then by seeders
            results.sort((a, b) => {
                if (b.confidence !== a.confidence) {
                    return b.confidence - a.confidence;
                }
                return b.seeders - a.seeders;
            });
            
        } catch (error) {
            console.error('❌ Error parsing search results:', error);
        }
        
        return results;
    }

    calculateMatchConfidence(originalTitle, originalAuthor, resultTitle, resultAuthor) {
        // Simple token-based matching
        const titleTokens1 = this.tokenize(originalTitle.toLowerCase());
        const titleTokens2 = this.tokenize(resultTitle.toLowerCase());
        const authorTokens1 = this.tokenize(originalAuthor.toLowerCase());
        const authorTokens2 = this.tokenize(resultAuthor.toLowerCase());
        
        const titleSimilarity = this.jaccard(titleTokens1, titleTokens2);
        const authorSimilarity = this.jaccard(authorTokens1, authorTokens2);
        
        return (titleSimilarity * 0.7) + (authorSimilarity * 0.3);
    }

    tokenize(text) {
        return new Set(text.match(/\b\w+\b/g) || []);
    }

    jaccard(set1, set2) {
        if (set1.size === 0 && set2.size === 0) return 1;
        if (set1.size === 0 || set2.size === 0) return 0;
        
        const intersection = new Set([...set1].filter(x => set2.has(x)));
        const union = new Set([...set1, ...set2]);
        
        return intersection.size / union.size;
    }

    parseFileSize(sizeText) {
        const match = sizeText.match(/([\d.]+)\s*(MB|GB|KB)/i);
        if (!match) return 0;
        
        const value = parseFloat(match[1]);
        const unit = match[2].toUpperCase();
        
        switch (unit) {
            case 'KB': return value / 1024;
            case 'MB': return value;
            case 'GB': return value * 1024;
            default: return 0;
        }
    }

    async downloadTorrent(downloadUrl, torrentId, title) {
        try {
            console.log(`⬇️ Downloading torrent: ${title}`);
            
            // Start download
            const [download] = await Promise.all([
                this.page.waitForEvent('download'),
                this.page.goto(downloadUrl)
            ]);
            
            // Save download with proper filename
            const filename = `${this.sanitizeFilename(title)}_${torrentId}.torrent`;
            const filepath = path.join(this.config.downloadDir, filename);
            await download.saveAs(filepath);
            
            console.log(`✅ Downloaded: ${filename}`);
            
            // Update database
            await this.updateDownloadStatus(torrentId, 'completed', filepath);
            
            this.dailyDownloadCount++;
            
            return {
                success: true,
                filepath,
                filename
            };
            
        } catch (error) {
            console.error(`❌ Download failed for ${title}:`, error.message);
            
            // Update database with failure
            await this.updateDownloadStatus(torrentId, 'failed');
            
            return {
                success: false,
                error: error.message
            };
        }
    }

    sanitizeFilename(filename) {
        return filename
            .replace(/[^\w\s-]/g, '')
            .replace(/\s+/g, '_')
            .substring(0, 100);
    }

    async updateDownloadStatus(torrentId, status, filepath = null) {
        return new Promise((resolve, reject) => {
            const db = new sqlite3.Database(this.config.dbPath);
            
            const updateQuery = `
                UPDATE ebooks 
                SET download_status = ?, 
                    download_date = datetime('now'),
                    local_file_path = ?
                WHERE mam_torrent_id = ?
            `;
            
            db.run(updateQuery, [status, filepath, torrentId], function(err) {
                if (err) {
                    console.error('Database update error:', err);
                    reject(err);
                } else {
                    resolve(this.changes);
                }
            });
            
            db.close();
        });
    }

    async processAudiobooksQueue(limit = 20) {
        console.log(`🎯 Processing audiobooks queue (limit: ${limit})`);
        
        const audiobooks = await this.getAudiobooksWithoutEbooks(limit);
        console.log(`📚 Found ${audiobooks.length} audiobooks without ebooks`);
        
        let processed = 0;
        let successful = 0;
        
        for (const audiobook of audiobooks) {
            if (this.dailyDownloadCount >= this.config.maxDailyDownloads) {
                console.log('🛑 Daily download limit reached');
                break;
            }
            
            console.log(`\n[${processed + 1}/${audiobooks.length}] Processing: ${audiobook.title}`);
            
            try {
                // Search for ebook
                const results = await this.searchEbook(audiobook.clean_title, audiobook.clean_author);
                
                if (results.length > 0) {
                    const bestMatch = results[0];
                    
                    if (bestMatch.confidence > 0.6) {
                        console.log(`✨ Good match found (confidence: ${bestMatch.confidence.toFixed(2)})`);
                        console.log(`   📖 ${bestMatch.title} by ${bestMatch.author}`);
                        console.log(`   🌱 Seeders: ${bestMatch.seeders}, Size: ${bestMatch.sizeMB.toFixed(1)}MB`);
                        
                        // Save to database before download
                        await this.saveEbookResult(audiobook.album_id, bestMatch);
                        
                        // Download torrent
                        const downloadResult = await this.downloadTorrent(
                            bestMatch.downloadUrl,
                            bestMatch.torrentId,
                            bestMatch.title
                        );
                        
                        if (downloadResult.success) {
                            successful++;
                        }
                        
                        // Delay between downloads
                        await this.delay(3000);
                        
                    } else {
                        console.log(`🤔 Low confidence match (${bestMatch.confidence.toFixed(2)}): ${bestMatch.title}`);
                    }
                } else {
                    console.log('🚫 No matches found');
                }
                
                // Log search attempt
                await this.logSearchAttempt(audiobook.album_id, `${audiobook.clean_title} ${audiobook.clean_author}`, results.length);
                
            } catch (error) {
                console.error(`❌ Error processing ${audiobook.title}:`, error.message);
            }
            
            processed++;
            
            // Delay between searches
            await this.delay(2000);
        }
        
        console.log(`\n🎉 Processing complete: ${successful}/${processed} successful downloads`);
        return { processed, successful };
    }

    async saveEbookResult(audiobookId, result) {
        return new Promise((resolve, reject) => {
            const db = new sqlite3.Database(this.config.dbPath);
            
            const insertQuery = `
                INSERT OR REPLACE INTO ebooks (
                    audiobook_id, mam_torrent_id, ebook_title, ebook_author,
                    file_format, file_size_mb, seeders, leechers,
                    match_confidence, download_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            `;
            
            db.run(insertQuery, [
                audiobookId,
                result.torrentId,
                result.title,
                result.author,
                'epub', // Default format
                result.sizeMB,
                result.seeders,
                0, // leechers not tracked
                result.confidence,
                'available'
            ], function(err) {
                if (err) {
                    reject(err);
                } else {
                    resolve(this.lastID);
                }
            });
            
            db.close();
        });
    }

    async logSearchAttempt(audiobookId, query, resultsFound) {
        return new Promise((resolve, reject) => {
            const db = new sqlite3.Database(this.config.dbPath);
            
            const insertQuery = `
                INSERT INTO search_attempts (audiobook_id, search_query, results_found)
                VALUES (?, ?, ?)
            `;
            
            db.run(insertQuery, [audiobookId, query, resultsFound], function(err) {
                if (err) {
                    reject(err);
                } else {
                    resolve(this.lastID);
                }
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

    async delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    async close() {
        if (this.page) {
            await this.saveSession();
        }
        if (this.browser) {
            await this.browser.close();
        }
        console.log('🔒 Browser closed');
    }
}

// CLI interface
async function main() {
    const config = {
        headless: process.env.HEADLESS === 'true',
        downloadDir: process.env.DOWNLOAD_DIR || './mam_downloads',
        dbPath: process.env.DB_PATH || './audiobook_ebook_tracker.db',
        maxDailyDownloads: parseInt(process.env.MAX_DAILY_DOWNLOADS) || 95
    };
    
    const automation = new MAMPlaywrightAutomation(config);
    
    try {
        await automation.init();
        
        // Login with credentials or use session cookie
        const username = process.env.MAM_USERNAME;
        const password = process.env.MAM_PASSWORD;
        const sessionCookie = process.env.MAM_SESSION_COOKIE;
        
        // Auto-login with credentials from .env
        console.log('🔐 Auto-filling login credentials...');
        
        // Go to login page
        await automation.page.goto('https://www.myanonamouse.net/login.php');
        
        try {
            // Try different common login form selectors
            const possibleSelectors = [
                '#usernamelogin', '#username', 'input[name="username"]', 
                '#email', 'input[name="email"]', 'input[type="email"]',
                '#login', 'input[name="login"]'
            ];
            
            let usernameSelector = null;
            for (const selector of possibleSelectors) {
                try {
                    await automation.page.waitForSelector(selector, { timeout: 2000 });
                    usernameSelector = selector;
                    console.log(`📝 Found username field: ${selector}`);
                    break;
                } catch (e) {
                    // Try next selector
                }
            }
            
            if (!usernameSelector) {
                console.log('🔍 Could not find username field, will wait for manual login...');
                console.log('📱 Please login manually in the browser window');
                await automation.page.waitForSelector('.user-menu, #user-menu, .navbar-nav', { timeout: 60000 });
                console.log('✅ Manual login detected!');
            } else {
                // Auto-fill login form
                await automation.page.fill(usernameSelector, username);
                
                // Find password field
                const passwordSelectors = ['#passwordlogin', '#password', 'input[name="password"]', 'input[type="password"]'];
                let passwordSelector = null;
                for (const selector of passwordSelectors) {
                    try {
                        await automation.page.waitForSelector(selector, { timeout: 1000 });
                        passwordSelector = selector;
                        break;
                    } catch (e) {
                        // Try next
                    }
                }
                
                if (passwordSelector) {
                    await automation.page.fill(passwordSelector, password);
                    console.log('✍️ Credentials auto-filled from .env file');
                    
                    // Try to submit
                    try {
                        await automation.page.click('input[type="submit"], button[type="submit"], .btn-login, #login-submit');
                        console.log('📤 Login submitted automatically');
                        
                        // Wait for successful login
                        await automation.page.waitForSelector('.user-menu, #user-menu, .navbar-nav', { timeout: 15000 });
                        console.log('✅ Auto-login successful!');
                    } catch (e) {
                        console.log('📱 Please click the login button manually');
                        await automation.page.waitForSelector('.user-menu, #user-menu, .navbar-nav', { timeout: 30000 });
                        console.log('✅ Manual login completed!');
                    }
                }
            }
            
            await automation.saveSession();
            
        } catch (error) {
            console.error('❌ Auto-login failed:', error.message);
            console.log('💡 Check your MAM_USERNAME and MAM_PASSWORD in .env file');
            process.exit(1);
        }
        
        // Process audiobooks queue
        const limit = parseInt(process.argv[2]) || 20;
        await automation.processAudiobooksQueue(limit);
        
    } catch (error) {
        console.error('💥 Fatal error:', error);
    } finally {
        await automation.close();
    }
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = MAMPlaywrightAutomation;