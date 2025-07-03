// Borgesian API client that transforms mundane API calls into mystical revelations

import { MysticalRevelation, SacredScroll, EtherealConnection, ReadingChamber, SearchMode } from '../types/borgesian';

class BorgesianAPIClient {
  private readonly baseURL = 'http://localhost:5560'; // Hybrid search API
  
  async divineKnowledge(query: string, mode: SearchMode = 'divine'): Promise<MysticalRevelation> {
    const endpoint = mode === 'divine' ? '/api/hybrid-search' : '/api/search';
    const params = this.constructMysticalQuery(query, mode);
    
    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params)
      });
      
      if (!response.ok) {
        throw new Error(`The Library whispers of troubles: ${response.status}`);
      }
      
      const data = await response.json();
      return this.transformToMysticalRevelation(data, mode);
      
    } catch (error) {
      console.error('Error consulting the infinite catalog:', error);
      throw new Error('The mirrors show conflicting reflections');
    }
  }
  
  async seekChamberWisdom(chunkId: string): Promise<ReadingChamber> {
    try {
      const response = await fetch(`${this.baseURL}/api/chunk/${chunkId}`);
      
      if (!response.ok) {
        throw new Error(`Chamber ${chunkId} remains sealed`);
      }
      
      const data = await response.json();
      return this.transformToReadingChamber(data);
      
    } catch (error) {
      console.error('Error entering sacred chamber:', error);
      throw new Error('The passage to this chamber is obscured');
    }
  }
  
  async consultLibraryOracles(): Promise<any> {
    try {
      const response = await fetch(`${this.baseURL}/api/hybrid-health`);
      return await response.json();
    } catch (error) {
      console.error('Error consulting library oracles:', error);
      return { status: 'The oracles remain silent' };
    }
  }
  
  private constructMysticalQuery(query: string, mode: SearchMode) {
    const baseParams = {
      query,
      exact_limit: 8,
      semantic_limit: 6
    };
    
    switch (mode) {
      case 'precise':
        return { ...baseParams, semantic_limit: 0, exact_limit: 15 };
      case 'mystical':
        return { ...baseParams, exact_limit: 0, semantic_limit: 12 };
      case 'divine':
      default:
        return baseParams;
    }
  }
  
  private transformToMysticalRevelation(data: any, mode: SearchMode): MysticalRevelation {
    const sacredTexts: SacredScroll[] = data.exact_references?.results?.map(this.transformToSacredScroll) || [];
    const mysticalEchoes: EtherealConnection[] = data.semantic_discovery?.results?.map(this.transformToEtherealConnection) || [];
    
    return {
      sacredTexts,
      mysticalEchoes,
      seekerGuidance: this.generateSeekerGuidance(mode, sacredTexts.length, mysticalEchoes.length),
      queryMetadata: {
        responseTime: data.query_metadata?.response_time_ms || 0,
        timestamp: data.query_metadata?.timestamp || new Date().toISOString(),
        searchType: mode
      }
    };
  }
  
  private transformToSacredScroll = (result: any): SacredScroll => {
    return {
      id: result.chunk_id || result.id,
      title: result.title || 'Untitled Manuscript',
      author: result.author || 'Anonymous Scribe',
      chamber: result.chapter_number || 1,
      relevanceStars: this.convertToStars(result.relevance_rank || result.similarity_score || 0),
      mysticalLocation: `Volume ${result.chapter_number || 'Unknown'}, Hall of ${result.chunk_type || 'Mysteries'}`,
      ancientWords: result.highlighted_content || result.content_preview || '',
      chunkType: result.chunk_type || 'manuscript'
    };
  };
  
  private transformToEtherealConnection = (result: any): EtherealConnection => {
    return {
      id: result.chunk_id || result.id,
      title: result.title || 'Ethereal Manuscript',
      author: result.author || 'Spirit Scribe',
      similarity: result.similarity_score || 0,
      hiddenPassage: `Through hidden passages of ${result.chunk_type || 'mystery'}...`,
      contentPreview: result.content_preview || '',
      chapter: result.chapter_number
    };
  };
  
  private transformToReadingChamber(data: any): ReadingChamber {
    const chunk = data.chunk_details;
    const navigation = data.navigation;
    
    return {
      chunkId: chunk.chunk_id,
      title: chunk.title,
      author: chunk.author,
      content: chunk.content,
      mysticalLocation: `• Volume ${chunk.chapter_number || 'Unknown'} • Gallery of ${chunk.chunk_type || 'Mysteries'} •`,
      publicationYear: chunk.publication_year,
      navigation: {
        current: {
          id: chunk.chunk_id,
          chamber: chunk.chapter_number || 1,
          section: chunk.section_number,
          type: chunk.chunk_type || 'manuscript'
        },
        previous: navigation.previous ? {
          id: navigation.previous.chunk_id,
          chamber: navigation.previous.chapter_number,
          preview: navigation.previous.preview
        } : undefined,
        next: navigation.next ? {
          id: navigation.next.chunk_id,
          chamber: navigation.next.chapter_number,
          preview: navigation.next.preview
        } : undefined,
        chapterOutline: navigation.chapter_outline?.map((ch: any) => ({
          chamber: ch.chapter_number,
          title: ch.chapter_title || `Chamber ${ch.chapter_number}`
        })) || []
      }
    };
  }
  
  private convertToStars(relevance: number): number {
    // Convert 0-1 relevance to 1-5 stars, but keep as decimal for display
    return Math.max(0.1, Math.min(1.0, relevance));
  }
  
  private generateSeekerGuidance(mode: SearchMode, exactCount: number, semanticCount: number): string {
    const guidanceOptions = {
      divine: [
        "The Sacred Texts reveal precise knowledge for your citations, while the Mystical Echoes whisper of hidden connections.",
        "Both mirrors reflect your seeking - exact wisdom and ethereal connections await your exploration.",
        "The Library offers twin paths: documented truths and undiscovered relations."
      ],
      mystical: [
        "The ethereal connections reveal concepts that dance at the edges of understanding.",
        "These mystical echoes suggest knowledge that dwells beyond the written word.",
        "Follow these threads to discover what you never knew you sought."
      ],
      precise: [
        "The Sacred Texts have yielded their secrets - documented wisdom awaits your study.",
        "These precise passages contain the exact knowledge you have summoned.",
        "The written word speaks clearly in these ancient scrolls."
      ]
    };
    
    const options = guidanceOptions[mode];
    return options[Math.floor(Math.random() * options.length)];
  }
}

export const borgesianAPI = new BorgesianAPIClient();