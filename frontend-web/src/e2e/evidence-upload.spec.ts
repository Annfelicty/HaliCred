/**
 * E2E tests for evidence upload and green score calculation.
 * Tests the complete workflow from evidence upload to score updates.
 */

import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Evidence Upload Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Use pre-authenticated state
    await page.goto('/dashboard', {
      storageState: 'test-results/test-user-1-auth.json'
    });
  });

  test.describe('Evidence Upload Interface', () => {
    test('should access evidence upload section', async ({ page }) => {
      // Navigate to evidence upload
      await page.click('[data-testid="evidence-nav-item"]');

      await expect(page).toHaveURL(/\/evidence/);
      await expect(page.locator('[data-testid="evidence-upload-section"]')).toBeVisible();
    });

    test('should display upload instructions and requirements', async ({ page }) => {
      await page.click('[data-testid="evidence-nav-item"]');

      // Should show file requirements
      await expect(page.locator('[data-testid="file-requirements"]')).toContainText(/supported.*formats/i);
      await expect(page.locator('[data-testid="max-file-size"]')).toContainText(/10.*MB/i);

      // Should show evidence types
      await expect(page.locator('[data-testid="evidence-types-info"]')).toBeVisible();
    });

    test('should show existing evidence gallery', async ({ page }) => {
      await page.click('[data-testid="evidence-nav-item"]');
      await page.click('[data-testid="my-evidence-tab"]');

      await expect(page.locator('[data-testid="evidence-gallery"]')).toBeVisible();

      // Should show evidence items
      const evidenceItems = page.locator('[data-testid^="evidence-item-"]');
      await expect(evidenceItems.first()).toBeVisible();
    });
  });

  test.describe('File Upload Process', () => {
    test('should upload image evidence successfully', async ({ page }) => {
      await page.click('[data-testid="evidence-nav-item"]');

      // Create a test file
      const testFile = path.join(__dirname, 'fixtures', 'solar-panel-receipt.jpg');

      // Upload file via drag and drop
      const fileInput = page.locator('[data-testid="file-upload-input"]');
      await fileInput.setInputFiles(testFile);

      // Should show file preview
      await expect(page.locator('[data-testid="file-preview"]')).toBeVisible();
      await expect(page.locator('[data-testid="file-name"]')).toContainText('solar-panel-receipt.jpg');

      // Select evidence type
      await page.selectOption('[data-testid="evidence-type-select"]', 'solar_panel');

      // Add description
      await page.fill(
        '[data-testid="evidence-description"]',
        'Receipt for 5kW solar panel system installation'
      );

      // Submit upload
      await page.click('[data-testid="upload-submit-button"]');

      // Should show upload progress
      await expect(page.locator('[data-testid="upload-progress"]')).toBeVisible();

      // Should show success message
      await expect(page.locator('[data-testid="upload-success"]')).toContainText(/uploaded.*successfully/i);
    });

    test('should upload PDF document evidence', async ({ page }) => {
      await page.click('[data-testid="evidence-nav-item"]');

      const testFile = path.join(__dirname, 'fixtures', 'energy-bill.pdf');
      await page.locator('[data-testid="file-upload-input"]').setInputFiles(testFile);

      await page.selectOption('[data-testid="evidence-type-select"]', 'energy_bill');
      await page.fill('[data-testid="evidence-description"]', 'Monthly energy consumption bill');

      await page.click('[data-testid="upload-submit-button"]');

      await expect(page.locator('[data-testid="upload-success"]')).toBeVisible();
    });

    test('should handle multiple file uploads', async ({ page }) => {
      await page.click('[data-testid="evidence-nav-item"]');

      const testFiles = [
        path.join(__dirname, 'fixtures', 'solar-panel-receipt.jpg'),
        path.join(__dirname, 'fixtures', 'led-lights-receipt.jpg'),
      ];

      await page.locator('[data-testid="file-upload-input"]').setInputFiles(testFiles);

      // Should show multiple file previews
      await expect(page.locator('[data-testid="file-preview-0"]')).toBeVisible();
      await expect(page.locator('[data-testid="file-preview-1"]')).toBeVisible();

      // Set evidence types for each file
      await page.selectOption('[data-testid="evidence-type-select-0"]', 'solar_panel');
      await page.selectOption('[data-testid="evidence-type-select-1"]', 'led_lighting');

      await page.click('[data-testid="upload-all-button"]');

      // Should show batch upload progress
      await expect(page.locator('[data-testid="batch-upload-progress"]')).toBeVisible();

      await expect(page.locator('[data-testid="batch-upload-success"]')).toContainText(/2.*uploaded/i);
    });

    test('should validate file types and sizes', async ({ page }) => {
      await page.click('[data-testid="evidence-nav-item"]');

      // Try uploading unsupported file type
      const unsupportedFile = path.join(__dirname, 'fixtures', 'document.exe');
      await page.locator('[data-testid="file-upload-input"]').setInputFiles(unsupportedFile);

      await expect(page.locator('[data-testid="file-type-error"]')).toContainText(/unsupported.*file.*type/i);

      // Try uploading oversized file
      const largeFile = path.join(__dirname, 'fixtures', 'large-image.jpg'); // Mock 15MB file
      await page.locator('[data-testid="file-upload-input"]').setInputFiles(largeFile);

      await expect(page.locator('[data-testid="file-size-error"]')).toContainText(/file.*too.*large/i);
    });

    test('should handle upload errors gracefully', async ({ page }) => {
      // Mock upload failure
      await page.route('/api/evidence/upload', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            error: { message: 'Upload service temporarily unavailable' }
          })
        });
      });

      await page.click('[data-testid="evidence-nav-item"]');

      const testFile = path.join(__dirname, 'fixtures', 'solar-panel-receipt.jpg');
      await page.locator('[data-testid="file-upload-input"]').setInputFiles(testFile);
      await page.selectOption('[data-testid="evidence-type-select"]', 'solar_panel');

      await page.click('[data-testid="upload-submit-button"]');

      // Should show error message
      await expect(page.locator('[data-testid="upload-error"]')).toContainText(/upload.*failed/i);

      // Should offer retry option
      await expect(page.locator('[data-testid="retry-upload-button"]')).toBeVisible();
    });
  });

  test.describe('Evidence Management', () => {
    test('should view evidence details', async ({ page }) => {
      await page.click('[data-testid="evidence-nav-item"]');
      await page.click('[data-testid="my-evidence-tab"]');

      // Click on specific evidence item
      await page.click('[data-testid="evidence-item-0"]');

      await expect(page.locator('[data-testid="evidence-details-modal"]')).toBeVisible();

      // Should show evidence information
      await expect(page.locator('[data-testid="evidence-image"]')).toBeVisible();
      await expect(page.locator('[data-testid="evidence-type-detail"]')).toBeVisible();
      await expect(page.locator('[data-testid="upload-date-detail"]')).toBeVisible();
      await expect(page.locator('[data-testid="processing-status-detail"]')).toBeVisible();
    });

    test('should show AI analysis results', async ({ page }) => {
      await page.click('[data-testid="evidence-nav-item"]');
      await page.click('[data-testid="my-evidence-tab"]');

      await page.click('[data-testid="evidence-item-processed"]');

      // Should show AI analysis
      await expect(page.locator('[data-testid="ai-analysis-section"]')).toBeVisible();
      await expect(page.locator('[data-testid="confidence-score"]')).toContainText(/%/);
      await expect(page.locator('[data-testid="extracted-text"]')).toBeVisible();
      await expect(page.locator('[data-testid="sustainability-impact"]')).toBeVisible();
    });

    test('should allow editing evidence details', async ({ page }) => {
      await page.click('[data-testid="evidence-nav-item"]');
      await page.click('[data-testid="my-evidence-tab"]');

      await page.click('[data-testid="evidence-item-0"]');
      await page.click('[data-testid="edit-evidence-button"]');

      // Update description
      const descriptionField = page.locator('[data-testid="edit-description-input"]');
      await descriptionField.clear();
      await descriptionField.fill('Updated description with more details');

      await page.click('[data-testid="save-changes-button"]');

      await expect(page.locator('[data-testid="evidence-updated"]')).toContainText(/updated.*successfully/i);
    });

    test('should delete evidence with confirmation', async ({ page }) => {
      await page.click('[data-testid="evidence-nav-item"]');
      await page.click('[data-testid="my-evidence-tab"]');

      await page.click('[data-testid="evidence-item-0"]');
      await page.click('[data-testid="delete-evidence-button"]');

      // Should show confirmation dialog
      await expect(page.locator('[data-testid="delete-confirmation-modal"]')).toBeVisible();
      await expect(page.locator('[data-testid="delete-warning"]')).toContainText(/cannot.*be.*undone/i);

      await page.click('[data-testid="confirm-delete-button"]');

      await expect(page.locator('[data-testid="evidence-deleted"]')).toContainText(/deleted.*successfully/i);
    });
  });

  test.describe('Green Score Integration', () => {
    test('should update green score after evidence upload', async ({ page }) => {
      // Get initial green score
      await page.goto('/dashboard');
      const initialScore = await page.locator('[data-testid="current-green-score"]').textContent();

      // Upload new evidence
      await page.click('[data-testid="evidence-nav-item"]');

      const testFile = path.join(__dirname, 'fixtures', 'water-conservation.jpg');
      await page.locator('[data-testid="file-upload-input"]').setInputFiles(testFile);
      await page.selectOption('[data-testid="evidence-type-select"]', 'water_conservation');
      await page.fill('[data-testid="evidence-description"]', 'Rainwater harvesting system');

      await page.click('[data-testid="upload-submit-button"]');

      // Wait for processing
      await expect(page.locator('[data-testid="upload-success"]')).toBeVisible();

      // Navigate back to dashboard
      await page.click('[data-testid="dashboard-nav-item"]');

      // Should show score update notification
      await expect(page.locator('[data-testid="score-update-notification"]')).toContainText(/score.*updated/i);

      // Score should be different (assuming processing is fast in test env)
      const newScore = await page.locator('[data-testid="current-green-score"]').textContent();
      expect(newScore).not.toBe(initialScore);
    });

    test('should show evidence contribution to score breakdown', async ({ page }) => {
      await page.goto('/dashboard');
      await page.click('[data-testid="view-score-breakdown-button"]');

      await expect(page.locator('[data-testid="score-breakdown-modal"]')).toBeVisible();

      // Should show evidence contributions
      await expect(page.locator('[data-testid="evidence-contributions"]')).toBeVisible();
      await expect(page.locator('[data-testid="solar-panel-contribution"]')).toBeVisible();
      await expect(page.locator('[data-testid="led-lighting-contribution"]')).toBeVisible();

      // Should show score factors
      await expect(page.locator('[data-testid="energy-efficiency-factor"]')).toBeVisible();
      await expect(page.locator('[data-testid="renewable-energy-factor"]')).toBeVisible();
    });

    test('should provide score improvement recommendations', async ({ page }) => {
      await page.goto('/dashboard');
      await page.click('[data-testid="view-recommendations-button"]');

      await expect(page.locator('[data-testid="recommendations-modal"]')).toBeVisible();

      // Should show actionable recommendations
      const recommendations = page.locator('[data-testid^="recommendation-"]');
      await expect(recommendations.first()).toBeVisible();

      // Each recommendation should have details
      await expect(page.locator('[data-testid="recommendation-action"]')).toBeVisible();
      await expect(page.locator('[data-testid="recommendation-impact"]')).toContainText(/points/i);
      await expect(page.locator('[data-testid="recommendation-cost"]')).toContainText(/KES/i);
    });
  });

  test.describe('Processing Status Tracking', () => {
    test('should show processing progress for uploaded evidence', async ({ page }) => {
      await page.click('[data-testid="evidence-nav-item"]');

      const testFile = path.join(__dirname, 'fixtures', 'waste-management.jpg');
      await page.locator('[data-testid="file-upload-input"]').setInputFiles(testFile);
      await page.selectOption('[data-testid="evidence-type-select"]', 'waste_management');

      await page.click('[data-testid="upload-submit-button"]');

      // Should show processing status
      await expect(page.locator('[data-testid="processing-status"]')).toContainText(/processing/i);

      // Should show progress indicator
      await expect(page.locator('[data-testid="processing-progress"]')).toBeVisible();

      // Wait for processing to complete
      await expect(page.locator('[data-testid="processing-complete"]')).toBeVisible({ timeout: 30000 });

      // Should show analysis results
      await expect(page.locator('[data-testid="analysis-complete"]')).toContainText(/analysis.*complete/i);
    });

    test('should handle processing errors', async ({ page }) => {
      // Mock processing failure
      await page.route('/api/evidence/*/process', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            error: { message: 'AI processing failed' }
          })
        });
      });

      await page.click('[data-testid="evidence-nav-item"]');

      const testFile = path.join(__dirname, 'fixtures', 'corrupt-image.jpg');
      await page.locator('[data-testid="file-upload-input"]').setInputFiles(testFile);
      await page.selectOption('[data-testid="evidence-type-select"]', 'solar_panel');

      await page.click('[data-testid="upload-submit-button"]');

      // Should show processing error
      await expect(page.locator('[data-testid="processing-error"]')).toContainText(/processing.*failed/i);

      // Should offer reprocessing option
      await expect(page.locator('[data-testid="reprocess-button"]')).toBeVisible();
    });

    test('should show processing queue status', async ({ page }) => {
      await page.click('[data-testid="evidence-nav-item"]');
      await page.click('[data-testid="processing-queue-tab"]');

      // Should show items in processing queue
      await expect(page.locator('[data-testid="processing-queue-list"]')).toBeVisible();

      // Should show queue position for pending items
      await expect(page.locator('[data-testid="queue-position"]')).toContainText(/position.*in.*queue/i);

      // Should show estimated processing time
      await expect(page.locator('[data-testid="estimated-processing-time"]')).toContainText(/minutes/i);
    });
  });

  test.describe('Mobile Evidence Upload', () => {
    test.use({ viewport: { width: 375, height: 667 } });

    test('should work on mobile devices', async ({ page }) => {
      await page.click('[data-testid="mobile-evidence-nav"]');

      // Should show mobile-optimized upload interface
      await expect(page.locator('[data-testid="mobile-upload-area"]')).toBeVisible();

      // Upload using mobile interface
      const testFile = path.join(__dirname, 'fixtures', 'mobile-photo.jpg');
      await page.locator('[data-testid="mobile-file-input"]').setInputFiles(testFile);

      await expect(page.locator('[data-testid="mobile-preview"]')).toBeVisible();
    });

    test('should support camera capture', async ({ page }) => {
      await page.click('[data-testid="mobile-evidence-nav"]');

      // Should show camera option
      await expect(page.locator('[data-testid="camera-capture-button"]')).toBeVisible();

      // Mock camera capture
      await page.click('[data-testid="camera-capture-button"]');

      // Would trigger camera interface (mocked in test environment)
      await expect(page.locator('[data-testid="camera-interface"]')).toBeVisible();
    });

    test('should have touch-friendly upload controls', async ({ page }) => {
      await page.click('[data-testid="mobile-evidence-nav"]');

      // Check touch target sizes
      const uploadButton = page.locator('[data-testid="mobile-upload-button"]');
      const box = await uploadButton.boundingBox();
      expect(box?.height).toBeGreaterThanOrEqual(44);
    });
  });

  test.describe('Performance and Optimization', () => {
    test('should handle large file uploads efficiently', async ({ page }) => {
      await page.click('[data-testid="evidence-nav-item"]');

      // Mock large file (simulated)
      const largeFile = path.join(__dirname, 'fixtures', 'large-document.pdf');
      await page.locator('[data-testid="file-upload-input"]').setInputFiles(largeFile);

      // Should show upload progress with chunked upload
      await expect(page.locator('[data-testid="chunked-upload-progress"]')).toBeVisible();

      // Should complete within reasonable time
      await expect(page.locator('[data-testid="upload-success"]')).toBeVisible({ timeout: 60000 });
    });

    test('should optimize image files before upload', async ({ page }) => {
      await page.click('[data-testid="evidence-nav-item"]');

      const highResImage = path.join(__dirname, 'fixtures', 'high-res-photo.jpg');
      await page.locator('[data-testid="file-upload-input"]').setInputFiles(highResImage);

      // Should show compression progress
      await expect(page.locator('[data-testid="image-compression"]')).toContainText(/optimizing/i);

      // Should show reduced file size
      await expect(page.locator('[data-testid="optimized-size"]')).toContainText(/reduced.*size/i);
    });
  });
});