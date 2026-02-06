import { SearchInterface } from '@/components/search'
import { Header } from '@/components/layout/Header'

export default function DemoPage() {
  return (
    <main className="min-h-screen">
      <Header />
      <div className="max-w-6xl mx-auto px-4 pt-8 pb-4">
        <h1 className="text-2xl font-bold mb-2">Live Demo</h1>
        <p className="text-text-secondary mb-6">
          Semantic search across 4,939 books — powered by the same offline RAG pipeline you can deploy on your own infrastructure.
        </p>
      </div>
      <SearchInterface />
    </main>
  )
}
