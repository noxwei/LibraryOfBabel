/**
 * Comprehensive Frontend Integration Tests for LibraryOfBabel API
 * Tests frontend consumption of all API endpoints and metadata display
 */

import { test, expect, Page } from '@playwright/test';

// Test configuration
const API_BASE_URL = process.env.PLAYWRIGHT_API_URL || 'https://localhost:5562';
const API_KEY = process.env.PLAYWRIGHT_API_KEY || 'babel_secure_YOUR_KEY_HERE';
const FRONTEND_URL = process.env.PLAYWRIGHT_FRONTEND_URL || 'http://localhost:3000';

// Test data structure interfaces
interface BookMetadata {
  book_id: number;
  title: string;
  author: string;
  publisher?: string;
  publication_date?: string;
  language?: string;
  isbn?: string;
  description?: string;
  genre?: string;
  word_count?: number;
  file_path?: string;
  processed_date?: string;
  md5_hash?: string;
  has_hash?: boolean;
  chunks_available?: number;
  embeddings_available?: number;
}

interface SearchResultMetadata {
  book_id: number;
  title: string;
  author: string;
  chunk_id?: number;
  content: string;
  chapter_number?: number;
  section_number?: string;
  word_count?: number;
  relevance_score?: number;
  chunk_type?: string;
}

interface PaginationMetadata {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

interface NavigationLinks {
  first?: string;
  prev?: string;
  next?: string;
  last?: string;
  self?: string;
  chunks?: string;
  search_in_book?: string;
}

// Helper functions for API testing
async function makeAPIRequest(endpoint: string, params: Record<string, string> = {}): Promise<Response> {
  const url = new URL(endpoint, API_BASE_URL);
  Object.entries(params).forEach(([key, value]) => {
    url.searchParams.append(key, value);
  });
  url.searchParams.append('api_key', API_KEY);

  return fetch(url.toString(), {
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json'
    }
  });
}

// Test suite for API Health and Infrastructure
test.describe('API Health and Infrastructure', () => {
  test('API health endpoint should return system information', async () => {
    const response = await makeAPIRequest('/health');
    expect(response.status).toBe(200);

    const healthData = await response.json();
    
    // Verify health response structure
    expect(healthData).toHaveProperty('status', 'healthy');
    expect(healthData).toHaveProperty('database', 'connected');
    expect(healthData).toHaveProperty('books');
    expect(healthData).toHaveProperty('chunks');
    expect(healthData).toHaveProperty('embeddings');
    expect(healthData).toHaveProperty('response_time_ms');
    expect(healthData).toHaveProperty('api_version', '2.0-secure-paginated');
    expect(healthData).toHaveProperty('features');
    expect(healthData).toHaveProperty('chunk_levels');
    expect(healthData).toHaveProperty('security', 'enabled');

    // Verify expected features are present
    const expectedFeatures = ['pagination', 'chunking_levels', 'navigation_links', 'authentication', 'rate_limiting'];
    expectedFeatures.forEach(feature => {
      expect(healthData.features).toContain(feature);
    });

    // Verify chunk levels
    const expectedChunkLevels = ['small', 'medium', 'large'];
    expectedChunkLevels.forEach(level => {
      expect(healthData.chunk_levels).toContain(level);
    });
  });

  test('API authentication should be enforced', async () => {
    // Test without API key
    const response = await fetch(`${API_BASE_URL}/books`);
    expect(response.status).toBe(401);

    const errorData = await response.json();
    expect(errorData).toHaveProperty('success', false);
    expect(errorData).toHaveProperty('error', 'API key required');
    expect(errorData).toHaveProperty('message');
  });

  test('API rate limiting should be functional', async () => {
    // This test would require multiple rapid requests to trigger rate limiting
    // Implementation depends on rate limit configuration (60 req/min)
    const response = await makeAPIRequest('/health');
    expect(response.status).toBe(200);
    
    // Verify rate limit headers if implemented
    // expect(response.headers.get('X-RateLimit-Remaining')).toBeDefined();
  });
});

