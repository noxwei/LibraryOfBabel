'use client'

import { useState, useCallback } from 'react'
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, X } from 'lucide-react'

interface UploadedFile {
  filename: string
  size_mb: number
  status: string
}

interface ProcessingStage {
  status: string
  title?: string
  author?: string
  chapters?: number
  words?: number
  chunks_created?: number
  book_id?: number
  message?: string
}

interface ProcessingResult {
  filename: string
  status: 'processing' | 'complete' | 'failed'
  stages?: {
    extraction?: ProcessingStage
    chunking?: ProcessingStage
    ingestion?: ProcessingStage
    embedding?: ProcessingStage
  }
  error?: string
  book_id?: number
}

interface JobStatus {
  job_id: string
  status: 'queued' | 'processing' | 'complete' | 'partial' | 'failed'
  files: UploadedFile[]
  progress: {
    total: number
    processed: number
    current_file: string | null
    current_stage: string | null
  }
  results: ProcessingResult[]
  errors: string[]
}

export function UploadDropzone() {
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files).filter(
      file => file.name.toLowerCase().endsWith('.epub')
    )

    if (files.length > 0) {
      setSelectedFiles(prev => [...prev, ...files])
      setError(null)
    } else {
      setError('Only EPUB files are supported')
    }
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files) {
      const epubFiles = Array.from(files).filter(
        file => file.name.toLowerCase().endsWith('.epub')
      )
      setSelectedFiles(prev => [...prev, ...epubFiles])
      setError(null)
    }
  }, [])

  const removeFile = useCallback((index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index))
  }, [])

  const pollJobStatus = useCallback(async (jobId: string) => {
    const maxPolls = 120 // 10 minutes max
    let polls = 0

    const poll = async () => {
      try {
        const response = await fetch(`/api/upload?job_id=${jobId}`)
        const data = await response.json()

        if (data.success) {
          setJobStatus(data.data)

          // Continue polling if still processing
          if (data.data.status === 'processing' || data.data.status === 'queued') {
            polls++
            if (polls < maxPolls) {
              setTimeout(poll, 5000) // Poll every 5 seconds
            }
          }
        }
      } catch (err) {
        console.error('Polling error:', err)
      }
    }

    poll()
  }, [])

  const handleUpload = useCallback(async () => {
    if (selectedFiles.length === 0) return

    setIsUploading(true)
    setError(null)

    const formData = new FormData()
    selectedFiles.forEach(file => {
      formData.append('files', file)
    })

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (data.success) {
        setJobStatus({
          job_id: data.data.job_id,
          status: 'queued',
          files: data.data.files,
          progress: { total: data.data.files_uploaded, processed: 0, current_file: null, current_stage: null },
          results: [],
          errors: data.data.errors || []
        })
        setSelectedFiles([])

        // Start polling for status
        pollJobStatus(data.data.job_id)
      } else {
        setError(data.error || 'Upload failed')
      }
    } catch (err) {
      setError('Upload failed: ' + (err instanceof Error ? err.message : 'Unknown error'))
    } finally {
      setIsUploading(false)
    }
  }, [selectedFiles, pollJobStatus])

  const formatFileSize = (mb: number) => {
    return mb < 1 ? `${(mb * 1024).toFixed(0)} KB` : `${mb.toFixed(1)} MB`
  }

  const getStageIcon = (stage: string, status: string) => {
    if (status === 'complete') return <CheckCircle className="w-4 h-4 text-green-500" />
    if (status === 'queued') return <Loader2 className="w-4 h-4 text-yellow-500 animate-spin" />
    return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
  }

  return (
    <div className="space-y-6">
      {/* Dropzone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-xl p-8 text-center transition-all
          ${isDragging
            ? 'border-blue-500 bg-blue-500/10'
            : 'border-gray-700 hover:border-gray-600 bg-bg-card'
          }
        `}
      >
        <input
          type="file"
          accept=".epub"
          multiple
          onChange={handleFileSelect}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />

        <Upload className={`w-12 h-12 mx-auto mb-4 ${isDragging ? 'text-blue-500' : 'text-text-secondary'}`} />

        <p className="text-lg font-medium mb-1">
          {isDragging ? 'Drop your EPUBs here' : 'Drag & drop EPUB files'}
        </p>
        <p className="text-text-secondary text-sm">
          or click to browse (max 100MB per file)
        </p>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Selected Files */}
      {selectedFiles.length > 0 && (
        <div className="bg-bg-card rounded-xl border border-gray-800 p-4">
          <h3 className="font-medium mb-3">Selected Files ({selectedFiles.length})</h3>
          <div className="space-y-2">
            {selectedFiles.map((file, i) => (
              <div key={i} className="flex items-center justify-between bg-bg-primary rounded-lg p-3">
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-blue-400" />
                  <div>
                    <p className="font-medium text-sm">{file.name}</p>
                    <p className="text-text-secondary text-xs">{formatFileSize(file.size / 1024 / 1024)}</p>
                  </div>
                </div>
                <button
                  onClick={() => removeFile(i)}
                  className="p-1 hover:bg-gray-700 rounded"
                >
                  <X className="w-4 h-4 text-text-secondary" />
                </button>
              </div>
            ))}
          </div>

          <button
            onClick={handleUpload}
            disabled={isUploading}
            className="w-full mt-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            {isUploading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="w-5 h-5" />
                Upload & Process
              </>
            )}
          </button>
        </div>
      )}

      {/* Processing Status */}
      {jobStatus && (
        <div className="bg-bg-card rounded-xl border border-gray-800 p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium">
              Processing Job: {jobStatus.job_id}
            </h3>
            <span className={`
              px-3 py-1 rounded-full text-sm font-medium
              ${jobStatus.status === 'complete' ? 'bg-green-900/50 text-green-400' : ''}
              ${jobStatus.status === 'processing' || jobStatus.status === 'queued' ? 'bg-blue-900/50 text-blue-400' : ''}
              ${jobStatus.status === 'failed' ? 'bg-red-900/50 text-red-400' : ''}
              ${jobStatus.status === 'partial' ? 'bg-yellow-900/50 text-yellow-400' : ''}
            `}>
              {jobStatus.status}
            </span>
          </div>

          {/* Progress */}
          {(jobStatus.status === 'processing' || jobStatus.status === 'queued') && (
            <div className="mb-4">
              <div className="flex justify-between text-sm text-text-secondary mb-2">
                <span>Progress: {jobStatus.progress.processed}/{jobStatus.progress.total}</span>
                {jobStatus.progress.current_file && (
                  <span>Processing: {jobStatus.progress.current_file}</span>
                )}
              </div>
              <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 transition-all"
                  style={{ width: `${(jobStatus.progress.processed / jobStatus.progress.total) * 100}%` }}
                />
              </div>
              {jobStatus.progress.current_stage && (
                <p className="text-sm text-text-secondary mt-2 flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Stage: {jobStatus.progress.current_stage}
                </p>
              )}
            </div>
          )}

          {/* Results */}
          {jobStatus.results.length > 0 && (
            <div className="space-y-3">
              {jobStatus.results.map((result, i) => (
                <div key={i} className="bg-bg-primary rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm">{result.filename}</span>
                    {result.status === 'complete' && <CheckCircle className="w-5 h-5 text-green-500" />}
                    {result.status === 'failed' && <AlertCircle className="w-5 h-5 text-red-500" />}
                    {result.status === 'processing' && <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />}
                  </div>

                  {result.stages && (
                    <div className="space-y-1 text-sm">
                      {result.stages.extraction && (
                        <div className="flex items-center gap-2 text-text-secondary">
                          {getStageIcon('extraction', result.stages.extraction.status)}
                          <span>Extracted: {result.stages.extraction.title} ({result.stages.extraction.chapters} chapters, {result.stages.extraction.words?.toLocaleString()} words)</span>
                        </div>
                      )}
                      {result.stages.chunking && (
                        <div className="flex items-center gap-2 text-text-secondary">
                          {getStageIcon('chunking', result.stages.chunking.status)}
                          <span>Chunked: {result.stages.chunking.chunks_created} chunks</span>
                        </div>
                      )}
                      {result.stages.ingestion && (
                        <div className="flex items-center gap-2 text-text-secondary">
                          {getStageIcon('ingestion', result.stages.ingestion.status)}
                          <span>Ingested: Book ID #{result.stages.ingestion.book_id}</span>
                        </div>
                      )}
                      {result.stages.embedding && (
                        <div className="flex items-center gap-2 text-text-secondary">
                          {getStageIcon('embedding', result.stages.embedding.status)}
                          <span>{result.stages.embedding.message}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {result.error && (
                    <p className="text-red-400 text-sm mt-2">{result.error}</p>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Errors */}
          {jobStatus.errors.length > 0 && (
            <div className="mt-4 bg-red-900/20 border border-red-800 rounded-lg p-3">
              <p className="text-red-400 text-sm font-medium mb-1">Errors:</p>
              {jobStatus.errors.map((err, i) => (
                <p key={i} className="text-red-400 text-sm">{err}</p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
