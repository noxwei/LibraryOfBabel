/**
 * Playwright Configuration for Library of Babel Testing
 * 
 * Automated testing configuration for the complete Borgesian system
 */

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/playwright',
  
  /* Run tests in files in parallel */
  fullyParallel: true,
  
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  
  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 1 : undefined,
  
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: [
    ['html', { outputFolder: 'tests/playwright-report' }],
    ['json', { outputFile: 'tests/playwright-results.json' }],
    ['list']
  ],
  
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: 'http://localhost:3000',
    
    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: 'on-first-retry',
    
    /* Take screenshot on failure */
    screenshot: 'only-on-failure',
    
    /* Record video on failure */
    video: 'retain-on-failure',
    
    /* Global timeout for actions */
    actionTimeout: 15000,
    
    /* Global timeout for navigation */
    navigationTimeout: 30000,
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    /* Test against mobile viewports. */
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },

    /* Test against branded browsers. */
    {
      name: 'Microsoft Edge',
      use: { ...devices['Desktop Edge'], channel: 'msedge' },
    },
    {
      name: 'Google Chrome',
      use: { ...devices['Desktop Chrome'], channel: 'chrome' },
    },
  ],

  /* Run your local dev server before starting the tests */
  webServer: [
    {
      command: 'cd babel-backend && npm start',
      port: 5570,
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
      env: {
        LIBRARY_MODE: 'educational',
        DEBUG_MODE: 'true'
      }
    },
    {
      command: 'cd frontend && npm start',
      port: 3000,
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
    }
  ],

  /* Global setup and teardown */
  globalSetup: './tests/playwright/global-setup.ts',
  globalTeardown: './tests/playwright/global-teardown.ts',

  /* Test timeout */
  timeout: 60000,

  /* Expect timeout */
  expect: {
    timeout: 10000,
  },
  
  /* Folder for test artifacts such as screenshots, videos, traces, etc. */
  outputDir: 'tests/test-results/',
});