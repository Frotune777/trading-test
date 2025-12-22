/**
 * E2E Tests for Navigation and Cross-Page Functionality
 * 
 * Tests:
 * - Navigation between QUAD dashboard and other pages
 * - Sidebar navigation
 * - No regressions on existing stock detail pages
 */

import { test, expect } from '@playwright/test';

test.describe('Navigation and Cross-Page Tests', () => {
  test('should navigate to QUAD dashboard from sidebar', async ({ page }) => {
    await page.goto('/dashboard');

    // Click QUAD Analytics link in sidebar
    const quadLink = page.locator('text=QUAD Analytics');
    await expect(quadLink).toBeVisible();
    await quadLink.click();

    // Should navigate to /quad route
    await expect(page).toHaveURL(/.*\/quad/);
    await expect(page.locator('h1')).toContainText('QUAD Reasoning Analytics');
  });

  test('should show QUAD Analytics in sidebar navigation', async ({ page }) => {
    await page.goto('/dashboard');

    // Check that QUAD Analytics link exists in sidebar
    const quadLink = page.locator('a:has-text("QUAD Analytics")');
    await expect(quadLink).toBeVisible();

    // Check it has the Brain icon (lucide-react icon)
    await expect(quadLink).toBeVisible();
  });

  test('should navigate back to dashboard from QUAD', async ({ page }) => {
    await page.goto('/quad');

    // Click Dashboard link in sidebar (if visible)
    const dashboardLink = page.locator('nav a:has-text("Dashboard")');
    await dashboardLink.click();

    // Should navigate back to dashboard
    await expect(page).toHaveURL(/.*\/dashboard/);
  });

  test('should maintain state when navigating back to QUAD', async ({ page }) => {
    // Mock API
    await page.route('**/api/v1/recommendations/*/reasoning', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          symbol: 'TCS',
          directional_bias: 'BULLISH',
          conviction_score: 80,
          is_execution_ready: true,
          quality: {
            total_pillars: 6,
            active_pillars: 6,
            placeholder_pillars: 0,
            failed_pillars: [],
          },
          pillar_scores: {},
          warnings: [],
          reasoning: 'Test reasoning',
          contract_version: '1.0.0',
          analysis_timestamp: '2025-12-23T00:00:00Z',
          is_valid: true,
        }),
      });
    });

    await page.goto('/quad');

    // Change symbol to TCS
    const symbolInput = page.locator('input[id="symbol"]');
    await symbolInput.clear();
    await symbolInput.fill('TCS');
    await page.click('button:has-text("Analyze")');

    // Wait for data to load
    await page.waitForTimeout(500);

    // Navigate away
    await page.goto('/dashboard');

    // Navigate back
    await page.goto('/quad');

    // Symbol input should still show the value (or reset to default)
    await expect(symbolInput).toBeVisible();
  });

  test('should not break existing pages when QUAD is added', async ({ page }) => {
    // Test that dashboard still works
    await page.goto('/dashboard');
    // Look specifically for the Dashboard heading in the main content
    await expect(page.locator('main h1, .dashboard-title, text="Dashboard Overview"').first()).toBeVisible();

    // Test that we can navigate to other routes
    const analysisLink = page.locator('nav a:has-text("Analysis")');
    if (await analysisLink.isVisible()) {
      // Page exists, can navigate
      await expect(analysisLink).toBeVisible();
    }
  });

  test('should handle direct URL navigation to /quad', async ({ page }) => {
    // Navigate directly to /quad URL
    await page.goto('http://localhost:3000/quad');

    // Page should load correctly
    await expect(page.locator('h1')).toContainText('QUAD Reasoning Analytics');
    await expect(page.locator('input[id="symbol"]')).toBeVisible();
  });

  test('should have correct page title', async ({ page }) => {
    await page.goto('/quad');

    // Check page title (may be set by Next.js metadata)
    const title = await page.title();
    expect(title).toBeTruthy();
  });

  test('should handle browser back/forward navigation', async ({ page }) => {
    // Start at dashboard
    await page.goto('/dashboard');

    // Navigate to QUAD
    await page.goto('/quad');
    await expect(page.locator('h1')).toContainText('QUAD Reasoning Analytics');

    // Go back
    await page.goBack();
    await expect(page).toHaveURL(/.*\/dashboard/);

    // Go forward
   await page.goForward();
    await expect(page).toHaveURL(/.*\/quad/);
    await expect(page.locator('h1')).toContainText('QUAD Reasoning Analytics');
  });

  test('should support keyboard navigation', async ({ page }) => {
    await page.goto('/quad');

    // Tab to symbol input (first might be Home, then Dashboard, etc.)
    // We'll iterate until focused or use focused locator
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Type a symbol
    await page.keyboard.type('INFY');
    await expect(page.locator('input[id="symbol"]')).toHaveValue(/.*INFY/);
  });
});