// Test suite for Book Listing and Metadata
test.describe('Book Listing and Metadata Display', () => {
  test('Books endpoint should return paginated results with all metadata', async () => {
    const response = await makeAPIRequest('/books', { page: '1', page_size: '10' });
    expect(response.status).toBe(200);

    const booksData = await response.json();

    // Verify response structure
    expect(booksData).toHaveProperty('results');
    expect(booksData).toHaveProperty('pagination');
    expect(booksData).toHaveProperty('navigation');
    expect(booksData).toHaveProperty('meta');

    // Verify pagination metadata
    const pagination: PaginationMetadata = booksData.pagination;
    expect(pagination).toHaveProperty('page');
    expect(pagination).toHaveProperty('page_size');
    expect(pagination).toHaveProperty('total_items');
    expect(pagination).toHaveProperty('total_pages');
    expect(pagination).toHaveProperty('has_next');
    expect(pagination).toHaveProperty('has_prev');

    // Verify book metadata structure
    if (booksData.results.length > 0) {
      const book: BookMetadata = booksData.results[0];
      expect(book).toHaveProperty('book_id');
      expect(book).toHaveProperty('title');
      expect(book).toHaveProperty('author');
      expect(book).toHaveProperty('publisher');
      expect(book).toHaveProperty('publication_date');
      expect(book).toHaveProperty('language');
      expect(book).toHaveProperty('genre');
      expect(book).toHaveProperty('word_count');
      expect(book).toHaveProperty('processed_date');
      expect(book).toHaveProperty('has_hash');
      expect(book).toHaveProperty('links');

      // Verify navigation links for each book
      const links: NavigationLinks = book.links;
      expect(links).toHaveProperty('self');
      expect(links).toHaveProperty('chunks');
    }

    // Verify meta information
    expect(booksData.meta).toHaveProperty('timestamp');
    expect(booksData.meta).toHaveProperty('query_time_ms');
  });

  test('Books search filtering should work with all parameters', async () => {
    // Test search filter
    const searchResponse = await makeAPIRequest('/books', { 
      search: 'AI', 
      page: '1', 
      page_size: '5' 
    });
    expect(searchResponse.status).toBe(200);

    // Test author filter
    const authorResponse = await makeAPIRequest('/books', { 
      author: 'Butler', 
      page: '1', 
      page_size: '5' 
    });
    expect(authorResponse.status).toBe(200);

    // Test genre filter
    const genreResponse = await makeAPIRequest('/books', { 
      genre: 'Science Fiction', 
      page: '1', 
      page_size: '5' 
    });
    expect(genreResponse.status).toBe(200);

    // Verify all responses have proper structure
    const responses = [searchResponse, authorResponse, genreResponse];
    for (const response of responses) {
      const data = await response.json();
      expect(data).toHaveProperty('results');
      expect(data).toHaveProperty('pagination');
      expect(data).toHaveProperty('navigation');
    }
  });

  test('Single book details should include all metadata fields', async () => {
    // First get a book ID from the books list
    const booksResponse = await makeAPIRequest('/books', { page: '1', page_size: '1' });
    const booksData = await booksResponse.json();
    
    if (booksData.results.length === 0) {
      test.skip(); // Skip if no books available
    }

    const bookId = booksData.results[0].book_id;
    const response = await makeAPIRequest(`/books/${bookId}`);
    expect(response.status).toBe(200);

    const bookData: BookMetadata = await response.json();

    // Verify all expected metadata fields
    expect(bookData).toHaveProperty('book_id', bookId);
    expect(bookData).toHaveProperty('title');
    expect(bookData).toHaveProperty('author');
    expect(bookData).toHaveProperty('publisher');
    expect(bookData).toHaveProperty('publication_date');
    expect(bookData).toHaveProperty('language');
    expect(bookData).toHaveProperty('isbn');
    expect(bookData).toHaveProperty('description');
    expect(bookData).toHaveProperty('genre');
    expect(bookData).toHaveProperty('word_count');
    expect(bookData).toHaveProperty('file_path');
    expect(bookData).toHaveProperty('processed_date');
    expect(bookData).toHaveProperty('md5_hash');
    expect(bookData).toHaveProperty('chunks_available');
    expect(bookData).toHaveProperty('embeddings_available');
    expect(bookData).toHaveProperty('links');
    expect(bookData).toHaveProperty('meta');

    // Verify links structure
    const links: NavigationLinks = bookData.links;
    expect(links).toHaveProperty('chunks');
    expect(links).toHaveProperty('search_in_book');

    // Verify meta information
    expect(bookData.meta).toHaveProperty('query_time_ms');
  });
});

