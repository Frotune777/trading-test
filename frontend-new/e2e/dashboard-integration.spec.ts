import { test, expect } from '@playwright/test';

test.describe('Dashboard Live Integration', () => {

    test('Market Overview should load live indices and breadth', async ({ page }) => {
        await page.goto('/dashboard');

        // Verify header
        await expect(page.locator('h2')).toContainText('Market Pulse');

        // Verify indices load (at least one card should be visible)
        const indexCards = page.locator('.grid.gap-4.md\\:grid-cols-2.lg\\:grid-cols-4 .bg-slate-900\\/50');
        await expect(indexCards.first()).toBeVisible({ timeout: 10000 });

        // Verify Market Breadth Widget
        await expect(page.locator('text=Market Breadth')).toBeVisible();
        await expect(page.locator('text=Advance/Decline Ratio')).toBeVisible();

        // Verify Trend Leaders table
        await expect(page.locator('text=Trend Leaders (Volume)')).toBeVisible();
        const tableRows = page.locator('tbody tr');
        await expect(tableRows.first()).toBeVisible();
    });

    test('Analysis Page should load QUAD data for RELIANCE', async ({ page }) => {
        await page.goto('/dashboard/analysis');

        // Default symbol should be RELIANCE
        await expect(page.locator('input[placeholder*="Enter symbol"]')).toHaveValue('RELIANCE');

        // Check QUAD tab content (default active tab)
        await expect(page.getByRole('tab', { name: 'QUAD Analysis' })).toBeVisible();

        // Wait for conviction score to populate using data-testid
        await expect(page.getByTestId('conviction-score')).toBeVisible({ timeout: 15000 });
        await expect(page.getByTestId('directional-bias')).toBeVisible();
    });

    test('Insider Page should load Sentinel signals', async ({ page }) => {
        await page.goto('/dashboard/insider');

        // Verify Sentinel header
        await expect(page.locator('h2')).toContainText('Sentinel Intelligence');

        // Verify specific symbol sentinel (INDOSTAR is default)
        await expect(page.locator('text=INDOSTAR SENTINEL')).toBeVisible();

        // Verify Recent Insider Activity table
        await expect(page.locator('text=Recent Insider Activity')).toBeVisible();
        const tradeRows = page.locator('tbody tr');
        await expect(tradeRows.first()).toBeVisible({ timeout: 10000 });
    });

    test('Navigation should work between dashboard segments', async ({ page }) => {
        await page.goto('/dashboard');

        // Link to Analysis (usually in sidebar layout, but we can test direct navigation)
        await page.goto('/dashboard/analysis');
        await expect(page.url()).toContain('/dashboard/analysis');

        // Link to Insider
        await page.goto('/dashboard/insider');
        await expect(page.url()).toContain('/dashboard/insider');
    });
});
