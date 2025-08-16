-- =========================================================================
-- V001: LibraryOfBabel Initial Database Schema
-- =========================================================================
-- Description: Core database schema with authors, books, and chunks tables
-- Author: Database Team
-- Date: 2025-08-15
-- =========================================================================

-- Authors table for normalized author data
CREATE TABLE authors (
    author_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Books table for metadata
CREATE TABLE books (
    book_id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    author VARCHAR(255),
    author_id INTEGER REFERENCES authors(author_id),
    publisher VARCHAR(255),
    publication_date VARCHAR(100),
    publication_year INTEGER,
    language VARCHAR(50) DEFAULT 'english',
    isbn VARCHAR(50),
    description TEXT,
    genre VARCHAR(100),
    word_count INTEGER DEFAULT 0,
    file_path VARCHAR(1000),
    source_location VARCHAR(1000),
    import_source VARCHAR(100),
    processed_date TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Chunks table for searchable text segments
CREATE TABLE chunks (
    chunk_id VARCHAR(255) PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
    chunk_type VARCHAR(50) NOT NULL,
    title VARCHAR(500),
    content TEXT NOT NULL,
    word_count INTEGER DEFAULT 0,
    character_count INTEGER DEFAULT 0,
    chapter_number INTEGER,
    section_number INTEGER,
    paragraph_number INTEGER,
    start_position INTEGER DEFAULT 0,
    end_position INTEGER DEFAULT 0,
    parent_chunk_id VARCHAR(255),
    search_vector tsvector,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_books_title ON books USING GIN(to_tsvector('english', title));
CREATE INDEX idx_books_author ON books(author);
CREATE INDEX idx_books_author_id ON books(author_id);
CREATE INDEX idx_books_publication_year ON books(publication_year);
CREATE INDEX idx_books_genre ON books(genre);
CREATE INDEX idx_books_word_count ON books(word_count);
CREATE INDEX idx_books_import_source ON books(import_source);
CREATE INDEX idx_books_processed_date ON books(processed_date);

CREATE INDEX idx_chunks_book_id ON chunks(book_id);
CREATE INDEX idx_chunks_type ON chunks(chunk_type);
CREATE INDEX idx_chunks_chapter ON chunks(chapter_number);
CREATE INDEX idx_chunks_word_count ON chunks(word_count);
CREATE INDEX idx_chunks_parent ON chunks(parent_chunk_id);

-- Full-text search indexes
CREATE INDEX idx_chunks_search_vector ON chunks USING GIN(search_vector);
CREATE INDEX idx_chunks_content_search ON chunks USING GIN(to_tsvector('english', content));

-- Composite indexes for common query patterns
CREATE INDEX idx_books_author_year ON books(author, publication_year);
CREATE INDEX idx_chunks_book_type ON chunks(book_id, chunk_type);
CREATE INDEX idx_chunks_book_chapter ON chunks(book_id, chapter_number);

-- Authors table indexes
CREATE UNIQUE INDEX idx_authors_name ON authors(name);

-- Function to automatically update search_vector
CREATE OR REPLACE FUNCTION update_search_vector() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', COALESCE(NEW.title, '') || ' ' || COALESCE(NEW.content, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update search_vector on insert/update
CREATE TRIGGER trigger_update_search_vector
    BEFORE INSERT OR UPDATE ON chunks
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();

-- Function to update book word count
CREATE OR REPLACE FUNCTION update_book_word_count() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        UPDATE books 
        SET word_count = (
            SELECT COALESCE(SUM(word_count), 0) 
            FROM chunks 
            WHERE book_id = NEW.book_id
        )
        WHERE book_id = NEW.book_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE books 
        SET word_count = (
            SELECT COALESCE(SUM(word_count), 0) 
            FROM chunks 
            WHERE book_id = OLD.book_id
        )
        WHERE book_id = OLD.book_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update book word count
CREATE TRIGGER trigger_update_book_word_count
    AFTER INSERT OR UPDATE OR DELETE ON chunks
    FOR EACH ROW EXECUTE FUNCTION update_book_word_count();