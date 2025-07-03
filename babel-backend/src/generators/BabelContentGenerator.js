/**
 * BabelContentGenerator - Core procedural content generation engine
 * 
 * This module implements Borges' Library of Babel concept through deterministic
 * procedural generation, creating an infinite space of literary exploration
 * while maintaining educational value and thematic coherence.
 * 
 * Mathematical Foundation:
 * - Uses seedrandom for deterministic pseudorandom generation
 * - Implements hexagonal coordinate system inspired by Borges' hexagonal rooms
 * - Applies Markov chain principles for coherent text generation
 * - Uses weighted selection algorithms for thematic consistency
 */

const seedrandom = require('seedrandom');
const config = require('../../config/default');

class BabelContentGenerator {
  constructor() {
    this.config = config.library.procedural;
    this.baseSeed = this.config.hexagonalSeed;
    
    // Initialize content templates and data
    this.initializeTemplates();
    this.initializeMarkovChains();
    this.initializeAuthorNames();
  }

  /**
   * Generate a complete book based on coordinates in the infinite library
   * 
   * @param {number} hexagon - Hexagonal room coordinate (0 to ∞)
   * @param {number} wall - Wall position (0-5, representing hexagon sides)
   * @param {number} shelf - Shelf position (0-4, five shelves per wall)
   * @param {number} volume - Volume position (0-31, thirty-two volumes per shelf)
   * @returns {Object} Complete book object with procedural content
   */
  generateBook(hexagon, wall, shelf, volume) {
    const bookSeed = `${this.baseSeed}-${hexagon}-${wall}-${shelf}-${volume}`;
    const rng = seedrandom(bookSeed);
    
    // Generate book metadata
    const bookId = `${hexagon}.${wall}.${shelf}.${volume}`;
    const title = this.generateTitle(rng);
    const author = this.generateAuthor(rng);
    const publicationYear = this.generatePublicationYear(rng);
    
    // Generate book structure
    const chapters = this.generateChapters(rng, title);
    const abstract = this.generateAbstract(rng, title);
    const bibliography = this.generateBibliography(rng);
    
    return {
      id: bookId,
      coordinates: { hexagon, wall, shelf, volume },
      title,
      author,
      publicationYear,
      abstract,
      chapters,
      bibliography,
      wordCount: this.calculateWordCount(chapters),
      genre: this.determineGenre(rng, title),
      language: 'English', // Could be extended to multiple languages
      isbn: this.generateISBN(rng),
      deweyDecimal: this.generateDeweyDecimal(rng),
      metadata: {
        generatedAt: new Date().toISOString(),
        seed: bookSeed,
        version: '1.0.0'
      }
    };
  }

  /**
   * Generate a scholarly title using weighted template selection
   * 
   * @param {Function} rng - Seeded random number generator
   * @returns {string} Generated academic title
   */
  generateTitle(rng) {
    const template = this.selectWeighted(rng, this.config.titleTemplates);
    
    return template.replace(/{(\w+)}/g, (match, type) => {
      switch (type) {
        case 'concept':
          return this.selectWeighted(rng, this.config.concepts);
        case 'adjective':
          return this.selectWeighted(rng, this.config.adjectives);
        case 'noun':
          return this.generateAcademicNoun(rng);
        case 'field':
          return this.selectWeighted(rng, this.config.academicFields);
        default:
          return match;
      }
    });
  }

  /**
   * Generate a fictional but credible author name
   * 
   * @param {Function} rng - Seeded random number generator
   * @returns {string} Generated author name
   */
  generateAuthor(rng) {
    const firstNames = this.authorNames.first;
    const lastNames = this.authorNames.last;
    const titles = this.authorNames.titles;
    
    const firstName = this.selectWeighted(rng, firstNames);
    const lastName = this.selectWeighted(rng, lastNames);
    const title = rng() < 0.3 ? this.selectWeighted(rng, titles) + ' ' : '';
    
    return `${title}${firstName} ${lastName}`;
  }

