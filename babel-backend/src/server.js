/**
 * Library of Babel Backend Server
 * 
 * Educational demonstration of Borges' infinite library concept
 * with configurable modes for different use cases
 */

const express = require('express');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

// Import our core modules
const BabelContentGenerator = require('./generators/BabelContentGenerator');
const BabelSearchEngine = require('./search/BabelSearchEngine');
const config = require('../config/default');

// Initialize the application
const app = express();
const port = config.server.port;

// Initialize our engines
const contentGenerator = new BabelContentGenerator();
const searchEngine = new BabelSearchEngine();

// Middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));
app.use(cors(config.api.cors));

// Enhanced mode integration (for development/testing)
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
        return this.transformEnhancedResults(data);
      } catch (error) {
        console.warn('Enhanced mode API error:', error);
        if (config.library.enhanced.fallbackToProceduralOnError) {
          return await searchEngine.search(query, options);
        }
        throw error;
      }
    },
    
    transformEnhancedResults(data) {
      // Transform real API results to match our educational interface
      const results = [];
      
      // Process exact references
      if (data.exact_references?.results) {
        for (const result of data.exact_references.results) {
          results.push({
            id: result.chunk_id,
            title: result.title,
            author: result.author,
            type: 'enhanced_exact',
            content: result.content_preview || result.highlighted_content,
            relevanceScore: result.relevance_rank || 0.9,
            metadata: {
              source: 'enhanced_mode',
              chunkType: result.chunk_type,
              chapterNumber: result.chapter_number
            }
          });
        }
      }
      
      // Process semantic results
      if (data.semantic_discovery?.results) {
        for (const result of data.semantic_discovery.results) {
          results.push({
            id: result.chunk_id,
            title: result.title,
            author: result.author,
            type: 'enhanced_semantic',
            content: result.content_preview,
            relevanceScore: result.similarity_score || 0.8,
            metadata: {
              source: 'enhanced_mode',
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
          responseTime: data.query_metadata?.response_time_ms || 0,
          totalResults: results.length
        }
      };
    }
  };
}

// API Routes

/**
 * GET /api/library/info
 * Returns information about the current library configuration
 */
app.get('/api/library/info', (req, res) => {
  res.json({
    name: 'Library of Babel',
    description: 'Educational demonstration of Borges\' infinite library concept',
    mode: config.library.mode,
    features: {
      proceduralGeneration: true,
      infiniteSpace: true,
      deterministicContent: true,
      educationalPurpose: true,
      enhancedMode: config.library.enhanced.enabled
    },
    statistics: {
      maxBooks: config.library.procedural.maxBooks,
      averageWordsPerBook: config.library.procedural.averageWordsPerBook,
      chaptersPerBook: config.library.procedural.chaptersPerBook,
      availableConcepts: config.library.procedural.concepts.length,
      availableFields: config.library.procedural.academicFields.length
    },
    version: '1.0.0'
  });
});

/**
 * POST /api/search
 * Search the infinite library
 */
app.post('/api/search', async (req, res) => {
  try {
    const { query, mode = 'comprehensive', maxResults = 10 } = req.body;
    
    if (!query || query.trim().length === 0) {
      return res.status(400).json({
        error: 'Search query is required',
        message: 'Please provide a search query to explore the library'
      });
    }
    
    // Determine which search engine to use
    const useEnhanced = config.library.enhanced.enabled && 
                       (mode === 'enhanced' || req.query.mode === 'enhanced');
    
    let searchResults;
    
    if (useEnhanced && enhancedModeAPI) {
      searchResults = await enhancedModeAPI.search(query, {
        exact_limit: maxResults / 2,
        semantic_limit: maxResults / 2
      });
    } else {
      searchResults = await searchEngine.search(query, {
        maxResults,
        mode: mode === 'enhanced' ? 'comprehensive' : mode,
        includeContent: true
      });
    }
    
    // Add educational context
    const response = {
      query,
      results: searchResults.results || searchResults,
      metadata: {
        ...searchResults.metadata,
        library: {
          mode: useEnhanced ? 'enhanced' : 'educational',
          infinite: true,
          procedural: !useEnhanced,
          educational: true
        },
        search: {
          algorithm: useEnhanced ? 'enhanced_hybrid' : 'procedural_babel',
          timestamp: new Date().toISOString(),
          totalExplored: searchResults.metadata?.totalExplored || 0
        }
      },
      educational: {
        concept: 'This demonstrates Borges\' Library of Babel - an infinite library containing all possible books',
        note: useEnhanced ? 
          'Enhanced mode for development/testing - comparing with real search results' :
          'Procedural generation creates books deterministically based on coordinates',
        philosophy: 'Every search reveals both the sought knowledge and unexpected discoveries'
      }
    };
    
    res.json(response);
    
  } catch (error) {
    console.error('Search error:', error);
    res.status(500).json({
      error: 'Library search failed',
      message: 'The infinite corridors seem temporarily obscured',
      details: config.library.enhanced.debugMode ? error.message : undefined
    });
  }
});

/**
 * GET /api/book/:hexagon/:wall/:shelf/:volume
 * Retrieve a specific book from the library coordinates
 */
app.get('/api/book/:hexagon/:wall/:shelf/:volume', async (req, res) => {
  try {
    const { hexagon, wall, shelf, volume } = req.params;
    const { includeContent = true } = req.query;
    
    // Validate coordinates
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
        message: 'Coordinates must be: wall (0-5), shelf (0-4), volume (0-31)',
        provided: coords
      });
    }
    
    // Generate the book
    const book = contentGenerator.generateBook(
      coords.hexagon,
      coords.wall,
      coords.shelf,
      coords.volume
    );
    
    // Optionally exclude content for metadata-only requests
    if (!includeContent) {
      delete book.chapters;
      delete book.bibliography;
    }
    
    res.json({
      book,
      educational: {
        concept: 'Each book is generated deterministically from its coordinates',
        note: 'The same coordinates will always produce the same book',
        coordinates: `Hexagon ${hexagon}, Wall ${wall}, Shelf ${shelf}, Volume ${volume}`
      }
    });
    
  } catch (error) {
    console.error('Book generation error:', error);
    res.status(500).json({
      error: 'Book generation failed',
      message: 'Unable to retrieve book from these coordinates'
    });
  }
});

