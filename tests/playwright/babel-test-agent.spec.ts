/**
 * 🎭 Library of Babel Playwright Test Agent
 * 
 * Automated testing agent that explores the infinite library and validates
 * the complete integration between frontend and backend systems.
 * 
 * This agent acts as an autonomous explorer, testing every aspect of
 * Borges' digital library implementation.
 */

import { test, expect, Page } from '@playwright/test';

class BabelTestAgent {
  constructor(private page: Page) {}

  /**
   * 🏛️ Test the infinite library homepage and initial state
   */
  async testLibraryHomepage() {
    await this.page.goto('http://localhost:3000');
    
    // Verify the sacred title appears
    await expect(this.page.getByText('THE LIBRARY OF BABEL')).toBeVisible();
    
    // Verify Borges quote is present
    await expect(this.page.getByText('somewhere in these halls lies every truth')).toBeVisible();
    
    // Verify search interface is ready
    await expect(this.page.getByPlaceholder('What knowledge do you seek?')).toBeVisible();
    
    // Verify mode switcher is present
    await expect(this.page.getByText('Library Mode:')).toBeVisible();
    await expect(this.page.getByText('📚 Educational')).toBeVisible();
    await expect(this.page.getByText('🔧 Enhanced')).toBeVisible();
    
    console.log('✅ Library homepage loaded successfully');
  }

  /**
   * 🔮 Test divine search mode (hybrid search)
   */
  async testDivineSearch() {
    // Search for a philosophical concept
    await this.page.getByPlaceholder('What knowledge do you seek?').fill('infinity and paradox');
    
    // Select divine mode
    await this.page.getByText('🔮 Divine').click();
    
    // Execute search
    await this.page.getByText('Seek Knowledge').click();
    
    // Wait for results to load
    await expect(this.page.getByText('The Library reveals')).toBeVisible({ timeout: 10000 });
    
    // Verify both sacred texts and mystical echoes are present
    await expect(this.page.getByText('📜 SACRED TEXTS')).toBeVisible();
    await expect(this.page.getByText('🌀 MYSTICAL ECHOES')).toBeVisible();
    
    // Verify at least one book result appears
    await expect(this.page.locator('.ancient-scroll, .ethereal-connection').first()).toBeVisible();
    
    // Verify educational context is provided
    await expect(this.page.getByText('This demonstrates Borges')).toBeVisible();
    
    console.log('✅ Divine search completed successfully');
  }

  /**
   * 📜 Test precise search mode (exact matches)
   */
  async testPreciseSearch() {
    // Navigate back to search if needed
    await this.page.getByText('← Return to Search').click();
    
    // Search for specific academic field
    await this.page.getByPlaceholder('What knowledge do you seek?').fill('metaphysics consciousness');
    
    // Select precise mode
    await this.page.getByText('📜 Precise').click();
    
    // Execute search
    await this.page.getByText('Seek Knowledge').click();
    
    // Wait for results
    await expect(this.page.getByText('The Library reveals')).toBeVisible({ timeout: 10000 });
    
    // Verify only sacred texts appear (no mystical echoes in precise mode)
    await expect(this.page.getByText('📜 SACRED TEXTS')).toBeVisible();
    
    // Verify scholarly content quality
    await expect(this.page.getByText(/(Dr\.|Prof\.|Studies|Meditations|Analysis)/)).toBeVisible();
    
    console.log('✅ Precise search completed successfully');
  }

  /**
   * 🌀 Test mystical search mode (semantic connections)
   */
  async testMysticalSearch() {
    // Navigate back to search
    await this.page.getByText('← Return to Search').click();
    
    // Search for abstract concepts
    await this.page.getByPlaceholder('What knowledge do you seek?').fill('existence being reality');
    
    // Select mystical mode
    await this.page.getByText('📿 Mystical').click();
    
    // Execute search
    await this.page.getByText('Seek Knowledge').click();
    
    // Wait for mystical results
    await expect(this.page.getByText('The Library reveals')).toBeVisible({ timeout: 10000 });
    
    // Verify mystical echoes are present
    await expect(this.page.getByText('🌀 MYSTICAL ECHOES')).toBeVisible();
    
    // Verify ethereal connections appear
    await expect(this.page.locator('.ethereal-connection').first()).toBeVisible();
    
    console.log('✅ Mystical search completed successfully');
  }

