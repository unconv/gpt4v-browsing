const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const url = process.argv[2];
const timeout = 8000;

(async () => {
    const browser = await puppeteer.launch( {
        headless: "new",
    } );

    const page = await browser.newPage();

    await page.setViewport( {
        width: 1200,
        height: 1200,
        deviceScaleFactor: 1,
    } );

    setTimeout(async () => {
        await page.screenshot( {
            path: "screenshot.jpg",
            fullPage: true,
        } );
    }, timeout-2000);

    await page.goto( url, {
        waitUntil: "networkidle0",
        timeout: timeout,
    } );

    await page.screenshot( {
        path: "screenshot.jpg",
        fullPage: true,
    } );

    await browser.close();
})();
