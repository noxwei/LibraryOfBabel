import type { Meta, StoryObj } from '@storybook/react'
import { useState } from 'react'
import { SearchTypeSelector } from './SearchTypeSelector'
import type { SearchType } from '@/types'

const meta: Meta<typeof SearchTypeSelector> = {
  title: 'Search/SearchTypeSelector',
  component: SearchTypeSelector,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof SearchTypeSelector>

// Interactive wrapper for state management
function InteractiveSelector({ initialType = 'semantic' }: { initialType?: SearchType }) {
  const [selected, setSelected] = useState<SearchType>(initialType)
  return (
    <div className="p-4">
      <SearchTypeSelector selected={selected} onSelect={setSelected} />
      <p className="mt-4 text-sm text-gray-400">Selected: {selected}</p>
    </div>
  )
}

export const Default: Story = {
  render: () => <InteractiveSelector />,
}

export const SemanticSelected: Story = {
  args: {
    selected: 'semantic',
    onSelect: () => {},
  },
}

export const EmotionalSelected: Story = {
  args: {
    selected: 'emotional',
    onSelect: () => {},
  },
}

export const DiscoverySelected: Story = {
  args: {
    selected: 'discovery',
    onSelect: () => {},
  },
}

export const AnalysisSelected: Story = {
  args: {
    selected: 'content_analysis',
    onSelect: () => {},
  },
}

export const StyleSelected: Story = {
  args: {
    selected: 'style',
    onSelect: () => {},
  },
}
