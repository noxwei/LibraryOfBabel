import React, { useState } from 'react';
import './simple.css';

type SearchMode = 'divine' | 'mystical' | 'precise';

interface Book {
  title: string;
  author: string;
  excerpt: string;
  coordinates: string;
  id: string;
}

interface SearchResults {
  books: Book[];
  query: string;
  totalResults: number;
}

function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchMode, setSearchMode] = useState<SearchMode>('divine');

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    setError(null);
    
    try {
      // Detect domain and use appropriate port
      const currentHost = window.location.hostname;
      const port = window.location.port || (window.location.hostname === 'localhost' ? '5571' : '5571');
      const apiUrl = `http://${currentHost}:${port}/api/search`;
      
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchQuery,
          mode: searchMode,
          maxResults: 5
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Transform API response to our interface
      const results: SearchResults = {
        books: data.books?.map((book: any) => ({
          title: book.title || 'Untitled Manuscript',
          author: book.author || 'Anonymous Scribe',
          excerpt: book.content?.substring(0, 300) + '...' || 'No excerpt available',
          coordinates: book.coordinates || 'Unknown coordinates',
          id: book.id || Math.random().toString()
        })) || [],
        query: searchQuery,
        totalResults: data.totalResults || 0
      };
      
      setSearchResults(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="container">
      <h1 className="title">📚 Library of Babel</h1>
      
      <div className="search-container">
        <input
          type="text"
          className="search-input"
          placeholder="Search the infinite library..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={handleKeyPress}
        />
        
        <div className="mode-switcher">
          <button 
            className={`mode-button ${searchMode === 'divine' ? 'active' : ''}`}
            onClick={() => setSearchMode('divine')}
          >
            Divine
          </button>
          <button 
            className={`mode-button ${searchMode === 'mystical' ? 'active' : ''}`}
            onClick={() => setSearchMode('mystical')}
          >
            Mystical
          </button>
          <button 
            className={`mode-button ${searchMode === 'precise' ? 'active' : ''}`}
            onClick={() => setSearchMode('precise')}
          >
            Precise
          </button>
        </div>
        
        <button className="search-button" onClick={handleSearch} disabled={loading}>
          {loading ? '🔍 Searching the Infinite...' : '🔍 Search the Library'}
        </button>
      </div>

      {error && (
        <div className="error">
          ⚠️ {error}
        </div>
      )}

      {loading && (
        <div className="loading">
          ✨ Navigating the hexagonal galleries...
        </div>
      )}

      {searchResults && !loading && (
        <div className="results-container">
          <h2 className="title" style={{fontSize: '2rem', marginBottom: '1rem'}}>
            📖 Found {searchResults.totalResults} Books for "{searchResults.query}"
          </h2>
          
          {searchResults.books.map((book, index) => (
            <div key={book.id} className="book-result">
              <h3 className="book-title">{book.title}</h3>
              <p className="book-author">📝 By {book.author}</p>
              <p className="book-excerpt">{book.excerpt}</p>
              <p style={{color: '#888', fontSize: '0.9rem'}}>
                📍 Location: {book.coordinates}
              </p>
            </div>
          ))}
        </div>
      )}

      {!searchResults && !loading && (
        <div style={{margin: '2rem 0', textAlign: 'center', color: '#888'}}>
          <p>🏛️ Welcome to the infinite Library of Babel</p>
          <p>Every book that ever was or could be exists here</p>
          <p>Search above to begin your exploration...</p>
        </div>
      )}
    </div>
  );
}

export default App;