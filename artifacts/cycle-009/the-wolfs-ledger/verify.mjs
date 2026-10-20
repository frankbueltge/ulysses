// Drive The Wolf's Ledger in a real browser at two widths and check it against plate1.json. Node + playwright.
import { createRequire } from 'module'; import path from 'path'; import fs from 'fs'; import { fileURLToPath } from 'url';
const require = createRequire('/opt/node-tools/node_modules/'); const { chromium } = require('playwright');
const here = path.dirname(fileURLToPath(import.meta.url)); let bad = 0;
const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) bad++; };
const P = JSON.parse(fs.readFileSync(path.join(here, 'plate1.json')));
const P2 = JSON.parse(fs.readFileSync(path.join(here, 'plate2.json')));
const br = await chromium.launch({ executablePath: process.env.CHROMIUM || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--no-sandbox'] });
for (const [wd, scheme] of [[390, 'light'], [1100, 'dark']]) {
  const pg = await br.newPage({ viewport: { width: wd, height: 900 }, colorScheme: scheme }); const errs = [];
  pg.on('pageerror', e => errs.push(String(e))); pg.on('console', m => m.type() === 'error' && errs.push(m.text()));
  await pg.goto('file://' + path.join(here, 'index.html'));
  const t = id => pg.innerText('#' + id), p1 = () => pg.evaluate(() => window.__p1), near = (a, b) => Math.abs(a - b) < 1e-6;
  ok(await pg.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `${wd}px: no horizontal page scroll`);
  ok(await pg.evaluate(() => window.__p1check()), `${wd}px: the browser's village recomputes plate1.json's fifth cry for all three ledgers and both boys`);
  let j = await p1(); const F = P.model.fifth_cry;
  ok(near(j.b, F['came+wolf'].watcher) && !j.come && (await t('read')).includes('stays home'), `${wd}px: default ledger (came, wolf?) leaves the watcher's fifth cry at ${F['came+wolf'].watcher.toFixed(3)}, below t`);
  await pg.click('#c-words'); j = await p1();
  ok(near(j.b, P.model.defaults.p) && j.come, `${wd}px: with his words kept, the watcher is believed at p and the village comes`);
  for (const k of [0, 8]) { await pg.$eval('#s-k', (e, v) => { e.value = v; e.dispatchEvent(new Event('input')); }, k); j = await p1();
    ok(near(j.b, P.model.defaults.p), `${wd}px: with words, after ${k} empty cries the watcher is still believed at p (P3)`); }
  await pg.click('#b-hoax'); j = await p1();
  ok(near(j.b, P.model.defaults.w) && !j.come && (await t('read')).includes('liar is not believed'), `${wd}px: with words, the hoaxer is believed at w (the fable's moral)`);
  await pg.click('#c-words'); await pg.click('#c-wolf'); await pg.click('#b-watch');
  await pg.$eval('#s-k', e => { e.value = 4; e.dispatchEvent(new Event('input')); }); j = await p1();
  ok(near(j.b, F.came.watcher) && j.come, `${wd}px: a ledger that keeps only "came" believes the watcher at ${F.came.watcher} and comes`);
  ok(near(j.hab, P.model.habit_by_k[4] * F.came.watcher), `${wd}px: the habituated village reads the count only`);
  ok(await pg.$$eval('#ledger tr', r => r.length) === 6, `${wd}px: the ledger shows four empty cries and the next`);
  const px = await pg.$eval('#curve', e => { const d = e.getContext('2d').getImageData(0, 0, e.width, e.height).data; let n = 0; for (let i = 3; i < d.length; i += 4) n += d[i] > 0; return n; });
  ok(px > 1500, `${wd}px: the curves are drawn`);
  ok(await pg.$$eval('#cards .card', c => c.length) === 21 && await pg.$$eval('#cards .card[data-cls=hoax]', c => c.length) === 0, `${wd}px: 21 retractions, none a hoax (P1)`);
  ok((await t('n-error')) === String(P.archive.classes.error) && (await t('n-bare')) === String(P.archive.classes.bare), `${wd}px: class counts filled from plate1.json`);
  const hi = P.archive.rows.findIndex(r => r.r === 664); await pg.click(`#cards .card[data-i="${hi}"]`);
  ok((await t('cread')).includes('BALLISTIC MISSILE') && (await t('cread')).includes('38 minutes'), `${wd}px: the Hawaii retraction shows the warning it takes back`);
  const si = P.archive.rows.findIndex(r => r.r === 1894); await pg.click(`#cards .card[data-i="${si}"]`);
  ok((await t('cread')).includes('speaks to those who acted'), `${wd}px: the ShakeAlert retraction speaks to those who acted`);
  // plate II
  ok(await pg.evaluate(() => window.__p2check()), `${wd}px: the browser recounts the runs before every hit in the ${P2.counties_shown} counties it holds, as plate2.py did`);
  let q = await pg.evaluate(() => window.__p2);
  ok(q.county === P2.longest_run.county && !q.dealt && (await t('p2-read')).includes('Brevard'), `${wd}px: plate II opens on the longest run, Brevard County`);
  const rec = q, yr = JSON.stringify(q.perYear);
  await pg.click('#p2-deal'); q = await pg.evaluate(() => window.__p2);
  ok(q.dealt && JSON.stringify(q.perYear) === yr && q.met === rec.met && Math.abs(q.rec - rec.charge) < 1e-12, `${wd}px: a deal keeps every year's hits and changes only their order`);
  let moved = false; for (let i = 0; i < 6 && !moved; i++) { await pg.click('#p2-deal'); q = await pg.evaluate(() => window.__p2); moved = Math.abs(q.charge - rec.charge) > 1e-9; }
  ok(moved && (await t('p2-read')).includes('Dealt again'), `${wd}px: dealing again moves the charge (${rec.charge.toFixed(3)} -> ${q.charge.toFixed(3)})`);
  await pg.click('#p2-rec'); q = await pg.evaluate(() => window.__p2); ok(!q.dealt && Math.abs(q.charge - rec.charge) < 1e-12, `${wd}px: the record's order restores the charge`);
  await pg.click('#p2-any'); q = await pg.evaluate(() => window.__p2); ok(q.n >= 20, `${wd}px: any county draws a county with at least 20 warnings`);
  await pg.$eval('#p2-h', e => { e.value = 0.9; e.dispatchEvent(new Event('input')); }); ok((await t('p2-hv')) === '0.90', `${wd}px: the habit slider redraws`);
  ok((await t('p2f-a3')) === '9,427' && (await t('p2f-obs')) === '31.3 %' && (await t('p2f-off')) === (100 * P2.results.between_office_share).toFixed(1) + ' %' && (await t('p2f-luck')) === (100 * P2.results.luck_share).toFixed(1) + ' %', `${wd}px: plate II figures filled from plate2.json`);
  ok(!P2.predictions.P1 && !P2.predictions.P2 && P2.predictions.P3 && (await t('p2f-r2')) === (100 * P2.results.r2_rate).toFixed(1) + ' %', `${wd}px: the page reports P1 and P2 failed and P3 held, as plate2.json says`);
  for (const id of ['p2-strip', 'p2-hist']) { const n = await pg.$eval('#' + id, e => { const d = e.getContext('2d').getImageData(0, 0, e.width, e.height).data; let n = 0; for (let i = 3; i < d.length; i += 4) n += d[i] > 0; return n; }); ok(n > 1500, `${wd}px: ${id} is drawn`); }
  ok(await pg.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `${wd}px: still no horizontal scroll after use`);
  await pg.screenshot({ path: path.join(here, `shot-${wd}.png`), fullPage: false });
  ok(errs.length === 0, `${wd}px: no script errors ${errs.join(' | ')}`);
  await pg.close();
}
await br.close(); console.log(bad ? `${bad} FAILED` : 'all passed'); process.exit(bad ? 1 : 0);
