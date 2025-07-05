/**
 * Production Library of Babel Server with Domain-Specific Theming
 * 
 * Serves both ashortstayinhell.com (primary) and libraryofbabel.quest
 * with unique themes and seeker mode capabilities
 */

const express = require('express');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

// Import our core modules
const BabelContentGenerator = require('./generators/BabelContentGenerator');
const BabelSearchEngine = require('./search/BabelSearchEngine');
const config = require('../config/default');

// Domain-specific configurations (secure: no sensitive data)
const DOMAIN_CONFIGS = {
  [process.env.PRIMARY_DOMAIN || 'localhost:5571']: {
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
    seekerEnabled: process.env.SEEKER_MODE_ENABLED === 'true'
  },
  [process.env.SECONDARY_DOMAIN || 'localhost:5572']: {
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
    seekerEnabled: process.env.SEEKER_MODE_ENABLED === 'true'
  }
};

// Create app instances for each domain
function createDomainServer(domain, port) {
  const app = express();
  const domainConfig = DOMAIN_CONFIGS[domain];
  
  // Initialize engines
  const contentGenerator = new BabelContentGenerator();
  const searchEngine = new BabelSearchEngine();
  
  // Enhanced mode integration
  let enhancedModeAPI = null;
  if (config.library.enhanced.enabled) {
    const fetch = require('node-fetch');
    
    enhancedModeAPI = {
      async search(query, options = {}) {
        try {
          const response = await fetch(`${config.library.enhanced.realSearchApi}/api/hybrid-search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              query,
              exact_limit: options.exact_limit || 10,
              semantic_limit: options.semantic_limit || 8
            })
          });
          
          if (!response.ok) {
            throw new Error(`Enhanced API error: ${response.status}`);
          }
          
          const data = await response.json();
          return this.transformEnhancedResults(data, domain);
        } catch (error) {
          console.warn('Enhanced mode API error:', error);
          if (config.library.enhanced.fallbackToProceduralOnError) {
            return await searchEngine.search(query, options);
          }
          throw error;
        }
      },
      
      transformEnhancedResults(data, domain) {
        const results = [];
        const theme = domainConfig.theme;
        
        // Transform exact references with domain theming
        if (data.exact_references?.results) {
          for (const result of data.exact_references.results) {
            results.push({
              id: result.chunk_id,
              title: result.title,
              author: result.author,
              type: theme === 'infernal' ? 'damned_text' : 'sacred_text',
              content: result.content_preview || result.highlighted_content,
              relevanceScore: result.relevance_rank || 0.9,
              domainTheme: theme,
              metadata: {
                source: 'enhanced_mode',
                domain: domain,
                chunkType: result.chunk_type,
                chapterNumber: result.chapter_number
              }
            });
          }
        }
        
        // Transform semantic results
        if (data.semantic_discovery?.results) {
          for (const result of data.semantic_discovery.results) {
            results.push({
              id: result.chunk_id,
              title: result.title,
              author: result.author,
              type: theme === 'infernal' ? 'hellish_echo' : 'mystical_echo',
              content: result.content_preview,
              relevanceScore: result.similarity_score || 0.8,
              domainTheme: theme,
              metadata: {
                source: 'enhanced_mode',
                domain: domain,
                similarity: result.similarity_score,
                chunkType: result.chunk_type
              }
            });
          }
        }
        
        return {
          results,
          metadata: {
            searchType: 'enhanced',
            domain: domain,
            theme: theme,
            responseTime: data.query_metadata?.response_time_ms || 0,
            totalResults: results.length
          }
        };
      }
    };
  }
  
  // Middleware
  app.use(express.json({ limit: '10mb' }));
  app.use(express.urlencoded({ extended: true }));
  app.use(cors({
    origin: [`https://${domain}`, `http://${domain}`, 'http://localhost:3000'],
    credentials: true
  }));
  
  // Domain-aware middleware
  app.use((req, res, next) => {
    req.domain = domain;
    req.domainConfig = domainConfig;
    
    // Check for seeker mode (secure: use environment variable)
    const seekerKey = process.env.SEEKER_MODE_KEY || 'the_librarian_who_knows';
    if (req.query.seekermode === seekerKey && domainConfig.seekerEnabled) {
      req.seekerMode = true;
      req.enhancedAccess = true;
    }
    
    // Domain-specific enhanced mode (secure: use environment variables)
    if (domain === process.env.PRIMARY_DOMAIN) {
      req.defaultEnhancedMode = process.env.PRIMARY_ENHANCED_DEFAULT === 'true';
    }
    
    next();
  });
  
  // Serve static frontend files
  app.use(express.static(path.join(__dirname, '../../frontend/build')));
  
  /**
   * GET /api/domain/info
   * Returns domain-specific configuration and theming
   */
  app.get('/api/domain/info', (req, res) => {
    res.json({
      domain: domain,
      config: domainConfig,
      features: {
        proceduralGeneration: true,
        domainTheming: true,
        seekerMode: domainConfig.seekerEnabled,
        enhancedMode: config.library.enhanced.enabled,
        infiniteSpace: true
      },
      library: {
        mode: req.seekerMode ? 'seeker' : domainConfig.mode,
        enhancedAccess: req.enhancedAccess || false,
        theme: domainConfig.theme
      }
    });
  });
  
  /**
   * GET /api/library/info
   * Enhanced library info with domain theming
   */
  app.get('/api/library/info', (req, res) => {
    res.json({
      name: domainConfig.name,
      subtitle: domainConfig.subtitle,
      description: domainConfig.description,
      motto: domainConfig.motto,
      domain: domain,
      theme: domainConfig.theme,
      mode: req.seekerMode ? 'seeker' : config.library.mode,
      features: {
        proceduralGeneration: true,
        infiniteSpace: true,
        deterministicContent: true,
        domainTheming: true,
        seekerMode: req.seekerMode || false,
        enhancedMode: config.library.enhanced.enabled
      },
      statistics: {
        maxBooks: config.library.procedural.maxBooks,
        averageWordsPerBook: config.library.procedural.averageWordsPerBook,
        chaptersPerBook: config.library.procedural.chaptersPerBook,
        availableConcepts: config.library.procedural.concepts.length,
        availableFields: config.library.procedural.academicFields.length
      },
      styling: domainConfig.colors,
      version: '2.0.0-production'
    });
  });
  
  /**
   * POST /api/search
   * Domain-aware search with theming and seeker mode
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
          domain: domain
        });
      }
      
      // Determine search mode based on domain and seeker status
      let searchMode = mode;
      let useEnhanced = false;
      
      if (req.seekerMode || req.defaultEnhancedMode) {
        useEnhanced = config.library.enhanced.enabled && enhancedModeAPI;
        searchMode = 'enhanced';
      }
      
      let searchResults;
      
      if (useEnhanced) {
        searchResults = await enhancedModeAPI.search(query, {
          exact_limit: maxResults / 2,
          semantic_limit: maxResults / 2
        });
      } else {
        searchResults = await searchEngine.search(query, {
          maxResults,
          mode: searchMode === 'enhanced' ? 'comprehensive' : searchMode,
          includeContent: true
        });
        
        // Apply domain theming to procedural results
        searchResults.results = searchResults.results.map(result => ({
          ...result,
          domainTheme: domainConfig.theme,
          themedTitle: domainConfig.theme === 'infernal' 
            ? `The Damned Treatise: ${result.title}`
            : result.title,
          themedAuthor: domainConfig.theme === 'infernal'
            ? `${result.author} (Soul #${Math.floor(Math.random() * 999999)})`
            : result.author
        }));
      }
      
      // Enhanced response with domain theming
      const response = {
        query,
        results: searchResults.results || searchResults,
        metadata: {
          ...searchResults.metadata,
          domain: domain,
          theme: domainConfig.theme,
          seekerMode: req.seekerMode || false,
          library: {
            mode: useEnhanced ? 'enhanced' : 'educational',
            infinite: true,
            procedural: !useEnhanced,
            domain: domain,
            theme: domainConfig.theme
          },
          search: {
            algorithm: useEnhanced ? 'enhanced_hybrid' : 'procedural_babel',
            timestamp: new Date().toISOString(),
            totalExplored: searchResults.metadata?.totalExplored || 0
          }
        },
        educational: {
          concept: domainConfig.theme === 'infernal'
            ? 'Welcome to the infinite hellish archives where every book contains both knowledge and torment'
            : 'This demonstrates Borges\\' Library of Babel - an infinite library containing all possible books',
          note: useEnhanced 
            ? `Seeker mode activated - accessing enhanced ${domain} archives`
            : `Procedural generation creates books deterministically for ${domain}`,
          philosophy: domainConfig.motto,
          domain: domain
        },
        theming: {
          colors: domainConfig.colors,
          theme: domainConfig.theme,
          name: domainConfig.name
        }
      };
      
      res.json(response);
      
    } catch (error) {
      console.error('Search error:', error);
      res.status(500).json({
        error: 'Library search failed',
        message: domainConfig.theme === 'infernal'
          ? 'The infernal archives burn with errors - your query is lost in flames'
          : 'The infinite corridors seem temporarily obscured',
        domain: domain,
        details: config.library.enhanced.debugMode ? error.message : undefined
      });
    }
  });
  
  // All other existing endpoints with domain theming...
  // (book retrieval, random book, concepts, etc.)
  
  /**
   * GET /api/book/:hexagon/:wall/:shelf/:volume
   * Domain-themed book retrieval
   */
  app.get('/api/book/:hexagon/:wall/:shelf/:volume', async (req, res) => {
    try {
      const { hexagon, wall, shelf, volume } = req.params;
      const { includeContent = true } = req.query;
      
      const coords = {
        hexagon: parseInt(hexagon),
        wall: parseInt(wall),
        shelf: parseInt(shelf),
        volume: parseInt(volume)
      };
      
      if (coords.wall < 0 || coords.wall > 5 ||
          coords.shelf < 0 || coords.shelf > 4 ||
          coords.volume < 0 || coords.volume > 31) {
        return res.status(400).json({
          error: 'Invalid library coordinates',
          message: domainConfig.theme === 'infernal'
            ? 'These coordinates lead only to empty flames - choose your path more wisely'
            : 'Coordinates must be: wall (0-5), shelf (0-4), volume (0-31)',
          provided: coords,
          domain: domain
        });
      }
      
      const book = contentGenerator.generateBook(
        coords.hexagon,
        coords.wall,
        coords.shelf,
        coords.volume
      );
      
      // Apply domain theming
      if (domainConfig.theme === 'infernal') {
        book.title = `The Damned Treatise: ${book.title}`;
        book.author = `${book.author} (Condemned Soul)`;
        book.genre = `Infernal ${book.genre}`;
      }
      
      if (!includeContent) {
        delete book.chapters;
        delete book.bibliography;
      }
      
      res.json({
        book,
        educational: {
          concept: domainConfig.theme === 'infernal'
            ? 'Each book in hell is generated deterministically - your torment is perfectly reproducible'
            : 'Each book is generated deterministically from its coordinates',
          note: domainConfig.theme === 'infernal'
            ? 'The same coordinates always lead to the same damnation'
            : 'The same coordinates will always produce the same book',
          coordinates: `${domainConfig.name}: Hexagon ${hexagon}, Wall ${wall}, Shelf ${shelf}, Volume ${volume}`,
          domain: domain
        },
        theming: {
          colors: domainConfig.colors,
          theme: domainConfig.theme
        }
      });
      
    } catch (error) {
      console.error('Book generation error:', error);
      res.status(500).json({
        error: 'Book generation failed',
        message: domainConfig.theme === 'infernal'
          ? 'This tome burns too brightly to be retrieved'
          : 'Unable to retrieve book from these coordinates',
        domain: domain
      });
    }
  });
  
  /**
   * GET /api/health
   * Domain-aware health check
   */
  app.get('/api/health', (req, res) => {
    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      domain: domain,
      library: {
        name: domainConfig.name,
        theme: domainConfig.theme,
        mode: req.seekerMode ? 'seeker' : config.library.mode,
        enhancedMode: config.library.enhanced.enabled,
        infinite: true,
        ready: true
      },
      server: {
        port: port,
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        version: process.version
      },
      theming: domainConfig.colors
    });
  });
  
  // Serve React app for all non-API routes
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '../../frontend/build/index.html'));
  });
  
  // Error handling
  app.use((err, req, res, next) => {
    console.error('Server error:', err);
    res.status(500).json({
      error: 'Internal server error',
      message: domainConfig.theme === 'infernal'
        ? 'The infernal servers burn with unexpected errors'
        : 'The library experiences a temporary disturbance',
      domain: domain,
      details: config.library.enhanced.debugMode ? err.message : undefined
    });
  });
  
  return app;
}

