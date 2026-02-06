'use client'

import type { SearchType } from '@/types'
import { SEARCH_TYPES } from '@/types'

interface SearchTypeSelectorProps {
  selected: SearchType
  onSelect: (type: SearchType) => void
}

// Primary search types to show in tabs (limited for cleaner UI)
const PRIMARY_TYPES: SearchType[] = ['semantic_passages', 'emotional', 'discovery', 'content_analysis', 'style']

export function SearchTypeSelector({ selected, onSelect }: SearchTypeSelectorProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {PRIMARY_TYPES.map((type) => {
        const info = SEARCH_TYPES[type]
        const isSelected = selected === type

        return (
          <button
            key={type}
            onClick={() => onSelect(type)}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
              ${isSelected
                ? 'bg-model-technical text-white'
                : 'bg-bg-primary border border-gray-700 hover:border-gray-600'
              }
            `}
          >
            <span>{info.icon}</span>
            <span>{info.label}</span>
          </button>
        )
      })}
    </div>
  )
}
