'use client'

import { UploadDropzone } from '@/components/upload/UploadDropzone'
import { BookOpen, Database, Cpu, Zap } from 'lucide-react'

export default function UploadPage() {
  return (
    <div className="min-h-screen bg-bg-primary">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Upload Books</h1>
          <p className="text-text-secondary">
            Upload EPUB files to add them to the Library of Babel. Files will be processed, chunked, and queued for embedding.
          </p>
        </div>

        {/* Pipeline Info */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-bg-card rounded-xl border border-gray-800 p-4 text-center">
            <BookOpen className="w-8 h-8 mx-auto mb-2 text-blue-400" />
            <p className="font-medium text-sm">1. Extract</p>
            <p className="text-text-secondary text-xs">Parse EPUB metadata & content</p>
          </div>
          <div className="bg-bg-card rounded-xl border border-gray-800 p-4 text-center">
            <Zap className="w-8 h-8 mx-auto mb-2 text-yellow-400" />
            <p className="font-medium text-sm">2. Chunk</p>
            <p className="text-text-secondary text-xs">Split into semantic passages</p>
          </div>
          <div className="bg-bg-card rounded-xl border border-gray-800 p-4 text-center">
            <Database className="w-8 h-8 mx-auto mb-2 text-green-400" />
            <p className="font-medium text-sm">3. Ingest</p>
            <p className="text-text-secondary text-xs">Store in PostgreSQL</p>
          </div>
          <div className="bg-bg-card rounded-xl border border-gray-800 p-4 text-center">
            <Cpu className="w-8 h-8 mx-auto mb-2 text-purple-400" />
            <p className="font-medium text-sm">4. Embed</p>
            <p className="text-text-secondary text-xs">Generate nomic vectors</p>
          </div>
        </div>

        {/* Dropzone */}
        <UploadDropzone />

        {/* Info */}
        <div className="mt-8 bg-bg-card rounded-xl border border-gray-800 p-4">
          <h3 className="font-medium mb-2">Processing Notes</h3>
          <ul className="text-text-secondary text-sm space-y-1">
            <li>Extraction, chunking, and ingestion happen immediately after upload.</li>
            <li>Embedding is queued for background processing (nomic overnight embedder).</li>
            <li>Books will be searchable once embedding completes.</li>
            <li>Maximum file size: 100MB per EPUB.</li>
            <li>Supported format: EPUB only (no PDF, MOBI, etc.)</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
