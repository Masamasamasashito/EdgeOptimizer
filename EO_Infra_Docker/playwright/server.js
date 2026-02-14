const express = require('express');
const { chromium } = require('playwright');
const app = express();
app.use(express.json());

const PlaywrightNpmVer = require('playwright/package.json').version;
console.log(`[EO-Playwright-INFO] Playwright Service Started. PlaywrightNpmVersion: ${PlaywrightNpmVer}`);

// Health check endpoint for Docker
app.get('/healthz', (req, res) => {
    res.status(200).json({ status: 'ok', version: PlaywrightNpmVer });
});

app.post('/content', async (req, res) => {
    const { url } = req.body;
    if (!url) return res.status(400).send('URL is required');

    console.log(`[EO-Playwright-LOG] Processing: ${url}`);
    let browser;
    try {
        // Explicitly set headless mode to verify latest version behavior
        browser = await chromium.launch({ headless: true });
        const page = await browser.newPage();

        // Configured via PLAYWRIGHT_NAVIGATION_TIMEOUT_MS in EO_Infra_Docker/env.example
        const navigationTimeoutMs = parseInt(process.env.PLAYWRIGHT_NAVIGATION_TIMEOUT_MS, 10) || 30000;

        // Phase 1: Wait for 'load' (all synchronous resources ready).
        await page.goto(url, { waitUntil: 'load', timeout: navigationTimeoutMs });

        // Phase 2: Attempt 'networkidle' with a short grace period to capture
        // additional DOM content from SPA / deferred JS rendering.
        // Pages with persistent connections (analytics, ads, chat widgets, web workers)
        // will never reach networkidle, so we cap the wait and proceed with current DOM.
        // Configured via PLAYWRIGHT_NETWORKIDLE_GRACE_MS in EO_Infra_Docker/env.example
        const networkidleGraceMs = parseInt(process.env.PLAYWRIGHT_NETWORKIDLE_GRACE_MS, 10) || 5000;
        try {
            await page.waitForLoadState('networkidle', { timeout: networkidleGraceMs });
        } catch {
            console.log(`[EO-Playwright-INFO] networkidle not reached within ${networkidleGraceMs}ms, proceeding: ${url}`);
        }

        const content = await page.content();
        console.log(`[EO-Playwright-INFO] Successfully processed: ${url}`);
        res.json({ html: content, PlaywrightNpmVersion: PlaywrightNpmVer });
    } catch (error) {
        console.error(`[EO-Playwright-ERROR] Failed to process ${url}: ${error.message}`);
        res.status(500).json({ error: error.message, PlaywrightNpmVersion: PlaywrightNpmVer });
    } finally {
        if (browser) await browser.close();
    }
});

const port = process.env.PLAYWRIGHT_CONTAINER_LISTEN_PORT || 3000;
app.listen(port, () => console.log(`[EO-Playwright-INFO] API Listening on port ${port}`));
