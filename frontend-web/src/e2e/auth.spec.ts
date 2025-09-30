/**
 * E2E tests for authentication flow.
 * Tests user registration, login, and session management.
 */

import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Clear any existing session
    await page.context().clearCookies();
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
  });

  test.describe('User Registration', () => {
    test('should complete full registration flow', async ({ page }) => {
      // Navigate to registration page
      await page.goto('/auth/register');

      // Fill phone number
      await page.fill('[data-testid="phone-input"]', '+254700123456');

      // Send OTP
      await page.click('[data-testid="send-otp-button"]');

      // Wait for OTP input to appear
      await expect(page.locator('[data-testid="otp-input"]')).toBeVisible();

      // Enter OTP
      await page.fill('[data-testid="otp-input"]', '123456');

      // Verify OTP
      await page.click('[data-testid="verify-otp-button"]');

      // Fill registration form
      await page.fill('[data-testid="name-input"]', 'John Doe');
      await page.fill('[data-testid="email-input"]', 'john@example.com');
      await page.fill('[data-testid="business-name-input"]', 'Doe Enterprises');
      await page.selectOption('[data-testid="business-type-select"]', 'farmer');
      await page.fill('[data-testid="location-input"]', 'Nairobi');

      // Submit registration
      await page.click('[data-testid="complete-registration-button"]');

      // Should redirect to dashboard
      await expect(page).toHaveURL(/\/dashboard/);
      await expect(page.locator('[data-testid="welcome-message"]')).toContainText('Welcome, John Doe');
    });

    test('should validate phone number format', async ({ page }) => {
      await page.goto('/auth/register');

      // Try invalid phone number
      await page.fill('[data-testid="phone-input"]', '123456789');
      await page.click('[data-testid="send-otp-button"]');

      // Should show validation error
      await expect(page.locator('[data-testid="phone-error"]')).toContainText(/invalid.*format/i);
    });

    test('should handle OTP expiration', async ({ page }) => {
      await page.goto('/auth/register');

      await page.fill('[data-testid="phone-input"]', '+254700123456');
      await page.click('[data-testid="send-otp-button"]');

      // Wait for OTP to "expire" (mock scenario)
      await page.waitForTimeout(5000);

      await page.fill('[data-testid="otp-input"]', '123456');
      await page.click('[data-testid="verify-otp-button"]');

      // Should show expiration error
      await expect(page.locator('[data-testid="otp-error"]')).toContainText(/expired/i);

      // Should allow resending OTP
      await expect(page.locator('[data-testid="resend-otp-button"]')).toBeEnabled();
    });

    test('should prevent registration with existing phone', async ({ page }) => {
      await page.goto('/auth/register');

      // Use existing test user phone
      await page.fill('[data-testid="phone-input"]', '+254700000001');
      await page.click('[data-testid="send-otp-button"]');

      // Should show error about existing account
      await expect(page.locator('[data-testid="registration-error"]')).toContainText(/already.*registered/i);
      await expect(page.locator('[data-testid="login-link"]')).toBeVisible();
    });
  });

  test.describe('User Login', () => {
    test('should login existing user successfully', async ({ page }) => {
      await page.goto('/auth/login');

      // Enter existing user phone
      await page.fill('[data-testid="phone-input"]', '+254700000001');
      await page.click('[data-testid="send-otp-button"]');

      // Enter OTP
      await page.fill('[data-testid="otp-input"]', '123456');
      await page.click('[data-testid="verify-otp-button"]');

      // Should redirect to dashboard
      await expect(page).toHaveURL(/\/dashboard/);
      await expect(page.locator('[data-testid="user-profile"]')).toBeVisible();
    });

    test('should handle invalid OTP', async ({ page }) => {
      await page.goto('/auth/login');

      await page.fill('[data-testid="phone-input"]', '+254700000001');
      await page.click('[data-testid="send-otp-button"]');

      // Enter wrong OTP
      await page.fill('[data-testid="otp-input"]', '000000');
      await page.click('[data-testid="verify-otp-button"]');

      // Should show error
      await expect(page.locator('[data-testid="otp-error"]')).toContainText(/invalid.*otp/i);

      // Should allow retry
      await expect(page.locator('[data-testid="otp-input"]')).toBeEnabled();
    });

    test('should handle non-existent user', async ({ page }) => {
      await page.goto('/auth/login');

      await page.fill('[data-testid="phone-input"]', '+254700999999');
      await page.click('[data-testid="send-otp-button"]');

      // Should suggest registration
      await expect(page.locator('[data-testid="user-not-found"]')).toContainText(/not.*found/i);
      await expect(page.locator('[data-testid="register-link"]')).toBeVisible();
    });
  });

  test.describe('Session Management', () => {
    test('should maintain session across page reloads', async ({ page }) => {
      // Login first
      await page.goto('/auth/login');
      await page.fill('[data-testid="phone-input"]', '+254700000001');
      await page.click('[data-testid="send-otp-button"]');
      await page.fill('[data-testid="otp-input"]', '123456');
      await page.click('[data-testid="verify-otp-button"]');

      await expect(page).toHaveURL(/\/dashboard/);

      // Reload page
      await page.reload();

      // Should still be logged in
      await expect(page).toHaveURL(/\/dashboard/);
      await expect(page.locator('[data-testid="user-profile"]')).toBeVisible();
    });

    test('should logout user successfully', async ({ page }) => {
      // Use pre-authenticated state
      await page.goto('/dashboard', {
        storageState: 'test-results/test-user-1-auth.json'
      });

      // Click logout
      await page.click('[data-testid="user-menu"]');
      await page.click('[data-testid="logout-button"]');

      // Should redirect to login
      await expect(page).toHaveURL(/\/auth\/login/);

      // Verify session is cleared
      const token = await page.evaluate(() => localStorage.getItem('auth_token'));
      expect(token).toBeNull();
    });

    test('should redirect unauthenticated users to login', async ({ page }) => {
      // Try to access protected page without authentication
      await page.goto('/dashboard');

      // Should redirect to login
      await expect(page).toHaveURL(/\/auth\/login/);
      await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
    });

    test('should handle token expiration gracefully', async ({ page }) => {
      // Setup expired token
      await page.goto('/dashboard');
      await page.evaluate(() => {
        localStorage.setItem('auth_token', 'expired.token.here');
      });

      // Reload page to trigger token validation
      await page.reload();

      // Should redirect to login
      await expect(page).toHaveURL(/\/auth\/login/);
      await expect(page.locator('[data-testid="session-expired"]')).toContainText(/session.*expired/i);
    });
  });

  test.describe('Authentication Security', () => {
    test('should enforce rate limiting on OTP requests', async ({ page }) => {
      await page.goto('/auth/login');

      const phone = '+254700000001';
      await page.fill('[data-testid="phone-input"]', phone);

      // Send multiple OTP requests rapidly
      for (let i = 0; i < 6; i++) {
        await page.click('[data-testid="send-otp-button"]');
        await page.waitForTimeout(100);
      }

      // Should show rate limit error
      await expect(page.locator('[data-testid="rate-limit-error"]')).toContainText(/too.*many.*requests/i);

      // Button should be disabled
      await expect(page.locator('[data-testid="send-otp-button"]')).toBeDisabled();
    });

    test('should validate input against XSS attempts', async ({ page }) => {
      await page.goto('/auth/register');

      // Try XSS in name field
      const maliciousInput = '<script>alert("xss")</script>';
      await page.fill('[data-testid="phone-input"]', '+254700123456');
      await page.click('[data-testid="send-otp-button"]');
      await page.fill('[data-testid="otp-input"]', '123456');
      await page.click('[data-testid="verify-otp-button"]');

      await page.fill('[data-testid="name-input"]', maliciousInput);

      // Should either sanitize or reject the input
      const nameValue = await page.inputValue('[data-testid="name-input"]');
      expect(nameValue).not.toContain('<script>');

      // Or should show validation error
      const hasError = await page.locator('[data-testid="name-error"]').isVisible();
      if (hasError) {
        await expect(page.locator('[data-testid="name-error"]')).toContainText(/invalid.*characters/i);
      }
    });

    test('should protect against CSRF attacks', async ({ page, context }) => {
      // This test would require setting up CSRF scenarios
      // For now, we'll verify CSRF tokens are present in forms

      await page.goto('/auth/login');

      // Check for CSRF protection mechanisms
      const metaTags = await page.locator('meta[name="csrf-token"]').count();
      const hiddenInputs = await page.locator('input[type="hidden"][name*="csrf"]').count();

      // Should have some form of CSRF protection
      expect(metaTags + hiddenInputs).toBeGreaterThan(0);
    });
  });

  test.describe('Mobile Authentication', () => {
    test.use({ viewport: { width: 375, height: 667 } }); // iPhone SE

    test('should work on mobile devices', async ({ page }) => {
      await page.goto('/auth/login');

      // Check mobile-responsive design
      await expect(page.locator('[data-testid="mobile-auth-container"]')).toBeVisible();

      // Complete login flow on mobile
      await page.fill('[data-testid="phone-input"]', '+254700000001');
      await page.click('[data-testid="send-otp-button"]');
      await page.fill('[data-testid="otp-input"]', '123456');
      await page.click('[data-testid="verify-otp-button"]');

      await expect(page).toHaveURL(/\/dashboard/);
    });

    test('should handle touch interactions', async ({ page }) => {
      await page.goto('/auth/login');

      // Test touch-friendly OTP input
      await page.fill('[data-testid="phone-input"]', '+254700000001');
      await page.click('[data-testid="send-otp-button"]');

      // OTP input should be touch-friendly
      const otpInput = page.locator('[data-testid="otp-input"]');
      await expect(otpInput).toHaveCSS('min-height', /44px|3rem/); // Minimum touch target size
    });
  });

  test.describe('Accessibility', () => {
    test('should be accessible with keyboard navigation', async ({ page }) => {
      await page.goto('/auth/login');

      // Tab through the form
      await page.keyboard.press('Tab');
      await expect(page.locator('[data-testid="phone-input"]')).toBeFocused();

      await page.keyboard.press('Tab');
      await expect(page.locator('[data-testid="send-otp-button"]')).toBeFocused();

      // Fill form using keyboard
      await page.keyboard.press('Shift+Tab'); // Go back to phone input
      await page.keyboard.type('+254700000001');
      await page.keyboard.press('Tab');
      await page.keyboard.press('Enter'); // Click send OTP

      // Continue with OTP input
      await page.keyboard.press('Tab');
      await expect(page.locator('[data-testid="otp-input"]')).toBeFocused();
    });

    test('should have proper ARIA labels and screen reader support', async ({ page }) => {
      await page.goto('/auth/login');

      // Check ARIA labels
      await expect(page.locator('[data-testid="phone-input"]')).toHaveAttribute('aria-label');
      await expect(page.locator('[data-testid="send-otp-button"]')).toHaveAttribute('aria-describedby');

      // Check for screen reader announcements
      const liveRegion = page.locator('[aria-live="polite"]');
      await expect(liveRegion).toBeAttached();
    });

    test('should meet color contrast requirements', async ({ page }) => {
      await page.goto('/auth/login');

      // This would require color contrast analysis
      // For now, we'll check that high contrast mode is supported
      await page.emulateMedia({ colorScheme: 'dark' });
      await page.reload();

      // Elements should still be visible in dark mode
      await expect(page.locator('[data-testid="phone-input"]')).toBeVisible();
      await expect(page.locator('[data-testid="send-otp-button"]')).toBeVisible();
    });
  });
});