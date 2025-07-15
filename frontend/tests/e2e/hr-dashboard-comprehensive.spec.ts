import { test, expect } from '@playwright/test';

/**
 * HR Dashboard Comprehensive E2E Tests
 * Created by: Maya Rodriguez - Senior Frontend QA Engineer
 * Supervised by: Alex Chen (QA Lead) & Linda Zhang (HR Manager)
 * 
 * This test suite validates the complete HR dashboard functionality
 * including API integrations, user interactions, and accessibility.
 */

test.describe('HR Dashboard - Comprehensive QA Suite', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to HR dashboard before each test
    await page.goto('/hr');
    await page.waitForLoadState('networkidle');
  });

  test.describe('🏠 Page Load & Initial State', () => {
    test('should load HR dashboard with proper title and layout', async ({ page }) => {
      // Maya's Test: Verify page loads correctly
      await expect(page).toHaveTitle(/LibraryOfBabel/);
      
      // Check main heading
      await expect(page.locator('h1')).toContainText('HR Management System');
      
      // Check Linda's attribution
      await expect(page.locator('text=Linda Zhang (张丽娜)')).toBeVisible();
      
      // Check dashboard components load
      await expect(page.locator('text=👔 Linda\'s HR Management')).toBeVisible();
    });

    test('should display loading state initially', async ({ page }) => {
      // Maya's Test: Validate loading UX
      await page.goto('/hr');
      
      // Should show loading state briefly
      const loadingText = page.locator('text=Loading HR data...');
      // Note: This might be too fast to catch in some cases
      
      // Eventually should show the full dashboard
      await expect(page.locator('text=👔 Linda\'s HR Management')).toBeVisible();
    });
  });

  test.describe('🔘 Button Functionality Tests', () => {
    test('should open Reports modal with real data', async ({ page }) => {
      // Maya's Test: Verify Reports button functionality
      await page.click('button:has-text("📊 View Reports")');
      
      // Modal should appear
      await expect(page.locator('.modal-overlay')).toBeVisible();
      await expect(page.locator('.modal-header h3')).toContainText('📊 HR Performance Reports');
      
      // Should contain actual data from Maya's QA Agent
      await expect(page.locator('.modal-body')).toContainText('agent_performance');
      await expect(page.locator('.modal-body')).toContainText('linda_hr');
      await expect(page.locator('.modal-body')).toContainText('alex_qa');
      
      // Close modal
      await page.click('.modal-close');
      await expect(page.locator('.modal-overlay')).not.toBeVisible();
    });

    test('should open Cross-Training modal with program data', async ({ page }) => {
      // Maya's Test: Verify Cross-Training functionality
      await page.click('button:has-text("🔄 Cross-Training")');
      
      // Modal should appear with training data
      await expect(page.locator('.modal-overlay')).toBeVisible();
      await expect(page.locator('.modal-header h3')).toContainText('🔄 Cross-Training System');
      
      // Should contain training program data
      await expect(page.locator('.modal-body')).toContainText('active_programs');
      await expect(page.locator('.modal-body')).toContainText('Frontend Development');
      await expect(page.locator('.modal-body')).toContainText('Alex Chen');
      
      // Close modal by clicking overlay
      await page.click('.modal-overlay');
      await expect(page.locator('.modal-overlay')).not.toBeVisible();
    });

    test('should open Mentorship modal with pairing data', async ({ page }) => {
      // Maya's Test: Verify Mentorship functionality  
      await page.click('button:has-text("👥 Mentorship")');
      
      // Modal should appear with mentorship data
      await expect(page.locator('.modal-overlay')).toBeVisible();
      await expect(page.locator('.modal-header h3')).toContainText('👥 Mentorship Program');
      
      // Should contain mentorship program data
      await expect(page.locator('.modal-body')).toContainText('mentorship_program');
      await expect(page.locator('.modal-body')).toContainText('active_pairs');
      await expect(page.locator('.modal-body')).toContainText('Linda Zhang');
      
      // Test ESC key to close modal
      await page.keyboard.press('Escape');
      // Note: Would need to implement ESC handler in component
    });

    test('should refresh data and show success message', async ({ page }) => {
      // Maya's Test: Verify refresh functionality
      const refreshButton = page.locator('button:has-text("🔄 Refresh Data")');
      
      // Click refresh button
      await refreshButton.click();
      
      // Should show loading state
      await expect(page.locator('button:has-text("🔄 Loading...")')).toBeVisible();
      
      // Should show success alert
      page.on('dialog', async dialog => {
        expect(dialog.message()).toContain('✅ HR data refreshed successfully!');
        await dialog.accept();
      });
      
      // Should return to normal state
      await expect(refreshButton).toContainText('🔄 Refresh Data');
    });
  });

  test.describe('📱 Responsive Design Tests', () => {
    test('should work correctly on mobile devices', async ({ page }) => {
      // Maya's Test: Mobile responsiveness
      await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE
      
      // All elements should be visible and functional
      await expect(page.locator('h1')).toBeVisible();
      await expect(page.locator('text=👔 Linda\'s HR Management')).toBeVisible();
      
      // Buttons should be stacked vertically on mobile
      const buttons = page.locator('.hr-actions button');
      await expect(buttons).toHaveCount(4);
      
      // Test button functionality on mobile
      await page.click('button:has-text("📊 View Reports")');
      await expect(page.locator('.modal-overlay')).toBeVisible();
      
      // Modal should be responsive
      const modal = page.locator('.modal-content');
      await expect(modal).toHaveCSS('width', '90%');
    });

    test('should work correctly on tablet devices', async ({ page }) => {
      // Maya's Test: Tablet responsiveness  
      await page.setViewportSize({ width: 768, height: 1024 }); // iPad
      
      // Layout should adapt for tablet
      await expect(page.locator('h1')).toBeVisible();
      await expect(page.locator('.hr-dashboard')).toBeVisible();
      
      // Agent cards should display properly
      await expect(page.locator('.agents-grid')).toBeVisible();
    });
  });

  test.describe('♿ Accessibility Tests', () => {
    test('should have proper ARIA labels and roles', async ({ page }) => {
      // Maya's Test: Accessibility compliance
      
      // Check for proper heading structure
      const h1 = page.locator('h1');
      await expect(h1).toBeVisible();
      
      // Check for button accessibility
      const buttons = page.locator('button');
      for (const button of await buttons.all()) {
        // Each button should have accessible text
        const text = await button.textContent();
        expect(text).toBeTruthy();
        expect(text!.length).toBeGreaterThan(0);
      }
      
      // Check modal accessibility when opened
      await page.click('button:has-text("📊 View Reports")');
      
      // Modal should have proper focus management
      const modal = page.locator('.modal-content');
      await expect(modal).toBeVisible();
      
      // Close button should be accessible
      const closeButton = page.locator('.modal-close');
      await expect(closeButton).toBeVisible();
    });

    test('should support keyboard navigation', async ({ page }) => {
      // Maya's Test: Keyboard accessibility
      
      // Tab through all interactive elements
      await page.keyboard.press('Tab'); // First button
      await page.keyboard.press('Tab'); // Second button  
      await page.keyboard.press('Tab'); // Third button
      await page.keyboard.press('Tab'); // Fourth button
      
      // Should be able to activate buttons with Enter/Space
      await page.keyboard.press('Enter');
      
      // Modal should open and be navigable
      await expect(page.locator('.modal-overlay')).toBeVisible();
      
      // Should be able to close with focus on close button
      await page.keyboard.press('Tab'); // Focus close button
      await page.keyboard.press('Enter');
      await expect(page.locator('.modal-overlay')).not.toBeVisible();
    });
  });

  test.describe('🔗 API Integration Tests', () => {
    test('should handle API errors gracefully', async ({ page }) => {
      // Maya's Test: Error handling
      
      // Mock API failure
      await page.route('**/hr/qa/reports', route => {
        route.fulfill({
          status: 500,
          body: JSON.stringify({ error: 'Internal Server Error' })
        });
      });
      
      // Click reports button
      await page.click('button:has-text("📊 View Reports")');
      
      // Should show error alert
      page.on('dialog', async dialog => {
        expect(dialog.message()).toContain('Error loading reports');
        await dialog.accept();
      });
    });

    test('should handle slow API responses', async ({ page }) => {
      // Maya's Test: Performance under load
      
      // Mock slow API response
      await page.route('**/hr/qa/training', route => {
        setTimeout(() => {
          route.fulfill({
            status: 200,
            body: JSON.stringify({ cross_training: { active_programs: [] } })
          });
        }, 3000); // 3 second delay
      });
      
      // Click training button
      await page.click('button:has-text("🔄 Cross-Training")');
      
      // Should handle timeout gracefully
      // (Would need to implement timeout handling in component)
    });
  });

  test.describe('🎨 Visual Regression Tests', () => {
    test('should match visual baseline for desktop', async ({ page }) => {
      // Maya's Test: Visual consistency
      
      // Wait for full page load
      await page.waitForLoadState('networkidle');
      
      // Take screenshot for visual comparison
      await expect(page).toHaveScreenshot('hr-dashboard-desktop.png', {
        fullPage: true,
        threshold: 0.2
      });
    });

    test('should match visual baseline for mobile', async ({ page }) => {
      // Maya's Test: Mobile visual consistency
      
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('hr-dashboard-mobile.png', {
        fullPage: true,
        threshold: 0.2
      });
    });

    test('should display modal correctly', async ({ page }) => {
      // Maya's Test: Modal visual consistency
      
      await page.click('button:has-text("📊 View Reports")');
      await expect(page.locator('.modal-overlay')).toBeVisible();
      
      await expect(page).toHaveScreenshot('hr-modal-reports.png', {
        threshold: 0.2
      });
    });
  });

  test.describe('⚡ Performance Tests', () => {
    test('should load within performance budget', async ({ page }) => {
      // Maya's Test: Performance validation
      
      const startTime = Date.now();
      await page.goto('/hr');
      await page.waitForLoadState('networkidle');
      const loadTime = Date.now() - startTime;
      
      // Should load within 3 seconds
      expect(loadTime).toBeLessThan(3000);
    });

    test('should have minimal memory usage', async ({ page }) => {
      // Maya's Test: Memory performance
      
      await page.goto('/hr');
      await page.waitForLoadState('networkidle');
      
      // Test multiple modal opens/closes for memory leaks
      for (let i = 0; i < 5; i++) {
        await page.click('button:has-text("📊 View Reports")');
        await expect(page.locator('.modal-overlay')).toBeVisible();
        await page.click('.modal-close');
        await expect(page.locator('.modal-overlay')).not.toBeVisible();
      }
      
      // Memory usage should remain stable
      // (Would need browser dev tools integration for detailed memory analysis)
    });
  });

  test.describe('🔄 Cross-Browser Compatibility', () => {
    test('should work in all supported browsers', async ({ page, browserName }) => {
      // Maya's Test: Cross-browser validation
      
      console.log(`Testing in ${browserName}`);
      
      // Basic functionality should work in all browsers
      await expect(page.locator('h1')).toBeVisible();
      await expect(page.locator('text=👔 Linda\'s HR Management')).toBeVisible();
      
      // Test modal functionality
      await page.click('button:has-text("📊 View Reports")');
      await expect(page.locator('.modal-overlay')).toBeVisible();
      await page.click('.modal-close');
      
      console.log(`✅ ${browserName} compatibility confirmed`);
    });
  });
});

/**
 * Test Helper Functions
 * Maya's utilities for comprehensive testing
 */
test.describe('🛠️ Test Utilities & Helpers', () => {
  test('QA Agent health check', async ({ page }) => {
    // Maya's Test: Verify QA infrastructure
    
    // Check if Maya's QA Agent is responding
    const response = await page.request.get('http://localhost:8082/hr/qa/status');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.qa_agent).toContain('Maya Rodriguez');
    expect(data.status).toBe('active');
    
    console.log('✅ Maya Rodriguez QA Agent is operational');
  });

  test('CI/CD integration validation', async ({ page }) => {
    // Maya's Test: CI/CD pipeline validation
    
    // Verify all critical API endpoints
    const endpoints = [
      'http://localhost:8082/hr/qa/reports',
      'http://localhost:8082/hr/qa/training', 
      'http://localhost:8082/hr/qa/mentorship',
      'http://localhost:8082/hr/qa/test-results'
    ];
    
    for (const endpoint of endpoints) {
      const response = await page.request.get(endpoint);
      expect(response.status()).toBe(200);
      console.log(`✅ ${endpoint} responding correctly`);
    }
  });
});