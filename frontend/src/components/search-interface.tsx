"use client"

import { useState } from "react"
import { Search, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface SearchInterfaceProps {
  onSearch?: (query: string) => void
  isLoading?: boolean
  hasResults?: boolean
  currentQuery?: string
}

export function SearchInterface({ 
  onSearch, 
  isLoading = false, 
  hasResults = false,
  currentQuery = ""
}: SearchInterfaceProps) {
  const [query, setQuery] = useState(currentQuery)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim() && onSearch) {
      onSearch(query.trim())
    }
  }

  // Google-style: Large centered search when no results, compact header when results
  if (hasResults) {
    return (
      <div className="border-b bg-background/95 backdrop-blur sticky top-0 z-50">
        <div className="w-full max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center gap-6">
            {/* Logo */}
            <h1 className="text-xl font-bold text-foreground">
              LibraryOfBabel
            </h1>
            
            {/* Compact Search */}
            <form onSubmit={handleSubmit} className="flex-1 max-w-2xl">
              <div className="relative">
                <Input
                  data-testid="search-input"
                  type="text"
                  placeholder="Search your library..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="w-full h-10 pr-12"
                  disabled={isLoading}
                />
                <Button
                  data-testid="search-button"
                  type="submit"
                  size="icon"
                  variant="ghost"
                  className="absolute right-1 top-1 h-8 w-8"
                  disabled={isLoading || !query.trim()}
                >
                  {isLoading ? (
                    <Loader2 data-testid="search-loading" className="h-4 w-4 animate-spin" />
                  ) : (
                    <Search className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </form>

            {/* Quick Stats */}
            <div className="hidden md:flex text-xs text-muted-foreground">
              <span>360 books • 34M+ words</span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Google-style: Large centered search for homepage
  return (
    <div className="w-full max-w-4xl mx-auto px-4">
      {/* LibraryOfBabel Header - Google Style */}
      <div className="text-center mb-8">
        <h1 className="text-6xl font-light text-foreground mb-6 tracking-tight">
          LibraryOfBabel
        </h1>
        <p className="text-lg text-muted-foreground mb-2">
          Search across 360 books, 34+ million words
        </p>
        <p className="text-sm text-muted-foreground">
          Natural language search powered by AI
        </p>
      </div>

      {/* Main Search Interface - Google Style */}
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="relative max-w-2xl mx-auto">
          <Input
            data-testid="search-input"
            type="text"
            placeholder="Find books about AI consciousness and ethics..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full h-14 text-lg pr-14 pl-6 border-2 rounded-full shadow-lg hover:shadow-xl transition-shadow"
            disabled={isLoading}
          />
          <Button
            data-testid="search-button"
            type="submit"
            size="icon"
            className="absolute right-2 top-2 h-10 w-10 rounded-full"
            disabled={isLoading || !query.trim()}
          >
            {isLoading ? (
              <Loader2 data-testid="search-loading" className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Google-style Buttons */}
        <div className="flex justify-center gap-4">
          <Button 
            type="submit"
            variant="outline" 
            size="lg"
            disabled={isLoading || !query.trim()}
            className="px-6"
          >
            Search Library
          </Button>
          <Button 
            variant="outline" 
            size="lg"
            onClick={() => setQuery("AI consciousness and ethics")}
            disabled={isLoading}
            className="px-6"
          >
            I&apos;m Feeling Curious
          </Button>
        </div>

        {/* Search Examples */}
        <div className="text-center">
          <p className="text-sm text-muted-foreground mb-3">Popular searches:</p>
          <div className="flex flex-wrap justify-center gap-2">
            {[
              "AI consciousness and ethics",
              "Octavia Butler social justice",
              "quantum physics philosophy",
              "digital surveillance state",
              "posthuman consciousness"
            ].map((example) => (
              <Button
                key={example}
                variant="ghost"
                size="sm"
                type="button"
                onClick={() => setQuery(example)}
                className="text-sm h-9 px-4 hover:bg-accent"
                disabled={isLoading}
              >
                {example}
              </Button>
            ))}
          </div>
        </div>
      </form>

      {/* Search Type Indicator */}
      {query && (
        <div className="mt-6 text-center">
          <div
            data-testid="semantic-search-indicator"
            className="inline-flex items-center gap-2 text-sm text-muted-foreground bg-accent px-4 py-2 rounded-full"
          >
            <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
            Semantic search ready • Understanding context and meaning
          </div>
        </div>
      )}

      {/* Footer Stats */}
      <div className="mt-12 text-center">
        <div className="flex justify-center">
          <div className="text-sm text-muted-foreground space-x-6">
            <span>📚 360 books indexed</span>
            <span>📝 34,236,988 words searchable</span>
            <span>🔍 10,514 chunks analyzed</span>
          </div>
        </div>
      </div>
    </div>
  )
}