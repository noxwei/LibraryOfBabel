// Debug MAM Session - detailed logging
require('dotenv').config();

async function debugSession() {
    console.log('🔍 Debug MAM Session...');
    
    const sessionCookie = process.env.MAM_SESSION_COOKIE;
    console.log('🍪 Raw session cookie:', sessionCookie?.substring(0, 50) + '...');
    
    // Parse cookies like the Python version
    const cookies = {};
    if (sessionCookie && sessionCookie.includes('mam_id=')) {
        const cookieParts = sessionCookie.split(';');
        for (const part of cookieParts) {
            if (part.includes('=')) {
                const [key, value] = part.trim().split('=', 2);
                cookies[key] = value;
            }
        }
    }
    
    console.log('🍪 Parsed cookies:', Object.keys(cookies));
    console.log('🆔 mam_id length:', cookies.mam_id?.length);
    console.log('👤 uid:', cookies.uid);
    
    // Test with minimal request like curl
    const url = 'https://www.myanonamouse.net/tor/js/loadSearchJSONbasic.php';
    const params = new URLSearchParams({
        'tor[text]': 'programming',
        'tor[srchIn][title]': 'true',
        'tor[srchIn][author]': 'true',
        'tor[searchType]': 'all',
        'tor[cat][]': '14', // E-Books
        'tor[sortType]': 'seedersDesc',
        'tor[startNumber]': '0',
        'tor[perpage]': '5'
    });
    
    const headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.myanonamouse.net/',
        'Cookie': `mam_id=${cookies.mam_id}; uid=${cookies.uid}`
    };
    
    console.log('\n📡 Request details:');
    console.log('URL:', url);
    console.log('Cookie header:', headers.Cookie.substring(0, 50) + '...');
    
    try {
        const response = await fetch(`${url}?${params}`, {
            method: 'GET',
            headers: headers
        });
        
        console.log('\n📊 Response:');
        console.log('Status:', response.status);
        console.log('Headers:', Object.fromEntries(response.headers.entries()));
        
        if (response.status === 200) {
            const data = await response.json();
            console.log('✅ SUCCESS! Found results:', data.data?.length || 0);
            if (data.data?.[0]) {
                console.log('📖 First result:', data.data[0].title);
            }
        } else {
            const text = await response.text();
            console.log('❌ Error response:', text.substring(0, 200));
        }
        
    } catch (error) {
        console.error('💥 Request failed:', error.message);
    }
}

debugSession();