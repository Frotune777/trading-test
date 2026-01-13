const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    const page = await context.newPage();

    const errors = [];
    const warnings = [];
    const failedRequests = [];

    // Capture console messages
    page.on('console', msg => {
        if (msg.type() === 'error') {
            errors.push(msg.text());
        } else if (msg.type() === 'warning') {
            warnings.push(msg.text());
        }
    });

    // Capture page errors
    page.on('pageerror', error => {
        errors.push(`PageError: ${error.message}\n${error.stack}`);
    });

    // Capture failed requests
    page.on('requestfailed', request => {
        failedRequests.push({
            url: request.url(),
            failure: request.failure()?.errorText || 'Unknown error'
        });
    });

    // Capture response errors
    page.on('response', response => {
        if (response.status() >= 400) {
            failedRequests.push({
                url: response.url(),
                status: response.status(),
                statusText: response.statusText()
            });
        }
    });

    try {
        console.log('Navigating to http://localhost:3010/market/quad...');
        await page.goto('http://localhost:3010/market/quad', { waitUntil: 'networkidle', timeout: 30000 });

        console.log('Waiting for page to settle...');
        await page.waitForTimeout(5000);

        // Take screenshot
        await page.screenshot({ path: 'quad-page.png', fullPage: true });
        console.log('Screenshot saved to quad-page.png');

        // Print results
        console.log('\n=== FAILED REQUESTS ===');
        if (failedRequests.length === 0) {
            console.log('No failed requests!');
        } else {
            failedRequests.forEach((req, i) => {
                console.log(`${i + 1}. ${req.url}`);
                console.log(`   Status: ${req.status || 'N/A'} ${req.statusText || req.failure || ''}`);
            });
        }

        console.log('\n=== CONSOLE ERRORS ===');
        if (errors.length === 0) {
            console.log('No console errors!');
        } else {
            errors.forEach((err, i) => console.log(`${i + 1}. ${err}\n`));
        }

        console.log('\n=== WARNINGS ===');
        if (warnings.length === 0) {
            console.log('No warnings!');
        } else {
            warnings.slice(0, 5).forEach((warn, i) => console.log(`${i + 1}. ${warn}`));
            if (warnings.length > 5) {
                console.log(`... and ${warnings.length - 5} more warnings`);
            }
        }

        console.log(`\n=== SUMMARY ===`);
        console.log(`Failed Requests: ${failedRequests.length}`);
        console.log(`Console Errors: ${errors.length}`);
        console.log(`Warnings: ${warnings.length}`);

        // Exit with error code if errors found
        process.exit((errors.length + failedRequests.length) > 0 ? 1 : 0);

    } catch (error) {
        console.error('Test failed:', error);
        process.exit(1);
    } finally {
        await browser.close();
    }
})();
