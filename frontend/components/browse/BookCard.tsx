'use client'

import { useState } from 'react'
import { Search, BookOpen, X } from 'lucide-react'
import type { Book } from '@/types'
import * as Dialog from '@radix-ui/react-dialog'

interface BookCardProps {
  book: Book
  viewMode: 'grid' | 'list'
}

function getGenreColor(genre?: string): string {
  const colors: Record<string, string> = {
    'Philosophy': 'from-purple-600 to-purple-900',
    'Science Fiction': 'from-blue-600 to-indigo-900',
    'Sci-Fi': 'from-blue-600 to-indigo-900',
    'Technology': 'from-green-600 to-emerald-900',
    'Fiction': 'from-rose-600 to-pink-900',
    'History': 'from-amber-600 to-orange-900',
    'Science': 'from-cyan-600 to-teal-900',
    'Biography': 'from-gray-500 to-slate-800',
  }
  return colors[genre || ''] || 'from-gray-600 to-gray-900'
}

export function BookCard({ book, viewMode }: BookCardProps) {
  const [isOpen, setIsOpen] = useState(false)

  if (viewMode === 'list') {
    return (
      <div className="bg-bg-card rounded-xl border border-gray-800 p-4 flex items-center gap-4 hover:border-gray-700 transition-colors">
        {/* Mini Cover */}
        <div className={`w-16 h-20 rounded bg-gradient-to-br ${getGenreColor(book.genre)} flex items-center justify-center flex-shrink-0`}>
          <BookOpen className="w-8 h-8 text-white/60" />
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold truncate">{book.title}</h3>
          <p className="text-text-secondary text-sm truncate">{book.author}</p>
          <div className="flex items-center gap-3 mt-1 text-xs text-text-secondary">
            {book.genre && <span>{book.genre}</span>}
            {book.word_count && <span>{book.word_count.toLocaleString()} words</span>}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2 flex-shrink-0">
          <button className="p-2 rounded-lg bg-bg-primary border border-gray-700 hover:border-model-technical">
            <Search className="w-4 h-4" />
          </button>
        </div>
      </div>
    )
  }

  return (
    <Dialog.Root open={isOpen} onOpenChange={setIsOpen}>
      <div className="bg-bg-card rounded-xl border border-gray-800 overflow-hidden hover:border-gray-700 transition-colors">
        {/* Generated Cover */}
        <div className={`h-32 bg-gradient-to-br ${getGenreColor(book.genre)} flex items-center justify-center`}>
          <BookOpen className="w-12 h-12 text-white/60" />
        </div>

        {/* Content */}
        <div className="p-4">
          <h3 className="font-semibold line-clamp-2 mb-1">{book.title}</h3>
          <p className="text-text-secondary text-sm truncate">{book.author}</p>

          <div className="flex items-center gap-2 mt-3 text-xs">
            {book.genre && (
              <span className="px-2 py-0.5 rounded bg-bg-primary border border-gray-700">
                {book.genre}
              </span>
            )}
            {book.word_count && (
              <span className="text-text-secondary">{book.word_count.toLocaleString()} words</span>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-2 mt-4">
            <button className="flex-1 flex items-center justify-center gap-1 py-2 rounded-lg bg-bg-primary border border-gray-700 text-sm hover:border-model-technical transition-colors">
              <Search className="w-4 h-4" />
              Search
            </button>
            <Dialog.Trigger asChild>
              <button className="flex-1 flex items-center justify-center gap-1 py-2 rounded-lg bg-bg-primary border border-gray-700 text-sm hover:border-gray-600 transition-colors">
                <BookOpen className="w-4 h-4" />
                Details
              </button>
            </Dialog.Trigger>
          </div>
        </div>
      </div>

      {/* Book Detail Modal */}
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-bg-card border border-gray-800 rounded-xl w-full max-w-lg max-h-[85vh] overflow-y-auto">
          <div className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <Dialog.Title className="text-xl font-bold">{book.title}</Dialog.Title>
                <Dialog.Description className="text-text-secondary mt-1">
                  {book.author}
                </Dialog.Description>
              </div>
              <Dialog.Close asChild>
                <button className="p-1 rounded hover:bg-bg-primary">
                  <X className="w-5 h-5" />
                </button>
              </Dialog.Close>
            </div>

            <div className="space-y-4">
              <div>
                <h4 className="text-sm text-text-secondary mb-1">Genre</h4>
                <p>{book.genre || 'Unknown'}</p>
              </div>

              <div>
                <h4 className="text-sm text-text-secondary mb-1">Word Count</h4>
                <p>{book.word_count?.toLocaleString() || 'Unknown'} words</p>
              </div>

              {book.model_type && (
                <div>
                  <h4 className="text-sm text-text-secondary mb-1">AI Model</h4>
                  <p>{book.model_type}</p>
                </div>
              )}

              {/* Search within book */}
              <div className="pt-4 border-t border-gray-800">
                <h4 className="text-sm text-text-secondary mb-2">Search this book</h4>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary" />
                  <input
                    type="text"
                    placeholder={`Search within ${book.title}...`}
                    className="w-full bg-bg-primary border border-gray-700 rounded-lg py-2 pl-10 pr-4
                               focus:outline-none focus:ring-1 focus:ring-model-technical"
                  />
                </div>
              </div>
            </div>

            <div className="mt-6">
              <Dialog.Close asChild>
                <button className="w-full py-2 rounded-lg bg-bg-primary border border-gray-700 hover:border-gray-600">
                  Close
                </button>
              </Dialog.Close>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