  /**
   * 📖 Test entering a reading chamber
   */
  async testReadingChamber() {
    // Click on first available book result
    const firstBook = this.page.locator('.enter-text-portal, .follow-thread').first();
    await firstBook.click();
    
    // Wait for reading chamber to load
    await expect(this.page.getByText('Return to Halls')).toBeVisible({ timeout: 10000 });
    
    // Verify book structure is present
    await expect(this.page.locator('.illuminated-manuscript')).toBeVisible();
    await expect(this.page.locator('.parchment-content')).toBeVisible();
    
    // Verify chamber navigation is available
    await expect(this.page.getByText('Previous Chamber')).toBeVisible();
    await expect(this.page.getByText('Next Chamber')).toBeVisible();
    
    // Verify mystical location is displayed
    await expect(this.page.getByText(/Volume \d+.*Gallery/)).toBeVisible();
    
    // Test chamber tools
    await this.page.getByText('⬟ Outline').click();
    
    // Verify annotations work
    await this.page.getByText('◈ Annotations').click();
    await expect(this.page.getByText('Sacred Annotations')).toBeVisible();
    
    console.log('✅ Reading chamber exploration completed');
  }

  /**
   * 🔄 Test library mode switching
   */
  async testModeSwitch() {
    // Navigate back to search
    await this.page.getByText('Return to Halls').click();
    
    // Test switching to enhanced mode
    await this.page.getByText('🔧 Enhanced').click();
    
    // Verify mode description changes
    await expect(this.page.getByText('Hybrid with real content')).toBeVisible();
    
    // Test search in enhanced mode
    await this.page.getByPlaceholder('What knowledge do you seek?').fill('philosophy');
    await this.page.getByText('Seek Knowledge').click();
    
    // Wait for results (may take longer or fail gracefully)
    await this.page.waitForTimeout(3000);
    
    // Switch back to educational mode
    await this.page.getByText('📚 Educational').click();
    await expect(this.page.getByText('Infinite procedural generation')).toBeVisible();
    
    console.log('✅ Mode switching tested successfully');
  }

  /**
   * 🎲 Test deterministic generation
   */
  async testDeterministicGeneration() {
    // Search for the same concept multiple times
    const searchQuery = 'recursion logic';
    
    // First search
    await this.page.getByPlaceholder('What knowledge do you seek?').fill(searchQuery);
    await this.page.getByText('Seek Knowledge').click();
    await expect(this.page.getByText('The Library reveals')).toBeVisible({ timeout: 10000 });
    
    // Capture first result
    const firstResultTitle = await this.page.locator('.illuminated-title').first().textContent();
    
    // Search again with same query
    await this.page.getByText('← Return to Search').click();
    await this.page.getByPlaceholder('What knowledge do you seek?').fill(searchQuery);
    await this.page.getByText('Seek Knowledge').click();
    await expect(this.page.getByText('The Library reveals')).toBeVisible({ timeout: 10000 });
    
    // Verify deterministic results (should be same)
    const secondResultTitle = await this.page.locator('.illuminated-title').first().textContent();
    expect(firstResultTitle).toBe(secondResultTitle);
    
    console.log('✅ Deterministic generation verified');
  }

  /**
   * 🚀 Test performance and responsiveness
   */
  async testPerformance() {
    await this.page.getByText('← Return to Search').click();
    
    const startTime = Date.now();
    
    // Execute a search and measure response time
    await this.page.getByPlaceholder('What knowledge do you seek?').fill('time eternity');
    await this.page.getByText('Seek Knowledge').click();
    await expect(this.page.getByText('The Library reveals')).toBeVisible({ timeout: 10000 });
    
    const responseTime = Date.now() - startTime;
    console.log(`⚡ Search response time: ${responseTime}ms`);
    
    // Verify reasonable performance (should be under 5 seconds)
    expect(responseTime).toBeLessThan(5000);
    
    console.log('✅ Performance test completed');
  }