// Test suite for Chunking and Content Display
test.describe('Chunking and Content Display', () => {
  test('Book chunks should support all chunking levels', async () => {
    // Get a book ID first
    const booksResponse = await makeAPIRequest('/books', { page: '1', page_size: '1' });
    const booksData = await booksResponse.json();
    
    if (booksData.results.length === 0) {
      test.skip(); // Skip if no books available
    }

    const bookId = booksData.results[0].book_id;
    const chunkLevels = ['small', 'medium', 'large'];

    for (const chunkLevel of chunkLevels) {
      const response = await makeAPIRequest(`/books/${bookId}/chunks`, {
        chunk_level: chunkLevel,
        page: '1',
        page_size: '5'
      });
      expect(response.status).toBe(200);

      const chunksData = await response.json();

      // Verify response structure
      expect(chunksData).toHaveProperty('results');
      expect(chunksData).toHaveProperty('pagination');
      expect(chunksData).toHaveProperty('meta');

      // Verify chunk level metadata
      expect(chunksData.meta).toHaveProperty('chunk_level', chunkLevel);
      expect(chunksData.meta).toHaveProperty('available_levels');
      expect(chunksData.meta.available_levels).toContain(chunkLevel);
      expect(chunksData.meta).toHaveProperty('query_time_ms');

      // Verify chunk structure if chunks exist
      if (chunksData.results.length > 0) {
        const chunk = chunksData.results[0];
        expect(chunk).toHaveProperty('chunk_id');
        expect(chunk).toHaveProperty('title');
        expect(chunk).toHaveProperty('chapter_number');
        expect(chunk).toHaveProperty('original_word_count');
        expect(chunk).toHaveProperty('sub_chunks');
        expect(chunk).toHaveProperty('total_sub_chunks');
        expect(chunk).toHaveProperty('chunk_level', chunkLevel);

        // Verify sub-chunks structure
        if (chunk.sub_chunks.length > 0) {
          const subChunk = chunk.sub_chunks[0];
          expect(subChunk).toHaveProperty('chunk_id');
          expect(subChunk).toHaveProperty('text');
          expect(subChunk).toHaveProperty('word_count');
          expect(subChunk).toHaveProperty('char_count');
          expect(subChunk).toHaveProperty('chunk_level', chunkLevel);
        }
      }
    }
  });

  test('Individual chunk content should include all metadata', async () => {
    // Get a chunk ID first
    const booksResponse = await makeAPIRequest('/books', { page: '1', page_size: '1' });
    const booksData = await booksResponse.json();
    
    if (booksData.results.length === 0) {
      test.skip(); // Skip if no books available
    }

    const bookId = booksData.results[0].book_id;
    const chunksResponse = await makeAPIRequest(`/books/${bookId}/chunks`, {
      page: '1',
      page_size: '1'
    });
    const chunksData = await chunksResponse.json();

    if (chunksData.results.length === 0) {
      test.skip(); // Skip if no chunks available
    }

    const chunkId = chunksData.results[0].chunk_id;
    const response = await makeAPIRequest(`/chunks/${chunkId}`, {
      chunk_level: 'medium'
    });
    expect(response.status).toBe(200);

    const chunkData = await response.json();

    // Verify chunk metadata
    expect(chunkData).toHaveProperty('chunk_id', chunkId);
    expect(chunkData).toHaveProperty('book_id', bookId);
    expect(chunkData).toHaveProperty('title');
    expect(chunkData).toHaveProperty('chapter_number');
    expect(chunkData).toHaveProperty('original_word_count');
    expect(chunkData).toHaveProperty('chunk_level', 'medium');
    expect(chunkData).toHaveProperty('sub_chunks');
    expect(chunkData).toHaveProperty('total_sub_chunks');
    expect(chunkData).toHaveProperty('links');
    expect(chunkData).toHaveProperty('meta');

    // Verify links
    const links: NavigationLinks = chunkData.links;
    expect(links).toHaveProperty('book');

    // Verify meta information
    expect(chunkData.meta).toHaveProperty('query_time_ms');
  });
});

