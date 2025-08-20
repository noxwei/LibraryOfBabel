-- =============================================================================
-- BabelProcessorDb Test Database Schema
-- =============================================================================
-- Minimal schema based on standardized API requirements
-- Core tables: books, chunks, chunk_embeddings
-- =============================================================================

-- Create database (run manually)
-- CREATE DATABASE BabelProcessorDb;
-- \c BabelProcessorDb;

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================================================
-- CORE TABLES
-- =============================================================================

-- Books table - simplified for testing
CREATE TABLE IF NOT EXISTS books (
    book_id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    author VARCHAR(255),
    publisher VARCHAR(255),
    publication_date VARCHAR(100),
    language VARCHAR(50) DEFAULT 'english',
    isbn VARCHAR(50),
    description TEXT,
    genre VARCHAR(100),
    word_count INTEGER DEFAULT 0,
    file_path VARCHAR(1000),
    processed_date TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Chunks table - text segments for embedding
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id VARCHAR(255) PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
    chunk_type VARCHAR(50) NOT NULL, -- 'chapter', 'paragraph', 'sentence'
    title VARCHAR(500),
    content TEXT NOT NULL,
    word_count INTEGER DEFAULT 0,
    chapter_number INTEGER,
    section_number INTEGER,
    paragraph_number INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Chunk embeddings - vector storage for both models
CREATE TABLE IF NOT EXISTS chunk_embeddings (
    embedding_id SERIAL PRIMARY KEY,
    chunk_id VARCHAR(255) NOT NULL REFERENCES chunks(chunk_id) ON DELETE CASCADE,
    embedding_model VARCHAR(50) NOT NULL, -- 'nomic-embed-text', 'bge-m3'
    embedding_vector vector(768), -- Will be 1024 for BGE-M3
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(chunk_id, embedding_model)
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Book indexes
CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);

-- Chunk indexes  
CREATE INDEX IF NOT EXISTS idx_chunks_book_id ON chunks(book_id);
CREATE INDEX IF NOT EXISTS idx_chunks_type ON chunks(chunk_type);
CREATE INDEX IF NOT EXISTS idx_chunks_chapter ON chunks(chapter_number);

-- Embedding indexes
CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id ON chunk_embeddings(chunk_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_model ON chunk_embeddings(embedding_model);

-- Vector similarity indexes (will be created after embeddings are added)
-- CREATE INDEX idx_embeddings_vector_nomic ON chunk_embeddings USING hnsw (embedding_vector vector_cosine_ops) WHERE embedding_model = 'nomic-embed-text';
-- CREATE INDEX idx_embeddings_vector_bge ON chunk_embeddings USING hnsw (embedding_vector vector_cosine_ops) WHERE embedding_model = 'bge-m3';

-- =============================================================================
-- SAMPLE DATA FOR TESTING
-- =============================================================================

-- Insert a test book
INSERT INTO books (book_id, title, author, description, word_count) 
VALUES (1, 'Test Book for Pipeline', 'Test Author', 'A sample book for testing the embedding pipeline', 1000)
ON CONFLICT (book_id) DO NOTHING;

-- =============================================================================
-- UTILITY FUNCTIONS FOR TESTING
-- =============================================================================

-- Get embedding stats
CREATE OR REPLACE FUNCTION get_embedding_stats()
RETURNS TABLE(
    model VARCHAR(50),
    total_embeddings BIGINT,
    unique_chunks BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        embedding_model,
        COUNT(*) as total_embeddings,
        COUNT(DISTINCT chunk_id) as unique_chunks
    FROM chunk_embeddings 
    GROUP BY embedding_model
    ORDER BY embedding_model;
END;
$$ LANGUAGE plpgsql;

-- Get processing progress
CREATE OR REPLACE FUNCTION get_processing_progress()
RETURNS TABLE(
    total_books BIGINT,
    total_chunks BIGINT,
    chunks_with_nomic BIGINT,
    chunks_with_bge BIGINT,
    completion_percent_nomic NUMERIC,
    completion_percent_bge NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM books) as total_books,
        (SELECT COUNT(*) FROM chunks) as total_chunks,
        (SELECT COUNT(DISTINCT chunk_id) FROM chunk_embeddings WHERE embedding_model = 'nomic-embed-text') as chunks_with_nomic,
        (SELECT COUNT(DISTINCT chunk_id) FROM chunk_embeddings WHERE embedding_model = 'bge-m3') as chunks_with_bge,
        CASE 
            WHEN (SELECT COUNT(*) FROM chunks) = 0 THEN 0
            ELSE ROUND((SELECT COUNT(DISTINCT chunk_id) FROM chunk_embeddings WHERE embedding_model = 'nomic-embed-text')::NUMERIC / (SELECT COUNT(*) FROM chunks)::NUMERIC * 100, 2)
        END as completion_percent_nomic,
        CASE 
            WHEN (SELECT COUNT(*) FROM chunks) = 0 THEN 0
            ELSE ROUND((SELECT COUNT(DISTINCT chunk_id) FROM chunk_embeddings WHERE embedding_model = 'bge-m3')::NUMERIC / (SELECT COUNT(*) FROM chunks)::NUMERIC * 100, 2)
        END as completion_percent_bge;
END;
$$ LANGUAGE plpgsql;

-- Test the schema
SELECT 'Schema created successfully' as status;