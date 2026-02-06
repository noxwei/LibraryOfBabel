'use client'

import { useState, useEffect } from 'react'
import { X, Send, Loader2 } from 'lucide-react'
import { CodeSnippet } from './CodeSnippet'
import type { EndpointParameter } from './EndpointCard'

interface TryItEndpoint {
  method: string
  path: string
  parameters: EndpointParameter[]
}

interface TryItPanelProps {
  endpoint: TryItEndpoint
  onClose: () => void
}

type CodeTab = 'curl' | 'python' | 'javascript'

function buildUrl(path: string, method: string, params: Record<string, string>): string {
  // For GET requests, append filled params as query parameters
  // The path already contains query params like ?action=list, so we append with &
  if (method === 'GET') {
    const filledParams = Object.entries(params).filter(([, v]) => v.trim() !== '')
    if (filledParams.length === 0) return path
    const separator = path.includes('?') ? '&' : '?'
    const queryString = filledParams.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join('&')
    return `${path}${separator}${queryString}`
  }
  return path
}

function generateCurl(method: string, path: string, params: Record<string, string>): string {
  const url = buildUrl(path, method, params)
  const fullUrl = `https://api.example.com${url}`

  if (method === 'GET') {
    return `curl -X GET "${fullUrl}" \\
  -H "X-API-Key: YOUR_API_KEY"`
  }

  const body = Object.fromEntries(Object.entries(params).filter(([, v]) => v.trim() !== ''))
  return `curl -X POST "${fullUrl}" \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '${JSON.stringify(body, null, 2)}'`
}

function generatePython(method: string, path: string, params: Record<string, string>): string {
  const filledParams = Object.fromEntries(Object.entries(params).filter(([, v]) => v.trim() !== ''))

  if (method === 'GET') {
    const url = buildUrl(path, method, params)
    return `import requests

response = requests.get(
    "https://api.example.com${url}",
    headers={"X-API-Key": "YOUR_API_KEY"}
)

data = response.json()
print(data)`
  }

  return `import requests

response = requests.post(
    "https://api.example.com${path}",
    headers={
        "X-API-Key": "YOUR_API_KEY",
        "Content-Type": "application/json"
    },
    json=${JSON.stringify(filledParams, null, 4).replace(/"/g, '"')}
)

data = response.json()
print(data)`
}

function generateJavascript(method: string, path: string, params: Record<string, string>): string {
  const filledParams = Object.fromEntries(Object.entries(params).filter(([, v]) => v.trim() !== ''))

  if (method === 'GET') {
    const url = buildUrl(path, method, params)
    return `const response = await fetch("${url}", {
  headers: {
    "X-API-Key": "YOUR_API_KEY"
  }
});

const data = await response.json();
console.log(data);`
  }

  return `const response = await fetch("${path}", {
  method: "POST",
  headers: {
    "X-API-Key": "YOUR_API_KEY",
    "Content-Type": "application/json"
  },
  body: JSON.stringify(${JSON.stringify(filledParams, null, 2)})
});

const data = await response.json();
console.log(data);`
}

