/**
 * Babel Library API Client - Integration with the Library of Babel Backend
 * 
 * This service connects the Borgesian frontend with the procedural content
 * generation backend, providing seamless access to infinite literary space
 * while maintaining the mystical interface experience.
 */

import { MysticalRevelation, SacredScroll, EtherealConnection, ReadingChamber, SearchMode } from '../types/borgesian';

interface BabelBookResult {
  id: string;
  title: string;
  author: string;
  abstract: string;
  relevanceScore: number;
  coordinates: {
    hexagon: number;
    wall: number;
    shelf: number;
    volume: number;
  };
  genre: string;
  publicationYear: number;
  wordCount?: number;
  chapters?: Array<{
    number: number;
    title: string;
    content: string;
    wordCount: number;
    keyTerms: string[];
  }>;
}

interface BabelSearchResponse {
  query: string;
  results: BabelBookResult[];
  metadata: {
    library: {
      mode: string;
      infinite: boolean;
      procedural: boolean;
    };
    search: {
      algorithm: string;
      totalExplored: number;
    };
  };
  educational: {
    concept: string;
    note: string;
    philosophy: string;
  };
}

interface BabelBookResponse {
  book: {
    id: string;
    title: string;
    author: string;
    content?: string;
    chapters: Array<{
      number: number;
      title: string;
      content: string;
      wordCount: number;
      keyTerms: string[];
      summary: string;
    }>;
    bibliography: Array<{
      author: string;
      title: string;
      year: number;
      publisher: string;
      formatted: string;
    }>;
    coordinates: {
      hexagon: number;
      wall: number;
      shelf: number;
      volume: number;
    };
    publicationYear: number;
    wordCount: number;
    genre: string;
  };
  educational: {
    concept: string;
    note?: string;
    coordinates: string;
  };
}

class BabelLibraryAPIClient {
  private readonly baseURL: string;
  private readonly mode: 'educational' | 'enhanced';

  constructor(mode: 'educational' | 'enhanced' = 'educational') {
    this.baseURL = mode === 'educational' ? 'http://localhost:5570' : 'http://localhost:5560';
    this.mode = mode;
  }

