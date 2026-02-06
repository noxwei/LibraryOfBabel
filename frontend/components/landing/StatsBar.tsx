'use client'

import { useEffect, useState } from 'react'
import { BookOpen, Layers, Box, Zap } from 'lucide-react'

interface HealthData {
  total_books?: number
  total_chunks?: number
}

const FALLBACK = {
  total_books: 4939,
  total_chunks: 2114019,
}

const stats = [
  { key: 'books' as const, label: 'Total Books', icon: BookOpen },
  { key: 'chunks' as const, label: 'Total Chunks', icon: Layers },
  { key: 'dimensions' as const, label: 'Embedding Dimensions', icon: Box },
  { key: 'speed' as const, label: 'Search Speed', icon: Zap },
]

function formatNumber(n: number): string {
  return n.toLocaleString()
}

export function StatsBar() {
  const [data, setData] = useState<HealthData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json())
      .then((json) => {
        setData(json)
        setLoading(false)
      })
      .catch(() => {
        setData(null)
        setLoading(false)
      })
  }, [])

  const books = data?.total_books ?? FALLBACK.total_books
  const chunks = data?.total_chunks ?? FALLBACK.total_chunks

  const values: Record<string, string> = {
    books: formatNumber(books),
    chunks: formatNumber(chunks),
    dimensions: '768',
    speed: '<100ms',
  }

  return (
    <section className="max-w-6xl mx-auto px-4 py-8">
      <div className="bg-bg-card border border-gray-800 rounded-xl p-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {stats.map(({ key, label, icon: Icon }) => (
            <div key={key} className="text-center">
              <Icon className="w-5 h-5 text-model-technical mx-auto mb-2" />
              {loading ? (
                <div className="skeleton h-8 w-24 mx-auto rounded mb-1" />
              ) : (
                <div className="text-2xl sm:text-3xl font-bold text-text-primary">
                  {values[key]}
                </div>
              )}
              <div className="text-text-secondary text-sm mt-1">{label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
