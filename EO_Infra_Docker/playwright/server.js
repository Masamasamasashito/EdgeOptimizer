const express = require('express');
const { chromium } = require('playwright');
const app = express();
app.use(express.json());

const PlaywrightNpmVer = require('playwright/package.json').version;
console.log(`[EO-INFO] Playwright Service Started. PlaywrightNpmVersion: ${PlaywrightNpmVer}`);

// Health check endpoint for Docker
app.get('/healthz', (req, res) => {
    res.status(200).json({ status: 'ok', version: PlaywrightNpmVer });
});

app.post('/content', async (req, res) => {
    const { url } = req.body;
    if (!url) return res.status(400).send('URL is required');

    console.log(`[EO-LOG] Processing: ${url}`);
    let browser;
    try {
        // Explicitly set headless mode to verify latest version behavior
        browser = await chromium.launch({ headless: true });
        const page = await browser.newPage();

        // Timeout settings can be received from n8n or use default values
        await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });

        const content = await page.content();
        console.log(`[EO-INFO] Successfully processed: ${url}`);
        res.json({ html: content, PlaywrightNpmVersion: PlaywrightNpmVer });
    } catch (error) {
        console.error(`[EO-ERROR] Failed to process ${url}: ${error.message}`);
        res.status(500).json({ error: error.message, PlaywrightNpmVersion: PlaywrightNpmVer });
    } finally {
        if (browser) await browser.close();
    }
});

const port = process.env.PLAYWRIGHT_CONTAINER_LISTEN_PORT || 3000;
app.listen(port, () => console.log(`[EO-INFO] API Listening on port ${port}`));
