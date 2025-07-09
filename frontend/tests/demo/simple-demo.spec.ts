import { test, expect } from '@playwright/test';

test.describe('LibraryOfBabel Simple Demo', () => {
  test('Show the Google-style homepage', async ({ page }) => {
    console.log('🚀 Opening LibraryOfBabel Google-Style Homepage...');
    
    // Navigate to homepage
    await page.goto('http://localhost:3000');
    
    // Wait for the page to load
    await page.waitForTimeout(2000);
    
    // Take a screenshot so you can see it
    await page.screenshot({ 
      path: 'google-style-homepage.png', 
      fullPage: true 
    });
    
    console.log('📸 Screenshot saved as google-style-homepage.png');
    console.log('🎉 You can now see the Google-style LibraryOfBabel interface!');
    
    // Keep the browser open for 10 seconds so you can see it
    await page.waitForTimeout(10000);
    
    console.log('✅ Demo complete! Check the screenshot to see the beautiful Google-style homepage.');
  });
});