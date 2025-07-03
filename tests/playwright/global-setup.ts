/**
 * Playwright Global Setup for Library of Babel Testing
 * 
 * Ensures the complete system is ready for automated testing
 */

import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('🎭 Setting up Library of Babel test environment...\n');
  
  // Wait for backend to be ready
  console.log('🔧 Checking backend availability...');
  const maxRetries = 30;
  let backendReady = false;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch('http://localhost:5570/api/health');
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'healthy') {
          backendReady = true;
          console.log('✅ Library of Babel backend is operational');
          break;
        }
      }
    } catch (error) {
      // Backend not ready yet
    }
    
    console.log(`⏳ Waiting for backend... (${i + 1}/${maxRetries})`);
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  
  if (!backendReady) {
    throw new Error('❌ Backend failed to start. Please ensure babel-backend is running.');
  }
  
  // Wait for frontend to be ready
  console.log('🎨 Checking frontend availability...');
  let frontendReady = false;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch('http://localhost:3000');
      if (response.ok) {
        frontendReady = true;
        console.log('✅ Borgesian frontend is operational');
        break;
      }
    } catch (error) {
      // Frontend not ready yet
    }
    
    console.log(`⏳ Waiting for frontend... (${i + 1}/${maxRetries})`);
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  
  if (!frontendReady) {
    throw new Error('❌ Frontend failed to start. Please ensure frontend is running.');
  }
  
  // Perform system health check
  console.log('🏥 Performing system health check...');
  
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  try {
    // Test basic navigation
    await page.goto('http://localhost:3000');
    await page.waitForSelector('[data-testid="library-title"], h1', { timeout: 10000 });
    
    // Test backend API
    const apiResponse = await fetch('http://localhost:5570/api/library/info');
    const apiData = await apiResponse.json();
    
    if (!apiData.features?.proceduralGeneration) {
      throw new Error('Backend API not responding correctly');
    }
    
    console.log('✅ System health check passed');
    console.log(`📚 Library Mode: ${apiData.mode}`);
    console.log(`🎯 Max Books: ${apiData.statistics?.maxBooks || 'Infinite'}`);
    console.log(`📖 Available Concepts: ${apiData.statistics?.availableConcepts || 'Unknown'}`);
    
  } catch (error) {
    console.error('❌ System health check failed:', error);
    throw error;
  } finally {
    await browser.close();
  }
  
  // Create test directories
  const fs = require('fs');
  const testDirs = [
    'tests/screenshots',
    'tests/test-results',
    'tests/playwright-report'
  ];
  
  for (const dir of testDirs) {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
      console.log(`📁 Created test directory: ${dir}`);
    }
  }
  
  console.log('\n🎊 Library of Babel test environment is ready!');
  console.log('🏛️ Backend: http://localhost:5570');
  console.log('🎭 Frontend: http://localhost:3000');
  console.log('🎯 Ready for infinite exploration testing!\n');
}

export default globalSetup;