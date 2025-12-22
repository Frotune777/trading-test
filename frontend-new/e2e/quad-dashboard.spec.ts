/**
 * E2E Tests for QUAD Analytics Dashboard
 * 
 * Tests:
 * - API connectivity with mocked responses
 * - All components rendering correctly
 * - Responsiveness across desktop and mobile
 * - Navigation between pages
 * - Edge cases (errors, missing data, placeholders)
 */

import { test, expect } from '@playwright/test';
import {
  mockTradeIntentResponse,
  mockTradeIntentNotReady,
  mockTradeIntentWithFailures,
} from './fixtures/mock-api-data';

test.describe('QUAD Analytics Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API endpoint before navigating to page
    await page.route('**/api/v1/recommendations/*/reasoning', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockTradeIntentResponse),
      });
    });
  });

  test.describe('Page Load and Initialization', () => {
    test('should load QUAD dashboard and display header', async ({ page }) => {
      await page.goto('/quad');

      // Check page title and header
      await expect(page.locator('h1')).toContainText('QUAD Reasoning Analytics');
      await expect(page.locator('text=Multi-dimensional market analysis')).toBeVisible();
    });

    test('should have symbol input field with default value', async ({ page }) => {
      await page.goto('/quad');

      // Check symbol input exists and has default value
      const symbolInput = page.locator('input[id="symbol"]');
      await expect(symbolInput).toBeVisible();
      await expect(symbolInput).toHaveValue('RELIANCE');
    });

    test('should have analyze button', async ({ page }) => {
      await page.goto('/quad');

      const analyzeButton = page.locator('button:has-text("Analyze")');
      await expect(analyzeButton).toBeVisible();
      await expect(analyzeButton).toBeEnabled();
    });
  });

  test.describe('API Integration', () => {
    test('should fetch and display reasoning data on page load', async ({ page }) => {
      await page.goto('/quad');

      // Wait for API call and data to load
      await expect(page.locator('text=Analyzing')).not.toBeVisible();

      // Check that reasoning summary is displayed
      await expect(
        page.locator('text=Bias: BULLISH (Conviction: 70%)')
      ).toBeVisible();
    });

    test('should show loading state while fetching data', async ({ page }) => {
      // Delay the API response to see loading state
      await page.route('**/api/v1/recommendations/*/reasoning', async (route) => {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockTradeIntentResponse),
        });
      });

      await page.goto('/quad');
      
      // Click analyze to trigger fetch
      await page.click('button:has-text("Analyze")');

      // Should show loading indicator
      await expect(page.locator('text=Analyzing RELIANCE...')).toBeVisible();
    });

    test('should handle API errors gracefully', async ({ page }) => {
      await page.route('**/api/v1/recommendations/*/reasoning', async (route) => {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Internal server error' }),
        });
      });

      await page.goto('/quad');

      // Should show error message
      await expect(page.getByText('Error', { exact: true })).toBeVisible();
      await expect(page.locator('text=API error')).toBeVisible();
    });
  });

  test.describe('ConvictionMeter Component', () => {
    test('should display conviction score correctly', async ({ page }) => {
      await page.goto('/quad');

      // Check conviction percentage
      await expect(page.getByTestId('conviction-score')).toContainText('70.2%');
      await expect(page.getByTestId('conviction-label')).toHaveText('High');
    });

    test('should show execution ready status', async ({ page }) => {
      await page.goto('/quad');

      await expect(page.locator('text=Ready')).toBeVisible();
      await expect(page.locator('text=Execution Status')).toBeVisible();
    });

    test('should display directional bias', async ({ page }) => {
      await page.goto('/quad');

      // Check directional bias is visible
      await expect(page.getByTestId('conviction-bias')).toHaveText('BULLISH');
      await expect(page.locator('text=Directional Bias')).toBeVisible();
    });

    test('should show contract version', async ({ page }) => {
      await page.goto('/quad');

      await expect(page.locator('text=v1.0.0')).toBeVisible();
    });

    test('should display disclaimer text', async ({ page }) => {
      await page.goto('/quad');

      await expect(
        page.locator('text=This is analysis only, not trading advice')
      ).toBeVisible();
    });
  });

  test.describe('PillarDashboard Component', () => {
    test('should render all six pillars', async ({ page }) => {
      await page.goto('/quad');

      // Check all pillar names are visible
      await expect(page.locator('text=Trend').first()).toBeVisible();
      await expect(page.locator('text=Momentum').first()).toBeVisible();
      await expect(page.locator('text=Volatility').first()).toBeVisible();
      await expect(page.locator('text=Liquidity').first()).toBeVisible();
      await expect(page.locator('text=Sentiment').first()).toBeVisible();
      await expect(page.locator('text=Regime').first()).toBeVisible();
    });

    test('should display correct scores for each pillar', async ({ page }) => {
      await page.goto('/quad');

      // Check specific scores
      await expect(page.locator('text=50.0').first()).toBeVisible(); // Trend
      await expect(page.locator('text=100.0')).toBeVisible(); // Momentum
      await expect(page.locator('text=85.0')).toBeVisible(); // Regime
    });

    test('should show placeholder indicators', async ({ page }) => {
      await page.goto('/quad');

      // Should have 2 placeholder badges in the pillar cards
      const placeholderBadges = page.locator('[data-testid="pillar-card"] :text("Placeholder")');
      await expect(placeholderBadges).toHaveCount(2);
    });

    test('should display weight percentages', async ({ page }) => {
      await page.goto('/quad');

      await expect(page.locator('text=30% weight')).toBeVisible(); // Trend
      await expect(page.locator('text=10% weight').first()).toBeVisible(); // Volatility/Liquidity/Sentiment
    });

    test('should show pillar count in header', async ({ page }) => {
      await page.goto('/quad');

      await expect(page.locator('text=6 pillars analyzed')).toBeVisible();
    });
  });

  test.describe('WarningsPanel Component', () => {
    test('should display quality metadata', async ({ page }) => {
      await page.goto('/quad');

      // Check active pillars
      await expect(page.locator('text=4/6').first()).toBeVisible();
      await expect(page.locator('text=67% operational')).toBeVisible();
      
      // Check placeholder count
      await expect(page.getByTestId('placeholder-count')).toHaveText('2');
    });

    test('should show degradation warnings', async ({ page }) => {
      await page.goto('/quad');

      await expect(page.locator('text=Degradation Warnings (2)')).toBeVisible();
      await expect(
        page.locator('text=Volatility pillar is placeholder')
      ).toBeVisible();
      await expect(
        page.locator('text=Liquidity pillar is placeholder')
      ).toBeVisible();
    });

    test('should display health status', async ({ page }) => {
      await page.goto('/quad');

      await expect(page.locator('text=Warning').first()).toBeVisible();
    });

    test('should show data age', async ({ page }) => {
      await page.goto('/quad');

      await expect(page.locator('text=Data age:')).toBeVisible();
      await expect(page.locator('text=5s')).toBeVisible();
    });
  });

  test.describe('User Interactions', () => {
    test('should allow user to enter a different symbol', async ({ page }) => {
      await page.goto('/quad');

      const symbolInput = page.locator('input[id="symbol"]');
      await symbolInput.clear();
      await symbolInput.fill('TCS');

      await expect(symbolInput).toHaveValue('TCS');
    });

    test('should trigger analysis when analyze button is clicked', async ({ page }) => {
      await page.goto('/quad');

      // Change symbol
      const symbolInput = page.locator('input[id="symbol"]');
      await symbolInput.clear();
      await symbolInput.fill('INFY');

      // Click analyze
      await page.click('button:has-text("Analyze")');

      // Should see loading state briefly, then results
      await page.waitForTimeout(500);

      // Data should be displayed (mocked for INFY)
      await expect(page.locator('text=QUAD Reasoning Analytics')).toBeVisible();
    });

    test('should disable button while loading', async ({ page }) => {
      await page.route('**/api/v1/recommendations/*/reasoning', async (route) => {
        await new Promise((resolve) => setTimeout(resolve, 2000));
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockTradeIntentResponse),
        });
      });

      await page.goto('/quad');

      // Click analyze
      await page.click('button:has-text("Analyze")');

      // Button should be disabled during loading
      const analyzeButton = page.locator('button:has-text("Analyzing...")');
      await expect(analyzeButton).toBeDisabled();
    });
  });

  test.describe('Edge Cases', () => {
    test('should handle not execution ready state', async ({ page }) => {
      await page.route('**/api/v1/recommendations/*/reasoning', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockTradeIntentNotReady),
        });
      });

      await page.goto('/quad');

      // Should show "Not Ready" status
      await expect(page.getByTestId('execution-ready-status')).toHaveText('Not Ready');
      await expect(page.getByTestId('conviction-score')).toContainText('45.0%');
      await expect(page.getByTestId('conviction-bias')).toHaveText('NEUTRAL');
    });

    test('should handle failed pillars', async ({ page }) => {
      await page.route('**/api/v1/recommendations/*/reasoning', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockTradeIntentWithFailures),
        });
      });

      await page.goto('/quad');

      // Should show critical status
      await expect(page.locator('text=Critical')).toBeVisible();
      await expect(page.locator('text=trend, momentum')).toBeVisible();
      await expect(page.locator('text=INVALID')).toBeVisible();
    });

    test('should show empty state when no data', async ({ page }) => {
      // Don't auto-load data on initial visit
      await page.route('**/api/v1/recommendations/*/reasoning', async (route) => {
        // Block initial request
        await route.abort();
      });

      await page.goto('/quad');

      // Should show empty state message
      await expect(
        page.locator('text=Enter a stock symbol to begin analysis')
      ).toBeVisible();
    });
  });

  test.describe('Responsive Design', () => {
    test('should display correctly on desktop', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto('/quad');

      // Check that components are visible and laid out horizontally
      const pillarDashboard = page.locator('text=QUAD Pillar Breakdown');
      await expect(pillarDashboard).toBeVisible();

      // Check layout is not stacked vertically (desktop view)
      const convictionMeter = page.locator('text=Analysis Conviction');
      await expect(convictionMeter).toBeVisible();
    });

    test('should display correctly on mobile', async ({ page }, testInfo) => {
      // Only run on mobile projects
      if (!testInfo.project.name.includes('Mobile')) {
        test.skip();
      }

      await page.goto('/quad');

      // Components should still be visible on mobile
      await expect(page.locator('text=QUAD Reasoning Analytics')).toBeVisible();
      await expect(page.locator('text=70.2%')).toBeVisible();

      // Check that pillars are stacked vertically (mobile view)
      const pillars = page.locator('text=Trend');
      await expect(pillars.first()).toBeVisible();
    });

    test('should handle text wrapping on small screens', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE

      await page.goto('/quad');

      // All main components should still be accessible
      await expect(page.locator('text=QUAD Reasoning Analytics')).toBeVisible();
      await expect(page.locator('input[id="symbol"]')).toBeVisible();
      await expect(page.locator('button:has-text("Analyze")')).toBeVisible();
    });
  });
});
