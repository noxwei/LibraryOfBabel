import React from 'react';
import { MysticalRevelation, borgesianTerms } from '../types/borgesian';

interface TwinMirrorsOfKnowledgeProps {
  revelation: MysticalRevelation;
  onEnterChamber: (chunkId: string) => void;
  onFollowThread: (chunkId: string) => void;
}

const TwinMirrorsOfKnowledge: React.FC<TwinMirrorsOfKnowledgeProps> = ({
  revelation,
  onEnterChamber,
  onFollowThread
}) => {
  const { sacredTexts, mysticalEchoes, seekerGuidance, queryMetadata } = revelation;
  
  return (
    <div className="min-h-screen">
      {/* Query metadata */}
      <div className="p-4 text-center border-b border-ancient-gold-800">
        <p className="text-mystic-silver-500 font-manuscript text-sm">
          {borgesianTerms.results} • Consulted in {queryMetadata.responseTime.toFixed(0)}ms • 
          {sacredTexts.length + mysticalEchoes.length} passages discovered
        </p>
        <p className="text-mystic-silver-400 font-manuscript text-sm italic mt-1">
          {seekerGuidance}
        </p>
      </div>
      
      {/* Twin mirrors layout */}
      <div className="twin-mirrors-layout">
        {/* Sacred Texts Panel */}
        <div className="sacred-texts-panel">
          <h2 className="panel-title">
            {borgesianTerms.exactRefs}
          </h2>
          
          {sacredTexts.length > 0 ? (
            <div className="space-y-4">
              {sacredTexts.map((scroll, index) => (
                <div
                  key={scroll.id}
                  className={`ancient-scroll animate-mystical-reveal animate-mystical-reveal-${Math.min(index + 1, 5)}`}
                >
                  <div className="relevance-star">
                    ✦ Found exact words {scroll.relevanceStars.toFixed(3)}
                  </div>
                  
                  <h3 className="illuminated-title">
                    "{scroll.title}"
                  </h3>
                  
                  <p className="scribe-name">
                    by {scroll.author}
                  </p>
                  
                  <p className="chamber-location">
                    {scroll.mysticalLocation}
                  </p>
                  
                  {scroll.ancientWords && (
                    <div 
                      className="text-parchment-100 font-manuscript text-sm leading-relaxed mb-4 p-3 bg-infinite-depths-900 bg-opacity-30"
                      dangerouslySetInnerHTML={{ __html: scroll.ancientWords }}
                    />
                  )}
                  
                  <button
                    onClick={() => onEnterChamber(scroll.id)}
                    className="enter-text-portal"
                  >
                    {borgesianTerms.enterText}
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="w-16 h-16 mx-auto mb-4 border border-ancient-gold-800 opacity-50 clip-hexagon"></div>
              <p className="text-mystic-silver-500 font-manuscript italic">
                "The sacred texts remain silent on this matter..."
              </p>
            </div>
          )}
        </div>
        
        {/* Mystical Echoes Panel */}
        <div className="mystical-echoes-panel">
          <h2 className="panel-title">
            {borgesianTerms.semanticEchoes}
          </h2>
          
          {mysticalEchoes.length > 0 ? (
            <div className="space-y-4">
              {mysticalEchoes.map((echo, index) => (
                <div
                  key={echo.id}
                  className={`ethereal-connection animate-mystical-reveal animate-mystical-reveal-${Math.min(index + 1, 5)}`}
                >
                  <div className="similarity-gem">
                    ♦ Resonant with your seeking {echo.similarity.toFixed(3)}
                  </div>
                  
                  <h3 className="illuminated-title">
                    "{echo.title}"
                  </h3>
                  
                  <p className="spirit-scribe">
                    by {echo.author}
                  </p>
                  
                  <p className="hidden-passage">
                    {echo.hiddenPassage}
                  </p>
                  
                  {echo.contentPreview && (
                    <div className="text-parchment-100 font-manuscript text-sm leading-relaxed mb-4 p-3 bg-infinite-depths-900 bg-opacity-30">
                      {echo.contentPreview.length > 200 
                        ? `${echo.contentPreview.substring(0, 200)}...`
                        : echo.contentPreview
                      }
                    </div>
                  )}
                  
                  <button
                    onClick={() => onFollowThread(echo.id)}
                    className="follow-thread"
                  >
                    {borgesianTerms.followThread}
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="w-16 h-16 mx-auto mb-4 border border-ancient-gold-800 opacity-50 clip-hexagon transform rotate-180"></div>
              <p className="text-mystic-silver-500 font-manuscript italic">
                "The mystical echoes fall silent..."
              </p>
            </div>
          )}
        </div>
      </div>
      
      {/* Footer with mystical elements */}
      <div className="p-8 text-center border-t border-ancient-gold-800">
        <p className="text-mystic-silver-400 font-manuscript text-sm italic">
          "In the Library, every search unveils both the sought and the unexpected"
        </p>
        
        {/* Decorative hexagonal elements */}
        <div className="flex justify-center space-x-4 mt-4">
          <div className="w-3 h-3 border border-ancient-gold-800 opacity-40 clip-hexagon"></div>
          <div className="w-3 h-3 border border-ancient-gold-800 opacity-60 clip-hexagon"></div>
          <div className="w-3 h-3 border border-ancient-gold-800 opacity-40 clip-hexagon"></div>
        </div>
      </div>
    </div>
  );
};

export default TwinMirrorsOfKnowledge;