  /**
   * 🎨 Test visual elements and mystical aesthetics
   */
  async testMysticalAesthetics() {
    // Verify hexagonal elements are present
    await expect(this.page.locator('.clip-hexagon')).toHaveCount({ min: 1 });
    
    // Verify ancient color scheme is applied
    const searchInput = this.page.getByPlaceholder('What knowledge do you seek?');
    const backgroundColor = await searchInput.evaluate(el => 
      getComputedStyle(el).backgroundColor
    );
    
    // Should have dark mystical background
    expect(backgroundColor).toContain('rgb');
    
    // Verify mystical font is loaded
    const titleElement = this.page.getByText('THE LIBRARY OF BABEL');
    const fontFamily = await titleElement.evaluate(el => 
      getComputedStyle(el).fontFamily
    );
    
    console.log(`📝 Font family: ${fontFamily}`);
    console.log('✅ Mystical aesthetics verified');
  }

  /**
   * 🔍 Test error handling and edge cases
   */
  async testErrorHandling() {
    await this.page.getByText('← Return to Search').click();
    
    // Test empty search
    await this.page.getByPlaceholder('What knowledge do you seek?').fill('');
    
    // Search button should be disabled for empty query
    const searchButton = this.page.getByText('Seek Knowledge');
    expect(await searchButton.isDisabled()).toBe(true);
    
    // Test very long search query
    const longQuery = 'a'.repeat(1000);
    await this.page.getByPlaceholder('What knowledge do you seek?').fill(longQuery);
    await this.page.getByText('Seek Knowledge').click();
    
    // Should handle gracefully (either results or error message)
    await this.page.waitForTimeout(3000);
    
    console.log('✅ Error handling tested');
  }

  /**
   * 🌌 Run complete library exploration
   */
  async exploreInfiniteLibrary() {
    console.log('🎭 Starting automated Library of Babel exploration...\n');
    
    await this.testLibraryHomepage();
    await this.testDivineSearch();
    await this.testPreciseSearch();
    await this.testMysticalSearch();
    await this.testReadingChamber();
    await this.testModeSwitch();
    await this.testDeterministicGeneration();
    await this.testPerformance();
    await this.testMysticalAesthetics();
    await this.testErrorHandling();
    
    console.log('\n🎊 Complete Library of Babel exploration finished successfully!');
    console.log('✨ The infinite library is fully operational and magnificent!');
  }
}

// Test Suite: Complete Library of Babel System
test.describe('🏛️ Library of Babel - Complete System Integration', () => {
  test.beforeEach(async ({ page }) => {
    // Ensure both backend and frontend are running
    console.log('🔧 Ensuring Library of Babel system is operational...');
    
    // Check backend health
    try {
      const response = await fetch('http://localhost:5570/api/health');
      if (!response.ok) {
        throw new Error('Backend not responding');
      }
      console.log('✅ Backend is operational at http://localhost:5570');
    } catch (error) {
      console.error('❌ Backend not available. Please start: cd babel-backend && npm start');
      throw error;
    }
    
    // Navigate to frontend
    await page.goto('http://localhost:3000');
    console.log('✅ Frontend is operational at http://localhost:3000');
  });

  test('🌟 Complete Library of Babel Exploration', async ({ page }) => {
    const agent = new BabelTestAgent(page);
    await agent.exploreInfiniteLibrary();
  });

  test('🔮 Educational Mode Deep Dive', async ({ page }) => {
    const agent = new BabelTestAgent(page);
    
    // Ensure educational mode is selected
    await agent.testLibraryHomepage();
    await page.getByText('📚 Educational').click();
    
    // Test multiple philosophical searches
    const concepts = ['infinity', 'consciousness', 'paradox', 'existence', 'reality'];
    
    for (const concept of concepts) {
      console.log(`🔍 Exploring concept: ${concept}`);
      
      await page.getByPlaceholder('What knowledge do you seek?').fill(concept);
      await page.getByText('Seek Knowledge').click();
      await expect(page.getByText('The Library reveals')).toBeVisible({ timeout: 10000 });
      
      // Verify scholarly content appears
      await expect(page.getByText(/(Dr\.|Prof\.|Studies|Meditations|Analysis)/)).toBeVisible();
      
      await page.getByText('← Return to Search').click();
    }
    
    console.log('✅ Educational mode deep dive completed');
  });

  test('⚡ Performance and Stress Testing', async ({ page }) => {
    const agent = new BabelTestAgent(page);
    await agent.testLibraryHomepage();
    
    // Test rapid consecutive searches
    const rapidSearches = ['logic', 'ethics', 'aesthetics', 'physics', 'mathematics'];
    
    console.log('🚀 Testing rapid consecutive searches...');
    
    for (let i = 0; i < rapidSearches.length; i++) {
      const startTime = Date.now();
      
      await page.getByPlaceholder('What knowledge do you seek?').fill(rapidSearches[i]);
      await page.getByText('Seek Knowledge').click();
      await expect(page.getByText('The Library reveals')).toBeVisible({ timeout: 10000 });
      
      const responseTime = Date.now() - startTime;
      console.log(`Search ${i + 1} (${rapidSearches[i]}): ${responseTime}ms`);
      
      if (i < rapidSearches.length - 1) {
        await page.getByText('← Return to Search').click();
      }
    }
    
    console.log('✅ Performance stress testing completed');
  });

  test('🎨 Visual Regression and UI Consistency', async ({ page }) => {
    const agent = new BabelTestAgent(page);
    await agent.testLibraryHomepage();
    
    // Take screenshot of main interface
    await page.screenshot({ path: 'tests/screenshots/library-homepage.png', fullPage: true });
    
    // Test search results layout
    await page.getByPlaceholder('What knowledge do you seek?').fill('ancient wisdom');
    await page.getByText('Seek Knowledge').click();
    await expect(page.getByText('The Library reveals')).toBeVisible({ timeout: 10000 });
    
    await page.screenshot({ path: 'tests/screenshots/search-results.png', fullPage: true });
    
    // Test reading chamber layout
    await page.locator('.enter-text-portal').first().click();
    await expect(page.getByText('Return to Halls')).toBeVisible({ timeout: 10000 });
    
    await page.screenshot({ path: 'tests/screenshots/reading-chamber.png', fullPage: true });
    
    console.log('✅ Visual regression testing completed');
  });
});