  /**
   * Search the infinite Library of Babel for books matching the query
   */
  async divineKnowledge(query: string, mode: SearchMode = 'divine'): Promise<MysticalRevelation> {
    try {
      const searchMode = this.mapSearchMode(mode);
      
      const response = await fetch(`${this.baseURL}/api/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          mode: this.mode === 'enhanced' ? 'enhanced' : searchMode,
          maxResults: this.getResultLimits(mode).total
        })
      });

      if (!response.ok) {
        throw new Error(`The Library whispers of troubles: ${response.status}`);
      }

      const data: BabelSearchResponse = await response.json();
      return this.transformToMysticalRevelation(data, mode);

    } catch (error) {
      console.error('Error consulting the infinite catalog:', error);
      throw new Error('The mirrors show conflicting reflections');
    }
  }

  /**
   * Retrieve a specific book from the library coordinates
   */
  async seekChamberWisdom(bookId: string): Promise<ReadingChamber> {
    try {
      // Parse coordinates from book ID (format: hexagon.wall.shelf.volume)
      const coords = this.parseBookCoordinates(bookId);
      
      const response = await fetch(
        `${this.baseURL}/api/book/${coords.hexagon}/${coords.wall}/${coords.shelf}/${coords.volume}`
      );

      if (!response.ok) {
        throw new Error(`Chamber ${bookId} remains sealed`);
      }

      const data: BabelBookResponse = await response.json();
      return this.transformToReadingChamber(data);

    } catch (error) {
      console.error('Error entering sacred chamber:', error);
      throw new Error('The passage to this chamber is obscured');
    }
  }

  /**
   * Get a random book from the infinite library
   */
  async seekRandomWisdom(): Promise<ReadingChamber> {
    try {
      const response = await fetch(`${this.baseURL}/api/random-book`);

      if (!response.ok) {
        throw new Error('The random paths of the library are obscured');
      }

      const data: BabelBookResponse = await response.json();
      return this.transformToReadingChamber(data);

    } catch (error) {
      console.error('Error finding random chamber:', error);
      throw new Error('The serendipitous passages remain hidden');
    }
  }

  /**
   * Explore books related to a specific concept
   */
  async exploreConceptualRealm(concept: string, limit: number = 5): Promise<MysticalRevelation> {
    try {
      const response = await fetch(`${this.baseURL}/api/explore/${encodeURIComponent(concept)}?limit=${limit}`);

      if (!response.ok) {
        throw new Error(`The concept '${concept}' dwells in distant corridors`);
      }

      const data = await response.json();
      
      // Transform exploration results into mystical revelation format
      return {
        sacredTexts: data.books.map(this.transformToSacredScroll),
        mysticalEchoes: [], // Exploration focuses on direct matches
        seekerGuidance: data.educational.note || `Exploring the infinite treatment of '${concept}'`,
        queryMetadata: {
          responseTime: Date.now(),
          timestamp: new Date().toISOString(),
          searchType: 'precise'
        }
      };

    } catch (error) {
      console.error('Error exploring conceptual realm:', error);
      throw new Error('The concept remains beyond the current corridors');
    }
  }

  /**
   * Get available concepts for exploration
   */
  async consultLibraryOracles(): Promise<{
    concepts: string[];
    academicFields: string[];
    adjectives: string[];
    educational: any;
  }> {
    try {
      const response = await fetch(`${this.baseURL}/api/concepts`);
      
      if (!response.ok) {
        throw new Error('The oracles remain silent');
      }

      return await response.json();

    } catch (error) {
      console.error('Error consulting library oracles:', error);
      return {
        concepts: [],
        academicFields: [],
        adjectives: [],
        educational: { note: 'The oracles are temporarily unavailable' }
      };
    }
  }

  /**
   * Check library health and status
   */
  async consultLibraryHealth(): Promise<any> {
    try {
      const response = await fetch(`${this.baseURL}/api/health`);
      return await response.json();
    } catch (error) {
      console.error('Error consulting library health:', error);
      return { status: 'The library experiences temporal disturbances' };
    }
  }

  /**
   * Transform backend search results to mystical revelation format
   */
  private transformToMysticalRevelation(data: BabelSearchResponse, mode: SearchMode): MysticalRevelation {
    const limits = this.getResultLimits(mode);
    
    // Split results based on search mode
    const allResults = data.results || [];
    
    let sacredTexts: SacredScroll[] = [];
    let mysticalEchoes: EtherealConnection[] = [];

    if (mode === 'divine') {
      // Divine mode shows both exact and semantic results
      sacredTexts = allResults.slice(0, limits.exact).map(this.transformToSacredScroll);
      mysticalEchoes = allResults.slice(limits.exact, limits.exact + limits.semantic).map(this.transformToEtherealConnection);
    } else if (mode === 'precise') {
      // Precise mode shows only exact matches
      sacredTexts = allResults.slice(0, limits.exact).map(this.transformToSacredScroll);
    } else if (mode === 'mystical') {
      // Mystical mode shows only semantic connections
      mysticalEchoes = allResults.slice(0, limits.semantic).map(this.transformToEtherealConnection);
    }

    return {
      sacredTexts,
      mysticalEchoes,
      seekerGuidance: this.generateSeekerGuidance(mode, sacredTexts.length, mysticalEchoes.length, data.educational),
      queryMetadata: {
        responseTime: Date.now(),
        timestamp: new Date().toISOString(),
        searchType: mode
      }
    };
  }

  /**
   * Transform backend book result to sacred scroll format
   */
  private transformToSacredScroll = (result: BabelBookResult): SacredScroll => {
    return {
      id: result.id,
      title: result.title,
      author: result.author,
      chamber: result.coordinates.hexagon % 1000, // Display-friendly chamber number
      relevanceStars: result.relevanceScore,
      mysticalLocation: `Hexagon ${result.coordinates.hexagon}, Wall ${result.coordinates.wall}, Shelf ${result.coordinates.shelf}, Volume ${result.coordinates.volume}`,
      ancientWords: this.highlightContent(result.abstract || ''),
      chunkType: result.genre.toLowerCase()
    };
  };

  /**
   * Transform backend book result to ethereal connection format
   */
  private transformToEtherealConnection = (result: BabelBookResult): EtherealConnection => {
    return {
      id: result.id,
      title: result.title,
      author: result.author,
      similarity: result.relevanceScore,
      hiddenPassage: `Through the ethereal corridors of ${result.genre}, in the year ${result.publicationYear}...`,
      contentPreview: result.abstract || '',
      chapter: result.coordinates.hexagon % 100 // Mystical chapter reference
    };
  };

  /**
   * Transform backend book response to reading chamber format
   */
  private transformToReadingChamber(data: BabelBookResponse): ReadingChamber {
    const book = data.book;
    const coords = book.coordinates;
    
    return {
      chunkId: book.id,
      title: book.title,
      author: book.author,
      content: this.assembleBookContent(book.chapters),
      mysticalLocation: `• Hexagon ${coords.hexagon} • Wall ${coords.wall} • Shelf ${coords.shelf} • Volume ${coords.volume} •`,
      publicationYear: book.publicationYear,
      navigation: {
        current: {
          id: book.id,
          chamber: coords.hexagon % 1000,
          section: coords.volume,
          type: book.genre
        },
        previous: this.generateAdjacentBook(coords, -1),
        next: this.generateAdjacentBook(coords, 1),
        chapterOutline: book.chapters.map((chapter, index) => ({
          chamber: index + 1,
          title: chapter.title
        }))
      }
    };
  }

  /**
   * Helper methods
   */
  private mapSearchMode(mode: SearchMode): string {
    switch (mode) {
      case 'divine': return 'comprehensive';
      case 'mystical': return 'exploratory';
      case 'precise': return 'precise';
      default: return 'comprehensive';
    }
  }

  private getResultLimits(mode: SearchMode) {
    switch (mode) {
      case 'divine': return { exact: 8, semantic: 6, total: 14 };
      case 'mystical': return { exact: 0, semantic: 12, total: 12 };
      case 'precise': return { exact: 15, semantic: 0, total: 15 };
      default: return { exact: 8, semantic: 6, total: 14 };
    }
  }

  private parseBookCoordinates(bookId: string) {
    const parts = bookId.split('.');
    if (parts.length !== 4) {
      throw new Error('Invalid book coordinate format');
    }
    
    return {
      hexagon: parseInt(parts[0]),
      wall: parseInt(parts[1]),
      shelf: parseInt(parts[2]),
      volume: parseInt(parts[3])
    };
  }

  private highlightContent(content: string): string {
    // Simple highlighting for key academic terms
    const keywords = ['concept', 'theory', 'analysis', 'study', 'examination', 'investigation'];
    let highlighted = content;
    
    keywords.forEach(keyword => {
      const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
      highlighted = highlighted.replace(regex, `<mark class="ancient-highlight">$&</mark>`);
    });
    
    return highlighted;
  }

  private assembleBookContent(chapters: any[]): string {
    return chapters.map(chapter => 
      `${chapter.title}\n\n${chapter.content}`
    ).join('\n\n---\n\n');
  }

  private generateAdjacentBook(coords: any, direction: number) {
    const newVolume = (coords.volume + direction + 32) % 32;
    const newId = `${coords.hexagon}.${coords.wall}.${coords.shelf}.${newVolume}`;
    
    return {
      id: newId,
      chamber: coords.hexagon % 1000,
      preview: `Volume ${newVolume} in the same shelf contains related wisdom...`
    };
  }

  private generateSeekerGuidance(mode: SearchMode, exactCount: number, semanticCount: number, educational: any): string {
    const baseGuidance = educational?.philosophy || "Every search unveils both the sought and the unexpected";
    
    const modeGuidance = {
      divine: "The Library reveals both documented truths and hidden connections in perfect harmony.",
      mystical: "These ethereal echoes suggest knowledge that dwells beyond the written word.",
      precise: "The sacred texts have yielded their documented wisdom for your study."
    };
    
    return `${modeGuidance[mode]} ${baseGuidance}`;
  }
}

// Export configured instances for different modes
export const babelLibraryAPI = new BabelLibraryAPIClient('educational');
export const enhancedBabelAPI = new BabelLibraryAPIClient('enhanced');
export default babelLibraryAPI;