'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { LayoutGrid, List, ChevronLeft, ChevronRight } from 'lucide-react'
import { api, createBooksQueryKey } from '@/lib/api'
import { BookCard } from './BookCard'

type ViewMode = 'grid' | 'list'

export function BrowseLibrary() {
  const [page, setPage] = useState(1)
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const limit = 20

  const { data, isLoading, error } = useQuery({
    queryKey: createBooksQueryKey(page, limit),
    queryFn: () => api.getBooks(page, limit),
  })

  const totalPages = data ? Math.ceil(data.total / limit) : 0

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Library Browse</h1>
          <p className="text-text-secondary mt-1">
            {data ? `${data.total.toLocaleString()} books` : 'Loading...'}
          </p>
        </div>

        {/* View Toggle */}
        <div className="flex items-center gap-2 bg-bg-card border border-gray-800 rounded-lg p-1">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-2 rounded ${viewMode === 'grid' ? 'bg-bg-primary' : ''}`}
          >
            <LayoutGrid className="w-5 h-5" />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-2 rounded ${viewMode === 'list' ? 'bg-bg-primary' : ''}`}
          >
            <List className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Genre Filters - Horizontal scroll */}
      <div className="flex gap-2 overflow-x-auto pb-4 mb-6 scrollbar-hide">
        {['All', 'Philosophy', 'Sci-Fi', 'Technology', 'Fiction', 'History', 'Science', 'Biography'].map(
          (genre) => (
            <button
              key={genre}
              className={`px-4 py-2 rounded-full text-sm whitespace-nowrap border transition-colors
                ${genre === 'All'
                  ? 'bg-model-technical text-white border-model-technical'
                  : 'bg-bg-card border-gray-700 hover:border-gray-600'
                }`}
            >
              {genre}
            </button>
          )
        )}
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-xl p-4 text-red-400">
          Error loading books: {error instanceof Error ? error.message : 'Unknown error'}
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className={`grid gap-4 ${viewMode === 'grid' ? 'grid-cols-2 md:grid-cols-3 lg:grid-cols-4' : 'grid-cols-1'}`}>
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="bg-bg-card rounded-xl p-4 border border-gray-800">
              <div className="skeleton h-32 rounded-lg mb-3" />
              <div className="skeleton h-4 w-3/4 rounded mb-2" />
              <div className="skeleton h-3 w-1/2 rounded" />
            </div>
          ))}
        </div>
      )}

      {/* Books Grid/List */}
      {data && (
        <div className={`grid gap-4 ${viewMode === 'grid' ? 'grid-cols-2 md:grid-cols-3 lg:grid-cols-4' : 'grid-cols-1'}`}>
          {data.books.map((book) => (
            <BookCard key={book.id} book={book} viewMode={viewMode} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {data && totalPages > 1 && (
        <div className="flex items-center justify-center gap-4 mt-8">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="flex items-center gap-1 px-4 py-2 rounded-lg bg-bg-card border border-gray-700
                       hover:border-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-4 h-4" />
            Previous
          </button>

          <span className="text-text-secondary">
            Page {page} of {totalPages}
          </span>

          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="flex items-center gap-1 px-4 py-2 rounded-lg bg-bg-card border border-gray-700
                       hover:border-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  )
}
