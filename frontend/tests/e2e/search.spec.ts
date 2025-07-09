import { test, expect } from '@playwright/test';

test.describe('LibraryOfBabel Search Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display search interface on homepage', async ({ page }) => {
    // Check that the main search input is visible
    await expect(page.locator('[data-testid="search-input"]')).toBeVisible();
    
    // Check for search button
    await expect(page.locator('[data-testid="search-button"]')).toBeVisible();
    
    // Check page title
    await expect(page).toHaveTitle(/LibraryOfBabel/);
  });

  test('should perform basic book search', async ({ page }) => {
    // Enter search query
    await page.fill('[data-testid="search-input"]', 'consciousness ethics philosophy');
    
    // Click search button
    await page.click('[data-testid="search-button"]');
    
    // Wait for results to load
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
    
    // Check that results are displayed
    await expect(page.locator('[data-testid="result-item"]').first()).toBeVisible();
  });

  test('should handle empty search gracefully', async ({ page }) => {
    // Click search without entering text
    await page.click('[data-testid="search-button"]');
    
    // Should show appropriate message or prevent search
    // This will be implemented based on UX decisions
  });

  test('should handle very long search queries', async ({ page }) => {
    const longQuery = 'consciousness ethics philosophy artificial intelligence machine learning deep learning neural networks cognitive science psychology neuroscience phenomenology existentialism poststructuralism critical theory social theory political philosophy economic theory'.repeat(3);
    
    await page.fill('[data-testid="search-input"]', longQuery);
    await page.click('[data-testid="search-button"]');
    
    // Should handle gracefully without crashing
    await expect(page.locator('[data-testid="search-input"]')).toBeVisible();
  });

  test('should support semantic search', async ({ page }) => {
    // Test semantic search capabilities
    await page.fill('[data-testid="search-input"]', 'books about AI consciousness and ethics');
    await page.click('[data-testid="search-button"]');
    
    // Wait for semantic search results
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
    
    // Check for semantic search indicator
    await expect(page.locator('[data-testid="semantic-search-indicator"]')).toBeVisible();
  });

  test('should display search loading state', async ({ page }) => {
    // Start search
    await page.fill('[data-testid="search-input"]', 'philosophy');
    await page.click('[data-testid="search-button"]');
    
    // Should show loading indicator briefly
    await expect(page.locator('[data-testid="search-loading"]')).toBeVisible();
  });
});