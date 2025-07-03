/**
 * Local Network Library of Babel Server
 * 
 * Runs dual-domain system on local network for testing before Cloudflare deployment
 * Access via localhost and local IP address (10.0.0.x)
 */

require('dotenv').config({ path: '.env.local' });
const express = require('express');
const cors = require('cors');
const path = require('path');
const os = require('os');

// Import our core modules
const BabelContentGenerator = require('./generators/BabelContentGenerator');
const BabelSearchEngine = require('./search/BabelSearchEngine');
const config = require('../config/default');

// Get local IP address automatically
function getLocalIP() {
  const interfaces = os.networkInterfaces();
  for (const name of Object.keys(interfaces)) {
    for (const interface of interfaces[name]) {
      if (interface.family === 'IPv4' && !interface.internal) {
        return interface.address;
      }
    }
  }
  return '10.0.0.100'; // fallback
}

const LOCAL_IP = getLocalIP();

// Local domain configurations for testing
const LOCAL_DOMAIN_CONFIGS = {
  // Hell theme - accessible via localhost:5571 and LOCAL_IP:5571
  'hell': {
    name: 'A Short Stay in Hell',
    subtitle: 'The Infinite Library of Torment',
    theme: 'infernal',
    colors: {
      primary: '#dc2626',     // Hell red
      secondary: '#991b1b',   // Dark red
      accent: '#fbbf24',      // Hellfire gold
      background: '#1c1917',  // Burnt black
      text: '#f3f4f6'         // Ash white
    },
    motto: 'In infinite corridors, every soul finds its perfect torment',
    description: 'Navigate the endless hellish archives where every book contains both revelation and damnation',
    mode: 'infernal-enhanced',
    seekerEnabled: true,
    port: 5571,
    urls: [`localhost:5571`, `${LOCAL_IP}:5571`]
  },
  
  // Mystical theme - accessible via localhost:5572 and LOCAL_IP:5572
  'quest': {
    name: 'The Library of Babel',
    subtitle: 'Quest for Infinite Knowledge',
    theme: 'mystical',
    colors: {
      primary: '#a16207',     // Ancient gold
      secondary: '#92400e',   // Deep gold
      accent: '#64748b',      // Mystic silver
      background: '#0f172a',  // Infinite depths
      text: '#f1f5f9'         // Parchment white
    },
    motto: 'Every truth awaits its destined seeker',
    description: 'Explore the infinite hexagonal galleries where all knowledge dwells in perfect mathematical harmony',
    mode: 'mystical-educational',
    seekerEnabled: true,
    port: 5572,
    urls: [`localhost:5572`, `${LOCAL_IP}:5572`]
  }
};

