'use client'

import { SearchInterface } from '@/components/search'

export function LiveDemo() {
  return (
    <section className="max-w-6xl mx-auto px-4 py-16">
      {/* Section header */}
      <div className="text-center mb-10">
        <h2 className="text-3xl font-bold mb-3">Try It Live</h2>
        <p className="text-text-secondary text-lg max-w-2xl mx-auto">
          Search 4,939 books with semantic AI — this is a live demo running on our RAG pipeline.
        </p>
      </div>

      {/* Demo container with subtle glow */}
      <div className="relative">
        <div className="absolute -inset-px rounded-2xl bg-gradient-to-b from-model-technical/20 to-transparent pointer-events-none" />
        <div className="relative bg-bg-card border border-gray-800 rounded-2xl p-2 sm:p-4">
          <SearchInterface />
        </div>
      </div>

      {/* Footer note */}
      <p className="text-center text-text-secondary text-sm mt-6 max-w-2xl mx-auto">
        This demo searches a library of 4,939 books using Nomic embeddings. The same pipeline
        works with any document corpus.
      </p>
    </section>
  )
}
