// Frame renderer: node render.js <build/index.html> <outDir> <W> <H> <fps> <startFrame> <endFrame>
//                 node render.js <build/index.html> <outDir> <W> <H> stills t1 t2 ...
const { chromium } = require('playwright');
const path = require('path'); const fs = require('fs');
(async () => {
  const [, , html, out, w, h, mode, ...rest] = process.argv;
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--force-color-profile=srgb', '--disable-web-security'] });
  const page = await browser.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.log('ERR', e.message));
  page.on('console', m => { if (m.type() === 'error') console.log('CONSOLE', m.text()); });
  await page.goto('file://' + path.resolve(html));
  await page.evaluate(() => document.fonts.ready);
  fs.mkdirSync(out, { recursive: true });
  let jobs = [];
  if (mode === 'stills') jobs = rest.map(t => [+t, `still_${(+t).toFixed(2)}.jpg`]);
  else { const fps = +mode, a = +rest[0], b = +rest[1]; for (let i = a; i < b; i++) jobs.push([i / fps, `f${String(i).padStart(5, '0')}.jpg`]); }
  const t0 = Date.now(); let k = 0;
  for (const [t, name] of jobs) {
    await page.evaluate(t => window.renderAt(t), t);
    await page.screenshot({ path: path.join(out, name), type: 'jpeg', quality: 92 });
    if (++k % 100 === 0) console.log(k, 'frames', ((Date.now() - t0) / k).toFixed(0), 'ms/f');
  }
  await browser.close();
})();
