/**
 * Global setup for E2E tests.
 * Handles test environment preparation and authentication setup.
 */

import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting E2E test environment setup...');

  const baseURL = config.projects[0].use.baseURL || 'http://localhost:5173';

  // Launch browser for setup
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Wait for the application to be ready
    console.log('⏳ Waiting for application to be ready...');
    await page.goto(baseURL);
    await page.waitForSelector('[data-testid="app-ready"]', { timeout: 30000 });
    console.log('✅ Application is ready');

    // Setup test data if needed
    await setupTestData(page);

    // Authenticate test users
    await authenticateTestUsers(page);

    console.log('✅ E2E test environment setup completed');

  } catch (error) {
    console.error('❌ E2E setup failed:', error);
    throw error;
  } finally {
    await context.close();
    await browser.close();
  }
}

async function setupTestData(page: any) {
  console.log('📊 Setting up test data...');

  // Check if running against local development server
  const url = page.url();
  if (url.includes('localhost') || url.includes('127.0.0.1')) {
    // Reset database state for clean tests
    await page.evaluate(() => {
      // Clear localStorage
      localStorage.clear();
      sessionStorage.clear();
    });
  }

  // Create test users via API if needed
  try {
    await page.request.post('/api/test/setup', {
      data: {
        action: 'create_test_users',
        users: [
          {
            phone: '+254700000001',
            name: 'Test User 1',
            business_name: 'Test Business 1',
            business_type: 'farmer',
            green_score: 75,
          },
          {
            phone: '+254700000002',
            name: 'Test User 2',
            business_name: 'Test Business 2',
            business_type: 'salon',
            green_score: 85,
          },
        ],
      },
    });
  } catch (error) {
    console.warn('⚠️  Could not set up test data via API (this is OK for mock environments)');
  }

  console.log('✅ Test data setup completed');
}

async function authenticateTestUsers(page: any) {
  console.log('🔐 Setting up authentication for test users...');

  const testUsers = [
    {
      phone: '+254700000001',
      name: 'Test User 1',
      storageFile: 'test-user-1-auth.json',
    },
    {
      phone: '+254700000002',
      name: 'Test User 2',
      storageFile: 'test-user-2-auth.json',
    },
  ];

  for (const user of testUsers) {
    try {
      // Navigate to login page
      await page.goto('/auth/login');

      // Enter phone number
      await page.fill('[data-testid="phone-input"]', user.phone);
      await page.click('[data-testid="send-otp-button"]');

      // Wait for OTP input
      await page.waitForSelector('[data-testid="otp-input"]');

      // In test environment, use a fixed OTP
      await page.fill('[data-testid="otp-input"]', '123456');
      await page.click('[data-testid="verify-otp-button"]');

      // Wait for successful authentication
      await page.waitForSelector('[data-testid="dashboard"]', { timeout: 10000 });

      // Save authentication state
      await page.context().storageState({ path: `test-results/${user.storageFile}` });

      console.log(`✅ Authentication setup completed for ${user.name}`);

    } catch (error) {
      console.warn(`⚠️  Could not authenticate ${user.name}:`, error.message);
      // Continue with other users
    }
  }

  console.log('✅ User authentication setup completed');
}

export default globalSetup;