// Create local app instance
function createLocalServer(themeKey, config) {
  const app = express();
  const domainConfig = config;
  
  // Initialize engines
  const contentGenerator = new BabelContentGenerator();
  const searchEngine = new BabelSearchEngine();
  
  // Middleware
  app.use(express.json({ limit: '10mb' }));
  app.use(express.urlencoded({ extended: true }));
  app.use(cors({
    origin: ['http://localhost:3000', `http://${LOCAL_IP}:3000`, '*'],
    credentials: true
  }));
  
  // Local middleware
  app.use((req, res, next) => {
    req.domain = req.get('host') || `localhost:${config.port}`;
    req.domainConfig = domainConfig;
    req.theme = themeKey;
    
    // Check for seeker mode
    const seekerKey = process.env.SEEKER_MODE_KEY || 'the_librarian_who_knows';
    if (req.query.seekermode === seekerKey && domainConfig.seekerEnabled) {
      req.seekerMode = true;
      req.enhancedAccess = true;
    }
    
    // Hell theme gets enhanced by default for testing
    if (themeKey === 'hell') {
      req.defaultEnhancedMode = true;
    }
    
    next();
  });
  
  // Serve static files (if frontend is built)
  const frontendPath = path.join(__dirname, '../../frontend/build');
  app.use(express.static(frontendPath));
  
  /**
   * GET /api/local/info
   * Local server information
   */
  app.get('/api/local/info', (req, res) => {
    res.json({
      server: 'Local Library of Babel',
      theme: themeKey,
      localIP: LOCAL_IP,
      accessUrls: domainConfig.urls.map(url => `http://${url}`),
      config: domainConfig,
      features: {
        localTesting: true,
        networkAccess: true,
        seekerMode: true,
        enhancedMode: true
      }
    });
  });
  
  /**
   * GET /api/library/info
   * Enhanced library info with local theming
   */
  app.get('/api/library/info', (req, res) => {
    res.json({
      name: domainConfig.name,
      subtitle: domainConfig.subtitle,
      description: domainConfig.description,
      motto: domainConfig.motto,
      theme: domainConfig.theme,
      localAccess: {
        localhost: `http://localhost:${config.port}`,
        networkIP: `http://${LOCAL_IP}:${config.port}`,
        seekerMode: `?seekermode=${process.env.SEEKER_MODE_KEY}`
      },
      mode: req.seekerMode ? 'seeker' : domainConfig.mode,
      features: {
        proceduralGeneration: true,
        infiniteSpace: true,
        deterministicContent: true,
        localTesting: true,
        seekerMode: req.seekerMode || false,
        enhancedMode: req.defaultEnhancedMode || false
      },
      statistics: {
        maxBooks: config.library?.procedural?.maxBooks || 999999999,
        averageWordsPerBook: 4200,
        availableConcepts: 30,
        availableFields: 22
      },
      styling: domainConfig.colors,
      version: '2.0.0-local'
    });
  });
  
  /**
   * POST /api/search
   * Local search with theming
   */
  app.post('/api/search', async (req, res) => {
    try {
      const { query, mode = 'comprehensive', maxResults = 10 } = req.body;
      
      if (!query || query.trim().length === 0) {
        return res.status(400).json({
          error: 'Search query is required',
          message: domainConfig.theme === 'infernal' 
            ? 'Speak your torment clearly, or remain silent in the flames'
            : 'Please provide a search query to explore the library',
          theme: domainConfig.theme
        });
      }
      
      // For local testing, use procedural generation
      const searchResults = await searchEngine.search(query, {
        maxResults,
        mode: mode === 'enhanced' ? 'comprehensive' : mode,
        includeContent: true
      });
      
      // Apply theme-specific transformations
      searchResults.results = searchResults.results.map(result => ({
        ...result,
        domainTheme: domainConfig.theme,
        themedTitle: domainConfig.theme === 'infernal' 
          ? `The Damned Treatise: ${result.title}`
          : result.title,
        themedAuthor: domainConfig.theme === 'infernal'
          ? `${result.author} (Soul #${Math.floor(Math.random() * 999999)})`
          : result.author,
        localAccess: true
      }));
      
      const response = {
        query,
        results: searchResults.results,
        metadata: {
          ...searchResults.metadata,
          theme: domainConfig.theme,
          localServer: true,
          seekerMode: req.seekerMode || false,
          accessUrl: `http://${req.get('host')}`
        },
        educational: {
          concept: domainConfig.theme === 'infernal'
            ? 'Welcome to the local hellish archives - test the infinite torment safely!'
            : 'Local Library of Babel - explore infinite knowledge from your network!',
          note: `Local testing mode - running on ${req.get('host')}`,
          philosophy: domainConfig.motto,
          localTesting: true
        },
        theming: {
          colors: domainConfig.colors,
          theme: domainConfig.theme,
          name: domainConfig.name
        }
      };
      
      res.json(response);
      
    } catch (error) {
      console.error('Local search error:', error);
      res.status(500).json({
        error: 'Local library search failed',
        message: domainConfig.theme === 'infernal'
          ? 'The local infernal archives are experiencing technical difficulties'
          : 'The local infinite corridors seem temporarily obscured',
        theme: domainConfig.theme
      });
    }
  });
  
  /**
   * GET /api/network/scan
   * Show all available access points
   */
  app.get('/api/network/scan', (req, res) => {
    res.json({
      localIP: LOCAL_IP,
      availableServers: {
        hell: {
          localhost: 'http://localhost:5571',
          network: `http://${LOCAL_IP}:5571`,
          theme: 'Infernal Archives',
          seekerUrl: `http://localhost:5571?seekermode=${process.env.SEEKER_MODE_KEY}`
        },
        quest: {
          localhost: 'http://localhost:5572', 
          network: `http://${LOCAL_IP}:5572`,
          theme: 'Mystical Library',
          seekerUrl: `http://localhost:5572?seekermode=${process.env.SEEKER_MODE_KEY}`
        }
      },
      instructions: {
        localhost: 'Access from this Mac',
        network: 'Access from other devices on same network',
        seeker: 'Add seeker parameter for enhanced features'
      }
    });
  });
  
  // Health endpoint
  app.get('/api/health', (req, res) => {
    res.json({
      status: 'healthy',
      theme: themeKey,
      localIP: LOCAL_IP,
      accessUrls: domainConfig.urls.map(url => `http://${url}`),
      version: 'local-2.0.0'
    });
  });
  
  // Serve React app for all non-API routes
  app.get('*', (req, res) => {
    const indexPath = path.join(__dirname, '../../frontend/build/index.html');
    if (require('fs').existsSync(indexPath)) {
      res.sendFile(indexPath);
    } else {
      res.json({
        message: 'Library of Babel API is running!',
        theme: domainConfig.name,
        buildFrontend: 'Run: cd frontend && npm run build',
        accessAPI: `http://${req.get('host')}/api/library/info`
      });
    }
  });
  
  return app;
}

// Create both servers
const hellServer = createLocalServer('hell', LOCAL_DOMAIN_CONFIGS.hell);
const questServer = createLocalServer('quest', LOCAL_DOMAIN_CONFIGS.quest);

// Start servers
hellServer.listen(5571, '0.0.0.0', () => {
  console.log(`\\n🔥 A Short Stay in Hell - Local Testing Server`);
  console.log(`🌐 Localhost: http://localhost:5571`);
  console.log(`🏠 Network: http://${LOCAL_IP}:5571`);
  console.log(`🔍 Seeker: http://localhost:5571?seekermode=the_librarian_who_knows`);
  console.log(`👹 Theme: Infernal Archives (Red/Black)`);
  console.log(`🔥 Enhanced mode enabled by default`);
});

questServer.listen(5572, '0.0.0.0', () => {
  console.log(`\\n✨ Library of Babel - Local Testing Server`);
  console.log(`🌐 Localhost: http://localhost:5572`);
  console.log(`🏠 Network: http://${LOCAL_IP}:5572`);
  console.log(`🔍 Seeker: http://localhost:5572?seekermode=the_librarian_who_knows`);
  console.log(`🔮 Theme: Mystical Knowledge (Gold/Blue)`);
  console.log(`📚 Educational mode by default`);
});

console.log(`\\n🎭 Local Dual-Domain Library of Babel Ready!`);
console.log(`📱 Access from any device on your network:`);
console.log(`   Hell: http://${LOCAL_IP}:5571`);
console.log(`   Quest: http://${LOCAL_IP}:5572`);
console.log(`\\n🔍 Network scan: http://localhost:5571/api/network/scan`);
console.log(`\\n🏠 Perfect for testing before Cloudflare deployment!\\n`);

module.exports = { hellServer, questServer };