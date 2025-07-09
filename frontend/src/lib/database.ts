/**
 * LibraryOfBabel Database Connection
 * Connects Next.js frontend to PostgreSQL backend with 360 books
 */

import { Pool } from 'pg';

// Database configuration
const dbConfig = {
  host: process.env.DB_HOST || 'localhost',
  database: process.env.DB_NAME || 'knowledge_base',
  user: process.env.DB_USER || 'weixiangzhang',
  port: parseInt(process.env.DB_PORT || '5432'),
  password: process.env.DB_PASSWORD,
  // Connection pool settings
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
};

// Create connection pool
const pool = new Pool(dbConfig);

// Handle pool errors
pool.on('error', (err) => {
  console.error('Unexpected error on idle client', err);
  process.exit(-1);
});

export interface BookResult {
  book_id: number;
  title: string;
  author: string;
  publication_year?: number;
  genre?: string;
  word_count: number;
  chunk_id: string;
  chunk_type: string;
  content: string;
  chapter_number?: number;
  section_number?: number;
  relevance: number;
}

export interface SearchResponse {
  query: string;
  results: BookResult[];
  totalResults: number;
  searchTime: string;
  libraryStats: {
    totalBooks: number;
    totalWords: number;
    totalChunks: number;
  };
  suggestions?: string[];
}

/**
 * Execute full-text search across the 360-book database
 */
export async function searchDatabase(query: string, limit: number = 8): Promise<SearchResponse> {
  const startTime = Date.now();
  
  try {
    const client = await pool.connect();
    
    try {
      // Full-text search with relevance ranking
      const searchQuery = `
        SELECT 
          c.chunk_id,
          c.book_id,
          b.title,
          b.author,
          b.publication_year,
          b.genre,
          b.word_count,
          c.chunk_type,
          c.content,
          c.chapter_number,
          c.section_number,
          ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', $1)) as relevance
        FROM chunks c
        JOIN books b ON c.book_id = b.book_id
        WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', $1)
        ORDER BY relevance DESC, b.word_count DESC
        LIMIT $2
      `;
      
      const result = await client.query(searchQuery, [query, limit]);
      
      // Get library statistics
      const statsQuery = `
        SELECT 
          (SELECT COUNT(*) FROM books) as total_books,
          (SELECT SUM(word_count) FROM books) as total_words,
          (SELECT COUNT(*) FROM chunks) as total_chunks
      `;
      
      const statsResult = await client.query(statsQuery);
      const stats = statsResult.rows[0];
      
      const searchTime = `${Date.now() - startTime}ms`;
      
      // Generate suggestions if no results
      const suggestions = result.rows.length === 0 ? [
        "Try searching for specific authors like 'Octavia Butler' or 'Harari'",
        "Search for topics like 'consciousness', 'quantum physics', or 'surveillance'",
        "Use broader terms like 'AI', 'technology', or 'philosophy'",
        "Try book titles like 'Parable of the Sower' or 'Sapiens'"
      ] : [];
      
      return {
        query,
        results: result.rows.map(row => ({
          book_id: row.book_id,
          title: row.title,
          author: row.author,
          publication_year: row.publication_year,
          genre: row.genre,
          word_count: row.word_count,
          chunk_id: row.chunk_id,
          chunk_type: row.chunk_type,
          content: row.content,
          chapter_number: row.chapter_number,
          section_number: row.section_number,
          relevance: parseFloat(row.relevance) || 0
        })),
        totalResults: result.rows.length,
        searchTime,
        libraryStats: {
          totalBooks: parseInt(stats.total_books) || 0,
          totalWords: parseInt(stats.total_words) || 0,
          totalChunks: parseInt(stats.total_chunks) || 0
        },
        suggestions
      };
      
    } finally {
      client.release();
    }
    
  } catch (error) {
    console.error('Database search error:', error);
    throw new Error('Database search failed');
  }
}

/**
 * Get random books for "I'm Feeling Curious" feature
 */
export async function getRandomBooks(limit: number = 5): Promise<BookResult[]> {
  try {
    const client = await pool.connect();
    
    try {
      const randomQuery = `
        SELECT 
          c.chunk_id,
          c.book_id,
          b.title,
          b.author,
          b.publication_year,
          b.genre,
          b.word_count,
          c.chunk_type,
          c.content,
          c.chapter_number,
          c.section_number,
          0.8 as relevance
        FROM chunks c
        JOIN books b ON c.book_id = b.book_id
        WHERE c.chunk_type = 'chapter'
        ORDER BY RANDOM()
        LIMIT $1
      `;
      
      const result = await client.query(randomQuery, [limit]);
      
      return result.rows.map(row => ({
        book_id: row.book_id,
        title: row.title,
        author: row.author,
        publication_year: row.publication_year,
        genre: row.genre,
        word_count: row.word_count,
        chunk_id: row.chunk_id,
        chunk_type: row.chunk_type,
        content: row.content,
        chapter_number: row.chapter_number,
        section_number: row.section_number,
        relevance: parseFloat(row.relevance) || 0
      }));
      
    } finally {
      client.release();
    }
    
  } catch (error) {
    console.error('Random books error:', error);
    throw new Error('Failed to get random books');
  }
}

/**
 * Test database connection and return health status
 */
export async function testConnection(): Promise<{ 
  connected: boolean; 
  totalBooks: number; 
  totalChunks: number; 
  totalWords: number;
}> {
  try {
    const client = await pool.connect();
    
    try {
      const result = await client.query(`
        SELECT 
          (SELECT COUNT(*) FROM books) as total_books,
          (SELECT COUNT(*) FROM chunks) as total_chunks,
          (SELECT SUM(word_count) FROM books) as total_words
      `);
      
      const stats = result.rows[0];
      
      return {
        connected: true,
        totalBooks: parseInt(stats.total_books) || 0,
        totalChunks: parseInt(stats.total_chunks) || 0,
        totalWords: parseInt(stats.total_words) || 0
      };
      
    } finally {
      client.release();
    }
    
  } catch (error) {
    console.error('Database connection test failed:', error);
    return {
      connected: false,
      totalBooks: 0,
      totalChunks: 0,
      totalWords: 0
    };
  }
}

export default pool;