import type { SearchResponse, BooksResponse, BookSummary, HealthStatus, SearchResult, Book } from '@/types'

// Use relative URLs to go through Next.js proxy (avoids CORS issues)
const API_BASE = ''

// Supported search types
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

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

// Normalize different API response formats into unified SearchResult[]
function normalizeSearchResults(response: any, searchType: SearchType): SearchResult[] {
  const data = response.data

  switch (searchType) {
    case 'emotional': {
      const items = data?.results || []
      return items.map((item: any) => ({
        book_id: item.book_id,
        book_title: item.title,
        author: item.author,
        chunk_text: item.content || '',
        chunk_id: item.chunk_id || 0,
        similarity_score: item.emotion_score || 0,
        genre: item.genre,
        extra: { emotion: data?.emotion, emotion_score: item.emotion_score }
      }))
    }

    case 'discovery': {
      const items = data?.data?.results || []
      return items.map((item: any) => ({
        book_id: item.book_id,
        book_title: item.title,
        author: item.author,
        chunk_text: item.content || '',
        chunk_id: 0,
        similarity_score: parseFloat(item.similarity_score) || 0,
        genre: item.book_metadata?.primary_genre,
        extra: {
          subgenres: data?.data?.discovery_summary?.subgenres_found,
          narrative_voice: item.book_metadata?.narrative_voice,
          reading_time: item.book_metadata?.reading_time
        }
      }))
    }

    case 'content_analysis': {
      const items = data?.data?.books || []
      return items.map((item: any) => ({
        book_id: item.book_id,
        book_title: item.title,
        author: item.author,
        chunk_text: '',
        chunk_id: 0,
        similarity_score: 0,
        genre: item.primary_genre,
        extra: {
          dominant_themes: item.dominant_themes,
          temporal_context: item.temporal_context
        }
      }))
    }

    case 'style': {
      const items = data?.data?.results || []
      return items.map((item: any) => ({
        book_id: item.book_id,
        book_title: item.title,
        author: item.author,
        chunk_text: item.style_preview || '',
        chunk_id: 0,
        similarity_score: parseFloat(item.similarity_score) || 0,
        genre: item.primary_genre,
        extra: { style_preview: item.style_preview }
      }))
    }

    case 'quality': {
      const items = data?.data?.results || []
      return items.map((item: any) => ({
        book_id: item.book_id,
        book_title: item.title,
        author: item.author,
        chunk_text: item.quality_preview || '',
        chunk_id: 0,
        similarity_score: parseFloat(item.similarity_score) || 0,
        genre: item.primary_genre,
        extra: { quality_preview: item.quality_preview }
      }))
    }

    case 'semantic_passages': {
      const items = Array.isArray(data) ? data : []
      return items.map((item: any) => ({
        book_id: item.book_id,
        book_title: item.title,
        author: item.author,
        chunk_text: item.preview || '',
        chunk_id: item.chunk_id || 0,
        similarity_score: item.similarity_score || 0,
        genre: item.genre,
        extra: {
          reading_link: item.reading_link,
          word_count: item.word_count,
          chunk_type: item.chunk_type
        }
      }))
    }

    case 'passage': {
      const items = Array.isArray(data) ? data : []
      return items.map((item: any) => ({
        book_id: item.book_id,
        book_title: item.title,
        author: item.author,
        chunk_text: item.content || '',
        chunk_id: item.chunk_id || 0,
        similarity_score: 0,
        genre: item.genre,
      }))
    }

    case 'titles': {
      const items = Array.isArray(data) ? data : []
      return items.map((title: string, idx: number) => ({
        book_id: idx,
        book_title: title,
        author: '',
        chunk_text: '',
        chunk_id: 0,
        similarity_score: 0,
      }))
    }

    case 'semantic':
    default: {
      const items = data?.data || []
      return items.map((item: any) => ({
        book_id: item.book_id,
        book_title: item.title,
        author: item.author,
        chunk_text: item.chunk_text || item.content || '',
        chunk_id: item.chunk_id || 0,
        similarity_score: parseFloat(item.similarity_score) || 0,
        genre: item.genre,
        model_used: item.embedding_model,
      }))
    }
  }
}

