import React, { useState } from 'react';
import { ReadingChamber as ReadingChamberType, borgesianTerms } from '../types/borgesian';

interface ReadingChamberProps {
  chamber: ReadingChamberType;
  onReturnToHalls: () => void;
  onNavigateToChunk: (chunkId: string) => void;
}

const ReadingChamber: React.FC<ReadingChamberProps> = ({
  chamber,
  onReturnToHalls,
  onNavigateToChunk
}) => {
  const [showChapterOutline, setShowChapterOutline] = useState(false);
  const [fontSize, setFontSize] = useState('text-lg');
  const [showAnnotations, setShowAnnotations] = useState(false);
  
  const fontSizes = {
    'text-sm': 'Small',
    'text-base': 'Normal', 
    'text-lg': 'Large',
    'text-xl': 'Extra Large'
  };
  
  return (
    <div className="reading-chamber">
      {/* Chamber navigation */}
      <nav className="chamber-navigation">
        <button
          onClick={onReturnToHalls}
          className="mystical-button"
        >
          {borgesianTerms.returnToHalls}
        </button>
        
        <h1 className="tome-title">
          ✦ "{chamber.title}" by {chamber.author} ✦
        </h1>
        
        <div className="flex space-x-2">
          {/* Font size control */}
          <select
            value={fontSize}
            onChange={(e) => setFontSize(e.target.value)}
            className="bg-infinite-depths-800 border border-ancient-gold-800 text-parchment-50 px-2 py-1 text-sm"
          >
            {Object.entries(fontSizes).map(([size, label]) => (
              <option key={size} value={size}>{label}</option>
            ))}
          </select>
          
          {/* Chapter outline toggle */}
          <button
            onClick={() => setShowChapterOutline(!showChapterOutline)}
            className="mystical-button text-sm"
          >
            ⬟ Outline
          </button>
        </div>
      </nav>
      
      {/* Chamber location */}
      <div className="chamber-location-info">
        {chamber.mysticalLocation}
        {chamber.publicationYear && (
          <span className="text-mystic-silver-400"> • {chamber.publicationYear}</span>
        )}
      </div>
      
      {/* Passage navigation */}
      <div className="passage-navigation">
        <button
          onClick={() => chamber.navigation.previous && onNavigateToChunk(chamber.navigation.previous.id)}
          disabled={!chamber.navigation.previous}
          className="mystical-button disabled:opacity-30 disabled:cursor-not-allowed"
        >
          {borgesianTerms.previousChamber}
        </button>
        
        <div className="flex items-center space-x-2 text-mystic-silver-500">
          <div className="w-8 h-0.5 bg-ancient-gold-800"></div>
          <span className="font-manuscript">Chamber {chamber.navigation.current.chamber}</span>
          <div className="w-8 h-0.5 bg-ancient-gold-800"></div>
        </div>
        
        <button
          onClick={() => chamber.navigation.next && onNavigateToChunk(chamber.navigation.next.id)}
          disabled={!chamber.navigation.next}
          className="mystical-button disabled:opacity-30 disabled:cursor-not-allowed"
        >
          {borgesianTerms.nextChamber}
        </button>
      </div>
      
      {/* Main content area */}
      <div className="flex gap-8">
        {/* Chapter outline sidebar */}
        {showChapterOutline && chamber.navigation.chapterOutline.length > 0 && (
          <div className="w-64 bg-infinite-depths-800 bg-opacity-30 border border-ancient-gold-800 p-4">
            <h3 className="font-sacred text-ancient-gold-800 mb-4">Chamber Map</h3>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {chamber.navigation.chapterOutline.map((chapter) => (
                <div
                  key={chapter.chamber}
                  className={`p-2 border border-transparent hover:border-ancient-gold-800 cursor-pointer transition-all ${
                    chapter.chamber === chamber.navigation.current.chamber 
                      ? 'border-ancient-gold-800 bg-ancient-gold-800 bg-opacity-20' 
                      : ''
                  }`}
                >
                  <div className="text-ancient-gold-700 text-sm">Chamber {chapter.chamber}</div>
                  <div className="text-mystic-silver-500 text-xs font-manuscript">
                    {chapter.title.length > 40 ? `${chapter.title.substring(0, 40)}...` : chapter.title}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Main reading area */}
        <div className="flex-1">
          <div className="illuminated-manuscript">
            <div className={`parchment-content ${fontSize}`}>
              {/* Format the content with proper spacing */}
              {chamber.content.split('\n\n').map((paragraph, index) => (
                <p key={index} className="mb-6 leading-relaxed">
                  {paragraph}
                </p>
              ))}
            </div>
          </div>
        </div>
      </div>
      
      {/* Chamber tools */}
      <div className="chamber-tools">
        <button
          onClick={() => setShowChapterOutline(!showChapterOutline)}
          className="mystical-button"
        >
          {borgesianTerms.chamberMap}
        </button>
        
        <button
          onClick={() => setShowAnnotations(!showAnnotations)}
          className="mystical-button"
        >
          {borgesianTerms.annotations}
        </button>
        
        <button className="mystical-button">
          {borgesianTerms.hiddenPassages}
        </button>
        
        {/* Navigation previews */}
        {chamber.navigation.previous && (
          <button
            onClick={() => onNavigateToChunk(chamber.navigation.previous!.id)}
            className="mystical-button max-w-xs"
            title={chamber.navigation.previous.preview}
          >
            ◄ Chamber {chamber.navigation.previous.chamber}
          </button>
        )}
        
        {chamber.navigation.next && (
          <button
            onClick={() => onNavigateToChunk(chamber.navigation.next!.id)}
            className="mystical-button max-w-xs"
            title={chamber.navigation.next.preview}
          >
            Chamber {chamber.navigation.next.chamber} ►
          </button>
        )}
      </div>
      
      {/* Annotations panel */}
      {showAnnotations && (
        <div className="mt-8 bg-infinite-depths-800 bg-opacity-30 border border-ancient-gold-800 p-6">
          <h3 className="font-sacred text-ancient-gold-800 mb-4">Sacred Annotations</h3>
          <p className="text-mystic-silver-500 font-manuscript italic">
            "Here the reader may inscribe their reflections upon the eternal wisdom..."
          </p>
          <div className="mt-4 space-y-2">
            <p className="text-mystic-silver-400 text-sm">
              • Current chamber: {chamber.navigation.current.type}
            </p>
            <p className="text-mystic-silver-400 text-sm">
              • Word count: ~{Math.ceil(chamber.content.length / 5)} words
            </p>
            <p className="text-mystic-silver-400 text-sm">
              • Reading time: ~{Math.ceil(chamber.content.length / 1000)} minutes
            </p>
          </div>
        </div>
      )}
      
      {/* Mystical footer */}
      <div className="mt-12 text-center">
        <p className="text-mystic-silver-400 font-manuscript text-sm italic">
          "Every word in the Library awaits its destined reader"
        </p>
        
        {/* Hexagonal navigation elements */}
        <div className="flex justify-center space-x-8 mt-6">
          <div className="w-4 h-4 border border-ancient-gold-800 opacity-40 clip-hexagon"></div>
          <div className="w-6 h-6 border border-ancient-gold-800 opacity-60 clip-hexagon"></div>
          <div className="w-4 h-4 border border-ancient-gold-800 opacity-40 clip-hexagon"></div>
        </div>
      </div>
    </div>
  );
};

export default ReadingChamber;