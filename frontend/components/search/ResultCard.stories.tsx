import type { Meta, StoryObj } from '@storybook/react'
import { ResultCard } from './ResultCard'
import type { SearchResult } from '@/types'

const meta: Meta<typeof ResultCard> = {
  title: 'Search/ResultCard',
  component: ResultCard,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof ResultCard>

const baseResult: SearchResult = {
  book_id: 1234,
  book_title: 'The Philosophy of Mind',
  author: 'Daniel Dennett',
  chunk_text: 'Consciousness is not a single thing but a complex of many different things, some of which we understand quite well, and some of which remain deeply mysterious. The hard problem of consciousness - why there is something it is like to be conscious - may or may not be a real problem.',
  chunk_id: 42,
  similarity_score: 0.89,
  genre: 'Philosophy',
  model_used: 'nomic-embed-text',
}

export const Default: Story = {
  args: {
    result: baseResult,
  },
}

export const HighRelevance: Story = {
  args: {
    result: {
      ...baseResult,
      similarity_score: 0.95,
    },
  },
}

export const MediumRelevance: Story = {
  args: {
    result: {
      ...baseResult,
      similarity_score: 0.75,
    },
  },
}

export const LowRelevance: Story = {
  args: {
    result: {
      ...baseResult,
      similarity_score: 0.55,
    },
  },
}

export const WithEmotionalData: Story = {
  args: {
    result: {
      ...baseResult,
      book_title: 'A Grief Observed',
      author: 'C.S. Lewis',
      chunk_text: 'No one ever told me that grief felt so like fear. I am not afraid, but the sensation is like being afraid. The same fluttering in the stomach, the same restlessness, the yawning.',
      extra: {
        emotion: 'grief',
        emotion_score: 0.92,
      },
    },
  },
}

export const WithDiscoveryData: Story = {
  args: {
    result: {
      ...baseResult,
      book_title: '1984',
      author: 'George Orwell',
      chunk_text: 'War is peace. Freedom is slavery. Ignorance is strength.',
      genre: 'Dystopian Fiction',
      extra: {
        subgenres: ['Dystopia', 'Political Fiction', 'Social Commentary'],
        narrative_voice: 'Third Person Limited',
        reading_time: '6-8 hours',
      },
    },
  },
}

export const WithContentAnalysis: Story = {
  args: {
    result: {
      ...baseResult,
      book_title: 'Capital in the Twenty-First Century',
      author: 'Thomas Piketty',
      chunk_text: 'When the rate of return on capital exceeds the rate of growth of output and income, capitalism automatically generates arbitrary and unsustainable inequalities.',
      extra: {
        dominant_themes: [
          { theme: 'Economic Inequality', score: '0.89' },
          { theme: 'Capitalism', score: '0.85' },
          { theme: 'Wealth Distribution', score: '0.78' },
        ],
      },
    },
  },
}

export const WithPassageData: Story = {
  args: {
    result: {
      ...baseResult,
      chunk_text: 'It was the best of times, it was the worst of times, it was the age of wisdom, it was the age of foolishness, it was the epoch of belief, it was the epoch of incredulity.',
      extra: {
        word_count: 847,
        chunk_type: 'opening',
      },
    },
  },
}

export const LongContent: Story = {
  args: {
    result: {
      ...baseResult,
      chunk_text: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt.',
    },
  },
}

export const NoModel: Story = {
  args: {
    result: {
      ...baseResult,
      model_used: undefined,
    },
  },
}

export const NaNScore: Story = {
  args: {
    result: {
      ...baseResult,
      similarity_score: NaN,
    },
  },
}
