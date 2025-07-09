import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { libraryAPI, type BookSearchResult } from './api'

interface SearchState {
  // Current search
  query: string
  isLoading: boolean
  results: BookSearchResult[]
  totalResults: number
  searchTime: number
  searchType: 'semantic' | 'topic' | 'keyword' | null
  error: string | null

  // Search history
  recentSearches: string[]
  
  // UI state
  selectedBook: BookSearchResult | null
  
  // Actions
  setQuery: (query: string) => void
  performSearch: (query: string) => Promise<void>
  clearResults: () => void
  setSelectedBook: (book: BookSearchResult | null) => void
  addToRecentSearches: (query: string) => void
  clearError: () => void
}

export const useSearchStore = create<SearchState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        query: '',
        isLoading: false,
        results: [],
        totalResults: 0,
        searchTime: 0,
        searchType: null,
        error: null,
        recentSearches: [],
        selectedBook: null,

        // Actions
        setQuery: (query: string) => {
          set({ query, error: null })
        },

        performSearch: async (query: string) => {
          if (!query.trim()) return

          set({ 
            isLoading: true, 
            error: null,
            query: query.trim()
          })

          try {
            const startTime = Date.now()
            
            // Perform semantic search as primary strategy
            const response = await libraryAPI.searchBooks(query.trim(), 20)
            
            const searchTime = Date.now() - startTime

            set({
              results: response.results,
              totalResults: response.total_results,
              searchTime: searchTime,
              searchType: response.search_type,
              isLoading: false,
              error: null
            })

            // Add to recent searches
            get().addToRecentSearches(query.trim())

          } catch (error) {
            console.error('Search error:', error)
            set({
              isLoading: false,
              error: error instanceof Error ? error.message : 'Search failed',
              results: [],
              totalResults: 0,
              searchTime: 0,
              searchType: null
            })
          }
        },

        clearResults: () => {
          set({
            results: [],
            totalResults: 0,
            searchTime: 0,
            searchType: null,
            error: null,
            selectedBook: null
          })
        },

        setSelectedBook: (book: BookSearchResult | null) => {
          set({ selectedBook: book })
        },

        addToRecentSearches: (query: string) => {
          const current = get().recentSearches
          const updated = [
            query,
            ...current.filter(q => q !== query)
          ].slice(0, 10) // Keep only last 10 searches
          
          set({ recentSearches: updated })
        },

        clearError: () => {
          set({ error: null })
        }
      }),
      {
        name: 'library-babel-search',
        partialize: (state) => ({
          recentSearches: state.recentSearches
        })
      }
    ),
    { name: 'library-babel-search' }
  )
)

// Additional stores for different features

interface UIState {
  theme: 'light' | 'dark' | 'system'
  sidebarOpen: boolean
  viewMode: 'grid' | 'list'
  
  setTheme: (theme: 'light' | 'dark' | 'system') => void
  toggleSidebar: () => void
  setViewMode: (mode: 'grid' | 'list') => void
}

export const useUIStore = create<UIState>()(
  devtools(
    persist(
      (set) => ({
        theme: 'system',
        sidebarOpen: false,
        viewMode: 'list',

        setTheme: (theme) => set({ theme }),
        toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
        setViewMode: (viewMode) => set({ viewMode })
      }),
      {
        name: 'library-babel-ui'
      }
    ),
    { name: 'library-babel-ui' }
  )
)