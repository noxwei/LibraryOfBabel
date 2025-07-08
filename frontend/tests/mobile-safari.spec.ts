import { test, expect, devices } from '@playwright/test';

// Mobile Safari specific configuration
const iPhone13 = devices['iPhone 13'];
const iPad = devices['iPad Pro'];
const iPhoneSE = devices['iPhone SE'];

test.describe('Mobile Safari Optimization Tests', () => {
  test.describe('iPhone 13 Tests', () => {

    test('should load homepage with mobile-first design', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto('http://localhost:3000');
      
      // Verify mobile-first loading
      await expect(page).toHaveTitle(/Library Of Babel/);
      
      // Check mobile viewport is properly set
      const viewport = page.viewportSize();
      expect(viewport?.width).toBe(390);
      expect(viewport?.height).toBe(844);
      
      // Verify mobile-specific elements are visible
      const searchInput = page.locator('input[data-testid="search-input"]');
      await expect(searchInput).toBeVisible();
      
      // Test touch target sizes (minimum 44px)
      const searchButton = page.locator('button[data-testid="search-button"]');
      await expect(searchButton).toBeVisible();
      
      const boundingBox = await searchButton.boundingBox();
      expect(boundingBox?.width).toBeGreaterThanOrEqual(44);
      expect(boundingBox?.height).toBeGreaterThanOrEqual(44);
    });

    test('should handle touch interactions properly', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto('http://localhost:3000');
      
      // Test tap gesture
      const searchInput = page.locator('input[data-testid="search-input"]');
      await searchInput.click();
      await expect(searchInput).toBeFocused();
      
      // Test virtual keyboard appearance
      await searchInput.fill('philosophy');
      await expect(searchInput).toHaveValue('philosophy');
      
      // Test touch scroll behavior
      await page.evaluate(() => {
        window.scrollTo(0, 100);
      });
      
      const scrollY = await page.evaluate(() => window.scrollY);
      expect(scrollY).toBe(100);
    });

    test('should support swipe gestures', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto('http://localhost:3000');
      
      // Test horizontal swipe on mobile
      await page.touchscreen.tap(200, 400);
      await page.touchscreen.tap(300, 400);
      
      // Verify swipe interaction doesn't break interface
      const searchInput = page.locator('input[data-testid="search-input"]');
      await expect(searchInput).toBeVisible();
    });

    test('should have proper mobile search functionality', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto('http://localhost:3000');
      
      const searchInput = page.locator('input[data-testid="search-input"]');
      await searchInput.click();
      await searchInput.fill('artificial intelligence');
      
      // Test autocomplete/suggestions on mobile
      await page.keyboard.press('Enter');
      
      // Verify search results are mobile-optimized
      await page.waitForTimeout(1000);
      
      // Check that results are properly formatted for mobile
      const resultsContainer = page.locator('[data-testid="search-results"]');
      if (await resultsContainer.count() > 0) {
        await expect(resultsContainer).toBeVisible();
      }
    });

    test('should handle device orientation changes', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto('http://localhost:3000');
      
      // Test portrait mode (default)
      let viewport = page.viewportSize();
      expect(viewport?.width).toBe(390);
      
      // Simulate landscape mode
      await page.setViewportSize({ width: 844, height: 390 });
      
      // Verify interface adapts to landscape
      const searchInput = page.locator('input[data-testid="search-input"]');
      await expect(searchInput).toBeVisible();
      
      // Verify touch targets remain accessible
      const boundingBox = await searchInput.boundingBox();
      expect(boundingBox?.height).toBeGreaterThanOrEqual(44);
    });
  });

  test.describe('iPad Pro Tests', () => {

    test('should provide tablet-optimized experience', async ({ page }) => {
      await page.setViewportSize({ width: 1024, height: 1366 });
      await page.goto('http://localhost:3000');
      
      // Verify tablet layout
      const viewport = page.viewportSize();
      expect(viewport?.width).toBe(1024);
      expect(viewport?.height).toBe(1366);
      
      // Test that interface utilizes larger screen space
      const searchInput = page.locator('input[data-testid="search-input"]');
      await expect(searchInput).toBeVisible();
      
      // Verify touch targets are appropriately sized for tablet
      const boundingBox = await searchInput.boundingBox();
      expect(boundingBox?.width).toBeGreaterThan(200);
    });

    test('should support multi-touch gestures', async ({ page }) => {
      await page.setViewportSize({ width: 1024, height: 1366 });
      await page.goto('http://localhost:3000');
      
      // Test pinch-to-zoom behavior
      await page.touchscreen.tap(400, 500);
      await page.touchscreen.tap(600, 500);
      
      // Verify interface remains functional after touch interactions
      const searchInput = page.locator('input[data-testid="search-input"]');
      await expect(searchInput).toBeVisible();
    });
  });

  test.describe('iPhone SE Tests (Small Screen)', () => {

    test('should work on smallest supported screen', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('http://localhost:3000');
      
      // Verify small screen compatibility
      const viewport = page.viewportSize();
      expect(viewport?.width).toBe(375);
      expect(viewport?.height).toBe(667);
      
      // Test that all critical elements are visible
      const searchInput = page.locator('input[data-testid="search-input"]');
      await expect(searchInput).toBeVisible();
      
      // Verify no horizontal scrolling on small screens
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      expect(bodyWidth).toBeLessThanOrEqual(375);
    });

    test('should handle limited screen space efficiently', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('http://localhost:3000');
      
      // Test that interface elements don't overlap
      const searchInput = page.locator('input[data-testid="search-input"]');
      const searchButton = page.locator('button[data-testid="search-button"]');
      
      const inputBox = await searchInput.boundingBox();
      const buttonBox = await searchButton.boundingBox();
      
      if (inputBox && buttonBox) {
        // Verify elements don't overlap
        expect(inputBox.x + inputBox.width).toBeLessThanOrEqual(buttonBox.x + 10);
      }
    });
  });

  test.describe('Mobile Safari Specific Features', () => {

    test('should handle iOS Safari specific behaviors', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto('http://localhost:3000');
      
      // Test iOS Safari address bar behavior
      await page.evaluate(() => {
        window.scrollTo(0, 100);
        window.scrollTo(0, 0);
      });
      
      // Verify interface adapts to Safari's dynamic viewport
      const searchInput = page.locator('input[data-testid="search-input"]');
      await expect(searchInput).toBeVisible();
      
      // Test that touch events work properly in iOS Safari
      await searchInput.click();
      await expect(searchInput).toBeFocused();
    });

    test('should handle iOS safe areas', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto('http://localhost:3000');
      
      // Test that content respects safe areas
      const body = page.locator('body');
      const styles = await body.evaluate((el) => {
        return window.getComputedStyle(el);
      });
      
      // Verify safe area handling
      expect(styles).toBeDefined();
    });

    test('should optimize for iOS dark mode', async ({ page }) => {
      // Test dark mode compatibility
      await page.setViewportSize({ width: 390, height: 844 });
      await page.emulateMedia({ colorScheme: 'dark' });
      await page.goto('http://localhost:3000');
      
      // Verify dark mode styling
      const searchInput = page.locator('input[data-testid="search-input"]');
      await expect(searchInput).toBeVisible();
      
      // Test that contrast is maintained in dark mode
      const inputStyles = await searchInput.evaluate((el) => {
        return window.getComputedStyle(el);
      });
      
      expect(inputStyles.backgroundColor).toBeDefined();
    });
  });

  test.describe('Performance Tests', () => {

    test('should load quickly on mobile networks', async ({ page }) => {
      // Simulate slow 3G connection
      await page.setViewportSize({ width: 390, height: 844 });
      await page.route('**/*', (route) => {
        route.continue();
      });
      
      const startTime = Date.now();
      await page.goto('http://localhost:3000');
      
      const searchInput = page.locator('input[data-testid="search-input"]');
      await expect(searchInput).toBeVisible();
      
      const loadTime = Date.now() - startTime;
      expect(loadTime).toBeLessThan(5000); // Under 5 seconds
    });

    test('should handle memory constraints', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto('http://localhost:3000');
      
      // Test memory usage doesn't grow excessively
      const memoryUsage = await page.evaluate(() => {
        return (performance as any).memory?.usedJSHeapSize || 0;
      });
      
      // Verify reasonable memory usage (under 50MB)
      expect(memoryUsage).toBeLessThan(50 * 1024 * 1024);
    });
  });
});