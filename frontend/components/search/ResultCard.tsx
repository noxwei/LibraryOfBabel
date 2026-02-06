'use client'

import { useState } from 'react'
import { Copy, Link, BookOpen, ChevronDown, ChevronUp, Check, X, Loader2 } from 'lucide-react'
import * as Dialog from '@radix-ui/react-dialog'
import type { SearchResult } from '@/types'

interface ResultCardProps {
  result: SearchResult
}

interface BookContext {
  content: string
  title: string
  page_number: number
  total_pages: number
  navigation: {
    next_page: string | null
    previous_page: string | null
  }
}

function getRelevanceColor(score: number): string {
  if (isNaN(score) || score >= 0.9) return 'bg-relevance-high'
  if (score >= 0.7) return 'bg-relevance-medium'
  return 'bg-relevance-low'
}

function getRelevanceText(score: number): string {
  if (isNaN(score)) return 'N/A'
  return `${(score * 100).toFixed(1)}%`
}

function getModelColor(model?: string): string {
  const modelMap: Record<string, string> = {
    'granite': 'text-model-technical bg-model-technical/10',
    'bge': 'text-model-creative bg-model-creative/10',
    'mxbai': 'text-model-multilingual bg-model-multilingual/10',
    'nomic': 'text-model-general bg-model-general/10',
    'snowflake': 'text-model-specialized bg-model-specialized/10',
  }

  if (!model) return 'text-gray-400 bg-gray-400/10'

  const key = Object.keys(modelMap).find(k => model.toLowerCase().includes(k))
  return key ? modelMap[key] : 'text-gray-400 bg-gray-400/10'
}

