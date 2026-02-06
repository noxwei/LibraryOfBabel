import { Header } from '@/components/layout/Header'
import { HeroSection } from '@/components/landing/HeroSection'
import { StatsBar } from '@/components/landing/StatsBar'
import { HowItWorks } from '@/components/landing/HowItWorks'
import { UseCases } from '@/components/landing/UseCases'
import { LiveDemo } from '@/components/landing/LiveDemo'

export default function Home() {
  return (
    <main className="min-h-screen">
      <Header />
      <HeroSection />
      <StatsBar />
      <LiveDemo />
      <HowItWorks />
      <UseCases />
      <footer className="py-12 text-center text-text-secondary text-sm border-t border-gray-800">
        <p>LibraryOfBabel — Offline RAG Pipeline</p>
      </footer>
    </main>
  )
}
