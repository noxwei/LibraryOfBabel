/**
 * BabelSearchEngine - Search algorithm for procedural infinite library
 * 
 * This module implements intelligent search across the infinite procedural
 * library space, using mathematical techniques to find relevant content
 * without pre-indexing the entire infinite space.
 * 
 * Search Strategy:
 * 1. Concept-based coordinate mapping
 * 2. Semantic similarity calculation
 * 3. Deterministic exploration with serendipity
 * 4. Relevance scoring with diversity optimization
 */

const BabelContentGenerator = require('../generators/BabelContentGenerator');
const config = require('../../config/default');

class BabelSearchEngine {
  constructor() {
    this.generator = new BabelContentGenerator();
    this.config = config.search;
    this.conceptIndex = this.buildConceptIndex();
  }

  /**
   * Primary search method that finds relevant books in the infinite library
   * 
   * @param {string} query - Search query
   * @param {Object} options - Search options
   * @returns {Object} Search results with relevance scores
   */
  async search(query, options = {}) {
    const searchOptions = {
      maxResults: options.maxResults || this.config.maxResults,
      mode: options.mode || 'comprehensive', // 'precise', 'exploratory', 'comprehensive'
      includeContent: options.includeContent || false,
      diversityWeight: options.diversityWeight || 0.7,
      ...options
    };

    // Parse and analyze the query
    const queryAnalysis = this.analyzeQuery(query);
    
    // Generate search coordinates using concept mapping
    const searchCoordinates = this.generateSearchCoordinates(queryAnalysis);
    
    // Explore the library space around these coordinates
    const candidateBooks = await this.exploreLibrarySpace(searchCoordinates, searchOptions);
    
    // Score and rank results
    const rankedResults = this.rankResults(candidateBooks, queryAnalysis, searchOptions);
    
    // Apply diversity optimization
    const diverseResults = this.optimizeForDiversity(rankedResults, searchOptions);
    
    return {
      query,
      results: diverseResults.slice(0, searchOptions.maxResults),
      metadata: {
        totalExplored: candidateBooks.length,
        searchSpace: searchCoordinates.length,
        queryAnalysis,
        searchTime: Date.now(),
        algorithm: 'BabelSearchEngine v1.0'
      }
    };
  }

  /**
   * Analyze search query to extract concepts and intent
   * 
   * @param {string} query - Search query
   * @returns {Object} Query analysis results
   */
  analyzeQuery(query) {
    const words = query.toLowerCase().split(/\s+/);
    const concepts = [];
    const fields = [];
    const adjectives = [];
    const unknownTerms = [];

    for (const word of words) {
      if (this.generator.config.concepts.includes(word)) {
        concepts.push(word);
      } else if (this.generator.config.academicFields.includes(word)) {
        fields.push(word);
      } else if (this.generator.config.adjectives.includes(word)) {
        adjectives.push(word);
      } else {
        unknownTerms.push(word);
      }
    }

    return {
      originalQuery: query,
      concepts,
      fields,
      adjectives,
      unknownTerms,
      queryType: this.determineQueryType(concepts, fields, adjectives),
      searchComplexity: this.calculateSearchComplexity(words.length, concepts.length, fields.length)
    };
  }

  /**
   * Generate search coordinates in the library space based on query analysis
   * 
   * @param {Object} queryAnalysis - Analyzed query
   * @returns {Array} Array of coordinate sets to explore
   */
  generateSearchCoordinates(queryAnalysis) {
    const coordinates = [];
    const { concepts, fields, adjectives } = queryAnalysis;
    
    // Generate primary coordinates based on concepts
    for (const concept of concepts) {
      const conceptCoords = this.conceptToCoordinates(concept);
      coordinates.push(...conceptCoords);
    }
    
    // Generate secondary coordinates based on fields
    for (const field of fields) {
      const fieldCoords = this.fieldToCoordinates(field);
      coordinates.push(...fieldCoords);
    }
    
    // Generate tertiary coordinates for exploration
    const explorationCoords = this.generateExplorationCoordinates(queryAnalysis);
    coordinates.push(...explorationCoords);
    
    // Remove duplicates and sort by relevance
    const uniqueCoords = this.deduplicateCoordinates(coordinates);
    
    return uniqueCoords.slice(0, 100); // Limit exploration space
  }

