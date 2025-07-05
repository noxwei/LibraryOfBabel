// Borgesian type definitions for the mystical library

export interface SacredScroll {
  id: string;
  title: string;
  author: string;
  chamber: number;
  relevanceStars: number;
  mysticalLocation: string;
  ancientWords: string;
  chunkType: string;
}

export interface EtherealConnection {
  id: string;
  title: string;
  author: string;
  similarity: number;
  hiddenPassage: string;
  contentPreview: string;
  chapter?: number;
}

export interface MysticalRevelation {
  sacredTexts: SacredScroll[];
  mysticalEchoes: EtherealConnection[];
  seekerGuidance: string;
  queryMetadata: {
    responseTime: number;
    timestamp: string;
    searchType: 'divine' | 'mystical' | 'precise';
  };
}

export interface ChambersNavigation {
  current: {
    id: string;
    chamber: number;
    section?: number;
    type: string;
  };
  previous?: {
    id: string;
    chamber: number;
    preview: string;
  };
  next?: {
    id: string;
    chamber: number;
    preview: string;
  };
  chapterOutline: Array<{
    chamber: number;
    title: string;
  }>;
}

export interface ReadingChamber {
  chunkId: string;
  title: string;
  author: string;
  content: string;
  navigation: ChambersNavigation;
  mysticalLocation: string;
  publicationYear?: number;
}

export interface ConceptNode {
  id: string;
  name: string;
  x: number;
  y: number;
  size: number;
  connections: string[];
}

export interface ConceptEdge {
  id: string;
  from: ConceptNode;
  to: ConceptNode;
  strength: number;
}

export interface LabyrinthMap {
  concepts: ConceptNode[];
  relationships: ConceptEdge[];
  centralConcept: string;
}

export type SearchMode = 'divine' | 'mystical' | 'precise';

export interface SearchState {
  query: string;
  mode: SearchMode;
  results: MysticalRevelation | null;
  loading: boolean;
  error: string | null;
}

// Borgesian language transformations
export const borgesianTerms = {
  search: "What knowledge do you seek?",
  results: "The Library reveals",
  noResults: "This knowledge dwells in distant corridors",
  loading: "Consulting the infinite catalog...",
  error: "The mirrors show conflicting reflections",
  divine: "🔮 Divine",
  mystical: "📿 Mystical", 
  precise: "📜 Precise",
  exactRefs: "📜 SACRED TEXTS",
  semanticEchoes: "🌀 MYSTICAL ECHOES",
  enterText: "Enter Text",
  followThread: "Follow Thread",
  returnToHalls: "← Return to Halls",
  previousChamber: "◄ Previous Chamber",
  nextChamber: "Next Chamber ►",
  chamberMap: "⬟ Chamber Map",
  hiddenPassages: "◇ Hidden Passages",
  annotations: "◈ Annotations"
} as const;