export function TryItPanel({ endpoint, onClose }: TryItPanelProps) {
  const [params, setParams] = useState<Record<string, string>>({})
  const [response, setResponse] = useState<{ status: number; body: string } | null>(null)
  const [loading, setLoading] = useState(false)
  const [codeTab, setCodeTab] = useState<CodeTab>('curl')

  // Initialize params from endpoint definition
  useEffect(() => {
    const initial: Record<string, string> = {}
    endpoint.parameters.forEach((p) => {
      initial[p.name] = ''
    })
    setParams(initial)
    setResponse(null)
  }, [endpoint])

  const handleParamChange = (name: string, value: string) => {
    setParams((prev) => ({ ...prev, [name]: value }))
  }

  const handleSend = async () => {
    setLoading(true)
    setResponse(null)

    try {
      const url = buildUrl(endpoint.path, endpoint.method, params)

      const options: RequestInit = {
        method: endpoint.method,
        headers: {} as Record<string, string>,
      }

      if (endpoint.method === 'POST') {
        const body = Object.fromEntries(
          Object.entries(params).filter(([, v]) => v.trim() !== '')
        )
        options.headers = { 'Content-Type': 'application/json' }
        options.body = JSON.stringify(body)
      }

      const res = await fetch(url, options)
      const text = await res.text()

      let formatted: string
      try {
        formatted = JSON.stringify(JSON.parse(text), null, 2)
      } catch {
        formatted = text
      }

      setResponse({ status: res.status, body: formatted })
    } catch (err) {
      setResponse({
        status: 0,
        body: JSON.stringify({ error: err instanceof Error ? err.message : 'Request failed' }, null, 2),
      })
    } finally {
      setLoading(false)
    }
  }

  const codeTabs: { key: CodeTab; label: string }[] = [
    { key: 'curl', label: 'cURL' },
    { key: 'python', label: 'Python' },
    { key: 'javascript', label: 'JavaScript' },
  ]

  const codeGenerators: Record<CodeTab, () => string> = {
    curl: () => generateCurl(endpoint.method, endpoint.path, params),
    python: () => generatePython(endpoint.method, endpoint.path, params),
    javascript: () => generateJavascript(endpoint.method, endpoint.path, params),
  }

  const codeLanguageMap: Record<CodeTab, string> = {
    curl: 'bash',
    python: 'python',
    javascript: 'javascript',
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-bg-card border border-gray-800 rounded-xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col m-4">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <span
              className={`px-2.5 py-1 rounded text-xs font-bold font-mono border ${
                endpoint.method === 'GET'
                  ? 'bg-green-500/15 text-green-400 border-green-500/30'
                  : 'bg-blue-500/15 text-blue-400 border-blue-500/30'
              }`}
            >
              {endpoint.method}
            </span>
            <code className="font-mono text-sm text-text-primary">{endpoint.path}</code>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded hover:bg-bg-hover transition-colors"
            aria-label="Close panel"
          >
            <X className="w-5 h-5 text-text-secondary" />
          </button>
        </div>

        {/* Scrollable body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-5">
          {/* Parameters */}
          {endpoint.parameters.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-text-primary mb-3">Parameters</h3>
              <div className="space-y-3">
                {endpoint.parameters.map((param) => (
                  <div key={param.name}>
                    <label className="flex items-center gap-2 text-sm mb-1">
                      <span className="font-mono text-model-general">{param.name}</span>
                      <span className="text-text-secondary text-xs">({param.type})</span>
                      {param.required && (
                        <span className="text-xs px-1.5 py-0.5 rounded bg-red-500/15 text-red-400">required</span>
                      )}
                    </label>
                    <input
                      type="text"
                      value={params[param.name] || ''}
                      onChange={(e) => handleParamChange(param.name, e.target.value)}
                      placeholder={param.description}
                      className="w-full px-3 py-2 rounded-lg bg-bg-primary border border-gray-700 text-text-primary
                                 text-sm font-mono placeholder:text-gray-600 focus:outline-none focus:border-model-technical
                                 transition-colors"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Send button */}
          <button
            onClick={handleSend}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-model-technical
                       text-white font-medium text-sm hover:bg-model-technical/90 disabled:opacity-60
                       disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Sending...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                Send Request
              </>
            )}
          </button>

          {/* Response */}
          {response && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <h3 className="text-sm font-medium text-text-primary">Response</h3>
                <span
                  className={`px-2 py-0.5 rounded text-xs font-mono font-bold ${
                    response.status >= 200 && response.status < 300
                      ? 'bg-green-500/15 text-green-400'
                      : response.status >= 400
                        ? 'bg-red-500/15 text-red-400'
                        : 'bg-yellow-500/15 text-yellow-400'
                  }`}
                >
                  {response.status === 0 ? 'Error' : response.status}
                </span>
              </div>
              <CodeSnippet code={response.body} language="json" />
            </div>
          )}

          {/* Generated code tabs */}
          <div>
            <h3 className="text-sm font-medium text-text-primary mb-3">Generated Code</h3>
            <div className="flex gap-1 mb-3">
              {codeTabs.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setCodeTab(tab.key)}
                  className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                    codeTab === tab.key
                      ? 'bg-model-technical/20 text-model-technical border border-model-technical/30'
                      : 'bg-bg-primary text-text-secondary border border-gray-800 hover:text-text-primary'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
            <CodeSnippet
              code={codeGenerators[codeTab]()}
              language={codeLanguageMap[codeTab]}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
