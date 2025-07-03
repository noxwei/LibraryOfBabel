import React, { useState } from 'react';
import InfiniteSearchChamber from './components/InfiniteSearchChamber';
import TwinMirrorsOfKnowledge from './components/TwinMirrorsOfKnowledge';
import ReadingChamber from './components/ReadingChamber';
import { babelLibraryAPI, enhancedBabelAPI } from './services/BabelLibraryAPI';
import { SearchMode, MysticalRevelation, ReadingChamber as ReadingChamberType } from './types/borgesian';

type AppState = 'search' | 'results' | 'reading';

function App() {
  const [appState, setAppState] = useState<AppState>('search');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<MysticalRevelation | null>(null);
  const [currentChamber, setCurrentChamber] = useState<ReadingChamberType | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [libraryMode, setLibraryMode] = useState<'educational' | 'enhanced'>('educational');

  const getAPIClient = () => libraryMode === 'enhanced' ? enhancedBabelAPI : babelLibraryAPI;

  const handleSearch = async (query: string, mode: SearchMode) => {
    setLoading(true);
    setError(null);
    
    try {
      const api = getAPIClient();
      const revelation = await api.divineKnowledge(query, mode);
      setSearchResults(revelation);
      setAppState('results');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'The mirrors show conflicting reflections');
    } finally {
      setLoading(false);
    }
  };

  const handleEnterChamber = async (chunkId: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const api = getAPIClient();
      const chamber = await api.seekChamberWisdom(chunkId);
      setCurrentChamber(chamber);
      setAppState('reading');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'The passage to this chamber is obscured');
    } finally {
      setLoading(false);
    }
  };

  const handleFollowThread = async (chunkId: string) => {
    await handleEnterChamber(chunkId);
  };

  const handleReturnToHalls = () => {
    setAppState('search');
    setCurrentChamber(null);
    setSearchResults(null);
    setSearchQuery('');
  };

  const handleReturnToResults = () => {
    if (searchResults) {
      setAppState('results');
      setCurrentChamber(null);
    } else {
      handleReturnToHalls();
    }
  };

  const handleNavigateToChunk = async (chunkId: string) => {
    await handleEnterChamber(chunkId);
  };

  return (
    <div className="min-h-screen bg-infinite-depths-900 text-parchment-50 font-manuscript">
      {/* Library Mode Switcher */}
      <div className="fixed top-4 left-4 z-50">
        <div className="bg-infinite-depths-800 bg-opacity-90 border border-ancient-gold-800 p-3 rounded">
          <p className="text-ancient-gold-600 text-xs font-manuscript mb-2">Library Mode:</p>
          <div className="flex space-x-2">
            <button
              onClick={() => setLibraryMode('educational')}
              className={`px-3 py-1 text-xs font-manuscript transition-all ${
                libraryMode === 'educational'
                  ? 'bg-ancient-gold-800 text-infinite-depths-900'
                  : 'border border-ancient-gold-800 text-ancient-gold-600 hover:text-ancient-gold-400'
              }`}
            >
              📚 Educational
            </button>
            <button
              onClick={() => setLibraryMode('enhanced')}
              className={`px-3 py-1 text-xs font-manuscript transition-all ${
                libraryMode === 'enhanced'
                  ? 'bg-ancient-gold-800 text-infinite-depths-900'
                  : 'border border-ancient-gold-800 text-ancient-gold-600 hover:text-ancient-gold-400'
              }`}
            >
              🔧 Enhanced
            </button>
          </div>
          <p className="text-mystic-silver-500 text-xs mt-1 italic">
            {libraryMode === 'educational' 
              ? 'Infinite procedural generation' 
              : 'Hybrid with real content'}
          </p>
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="fixed top-4 right-4 z-50 bg-red-900 bg-opacity-80 border border-red-700 text-red-200 px-4 py-2 rounded">
          <p className="font-manuscript text-sm">{error}</p>
          <button 
            onClick={() => setError(null)}
            className="ml-2 text-red-400 hover:text-red-200"
          >
            ✕
          </button>
        </div>
      )}

      {/* Main application states */}
      {appState === 'search' && (
        <InfiniteSearchChamber
          onSearch={handleSearch}
          loading={loading}
          query={searchQuery}
          onQueryChange={setSearchQuery}
        />
      )}

      {appState === 'results' && searchResults && (
        <div>
          {/* Return to search button */}
          <div className="p-4 border-b border-ancient-gold-800">
            <button
              onClick={handleReturnToHalls}
              className="mystical-button"
            >
              ← Return to Search
            </button>
            <span className="ml-4 text-mystic-silver-500 font-manuscript">
              Sought: "{searchQuery}"
            </span>
          </div>
          
          <TwinMirrorsOfKnowledge
            revelation={searchResults}
            onEnterChamber={handleEnterChamber}
            onFollowThread={handleFollowThread}
          />
        </div>
      )}

      {appState === 'reading' && currentChamber && (
        <ReadingChamber
          chamber={currentChamber}
          onReturnToHalls={handleReturnToResults}
          onNavigateToChunk={handleNavigateToChunk}
        />
      )}

      {/* Loading overlay */}
      {loading && (
        <div className="fixed inset-0 bg-infinite-depths-900 bg-opacity-80 flex items-center justify-center z-50">
          <div className="flex items-center space-x-4">
            <div className="w-8 h-8 bg-ancient-gold-800 animate-hexagonal-pulse clip-hexagon"></div>
            <div className="w-6 h-6 bg-ancient-gold-700 animate-hexagonal-pulse clip-hexagon" style={{animationDelay: '0.2s'}}></div>
            <div className="w-4 h-4 bg-ancient-gold-600 animate-hexagonal-pulse clip-hexagon" style={{animationDelay: '0.4s'}}></div>
            <span className="text-mystic-silver-400 font-manuscript ml-4">
              Consulting the infinite catalog...
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