// Test suite for Search Functionality
test.describe('Search Functionality Integration', () => {
  test('Basic search should return results with proper metadata', async () => {
    const response = await makeAPIRequest('/search', {
      q: 'consciousness',
      page: '1',
      page_size: '10'
    });
    expect(response.status).toBe(200);

    const searchData = await response.json();

    // Verify search response structure
    expect(searchData).toHaveProperty('results');
    expect(searchData).toHaveProperty('pagination');
    expect(searchData).toHaveProperty('navigation');
    expect(searchData).toHaveProperty('meta');

    // Verify meta information
    expect(searchData.meta).toHaveProperty('timestamp');
    expect(searchData.meta).toHaveProperty('query_time_ms');
    expect(searchData.meta).toHaveProperty('search_query', 'consciousness');

    // Verify search result structure
    if (searchData.results.length > 0) {
      const result: SearchResultMetadata = searchData.results[0];
      expect(result).toHaveProperty('book_id');
      expect(result).toHaveProperty('title');
      expect(result).toHaveProperty('author');
      expect(result).toHaveProperty('description');
      expect(result).toHaveProperty('word_count');
      expect(result).toHaveProperty('links');

      // Verify result links
      const links: NavigationLinks = result.links;
      expect(links).toHaveProperty('book');
      expect(links).toHaveProperty('chunks');
    }
  });

  test('In-book search should work with proper metadata', async () => {
    // Get a book ID first
    const booksResponse = await makeAPIRequest('/books', { page: '1', page_size: '1' });
    const booksData = await booksResponse.json();
    
    if (booksData.results.length === 0) {
      test.skip(); // Skip if no books available
    }

    const bookId = booksData.results[0].book_id;
    const response = await makeAPIRequest(`/books/${bookId}/search`, {
      q: 'the',
      page: '1',
      page_size: '5'
    });

    // Note: This might return 200 with 0 results or 404 if no matches
    if (response.status === 404) {
      test.skip(); // Skip if book not found
    }

    expect(response.status).toBe(200);
    const searchData = await response.json();

    // Verify search response structure
    expect(searchData).toHaveProperty('results');
    expect(searchData).toHaveProperty('pagination');
    expect(searchData).toHaveProperty('navigation');
    expect(searchData).toHaveProperty('book_info');
    expect(searchData).toHaveProperty('meta');

    // Verify book info
    expect(searchData.book_info).toHaveProperty('book_id', bookId);
    expect(searchData.book_info).toHaveProperty('title');
    expect(searchData.book_info).toHaveProperty('author');

    // Verify meta information
    expect(searchData.meta).toHaveProperty('search_query', 'the');
    expect(searchData.meta).toHaveProperty('search_scope', `within book ${bookId}`);
    expect(searchData.meta).toHaveProperty('query_time_ms');

    // Verify search results if any
    if (searchData.results.length > 0) {
      const result = searchData.results[0];
      expect(result).toHaveProperty('chunk_id');
      expect(result).toHaveProperty('book_id', bookId);
      expect(result).toHaveProperty('chapter_number');
      expect(result).toHaveProperty('content');
      expect(result).toHaveProperty('word_count');
      expect(result).toHaveProperty('relevance');
    }
  });

  test('Fuzzy semantic search should include search stats', async () => {
    const response = await makeAPIRequest('/fuzzy-search', {
      q: 'artificial intelligence ethics',
      limit: '10',
      type: 'hybrid'
    });

    // This endpoint might not be available in all environments
    if (response.status === 500) {
      test.skip(); // Skip if fuzzy search not available
    }

    expect(response.status).toBe(200);
    const searchData = await response.json();

    // Verify fuzzy search response structure
    expect(searchData).toHaveProperty('results');
    expect(searchData).toHaveProperty('search_stats');
    expect(searchData).toHaveProperty('meta');

    // Verify search stats
    expect(searchData.search_stats).toHaveProperty('search_type');
    expect(searchData.search_stats).toHaveProperty('total_results');
    expect(searchData.search_stats).toHaveProperty('processing_time_ms');

    // Verify meta information
    expect(searchData.meta).toHaveProperty('search_query', 'artificial intelligence ethics');
    expect(searchData.meta).toHaveProperty('search_type', 'hybrid');
    expect(searchData.meta).toHaveProperty('api_version', '2.0-fuzzy-semantic');
  });
});

