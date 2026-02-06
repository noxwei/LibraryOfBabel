import { Header } from '@/components/layout/Header'
import { BrowseLibrary } from '@/components/browse/BrowseLibrary'

export default function BrowsePage() {
  return (
    <main className="min-h-screen">
      <Header />
      <BrowseLibrary />
    </main>
  )
}
