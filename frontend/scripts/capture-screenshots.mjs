import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';

const baseUrl = process.env.FLOWFORGE_URL || 'http://localhost:5173';
const outputDir = resolve(process.cwd(), '../portfolio');
await mkdir(outputDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({
  viewport: { width: 1440, height: 1000 },
  deviceScaleFactor: 1,
});

await page.goto(`${baseUrl}/?demo=1`, { waitUntil: 'networkidle' });
await page.screenshot({ path: resolve(outputDir, 'flowforge-dashboard.png'), fullPage: true });

await page.getByRole('button', { name: 'History' }).first().click();
await page.waitForLoadState('networkidle');
await page.screenshot({ path: resolve(outputDir, 'flowforge-executions.png'), fullPage: true });

await browser.close();
console.log(`Screenshots saved in ${outputDir}`);