/**
 * GET /api/random-book
 * Get a random book from the library
 */
app.get('/api/random-book', async (req, res) => {
  try {
    const { includeContent = true } = req.query;
    
    // Generate random coordinates
    const coords = {
      hexagon: Math.floor(Math.random() * 1000000),
      wall: Math.floor(Math.random() * 6),
      shelf: Math.floor(Math.random() * 5),
      volume: Math.floor(Math.random() * 32)
    };
    
    const book = contentGenerator.generateBook(
      coords.hexagon,
      coords.wall,
      coords.shelf,
      coords.volume
    );
    
    if (!includeContent) {
      delete book.chapters;
      delete book.bibliography;
    }
    
    res.json({
      book,
      educational: {
        concept: 'Random exploration of the infinite library',
        note: 'Each random book demonstrates the vast scope of generated content',
        serendipity: 'Sometimes the most interesting discoveries are unexpected'
      }
    });
    
  } catch (error) {
    console.error('Random book error:', error);
    res.status(500).json({
      error: 'Random book generation failed',
      message: 'Unable to select random book'
    });
  }
});

/**
 * GET /api/concepts
 * Get available concepts for search
 */
app.get('/api/concepts', (req, res) => {
  res.json({
    concepts: config.library.procedural.concepts,
    academicFields: config.library.procedural.academicFields,
    adjectives: config.library.procedural.adjectives,
    educational: {
      concept: 'These are the conceptual building blocks of the library',
      note: 'Books are generated using combinations of these elements',
      usage: 'Search for any of these concepts to find relevant books'
    }
  });
});

/**
 * GET /api/explore/:concept
 * Explore books related to a specific concept
 */
app.get('/api/explore/:concept', async (req, res) => {
  try {
    const { concept } = req.params;
    const { limit = 5 } = req.query;
    
    // Validate concept
    if (!config.library.procedural.concepts.includes(concept)) {
      return res.status(400).json({
        error: 'Unknown concept',
        message: `Concept '${concept}' not found in library vocabulary`,
        availableConcepts: config.library.procedural.concepts
      });
    }
    
    // Search for books about this concept
    const searchResults = await searchEngine.search(concept, {
      maxResults: parseInt(limit),
      mode: 'comprehensive'
    });
    
    res.json({
      concept,
      books: searchResults.results,
      educational: {
        concept: `Exploring the library's treatment of '${concept}'`,
        note: 'Books are selected based on thematic relevance to the concept',
        philosophy: 'Each concept opens doorways to different regions of knowledge'
      }
    });
    
  } catch (error) {
    console.error('Concept exploration error:', error);
    res.status(500).json({
      error: 'Concept exploration failed',
      message: 'Unable to explore this concept'
    });
  }
});

/**
 * GET /api/health
 * Health check endpoint
 */
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    library: {
      mode: config.library.mode,
      enhancedMode: config.library.enhanced.enabled,
      infinite: true,
      ready: true
    },
    server: {
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      version: process.version
    }
  });
});

// Static file serving for educational documentation
app.use('/docs', express.static(path.join(__dirname, '../docs')));

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Server error:', err);
  res.status(500).json({
    error: 'Internal server error',
    message: 'The library experiences a temporary disturbance',
    details: config.library.enhanced.debugMode ? err.message : undefined
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Endpoint not found',
    message: 'This corridor of the library remains unexplored',
    availableEndpoints: [
      'GET /api/library/info',
      'POST /api/search',
      'GET /api/book/:hexagon/:wall/:shelf/:volume',
      'GET /api/random-book',
      'GET /api/concepts',
      'GET /api/explore/:concept',
      'GET /api/health'
    ]
  });
});

// Start the server
app.listen(port, config.server.host, () => {
  console.log(`\n🏛️  Library of Babel Backend Server\n`);
  console.log(`📚 Educational demonstration of Borges' infinite library concept`);
  console.log(`🌐 Server running at http://${config.server.host}:${port}`);
  console.log(`📖 Library Mode: ${config.library.mode}`);
  console.log(`🔧 Enhanced Mode: ${config.library.enhanced.enabled ? 'Enabled' : 'Disabled'}`);
  console.log(`🎯 Purpose: Educational exploration of infinite literary space`);
  console.log(`\n📋 Available endpoints:`);
  console.log(`   GET  /api/library/info - Library information`);
  console.log(`   POST /api/search - Search the infinite library`);
  console.log(`   GET  /api/book/:coords - Retrieve specific book`);
  console.log(`   GET  /api/random-book - Get random book`);
  console.log(`   GET  /api/concepts - Available concepts`);
  console.log(`   GET  /api/explore/:concept - Explore concept`);
  console.log(`   GET  /api/health - Health check`);
  console.log(`\n🎓 Educational Note:`);
  console.log(`   This system demonstrates Borges' Library of Babel concept`);
  console.log(`   through procedural generation of infinite literary content.`);
  console.log(`\n✨ Ready to explore the infinite library!\n`);
});

module.exports = app;