'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp, Play } from 'lucide-react'
import { CodeSnippet } from './CodeSnippet'

export interface EndpointParameter {
  name: string
  type: string
  required: boolean
  description: string
}

interface EndpointCardProps {
  method: string
  path: string
  description: string
  parameters: EndpointParameter[]
  exampleResponse: string
  onTryIt: () => void
}

function MethodBadge({ method }: { method: string }) {
  const colors = method === 'GET'
    ? 'bg-green-500/15 text-green-400 border-green-500/30'
    : 'bg-blue-500/15 text-blue-400 border-blue-500/30'

  return (
    <span className={`px-2.5 py-1 rounded text-xs font-bold font-mono border ${colors}`}>
      {method}
    </span>
  )
}

export function EndpointCard({
  method,
  path,
  description,
  parameters,
  exampleResponse,
  onTryIt,
}: EndpointCardProps) {
  const [paramsExpanded, setParamsExpanded] = useState(false)
  const [responseExpanded, setResponseExpanded] = useState(false)

  return (
    <div className="bg-bg-card rounded-lg border border-gray-800 overflow-hidden hover:border-gray-700 transition-colors">
      {/* Header */}
      <div className="p-4 flex items-start justify-between gap-4">
        <div className="flex items-center gap-3 flex-wrap">
          <MethodBadge method={method} />
          <code className="font-mono text-sm text-text-primary break-all">{path}</code>
        </div>
        <button
          onClick={onTryIt}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-model-technical/15 text-model-technical
                     border border-model-technical/30 hover:bg-model-technical/25 transition-colors text-sm font-medium
                     flex-shrink-0"
        >
          <Play className="w-3.5 h-3.5" />
          Try It
        </button>
      </div>

      {/* Description */}
      <div className="px-4 pb-3">
        <p className="text-text-secondary text-sm">{description}</p>
      </div>

      {/* Parameters section */}
      {parameters.length > 0 && (
        <div className="border-t border-gray-800">
          <button
            onClick={() => setParamsExpanded(!paramsExpanded)}
            className="w-full flex items-center justify-between px-4 py-3 text-sm text-text-secondary
                       hover:text-text-primary hover:bg-bg-hover/50 transition-colors"
          >
            <span>Parameters ({parameters.length})</span>
            {paramsExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>

          {paramsExpanded && (
            <div className="px-4 pb-4">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-text-secondary border-b border-gray-800">
                    <th className="pb-2 pr-4 font-medium">Name</th>
                    <th className="pb-2 pr-4 font-medium">Type</th>
                    <th className="pb-2 pr-4 font-medium">Required</th>
                    <th className="pb-2 font-medium">Description</th>
                  </tr>
                </thead>
                <tbody>
                  {parameters.map((param) => (
                    <tr key={param.name} className="border-b border-gray-800/50 last:border-0">
                      <td className="py-2 pr-4 font-mono text-model-general">{param.name}</td>
                      <td className="py-2 pr-4 text-text-secondary">{param.type}</td>
                      <td className="py-2 pr-4">
                        {param.required ? (
                          <span className="text-xs px-1.5 py-0.5 rounded bg-red-500/15 text-red-400">required</span>
                        ) : (
                          <span className="text-xs px-1.5 py-0.5 rounded bg-gray-700 text-gray-400">optional</span>
                        )}
                      </td>
                      <td className="py-2 text-text-secondary">{param.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Example Response section */}
      <div className="border-t border-gray-800">
        <button
          onClick={() => setResponseExpanded(!responseExpanded)}
          className="w-full flex items-center justify-between px-4 py-3 text-sm text-text-secondary
                     hover:text-text-primary hover:bg-bg-hover/50 transition-colors"
        >
          <span>Example Response</span>
          {responseExpanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>

        {responseExpanded && (
          <div className="px-4 pb-4">
            <CodeSnippet code={exampleResponse} language="json" />
          </div>
        )}
      </div>
    </div>
  )
}
