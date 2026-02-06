'use client'

import { Brain } from 'lucide-react'
import type { AIModel } from '@/types'
import { MODEL_INFO } from '@/types'

interface ModelSelectorProps {
  selected: AIModel
  onSelect: (model: AIModel) => void
}

const models: AIModel[] = ['auto', 'technical', 'creative', 'multilingual', 'general', 'specialized']

export function ModelSelector({ selected, onSelect }: ModelSelectorProps) {
  return (
    <div className="mt-6 pt-4 border-t border-gray-700">
      <div className="flex items-center gap-2 mb-4">
        <Brain className="w-5 h-5 text-model-technical" />
        <span className="font-semibold">AI Model Routing</span>
        <span className="text-text-secondary text-sm">(Auto-select or manual)</span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {models.map((model) => {
          const info = MODEL_INFO[model]
          const isSelected = selected === model

          return (
            <button
              key={model}
              onClick={() => onSelect(model)}
              className={`
                relative p-3 rounded-lg border text-left transition-all
                ${isSelected
                  ? 'bg-bg-primary border-model-technical ring-1 ring-model-technical'
                  : 'bg-bg-primary border-gray-700 hover:border-gray-600'
                }
              `}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">{info.icon}</span>
                <span className={`text-sm font-medium ${isSelected ? info.color : ''}`}>
                  {info.name}
                </span>
              </div>
              <p className="text-xs text-text-secondary line-clamp-2">
                {info.description}
              </p>

              {isSelected && (
                <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-model-technical" />
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}
