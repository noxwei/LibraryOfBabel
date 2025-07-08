// LibraryOfBabel API Integration
// Connects to existing PostgreSQL backend with 360 books

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://localhost:5563'
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || 'babel_secure_3f99c2d1d294fbebdfc6b10cce93652d'

export interface BookSearchResult {
  book_id: number
  title: string
  author: string
  chunk_id: number
  content: string
  chapter?: string
  section?: string
  relevance_score?: number
  word_count?: number
}

export interface SearchResponse {
  success: boolean
  query: string
  results: BookSearchResult[]
  total_results: number
  search_time: number
  search_type: 'semantic' | 'topic' | 'keyword'
}

export interface ApiError {
  error: string
  message: string
  status: number
}

class LibraryOfBabelAPI {
  private baseURL: string
  private apiKey: string

  constructor(baseURL: string = API_BASE_URL, apiKey: string = API_KEY) {
    this.baseURL = baseURL
    this.apiKey = apiKey
  }

  private async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`
    
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.apiKey}`,
      'X-API-Key': this.apiKey,
      ...options.headers,
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('API Request Error:', error)
      throw error
    }
  }

  /**
   * Search across all books using semantic search
   */
  async searchBooks(query: string, limit: number = 10): Promise<SearchResponse> {
    const encodedQuery = encodeURIComponent(query)
    return this.makeRequest<SearchResponse>(
      `/api/v3/search?q=${encodedQuery}&limit=${limit}&type=content`
    )
  }

  /**
   * Search using topic-based approach
   */
  async searchByTopic(query: string, limit: number = 8): Promise<SearchResponse> {
    const encodedQuery = encodeURIComponent(query)
    return this.makeRequest<SearchResponse>(
      `/api/v3/search?q=${encodedQuery}&limit=${limit}&type=cross_reference`
    )
  }

  /**
   * Get book details by ID
   */
  async getBookDetails(bookId: number): Promise<unknown> {
    return this.makeRequest(`/api/v3/books/${bookId}`)
  }

  /**
   * Advanced search with multiple strategies
   */
  async advancedSearch(query: string): Promise<{
    semantic: SearchResponse
    topic: SearchResponse
  }> {
    const [semantic, topic] = await Promise.all([
      this.searchBooks(query, 10),
      this.searchByTopic(query, 8)
    ])

    return { semantic, topic }
  }

  /**
   * Get search suggestions based on partial query
   */
  async getSearchSuggestions(partial: string): Promise<string[]> {
    // This would be implemented based on backend capabilities
    // For now, return static suggestions
    const suggestions = [
      "AI consciousness and ethics",
      "Octavia Butler social justice analysis", 
      "quantum physics philosophy",
      "digital surveillance state",
      "posthuman consciousness",
      "climate change policy",
      "race and technology intersection"
    ]
    
    return suggestions.filter(s => 
      s.toLowerCase().includes(partial.toLowerCase())
    ).slice(0, 5)
  }

  /**
   * Health check for API connectivity
   */
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    try {
      return await this.makeRequest('/api/v3/health')
    } catch {
      return {
        status: 'error',
        timestamp: new Date().toISOString()
      }
    }
  }
}

// Export singleton instance
export const libraryAPI = new LibraryOfBabelAPI()

// Export class for testing
export { LibraryOfBabelAPI }