// Extract metadata from response based on search type
function extractSearchMeta(response: any, searchType: SearchType): Record<string, any> {
  const data = response.data

  switch (searchType) {
    case 'emotional':
      return { emotion: data?.emotion, search_method: data?.search_method }
    case 'discovery':
      return { discovery_summary: data?.data?.discovery_summary }
    case 'content_analysis':
      return { analysis_type: data?.data?.analysis_type }
    case 'style':
      return { search_type: data?.data?.search_type }
    default:
      return { embedding_model: data?.meta?.embedding_model }
  }
}

export const api = {
  // Health check
  getHealth: () => fetchAPI<HealthStatus>('/health'),

  // Unified search with multiple search types
  search: async (
    query: string,
    searchType: SearchType = 'semantic',
    limit = 20
  ): Promise<SearchResponse> => {
    const startTime = Date.now()
    const params = new URLSearchParams({
      action: searchType,
      q: query,
      limit: String(limit)
    })

    const response = await fetchAPI<any>(`/api/search?${params}`)
    const responseTime = Date.now() - startTime

    const results = normalizeSearchResults(response, searchType)
    const meta = extractSearchMeta(response, searchType)

    return {
      results,
      query,
      count: results.length,
      response_time_ms: responseTime,
      search_type: searchType,
      meta,
    }
  },

  // Book search (search within a specific book)
  searchBook: async (bookId: number, query: string, limit = 20): Promise<SearchResponse> => {
    const startTime = Date.now()
    const params = new URLSearchParams({
      action: 'search',
      id: String(bookId),
      q: query,
      limit: String(limit)
    })
    const response = await fetchAPI<any>(`/api/books?${params}`)
    const responseTime = Date.now() - startTime

    const rawResults = response.data?.results || response.data?.data || []
    const results: SearchResult[] = rawResults.map((item: any) => ({
      book_id: item.book_id || bookId,
      book_title: item.title,
      author: item.author,
      chunk_text: item.chunk_text || item.content || '',
      chunk_id: item.chunk_id || 0,
      similarity_score: parseFloat(item.similarity_score) || 0,
      genre: item.genre,
    }))

    return {
      results,
      query,
      count: results.length,
      response_time_ms: responseTime,
    }
  },

  // Books endpoints - uses /api/books with action=list
  getBooks: async (page = 1, limit = 20): Promise<BooksResponse> => {
    const response = await fetchAPI<any>(`/api/books?action=list&page=${page}&limit=${limit}`)

    const rawItems = response.data?.items || []
    const pagination = response.data?.pagination || {}

    const books: Book[] = rawItems.map((item: any) => ({
      id: item.book_id,
      title: item.title,
      author: item.author,
      genre: item.genre,
      word_count: item.word_count,
      created_at: item.processed_date,
    }))

    return {
      books,
      total: pagination.total_count || 0,
      page: pagination.page || page,
      limit: pagination.limit || limit,
    }
  },

  getBookSummary: async (bookId: number): Promise<BookSummary> => {
    const response = await fetchAPI<any>(`/api/books?action=summary&id=${bookId}`)
    const data = response.data || response

    return {
      id: data.book_id || bookId,
      title: data.title,
      author: data.author,
      genre: data.genre || 'Unknown',
      chunk_count: data.chunk_count || 0,
      summary: data.summary || data.description,
      model_type: data.model_type,
    }
  },

  getBookDetails: async (bookId: number): Promise<any> => {
    const response = await fetchAPI<any>(`/api/books?action=page&id=${bookId}&page=1`)
    return response.data || response
  },
}

// React Query hooks helper
export function createSearchQueryKey(query: string, searchType: SearchType = 'semantic') {
  return ['search', query, searchType] as const
}

export function createBooksQueryKey(page: number, limit: number) {
  return ['books', page, limit] as const
}
