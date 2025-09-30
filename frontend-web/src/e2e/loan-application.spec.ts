/**
 * E2E tests for loan application flow.
 * Tests the complete user journey from eligibility check to loan application submission.
 */

import { test, expect } from '@playwright/test';

test.describe('Loan Application Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Use pre-authenticated state
    await page.goto('/dashboard', {
      storageState: 'test-results/test-user-1-auth.json'
    });
  });

  test.describe('Loan Eligibility', () => {
    test('should check loan eligibility based on green score', async ({ page }) => {
      // Navigate to loan section
      await page.click('[data-testid="loans-nav-item"]');
      await expect(page).toHaveURL(/\/loans/);

      // Check eligibility display
      await expect(page.locator('[data-testid="eligibility-status"]')).toBeVisible();

      // Should show green score impact
      await expect(page.locator('[data-testid="green-score-benefit"]')).toContainText(/green.*score/i);

      // Should display maximum loan amount
      const maxAmount = page.locator('[data-testid="max-loan-amount"]');
      await expect(maxAmount).toBeVisible();
      await expect(maxAmount).toContainText(/1,000,000|1M/);
    });

    test('should show ineligibility reasons for low green score', async ({ page, context }) => {
      // Switch to low green score user
      await page.goto('/dashboard', {
        storageState: 'test-results/test-user-2-auth.json'
      });

      await page.click('[data-testid="loans-nav-item"]');

      // Should show ineligibility message
      await expect(page.locator('[data-testid="ineligible-message"]')).toContainText(/not.*eligible/i);

      // Should show improvement suggestions
      await expect(page.locator('[data-testid="improvement-suggestions"]')).toBeVisible();
      await expect(page.locator('[data-testid="upload-evidence-suggestion"]')).toContainText(/upload.*evidence/i);
    });

    test('should display personalized loan terms', async ({ page }) => {
      await page.click('[data-testid="loans-nav-item"]');

      // Check interest rate display
      const interestRate = page.locator('[data-testid="interest-rate"]');
      await expect(interestRate).toBeVisible();
      await expect(interestRate).toContainText(/%/);

      // Check repayment terms
      await expect(page.locator('[data-testid="max-term"]')).toContainText(/months/i);

      // Check green score discount
      await expect(page.locator('[data-testid="green-discount"]')).toContainText(/discount|bonus/i);
    });
  });

  test.describe('Loan Calculator', () => {
    test('should calculate loan payments in real-time', async ({ page }) => {
      await page.click('[data-testid="loans-nav-item"]');

      // Use loan calculator
      const amountInput = page.locator('[data-testid="loan-amount-input"]');
      await amountInput.fill('500000');

      const termSelect = page.locator('[data-testid="loan-term-select"]');
      await termSelect.selectOption('12');

      // Should show calculated monthly payment
      const monthlyPayment = page.locator('[data-testid="monthly-payment"]');
      await expect(monthlyPayment).toBeVisible();
      await expect(monthlyPayment).toContainText(/44,471|44471/);

      // Should show total interest
      await expect(page.locator('[data-testid="total-interest"]')).toBeVisible();
    });

    test('should validate loan amount within limits', async ({ page }) => {
      await page.click('[data-testid="loans-nav-item"]');

      // Try amount above limit
      await page.fill('[data-testid="loan-amount-input"]', '2000000');

      await expect(page.locator('[data-testid="amount-error"]')).toContainText(/exceeds.*maximum/i);

      // Try amount below limit
      await page.fill('[data-testid="loan-amount-input"]', '10000');

      await expect(page.locator('[data-testid="amount-error"]')).toContainText(/below.*minimum/i);
    });

    test('should show amortization schedule', async ({ page }) => {
      await page.click('[data-testid="loans-nav-item"]');

      await page.fill('[data-testid="loan-amount-input"]', '300000');
      await page.selectOption('[data-testid="loan-term-select"]', '6');

      // Open amortization schedule
      await page.click('[data-testid="view-schedule-button"]');

      await expect(page.locator('[data-testid="amortization-modal"]')).toBeVisible();

      // Should show payment breakdown
      await expect(page.locator('[data-testid="payment-1"]')).toBeVisible();
      await expect(page.locator('[data-testid="principal-payment-1"]')).toBeVisible();
      await expect(page.locator('[data-testid="interest-payment-1"]')).toBeVisible();
    });
  });

  test.describe('Loan Application Process', () => {
    test('should complete full loan application', async ({ page }) => {
      await page.click('[data-testid="loans-nav-item"]');

      // Start application
      await page.click('[data-testid="apply-now-button"]');

      await expect(page.locator('[data-testid="loan-application-form"]')).toBeVisible();

      // Fill loan amount
      await page.fill('[data-testid="loan-amount-input"]', '500000');

      // Select loan term
      await page.selectOption('[data-testid="loan-term-select"]', '12');

      // Select loan purpose
      await page.selectOption('[data-testid="loan-purpose-select"]', 'equipment');

      // Fill business plan
      await page.fill(
        '[data-testid="business-plan-textarea"]',
        'Planning to purchase new farming equipment to increase productivity and implement sustainable practices.'
      );

      // Fill collateral description
      await page.fill(
        '[data-testid="collateral-textarea"]',
        'Farm equipment, land title, and existing machinery as collateral for the loan.'
      );

      // Submit application
      await page.click('[data-testid="submit-application-button"]');

      // Should show loading state
      await expect(page.locator('[data-testid="submitting-application"]')).toBeVisible();

      // Should show success message
      await expect(page.locator('[data-testid="application-success"]')).toContainText(/application.*submitted/i);

      // Should display application ID
      await expect(page.locator('[data-testid="application-id"]')).toBeVisible();
    });

    test('should validate required fields', async ({ page }) => {
      await page.click('[data-testid="loans-nav-item"]');
      await page.click('[data-testid="apply-now-button"]');

      // Try to submit without filling required fields
      await page.click('[data-testid="submit-application-button"]');

      // Should show validation errors
      await expect(page.locator('[data-testid="amount-required-error"]')).toContainText(/amount.*required/i);
      await expect(page.locator('[data-testid="purpose-required-error"]')).toContainText(/purpose.*required/i);
    });

    test('should save draft application', async ({ page }) => {
      await page.click('[data-testid="loans-nav-item"]');
      await page.click('[data-testid="apply-now-button"]');

      // Fill partial form
      await page.fill('[data-testid="loan-amount-input"]', '300000');
      await page.selectOption('[data-testid="loan-purpose-select"]', 'expansion');

      // Save as draft
      await page.click('[data-testid="save-draft-button"]');

      await expect(page.locator('[data-testid="draft-saved"]')).toContainText(/draft.*saved/i);

      // Navigate away and back
      await page.click('[data-testid="dashboard-nav-item"]');
      await page.click('[data-testid="loans-nav-item"]');

      // Should show draft notification
      await expect(page.locator('[data-testid="draft-application"]')).toBeVisible();

      // Resume draft
      await page.click('[data-testid="resume-draft-button"]');

      // Should have saved values
      await expect(page.locator('[data-testid="loan-amount-input"]')).toHaveValue('300000');
      await expect(page.locator('[data-testid="loan-purpose-select"]')).toHaveValue('expansion');
    });

    test('should handle application submission errors', async ({ page }) => {
      // Mock API error
      await page.route('/api/loans/apply', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            error: {
              message: 'Service temporarily unavailable',
              category: 'SYSTEM'
            }
          })
        });
      });

      await page.click('[data-testid="loans-nav-item"]');
      await page.click('[data-testid="apply-now-button"]');

      // Fill and submit form
      await page.fill('[data-testid="loan-amount-input"]', '400000');
      await page.selectOption('[data-testid="loan-purpose-select"]', 'equipment');
      await page.fill('[data-testid="business-plan-textarea"]', 'Test business plan');

      await page.click('[data-testid="submit-application-button"]');

      // Should show error message
      await expect(page.locator('[data-testid="application-error"]')).toContainText(/service.*unavailable/i);

      // Should allow retry
      await expect(page.locator('[data-testid="retry-application-button"]')).toBeVisible();
    });
  });

  test.describe('Loan Application Management', () => {
    test('should view existing loan applications', async ({ page }) => {
      // Navigate to loans section
      await page.click('[data-testid="loans-nav-item"]');
      await page.click('[data-testid="my-loans-tab"]');

      // Should show loan applications list
      await expect(page.locator('[data-testid="loan-applications-list"]')).toBeVisible();

      // Check loan application details
      const firstLoan = page.locator('[data-testid="loan-application-0"]');
      await expect(firstLoan).toBeVisible();
      await expect(firstLoan).toContainText(/500,000/); // Amount
      await expect(firstLoan).toContainText(/pending|approved|disbursed/); // Status
    });

    test('should view detailed loan application', async ({ page }) => {
      await page.click('[data-testid="loans-nav-item"]');
      await page.click('[data-testid="my-loans-tab"]');

      // Click on specific loan application
      await page.click('[data-testid="loan-application-0"]');

      await expect(page.locator('[data-testid="loan-details-modal"]')).toBeVisible();

      // Should show comprehensive details
      await expect(page.locator('[data-testid="loan-amount-detail"]')).toBeVisible();
      await expect(page.locator('[data-testid="interest-rate-detail"]')).toBeVisible();
      await expect(page.locator('[data-testid="application-status-detail"]')).toBeVisible();
      await expect(page.locator('[data-testid="application-date-detail"]')).toBeVisible();
    });

    test('should update pending loan application', async ({ page }) => {
      await page.click('[data-testid="loans-nav-item"]');
      await page.click('[data-testid="my-loans-tab"]');

      // Find pending application
      const pendingLoan = page.locator('[data-testid="loan-application-pending"]');
      await pendingLoan.click();

      // Should show edit option for pending loans
      await expect(page.locator('[data-testid="edit-application-button"]')).toBeVisible();

      await page.click('[data-testid="edit-application-button"]');

      // Update application
      await page.fill('[data-testid="business-plan-textarea"]', 'Updated business plan with more details');

      await page.click('[data-testid="update-application-button"]');

      await expect(page.locator('[data-testid="application-updated"]')).toContainText(/updated.*successfully/i);
    });

    test('should cancel pending loan application', async ({ page }) => {
      await page.click('[data-testid="loans-nav-item"]');
      await page.click('[data-testid="my-loans-tab"]');

      const pendingLoan = page.locator('[data-testid="loan-application-pending"]');
      await pendingLoan.click();

      // Cancel application
      await page.click('[data-testid="cancel-application-button"]');

      // Confirm cancellation
      await expect(page.locator('[data-testid="cancel-confirmation-modal"]')).toBeVisible();
      await page.click('[data-testid="confirm-cancel-button"]');

      await expect(page.locator('[data-testid="application-cancelled"]')).toContainText(/cancelled.*successfully/i);
    });
  });

  test.describe('Loan Status Tracking', () => {
    test('should show loan application progress', async ({ page }) => {
      await page.click('[data-testid="loans-nav-item"]');
      await page.click('[data-testid="my-loans-tab"]');

      // View loan in progress
      await page.click('[data-testid="loan-application-0"]');

      // Should show progress steps
      await expect(page.locator('[data-testid="loan-progress-tracker"]')).toBeVisible();

      const steps = [
        'Application Submitted',
        'Under Review',
        'Credit Assessment',
        'Approval Decision',
        'Disbursement'
      ];

      for (const step of steps) {
        await expect(page.locator(`[data-testid="progress-step-${step.toLowerCase().replace(/\s+/g, '-')}"]`)).toBeVisible();
      }
    });

    test('should show loan disbursement details', async ({ page }) => {
      // Mock approved/disbursed loan
      await page.route('/api/loans/my-loans', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: '1',
              amount: 500000,
              status: 'disbursed',
              disbursed_date: '2024-01-15T10:00:00Z',
              disbursed_amount: 500000,
              account_number: '****1234',
              next_payment_date: '2024-02-15',
              monthly_payment: 44471
            }
          ])
        });
      });

      await page.click('[data-testid="loans-nav-item"]');
      await page.click('[data-testid="my-loans-tab"]');

      await page.click('[data-testid="loan-application-0"]');

      // Should show disbursement information
      await expect(page.locator('[data-testid="disbursement-info"]')).toBeVisible();
      await expect(page.locator('[data-testid="disbursed-amount"]')).toContainText('500,000');
      await expect(page.locator('[data-testid="disbursed-date"]')).toContainText('Jan 15, 2024');
      await expect(page.locator('[data-testid="next-payment-date"]')).toContainText('Feb 15, 2024');
    });

    test('should show repayment schedule', async ({ page }) => {
      await page.click('[data-testid="loans-nav-item"]');
      await page.click('[data-testid="my-loans-tab"]');

      // View disbursed loan
      await page.click('[data-testid="loan-application-disbursed"]');

      // View repayment schedule
      await page.click('[data-testid="view-repayment-schedule-button"]');

      await expect(page.locator('[data-testid="repayment-schedule-modal"]')).toBeVisible();

      // Should show payment schedule
      await expect(page.locator('[data-testid="payment-schedule-table"]')).toBeVisible();
      await expect(page.locator('[data-testid="payment-1-date"]')).toBeVisible();
      await expect(page.locator('[data-testid="payment-1-amount"]')).toBeVisible();
      await expect(page.locator('[data-testid="payment-1-status"]')).toBeVisible();
    });
  });

  test.describe('Mobile Loan Application', () => {
    test.use({ viewport: { width: 375, height: 667 } });

    test('should work on mobile devices', async ({ page }) => {
      await page.click('[data-testid="mobile-loans-nav"]');

      // Mobile loan calculator
      await page.fill('[data-testid="loan-amount-input"]', '300000');
      await page.selectOption('[data-testid="loan-term-select"]', '12');

      // Should show mobile-optimized calculator
      await expect(page.locator('[data-testid="mobile-calculator"]')).toBeVisible();

      // Apply for loan on mobile
      await page.click('[data-testid="mobile-apply-button"]');

      // Should show mobile-optimized form
      await expect(page.locator('[data-testid="mobile-application-form"]')).toBeVisible();
    });

    test('should have touch-friendly interactions', async ({ page }) => {
      await page.click('[data-testid="mobile-loans-nav"]');

      // Check touch targets are large enough
      const applyButton = page.locator('[data-testid="mobile-apply-button"]');
      const box = await applyButton.boundingBox();
      expect(box?.height).toBeGreaterThanOrEqual(44); // Minimum touch target
    });
  });
});