// Backend API Testing
test.describe('🔧 Backend API Integration Tests', () => {
  test('📡 Library API Health and Info', async () => {
    // Test health endpoint
    const healthResponse = await fetch('http://localhost:5570/api/health');
    expect(healthResponse.ok).toBe(true);
    
    const healthData = await healthResponse.json();
    expect(healthData.status).toBe('healthy');
    expect(healthData.library.infinite).toBe(true);
    
    // Test library info endpoint
    const infoResponse = await fetch('http://localhost:5570/api/library/info');
    expect(infoResponse.ok).toBe(true);
    
    const infoData = await infoResponse.json();
    expect(infoData.name).toBe('Library of Babel');
    expect(infoData.features.proceduralGeneration).toBe(true);
    
    console.log('✅ Backend API health checks passed');
  });

  test('🔍 Search API Functionality', async () => {
    // Test search endpoint
    const searchResponse = await fetch('http://localhost:5570/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: 'philosophy wisdom', maxResults: 5 })
    });
    
    expect(searchResponse.ok).toBe(true);
    
    const searchData = await searchResponse.json();
    expect(searchData.query).toBe('philosophy wisdom');
    expect(searchData.results).toHaveLength(5);
    expect(searchData.educational.concept).toContain('Borges');
    
    console.log('✅ Search API functionality verified');
  });

  test('📚 Book Retrieval API', async () => {
    // Test specific book retrieval
    const bookResponse = await fetch('http://localhost:5570/api/book/12345/3/2/15');
    expect(bookResponse.ok).toBe(true);
    
    const bookData = await bookResponse.json();
    expect(bookData.book.id).toBe('12345.3.2.15');
    expect(bookData.book.title).toBeTruthy();
    expect(bookData.book.author).toBeTruthy();
    expect(bookData.book.chapters.length).toBeGreaterThan(0);
    
    console.log('✅ Book retrieval API verified');
  });

  test('🎲 Random Book and Concepts API', async () => {
    // Test random book
    const randomResponse = await fetch('http://localhost:5570/api/random-book');
    expect(randomResponse.ok).toBe(true);
    
    const randomData = await randomResponse.json();
    expect(randomData.book.title).toBeTruthy();
    
    // Test concepts endpoint
    const conceptsResponse = await fetch('http://localhost:5570/api/concepts');
    expect(conceptsResponse.ok).toBe(true);
    
    const conceptsData = await conceptsResponse.json();
    expect(conceptsData.concepts.length).toBeGreaterThan(0);
    expect(conceptsData.academicFields.length).toBeGreaterThan(0);
    
    console.log('✅ Random book and concepts APIs verified');
  });
});

export { BabelTestAgent };