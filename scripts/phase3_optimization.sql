-- =============================================================================
-- ⚡ PHASE 3: PERFORMANCE OPTIMIZATION
-- =============================================================================

-- Fast trigram index for critical theory concepts
CREATE INDEX IF NOT EXISTS idx_chen_fast_trigram
ON chunks USING gist(content gist_trgm_ops)
WHERE content IS NOT NULL 
AND word_count BETWEEN 100 AND 1000
AND (content ~* 'philosophy|science|technology|art|literature'
     OR content ~* 'love|power|desire|identity|freedom'
     OR content ~* 'queer|gender|sexuality|surveillance'
     OR content ~* 'magic|fantasy|scifi|future|robot');

-- Optimized composite index for analogical searches  
CREATE INDEX IF NOT EXISTS idx_chen_analogical_composite
ON chunks(chunk_type, word_count)
INCLUDE (content, search_vector)
WHERE content IS NOT NULL
AND word_count BETWEEN 100 AND 1200;

-- Update table statistics
ANALYZE chunks;