export function ResultCard({ result }: ResultCardProps) {
  const [expanded, setExpanded] = useState(false)
  const [copied, setCopied] = useState(false)
  const [contextOpen, setContextOpen] = useState(false)
  const [context, setContext] = useState<BookContext | null>(null)
  const [contextLoading, setContextLoading] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(result.chunk_text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleCite = async () => {
    const citation = `"${result.chunk_text.slice(0, 100)}..." — ${result.author}, ${result.book_title}`
    await navigator.clipboard.writeText(citation)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const fetchContext = async (pageUrl?: string) => {
    setContextLoading(true)
    try {
      const url = pageUrl || result.extra?.reading_link || `/api/books?action=page&id=${result.book_id}&page=1`
      const response = await fetch(url)
      const json = await response.json()
      const data = json.data?.data || json.data
      setContext({
        content: data.content,
        title: data.title,
        page_number: data.page_number,
        total_pages: data.pagination_info?.total_pages || 1,
        navigation: {
          next_page: data.navigation?.next_page,
          previous_page: data.navigation?.previous_page,
        }
      })
    } catch (error) {
      console.error('Failed to fetch context:', error)
    } finally {
      setContextLoading(false)
    }
  }

  const handleContextOpen = (open: boolean) => {
    setContextOpen(open)
    if (open && !context) {
      fetchContext()
    }
  }

  return (
    <div className="bg-bg-card rounded-xl border border-gray-800 overflow-hidden hover:border-gray-700 transition-colors">
      {/* Header */}
      <div className="p-4 border-b border-gray-800">
        <div className="flex justify-between items-start gap-4">
          <div>
            <h3 className="font-semibold text-lg">{result.book_title}</h3>
            <p className="text-text-secondary text-sm">
              {result.author}
              {result.genre && ` • ${result.genre}`}
            </p>
          </div>

          <div className="flex gap-2 flex-shrink-0">
            {/* Model Badge */}
            {result.model_used && (
              <span className={`px-2 py-1 rounded text-xs font-medium ${getModelColor(result.model_used)}`}>
                {result.model_used}
              </span>
            )}
          </div>
        </div>

        {/* Metrics Row */}
        <div className="flex items-center gap-4 mt-3 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-text-secondary">Relevance:</span>
            <div className="flex items-center gap-1">
              <div className={`w-2 h-2 rounded-full ${getRelevanceColor(result.similarity_score)}`} />
              <span className="font-mono">{getRelevanceText(result.similarity_score)}</span>
            </div>
          </div>

          {result.response_time_ms && (
            <div className="text-text-secondary">
              <span className="font-mono">{result.response_time_ms}ms</span>
            </div>
          )}

          <div className="text-text-secondary font-mono">
            Chunk #{result.chunk_id}
          </div>
        </div>
      </div>

      {/* Extra Type-Specific Info */}
      {result.extra && (
        <div className="px-4 py-2 border-b border-gray-800 bg-bg-primary/50">
          <div className="flex flex-wrap gap-3 text-sm">
            {/* Emotional search */}
            {result.extra.emotion && (
              <span className="px-2 py-1 rounded bg-model-creative/20 text-model-creative">
                💭 {result.extra.emotion}
              </span>
            )}

            {/* Discovery search */}
            {result.extra.subgenres && result.extra.subgenres.length > 0 && (
              <span className="text-text-secondary">
                Subgenres: {result.extra.subgenres.slice(0, 3).join(', ')}
              </span>
            )}
            {result.extra.narrative_voice && (
              <span className="text-text-secondary">
                Voice: {result.extra.narrative_voice}
              </span>
            )}

            {/* Content analysis */}
            {result.extra.dominant_themes && result.extra.dominant_themes.length > 0 && (
              <span className="text-text-secondary">
                Themes: {result.extra.dominant_themes.slice(0, 3).map(t => t.theme).join(', ')}
              </span>
            )}

            {/* Passages */}
            {result.extra.word_count && (
              <span className="text-text-secondary">
                {result.extra.word_count.toLocaleString()} words
              </span>
            )}
            {result.extra.chunk_type && (
              <span className="px-2 py-1 rounded bg-gray-700 text-gray-300">
                {result.extra.chunk_type}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Content */}
      <div className="p-4">
        <p className={`text-text-primary leading-relaxed ${expanded ? '' : 'line-clamp-4'}`}>
          {result.chunk_text || result.extra?.style_preview || result.extra?.quality_preview || 'No preview available'}
        </p>

        {(result.chunk_text?.length || 0) > 300 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-model-technical text-sm mt-2 hover:underline"
          >
            {expanded ? (
              <>
                Show less <ChevronUp className="w-4 h-4" />
              </>
            ) : (
              <>
                Show more <ChevronDown className="w-4 h-4" />
              </>
            )}
          </button>
        )}
      </div>

      {/* Actions */}
      <div className="px-4 pb-4 flex gap-2">
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-bg-primary border border-gray-700
                     hover:border-gray-600 transition-colors text-sm"
        >
          {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
          Copy
        </button>
        <button
          onClick={handleCite}
          className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-bg-primary border border-gray-700
                     hover:border-gray-600 transition-colors text-sm"
        >
          <Link className="w-4 h-4" />
          Cite
        </button>
        <Dialog.Root open={contextOpen} onOpenChange={handleContextOpen}>
          <Dialog.Trigger asChild>
            <button
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-bg-primary border border-gray-700
                         hover:border-gray-600 transition-colors text-sm"
            >
              <BookOpen className="w-4 h-4" />
              Context
            </button>
          </Dialog.Trigger>

          <Dialog.Portal>
            <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm" />
            <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-bg-card border border-gray-800 rounded-xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
              <div className="p-4 border-b border-gray-800 flex justify-between items-start">
                <div>
                  <Dialog.Title className="text-lg font-bold">{result.book_title}</Dialog.Title>
                  <Dialog.Description className="text-text-secondary text-sm">
                    {result.author} {context && `• Page ${context.page_number} of ${context.total_pages}`}
                  </Dialog.Description>
                </div>
                <Dialog.Close asChild>
                  <button className="p-1 rounded hover:bg-bg-primary">
                    <X className="w-5 h-5" />
                  </button>
                </Dialog.Close>
              </div>

              <div className="flex-1 overflow-y-auto p-4">
                {contextLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-model-technical" />
                  </div>
                ) : context ? (
                  <p className="text-text-primary leading-relaxed whitespace-pre-wrap">
                    {context.content}
                  </p>
                ) : (
                  <p className="text-text-secondary">Failed to load context</p>
                )}
              </div>

              {context && (
                <div className="p-4 border-t border-gray-800 flex justify-between">
                  <button
                    onClick={() => context.navigation.previous_page && fetchContext(context.navigation.previous_page)}
                    disabled={!context.navigation.previous_page}
                    className="px-4 py-2 rounded-lg bg-bg-primary border border-gray-700 hover:border-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => context.navigation.next_page && fetchContext(context.navigation.next_page)}
                    disabled={!context.navigation.next_page}
                    className="px-4 py-2 rounded-lg bg-bg-primary border border-gray-700 hover:border-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              )}
            </Dialog.Content>
          </Dialog.Portal>
        </Dialog.Root>
      </div>
    </div>
  )
}
