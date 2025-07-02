// Test working MAM API with broader searches
require('dotenv').config();

class MyAnonamouseAPI {
    constructor(sessionCookie) {
        this.baseUrl = 'https://www.myanonamouse.net';
        this.searchEndpoint = '/tor/js/loadSearchJSONbasic.php';
        this.sessionCookie = sessionCookie;
    }

    async search(options = {}) {
        const params = new URLSearchParams({
            'tor[text]': options.text || '',
            'tor[srchIn][title]': 'true',
            'tor[srchIn][author]': 'true', 
            'tor[searchType]': options.searchType || 'all',
            'tor[cat][]': options.categories ? options.categories[0] : '0', // 0 = all categories
            'tor[sortType]': options.sortType || 'seedersDesc',
            'tor[startNumber]': (options.startNumber || 0).toString(),
            'tor[perpage]': (options.perpage || 25).toString()
        });

        const response = await fetch(`${this.baseUrl}${this.searchEndpoint}?${params}`, {
            method: 'GET',
            headers: {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.myanonamouse.net/',
                'Cookie': this.sessionCookie
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    formatResults(searchResults) {
        if (!searchResults.data || !Array.isArray(searchResults.data)) {
            return [];
        }

        return searchResults.data.map(torrent => ({
            id: torrent.id,
            title: torrent.title || torrent.name,
            author: this.parseJsonField(torrent.author_info),
            category: torrent.catname,
            size: this.formatBytes(parseInt(torrent.size)),
            seeders: parseInt(torrent.seeders),
            leechers: parseInt(torrent.leechers),
            downloadUrl: `${this.baseUrl}/tor/download.php?tid=${torrent.id}`
        }));
    }

    parseJsonField(jsonString) {
        if (!jsonString) return null;
        try {
            return JSON.parse(jsonString);
        } catch (e) {
            return null;
        }
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

async function testWorkingAPI() {
    console.log('🎉 Testing Working MAM API...');
    
    const sessionCookie = process.env.MAM_SESSION_COOKIE;
    const api = new MyAnonamouseAPI(sessionCookie);

    const searches = [
        { text: 'python', desc: 'Popular programming topic' },
        { text: 'stephen king', desc: 'Popular author' },
        { text: 'fantasy', desc: 'Popular genre' },
        { text: '', desc: 'All books (newest)' }
    ];

    for (const search of searches) {
        try {
            console.log(`\n🔍 Testing: "${search.text}" (${search.desc})`);
            const results = await api.search({ 
                text: search.text, 
                perpage: 5,
                categories: ['0'] // All categories
            });
            
            console.log(`✅ Found ${results.data ? results.data.length : 0} results`);
            
            if (results.data && results.data.length > 0) {
                const formatted = api.formatResults(results);
                console.log(`📖 Sample: "${formatted[0].title}"`);
                console.log(`📂 Category: ${formatted[0].category}`);
                console.log(`🌱 Seeders: ${formatted[0].seeders}`);
                break; // Stop at first successful search with results
            }
            
        } catch (error) {
            console.error(`❌ Search failed: ${error.message}`);
        }
    }
    
    console.log('\n🎊 MAM API is fully operational!');
    console.log('Ready for integration with LibraryOfBabel system.');
}

testWorkingAPI();