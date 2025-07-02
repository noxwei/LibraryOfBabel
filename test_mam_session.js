// Test MAM Session with the provided API class
require('dotenv').config();

class MyAnonamouseAPI {
    constructor(sessionCookie) {
        this.baseUrl = 'https://www.myanonamouse.net';
        this.searchEndpoint = '/tor/js/loadSearchJSONbasic.php';
        this.downloadEndpoint = '/tor/download.php';
        this.sessionCookie = sessionCookie;
    }

    async search(options = {}) {
        // Use GET request with form parameters like the working Python version
        const params = new URLSearchParams({
            'tor[text]': options.text || '',
            'tor[srchIn][title]': 'true',
            'tor[srchIn][author]': 'true', 
            'tor[searchType]': options.searchType || 'all',
            'tor[cat][]': options.categories ? options.categories[0] : '0',
            'tor[sortType]': options.sortType || 'seedersDesc',
            'tor[startNumber]': (options.startNumber || 0).toString(),
            'tor[perpage]': (options.perpage || 25).toString()
        });

        try {
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
        } catch (error) {
            console.error('Search failed:', error);
            throw error;
        }
    }

    async searchEbooks(query, options = {}) {
        return this.search({
            text: query,
            categories: ['39', '40', '41', '42', '43', '44', '45', '46', '47', '48'],
            searchType: options.searchType || 'all',
            sortType: options.sortType || 'seedersDesc',
            ...options
        });
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
            leechers: parseInt(torrent.leechers)
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

async function testSession() {
    console.log('🔍 Testing MAM Session...');
    
    const sessionCookie = process.env.MAM_SESSION_COOKIE;
    if (!sessionCookie) {
        console.error('❌ No session cookie found in .env file');
        return;
    }

    console.log('🍪 Session cookie loaded from .env');
    
    const api = new MyAnonamouseAPI(sessionCookie);

    try {
        console.log('📚 Testing ebook search for "programming"...');
        const results = await api.searchEbooks('programming', { perpage: 5 });
        
        console.log(`✅ Search successful! Found ${results.data ? results.data.length : 0} results`);
        
        if (results.data && results.data.length > 0) {
            console.log('\n📖 Sample results:');
            const formatted = api.formatResults(results);
            formatted.slice(0, 3).forEach((book, i) => {
                console.log(`${i + 1}. ${book.title}`);
                console.log(`   Author: ${book.author ? Object.values(book.author).join(', ') : 'Unknown'}`);
                console.log(`   Size: ${book.size}, Seeders: ${book.seeders}`);
                console.log('');
            });
        }
        
        console.log('🎉 Session is working correctly!');
        
    } catch (error) {
        console.error('❌ Session test failed:', error.message);
        if (error.message.includes('401') || error.message.includes('403')) {
            console.log('🔄 Session may have expired. Try refreshing your browser session.');
        }
    }
}

testSession();