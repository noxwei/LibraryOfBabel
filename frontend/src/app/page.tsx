'use client';

import { useState } from 'react';

interface SearchResult {
  id: number;
  title: string;
  author: string;
  excerpt: string;
  relevance: number;
}

export default function Home() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    setShowResults(true);
    
    try {
      // Simulate API call for now - replace with actual API endpoint
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: searchQuery }),
      });
      
      if (response.ok) {
        const data = await response.json();
        setSearchResults(data.results || []);
      } else {
        // Mock results for demonstration
        const mockResults = [
          {
            id: 1,
            title: 'The Left Hand of Darkness',
            author: 'Ursula K. Le Guin',
            excerpt: 'A fascinating exploration of gender and society...',
            relevance: 0.95
          },
          {
            id: 2,
            title: 'Neuromancer',
            author: 'William Gibson',
            excerpt: 'The matrix has its roots in primitive arcade games...',
            relevance: 0.87
          }
        ];
        setSearchResults(mockResults);
      }
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleExampleSearch = (example: string) => {
    setSearchQuery(example);
    // Auto-submit the search
    setTimeout(() => {
      const form = document.querySelector('form');
      if (form) {
        form.requestSubmit();
      }
    }, 100);
  };

  const handleIAmFeelingCurious = () => {
    const examples = [
      "AI consciousness",
      "Octavia Butler",
      "quantum physics",
      "digital surveillance",
      "posthuman consciousness",
      "cybernetic organisms",
      "philosophy of mind",
      "artificial life"
    ];
    const randomExample = examples[Math.floor(Math.random() * examples.length)];
    handleExampleSearch(randomExample);
  };

  return (
    <div className="mobile-garden-container">
      <main className="container mx-auto px-4 py-8 sm:py-16 lg:py-20">
        <div className="flex items-center justify-center min-h-[70vh]">
          <div className="w-full max-w-4xl mx-auto px-4 fade-in">
            {/* Mobile-First Library Header */}
            <div className="text-center mb-8 sm:mb-12 space-golden-sm">
              <h1 className="text-4xl sm:text-5xl lg:text-7xl font-extralight text-primary mb-4 sm:mb-6 lg:mb-8 tracking-tight">
                Library Of Babel
              </h1>
              <p className="text-lg sm:text-xl text-secondary mb-2 sm:mb-3">
                Search across 360 books, 34+ million words
              </p>
              <p className="text-sm sm:text-base text-tertiary">
                Natural language search powered by AI
              </p>
            </div>

            {/* Mobile-First Search Interface */}
            <form onSubmit={handleSearch} className="space-y-6 sm:space-y-8">
              <div className="mobile-search-container">
                <div className="relative">
                  <input
                    data-testid="search-input"
                    type="search"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Find books about AI consciousness..."
                    className="search-input"
                    disabled={isSearching}
                  />
                  <button
                    data-testid="search-button"
                    type="submit"
                    className="search-button"
                    disabled={isSearching || !searchQuery.trim()}
                  >
                    {isSearching ? (
                      <svg className="h-5 w-5 sm:h-6 sm:w-6 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    ) : (
                      <svg className="h-5 w-5 sm:h-6 sm:w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              {/* Mobile-Optimized Action Buttons */}
              <div className="flex flex-col sm:flex-row justify-center gap-3 sm:gap-4 px-4">
                <button 
                  type="submit"
                  className="action-button font-medium w-full sm:w-auto"
                  disabled={isSearching || !searchQuery.trim()}
                >
                  {isSearching ? 'Searching...' : 'Search Library'}
                </button>
                <button 
                  type="button"
                  onClick={handleIAmFeelingCurious}
                  className="action-button font-medium w-full sm:w-auto"
                  disabled={isSearching}
                >
                  I&apos;m Feeling Curious
                </button>
              </div>

              {/* Mobile-Optimized Search Examples */}
              <div className="text-center px-4">
                <p className="text-sm text-tertiary mb-4">Popular searches:</p>
                <div className="flex flex-wrap justify-center gap-2 sm:gap-3">
                  {[
                    "AI consciousness",
                    "Octavia Butler",
                    "quantum physics",
                    "digital surveillance",
                    "posthuman consciousness"
                  ].map((example) => (
                    <button
                      key={example}
                      type="button"
                      onClick={() => handleExampleSearch(example)}
                      className="mobile-example-button"
                      disabled={isSearching}
                    >
                      {example}
                    </button>
                  ))}
                </div>
              </div>
            </form>

            {/* Search Results */}
            {showResults && (
              <div className="mt-8 sm:mt-12 max-w-4xl mx-auto">
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                  <div className="px-6 py-4 border-b border-gray-200">
                    <h2 className="text-lg font-semibold text-gray-900">
                      Search Results for &quot;{searchQuery}&quot;
                    </h2>
                    <p className="text-sm text-gray-600 mt-1">
                      {searchResults.length} results found from 360 books (34M+ words)
                    </p>
                  </div>
                  
                  <div data-testid="search-results" className="divide-y divide-gray-200">
                    {searchResults.length > 0 ? (
                      searchResults.map((result: SearchResult) => (
                        <div key={result.id} className="px-6 py-4 hover:bg-gray-50 transition-colors">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <h3 className="text-lg font-medium text-blue-600 hover:text-blue-700">
                                {result.title}
                              </h3>
                              <p className="text-sm text-gray-600 mt-1">
                                by {result.author}
                              </p>
                              <p className="text-gray-700 mt-2 leading-relaxed">
                                {result.excerpt}
                              </p>
                            </div>
                            <div className="ml-4 flex-shrink-0">
                              <div className="text-xs text-gray-500">
                                {Math.round(result.relevance * 100)}% match
                              </div>
                            </div>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="px-6 py-8 text-center">
                        <p className="text-gray-500">No results found for your search.</p>
                        <p className="text-sm text-gray-400 mt-2">
                          Try different keywords or check the popular searches above.
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                          Searching across 360 books with 34,236,988 words indexed.
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Mobile-Optimized Stats Display */}
            <div className={`text-center px-4 ${showResults ? 'mt-8 sm:mt-12' : 'mt-12 sm:mt-16'}`}>
              <div className="mobile-stats">
                <div className="flex flex-col sm:flex-row justify-center items-center gap-2 sm:gap-8">
                  <span className="inline-flex items-center">
                    <span className="text-base sm:text-lg mr-2">📚</span>
                    360 books indexed
                  </span>
                  <span className="inline-flex items-center">
                    <span className="text-base sm:text-lg mr-2">📝</span>
                    34,236,988 words searchable
                  </span>
                  <span className="inline-flex items-center">
                    <span className="text-base sm:text-lg mr-2">🔍</span>
                    10,514 chunks analyzed
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
      
      {/* Mobile-Optimized Footer */}
      <footer className="mobile-footer">
        <div className="container mx-auto px-4 py-6 sm:py-8">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4 text-sm text-secondary">
            <div className="text-center sm:text-left">
              <span className="font-semibold text-primary">Library Of Babel</span> 
              <span className="mx-2 hidden sm:inline">•</span>
              <span className="block sm:inline">Personal Knowledge Liberation System</span>
            </div>
            <div className="flex flex-col sm:flex-row items-center gap-2 sm:gap-8 text-xs sm:text-sm">
              <span>360 books indexed</span>
              <span>34M+ words searchable</span>
              <span>AI-powered semantic search</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}