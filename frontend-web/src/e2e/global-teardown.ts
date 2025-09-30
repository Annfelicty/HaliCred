/**
 * Global teardown for E2E tests.
 * Handles cleanup and environment restoration.
 */

import { chromium, FullConfig } from '@playwright/test';
import { promises as fs } from 'fs';
import path from 'path';

async function globalTeardown(config: FullConfig) {
  console.log('🧹 Starting E2E test environment cleanup...');

  try {
    // Clean up test data
    await cleanupTestData();

    // Clean up authentication files
    await cleanupAuthFiles();

    // Generate test report summary
    await generateTestSummary();

    console.log('✅ E2E test environment cleanup completed');

  } catch (error) {
    console.error('❌ E2E teardown failed:', error);
    // Don't fail the build on teardown errors
  }
}

async function cleanupTestData() {
  console.log('🗑️  Cleaning up test data...');

  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Clean up via API if available
    await page.request.post('/api/test/cleanup', {
      data: {
        action: 'cleanup_test_data',
      },
    });
  } catch (error) {
    console.warn('⚠️  Could not clean up test data via API');
  } finally {
    await context.close();
    await browser.close();
  }

  console.log('✅ Test data cleanup completed');
}

async function cleanupAuthFiles() {
  console.log('🗑️  Cleaning up authentication files...');

  const authFiles = [
    'test-results/test-user-1-auth.json',
    'test-results/test-user-2-auth.json',
  ];

  for (const file of authFiles) {
    try {
      await fs.unlink(file);
      console.log(`✅ Removed ${file}`);
    } catch (error) {
      // File might not exist, which is OK
    }
  }

  console.log('✅ Authentication files cleanup completed');
}

async function generateTestSummary() {
  console.log('📊 Generating test summary...');

  try {
    const resultsDir = 'test-results';
    const summaryFile = path.join(resultsDir, 'e2e-summary.json');

    // Ensure results directory exists
    await fs.mkdir(resultsDir, { recursive: true });

    // Create basic summary
    const summary = {
      timestamp: new Date().toISOString(),
      environment: process.env.NODE_ENV || 'development',
      buildNumber: process.env.BUILD_NUMBER || 'local',
      commitHash: process.env.COMMIT_HASH || 'unknown',
      testRun: {
        completed: true,
        duration: Date.now(), // This would be calculated properly in real implementation
      },
    };

    // Try to read existing test results
    try {
      const resultsFile = path.join(resultsDir, 'e2e-results.json');
      const resultsData = await fs.readFile(resultsFile, 'utf-8');
      const results = JSON.parse(resultsData);

      summary.testRun = {
        ...summary.testRun,
        total: results.stats?.total || 0,
        passed: results.stats?.passed || 0,
        failed: results.stats?.failed || 0,
        skipped: results.stats?.skipped || 0,
      };
    } catch (error) {
      console.warn('⚠️  Could not read test results for summary');
    }

    await fs.writeFile(summaryFile, JSON.stringify(summary, null, 2));
    console.log(`✅ Test summary generated: ${summaryFile}`);

  } catch (error) {
    console.warn('⚠️  Could not generate test summary:', error.message);
  }
}

export default globalTeardown;