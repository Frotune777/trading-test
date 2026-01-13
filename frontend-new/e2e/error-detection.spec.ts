import { test, expect } from '@playwright/test';

test.describe('QUAD Page Error Detection', () => {
    const consoleErrors: string[] = [];
    const consoleWarnings: string[] = [];

    test.beforeEach(async ({ page }) => {
        // Capture console errors
        page.on('console', msg => {
            if (msg.type() === 'error') {
                consoleErrors.push(msg.text());
            } else if (msg.type() === 'warning') {
                consoleWarnings.push(msg.text());
            }
        });

        // Capture page errors
        page.on('pageerror', error => {
            consoleErrors.push(`Page Error: ${error.message}`);
        });
    });

    test('should load QUAD page and check for errors', async ({ page }) => {
        // Navigate to QUAD page
        await page.goto('http://localhost:3010/quad');

        // Wait for page to load
        await page.waitForLoadState('networkidle');

        // Wait a bit for any async errors
        await page.waitForTimeout(3000);

        // Log all errors
        console.log('\\n=== CONSOLE ERRORS ===');
        consoleErrors.forEach(err => console.log(err));

        console.log('\\n=== CONSOLE WARNINGS ===');
        consoleWarnings.forEach(warn => console.log(warn));

        // Take a screenshot
        await page.screenshot({ path: 'quad-page-errors.png', fullPage: true });

        // Check if page loaded
        const title = await page.title();
        console.log(`\\nPage Title: ${title}`);

        // Print summary
        console.log(`\\n=== SUMMARY ===`);
        console.log(`Total Errors: ${consoleErrors.length}`);
        console.log(`Total Warnings: ${consoleWarnings.length}`);
    });
});