  /**
   * Generate chapter structure with thematically consistent content
   * 
   * @param {Function} rng - Seeded random number generator
   * @param {string} title - Book title for thematic consistency
   * @returns {Array} Array of chapter objects
   */
  generateChapters(rng, title) {
    const chapterCount = Math.floor(rng() * 8) + 6; // 6-13 chapters
    const chapters = [];
    
    // Extract key concepts from title for thematic consistency
    const titleConcepts = this.extractConcepts(title);
    
    for (let i = 0; i < chapterCount; i++) {
      const chapterTitle = this.generateChapterTitle(rng, titleConcepts, i + 1);
      const content = this.generateChapterContent(rng, chapterTitle, titleConcepts);
      
      chapters.push({
        number: i + 1,
        title: chapterTitle,
        content: content,
        wordCount: this.estimateWordCount(content),
        keyTerms: this.extractKeyTerms(content),
        summary: this.generateChapterSummary(rng, chapterTitle)
      });
    }
    
    return chapters;
  }

  /**
   * Generate coherent chapter content using Markov chain principles
   * 
   * @param {Function} rng - Seeded random number generator
   * @param {string} chapterTitle - Title for thematic guidance
   * @param {Array} concepts - Key concepts for consistency
   * @returns {string} Generated chapter content
   */
  generateChapterContent(rng, chapterTitle, concepts) {
    const paragraphCount = Math.floor(rng() * 12) + 8; // 8-19 paragraphs
    const paragraphs = [];
    
    for (let i = 0; i < paragraphCount; i++) {
      const paragraph = this.generateParagraph(rng, concepts, i === 0);
      paragraphs.push(paragraph);
    }
    
    return paragraphs.join('\n\n');
  }

  /**
   * Generate a thematically coherent paragraph
   * 
   * @param {Function} rng - Seeded random number generator
   * @param {Array} concepts - Key concepts for consistency
   * @param {boolean} isOpening - Whether this is the opening paragraph
   * @returns {string} Generated paragraph
   */
  generateParagraph(rng, concepts, isOpening = false) {
    const sentenceCount = Math.floor(rng() * 5) + 3; // 3-7 sentences
    const sentences = [];
    
    for (let i = 0; i < sentenceCount; i++) {
      const sentence = this.generateSentence(rng, concepts, i === 0 && isOpening);
      sentences.push(sentence);
    }
    
    return sentences.join(' ');
  }

  /**
   * Generate a philosophically coherent sentence
   * 
   * @param {Function} rng - Seeded random number generator
   * @param {Array} concepts - Key concepts for consistency
   * @param {boolean} isOpening - Whether this is the opening sentence
   * @returns {string} Generated sentence
   */
  generateSentence(rng, concepts, isOpening = false) {
    const structures = this.sentenceStructures;
    const structure = this.selectWeighted(rng, structures);
    
    return structure.replace(/{(\w+)}/g, (match, type) => {
      switch (type) {
        case 'concept':
          return rng() < 0.6 && concepts.length > 0 
            ? this.selectWeighted(rng, concepts)
            : this.selectWeighted(rng, this.config.concepts);
        case 'adjective':
          return this.selectWeighted(rng, this.config.adjectives);
        case 'field':
          return this.selectWeighted(rng, this.config.academicFields);
        case 'verb':
          return this.selectWeighted(rng, this.academicVerbs);
        case 'noun':
          return this.generateAcademicNoun(rng);
        default:
          return match;
      }
    });
  }

  /**
   * Initialize sentence structures for coherent generation
   */
  initializeMarkovChains() {
    this.sentenceStructures = [
      'The {concept} of {concept} {verb} the fundamental {noun} of {field}.',
      'In examining {concept}, we must consider the {adjective} nature of {concept}.',
      'The {adjective} relationship between {concept} and {concept} reveals {noun}.',
      'Through {field}, we observe that {concept} {verb} {concept}.',
      'The {concept} paradigm suggests that {concept} is {adjective}.',
      'Contemporary {field} demonstrates the {adjective} {concept} of {concept}.',
      'This {adjective} approach to {concept} {verb} our understanding of {concept}.',
      'The intersection of {concept} and {concept} {verb} {adjective} {noun}.',
      'Theoretical {field} posits that {concept} {verb} {concept}.',
      'The {adjective} framework of {concept} {verb} {concept} through {noun}.'
    ];
    
    this.academicVerbs = [
      'illuminates', 'demonstrates', 'reveals', 'suggests', 'indicates',
      'establishes', 'challenges', 'explores', 'examines', 'investigates',
      'analyzes', 'synthesizes', 'deconstructs', 'contextualizes', 'problematizes',
      'theorizes', 'conceptualizes', 'articulates', 'elucidates', 'explicates'
    ];
  }

