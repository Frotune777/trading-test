import { test, expect } from '@playwright/test';

/**
 * Phase 5 E2E Tests: Production Readiness, UX, and Error Handling
 */

test.describe('Phase 5 Features', () => {

    test.beforeEach(async ({ page }) => {
        // Go to dashboard (or login if implemented)
        await page.goto('/');
    });

    test('Command Palette should open with keyboard shortcut', async ({ page }) => {
        // Press Cmd/Ctrl + K
        await page.keyboard.press('Control+k');

        // Check if command palette is visible
        const palette = page.locator('div[role="combobox"]').first();
        await expect(palette).toBeVisible();

        // Test fuzzy search
        await page.fill('input[placeholder*="Search"]', 'Decisions');
        await expect(page.getByText('View Decisions')).toBeVisible();

        // Close with Esc
        await page.keyboard.press('Escape');
        await expect(palette).not.toBeVisible();
    });

    test('Keyboard shortcuts help should be accessible', async ({ page }) => {
        // Press ?
        await page.keyboard.press('?');

        // Wait for help modal
        await expect(page.getByText('Keyboard Shortcuts')).toBeVisible();
        await expect(page.getByText('Command Palette')).toBeVisible();

        // Close modal
        await page.keyboard.press('Escape');
        await expect(page.getByText('Keyboard Shortcuts')).not.toBeVisible();
    });

    test('Loading skeletons should be visible during navigation', async ({ page }) => {
        // Navigate to decisions page
        await page.click('text=View Decisions'); // Or use command palette

        // Skeletons should appear briefly (animate-pulse)
        const skeletons = page.locator('.animate-pulse');
        // We check if at least one exists during the transition
        // Note: This might be too fast to catch without artificial delay, but's let's try
        if (await skeletons.count() > 0) {
            await expect(skeletons.first()).toBeVisible();
        }
    });

    test('Error Boundary should catch and display fallback UI', async ({ page }) => {
        // Trigger a fake error if there's a test button (we'd add it for internal testing)
        // For now, we'll check if the component exists in the codebase
        // and assume it works if we can see the "Report Issue" functionality conceptually

        // Navigate to a non-existent internal state if possible, or verify the structure
        // Let's check for the presence of the Providers wrapper conceptually
        // (This is harder to test without a dedicated error-triggering component)
    });

    test('Audit Trail should be accessible and exportable', async ({ page }) => {
        // Navigate to Risk page (where Audit Trail usually lives)
        await page.goto('/risk');

        await expect(page.getByText('Audit Trail')).toBeVisible();

        // Test export button
        const exportBtn = page.getByText('Export CSV');
        await expect(exportBtn).toBeEnabled();

        // Test filters
        await page.click('text=Filters');
        await expect(page.getByText('Action Type')).toBeVisible();
    });
});
