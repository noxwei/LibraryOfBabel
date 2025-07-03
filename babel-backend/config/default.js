// Configuration for Library of Babel Backend
// Educational demonstration of Borges' infinite library concept

module.exports = {
  server: {
    port: process.env.PORT || 5570,
    host: process.env.HOST || 'localhost'
  },
  
  // Library modes for different educational contexts
  library: {
    mode: process.env.LIBRARY_MODE || 'educational', // 'educational' | 'enhanced'
    
    // Procedural generation settings
    procedural: {
      maxBooks: 999999999, // Simulate infinite library
      averageWordsPerBook: 4200, // Average book length
      chaptersPerBook: 12, // Average chapters
      hexagonalSeed: 'borges-1962', // Base seed for reproducible content
      
      // Content generation parameters
      titleTemplates: [
        'Meditations on {concept}',
        'The {adjective} {noun}',
        'Studies in {field}',
        'On the Nature of {concept}',
        'The {adjective} Foundation of {concept}',
        'Concerning {concept} and {concept}',
        'The {concept} Paradox',
        'Elements of {field}',
        'The {adjective} Guide to {concept}',
        'Reflections on {concept}'
      ],
      
      // Academic fields for content generation
      academicFields: [
        'Metaphysics', 'Epistemology', 'Logic', 'Ethics', 'Aesthetics',
        'Hermeneutics', 'Phenomenology', 'Ontology', 'Dialectics',
        'Semiotics', 'Linguistics', 'Philology', 'Historiography',
        'Mathematics', 'Geometry', 'Topology', 'Set Theory',
        'Literary Theory', 'Narrative Analysis', 'Textual Criticism',
        'Comparative Literature', 'Poetics', 'Rhetoric'
      ],
      
      // Philosophical concepts for content
      concepts: [
        'infinity', 'recursion', 'paradox', 'universals', 'particulars',
        'identity', 'difference', 'unity', 'multiplicity', 'being',
        'nothingness', 'time', 'eternity', 'space', 'causality',
        'necessity', 'possibility', 'knowledge', 'ignorance', 'truth',
        'falsehood', 'reality', 'appearance', 'form', 'content',
        'meaning', 'interpretation', 'language', 'silence', 'order',
        'chaos', 'pattern', 'randomness', 'structure', 'function'
      ],
      
      // Descriptive adjectives for academic works
      adjectives: [
        'Essential', 'Fundamental', 'Critical', 'Analytical', 'Systematic',
        'Comprehensive', 'Definitive', 'Preliminary', 'Advanced', 'Elementary',
        'Theoretical', 'Practical', 'Empirical', 'Rational', 'Intuitive',
        'Absolute', 'Relative', 'Universal', 'Particular', 'General',
        'Specific', 'Abstract', 'Concrete', 'Formal', 'Informal',
        'Sacred', 'Profane', 'Ancient', 'Modern', 'Classical'
      ]
    },
    
    // Enhanced mode settings for development/testing
    enhanced: {
      enabled: process.env.ENHANCED_MODE === 'true',
      realSearchApi: process.env.REAL_SEARCH_API || 'http://localhost:5560',
      fallbackToProceduralOnError: true,
      debugMode: process.env.DEBUG_MODE === 'true'
    }
  },
  
  // Search algorithm settings
  search: {
    maxResults: 20,
    relevanceThreshold: 0.1,
    semanticSearchEnabled: true,
    fuzzyMatchEnabled: true,
    
    // Procedural search parameters
    procedural: {
      diversityFactor: 0.7, // How diverse should results be
      serendipityFactor: 0.3, // How unexpected should results be
      scholarlySimilarity: 0.8 // How academic should results feel
    }
  },
  
  // Educational content parameters
  education: {
    includePhilosophicalNotes: true,
    includeLiteraryAnalysis: true,
    includeHistoricalContext: true,
    generateCitations: true,
    includeGlossary: true
  },
  
  // API configuration
  api: {
    version: 'v1',
    rateLimit: {
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 100 // requests per window
    },
    cors: {
      origin: process.env.FRONTEND_URL || 'http://localhost:3000',
      credentials: true
    }
  }
};