'use client'

import { useState } from 'react'
import { Copy, Check } from 'lucide-react'

interface CodeSnippetProps {
  code: string
  language: string
}

export function CodeSnippet({ code, language }: CodeSnippetProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="relative group rounded-lg overflow-hidden">
      {/* Language label */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#12121f] border-b border-gray-800">
        <span className="text-xs font-mono text-text-secondary uppercase tracking-wider">
          {language}
        </span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-2 py-1 rounded text-xs text-text-secondary
                     hover:text-text-primary hover:bg-bg-hover transition-colors"
          aria-label="Copy code"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-green-500" />
              <span className="text-green-500">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code block */}
      <pre className="bg-[#16162a] p-4 overflow-x-auto">
        <code className="font-mono text-sm text-text-primary leading-relaxed whitespace-pre">
          {code}
        </code>
      </pre>
    </div>
  )
}
