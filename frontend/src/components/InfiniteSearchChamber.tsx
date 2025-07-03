import React, { useState } from 'react';
import { SearchMode, borgesianTerms } from '../types/borgesian';

interface InfiniteSearchChamberProps {
  onSearch: (query: string, mode: SearchMode) => void;
  loading: boolean;
  query: string;
  onQueryChange: (query: string) => void;
}

const InfiniteSearchChamber: React.FC<InfiniteSearchChamberProps> = ({
  onSearch,
  loading,
  query,
  onQueryChange
}) => {
  const [selectedMode, setSelectedMode] = useState<SearchMode>('divine');
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim(), selectedMode);
    }
  };
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };
  
  return (
    <div className="infinite-search-chamber">
      {/* Floating mystical dust motes */}
      <div className="floating-dust-motes" />
      
      {/* Sacred title */}
      <h1 className="sacred-title">
        ✦ THE LIBRARY OF BABEL ✦
      </h1>
      
      {/* Borgesian epigraph */}
      <p className="borges-quote">
        "somewhere in these halls lies every truth"
      </p>
      
      {/* Search interface */}
      <form onSubmit={handleSubmit} className="hexagonal-search-container">
        <div className="flex flex-col items-center space-y-6">
          {/* Main search input */}
          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => onQueryChange(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={borgesianTerms.search}
              className="ancient-search-input"
              disabled={loading}
            />
            
            {/* Mystical loading indicator */}
            {loading && (
              <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2">
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-ancient-gold-800 animate-hexagonal-pulse clip-hexagon"></div>
                  <span className="text-mystic-silver-500 text-sm font-manuscript italic">
                    {borgesianTerms.loading}
                  </span>
                </div>
              </div>
            )}
          </div>
          
          {/* Search mode selection */}
          <div className="search-modes">
            <button
              type="button"
              onClick={() => setSelectedMode('divine')}
              className={`mystical-button ${
                selectedMode === 'divine' 
                  ? 'bg-ancient-gold-800 text-infinite-depths-900' 
                  : ''
              }`}
              disabled={loading}
            >
              {borgesianTerms.divine}
            </button>
            
            <button
              type="button"
              onClick={() => setSelectedMode('mystical')}
              className={`mystical-button ${
                selectedMode === 'mystical' 
                  ? 'bg-ancient-gold-800 text-infinite-depths-900' 
                  : ''
              }`}
              disabled={loading}
            >
              {borgesianTerms.mystical}
            </button>
            
            <button
              type="button"
              onClick={() => setSelectedMode('precise')}
              className={`mystical-button ${
                selectedMode === 'precise' 
                  ? 'bg-ancient-gold-800 text-infinite-depths-900' 
                  : ''
              }`}
              disabled={loading}
            >
              {borgesianTerms.precise}
            </button>
          </div>
          
          {/* Search button */}
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="mystical-button px-12 py-3 text-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Consulting...' : 'Seek Knowledge'}
          </button>
        </div>
      </form>
      
      {/* Mode descriptions */}
      <div className="mt-8 text-center text-mystic-silver-400 font-manuscript text-sm max-w-2xl">
        {selectedMode === 'divine' && (
          <p className="italic">
            "The divine search reveals both sacred texts and mystical echoes - 
            precise knowledge and hidden connections united in perfect harmony."
          </p>
        )}
        {selectedMode === 'mystical' && (
          <p className="italic">
            "The mystical search follows ethereal threads between concepts - 
            discover what dwells beyond the written word."
          </p>
        )}
        {selectedMode === 'precise' && (
          <p className="italic">
            "The precise search seeks exact words within the sacred texts - 
            find documented truth with scholarly precision."
          </p>
        )}
      </div>
      
      {/* Hexagonal decorative elements */}
      <div className="absolute top-10 left-10 w-8 h-8 border border-ancient-gold-800 opacity-30 clip-hexagon"></div>
      <div className="absolute top-20 right-16 w-6 h-6 border border-ancient-gold-800 opacity-20 clip-hexagon"></div>
      <div className="absolute bottom-16 left-20 w-10 h-10 border border-ancient-gold-800 opacity-25 clip-hexagon"></div>
      <div className="absolute bottom-10 right-10 w-12 h-12 border border-ancient-gold-800 opacity-35 clip-hexagon"></div>
    </div>
  );
};

export default InfiniteSearchChamber;