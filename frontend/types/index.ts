// Search Types
export type SearchType =
  | 'semantic'
  | 'semantic_passages'
  | 'emotional'
  | 'discovery'
  | 'content_analysis'
  | 'style'
  | 'passage'
  | 'titles'
  | 'quality'

export interface SearchTypeInfo {
  label: string
  icon: string
  color: string
  description: string
  placeholder: string
}

export const SEARCH_TYPES: Record<SearchType, SearchTypeInfo> = {
  semantic: {
    label: 'Books',
    icon: '📚',
    color: 'text-amber-400',
    description: 'Find matching books',
    placeholder: 'Search books by topic...',
  },
  semantic_passages: {
    label: 'Semantic',
    icon: '🧠',
    color: 'text-model-technical',
    description: 'AI-powered passage search',
    placeholder: 'Search by meaning...',
  },
  emotional: {
    label: 'Emotional',
    icon: '💭',
    color: 'text-model-creative',
    description: 'Find by emotion',
    placeholder: 'grief, hope, fear, joy...',
  },
  discovery: {
    label: 'Discovery',
    icon: '🔍',
    color: 'text-model-multilingual',
    description: 'Explore related content',
    placeholder: 'dystopia, cyberpunk...',
  },
  content_analysis: {
    label: 'Analysis',
    icon: '📊',
    color: 'text-model-specialized',
    description: 'Theme & content analysis',
    placeholder: 'capitalism, power...',
  },
  style: {
    label: 'Style',
    icon: '✍️',
    color: 'text-purple-400',
    description: 'Search by writing style',
    placeholder: 'poetic, technical...',
  },
  passage: {
    label: 'Text',
    icon: '📄',
    color: 'text-gray-400',
    description: 'Basic text search',
    placeholder: 'Search text...',
  },
  titles: {
    label: 'Titles',
    icon: '📚',
    color: 'text-amber-400',
    description: 'Search book titles',
    placeholder: 'Search titles...',
  },
  quality: {
    label: 'Quality',
    icon: '⭐',
    color: 'text-yellow-400',
    description: 'High-quality passages',
    placeholder: 'Search quality content...',
  },
}

// Legacy AI Model types (kept for compatibility)
export type AIModel = 'auto' | 'technical' | 'creative' | 'multilingual' | 'general' | 'specialized'

export interface SearchResult {
  book_id: number
  book_title: string
  author: string
  chunk_text: string
  chunk_id: string | number
  similarity_score: number
  genre?: string
  model_used?: string
  response_time_ms?: number
  // Extra data for specialized search types
  extra?: {
    // Emotional
    emotion?: string
    emotion_score?: number
    // Discovery
    subgenres?: string[]
    narrative_voice?: string
    reading_time?: string
    // Content Analysis
    dominant_themes?: Array<{ theme: string; score: string }>
    temporal_context?: Record<string, number>
    // Passages
    reading_link?: string
    word_count?: number
    chunk_type?: string
    // Style/Quality
    style_preview?: string
    quality_preview?: string
  }
}

export interface SearchResponse {
  results: SearchResult[]
  query: string
  count: number
  response_time_ms: number
  model_used?: string
  search_type?: SearchType
  meta?: Record<string, any>
}

export interface Book {
  id: number
  title: string
  author: string
  genre?: string
  chunk_count?: number
  word_count?: number
  model_type?: string
  created_at?: string
}

export interface BooksResponse {
  books: Book[]
  total: number
  page: number
  limit: number
}

export interface BookSummary {
  id: number
  title: string
  author: string
  genre: string
  chunk_count: number
  summary?: string
  model_type?: string
}

export interface HealthStatus {
  status: string
  database: string
  models: Record<string, boolean>
  stats: {
    total_books: number
    total_chunks: number
  }
}

// Legacy MODEL_INFO (kept for compatibility)
export const MODEL_INFO: Record<AIModel, { name: string; icon: string; color: string; description: string }> = {
  auto: {
    name: 'Auto-Route',
    icon: '🤖',
    color: 'text-gray-400',
    description: 'System analyzes query and selects optimal model',
  },
  technical: {
    name: 'Technical',
    icon: '🔬',
    color: 'text-model-technical',
    description: 'Best for: Science, Philosophy, Tech, Business',
  },
  creative: {
    name: 'Creative',
    icon: '📖',
    color: 'text-model-creative',
    description: 'Best for: Fiction, Literature, Narrative',
  },
  multilingual: {
    name: 'Multilingual',
    icon: '🌍',
    color: 'text-model-multilingual',
    description: 'Best for: History, Biography, Cultural studies',
  },
  general: {
    name: 'General',
    icon: '⚡',
    color: 'text-model-general',
    description: 'Best for: Reference, Self-help, General topics',
  },
  specialized: {
    name: 'Specialized',
    icon: '❄️',
    color: 'text-model-specialized',
    description: 'Best for: Domain-specific technical content',
  },
}
