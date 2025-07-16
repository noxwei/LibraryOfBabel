-- MULTI-MODEL ROUTING SCHEMA EXTENSIONS
-- LibraryOfBabel PostgreSQL Enhancements for Intelligent Embedding Routing
-- =======================================================================

-- 1. CONTENT TYPE CLASSIFICATION TABLE
-- Stores AI-determined content types for intelligent routing
CREATE TABLE IF NOT EXISTS content_classifications (
    classification_id SERIAL PRIMARY KEY,
    chunk_id VARCHAR(255) NOT NULL,
    book_id INTEGER NOT NULL REFERENCES books(book_id),
    content_type VARCHAR(50) NOT NULL, -- 'technical', 'dialogue', 'narrative', 'factual', 'abstract'
    detected_language VARCHAR(10) DEFAULT 'en',
    emotional_tone VARCHAR(20), -- 'neutral', 'emotional', 'analytical', 'creative'
    confidence_score DECIMAL(3,2) DEFAULT 0.0,
    classification_model VARCHAR(50) DEFAULT 'magistral',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(chunk_id)
);

-- 2. EMBEDDING MODEL ROUTING DECISIONS
-- Tracks which model was chosen for each chunk and why
CREATE TABLE IF NOT EXISTS embedding_routing_log (
    routing_id SERIAL PRIMARY KEY,
    chunk_id VARCHAR(255) NOT NULL,
    book_id INTEGER NOT NULL REFERENCES books(book_id),
    selected_model VARCHAR(100) NOT NULL,
    routing_reason TEXT, -- JSON with decision factors
    content_type VARCHAR(50),
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. ENHANCED CHUNK_EMBEDDINGS (modify existing)
-- Add routing metadata to existing table
ALTER TABLE chunk_embeddings ADD COLUMN IF NOT EXISTS content_type VARCHAR(50);
ALTER TABLE chunk_embeddings ADD COLUMN IF NOT EXISTS routing_reason TEXT;
ALTER TABLE chunk_embeddings ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(3,2);

-- 4. EXTRACTED ENTITIES TABLE
-- Store entities/keywords alongside embeddings for hybrid search
CREATE TABLE IF NOT EXISTS chunk_entities (
    entity_id SERIAL PRIMARY KEY,
    chunk_id VARCHAR(255) NOT NULL,
    book_id INTEGER NOT NULL REFERENCES books(book_id),
    entity_text VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50), -- 'person', 'place', 'concept', 'technical_term'
    confidence DECIMAL(3,2) DEFAULT 0.0,
    extraction_model VARCHAR(50) DEFAULT 'magistral',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 5. CHUNK SUMMARIES TABLE
-- Store AI-generated summaries for noise reduction
CREATE TABLE IF NOT EXISTS chunk_summaries (
    summary_id SERIAL PRIMARY KEY,
    chunk_id VARCHAR(255) NOT NULL UNIQUE,
    book_id INTEGER NOT NULL REFERENCES books(book_id),
    original_length INTEGER,
    summary_text TEXT NOT NULL,
    summary_length INTEGER,
    compression_ratio DECIMAL(4,2),
    summary_model VARCHAR(50) DEFAULT 'magistral',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 6. SEARCH PERFORMANCE METRICS
-- Track performance of different routing strategies
CREATE TABLE IF NOT EXISTS search_performance_metrics (
    metric_id SERIAL PRIMARY KEY,
    query_text TEXT,
    embedding_model VARCHAR(100),
    routing_strategy VARCHAR(50), -- 'single_model', 'intelligent_routing', 'fallback'
    results_count INTEGER,
    response_time_ms INTEGER,
    relevance_score DECIMAL(3,2),
    user_feedback INTEGER, -- 1-5 rating
    created_at TIMESTAMP DEFAULT NOW()
);

-- INDEXES FOR PERFORMANCE
-- =====================

-- Content classification indexes
CREATE INDEX IF NOT EXISTS idx_content_classifications_type ON content_classifications(content_type);
CREATE INDEX IF NOT EXISTS idx_content_classifications_book ON content_classifications(book_id);
CREATE INDEX IF NOT EXISTS idx_content_classifications_confidence ON content_classifications(confidence_score DESC);

-- Routing log indexes
CREATE INDEX IF NOT EXISTS idx_routing_log_model ON embedding_routing_log(selected_model);
CREATE INDEX IF NOT EXISTS idx_routing_log_content_type ON embedding_routing_log(content_type);
CREATE INDEX IF NOT EXISTS idx_routing_log_book ON embedding_routing_log(book_id);

-- Enhanced chunk_embeddings indexes (add to existing)
CREATE INDEX IF NOT EXISTS idx_chunk_embeddings_content_type ON chunk_embeddings(content_type);
CREATE INDEX IF NOT EXISTS idx_chunk_embeddings_confidence ON chunk_embeddings(confidence_score DESC);

-- Entity search indexes
CREATE INDEX IF NOT EXISTS idx_chunk_entities_text_gin ON chunk_entities USING gin(to_tsvector('english', entity_text));
CREATE INDEX IF NOT EXISTS idx_chunk_entities_type ON chunk_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_chunk_entities_book ON chunk_entities(book_id);

-- Summary indexes
CREATE INDEX IF NOT EXISTS idx_chunk_summaries_book ON chunk_summaries(book_id);
CREATE INDEX IF NOT EXISTS idx_chunk_summaries_compression ON chunk_summaries(compression_ratio);

-- Performance metrics indexes
CREATE INDEX IF NOT EXISTS idx_search_metrics_model ON search_performance_metrics(embedding_model);
CREATE INDEX IF NOT EXISTS idx_search_metrics_strategy ON search_performance_metrics(routing_strategy);
CREATE INDEX IF NOT EXISTS idx_search_metrics_created ON search_performance_metrics(created_at DESC);

-- TABLE COMMENTS FOR DOCUMENTATION
-- ===============================

COMMENT ON TABLE content_classifications IS 'AI-powered content type classification for intelligent embedding model routing';
COMMENT ON TABLE embedding_routing_log IS 'Audit log of embedding model selection decisions and performance';
COMMENT ON TABLE chunk_entities IS 'Extracted entities and keywords for hybrid lexical + vector search';
COMMENT ON TABLE chunk_summaries IS 'AI-generated summaries to reduce embedding noise';
COMMENT ON TABLE search_performance_metrics IS 'Performance tracking for A/B testing routing strategies';

-- GRANT PERMISSIONS
-- ================

-- Grant access to application user
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO weixiangzhang;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO weixiangzhang;