  /**
   * Map concept to library coordinates using deterministic hashing
   * 
   * @param {string} concept - Concept to map
   * @returns {Array} Array of coordinate objects
   */
  conceptToCoordinates(concept) {
    const hash = this.hashString(concept);
    const coordinates = [];
    
    // Generate multiple coordinate sets per concept for better coverage
    for (let i = 0; i < 5; i++) {
      const hexagon = (hash + i * 1000) % 1000000;
      const wall = (hash + i * 100) % 6;
      const shelf = (hash + i * 10) % 5;
      const volume = (hash + i) % 32;
      
      coordinates.push({
        hexagon,
        wall,
        shelf,
        volume,
        source: 'concept',
        relevance: 1.0 - (i * 0.1)
      });
    }
    
    return coordinates;
  }

  /**
   * Map academic field to library coordinates
   * 
   * @param {string} field - Academic field
   * @returns {Array} Array of coordinate objects
   */
  fieldToCoordinates(field) {
    const hash = this.hashString(field + '-field');
    const coordinates = [];
    
    for (let i = 0; i < 3; i++) {
      const hexagon = (hash + i * 2000) % 1000000;
      const wall = (hash + i * 200) % 6;
      const shelf = (hash + i * 20) % 5;
      const volume = (hash + i * 2) % 32;
      
      coordinates.push({
        hexagon,
        wall,
        shelf,
        volume,
        source: 'field',
        relevance: 0.8 - (i * 0.1)
      });
    }
    
    return coordinates;
  }

  /**
   * Generate exploration coordinates for serendipitous discovery
   * 
   * @param {Object} queryAnalysis - Query analysis
   * @returns {Array} Array of exploration coordinates
   */
  generateExplorationCoordinates(queryAnalysis) {
    const coordinates = [];
    const baseHash = this.hashString(queryAnalysis.originalQuery);
    
    // Generate coordinates in nearby library regions
    for (let i = 0; i < 20; i++) {
      const hexagon = (baseHash + i * 12345) % 1000000;
      const wall = (baseHash + i * 67) % 6;
      const shelf = (baseHash + i * 13) % 5;
      const volume = (baseHash + i * 7) % 32;
      
      coordinates.push({
        hexagon,
        wall,
        shelf,
        volume,
        source: 'exploration',
        relevance: 0.3 + (Math.random() * 0.4) // Serendipity factor
      });
    }
    
    return coordinates;
  }

  /**
   * Explore the library space around given coordinates
   * 
   * @param {Array} coordinates - Coordinates to explore
   * @param {Object} options - Search options
   * @returns {Array} Array of candidate books
   */
  async exploreLibrarySpace(coordinates, options) {
    const candidateBooks = [];
    
    for (const coord of coordinates) {
      try {
        const book = this.generator.generateBook(
          coord.hexagon,
          coord.wall,
          coord.shelf,
          coord.volume
        );
        
        // Add coordinate-based relevance
        book.coordinateRelevance = coord.relevance;
        book.searchSource = coord.source;
        
        candidateBooks.push(book);
        
        // Also explore adjacent volumes for better coverage
        if (candidateBooks.length < 200) {
          const adjacentBooks = this.exploreAdjacentVolumes(coord, 2);
          candidateBooks.push(...adjacentBooks);
        }
        
      } catch (error) {
        console.warn(`Error generating book at coordinate ${coord.hexagon}.${coord.wall}.${coord.shelf}.${coord.volume}:`, error);
      }
    }
    
    return candidateBooks;
  }

