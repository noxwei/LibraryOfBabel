import type { Meta, StoryObj } from '@storybook/react'
import { BookCard } from './BookCard'
import type { Book } from '@/types'

const meta: Meta<typeof BookCard> = {
  title: 'Browse/BookCard',
  component: BookCard,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof BookCard>

const baseBook: Book = {
  id: 1234,
  title: 'The Philosophy of Mind',
  author: 'Daniel Dennett',
  genre: 'Philosophy',
  word_count: 85000,
}

export const GridView: Story = {
  args: {
    book: baseBook,
    viewMode: 'grid',
  },
}

export const ListView: Story = {
  args: {
    book: baseBook,
    viewMode: 'list',
  },
}

export const SciFiBook: Story = {
  args: {
    book: {
      ...baseBook,
      title: 'Neuromancer',
      author: 'William Gibson',
      genre: 'Science Fiction',
      word_count: 95000,
    },
    viewMode: 'grid',
  },
}

export const HistoryBook: Story = {
  args: {
    book: {
      ...baseBook,
      title: 'A Short History of Nearly Everything',
      author: 'Bill Bryson',
      genre: 'History',
      word_count: 120000,
    },
    viewMode: 'grid',
  },
}

export const TechnologyBook: Story = {
  args: {
    book: {
      ...baseBook,
      title: 'Clean Code',
      author: 'Robert C. Martin',
      genre: 'Technology',
      word_count: 68000,
    },
    viewMode: 'grid',
  },
}

export const FictionBook: Story = {
  args: {
    book: {
      ...baseBook,
      title: 'The Great Gatsby',
      author: 'F. Scott Fitzgerald',
      genre: 'Fiction',
      word_count: 47000,
    },
    viewMode: 'grid',
  },
}

export const LongTitle: Story = {
  args: {
    book: {
      ...baseBook,
      title: 'The Absolutely True Diary of a Part-Time Indian: A Novel About Growing Up',
      author: 'Sherman Alexie',
    },
    viewMode: 'grid',
  },
}

export const NoGenre: Story = {
  args: {
    book: {
      ...baseBook,
      genre: undefined,
    },
    viewMode: 'grid',
  },
}

export const NoWordCount: Story = {
  args: {
    book: {
      ...baseBook,
      word_count: undefined,
    },
    viewMode: 'grid',
  },
}

export const ListViewLongTitle: Story = {
  args: {
    book: {
      ...baseBook,
      title: 'The Absolutely True Diary of a Part-Time Indian: A Novel About Growing Up',
    },
    viewMode: 'list',
  },
}
