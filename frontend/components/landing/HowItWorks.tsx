import { Upload, Cpu, Search, ArrowRight } from 'lucide-react'

const steps = [
  {
    icon: Upload,
    title: 'Ingest',
    description: 'Upload EPUB, PDF, or plain text documents into the pipeline.',
  },
  {
    icon: Cpu,
    title: 'Chunk & Embed',
    description:
      'AI splits documents into semantic chunks and generates vector embeddings offline.',
  },
  {
    icon: Search,
    title: 'Search & Retrieve',
    description:
      'Query your corpus with natural language. Get relevant passages instantly.',
  },
]

export function HowItWorks() {
  return (
    <section className="max-w-6xl mx-auto px-4 py-16">
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold mb-3">How It Works</h2>
        <p className="text-text-secondary text-lg">
          Three steps from raw documents to semantic search.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative">
        {steps.map((step, index) => (
          <div key={step.title} className="relative flex flex-col items-center">
            {/* Connecting arrow (desktop only, not after last card) */}
            {index < steps.length - 1 && (
              <div className="hidden md:flex absolute top-10 -right-3 z-10">
                <ArrowRight className="w-6 h-6 text-gray-600" />
              </div>
            )}

            <div className="bg-bg-card border border-gray-800 rounded-xl p-8 text-center w-full">
              {/* Step number + icon */}
              <div className="flex items-center justify-center w-14 h-14 rounded-full bg-model-technical/10 border border-model-technical/20 mx-auto mb-5">
                <step.icon className="w-6 h-6 text-model-technical" />
              </div>

              <h3 className="text-xl font-semibold mb-3">{step.title}</h3>
              <p className="text-text-secondary leading-relaxed">
                {step.description}
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