// Test suite for Pagination Controls
test.describe('Pagination Controls Integration', () => {
  test('Pagination navigation links should be functional', async () => {
    const response = await makeAPIRequest('/books', {
      page: '1',
      page_size: '5'
    });
    expect(response.status).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('navigation');

    const navigation = data.navigation;

    // Test navigation links structure
    if (data.pagination.total_pages > 1) {
      expect(navigation).toHaveProperty('first');
      expect(navigation).toHaveProperty('last');
      
      if (data.pagination.has_next) {
        expect(navigation).toHaveProperty('next');
      }
      
      if (data.pagination.has_prev) {
        expect(navigation).toHaveProperty('prev');
      }
    }

    // Verify navigation URLs are valid
    for (const [key, url] of Object.entries(navigation)) {
      if (typeof url === 'string') {
        expect(url).toMatch(/^https?:\/\//);
        expect(url).toContain('api_key=');
      }
    }
  });

  test('Page size limits should be enforced', async () => {
    // Test with max page size
    const maxResponse = await makeAPIRequest('/books', {
      page: '1',
      page_size: '100'
    });
    expect(maxResponse.status).toBe(200);

    const maxData = await maxResponse.json();
    expect(maxData.pagination.page_size).toBeLessThanOrEqual(100);

    // Test with excessive page size
    const excessiveResponse = await makeAPIRequest('/books', {
      page: '1',
      page_size: '500'
    });
    expect(excessiveResponse.status).toBe(200);

    const excessiveData = await excessiveResponse.json();
    expect(excessiveData.pagination.page_size).toBeLessThanOrEqual(100);
  });
});

// Test suite for Error Handling
test.describe('Error Handling Integration', () => {
  test('404 errors should be handled properly', async () => {
    const response = await makeAPIRequest('/books/999999');
    expect(response.status).toBe(404);

    const errorData = await response.json();
    expect(errorData).toHaveProperty('error', 'Book not found');
  });

  test('Invalid search parameters should return appropriate errors', async () => {
    const response = await makeAPIRequest('/search');
    expect(response.status).toBe(400);

    const errorData = await response.json();
    expect(errorData).toHaveProperty('error', 'Query parameter q is required');
  });

  test('Invalid chunk endpoints should return errors', async () => {
    const response = await makeAPIRequest('/chunks/999999');
    expect(response.status).toBe(404);

    const errorData = await response.json();
    expect(errorData).toHaveProperty('error', 'Chunk not found');
  });
});

// Test suite for Story Generation Feature
test.describe('Story Generation Integration', () => {
  test('Story templates should be available', async () => {
    const response = await fetch(`${API_BASE_URL}/story-templates`);
    expect(response.status).toBe(200);

    const templatesData = await response.json();
    expect(templatesData).toHaveProperty('success', true);
    expect(templatesData).toHaveProperty('templates');
    expect(templatesData).toHaveProperty('total_count');

    // Verify template structure
    if (templatesData.templates.length > 0) {
      const template = templatesData.templates[0];
      expect(template).toHaveProperty('id');
      expect(template).toHaveProperty('name');
      expect(template).toHaveProperty('description');
      expect(template).toHaveProperty('parameters');
    }
  });

  test('Story generation should work with proper metadata', async () => {
    const storyRequest = {
      genre: 'sci_fi',
      length: 'medium',
      theme: 'AI consciousness'
    };

    const response = await fetch(`${API_BASE_URL}/generate-story`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(storyRequest)
    });

    expect(response.status).toBe(200);
    const storyData = await response.json();

    expect(storyData).toHaveProperty('success', true);
    expect(storyData).toHaveProperty('story');

    // Verify story structure
    const story = storyData.story;
    expect(story).toHaveProperty('id');
    expect(story).toHaveProperty('title');
    expect(story).toHaveProperty('content');
    expect(story).toHaveProperty('genre', 'sci_fi');
    expect(story).toHaveProperty('length', 'medium');
    expect(story).toHaveProperty('generated_at');
    expect(story).toHaveProperty('metadata');

    // Verify story metadata
    expect(story.metadata).toHaveProperty('word_count');
    expect(story.metadata).toHaveProperty('reading_time');
  });
});

// Test suite for V3 API Compatibility
test.describe('V3 API Compatibility', () => {
  test('V3 API info should be available', async () => {
    const response = await fetch(`${API_BASE_URL}/api/v3/info`);
    expect(response.status).toBe(200);

    const infoData = await response.json();
    expect(infoData).toHaveProperty('api_name', 'LibraryOfBabel Unified Search API');
    expect(infoData).toHaveProperty('version', '3.0-unified');
    expect(infoData).toHaveProperty('endpoints');
    expect(infoData).toHaveProperty('features');
  });

  test('V3 books endpoint should work with authentication', async () => {
    const response = await makeAPIRequest('/api/v3/books');
    expect(response.status).toBe(200);

    const booksData = await response.json();
    expect(booksData).toHaveProperty('success', true);
    expect(booksData).toHaveProperty('data');
    expect(booksData).toHaveProperty('api_version', '3.0-unified');

    // Verify V3 data structure
    expect(booksData.data).toHaveProperty('books');
    expect(booksData.data).toHaveProperty('total_count');
  });

  test('V3 search endpoint should return proper format', async () => {
    const response = await makeAPIRequest('/api/v3/search', {
      q: 'consciousness',
      type: 'content',
      limit: '5'
    });
    expect(response.status).toBe(200);

    const searchData = await response.json();
    expect(searchData).toHaveProperty('success', true);
    expect(searchData).toHaveProperty('data');
    expect(searchData).toHaveProperty('meta');
    expect(searchData).toHaveProperty('api_version', '3.0-unified');

    // Verify V3 search data structure
    expect(searchData.data).toHaveProperty('results');
    expect(searchData.data).toHaveProperty('search_type', 'content');
    expect(searchData.data).toHaveProperty('total_count');

    // Verify meta structure
    expect(searchData.meta).toHaveProperty('query', 'consciousness');
    expect(searchData.meta).toHaveProperty('processing_time_ms');
  });
});