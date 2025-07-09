"use client"

import { Book, Clock, User, Hash, ExternalLink } from "lucide-react"
import { Button } from "@/components/ui/button"
import type { BookSearchResult } from "@/lib/api"

interface SearchResultsProps {
  results: BookSearchResult[]
  totalResults: number
  searchTime: number
  searchType: string | null
  query: string
  isLoading?: boolean
}

export function SearchResults({ 
  results, 
  totalResults, 
  searchTime, 
  searchType, 
  query,
  isLoading = false 
}: SearchResultsProps) {
  if (isLoading) {
    return (
      <div className="w-full max-w-4xl mx-auto px-4 mt-8">
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="border rounded-lg p-6 animate-pulse">
              <div className="h-4 bg-muted rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-muted rounded w-1/2 mb-4"></div>
              <div className="h-3 bg-muted rounded w-full mb-2"></div>
              <div className="h-3 bg-muted rounded w-5/6"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (results.length === 0 && !isLoading) {
    return (
      <div className="w-full max-w-4xl mx-auto px-4 mt-8">
        <div className="text-center py-12">
          <Book className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No results found</h3>
          <p className="text-muted-foreground mb-4">
            Try different keywords or check your spelling
          </p>
          <div className="space-y-2 text-sm text-muted-foreground">
            <p>Search suggestions:</p>
            <div className="flex flex-wrap justify-center gap-2">
              {[
                "consciousness",
                "philosophy", 
                "technology",
                "ethics",
                "society"
              ].map((suggestion) => (
                <Button
                  key={suggestion}
                  variant="outline"
                  size="sm"
                  className="text-xs"
                >
                  {suggestion}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div data-testid="search-results" className="w-full max-w-4xl mx-auto px-6 mt-12 fade-in">
      {/* Results Header - 留白 style with breathing room */}
      <div className="border-b border-gray-200 pb-6 mb-10">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6">
          <div>
            <h2 className="text-2xl font-light text-primary mb-2">
              Search Results
            </h2>
            <div className="flex items-center gap-6 text-sm text-tertiary">
              <span className="flex items-center gap-2">
                <Hash className="h-4 w-4" />
                {totalResults.toLocaleString()} results
              </span>
              <span className="flex items-center gap-2">
                <Clock className="h-4 w-4" />
                {(searchTime / 1000).toFixed(2)}s
              </span>
              {searchType && (
                <span className="px-3 py-1 bg-blue-50 text-blue-600 rounded-full text-xs font-medium">
                  {searchType} search
                </span>
              )}
            </div>
          </div>
          <div className="text-sm text-secondary">
            Searching: <span className="font-medium text-primary">&quot;{query}&quot;</span>
          </div>
        </div>
      </div>

      {/* Results List - Enhanced spacing and typography */}
      <div className="space-y-8">
        {results.map((result, index) => (
          <div
            key={`${result.book_id}-${result.chunk_id}-${index}`}
            data-testid="result-item"
            className="border border-gray-200 rounded-lg p-8 hover:shadow-md hover:border-gray-300 transition-all duration-200 bg-white"
          >
            {/* Book Header with improved hierarchy */}
            <div className="flex items-start justify-between mb-6">
              <div className="flex-1">
                <h3 
                  data-testid="book-title"
                  className="text-xl font-medium text-primary hover:text-blue-600 cursor-pointer transition-colors duration-150"
                >
                  {result.title}
                </h3>
                <div className="flex items-center gap-3 text-sm text-secondary mt-2">
                  <User className="h-4 w-4" />
                  <span className="font-medium">{result.author}</span>
                  {result.chapter && (
                    <>
                      <span className="text-gray-400">•</span>
                      <span>{result.chapter}</span>
                    </>
                  )}
                  {result.section && (
                    <>
                      <span className="text-gray-400">•</span>
                      <span>{result.section}</span>
                    </>
                  )}
                </div>
              </div>
              
              {result.relevance_score && (
                <div className="text-xs text-tertiary bg-gray-50 px-3 py-1 rounded-full">
                  {(result.relevance_score * 100).toFixed(1)}% match
                </div>
              )}
            </div>

            {/* Content Preview with better readability */}
            <div 
              data-testid="book-content"
              className="text-primary leading-relaxed mb-6 text-base"
            >
              <p className="line-clamp-4">
                {highlightSearchTerms(result.content, query)}
              </p>
            </div>

            {/* Action Buttons with refined styling */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Button variant="outline" size="sm" className="action-button">
                  <Book className="h-4 w-4 mr-2" />
                  View Book
                </Button>
                <Button variant="ghost" size="sm" className="text-secondary hover:text-primary">
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Read Chapter
                </Button>
              </div>
              
              <div className="text-xs text-tertiary">
                {result.word_count && `${result.word_count} words`}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Load More with improved spacing */}
      {results.length < totalResults && (
        <div className="text-center mt-12">
          <Button variant="outline" size="lg" className="action-button px-8 py-3">
            Load More Results
          </Button>
          <p className="text-sm text-tertiary mt-4">
            Showing {results.length} of {totalResults.toLocaleString()} results
          </p>
        </div>
      )}
    </div>
  )
}

// Helper function to highlight search terms in content
function highlightSearchTerms(content: string, query: string): React.ReactNode {
  if (!query || query.length < 2) return content

  const terms = query.toLowerCase().split(' ').filter(term => term.length > 2)
  let highlightedContent = content

  terms.forEach(term => {
    const regex = new RegExp(`(${term})`, 'gi')
    highlightedContent = highlightedContent.replace(
      regex, 
      '<mark class="bg-yellow-200 dark:bg-yellow-900 px-1 rounded">$1</mark>'
    )
  })

  return <div dangerouslySetInnerHTML={{ __html: highlightedContent }} />
}