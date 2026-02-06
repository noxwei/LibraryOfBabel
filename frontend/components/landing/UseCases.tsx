import { Shield, BookOpen, Server } from 'lucide-react'

const useCases = [
  {
    icon: Shield,
    title: 'NGOs & Nonprofits',
    description:
      'Keep sensitive field data on-premises. Search project documents, reports, and research without sending data to external APIs.',
    accentColor: 'border-model-technical',
  },
  {
    icon: BookOpen,
    title: 'Academic Researchers',
    description:
      'Search across your entire corpus semantically. Find connections across thousands of papers, books, and dissertations.',
    accentColor: 'border-model-general',
  },
  {
    icon: Server,
    title: 'Enterprise Teams',
    description:
      'Deploy RAG pipelines on your own infrastructure. Full API access, no cloud dependency, complete data sovereignty.',
    accentColor: 'border-model-multilingual',
  },
]

export function UseCases() {
  return (
    <section className="max-w-6xl mx-auto px-4 py-16">
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold mb-3">Built For</h2>
        <p className="text-text-secondary text-lg">
          Designed for teams that need control over their data.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {useCases.map(({ icon: Icon, title, description, accentColor }) => (
          <div
            key={title}
            className={`bg-bg-card border border-gray-800 border-l-4 ${accentColor} rounded-xl p-8`}
          >
            <Icon className="w-8 h-8 text-text-secondary mb-4" />
            <h3 className="text-xl font-semibold mb-3">{title}</h3>
            <p className="text-text-secondary leading-relaxed">{description}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
