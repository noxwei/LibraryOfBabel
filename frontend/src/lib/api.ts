// LibraryOfBabel API Integration
// Connects to existing PostgreSQL backend with 360 books

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://localhost:5563'
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || 'babel_secure_YOUR_KEY_HERE'
const HR_API_BASE_URL = process.env.NEXT_PUBLIC_HR_API_URL || 'http://localhost:8081'
const QA_API_BASE_URL = process.env.NEXT_PUBLIC_QA_API_URL || 'http://localhost:8082'

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

export interface HRStatus {
  status: string
  timestamp: string
  manager: string
  systems: string[]
}

export interface HRAgent {
  agent_id: string
  agent_name: string
  success_rate: number
  tasks_completed: number
  status: string
}

export interface HRAlert {
  alert_id: string
  agent_id: string
  alert_type: string
  alert_data: any
  status: string
  created_at: string
}

class LibraryOfBabelAPI {
  private baseURL: string
  private apiKey: string
  private hrBaseURL: string
  private qaBaseURL: string

  constructor(baseURL: string = API_BASE_URL, apiKey: string = API_KEY, hrBaseURL: string = HR_API_BASE_URL, qaBaseURL: string = QA_API_BASE_URL) {
    this.baseURL = baseURL
    this.apiKey = apiKey
    this.hrBaseURL = hrBaseURL
    this.qaBaseURL = qaBaseURL
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

  // HR API Methods
  private async makeHRRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.hrBaseURL}${endpoint}`
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('HR API Request Error:', error)
      throw error
    }
  }

  /**
   * Get HR system status
   */
  async getHRStatus(): Promise<HRStatus> {
    return this.makeHRRequest<HRStatus>('/hr/status')
  }

  /**
   * Get HR agents data (mock data when database unavailable)
   */
  async getHRAgents(): Promise<{ agents: HRAgent[] }> {
    try {
      return await this.makeHRRequest<{ agents: HRAgent[] }>('/hr/agents')
    } catch (error) {
      // Return mock data when database is unavailable
      console.warn('HR agents endpoint unavailable, returning mock data:', error)
      return {
        agents: [
          {
            agent_id: 'linda-hr',
            agent_name: 'Linda Zhang (HR Manager)',
            success_rate: 95.8,
            tasks_completed: 247,
            status: 'active'
          },
          {
            agent_id: 'alex-qa',
            agent_name: 'Alex Chen (QA Engineer)',
            success_rate: 92.3,
            tasks_completed: 156,
            status: 'active'
          },
          {
            agent_id: 'reddit-bibliophile',
            agent_name: 'Reddit Bibliophile Agent',
            success_rate: 88.7,
            tasks_completed: 89,
            status: 'active'
          }
        ]
      }
    }
  }

  /**
   * Get HR alerts (mock data when database unavailable)
   */
  async getHRAlerts(): Promise<{ alerts: HRAlert[] }> {
    try {
      return await this.makeHRRequest<{ alerts: HRAlert[] }>('/hr/alerts')
    } catch (error) {
      // Return mock data when database is unavailable
      console.warn('HR alerts endpoint unavailable, returning mock data:', error)
      return {
        alerts: [
          {
            alert_id: 'alert-001',
            agent_id: 'reddit-bibliophile',
            alert_type: 'performance_review',
            alert_data: { task: 'quarterly_review_due' },
            status: 'new',
            created_at: new Date().toISOString()
          }
        ]
      }
    }
  }

  // QA API Methods
  private async makeQARequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.qaBaseURL}${endpoint}`
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('QA API Request Error:', error)
      throw error
    }
  }

  /**
   * Get QA Reports from Linda's Frontend QA Agent
   */
  async getQAReports(): Promise<any> {
    return this.makeQARequest('/hr/qa/reports')
  }

  /**
   * Get Cross-Training data from Linda's QA Agent
   */
  async getQATraining(): Promise<any> {
    return this.makeQARequest('/hr/qa/training')
  }

  /**
   * Get Mentorship data from Linda's QA Agent
   */
  async getQAMentorship(): Promise<any> {
    return this.makeQARequest('/hr/qa/mentorship')
  }

  /**
   * Get Test Results from Linda's QA Agent
   */
  async getQATestResults(): Promise<any> {
    return this.makeQARequest('/hr/qa/test-results')
  }
}

// Export singleton instance
export const libraryAPI = new LibraryOfBabelAPI()

// Export class for testing
export { LibraryOfBabelAPI }