  /**
   * Initialize author name components for variety
   */
  initializeAuthorNames() {
    this.authorNames = {
      first: [
        'Alexander', 'Beatrice', 'Constantine', 'Dorothea', 'Edmund', 'Felicia',
        'Gaston', 'Helena', 'Ignatius', 'Josephine', 'Konstantin', 'Lucinda',
        'Maximilian', 'Natasha', 'Octavius', 'Penelope', 'Quentin', 'Rosalind',
        'Sebastian', 'Theodora', 'Ulysses', 'Veronica', 'Winston', 'Xenia',
        'Yves', 'Zelda', 'Ambrose', 'Cordelia', 'Dimitri', 'Evangeline'
      ],
      last: [
        'Albertson', 'Blackwood', 'Cromwell', 'Donovan', 'Ellsworth', 'Fairchild',
        'Goodwin', 'Harrington', 'Ingram', 'Jameson', 'Kingsley', 'Livingston',
        'Morrison', 'Northcott', 'Oldham', 'Pemberton', 'Quincy', 'Rothschild',
        'Sinclair', 'Thornton', 'Underwood', 'Vanderberg', 'Whitmore', 'Yaxley',
        'Ziegler', 'Ashford', 'Beaumont', 'Carlisle', 'Drummond', 'Evermore'
      ],
      titles: [
        'Dr.', 'Prof.', 'Sir', 'Dame', 'Rev.', 'Hon.'
      ]
    };
  }

  /**
   * Initialize content templates for consistent generation
   */
  initializeTemplates() {
    this.chapterTitleTemplates = [
      'The {concept} of {concept}',
      'On {concept} and {concept}',
      'Toward a {adjective} {concept}',
      'The {adjective} {concept}',
      'Between {concept} and {concept}',
      'The Problem of {concept}',
      'Rethinking {concept}',
      'The {concept} Question',
      'Beyond {concept}',
      'The {concept} Paradigm'
    ];
  }

  /**
   * Utility function for weighted selection from arrays
   * 
   * @param {Function} rng - Seeded random number generator
   * @param {Array} items - Items to select from
   * @returns {*} Selected item
   */
  selectWeighted(rng, items) {
    const index = Math.floor(rng() * items.length);
    return items[index];
  }

  /**
   * Generate a thematically appropriate chapter title
   * 
   * @param {Function} rng - Seeded random number generator
   * @param {Array} concepts - Key concepts for consistency
   * @param {number} chapterNumber - Chapter number for progression
   * @returns {string} Generated chapter title
   */
  generateChapterTitle(rng, concepts, chapterNumber) {
    const template = this.selectWeighted(rng, this.chapterTitleTemplates);
    
    return template.replace(/{(\w+)}/g, (match, type) => {
      switch (type) {
        case 'concept':
          return rng() < 0.7 && concepts.length > 0 
            ? this.selectWeighted(rng, concepts)
            : this.selectWeighted(rng, this.config.concepts);
        case 'adjective':
          return this.selectWeighted(rng, this.config.adjectives);
        default:
          return match;
      }
    });
  }

  /**
   * Extract key concepts from a title for thematic consistency
   * 
   * @param {string} title - Book title
   * @returns {Array} Array of extracted concepts
   */
  extractConcepts(title) {
    const concepts = [];
    const words = title.toLowerCase().split(/\s+/);
    
    for (const word of words) {
      if (this.config.concepts.includes(word)) {
        concepts.push(word);
      }
    }
    
    return concepts;
  }

  /**
   * Generate publication year with temporal distribution
   * 
   * @param {Function} rng - Seeded random number generator
   * @returns {number} Generated publication year
   */
  generatePublicationYear(rng) {
    // Weight toward more recent years, but include classics
    const currentYear = new Date().getFullYear();
    const yearRange = currentYear - 1850;
    const random = rng();
    
    // Use exponential distribution to favor recent years
    const year = Math.floor(1850 + yearRange * (1 - Math.pow(random, 2)));
    return year;
  }

  /**
   * Generate abstract based on title and content themes
   * 
   * @param {Function} rng - Seeded random number generator
   * @param {string} title - Book title
   * @returns {string} Generated abstract
   */
  generateAbstract(rng, title) {
    const concepts = this.extractConcepts(title);
    const sentences = [];
    
    for (let i = 0; i < 4; i++) {
      const sentence = this.generateSentence(rng, concepts, i === 0);
      sentences.push(sentence);
    }
    
    return sentences.join(' ');
  }