// Create and start both domain servers
const hellServer = createDomainServer('ashortstayinhell.com', 5571);
const questServer = createDomainServer('libraryofbabel.quest', 5572);

hellServer.listen(5571, 'localhost', () => {
  console.log(`\\n🔥 A Short Stay in Hell - Infernal Library Server`);
  console.log(`🌐 Domain: ashortstayinhell.com`);
  console.log(`🔗 Local: http://localhost:5571`);
  console.log(`👹 Theme: Infernal Archives`);
  console.log(`🔥 "In infinite corridors, every soul finds its perfect torment"`);
});

questServer.listen(5572, 'localhost', () => {
  console.log(`\\n✨ Library of Babel - Mystical Quest Server`);
  console.log(`🌐 Domain: libraryofbabel.quest`);
  console.log(`🔗 Local: http://localhost:5572`);
  console.log(`🔮 Theme: Mystical Knowledge`);
  console.log(`✨ "Every truth awaits its destined seeker"`);
});

console.log(`\\n🎭 Dual-Domain Library of Babel Servers Operational!`);
console.log(`🔥 Hell Mode: Enhanced by default, seeker mode available`);
console.log(`✨ Quest Mode: Educational with seeker mode available`);
console.log(`🔍 Seeker Mode: Add ?seekermode=the_librarian_who_knows to any domain`);
console.log(`\\n🚀 Ready for Cloudflare Tunnel deployment!\\n`);

module.exports = { hellServer, questServer };