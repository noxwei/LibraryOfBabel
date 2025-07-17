const { chromium } = require('playwright');

async function testMCPInBrowser() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  console.log('🧪 Testing MCP endpoints in browser...');
  
  // Test OAuth metadata discovery
  console.log('\n1. Testing OAuth metadata discovery...');
  const metadataResponse = await page.evaluate(async () => {
    try {
      const response = await fetch('https://api.ashortstayinhell.com:5562/.well-known/mcp_oauth_metadata');
      return {
        status: response.status,
        data: await response.json()
      };
    } catch (error) {
      return { error: error.message };
    }
  });
  console.log('OAuth metadata:', metadataResponse);
  
  // Test SSE endpoint without auth
  console.log('\n2. Testing SSE endpoint without auth...');
  const sseResponse = await page.evaluate(async () => {
    try {
      const response = await fetch('https://api.ashortstayinhell.com:5562/sse');
      return {
        status: response.status,
        text: await response.text()
      };
    } catch (error) {
      return { error: error.message };
    }
  });
  console.log('SSE without auth:', sseResponse);
  
  // Test SSE with API key
  console.log('\n3. Testing SSE with API key...');
  const sseWithKeyResponse = await page.evaluate(async () => {
    try {
      const response = await fetch('https://api.ashortstayinhell.com:5562/sse?api_key=babel_secure_3f99c2d1d294fbebdfc6b10cce93652d', {
        headers: {
          'Accept': 'text/event-stream'
        }
      });
      return {
        status: response.status,
        text: (await response.text()).substring(0, 500) + '...'
      };
    } catch (error) {
      return { error: error.message };
    }
  });
  console.log('SSE with API key:', sseWithKeyResponse);
  
  // Test OAuth flow
  console.log('\n4. Testing OAuth authorization flow...');
  const authResponse = await page.evaluate(async () => {
    try {
      const response = await fetch('https://api.ashortstayinhell.com:5562/oauth/authorize?client_id=library-of-babel-client&redirect_uri=https://claude.ai/oauth/callback&response_type=code&state=test123');
      const html = await response.text();
      const authCodeMatch = html.match(/babel_auth_[^"&]*/);
      return {
        status: response.status,
        authCode: authCodeMatch ? authCodeMatch[0] : null,
        hasRedirect: html.includes('window.location.href')
      };
    } catch (error) {
      return { error: error.message };
    }
  });
  console.log('OAuth auth:', authResponse);
  
  // Test token exchange
  if (authResponse.authCode) {
    console.log('\n5. Testing token exchange...');
    const tokenResponse = await page.evaluate(async (authCode) => {
      try {
        const response = await fetch('https://api.ashortstayinhell.com:5562/oauth/token', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            grant_type: 'authorization_code',
            code: authCode,
            client_id: 'library-of-babel-client',
            client_secret: 'babel_oauth_secret_key'
          })
        });
        return {
          status: response.status,
          data: await response.json()
        };
      } catch (error) {
        return { error: error.message };
      }
    }, authResponse.authCode);
    console.log('Token exchange:', tokenResponse);
    
    // Test SSE with Bearer token
    if (tokenResponse.data && tokenResponse.data.access_token) {
      console.log('\n6. Testing SSE with Bearer token...');
      const sseWithTokenResponse = await page.evaluate(async (token) => {
        try {
          const response = await fetch('https://api.ashortstayinhell.com:5562/sse', {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Accept': 'text/event-stream'
            }
          });
          return {
            status: response.status,
            text: (await response.text()).substring(0, 500) + '...'
          };
        } catch (error) {
          return { error: error.message };
        }
      }, tokenResponse.data.access_token);
      console.log('SSE with Bearer token:', sseWithTokenResponse);
      
      // Test tool call
      console.log('\n7. Testing tool call...');
      const toolResponse = await page.evaluate(async (token) => {
        try {
          const response = await fetch('https://api.ashortstayinhell.com:5562/sse', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              jsonrpc: '2.0',
              method: 'tools/call',
              params: {
                name: 'get_library_stats',
                arguments: {}
              },
              id: 1
            })
          });
          return {
            status: response.status,
            data: await response.json()
          };
        } catch (error) {
          return { error: error.message };
        }
      }, tokenResponse.data.access_token);
      console.log('Tool call:', toolResponse);
    }
  }
  
  console.log('\n✅ Browser testing complete!');
  await browser.close();
}

testMCPInBrowser().catch(console.error);