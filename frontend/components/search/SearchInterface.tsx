'use client'

import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, Brain, Clock, Loader2 } from 'lucide-react'
import { api, createSearchQueryKey } from '@/lib/api'
import type { SearchType, SearchResult } from '@/types'
import { SEARCH_TYPES } from '@/types'
import { SearchTypeSelector } from './SearchTypeSelector'
import { ResultCard } from './ResultCard'

// Suggested queries per search type
const SUGGESTIONS: Partial<Record<SearchType, string[]>> = {
  semantic_passages: ['philosophy of mind', 'quantum mechanics', 'human nature'],
  semantic: ['science fiction', 'philosophy', 'psychology'],
  emotional: ['grief', 'hope', 'fear', 'joy'],
  discovery: ['dystopia', 'cyberpunk', 'noir'],
  content_analysis: ['capitalism', 'power', 'identity'],
  style: ['poetic', 'technical', 'minimalist'],
}

export function SearchInterface() {
  const [query, setQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [searchType, setSearchType] = useState<SearchType>('semantic_passages')

  const handleSearch = useCallback((value: string) => {
    setQuery(value)
    // Debounce: wait 300ms after user stops typing
    const timer = setTimeout(() => {
      if (value.trim().length >= 2) {
        setDebouncedQuery(value.trim())
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [])

  const { data, isLoading, error } = useQuery({
    queryKey: createSearchQueryKey(debouncedQuery, searchType),
    queryFn: () => api.search(debouncedQuery, searchType, 20),
    enabled: debouncedQuery.length >= 2,
  })

  const typeInfo = SEARCH_TYPES[searchType]
  const suggestions = SUGGESTIONS[searchType] || SUGGESTIONS.semantic!

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold mb-2">LibraryOfBabel</h1>
        <p className="text-text-secondary text-lg">
          Explore 4,932 books with AI-powered search
        </p>
      </div>

      {/* Search Box */}
      <div className="bg-bg-card rounded-xl p-6 mb-6 border border-gray-800">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-text-secondary w-5 h-5" />
          <input
            type="text"
            value={query}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder={typeInfo.placeholder}
            className="w-full bg-bg-primary border border-gray-700 rounded-lg py-4 px-12 text-lg
                       focus:outline-none focus:ring-2 focus:ring-model-technical focus:border-transparent
                       placeholder:text-text-secondary"
          />
          {isLoading && (
            <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 text-model-technical w-5 h-5 animate-spin" />
          )}
        </div>

        {/* Search Type Selector */}
        <div className="mt-4">
          <SearchTypeSelector selected={searchType} onSelect={setSearchType} />
        </div>

        {/* Dynamic Suggestions */}
        <div className="mt-4 flex gap-2 flex-wrap">
          <span className="text-text-secondary text-sm">Try:</span>
          {suggestions.map((term) => (
            <button
              key={term}
              onClick={() => {
                setQuery(term)
                setDebouncedQuery(term)
              }}
              className="text-sm px-3 py-1 rounded-full bg-bg-primary border border-gray-700
                         hover:border-model-technical transition-colors"
            >
              {term}
            </button>
          ))}
        </div>
      </div>

      {/* Results Area */}
      <div className="flex gap-6">
        {/* Filters Sidebar */}
        <div className="w-48 flex-shrink-0 hidden lg:block">
          <div className="bg-bg-card rounded-xl p-4 border border-gray-800 sticky top-4">
            <h3 className="font-semibold mb-4">Filters</h3>

            <div className="space-y-4">
              <div>
                <label className="text-sm text-text-secondary">Sort By</label>
                <div className="mt-2 space-y-2">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input type="radio" name="sort" defaultChecked className="accent-model-technical" />
                    <span className="text-sm">Relevance</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input type="radio" name="sort" className="accent-model-technical" />
                    <span className="text-sm">Date</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input type="radio" name="sort" className="accent-model-technical" />
                    <span className="text-sm">Author</span>
                  </label>
                </div>
              </div>

              {/* Stats */}
              {data && (
                <div className="pt-4 border-t border-gray-700">
                  <div className="text-sm text-text-secondary mb-1">Results</div>
                  <div className="font-semibold">{data.count} found</div>
                  <div className="text-sm text-text-secondary flex items-center gap-1 mt-2">
                    <Clock className="w-3 h-3" />
                    {data.response_time_ms}ms
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Results */}
        <div className="flex-1">
          {error && (
            <div className="bg-red-900/20 border border-red-800 rounded-xl p-4 text-red-400">
              Error: {error instanceof Error ? error.message : 'Failed to search'}
            </div>
          )}

          {!debouncedQuery && !isLoading && (
            <div className="text-center py-16 text-text-secondary">
              <Brain className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p>Enter a search query to explore the library</p>
            </div>
          )}

          {isLoading && (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-bg-card rounded-xl p-6 border border-gray-800">
                  <div className="skeleton h-6 w-3/4 rounded mb-3" />
                  <div className="skeleton h-4 w-1/2 rounded mb-4" />
                  <div className="skeleton h-20 w-full rounded" />
                </div>
              ))}
            </div>
          )}

          {data && data.results.length > 0 && (
            <div className="space-y-4">
              {data.results.map((result, index) => (
                <ResultCard key={`${result.book_id}-${result.chunk_id}-${index}`} result={result} />
              ))}
            </div>
          )}

          {data && data.results.length === 0 && debouncedQuery && (
            <div className="text-center py-16 text-text-secondary">
              <p>No results found for "{debouncedQuery}"</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
