'use client'

import { useState } from 'react'
import { Header } from '@/components/layout/Header'
import { EndpointCard } from '@/components/api-docs/EndpointCard'
import { TryItPanel } from '@/components/api-docs/TryItPanel'
import { Key, BookOpen, Search, Smartphone, Activity } from 'lucide-react'
import type { EndpointParameter } from '@/components/api-docs/EndpointCard'

// ---------------------------------------------------------------------------
// Endpoint definitions
// ---------------------------------------------------------------------------

interface EndpointDef {
  id: string
  group: string
  method: string
  path: string
  description: string
  parameters: EndpointParameter[]
  exampleResponse: string
}

const ENDPOINTS: EndpointDef[] = [
  // ---- Health & System ----
  {
    id: 'health-api',
    group: 'Health & System',
    method: 'GET',
    path: '/api/health',
    description: 'Full system health check including database, embeddings, and API status. No authentication required.',
    parameters: [],
    exampleResponse: JSON.stringify(
      {
        status: 'healthy',
        database: 'connected',
        books_count: 8673,
        embeddings: 'operational',
        uptime: '14d 6h 32m',
      },
      null,
      2
    ),
  },
  {
    id: 'health-simple',
    group: 'Health & System',
    method: 'GET',
    path: '/health',
    description: 'Simple health ping. Returns 200 if the server is running. No authentication required.',
    parameters: [],
    exampleResponse: JSON.stringify({ status: 'ok' }, null, 2),
  },

  // ---- Books ----
  {
    id: 'books-list',
    group: 'Books',
    method: 'GET',
    path: '/api/books?action=list',
    description: 'List books in the library with pagination, sorting, and genre filtering.',
    parameters: [
      { name: 'limit', type: 'integer', required: false, description: 'Number of books per page (default: 20, max: 100)' },
      { name: 'page', type: 'integer', required: false, description: 'Page number for pagination (default: 1)' },
      { name: 'sort_by', type: 'string', required: false, description: 'Sort field: title, author, date_added' },
      { name: 'genre', type: 'string', required: false, description: 'Filter by genre (e.g. fiction, philosophy, poetry)' },
    ],
    exampleResponse: JSON.stringify(
      {
        status: 'success',
        data: {
          books: [
            {
              id: 42,
              title: 'The Garden of Forking Paths',
              author: 'Jorge Luis Borges',
              genre: 'fiction',
              total_pages: 12,
            },
          ],
          pagination: { page: 1, limit: 20, total: 8673 },
        },
      },
      null,
      2
    ),
  },
  {
    id: 'books-summary',
    group: 'Books',
    method: 'GET',
    path: '/api/books?action=summary&id={id}',
    description: 'Get detailed metadata and summary for a specific book.',
    parameters: [
      { name: 'id', type: 'integer', required: true, description: 'Book ID' },
    ],
    exampleResponse: JSON.stringify(
      {
        status: 'success',
        data: {
          id: 42,
          title: 'The Garden of Forking Paths',
          author: 'Jorge Luis Borges',
          genre: 'fiction',
          total_pages: 12,
          total_chunks: 87,
          date_added: '2024-03-15',
        },
      },
      null,
      2
    ),
  },
  {
    id: 'books-toc',
    group: 'Books',
    method: 'GET',
    path: '/api/books?action=toc&id={id}',
    description: 'Get the table of contents for a book, including chapter titles and page numbers.',
    parameters: [
      { name: 'id', type: 'integer', required: true, description: 'Book ID' },
    ],
    exampleResponse: JSON.stringify(
      {
        status: 'success',
        data: {
          book_id: 42,
          title: 'The Garden of Forking Paths',
          chapters: [
            { chapter: 1, title: 'The Labyrinth', page: 1 },
            { chapter: 2, title: 'Ts\'ui Pen', page: 5 },
          ],
        },
      },
      null,
      2
    ),
  },
  {
    id: 'books-page',
    group: 'Books',
    method: 'GET',
    path: '/api/books?action=page&id={id}&page={n}',
    description: 'Read a specific page of a book. Returns the page content with navigation links.',
    parameters: [
      { name: 'id', type: 'integer', required: true, description: 'Book ID' },
      { name: 'page', type: 'integer', required: true, description: 'Page number' },
    ],
    exampleResponse: JSON.stringify(
      {
        status: 'success',
        data: {
          book_id: 42,
          title: 'The Garden of Forking Paths',
          page_number: 1,
          content: 'On page 22 of Liddell Hart\'s History of World War I...',
          pagination_info: { total_pages: 12 },
          navigation: {
            previous_page: null,
            next_page: '/api/books?action=page&id=42&page=2',
          },
        },
      },
      null,
      2
    ),
  },

  // ---- Search ----
  {
    id: 'search-basic',
    group: 'Search',
    method: 'GET',
    path: '/api/search?action=search&q={query}',
    description: 'Basic full-text search across all books. Returns matching passages with relevance scores.',
    parameters: [
      { name: 'q', type: 'string', required: true, description: 'Search query text' },
      { name: 'limit', type: 'integer', required: false, description: 'Maximum results to return (default: 10, max: 50)' },
      { name: 'type', type: 'string', required: false, description: 'Search type: text, title, author' },
    ],
    exampleResponse: JSON.stringify(
      {
        status: 'success',
        data: {
          results: [
            {
              book_id: 42,
              book_title: 'The Garden of Forking Paths',
              author: 'Jorge Luis Borges',
              chunk_text: 'The garden of forking paths is an enormous riddle...',
              similarity_score: 0.95,
            },
          ],
          total: 1,
          query: 'forking paths',
        },
      },
      null,
      2
    ),
  },
  {
    id: 'search-semantic',
    group: 'Search',
    method: 'GET',
    path: '/api/search?action=semantic_passages&q={query}',
    description: 'AI-powered semantic search using embedding models. Finds conceptually similar passages even without exact keyword matches.',
    parameters: [
      { name: 'q', type: 'string', required: true, description: 'Semantic search query (natural language)' },
      { name: 'limit', type: 'integer', required: false, description: 'Maximum results to return (default: 10, max: 50)' },
      { name: 'genre', type: 'string', required: false, description: 'Filter results by genre' },
    ],
    exampleResponse: JSON.stringify(
      {
        status: 'success',
        data: {
          results: [
            {
              book_id: 42,
              book_title: 'The Garden of Forking Paths',
              author: 'Jorge Luis Borges',
              chunk_text: 'Time forks perpetually toward innumerable futures...',
              similarity_score: 0.92,
              model_used: 'nomic-embed-text',
              genre: 'fiction',
            },
          ],
          total: 1,
          query: 'the nature of time and parallel realities',
          model: 'nomic-embed-text',
        },
      },
      null,
      2
    ),
  },
  {
    id: 'search-count',
    group: 'Search',
    method: 'GET',
    path: '/api/search?action=count&q={query}',
    description: 'Get the number of search results for a query without returning the full results.',
    parameters: [
      { name: 'q', type: 'string', required: true, description: 'Search query text' },
    ],
    exampleResponse: JSON.stringify(
      {
        status: 'success',
        data: { count: 247, query: 'labyrinth' },
      },
      null,
      2
    ),
  },
  {
    id: 'search-books',
    group: 'Search',
    method: 'GET',
    path: '/api/search?action=books&q={query}',
    description: 'Search for books by title or metadata. Returns book-level results rather than individual passages.',
    parameters: [
      { name: 'q', type: 'string', required: true, description: 'Book search query' },
    ],
    exampleResponse: JSON.stringify(
      {
        status: 'success',
        data: {
          books: [
            {
              id: 42,
              title: 'The Garden of Forking Paths',
              author: 'Jorge Luis Borges',
              genre: 'fiction',
              total_pages: 12,
            },
          ],
          total: 1,
          query: 'Borges',
        },
      },
      null,
      2
    ),
  },

  // ---- Mobile / Shortcuts ----
  {
    id: 'mobile-random',
    group: 'Mobile / Shortcuts',
    method: 'GET',
    path: '/api/mobile/random?type=title',
    description: 'Get a random book title from the library. Useful for discovery features and "I\'m Feeling Lucky" flows.',
    parameters: [],
    exampleResponse: JSON.stringify(
      {
        status: 'success',
        data: { title: 'The Library of Babel', author: 'Jorge Luis Borges', id: 42 },
      },
      null,
      2
    ),
  },
  {
    id: 'mobile-stats',
    group: 'Mobile / Shortcuts',
    method: 'GET',
    path: '/api/mobile/stats?type=count',
    description: 'Get total book count in the library. Lightweight endpoint for dashboards and status displays.',
    parameters: [],
    exampleResponse: JSON.stringify(
      {
        status: 'success',
        data: { count: 8673 },
      },
      null,
      2
    ),
  },
  {
    id: 'mobile-search-count',
    group: 'Mobile / Shortcuts',
    method: 'GET',
    path: '/api/mobile/search?q={query}&action=count',
    description: 'Mobile-optimized search count. Returns just the number of matching results for a query.',
    parameters: [
      { name: 'q', type: 'string', required: true, description: 'Search query text' },
    ],
    exampleResponse: JSON.stringify(
      {
        status: 'success',
        data: { count: 42, query: 'infinite library' },
      },
      null,
      2
    ),
  },
]

