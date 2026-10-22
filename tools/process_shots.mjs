// Render a work's committed states to process/<n>.png, 1100 px wide, full page (amendment of 2026-10-22, point 5).
// Each state is the work's folder exactly as one commit left it, exported with `git archive`, opened from file://.
// Usage: node tools/process_shots.mjs <work-folder-in-repo> <out-dir> <commit> [<commit> ...]   (run at the repo root)
import { createRequire } from 'module'; import { execSync } from 'child_process'; import fs from 'fs'; import path from 'path'; import os from 'os';
const require = createRequire('/opt/node-tools/node_modules/'); const { chromium } = require('playwright');
const [work, out, ...commits] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1100, height: 900 }, colorScheme: 'light' });
for (const [i, c] of commits.entries()) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'state-'));
  execSync(`git archive ${c} ${work} | tar -x -C ${dir}`);
  await page.goto('file://' + path.join(dir, work, 'index.html'));
  await page.waitForTimeout(1500);
  const file = path.join(out, `${i + 1}.png`);
  await page.screenshot({ path: file, fullPage: true });
  const h = await page.evaluate(() => document.documentElement.scrollHeight);
  console.log(`${i + 1} ${c} height ${h}px ${fs.statSync(file).size} bytes`);
}
await browser.close();