  /**
   * Explore adjacent volumes in the library
   * 
   * @param {Object} coord - Base coordinate
   * @param {number} radius - Exploration radius
   * @returns {Array} Array of adjacent books
   */
  exploreAdjacentVolumes(coord, radius) {
    const adjacent = [];
    
    for (let v = -radius; v <= radius; v++) {
      if (v === 0) continue; // Skip the original coordinate
      
      const newVolume = (coord.volume + v + 32) % 32;
      try {
        const book = this.generator.generateBook(
          coord.hexagon,
          coord.wall,
          coord.shelf,
          newVolume
        );
        
        book.coordinateRelevance = coord.relevance * 0.8;
        book.searchSource = 'adjacent';
        
        adjacent.push(book);
      } catch (error) {
        // Skip problematic coordinates
      }
    }
    
    return adjacent;
  }

  /**
   * Rank search results by relevance to query
   * 
   * @param {Array} books - Candidate books
   * @param {Object} queryAnalysis - Query analysis
   * @param {Object} options - Search options
   * @returns {Array} Ranked results
   */
  rankResults(books, queryAnalysis, options) {
    const rankedBooks = books.map(book => {
      const relevanceScore = this.calculateRelevanceScore(book, queryAnalysis);
      const qualityScore = this.calculateQualityScore(book);
      const noveltyScore = this.calculateNoveltyScore(book);
      
      const finalScore = (
        relevanceScore * 0.6 +
        qualityScore * 0.3 +
        noveltyScore * 0.1
      );
      
      return {
        ...book,
        relevanceScore,
        qualityScore,
        noveltyScore,
        finalScore
      };
    });
    
    return rankedBooks.sort((a, b) => b.finalScore - a.finalScore);
  }

  /**
   * Calculate relevance score for a book
   * 
   * @param {Object} book - Book to score
   * @param {Object} queryAnalysis - Query analysis
   * @returns {number} Relevance score (0-1)
   */
  calculateRelevanceScore(book, queryAnalysis) {
    let score = 0;
    
    // Title relevance
    const titleScore = this.calculateTextRelevance(book.title, queryAnalysis);
    score += titleScore * 0.4;
    
    // Abstract relevance
    const abstractScore = this.calculateTextRelevance(book.abstract, queryAnalysis);
    score += abstractScore * 0.3;
    
    // Chapter titles relevance
    const chapterScore = book.chapters.reduce((sum, chapter) => {
      return sum + this.calculateTextRelevance(chapter.title, queryAnalysis);
    }, 0) / book.chapters.length;
    score += chapterScore * 0.2;
    
    // Coordinate relevance
    score += (book.coordinateRelevance || 0) * 0.1;
    
    return Math.min(1.0, score);
  }

  /**
   * Calculate text relevance to query
   * 
   * @param {string} text - Text to analyze
   * @param {Object} queryAnalysis - Query analysis
   * @returns {number} Text relevance score (0-1)
   */
  calculateTextRelevance(text, queryAnalysis) {
    const words = text.toLowerCase().split(/\s+/);
    let matches = 0;
    let totalTerms = 0;
    
    // Check for concept matches
    for (const concept of queryAnalysis.concepts) {
      totalTerms++;
      if (words.includes(concept)) {
        matches += 1.0;
      } else if (words.some(word => word.includes(concept) || concept.includes(word))) {
        matches += 0.5;
      }
    }
    
    // Check for field matches
    for (const field of queryAnalysis.fields) {
      totalTerms++;
      if (words.includes(field.toLowerCase())) {
        matches += 0.8;
      } else if (words.some(word => word.includes(field.toLowerCase()))) {
        matches += 0.4;
      }
    }
    
    // Check for adjective matches
    for (const adjective of queryAnalysis.adjectives) {
      totalTerms++;
      if (words.includes(adjective)) {
        matches += 0.6;
      }
    }
    
    return totalTerms > 0 ? matches / totalTerms : 0;
  }

