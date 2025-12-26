/**
 * E2E Tests for QUAD Analytics Dashboard (Institutional UI)
 */

import { test, expect } from '@playwright/test';
import {
  mockTradeIntentResponse,
  mockTradeIntentNotReady,
  mockTradeIntentWithFailures,
} from './fixtures/mock-api-data';

test.describe('QUAD Analytics Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API endpoints (v1.1 uses /reasoning/...)
    await page.route('**/api/v1/reasoning/*/reasoning', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockTradeIntentResponse),
      });
    });

    // Mock for stats
    await page.route('**/api/v1/decisions/statistics/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ 
          symbol: 'RELIANCE',
          total_decisions: 35, 
          days_analyzed: 90, 
          average_conviction: 72 
        }),
      });
    });

    // Mock for timeline
    await page.route('**/api/v1/decisions/conviction-timeline/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ 
          symbol: 'RELIANCE', 
          data_points: [], 
          sample_count: 35, 
          average_conviction: 72, 
          conviction_volatility: 5, 
          bias_consistency: 90, 
          conviction_trend: 'STABLE', 
          recent_bias: 'BULLISH', 
          bias_streak_count: 5 
        }),
      });
    });
  });

  test.describe('Page Load and Initialization', () => {
    test('should load QUAD dashboard and display header', async ({ page }) => {
      await page.goto('/quad');
      // Look for any header that contains QUAD Analytics
      await expect(page.locator('h1:has-text("QUAD Analytics")')).toBeVisible({ timeout: 15000 });
      await expect(page.locator('text=Institutional Multi-Dimensional Reasoning')).toBeVisible();
    });

    test('should have symbol select field with default value', async ({ page }) => {
      await page.goto('/quad');
      const symbolSelect = page.locator('select');
      await expect(symbolSelect).toBeVisible();
      await expect(symbolSelect).toHaveValue('RELIANCE');
    });

    test('should NOT have active analyze button in main layout (auto-fetch)', async ({ page }) => {
      await page.goto('/quad');
      const analyzeButton = page.locator('button:has-text("Analyze")');
      await expect(analyzeButton).not.toBeVisible();
    });
  });

  test.describe('Command Card & Conviction', () => {
    test('should display conviction score and confidence', async ({ page }) => {
      await page.goto('/quad');
      // Wait for data to load
      await expect(page.locator('text=70.2%')).toBeVisible();
      await expect(page.locator('text=HIGH')).toBeVisible();
    });

    test('should display directional bias in large text', async ({ page }) => {
      await page.goto('/quad');
      // Look for the signal text in the CommandCard
      await expect(page.locator('text=BULLISH')).toBeVisible();
      await expect(page.locator('text=QUAD Signal')).toBeVisible();
    });

    test('should show READY status when execution ready', async ({ page }) => {
      await page.goto('/quad');
      await expect(page.locator('text=READY')).toBeVisible();
    });
  });

  test.describe('Pillar Breakdown', () => {
    test('should render pillar names and scores', async ({ page }) => {
      await page.goto('/quad');
      await expect(page.locator('text=Trend').first()).toBeVisible();
      await expect(page.locator('text=Momentum').first()).toBeVisible();
      // Score 50 should be visible for Trend
      await expect(page.locator('text=50').first()).toBeVisible();
    });

    test('should show placeholder indicators for inactive pillars', async ({ page }) => {
      await page.goto('/quad');
      await expect(page.locator('text=PLACEHOLDER').first()).toBeVisible();
    });
  });

  test.describe('Readiness Strip', () => {
    test('should display health metrics', async ({ page }) => {
      await page.goto('/quad');
      await expect(page.locator('text=Historical Depth')).toBeVisible();
      await expect(page.locator('text=Model Accuracy')).toBeVisible();
      await expect(page.locator('text=System State')).toBeVisible();
      await expect(page.locator('text=DEGRADED')).toBeVisible();
    });
  });

  test.describe('User Interactions', () => {
    test('should trigger analysis when symbol is changed', async ({ page }) => {
      await page.goto('/quad');
      
      // Mock for specific symbol to verify fetch
      await page.route('**/api/v1/reasoning/INFY/reasoning', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ ...mockTradeIntentResponse, symbol: 'INFY', directional_bias: 'BEARISH' }),
        });
      });

      const symbolSelect = page.locator('select#symbol');
      await symbolSelect.selectOption('INFY');
      
      // Should show BEARISH signal now (wait for the text to appear)
      await expect(page.locator('text=BEARISH')).toBeVisible({ timeout: 10000 });
    });
  });

  test.describe('Edge Cases', () => {
    test('should handle not execution ready state', async ({ page }) => {
      await page.route('**/api/v1/reasoning/*/reasoning', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockTradeIntentNotReady),
        });
      });

      await page.goto('/quad');
      // "READY" badge should not be visible
      await expect(page.locator('text=READY')).not.toBeVisible();
      await expect(page.locator('text=45.0%')).toBeVisible();
      await expect(page.locator('text=NEUTRAL')).toBeVisible();
    });

    test('should handle failed pillars in readiness strip', async ({ page }) => {
      await page.route('**/api/v1/reasoning/*/reasoning', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockTradeIntentWithFailures),
        });
      });

      await page.goto('/quad');
      // Stability should show FAILED
      await expect(page.locator('text=FAILED')).toBeVisible();
    });
  });
});
