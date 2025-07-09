import { test, expect } from '@playwright/test';

test.describe('Search Functionality Tests', () => {
  test('should perform basic search', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Wait for page to load
    await expect(page).toHaveTitle(/Library Of Babel/);
    
    // Find search input and button
    const searchInput = page.locator('input[data-testid="search-input"]');
    const searchButton = page.locator('button[data-testid="search-button"]');
    
    // Verify elements are visible
    await expect(searchInput).toBeVisible();
    await expect(searchButton).toBeVisible();
    
    // Type in search query
    await searchInput.fill('artificial intelligence');
    
    // Submit search
    await searchButton.click();
    
    // Wait for results
    await page.waitForSelector('[data-testid="search-results"]', { timeout: 10000 });
    
    // Verify search results appear
    const searchResults = page.locator('[data-testid="search-results"]');
    await expect(searchResults).toBeVisible();
    
    // Check that we have results
    const resultItems = searchResults.locator('div').filter({ hasText: 'by' });
    await expect(resultItems.first()).toBeVisible();
  });

  test('should handle popular search buttons', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Wait for page to load
    await expect(page).toHaveTitle(/Library Of Babel/);
    
    // Find and click a popular search button
    const popularSearchButton = page.locator('button', { hasText: 'AI consciousness' });
    await expect(popularSearchButton).toBeVisible();
    await popularSearchButton.click();
    
    // Verify the search input is filled
    const searchInput = page.locator('input[data-testid="search-input"]');
    await expect(searchInput).toHaveValue('AI consciousness');
    
    // Wait for results
    await page.waitForSelector('[data-testid="search-results"]', { timeout: 10000 });
    
    // Verify search results appear
    const searchResults = page.locator('[data-testid="search-results"]');
    await expect(searchResults).toBeVisible();
  });

  test('should handle "I\'m Feeling Curious" button', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Wait for page to load
    await expect(page).toHaveTitle(/Library Of Babel/);
    
    // Find and click the "I'm Feeling Curious" button
    const curiousButton = page.locator('button', { hasText: 'I\'m Feeling Curious' });
    await expect(curiousButton).toBeVisible();
    await curiousButton.click();
    
    // Verify the search input is filled with something
    const searchInput = page.locator('input[data-testid="search-input"]');
    await expect(searchInput).not.toHaveValue('');
    
    // Wait for results
    await page.waitForSelector('[data-testid="search-results"]', { timeout: 10000 });
    
    // Verify search results appear
    const searchResults = page.locator('[data-testid="search-results"]');
    await expect(searchResults).toBeVisible();
  });

  test('should show loading state during search', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Wait for page to load
    await expect(page).toHaveTitle(/Library Of Babel/);
    
    // Find search elements
    const searchInput = page.locator('input[data-testid="search-input"]');
    const searchButton = page.locator('button[data-testid="search-button"]');
    
    // Type in search query
    await searchInput.fill('consciousness');
    
    // Submit search and immediately check for loading state
    await searchButton.click();
    
    // The button should show loading state briefly
    await expect(searchButton).toBeDisabled();
    
    // Wait for results
    await page.waitForSelector('[data-testid="search-results"]', { timeout: 10000 });
    
    // Button should be enabled again
    await expect(searchButton).toBeEnabled();
  });

  test('should handle empty search gracefully', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Wait for page to load
    await expect(page).toHaveTitle(/Library Of Babel/);
    
    // Find search elements
    const searchInput = page.locator('input[data-testid="search-input"]');
    const searchButton = page.locator('button[data-testid="search-button"]');
    
    // Verify search button is disabled when input is empty
    await expect(searchButton).toBeDisabled();
    
    // Type something and then clear it
    await searchInput.fill('test');
    await searchInput.clear();
    
    // Button should be disabled again
    await expect(searchButton).toBeDisabled();
  });
});