  /**
   * Calculate quality score for a book
   * 
   * @param {Object} book - Book to evaluate
   * @returns {number} Quality score (0-1)
   */
  calculateQualityScore(book) {
    let score = 0;
    
    // Length appropriateness
    const wordCount = book.wordCount;
    if (wordCount >= 2000 && wordCount <= 10000) {
      score += 0.3;
    } else if (wordCount >= 1000 && wordCount <= 15000) {
      score += 0.2;
    } else {
      score += 0.1;
    }
    
    // Chapter structure
    const chapterCount = book.chapters.length;
    if (chapterCount >= 6 && chapterCount <= 15) {
      score += 0.3;
    } else if (chapterCount >= 3 && chapterCount <= 20) {
      score += 0.2;
    } else {
      score += 0.1;
    }
    
    // Bibliography quality
    const bibCount = book.bibliography.length;
    if (bibCount >= 5 && bibCount <= 20) {
      score += 0.2;
    } else if (bibCount >= 2 && bibCount <= 30) {
      score += 0.1;
    }
    
    // Temporal relevance
    const currentYear = new Date().getFullYear();
    const age = currentYear - book.publicationYear;
    if (age <= 10) {
      score += 0.2;
    } else if (age <= 50) {
      score += 0.1;
    }
    
    return Math.min(1.0, score);
  }

  /**
   * Calculate novelty score for diversity
   * 
   * @param {Object} book - Book to evaluate
   * @returns {number} Novelty score (0-1)
   */
  calculateNoveltyScore(book) {
    // Simple novelty based on coordinate position
    const coord = book.coordinates;
    const novelty = (coord.hexagon % 1000) / 1000;
    
    return novelty;
  }

  /**
   * Optimize results for diversity
   * 
   * @param {Array} rankedResults - Ranked results
   * @param {Object} options - Search options
   * @returns {Array} Diversified results
   */
  optimizeForDiversity(rankedResults, options) {
    const diverseResults = [];
    const usedAuthors = new Set();
    const usedGenres = new Set();
    
    for (const book of rankedResults) {
      if (diverseResults.length >= options.maxResults) break;
      
      // Apply diversity constraints
      const authorDiversity = !usedAuthors.has(book.author) ? 0.2 : 0;
      const genreDiversity = !usedGenres.has(book.genre) ? 0.1 : 0;
      
      const diversityBonus = authorDiversity + genreDiversity;
      book.finalScore += diversityBonus * options.diversityWeight;
      
      diverseResults.push(book);
      usedAuthors.add(book.author);
      usedGenres.add(book.genre);
    }
    
    return diverseResults.sort((a, b) => b.finalScore - a.finalScore);
  }

  /**
   * Utility Methods
   */

  hashString(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
  }

  deduplicateCoordinates(coordinates) {
    const seen = new Set();
    return coordinates.filter(coord => {
      const key = `${coord.hexagon}.${coord.wall}.${coord.shelf}.${coord.volume}`;
      if (seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    });
  }

  determineQueryType(concepts, fields, adjectives) {
    if (concepts.length > 2) return 'conceptual';
    if (fields.length > 0) return 'academic';
    if (adjectives.length > 1) return 'qualitative';
    return 'general';
  }

  calculateSearchComplexity(wordCount, conceptCount, fieldCount) {
    return wordCount * 0.1 + conceptCount * 0.3 + fieldCount * 0.2;
  }

  buildConceptIndex() {
    // Build a mapping of concepts to coordinate regions
    const index = {};
    
    for (const concept of this.generator.config.concepts) {
      const hash = this.hashString(concept);
      index[concept] = {
        primaryRegion: hash % 1000000,
        secondaryRegions: [
          (hash + 1000) % 1000000,
          (hash + 2000) % 1000000,
          (hash + 3000) % 1000000
        ]
      };
    }
    
    return index;
  }
}

module.exports = BabelSearchEngine;