// ---------------------------------------------------------------------------
// Group config
// ---------------------------------------------------------------------------

interface GroupMeta {
  label: string
  icon: React.ReactNode
  description: string
}

const GROUP_META: Record<string, GroupMeta> = {
  'Health & System': {
    label: 'Health & System',
    icon: <Activity className="w-5 h-5 text-green-400" />,
    description: 'Server health and system status endpoints. No authentication required.',
  },
  Books: {
    label: 'Books',
    icon: <BookOpen className="w-5 h-5 text-model-general" />,
    description: 'Browse, list, and read books in the library.',
  },
  Search: {
    label: 'Search',
    icon: <Search className="w-5 h-5 text-model-technical" />,
    description: 'Full-text and AI-powered semantic search across all books and passages.',
  },
  'Mobile / Shortcuts': {
    label: 'Mobile / Shortcuts',
    icon: <Smartphone className="w-5 h-5 text-model-specialized" />,
    description: 'Lightweight endpoints optimized for mobile apps and quick lookups.',
  },
}

// Derive ordered groups from the endpoint list to preserve definition order
const GROUPS = Array.from(new Set(ENDPOINTS.map((e) => e.group)))

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export default function ApiDocsPage() {
  const [tryItEndpoint, setTryItEndpoint] = useState<EndpointDef | null>(null)

  return (
    <main className="min-h-screen">
      <Header />

      <div className="max-w-4xl mx-auto px-4 py-10">
        {/* Page header */}
        <div className="mb-10">
          <h1 className="text-3xl font-bold text-text-primary mb-2">API Reference</h1>
          <p className="text-text-secondary text-lg">
            Integrate LibraryOfBabel&apos;s semantic search into your applications
          </p>
        </div>

        {/* Authentication section */}
        <section className="mb-10 bg-bg-card rounded-lg border border-gray-800 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-model-technical/15">
              <Key className="w-5 h-5 text-model-technical" />
            </div>
            <h2 className="text-xl font-semibold text-text-primary">Authentication</h2>
          </div>
          <p className="text-text-secondary mb-4">
            Most endpoints require an API key passed via the{' '}
            <code className="px-1.5 py-0.5 rounded bg-bg-primary font-mono text-sm text-model-general">
              X-API-Key
            </code>{' '}
            request header. Health check endpoints are publicly accessible without authentication.
          </p>
          <div className="rounded-lg overflow-hidden">
            <pre className="bg-[#16162a] p-4 overflow-x-auto">
              <code className="font-mono text-sm text-text-primary">
                {`curl -H "X-API-Key: your_api_key_here" \\
  https://api.example.com/api/books?action=list`}
              </code>
            </pre>
          </div>
        </section>

        {/* Endpoint groups */}
        {GROUPS.map((group) => {
          const meta = GROUP_META[group]
          const endpoints = ENDPOINTS.filter((e) => e.group === group)
          return (
            <section key={group} className="mb-10">
              <div className="flex items-center gap-3 mb-2">
                {meta?.icon}
                <h2 className="text-xl font-semibold text-text-primary">{meta?.label ?? group}</h2>
              </div>
              {meta?.description && (
                <p className="text-text-secondary text-sm mb-5 ml-8">{meta.description}</p>
              )}

              <div className="space-y-4">
                {endpoints.map((ep) => (
                  <EndpointCard
                    key={ep.id}
                    method={ep.method}
                    path={ep.path}
                    description={ep.description}
                    parameters={ep.parameters}
                    exampleResponse={ep.exampleResponse}
                    onTryIt={() => setTryItEndpoint(ep)}
                  />
                ))}
              </div>
            </section>
          )
        })}
      </div>

      {/* Try It panel (modal) */}
      {tryItEndpoint && (
        <TryItPanel
          endpoint={{
            method: tryItEndpoint.method,
            path: tryItEndpoint.path,
            parameters: tryItEndpoint.parameters,
          }}
          onClose={() => setTryItEndpoint(null)}
        />
      )}
    </main>
  )
}