  /**
   * Generate bibliography with fictional but plausible citations
   * 
   * @param {Function} rng - Seeded random number generator
   * @returns {Array} Array of bibliographic entries
   */
  generateBibliography(rng) {
    const citationCount = Math.floor(rng() * 15) + 5; // 5-19 citations
    const citations = [];
    
    for (let i = 0; i < citationCount; i++) {
      const citation = this.generateCitation(rng);
      citations.push(citation);
    }
    
    return citations.sort((a, b) => a.author.localeCompare(b.author));
  }

  /**
   * Generate a single bibliographic citation
   * 
   * @param {Function} rng - Seeded random number generator
   * @returns {Object} Citation object
   */
  generateCitation(rng) {
    const author = this.generateAuthor(rng);
    const title = this.generateTitle(rng);
    const year = this.generatePublicationYear(rng);
    const publisher = this.generatePublisher(rng);
    
    return {
      author,
      title,
      year,
      publisher,
      formatted: `${author}. (${year}). ${title}. ${publisher}.`
    };
  }

  /**
   * Generate academic publisher name
   * 
   * @param {Function} rng - Seeded random number generator
   * @returns {string} Publisher name
   */
  generatePublisher(rng) {
    const publishers = [
      'Cambridge University Press', 'Oxford University Press', 'Harvard University Press',
      'Yale University Press', 'Princeton University Press', 'MIT Press',
      'University of Chicago Press', 'Stanford University Press', 'Cornell University Press',
      'Duke University Press', 'Johns Hopkins University Press', 'Blackwell Publishing',
      'Routledge', 'Springer', 'Elsevier', 'Wiley', 'Sage Publications',
      'Academic Press', 'Norton', 'Basic Books'
    ];
    
    return this.selectWeighted(rng, publishers);
  }

  /**
   * Additional utility methods for content generation
   */
  
  generateAcademicNoun(rng) {
    const nouns = [
      'principle', 'theory', 'framework', 'paradigm', 'model', 'structure',
      'system', 'method', 'approach', 'analysis', 'synthesis', 'perspective',
      'dimension', 'aspect', 'element', 'component', 'factor', 'variable',
      'phenomenon', 'concept', 'notion', 'idea', 'thought', 'consideration'
    ];
    
    return this.selectWeighted(rng, nouns);
  }

  determineGenre(rng, title) {
    const genres = [
      'Philosophy', 'Literary Criticism', 'Mathematics', 'Logic',
      'Metaphysics', 'Epistemology', 'Ethics', 'Aesthetics',
      'Linguistics', 'Semiotics', 'Hermeneutics', 'Phenomenology'
    ];
    
    return this.selectWeighted(rng, genres);
  }

  generateISBN(rng) {
    const isbn = '978-' + 
      Math.floor(rng() * 10) + 
      Math.floor(rng() * 900000 + 100000) + '-' +
      Math.floor(rng() * 90 + 10) + '-' +
      Math.floor(rng() * 10);
    
    return isbn;
  }

  generateDeweyDecimal(rng) {
    const categories = [
      '100', '110', '120', '130', '140', '150', '160', '170', '180', '190', // Philosophy
      '400', '410', '420', '430', '440', '450', '460', '470', '480', '490', // Language
      '800', '810', '820', '830', '840', '850', '860', '870', '880', '890'  // Literature
    ];
    
    const base = this.selectWeighted(rng, categories);
    const decimal = Math.floor(rng() * 1000).toString().padStart(3, '0');
    
    return `${base}.${decimal}`;
  }

  calculateWordCount(chapters) {
    return chapters.reduce((total, chapter) => total + chapter.wordCount, 0);
  }

  estimateWordCount(content) {
    return content.split(/\s+/).length;
  }

  extractKeyTerms(content) {
    const words = content.toLowerCase().split(/\s+/);
    const keyTerms = [];
    
    for (const word of words) {
      if (this.config.concepts.includes(word) || this.config.academicFields.includes(word)) {
        keyTerms.push(word);
      }
    }
    
    return [...new Set(keyTerms)].slice(0, 10);
  }

  generateChapterSummary(rng, chapterTitle) {
    const concepts = this.extractConcepts(chapterTitle);
    const summary = this.generateSentence(rng, concepts, true);
    
    return summary;
  }
}

module.exports = BabelContentGenerator;