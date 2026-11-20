/* bassam-reel engine — one beat-locked timeline, scenes as pure functions of time.
 * Data comes from data.js (window.REEL), written by build.py from reel.json.
 * Every visual is computed from t, so any frame can be rendered in any order. */
(() => {
const R = window.REEL;
const W = R.format.w, H = R.format.h, FPS = R.format.fps || 25;
const BPM = R.bpm || 129, BEAT = 60 / BPM;
const M = Math.min(W, H), U = M / 1080, VERT = H > W;
const C = Object.assign({
  cream: '#ECE6DA', paper: '#F4F2EE', ink: '#151515', black: '#050505', white: '#FFFFFF',
  accent: '#7B5CFF', red: '#E8412C', orange: '#F07A3A', lilac: '#B9A9F0', blue: '#5A7BEA', yellow: '#F1B91A', pink: '#E58BB0'
}, R.theme || {});
const F = {
  sans: "'IBM Plex Sans Arabic',sans-serif", display: "'Alexandria',sans-serif", kufi: "'Reem Kufi Fun',sans-serif",
  naskh: "'Amiri',serif", ruqaa: "'Aref Ruqaa',serif", readex: "'Readex Pro',sans-serif",
  serif: "'Newsreader','Noto Naskh Arabic',serif", mono: "'IBM Plex Mono','IBM Plex Sans Arabic',monospace", grotesk: "'Space Grotesk','Readex Pro',sans-serif", naskh2: "'Noto Naskh Arabic',serif"
};
const font = k => F[k] || k || F.display;

/* ---------- math & easing ---------- */
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, t) => a + (b - a) * t;
const P = (t, s, d) => clamp((t - s) / d);
function bez(x1, y1, x2, y2) { return x => { if (x <= 0) return 0; if (x >= 1) return 1; let t = x; for (let i = 0; i < 8; i++) { const cx = 3*x1*t*(1-t)**2 + 3*x2*t*t*(1-t) + t**3 - x, d = 3*x1*(1-t)**2 + 6*(x2-x1)*t*(1-t) + 3*(1-x2)*t*t; if (Math.abs(d) < 1e-6) break; t = clamp(t - cx / d); } return 3*y1*t*(1-t)**2 + 3*y2*t*t*(1-t) + t**3; }; }
const E = {
  sk: bez(.2, .8, .2, 1), snap: bez(.7, 0, .2, 1), lin: t => t,
  oE: t => t >= 1 ? 1 : 1 - Math.pow(2, -10 * t), iE: t => t <= 0 ? 0 : Math.pow(2, 10 * t - 10),
  io: t => t < .5 ? 4 * t ** 3 : 1 - (-2 * t + 2) ** 3 / 2, oC: t => 1 - (1 - t) ** 3, iC: t => t ** 3,
  ioE: t => t <= 0 ? 0 : t >= 1 ? 1 : t < .5 ? Math.pow(2, 20 * t - 10) / 2 : (2 - Math.pow(2, -20 * t + 10)) / 2,
  oB: t => { const c = 1.7; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2; },
  oEl: t => t <= 0 ? 0 : t >= 1 ? 1 : Math.pow(2, -10 * t) * Math.sin((t * 10 - .75) * (2 * Math.PI / 3)) + 1
};
const hash = n => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
const rnd = seed => { let s = seed >>> 0 || 1; return () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296; };
const lum = c => { const m = /^#?([\da-f]{2})([\da-f]{2})([\da-f]{2})/i.exec(c || ''); if (!m) return 0; const [r, g, b] = [1, 2, 3].map(i => parseInt(m[i], 16) / 255); return .2126 * r + .7152 * g + .0722 * b; };
const isDark = c => lum(c) < .45;
const px = n => (n * U) + 'px';
const fmt = n => Math.round(n).toLocaleString('en-US');

/* ---------- DOM helpers ---------- */
const stage = document.getElementById('stage');
stage.style.width = W + 'px'; stage.style.height = H + 'px';
document.documentElement.style.width = document.body.style.width = W + 'px';
document.documentElement.style.height = document.body.style.height = H + 'px';
const bidi = t => String(t).replace(/([\u0600-\u06FF]+[²³])/g, '\u2068$1\u2069').replace(/[+\-]?[\d\u0660-\u0669][\d\u0660-\u0669,.%]*/g, m => `<span class="num">${m}</span>`);
function el(tag, css = {}, parent, html) { const e = document.createElement(tag); Object.assign(e.style, css); if (html !== undefined) e.innerHTML = bidi(html); if (parent) parent.append(e); return e; }
function svgEl(tag, attrs = {}, parent) { const e = document.createElementNS('http://www.w3.org/2000/svg', tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.append(e); return e; }
function svg(parent, vb = `0 0 ${W} ${H}`, css = {}) { const s = svgEl('svg', { viewBox: vb, preserveAspectRatio: 'xMidYMid meet' }); Object.assign(s.style, { position: 'absolute', left: 0, top: 0, width: '100%', height: '100%', overflow: 'visible' }, css); parent.append(s); return s; }
function fx(e, { o = 1, x = 0, y = 0, s = 1, r = 0, b = 0, sx = null } = {}) {
  e.style.opacity = o;
  e.style.transform = `translate(${x}px,${y}px) scale(${s})${sx !== null ? ` scaleX(${sx})` : ''} rotate(${r}deg)`;
  e.style.filter = b > .05 ? `blur(${b.toFixed(2)}px)` : 'none';
}
function dash(p, k) { const L = p.getTotalLength ? p.getTotalLength() : 1000; p.style.strokeDasharray = L; p.style.strokeDashoffset = L * (1 - k); }
function splitWords(e, text) { e.innerHTML = ''; text.split(/(\s+)/).forEach(w => { if (!w) return; if (/^\s+$/.test(w)) { e.append(' '); return; } const m = el('span', { display: 'inline-block', overflow: 'hidden', padding: '.12em .06em .24em', margin: '-.12em -.06em -.24em', verticalAlign: 'bottom' }, e); el('span', { display: 'inline-block', willChange: 'transform' }, m, w).className = 'w'; }); return [...e.querySelectorAll('.w')]; }
function rise(ws, b, s, st = .25, d = 1, outS = null) { ws.forEach((w, k) => { const p = E.sk(P(b, s + k * st, d)); let y = (1 - p) * 115, bl = (1 - p) * 8; if (outS !== null) { const q = E.iC(P(b, outS + k * st * .4, .6)); y -= q * 115; bl += q * 10; } w.style.transform = `translateY(${y}%)`; w.style.filter = bl > .05 ? `blur(${bl}px)` : 'none'; }); }
function blurIn(e, b, s, d = 1, extra = {}) { const p = E.sk(P(b, s, d)); fx(e, Object.assign({ o: p, b: (1 - p) * 14 * U, s: lerp(1.08, 1, p) }, extra)); return p; }
function typeClip(e, p, steps = 14) { const q = Math.floor(clamp(p) * steps) / steps; e.style.clipPath = `inset(-30% 0 -40% ${(1 - q) * 100}%)`; }

/* ---------- media (images + extracted video frame sequences) ---------- */
function media(parent, item, css = {}) {
  const im = el('img', Object.assign({ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', display: 'block' }, css), parent);
  const it = typeof item === 'string' ? { src: item } : (item || {});
  if (it.src) im.src = it.src;
  if (it.pos) im.style.objectPosition = it.pos;
  let last = '';
  return { el: im, set(sec) { if (!it.seq) return; const f = clamp(Math.floor((sec * (it.speed || 1) + (it.start || 0)) * it.fps), 0, it.n - 1); const s = `${it.seq}/${String(f + 1).padStart(5, '0')}.jpg`; if (s !== last) { im.src = s; last = s; } } };
}

/* ---------- small vector library ---------- */
const ICON = {
  thumb: 'M2 10h4v11H2zM8 21h9.2c1 0 1.9-.7 2.1-1.7l1.6-7.3c.3-1.3-.7-2.5-2-2.5H14l.9-4.3c.2-1-.3-2-1.2-2.4L13 2.5 8 9z',
  yt: 'M21.6 7.2c-.2-.9-.9-1.6-1.8-1.8C18.2 5 12 5 12 5s-6.2 0-7.8.4c-.9.2-1.6.9-1.8 1.8C2 8.8 2 12 2 12s0 3.2.4 4.8c.2.9.9 1.6 1.8 1.8C5.8 19 12 19 12 19s6.2 0 7.8-.4c.9-.2 1.6-.9 1.8-1.8.4-1.6.4-4.8.4-4.8s0-3.2-.4-4.8zM10 15V9l5.2 3z',
  ig: 'M7 2h10a5 5 0 0 1 5 5v10a5 5 0 0 1-5 5H7a5 5 0 0 1-5-5V7a5 5 0 0 1 5-5zm0 2a3 3 0 0 0-3 3v10a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3V7a3 3 0 0 0-3-3zm5 3.5a4.5 4.5 0 1 1 0 9 4.5 4.5 0 0 1 0-9zm0 2a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5zM17.5 5.5a1 1 0 1 1 0 2 1 1 0 0 1 0-2z',
  tt: 'M16.5 2c.3 2.4 1.7 3.9 4 4v3.2c-1.5.1-2.8-.4-4-1.2v6.5c0 3.9-3.3 6.5-6.9 5.9-2.6-.4-4.6-2.6-4.6-5.4 0-3.6 3.4-6.3 7-5.4v3.4c-1.6-.6-3.6.4-3.6 2.2 0 1.3 1.1 2.3 2.4 2.3 1.4 0 2.4-1.1 2.4-2.6V2z',
  x: 'M3 3h5l4.3 6 5.2-6H20l-6.4 7.4L21 21h-5l-4.6-6.4L5.8 21H3.4l6.9-7.9z',
  snap: 'M12 2.5c3.4 0 5.6 2.6 5.5 5.7l-.1 2.2c.6.2 1.4-.4 1.9.1.5.6-.4 1.4-1.6 1.9.4 1.5 2 2.8 3.3 3.2-.2 1-1.9 1.1-2.6 1.3-.3.8-.3 1.3-1.4 1.1-1.3-.3-2.1 0-3.1.8-1.1.8-2.7.8-3.8 0-1-.8-1.8-1.1-3.1-.8-1.1.2-1.1-.3-1.4-1.1-.7-.2-2.4-.3-2.6-1.3 1.3-.4 2.9-1.7 3.3-3.2-1.2-.5-2.1-1.3-1.6-1.9.5-.5 1.3.1 1.9-.1l-.1-2.2C6.4 5.1 8.6 2.5 12 2.5z',
  play: 'M8 5v14l11-7z', heart: 'M12 21s-8-5.2-8-11a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20 10c0 5.8-8 11-8 11z',
  star: 'M12 0c.6 6.5 5.5 11.4 12 12-6.5.6-11.4 5.5-12 12-.6-6.5-5.5-11.4-12-12C6.5 11.4 11.4 6.5 12 0z',
  person: 'M12 2.2a2.3 2.3 0 1 1 0 4.6 2.3 2.3 0 0 1 0-4.6zM9.6 8h4.8c1 0 1.8.8 1.8 1.8V16h-1.5v6.5h-2V17h-1.4v5.5h-2V16H7.8V9.8C7.8 8.8 8.6 8 9.6 8z'
};
function icon(parent, name, size, color, css = {}) { const s = svgEl('svg', { viewBox: '0 0 24 24' }); Object.assign(s.style, { position: 'absolute', width: size + 'px', height: size + 'px', overflow: 'visible' }, css); svgEl('path', { d: ICON[name] || ICON.star, fill: color }, s); parent.append(s); return s; }

/* faux-3D iridescent chrome text (the "70" look) */
function chromeText(parent, text, size, fam) {
  const box = el('div', { position: 'absolute', left: 0, top: 0, width: '100%', height: '100%' }, parent);
  const s = svg(box); const id = 'g' + Math.floor(Math.random() * 1e9);
  const defs = svgEl('defs', {}, s);
  const g = svgEl('linearGradient', { id, x1: 0, y1: 0, x2: 1, y2: 1 }, defs);
  [['0', '#ff2d6f'], ['.18', '#ff9a1f'], ['.34', '#ffe44d'], ['.5', '#3de0ff'], ['.66', '#6a4dff'], ['.82', '#ff3dd2'], ['1', '#ff2d6f']].forEach(([o, c]) => svgEl('stop', { offset: o, 'stop-color': c }, g));
  const layers = [];
  const N = 16;
  for (let i = N; i >= 0; i--) {
    const tx = svgEl('text', { x: W / 2, y: H / 2, 'text-anchor': 'middle', 'dominant-baseline': 'central', 'font-size': size, 'font-family': fam || F.display, 'font-weight': 900 }, s);
    tx.textContent = text; tx.style.direction = 'ltr';
    if (i === 0) { tx.setAttribute('fill', `url(#${id})`); tx.setAttribute('stroke', 'rgba(255,255,255,.85)'); tx.setAttribute('stroke-width', size * .012); }
    else { tx.setAttribute('fill', `url(#${id})`); tx.style.filter = `brightness(${.35 + .5 * (1 - i / N)})`; }
    layers.push([tx, i]);
  }
  return { el: box, set(t, depth = 1) { g.setAttribute('gradientTransform', `rotate(${(t * 40) % 360} .5 .5)`); layers.forEach(([tx, i]) => { tx.setAttribute('transform', `translate(${i * size * .006 * depth},${i * size * .009 * depth})`); }); } };
}

/* ---------- persistent editorial chrome ---------- */
const ch = el('div', {}, stage); ch.id = 'chrome';
const MX = VERT ? .08 * W : .109 * W, TY = VERT ? .075 * H : .117 * H, BY = VERT ? .93 * H : .876 * H, FS = 22 * U;
const tl = el('div', { left: MX + 'px', top: (TY - FS * .7) + 'px', fontSize: FS + 'px' }, ch); tl.className = 't num';
const tr = el('div', { right: MX + 'px', top: (TY - FS * .7) + 'px', fontSize: FS + 'px' }, ch); tr.className = 't num';
const rule = el('div', { left: (MX + FS * 4.2) + 'px', right: (MX + FS * 4.2) + 'px', top: TY + 'px' }, ch); rule.className = 'rule';
const bl = el('div', { left: MX + 'px', top: (BY - FS * .7) + 'px', fontSize: FS + 'px' }, ch); bl.className = 't';
const br = el('div', { right: MX + 'px', top: (BY - FS * .7) + 'px', fontSize: FS + 'px' }, ch); br.className = 't';
const CH = R.chrome || {};
tl.textContent = CH.left ?? '2025'; tr.textContent = CH.right ?? '2026';
function setChrome(on, dark, label, role) {
  ch.style.display = on ? 'block' : 'none'; if (!on) return;
  const c = dark ? 'rgba(255,255,255,.78)' : 'rgba(20,20,20,.78)';
  [tl, tr, bl, br].forEach(e => e.style.color = c); rule.style.background = dark ? 'rgba(255,255,255,.35)' : 'rgba(20,20,20,.45)';
  bl.innerHTML = bidi(label || ''); br.innerHTML = bidi(role || '');
}

/* ---------- grain ---------- */
const gr = el('div', {}, stage); gr.id = 'grain';
{ const cv = document.createElement('canvas'); cv.width = cv.height = 256; const x = cv.getContext('2d'), d = x.createImageData(256, 256), r = rnd(7); for (let i = 0; i < d.data.length; i += 4) { const v = 128 + (r() - .5) * 180; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; } x.putImageData(d, 0, 0); gr.style.backgroundImage = `url(${cv.toDataURL()})`; gr.style.opacity = R.grain ?? .07; }
const FILM = R.look === 'film';
const vig = el('div', { position: 'absolute', inset: 0, zIndex: 58, pointerEvents: 'none', background: 'radial-gradient(ellipse at 50% 50%,transparent 62%,rgba(0,0,0,.32) 100%)', display: FILM ? 'block' : 'none' }, stage);
const halo = el('div', { position: 'absolute', inset: 0, zIndex: 57, pointerEvents: 'none', mixBlendMode: 'soft-light', background: 'linear-gradient(180deg,rgba(255,170,90,.10),rgba(40,60,90,.12))', display: FILM ? 'block' : 'none' }, stage);
const dust = svg(stage, `0 0 ${W} ${H}`, { zIndex: 59, pointerEvents: 'none', display: FILM ? 'block' : 'none' }); const dustDots = []; { const r = rnd(21); for (let i = 0; i < 14; i++) dustDots.push(svgEl('ellipse', { rx: (1 + r() * 3) * U, ry: (1 + r() * 9) * U, fill: r() < .5 ? '#fff' : '#000', opacity: 0 }, dust)); }
const flash = el('div', {}, stage); flash.id = 'flash';
const fade = el('div', {}, stage); fade.id = 'fade';

/* =====================================================================
 * SCENES — each returns { update(b, sec) -> {dark?} }, b = local beats
 * ===================================================================== */
const S = {};

/* hook: question words one per beat, then a giant chrome number */
S.hook = (root, s) => {
  const parts = (s.words || []).map(w => {
    const box = el('div', { position: 'absolute', inset: 0, display: 'none', background: w.bg || C.black }, root);
    const t = el('div', { position: 'absolute', left: '50%', top: '50%', whiteSpace: 'nowrap', fontFamily: font(w.font || 'ruqaa'), fontSize: px(w.size || 300), fontWeight: w.weight || 700, color: w.fg || (isDark(w.bg || C.black) ? '#fff' : C.ink), lineHeight: 1.3 }, box, w.t);
    return { w, box, t, beats: w.beats || 1 };
  });
  let big = null, bigBox = null, sub = null;
  if (s.big) {
    bigBox = el('div', { position: 'absolute', inset: 0, display: 'none', background: s.bigBg || C.black }, root);
    big = chromeText(bigBox, s.big, (s.bigSize || 820) * U, font(s.bigFont || 'display'));
    if (s.bigSub) sub = el('div', { position: 'absolute', left: '50%', top: '50%', color: '#fff', fontFamily: F.display, fontWeight: 800, fontSize: px(s.bigSubSize || 150), textShadow: `0 ${px(8)} ${px(30)} rgba(0,0,0,.6)`, whiteSpace: 'nowrap' }, bigBox, s.bigSub);
  }
  return { update(b) {
    let acc = 0, dark = true;
    parts.forEach(p => {
      const on = b >= acc && b < acc + p.beats; p.box.style.display = on ? 'block' : 'none';
      if (on) { const lb = b - acc; dark = isDark(p.w.bg || C.black);
        if (p.w.style === 'slide') { const k = E.oE(P(lb, 0, .7)); p.t.style.transform = `translate(calc(-50% + ${(1 - k) * -W * .7}px),-50%)`; p.t.style.filter = `blur(${(1 - k) * 30 * U}px)`; }
        else { const k = E.sk(P(lb, 0, .5)); p.t.style.transform = `translate(-50%,-50%) scale(${lerp(1.1, 1, k) + .03 * lb})`; p.t.style.filter = `blur(${(1 - k) * 18 * U}px)`; p.t.style.opacity = k; } }
      acc += p.beats;
    });
    if (bigBox) { const on = b >= acc; bigBox.style.display = on ? 'block' : 'none';
      if (on) { const lb = b - acc, k = E.oE(P(lb, 0, .6)); dark = isDark(s.bigBg || C.black);
        fx(big.el, { s: lerp(1.35, 1, k) * (1 + .03 * lb), b: (1 - k) * 25 * U, r: lerp(-8, -3, k) }); big.set(lb * BEAT, lerp(.4, 1, k));
        if (sub) { const q = E.oB(P(lb, .35, .5)); sub.style.transform = `translate(-40%,-30%) rotate(-10deg) scale(${clamp(q, 0, 1.2)})`; sub.style.opacity = clamp(P(lb, .35, .1)); } } }
    return { dark };
  } };
};

/* tiles: mark flashes over colour fields on 8ths, then a grid of brand tiles pops in */
S.tiles = (root, s) => {
  const flashes = s.flashes || [C.pink, C.yellow, '#2a2a2a'], tcol = s.tileColors || [C.black, C.blue, C.red, C.pink, '#9FE3D9', '#D9C9A8', C.yellow, '#3BC46B', C.lilac, '#F5B8C7'];
  const big = el('div', { position: 'absolute', left: '50%', top: '50%', fontFamily: font(s.font || 'display'), fontWeight: 900, fontSize: px(s.size || 260), lineHeight: 1, transform: 'translate(-50%,-50%)' }, root, s.img ? '' : (s.mark || 'B'));
  if (s.img) el('img', { width: px(s.size || 260), display: 'block' }, big).src = s.img;
  const grid = el('div', { position: 'absolute', inset: 0 }, root);
  const cols = VERT ? 4 : 6, rows = VERT ? 7 : 4, cell = (VERT ? .17 * W : .1 * W), gap = cell * .22, r = rnd(s.seed || 3), tiles = [];
  const gx = (W - cols * cell - (cols - 1) * gap) / 2, gy = (H - rows * cell - (rows - 1) * gap) / 2;
  for (let i = 0; i < rows; i++) for (let j = 0; j < cols; j++) { if (r() < .22) continue; const bg = tcol[Math.floor(r() * tcol.length)]; const t = el('div', { position: 'absolute', left: (gx + j * (cell + gap)) + 'px', top: (gy + i * (cell + gap)) + 'px', width: cell + 'px', height: cell + 'px', background: bg, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: font(s.font || 'display'), fontWeight: 900, fontSize: (cell * .55) + 'px', color: isDark(bg) ? '#fff' : C.ink }, grid); if (s.img) el('img', { width: '60%' }, t).src = s.img; else t.textContent = s.mark || 'B'; tiles.push({ t, d: r() * 1.6 }); }
  return { update(b) {
    let bg, dark;
    if (b < 1) { const i = Math.min(flashes.length - 1, Math.floor(b / (1 / flashes.length))); bg = flashes[i]; const fg = s.flashFg?.[i] || (isDark(bg) ? '#F2C9A8' : '#7b1630'); big.style.color = fg; big.style.display = 'block'; grid.style.display = 'none'; big.style.transform = `translate(-50%,-50%) scale(${1 + .02 * (b * 8 % 1)})`; }
    else if (b < 1.6) { bg = C.black; big.style.color = '#fff'; big.style.display = 'block'; grid.style.display = 'none'; const k = E.oE(P(b, 1, .3)); big.style.transform = `translate(-50%,-50%) scale(${lerp(1.25, 1, k)})`; }
    else { bg = s.bg || C.paper; big.style.display = 'none'; grid.style.display = 'block'; const k = P(b, 1.6, 2.2); tiles.forEach(({ t, d }) => { const q = E.oB(P(b, 1.6 + d * .9, .35)); t.style.transform = `scale(${clamp(q, 0, 1.15)})`; t.style.opacity = clamp(q * 3); }); grid.style.transform = `scale(${lerp(1.08, 1, E.oC(k))})`; }
    root.style.background = bg; dark = isDark(bg); return { dark };
  } };
};

/* construct: logo with geometric construction guides drawing over it */
S.construct = (root, s) => {
  root.style.background = s.bg || C.black;
  const g = svg(root); const col = s.guide || 'rgba(70,220,150,.55)', cx = W / 2, cy = H / 2, R0 = M * .32;
  const paths = [];
  [[cx, cy, R0], [cx - R0 * .62, cy, R0 * .62], [cx + R0 * .62, cy, R0 * .62], [cx, cy - R0 * .5, R0 * .5], [cx, cy + R0 * .5, R0 * .5]].forEach(([x, y, r]) => paths.push(svgEl('circle', { cx: x, cy: y, r, fill: 'none', stroke: col, 'stroke-width': 1.4 * U }, g)));
  [[0, cy, W, cy], [cx, 0, cx, H], [cx - R0 * 1.6, cy - R0 * 1.2, cx + R0 * 1.6, cy + R0 * 1.2], [cx + R0 * 1.6, cy - R0 * 1.2, cx - R0 * 1.6, cy + R0 * 1.2], [0, cy - R0 * .55, W, cy - R0 * .55], [0, cy + R0 * .55, W, cy + R0 * .55]].forEach(([a, b2, c, d]) => paths.push(svgEl('line', { x1: a, y1: b2, x2: c, y2: d, stroke: col, 'stroke-width': 1.2 * U }, g)));
  const mk = el('div', { position: 'absolute', left: '50%', top: '50%', fontFamily: font(s.font || 'display'), fontWeight: 900, fontSize: px(s.size || 300), color: s.fg || '#fff', lineHeight: 1, textShadow: `0 0 ${px(30)} rgba(255,255,255,.35)` }, root, s.img ? '' : (s.mark || 'B'));
  if (s.img) el('img', { width: px(s.size || 300), display: 'block' }, mk).src = s.img;
  return { update(b) {
    paths.forEach((p, i) => { dash(p, E.io(P(b, i * .12, 1.4))); p.style.opacity = 1 - P(b, (s.beats || 4) - 1.2, 1); });
    const k = E.oE(P(b, 0, .6)); mk.style.transform = `translate(-50%,-50%) scale(${lerp(1.15, 1, k) * (1 + .012 * b)})`; mk.style.filter = `blur(${(1 - k) * 10 * U}px)`;
    return { dark: isDark(s.bg || C.black) };
  } };
};

/* stroke: giant outlined word draws itself while panning, then lands small and filled with a latin twin */
S.stroke = (root, s) => {
  root.style.background = s.bg || C.black; const dark = isDark(s.bg || C.black), fg = s.fg || (dark ? '#fff' : C.ink);
  const g = svg(root);
  const big = svgEl('text', { x: W / 2, y: H * .62, 'text-anchor': 'middle', 'font-size': H * (s.bigScale || .95), 'font-family': font(s.font || 'naskh'), 'font-weight': 700, fill: 'none', stroke: fg, 'stroke-width': 2.2 * U }, g); big.textContent = s.word;
  const row = el('div', { position: 'absolute', left: '50%', top: '50%', display: 'flex', gap: px(30), alignItems: 'center', whiteSpace: 'nowrap', direction: 'rtl' }, root);
  const ar = el('div', { fontFamily: font(s.font || 'naskh'), fontWeight: 700, fontSize: px(s.size || 120), color: fg }, row, s.word);
  const la = s.latin ? el('div', { fontFamily: "'Amiri',serif", fontWeight: 700, fontSize: px((s.size || 120) * .62), letterSpacing: '.12em', color: fg }, row, s.latin) : null;
  if (la) la.className = 'ltr';
  return { update(b) {
    const sp = Math.min(2.6, (s.beats || 4) * .62);
    if (b < sp) { big.style.display = 'block'; row.style.display = 'none'; dash(big, E.io(P(b, 0, sp * .95))); const k = b / sp; big.setAttribute('transform', `translate(${lerp(W * .22, -W * .22, k)},0)`); }
    else { big.style.display = 'none'; row.style.display = 'flex'; const k = E.sk(P(b, sp, .7)); row.style.transform = `translate(-50%,-50%) scale(${lerp(1.06, 1, k)})`; ar.style.opacity = lerp(.15, 1, k); ar.style.filter = `blur(${(1 - k) * 8 * U}px)`; if (la) { la.style.opacity = E.oC(P(b, sp + .4, .6)); la.style.letterSpacing = lerp(.4, .12, E.oC(P(b, sp + .4, .8))) + 'em'; } }
    return { dark };
  } };
};

/* palette: title bar, then colour rows split in on beats */
S.palette = (root, s) => {
  root.style.background = s.bg || C.paper;
  const box = el('div', { position: 'absolute', left: '7%', right: '7%', top: '17%', bottom: '17%', display: 'flex', flexDirection: 'column', gap: px(14) }, root);
  const title = el('div', { flex: '1.3', background: s.titleBg || C.ink, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: px(24), fontFamily: font(s.font || 'naskh'), fontWeight: 700, fontSize: px(60) }, box, s.title || '');
  const rows = (s.rows || [[C.paper], [C.red, C.orange]]).map(cols => { const r = el('div', { flex: 1, display: 'flex', gap: px(14) }, box); return cols.map(c => el('div', { flex: 1, background: c, transformOrigin: '100% 50%' }, r)); });
  return { update(b) {
    const k = E.oE(P(b, 0, .4)); title.style.transform = `scaleY(${k})`;
    rows.forEach((r, i) => r.forEach((c, j) => { const q = E.ioE(P(b, .5 + i * .5 + j * .08, .45)); c.style.transform = `scaleX(${q})`; }));
    return { dark: isDark(s.bg || C.paper) };
  } };
};

/* ripple: concentric rings expand, then an ink disc irises over everything */
S.ripple = (root, s) => {
  root.style.background = s.bg || C.cream; const g = svg(root), col = s.color || C.red, rings = [];
  for (let i = 0; i < 14; i++) rings.push(svgEl('circle', { cx: W / 2, cy: H / 2, r: 1, fill: 'none', stroke: col, 'stroke-width': 2.4 * U }, g));
  const disc = svgEl('circle', { cx: W * .62, cy: H * .45, r: 0, fill: s.iris || C.black }, g);
  const core = svgEl('circle', { cx: W / 2, cy: H / 2, r: 0, fill: col }, g);
  return { update(b) {
    const n = s.beats || 4; rings.forEach((c, i) => { const k = E.oC(P(b, i * .12, 2)); c.setAttribute('r', Math.max(.1, k * (14 + i * 20) * U * 1.5)); c.style.opacity = k > 0 ? 1 : 0; });
    core.setAttribute('r', 8 * U * E.oB(P(b, 0, .3)));
    const q = E.ioE(P(b, n - 1, 1)); disc.setAttribute('r', q * Math.hypot(W, H)); disc.setAttribute('cx', lerp(W * 1.1, W / 2, q));
    return { dark: q > .5 };
  } };
};

/* glyph: wordmark revealed in RTL steps (built piece by piece) + typed credit */
S.glyph = (root, s) => {
  root.style.background = s.bg || C.cream; const dark = isDark(s.bg || C.cream);
  const w = el('div', { position: 'absolute', left: '50%', top: '47%', transform: 'translate(-50%,-50%)', fontFamily: font(s.font || 'kufi'), fontWeight: 700, fontSize: px(s.size || 260), color: s.fg || (dark ? '#fff' : C.ink), whiteSpace: 'nowrap', lineHeight: 1.2 }, root, s.word);
  const cr = s.credit ? el('div', { position: 'absolute', left: '50%', top: '64%', fontFamily: F.sans, fontSize: px(30), color: s.fg || (dark ? '#fff' : C.ink), whiteSpace: 'nowrap' }, root, s.credit) : null;
  return { update(b) {
    const steps = s.steps || 5, st = Math.min(steps, Math.floor(b / .35) + 1), p = st / steps;
    const lb = b - (st - 1) * .35, pop = 1 + .05 * (1 - E.oC(P(lb, 0, .3)));
    w.style.clipPath = `inset(-20% 0 -20% ${(1 - p) * 100}%)`; w.style.transform = `translate(-50%,-50%) scale(${pop * (1 + .01 * b)})`;
    if (cr) { typeClip(cr, P(b, steps * .35 + .2, .8)); cr.style.transform = 'translate(-20%,0)'; }
    return { dark };
  } };
};

/* halo: mark assembles from two slices, ring descends, coloured bokeh blooms */
S.halo = (root, s) => {
  root.style.background = s.bg || C.black; const fg = s.fg || '#F5F1E8';
  const bokeh = [s.glowA || 'rgba(230,40,60,.55)', s.glowB || 'rgba(120,90,255,.35)'].map((c, i) => el('div', { position: 'absolute', width: px(420), height: px(420), borderRadius: '50%', background: `radial-gradient(circle,${c},transparent 65%)`, left: i ? '62%' : '22%', top: i ? '18%' : '38%', filter: `blur(${px(30)})` }, root));
  const mk = (clip) => { const d = el('div', { position: 'absolute', left: '50%', top: '50%', fontFamily: font(s.font || 'display'), fontWeight: 900, fontSize: px(s.size || 380), color: fg, lineHeight: 1, clipPath: clip }, root, s.img ? '' : (s.mark || 'B')); if (s.img) el('img', { width: px(s.size || 380), display: 'block' }, d).src = s.img; return d; };
  const top = mk('inset(0 0 50% 0)'), bot = mk('inset(50% 0 0 0)');
  const g = svg(root); const ring = svgEl('ellipse', { cx: W / 2, cy: H * .3, rx: M * .13, ry: M * .02, fill: 'none', stroke: s.ring || '#B6A8FF', 'stroke-width': 3 * U }, g);
  const base = svgEl('line', { x1: W / 2 - M * .28, x2: W / 2 + M * .28, y1: H * .74, y2: H * .74, stroke: 'rgba(255,255,255,.6)', 'stroke-width': 2 * U }, g);
  return { update(b) {
    const k = E.snap(P(b, .3, 1.2)); top.style.transform = `translate(calc(-50% + ${(1 - k) * -M * .12}px),-50%)`; bot.style.transform = `translate(calc(-50% + ${(1 - k) * M * .12}px),-50%)`;
    const r = E.io(P(b, 0, 1.6)); ring.setAttribute('cy', lerp(H * .26, H * .36, r)); ring.setAttribute('rx', M * .13 * (1 - r * .6)); ring.style.opacity = 1 - P(b, 1.4, .4);
    dash(base, E.oE(P(b, 0, 1)));
    bokeh.forEach((e, i) => { const q = E.oC(P(b, 1.6 + i * .3, 1)); e.style.opacity = q; e.style.transform = `scale(${lerp(.6, 1, q)})`; });
    return { dark: true };
  } };
};

/* counter: number counts up under an illustration, coloured disc pops behind */
S.counter = (root, s) => {
  root.style.background = s.bg || C.cream; const dark = isDark(s.bg || C.cream), fg = s.fg || (dark ? '#fff' : C.ink);
  const disc = el('div', { position: 'absolute', width: px(s.disc || 300), height: px(s.disc || 300), borderRadius: '50%', background: s.discColor || C.orange, left: '34%', top: '52%' }, root);
  let img = null; if (s.img) { const box = el('div', { position: 'absolute', left: '15%', right: '15%', top: '6%', bottom: '28%' }, root); img = media(box, s.img, { objectFit: 'contain' }); }
  const nb = el('div', { position: 'absolute', left: '50%', top: VERT ? '72%' : '80%', transform: 'translate(-50%,-50%)', textAlign: 'center', color: fg }, root);
  const n = el('div', { fontFamily: F.display, fontWeight: 800, fontSize: px(s.size || 150), lineHeight: 1 }, nb); n.className = 'num';
  el('div', { fontFamily: F.sans, fontWeight: 600, fontSize: px(34), marginTop: px(6) }, nb, s.unit || '');
  return { update(b, sec) {
    const k = E.oE(P(b, .2, s.countBeats || 1.6)); const v = lerp(s.from || 0, s.to || 100, k);
    n.textContent = (s.prefix || '') + (s.decimals ? v.toFixed(s.decimals) : fmt(v)) + (s.suffix || '');
    const q = E.oB(P(b, .5, .5)); disc.style.transform = `translate(-50%,-50%) scale(${clamp(q, 0, 1.2)})`;
    if (img) img.set(sec);
    return { dark };
  } };
};

/* helix: generative DNA of coloured dots, collapses into a soft cell */
S.helix = (root, s) => {
  root.style.background = s.bg || C.black; const g = svg(root), cols = s.colors || ['#D7F25A', '#B57CFF', '#FFFFFF', '#4D7BFF'], dots = [], N = 44;
  for (let i = 0; i < N * 2; i++) dots.push(svgEl('circle', { r: 9 * U, fill: cols[i % cols.length] }, g));
  const cell = el('div', { position: 'absolute', left: '50%', top: '50%', width: px(780), height: px(380), borderRadius: '50% 45% 48% 52% / 55% 50% 50% 45%', background: 'radial-gradient(ellipse at 50% 40%,#f2f2f2,#9a9a9a 60%,#5a5a5a)', boxShadow: `inset 0 0 ${px(40)} rgba(0,0,0,.6)` }, root);
  return { update(b) {
    const n = s.beats || 4, col = P(b, n * .5, n * .4);
    dots.forEach((d, i) => { const k = i % N, side = i < N ? 0 : Math.PI, x = W * (k / (N - 1)) * 1.1 - W * .05, ph = k * .38 + b * 1.4 + side, y = H / 2 + Math.sin(ph) * H * .14, z = Math.cos(ph);
      const cx = lerp(x, W / 2 + (x - W / 2) * .28, E.io(col)), cy = lerp(y, H / 2 + (y - H / 2) * .4, E.io(col));
      d.setAttribute('cx', cx); d.setAttribute('cy', cy); d.setAttribute('r', (6 + 5 * (z + 1)) * U * lerp(1, .6, col)); d.style.opacity = .35 + .65 * (z + 1) / 2; });
    const q = E.oE(P(b, n * .5, n * .4)); cell.style.transform = `translate(-50%,-50%) scale(${q})`; cell.style.opacity = q;
    return { dark: true };
  } };
};

/* device: phone mockup + oversized bleed words + optional big word swap and side caption */
S.device = (root, s) => {
  root.style.background = s.bg || C.paper; const dark = isDark(s.bg || C.paper), fg = s.fg || (dark ? '#fff' : C.ink);
  if (s.glow) el('div', { position: 'absolute', left: '50%', top: '55%', width: px(700), height: px(900), transform: 'translate(-50%,-50%)', background: `radial-gradient(ellipse,${s.glow},transparent 65%)`, filter: `blur(${px(40)})` }, root);
  const bleed = (s.bleed || []).map((t, i) => el('div', { position: 'absolute', top: VERT ? (i ? '88%' : '15%') : (i ? '58%' : '42%'), [i ? 'left' : 'right']: '-6%', transform: 'translateY(-50%)', fontFamily: font(s.bleedFont || 'naskh'), fontWeight: 700, fontSize: px(s.bleedSize || 300), color: fg, whiteSpace: 'nowrap', lineHeight: 1 }, root, t));
  const ph = el('div', { position: 'absolute', left: '50%', top: VERT ? '57%' : '54%', width: px(VERT ? 480 : 430), height: px(VERT ? 980 : 880), borderRadius: px(64), background: '#0d0d0d', padding: px(14), boxShadow: `0 ${px(40)} ${px(80)} rgba(0,0,0,.35)` }, root);
  const scr = el('div', { position: 'relative', width: '100%', height: '100%', borderRadius: px(50), overflow: 'hidden', background: '#111' }, ph);
  const m = s.src ? media(scr, s.src) : null;
  if (!s.src && s.mark) el('div', { position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: s.markColor || C.accent, fontFamily: F.display, fontWeight: 900, fontSize: px(160) }, scr, s.mark);
  el('div', { position: 'absolute', left: '50%', top: px(14), width: px(130), height: px(34), borderRadius: px(20), background: '#000', transform: 'translateX(-50%)' }, scr);
  const side = s.side ? el('div', { position: 'absolute', right: VERT ? '8%' : '9%', top: VERT ? '23.5%' : '50%', transform: VERT ? 'none' : 'translateY(-50%)', fontFamily: font(s.sideFont || 'naskh'), fontWeight: 700, fontSize: px((s.sideSize || 110) * (VERT ? .6 : 1)), color: fg, lineHeight: 1.05, textAlign: 'right', maxWidth: VERT ? '84%' : '28%' }, root, s.side) : null;
  const sw = (s.swap || []).map(t => el('div', { position: 'absolute', left: '50%', top: '58%', transform: 'translate(-50%,-50%)', fontFamily: font(s.swapFont || 'display'), fontWeight: 900, fontSize: px(s.swapSize || 190), color: '#fff', whiteSpace: 'nowrap', textShadow: `0 0 ${px(30)} rgba(255,255,255,.55)`, opacity: 0 }, root, t));
  const spark = s.sparkles ? [0, 1, 2, 3].map(i => icon(root, 'star', (i % 2 ? 90 : 46) * U, s.sparkColor || '#F4B72A', { left: [26, 63, 30, 58][i] + '%', top: [24, 30, 70, 60][i] + '%' })) : [];
  return { update(b, sec) {
    const k = E.oE(P(b, 0, .7)); ph.style.transform = `translate(-50%,-50%) translateY(${(1 - k) * H * .6}px) rotate(${(1 - k) * 8}deg) scale(${1 + .015 * b})`;
    bleed.forEach((e, i) => { const q = E.oE(P(b, .15 + i * .1, .8)); e.style.transform = `translate(${(i ? -1 : 1) * (1 - q) * W * .3}px,-50%)`; e.style.filter = `blur(${(1 - q) * 20 * U}px)`; });
    if (side) { const q = E.sk(P(b, .6, .7)); fx(side, { o: q, b: (1 - q) * 10 * U, y: 0 }); side.style.transform += VERT ? '' : ' translateY(-50%)'; }
    sw.forEach((e, i) => { const st = (s.swapAt || 1.5) + i * (s.swapEvery || 1), on = b >= st && (i === sw.length - 1 || b < st + (s.swapEvery || 1)); const q = E.oE(P(b, st, .35)); e.style.opacity = on ? q : 0; e.style.transform = `translate(-50%,-50%) scale(${lerp(1.3, 1, q)})`; e.style.filter = `blur(${(1 - q) * 14 * U}px)`; });
    spark.forEach((e, i) => { const q = E.oB(P(b, .4 + i * .25, .4)); e.style.transform = `scale(${clamp(q, 0, 1.3) * (1 + .1 * Math.sin(b * 3 + i))}) rotate(${b * 20}deg)`; });
    if (m) m.set(sec);
    return { dark };
  } };
};

/* appicon: rounded app icon with neon glow pulsing on beats */
S.appicon = (root, s) => {
  root.style.background = s.bg || C.black; const g = s.glow || C.accent;
  const ic = el('div', { position: 'absolute', left: '50%', top: '50%', width: px(420), height: px(420), borderRadius: px(96), background: s.fill || '#0c0c0c', border: `${px(4)} solid ${g}`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontFamily: F.display, fontWeight: 900, fontSize: px(220) }, root, s.img ? '' : (s.mark || 'B'));
  if (s.img) el('img', { width: '62%' }, ic).src = s.img;
  return { update(b) { const k = E.oE(P(b, 0, .5)), pulse = 1 + .04 * Math.exp(-(b % 1) * 6); ic.style.transform = `translate(-50%,-50%) scale(${lerp(.6, 1, k) * pulse})`; ic.style.boxShadow = `0 0 ${px(40 + 50 * pulse)} ${g}, 0 0 ${px(160)} ${g}66, inset 0 0 ${px(30)} ${g}55`; return { dark: true }; } };
};

/* likes: a post card, then icons multiply on 16ths while a counter climbs */
S.likes = (root, s) => {
  root.style.background = s.bg || C.paper;
  const card = el('div', { position: 'absolute', left: '50%', top: '50%', width: VERT ? '84%' : '58%', padding: px(40), borderRadius: px(30), background: '#fff', boxShadow: `0 ${px(20)} ${px(60)} rgba(0,0,0,.12)`, transform: 'translate(-50%,-50%)', fontFamily: F.sans, color: C.ink }, root);
  if (s.img) { const bx = el('div', { position: 'relative', height: px(380), borderRadius: px(18), overflow: 'hidden', marginBottom: px(24) }, card); media(bx, s.img); }
  el('div', { fontSize: px(40), fontWeight: 700, lineHeight: 1.4 }, card, s.title || '');
  if (s.text) el('div', { fontSize: px(28), opacity: .7, marginTop: px(10), lineHeight: 1.5 }, card, s.text);
  const cnt = el('div', { position: 'absolute', left: px(28), top: px(24), display: 'flex', gap: px(10), alignItems: 'center', fontFamily: F.display, fontWeight: 800, fontSize: px(34), color: s.color || C.red }, card); cnt.className = 'ltr';
  const ci = icon(cnt, s.icon || 'thumb', 40 * U, s.color || C.red, { position: 'relative' }); const cn = el('span', {}, cnt);
  const r = rnd(s.seed || 11), many = [];
  for (let i = 0; i < (s.count || 26); i++) { const e = icon(root, s.icon || 'thumb', (60 + r() * 90) * U, s.color || C.red, { left: (r() * 92) + '%', top: (r() * 88) + '%' }); many.push({ e, d: i * .125 + r() * .05, r: (r() - .5) * 40 }); }
  return { update(b) {
    const k = E.oE(P(b, 0, .5)); card.style.transform = `translate(-50%,-50%) scale(${lerp(.9, 1, k)})`; card.style.opacity = k;
    let n = 0; many.forEach(({ e, d, r: rot }) => { const q = E.oB(P(b, .8 + d, .3)); if (b >= .8 + d) n++; e.style.transform = `scale(${clamp(q, 0, 1.25)}) rotate(${rot}deg)`; e.style.opacity = clamp(q * 3); });
    cn.textContent = fmt(n * (s.step || 2.3)); ci.style.transform = `scale(${1 + .25 * Math.exp(-((b * 8) % 1) * 5)})`;
    return { dark: isDark(s.bg || C.paper) };
  } };
};

/* flurry: hard cuts every `per` beats through a list of images/clips */
S.flurry = (root, s) => {
  root.style.background = s.bg || C.black; const per = s.per || .5, items = (s.srcs || []).map(src => { const box = el('div', { position: 'absolute', inset: s.card ? (VERT ? '18% 8%' : '14% 22%') : 0, display: 'none', borderRadius: s.card ? px(24) : 0, overflow: 'hidden' }, root); return { box, m: media(box, src) }; });
  return { update(b, sec) {
    const i = Math.min(items.length - 1, Math.floor(b / per)); items.forEach((it, j) => { it.box.style.display = j === i ? 'block' : 'none'; });
    if (items[i]) { const lb = (b - i * per) / per; items[i].box.style.transform = `scale(${lerp(1.08, 1, E.oE(clamp(lb * 1.5)))}) rotate(${(hash(i) - .5) * (s.card ? 4 : 0)}deg)`; items[i].m.set(sec); }
    return { dark: isDark(s.bg || C.black) };
  } };
};

/* scale: huge disc + monumental object + tiny human + measurement bracket */
S.scale = (root, s) => {
  root.style.background = s.bg || '#1a1a1a';
  const cam = el('div', { position: 'absolute', inset: 0, transformOrigin: '50% 45%' }, root);
  el('div', { position: 'absolute', left: '50%', top: '50%', width: px(860), height: px(860), borderRadius: '50%', background: `radial-gradient(circle at 45% 40%,${s.discHi || '#FF8A2A'},${s.disc || '#E0620F'} 70%)`, transform: 'translate(-50%,-50%)' }, cam);
  const ob = el('div', { position: 'absolute', left: '50%', top: '53%', width: px(s.objW || 300), height: px(s.objH || 560), transform: 'translate(-50%,-50%)', borderRadius: px(26), overflow: 'hidden', background: s.objColor || '#2b2724' }, cam);
  if (s.src) media(ob, s.src, { objectFit: s.fit || 'cover' });
  icon(cam, 'person', 90 * U, '#0d0d0d', { left: '67%', top: '72%' });
  const g = svg(cam); const yb = H * .53 - (s.objH || 560) * U / 2 - 22 * U, x0 = W / 2 - (s.objW || 300) * U / 2, x1 = W / 2 + (s.objW || 300) * U / 2;
  const br = svgEl('path', { d: `M${x0},${yb + 10 * U} L${x0},${yb} L${x1},${yb} L${x1},${yb + 10 * U}`, fill: 'none', stroke: s.bracket || '#FFD84A', 'stroke-width': 3 * U }, g);
  const lab = el('div', { position: 'absolute', left: '50%', top: (yb - 52 * U) + 'px', transform: 'translateX(-50%)', fontFamily: F.display, fontWeight: 800, fontSize: px(46), color: '#111', whiteSpace: 'nowrap' }, cam, s.measure || '');
  const st = icon(root, 'star', 70 * U, '#fff', { left: '8%', top: '12%' });
  return { update(b) {
    const k = E.io(P(b, 0, 1.2)); cam.style.transform = `scale(${lerp(s.zoomFrom || 2.4, 1, k)})`;
    dash(br, E.oE(P(b, 1.3, .6))); lab.style.opacity = E.oC(P(b, 1.5, .4));
    const q = E.oB(P(b, 2.5, .4)); st.style.transform = `scale(${clamp(q, 0, 1.3)}) rotate(${b * 30}deg)`; st.style.filter = `drop-shadow(0 0 ${px(18)} #fff)`;
    return { dark: true };
  } };
};

/* nodes: glass cards appear one per beat, then lines connect them */
S.nodes = (root, s) => {
  root.style.background = s.bg || '#0b0b14';
  if (s.src) { const bx = el('div', { position: 'absolute', inset: 0 }, root); media(bx, s.src); } else { const g0 = svg(root); const r = rnd(5); for (let i = 0; i < 260; i++) svgEl('circle', { cx: r() * W, cy: r() * H, r: r() * 1.8 * U, fill: '#fff', opacity: .2 + r() * .6 }, g0); }
  const g = svg(root); const nodes = s.nodes || [{ t: 'أ', x: .2, y: .7 }, { t: 'ب', x: .5, y: .25 }, { t: 'ج', x: .8, y: .7 }];
  const cards = nodes.map((n, i) => { const c = el('div', { position: 'absolute', left: (n.x * 100) + '%', top: (n.y * 100) + '%', width: px(s.cardW || 230), height: px(s.cardH || 150), transform: 'translate(-50%,-50%)', background: n.color || (i % 2 ? 'rgba(180,150,90,.45)' : 'rgba(80,110,200,.45)'), border: `1px solid rgba(255,255,255,.45)`, backdropFilter: `blur(${px(6)})`, color: '#fff', fontFamily: F.sans, fontWeight: 700, fontSize: px(34), padding: px(16) }, root, n.t); icon(c, 'star', 26 * U, '#fff', { left: '50%', top: '62%' }); return c; });
  const order = s.closed === false ? nodes : nodes.concat([nodes[0]]);
  const lines = []; for (let i = 0; i < order.length - 1; i++) lines.push(svgEl('line', { x1: order[i].x * W, y1: order[i].y * H + 30 * U, x2: order[i + 1].x * W, y2: order[i + 1].y * H + 30 * U, stroke: '#fff', 'stroke-width': 3 * U }, g));
  return { update(b) {
    cards.forEach((c, i) => { const q = E.oE(P(b, i * (s.every || .75), .5)); c.style.opacity = q; c.style.transform = `translate(-50%,-50%) translateY(${(1 - q) * -60 * U}px) rotate(${(1 - q) * 6}deg)`; });
    const st = nodes.length * (s.every || .75); lines.forEach((l, i) => dash(l, E.io(P(b, st + i * .35, .5))));
    return { dark: true };
  } };
};

/* spot: object in a hanging frame, frame falls away, spotlight cone on dark */
S.spot = (root, s) => {
  const wall = s.bg || '#E7D7BC';
  const dark = el('div', { position: 'absolute', inset: 0, background: '#0c0c0c' }, root);
  const cone = el('div', { position: 'absolute', inset: 0, background: wall, clipPath: 'polygon(42% 0,58% 0,100% 100%,0 100%)' }, root);
  const frame = el('div', { position: 'absolute', left: '50%', top: '42%', width: px(380), height: px(330), background: '#666', border: `${px(18)} solid #7a7a7a`, boxShadow: `0 ${px(14)} ${px(30)} rgba(0,0,0,.35)` }, root);
  const ob = el('div', { position: 'absolute', left: '50%', top: '44%', width: px(s.size || 260), height: px(s.size || 260) }, root);
  media(ob, s.src || '', { objectFit: 'contain' });
  const sh = el('div', { position: 'absolute', left: '50%', top: '62%', width: px(200), height: px(36), borderRadius: '50%', background: 'rgba(0,0,0,.35)', filter: `blur(${px(8)})` }, root);
  return { update(b) {
    const f = E.iC(P(b, .4, .8)); frame.style.transform = `translate(-50%,-50%) translateY(${f * H}px) rotate(${f * 25}deg)`;
    const d = E.oB(P(b, 1, .5)); ob.style.transform = `translate(-50%,-50%) translateY(${(d) * 40 * U}px)`; sh.style.transform = `translate(-50%,-50%) scale(${P(b, 1, .5)})`; sh.style.opacity = P(b, 1, .5);
    const c = E.ioE(P(b, 2, .6)); dark.style.opacity = c; cone.style.clipPath = c > 0 ? `polygon(${lerp(0, 42, c)}% 0,${lerp(100, 58, c)}% 0,100% 100%,0 100%)` : 'none';
    root.style.background = wall; return { dark: c > .5 };
  } };
};

/* bounce: platform icons pop in, a glossy ball bounces on every beat */
S.bounce = (root, s) => {
  root.style.background = s.bg || '#6C3BE8';
  const ics = (s.icons || ['yt', 'ig', 'tt']).map((n, i, a) => { const box = el('div', { position: 'absolute', left: (50 + (i - (a.length - 1) / 2) * 13) + '%', top: '36%', width: px(130), height: px(130), borderRadius: px(30), background: '#fff', boxShadow: `0 ${px(14)} ${px(30)} rgba(0,0,0,.2)` }, root); icon(box, n, 80 * U, ['#E53935', '#C13584', '#111', '#111', '#F7C600'][['yt', 'ig', 'tt', 'x', 'snap'].indexOf(n)] || '#111', { left: px(25), top: px(25) }); return box; });
  const ball = el('div', { position: 'absolute', left: '50%', width: px(260), height: px(260), borderRadius: '50%', background: 'radial-gradient(circle at 35% 30%,#ff8a8a,#e41b23 45%,#8d0b10)' }, root);
  return { update(b) {
    ics.forEach((e, i) => { const q = E.oB(P(b, i * .5, .4)); e.style.transform = `translate(-50%,-50%) scale(${clamp(q, 0, 1.25)}) translateY(${Math.sin(b * 3 + i) * 8 * U}px)`; });
    const ph = b % 1, h = 4 * ph * (1 - ph), sq = Math.exp(-ph * 12) + Math.exp(-(1 - ph) * 12);
    ball.style.top = (H * .98 - h * H * .32) + 'px'; ball.style.transform = `translate(-50%,-50%) scale(${1 + .18 * sq},${1 - .18 * sq})`;
    return { dark: true };
  } };
};

/* stats: dashboard cards slide in, area charts draw */
S.stats = (root, s) => {
  root.style.background = s.bg || C.paper; const dark = isDark(s.bg || C.paper), fg = dark ? '#fff' : C.ink;
  const head = el('div', { position: 'absolute', right: '10%', top: '26%', textAlign: 'right', color: fg, fontFamily: F.sans }, root);
  el('div', { fontSize: px(46), fontWeight: 700 }, head, s.title || 'الإحصائيات');
  if (s.chip) el('div', { display: 'inline-block', marginTop: px(10), padding: `${px(6)} ${px(18)}`, borderRadius: px(30), background: C.ink, color: '#fff', fontSize: px(22) }, head, s.chip);
  const cs = s.cards || [{ k: 'المشاهدات', v: '2.4 مليون' }, { k: 'المتابعون', v: '+38 ألف' }, { k: 'التفاعل', v: '9.1%' }, { k: 'الحفظ', v: '61 ألف' }];
  const pal = ['#BFC8F2', '#E8B9C0', '#C3E2CF', '#D6CDF4'], strokes = ['#6F86E8', '#C9606F', '#5BAA7C', '#8D7CE0'];
  const row = el('div', { position: 'absolute', left: '8%', right: '8%', top: VERT ? '40%' : '46%', display: 'flex', flexDirection: VERT ? 'column' : 'row-reverse', gap: px(26) }, root);
  const items = cs.map((c, i) => { const card = el('div', { flex: 1, color: fg, fontFamily: F.sans }, row); const top = el('div', { display: 'flex', justifyContent: 'space-between', fontSize: px(24), opacity: .8 }, card); el('span', {}, top, c.k); el('span', { fontWeight: 700, opacity: 1 }, top, c.v);
    const sv = svgEl('svg', { viewBox: '0 0 100 50', preserveAspectRatio: 'none' }); Object.assign(sv.style, { width: '100%', height: px(VERT ? 130 : 150), marginTop: px(10) }); card.append(sv);
    const r = rnd(i + 2); let pts = []; for (let j = 0; j <= 10; j++) pts.push([j * 10, 45 - (j / 10) * 30 - r() * 12]);
    const d = 'M' + pts.map(p => p.join(',')).join(' L'); const area = svgEl('path', { d: d + ' L100,50 L0,50 Z', fill: c.color || pal[i % 4] }, sv); const line = svgEl('path', { d, fill: 'none', stroke: strokes[i % 4], 'stroke-width': 1.2, 'vector-effect': 'non-scaling-stroke' }, sv);
    return { card, area, line }; });
  return { update(b) {
    items.forEach((it, i) => { const q = E.oE(P(b, .3 + i * .2, .6)); fx(it.card, { o: q, y: (1 - q) * 40 * U, b: (1 - q) * 8 * U }); dash(it.line, E.io(P(b, .5 + i * .2, 1))); it.area.style.clipPath = `inset(0 ${(1 - E.io(P(b, .5 + i * .2, 1))) * 100}% 0 0)`; });
    blurIn(head, b, 0, .6); return { dark };
  } };
};

/* grid: collage of everything assembles tile by tile, then pulls back */
S.grid = (root, s) => {
  root.style.background = s.bg || C.paper; const srcs = s.srcs || [], cols = s.cols || (VERT ? 3 : 5), rows = Math.ceil(srcs.length / cols), gap = 8 * U;
  const wrap = el('div', { position: 'absolute', inset: VERT ? '14% 4%' : '12% 6%', display: 'grid', gridTemplateColumns: `repeat(${cols},1fr)`, gridTemplateRows: `repeat(${rows},1fr)`, gap: gap + 'px' }, root);
  const tiles = srcs.map((src, i) => { const t = el('div', { position: 'relative', overflow: 'hidden', background: '#ddd' }, wrap); const m = media(t, src); return { t, m, d: hash(i + 3) * 1.4 }; });
  return { update(b, sec) {
    tiles.forEach(({ t, m, d }) => { const q = E.oE(P(b, d * .8, .35)); t.style.opacity = q > 0 ? 1 : 0; t.style.transform = `scale(${lerp(1.3, 1, q)})`; m.set(sec); });
    wrap.style.transform = `scale(${lerp(1.18, 1, E.io(P(b, 0, s.beats || 4)))})`;
    return { dark: isDark(s.bg || C.paper) };
  } };
};

/* more: "+word" gains a plus each beat while the background flips */
S.more = (root, s) => {
  const t = el('div', { position: 'absolute', left: '50%', top: '50%', transform: 'translate(-50%,-50%)', fontFamily: font(s.font || 'naskh'), fontWeight: 400, fontSize: px(s.size || 110), whiteSpace: 'nowrap' }, root);
  const g = svg(root); const arrow = svgEl('path', { d: `M${W * .44},${H * .54} q${-40 * U},${-6 * U} ${-70 * U},${30 * U} m${12 * U},${-24 * U} l${-12 * U},${24 * U} l${24 * U},${-4 * U}`, fill: 'none', 'stroke-width': 3 * U, 'stroke-linecap': 'round' }, g);
  const flips = s.flips || [C.paper, C.black, C.paper];
  return { update(b) {
    const i = Math.min(flips.length - 1, Math.floor(b)), bg = flips[i], dark = isDark(bg); root.style.background = bg;
    const n = Math.min(s.plus || 3, i + 1); t.innerHTML = `<span class="ltr">${'+'.repeat(n)}</span>${s.word || 'أكثر'}`; t.style.color = dark ? '#fff' : C.ink;
    arrow.setAttribute('stroke', dark ? '#fff' : C.ink); dash(arrow, i >= 1 ? E.oE(P(b, 1, .5)) : 0);
    t.style.transform = `translate(-50%,-50%) scale(${1 + .06 * Math.exp(-(b % 1) * 8)})`;
    return { dark };
  } };
};

/* handle: letter-spaced end tag, no chrome */
S.handle = (root, s) => {
  root.style.background = s.bg || C.black;
  const t = el('div', { position: 'absolute', left: '50%', top: '50%', fontFamily: F.readex, fontWeight: 500, fontSize: px(s.size || 34), color: s.fg || '#fff', whiteSpace: 'nowrap' }, root, s.text || '@handle'); t.className = 'ltr';
  return { update(b) { const k = E.oC(P(b, 0, 1.2)); t.style.letterSpacing = lerp(.6, .22, k) + 'em'; t.style.opacity = k; t.style.transform = 'translate(-50%,-50%)'; t.style.filter = `blur(${(1 - k) * 8 * U}px)`; return { dark: isDark(s.bg || C.black) }; } };
};

/* title: general big statement — modes rise | blur | weight | type */
S.title = (root, s) => {
  root.style.background = s.bg || C.cream; const dark = isDark(s.bg || C.cream), fg = s.fg || (dark ? '#fff' : C.ink);
  if (s.src) { const bx = el('div', { position: 'absolute', inset: 0 }, root); s._m = media(bx, s.src); if (s.dim !== 0) el('div', { position: 'absolute', inset: 0, background: `rgba(0,0,0,${s.dim ?? .45})` }, root); }
  const box = el('div', { position: 'absolute', left: '8%', right: '8%', top: '50%', transform: 'translateY(-50%)', textAlign: s.align || 'center', color: s.src ? '#fff' : fg }, root);
  const h = el('div', { fontFamily: font(s.font || 'display'), fontWeight: 800, fontSize: px(s.size || 170), lineHeight: 1.2 }, box); const ws = splitWords(h, s.text || '');
  const sub = s.sub ? el('div', { fontFamily: F.sans, fontSize: px(s.subSize || 44), marginTop: px(20), opacity: .85 }, box, s.sub) : null;
  if (s.accent) ws.forEach(w => { if (s.accent.includes(w.textContent)) w.style.color = s.accentColor || C.accent; });
  return { update(b, sec) {
    const mode = s.mode || 'rise';
    if (mode === 'rise') rise(ws, b, 0, .25, .9);
    else if (mode === 'weight') { h.style.fontVariationSettings = `'wght' ${Math.round(lerp(120, 850, E.oC(P(b, 0, 1.2))))}`; blurIn(h, b, 0, .6); }
    else if (mode === 'type') typeClip(h, P(b, 0, 1.4), 18);
    else blurIn(h, b, 0, .8);
    if (sub) blurIn(sub, b, .6, .8);
    if (s._m) { s._m.set(sec); s._m.el.style.transform = `scale(${1.08 - .02 * b})`; }
    return { dark: s.src ? true : dark };
  } };
};

/* full: full-bleed media with optional caption and slow push */
S.full = (root, s) => {
  root.style.background = C.black; const m = media(root, s.src);
  const cap = s.caption ? el('div', { position: 'absolute', right: '9%', left: '9%', bottom: VERT ? '16%' : '18%', textAlign: 'right', color: '#fff', fontFamily: font(s.font || 'display'), fontWeight: 800, fontSize: px(s.size || 90), textShadow: `0 ${px(4)} ${px(30)} rgba(0,0,0,.6)` }, root) : null;
  const ws = cap ? splitWords(cap, s.caption) : [];
  if (s.dim) el('div', { position: 'absolute', inset: 0, background: `rgba(0,0,0,${s.dim})` }, root);
  return { update(b, sec) { m.set(sec); const z = s.zoom ?? .06; m.el.style.transform = s.zoomTo ? `scale(${lerp(1, s.zoomTo, (s.zoomEase === 'in' ? E.iC : E.io)(clamp(b / (s.beats || 4))))})` : `scale(${1 + z - z * b / (s.beats || 4)})`; if (cap) rise(ws, b, .3, .2, .8); return { dark: true }; } };
};


/* ===================== MANIFESTO SCENES (film style) ===================== */
const isAr = t => /[؀-ۿ]/.test(t);

/* decode: wordmark builds char by char, each new char flickers through glyphs first; optional smear-out bar */
S.decode = (root, s) => {
  root.style.background = s.bg || '#E8E3D8'; const dark = isDark(s.bg || '#E8E3D8');
  const t = el('div', { position: 'absolute', left: '50%', top: '50%', transform: 'translate(-50%,-50%)', fontFamily: font(s.font || 'grotesk'), fontWeight: s.weight || 700, fontSize: px(s.size || 64), letterSpacing: s.tracking || '.04em', color: s.fg || (dark ? '#fff' : '#1b1b1b'), whiteSpace: 'nowrap', direction: isAr(s.text || '') ? 'rtl' : 'ltr', transformOrigin: '50% 50%' }, root);
  const chars = [...(s.text || 'BRAND')], G = (s.glyphs || '¥✳✺※⌘#@%&\\/<>[]{}=+*').split(''), GA = 'ء ؤ ئ ك ق ف ع ض ص ش س ز ر ذ د خ ح ج ث ت ب'.split(' ');
  const build = s.buildBeats || 3;
  return { update(b) {
    const per = build / chars.length; let out = '';
    chars.forEach((c, i) => { const st = i * per; if (b < st) return; const settled = b >= st + per * 1.6 || c === ' '; out += settled ? c : (isAr(c) ? GA : G)[Math.floor(hash(i * 31 + Math.floor(b * 14)) * (isAr(c) ? GA.length : G.length))]; });
    t.textContent = out;
    if (s.smear) { const n = s.beats || 4, k = E.iE(P(b, n - .9, .9)); t.style.transform = `translate(-50%,-50%) scaleX(${1 + 2.5 * k}) scale(${1 + 1.2 * k})`; t.style.filter = `blur(${k * 10 * U}px)`; t.style.opacity = 1 - E.iC(P(b, n - .3, .3)); }
    return { dark };
  } };
};

/* words: one (or a few) words per shot over cinematic media — the manifesto line.
   shots: [{src, words, beats?, fx: fade|scatter|smear|spread|big, pos:[x,y]}]  each word = s.wordBeats (default 1) */
S.words = (root, s) => {
  root.style.background = '#000'; const wb = s.wordBeats || 1, size = s.size || 46, fam = font(s.font || 'serif');
  let acc = 0;
  const shots = (s.shots || []).map((sh, i) => {
    const box = el('div', { position: 'absolute', inset: 0, display: 'none', overflow: 'hidden' }, root);
    const m = sh.src ? media(box, sh.src) : null; if (sh.bg) box.style.background = sh.bg;
    if (s.dim !== 0) el('div', { position: 'absolute', inset: 0, background: `rgba(0,0,0,${sh.dim ?? s.dim ?? .18})` }, box);
    const ws = (sh.words || '').split(/\s+/).filter(Boolean); const ar = ws.some(isAr);
    const big = sh.fx === 'big' || sh.fx === 'smear';
    const items = ws.map((w, j) => {
      const pos = sh.fx === 'spread' ? (sh.positions?.[j] || [[.2, .2], [.72, .5], [.6, .78], [.35, .6]][j % 4]) : (sh.pos || [.5, .5]);
      const e = el('div', { position: 'absolute', left: (pos[0] * 100) + '%', top: (pos[1] * 100) + '%', transform: 'translate(-50%,-50%)', fontFamily: fam, fontWeight: big ? 600 : 400, fontSize: px(big ? (sh.size || size * 4.2) : (sh.size || size)), color: sh.fg || '#fff', whiteSpace: 'nowrap', textShadow: `0 ${px(2)} ${px(18)} rgba(0,0,0,.35)`, direction: ar ? 'rtl' : 'ltr', letterSpacing: big ? '-.02em' : '0' }, box);
      if (sh.fx === 'scatter' && !isAr(w)) { [...w].forEach((c, k) => { const sp = el('span', { display: 'inline-block' }, e); sp.textContent = c; }); } else e.textContent = w;
      return e;
    });
    const beats = sh.beats || Math.max(ws.length, 1) * wb;
    const o = { box, m, items, t0: acc, beats, sh, ws }; acc += beats; return o;
  });
  s.beats = s.beats || acc;
  return { update(b, sec) {
    let cur = null;
    shots.forEach(o => { const on = b >= o.t0 && b < o.t0 + o.beats; o.box.style.display = on ? 'block' : 'none'; if (on) cur = o; });
    if (!cur) cur = shots[shots.length - 1];
    if (cur) { cur.box.style.display = 'block'; const lb = b - cur.t0; if (cur.m) { cur.m.set(sec); const z = cur.sh.zoom ?? .05; cur.m.el.style.transform = `scale(${1 + z * (lb / cur.beats)})`; }
      const n = cur.items.length, per = cur.beats / Math.max(n, 1), fx = cur.sh.fx || 'fade';
      cur.items.forEach((e, j) => {
        const st = j * per, active = lb >= st && (fx === 'spread' || j === n - 1 || lb < st + per);
        if (!active) { e.style.opacity = 0; return; }
        const k = E.oC(P(lb, st, Math.min(.35, per * .5)));
        if (fx === 'scatter' && e.children.length) { [...e.children].forEach((c, q) => { const r1 = hash(q * 7 + j), r2 = hash(q * 13 + j + 2), a = E.io(P(lb, st, per * .85)); c.style.transform = `translate(${(1 - a) * (r1 - .5) * W * .5}px,${(1 - a) * (r2 - .5) * H * .6}px)`; c.style.opacity = .3 + .7 * a; }); e.style.opacity = 1; }
        else if (fx === 'smear') { const out = E.iE(P(lb, st + per * .55, per * .45)); e.style.opacity = k * (1 - out * .6); e.style.transform = `translate(-50%,-50%) scaleX(${1 + out * 2.2})`; e.style.filter = `blur(${out * 26 * U}px)`; }
        else { e.style.opacity = k; e.style.filter = `blur(${(1 - k) * 6 * U}px)`; e.style.transform = 'translate(-50%,-50%)'; }
      }); }
    return { dark: true };
  } };
};

/* slugs: rapid montage of media with a mono label "\ project-slug \" */
S.slugs = (root, s) => {
  root.style.background = '#000'; const per = s.per || .5;
  const items = (s.items || []).map(it => { const box = el('div', { position: 'absolute', inset: 0, display: 'none' }, root); const m = media(box, it.src); const lab = el('div', { position: 'absolute', left: '50%', top: '50%', transform: 'translate(-50%,-50%)', fontFamily: F.mono, fontSize: px(s.size || 30), color: '#fff', whiteSpace: 'nowrap', textShadow: `0 0 ${px(10)} rgba(0,0,0,.6)`, direction: 'ltr' }, box); lab.textContent = `\\ ${it.t} \\`; return { box, m }; });
  return { update(b, sec) { const i = Math.min(items.length - 1, Math.floor(b / per)); items.forEach((it, j) => it.box.style.display = j === i ? 'block' : 'none'); if (items[i]) { items[i].m.set(sec); const lb = (b - i * per) / per; items[i].m.el.style.transform = `scale(${1.04 + .04 * lb})`; } return { dark: true }; } };
};

/* swap: serif sentence on paper; one slot cycles through words/logos, then a second line types in */
S.swap = (root, s) => {
  root.style.background = s.bg || '#E8E3D8'; const fg = s.fg || '#1b1b1b', ar = isAr((s.before || '') + (s.after || ''));
  const box = el('div', { position: 'absolute', left: '50%', top: '50%', transform: 'translate(-50%,-50%)', textAlign: 'center', fontFamily: font(s.font || 'serif'), fontSize: px(s.size || 40), color: fg, whiteSpace: 'nowrap', direction: ar ? 'rtl' : 'ltr', lineHeight: 1.35 }, root);
  const l1 = el('div', { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '.3em' }, box);
  el('span', {}, l1, s.before || ''); const slot = el('span', { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', minWidth: '2.6em', height: '1.4em' }, l1); el('span', {}, l1, s.after || '');
  const l2 = s.line2 ? el('div', {}, box, s.line2) : null;
  const opts = (s.slot || []).map(x => { const e = el('span', { display: 'none', alignItems: 'center', fontFamily: F.grotesk, fontWeight: 700, fontSize: '.62em', letterSpacing: '.02em', border: x.box ? `${px(2)} solid ${fg}` : 'none', padding: x.box ? '0 .25em' : 0 }, slot); if (x.img) { e.innerHTML = ''; el('img', { height: '1.1em' }, e).src = x.img; } else e.textContent = x.t || x; return e; });
  const def = el('span', { display: 'none' }, slot, s.default || '');
  return { update(b) {
    const k = E.oC(P(b, 0, .8)); box.style.opacity = k;
    const st = s.slotAt ?? 1, per = s.per || .5, n = opts.length, i = Math.floor((b - st) / per);
    opts.forEach((e, j) => e.style.display = (b >= st && i === j) ? 'inline-flex' : 'none');
    def.style.display = (b < st || i >= n) ? 'inline' : 'none'; slot.style.minWidth = (b < st || i >= n) ? '0' : '2.6em';
    if (l2) { const t2 = st + n * per + (s.gap ?? .8); typeClip(l2, P(b, t2, s.typeBeats || 1.2), 20); l2.style.clipPath = ar ? l2.style.clipPath : l2.style.clipPath.replace(/inset\((.*?) 0 (.*?) (.*?)%\)/, (m0, a, c, d) => `inset(${a} ${d}% ${c} 0)`); }
    return { dark: isDark(s.bg || '#E8E3D8') };
  } };
};

/* =====================================================================
 * timeline, transitions, render loop
 * ===================================================================== */
let acc = R.offset || 0;
R.scenes.forEach((s, i) => {
  const root = el('section', {}, stage); root.className = 'sc'; s.root = root;
  if (!S[s.type]) throw new Error('unknown scene type: ' + s.type);
  s.api = S[s.type](root, s);
  s.beats = s.beats || 4; s.t0 = acc; s.t1 = acc + s.beats * BEAT; acc = s.t1;
});
stage.append(ch, gr, flash, fade);
const DUR = acc + (R.tail ?? 0);
window.DUR = DUR; window.BEAT = BEAT;
window.TIMELINE = R.scenes.map(s => ({ type: s.type, t0: s.t0, t1: s.t1, in: s.in || 'cut', hit: s.hit, energy: s.energy }));

function trans(s, prev, b, t) {
  const kind = s.in || 'cut', d = s.inBeats || .5, p = clamp(b / d);
  const cur = s.root, pr = prev ? prev.root : null;
  cur.style.transform = 'none'; cur.style.filter = 'none'; cur.style.clipPath = 'none'; cur.style.opacity = 1;
  if (kind === 'cut' || p >= 1 || !pr) return false;
  pr.style.display = 'block'; pr.style.zIndex = 1; cur.style.zIndex = 2;
  prev.api.update(prev.beats + b, (t - prev.t0));
  const dir = s.dir === 'right' ? 1 : -1;
  if (kind === 'push') { const k = E.ioE(p); pr.style.transform = `translateX(${dir * k * W}px)`; pr.style.filter = `blur(${Math.sin(Math.PI * p) * 24 * U}px)`; cur.style.transform = `translateX(${-dir * (1 - k) * W}px)`; cur.style.filter = `blur(${Math.sin(Math.PI * p) * 24 * U}px)`; }
  else if (kind === 'iris') { const k = E.ioE(p); cur.style.clipPath = `circle(${k * 75}% at ${s.cx ?? 50}% ${s.cy ?? 50}%)`; }
  else if (kind === 'zoom') { const k = E.oE(p); pr.style.transform = `scale(${1 + 1.2 * E.iE(p)})`; pr.style.filter = `blur(${p * 30 * U}px)`; pr.style.opacity = 1 - p; cur.style.transform = `scale(${lerp(.82, 1, k)})`; cur.style.filter = `blur(${(1 - k) * 16 * U}px)`; }
  else if (kind === 'dissolve') { cur.style.opacity = E.io(p); }
  else if (kind === 'smear') { const k = E.ioE(p); pr.style.transform = `scaleX(${1 + 3 * k}) scaleY(${1 - .2 * k})`; pr.style.filter = `blur(${k * 40 * U}px)`; pr.style.opacity = 1 - k; cur.style.opacity = k; cur.style.transform = `scaleX(${lerp(1.6, 1, k)})`; cur.style.filter = `blur(${(1 - k) * 30 * U}px)`; }
  else if (kind === 'up') { const k = E.ioE(p); pr.style.transform = `translateY(${-k * H}px)`; cur.style.transform = `translateY(${(1 - k) * H}px)`; }
  else if (kind === 'shrink') { const k = E.ioE(p); pr.style.transform = `scale(${1 - k * .9})`; pr.style.borderRadius = `${k * 50}%`; pr.style.zIndex = 3; }
  return true;
}

window.renderAt = async t => {
  let i = R.scenes.findIndex(s => t >= s.t0 && t < s.t1); if (i < 0) i = R.scenes.length - 1;
  const s = R.scenes[i], prev = R.scenes[i - 1], b = (t - s.t0) / BEAT;
  R.scenes.forEach(x => { x.root.style.display = 'none'; x.root.style.zIndex = 0; x.root.style.transform = 'none'; x.root.style.filter = 'none'; x.root.style.borderRadius = 0; x.root.style.opacity = 1; });
  s.root.style.display = 'block';
  trans(s, prev, b, t);
  const res = s.api.update(b, t - s.t0) || {};
  const dark = res.dark ?? isDark(s.bg || C.cream);
  setChrome(s.chrome !== false && R.chromeOn !== false, dark, s.label, s.role);
  // flash on hits
  let fl = 0; if (s.hit) { fl = (s.hit === true ? .7 : s.hit) * (1 - clamp(b / .35)) ** 2; } flash.style.opacity = fl;
  // camera micro-shake on hits
  if (s.hit && b < .4) { const a = (1 - b / .4) ** 2 * 8 * U; s.root.style.translate = `${(hash(t * 97) - .5) * 2 * a}px ${(hash(t * 131) - .5) * 2 * a}px`; } else s.root.style.translate = '0 0';
  // grain shift
  const f = Math.floor(t * FPS); gr.style.backgroundPosition = `${Math.floor(hash(f) * 256)}px ${Math.floor(hash(f + 9) * 256)}px`;
  if (FILM) { const wv = R.weave ?? 1; stage.querySelectorAll('.sc').forEach(x => { if (x.style.display === 'block') x.style.translate = `${(hash(f * 3.1) - .5) * 2.2 * U * wv}px ${(hash(f * 7.7) - .5) * 2.2 * U * wv}px`; });
    const fl = 1 + (hash(f * 1.7) - .5) * .05; s.root.style.filter = (s.root.style.filter === 'none' || !s.root.style.filter ? '' : s.root.style.filter + ' ') + `brightness(${fl.toFixed(3)}) contrast(.94) saturate(.86) sepia(.08)`;
    dustDots.forEach((d, i) => { const on = hash(f * 13 + i) > .93; d.setAttribute('cx', hash(f + i * 5) * W); d.setAttribute('cy', hash(f * 2 + i) * H); d.setAttribute('opacity', on ? .35 : 0); });
    gr.style.opacity = R.grain ?? .14; }
  // global fade in/out
  fade.style.opacity = t < .12 ? 1 - t / .12 : clamp((t - (DUR - (R.fadeOut ?? .5))) / (R.fadeOut ?? .5));
  await Promise.all([...stage.querySelectorAll('img')].filter(im => im.src && im.offsetParent !== null).map(im => im.decode().catch(() => {})));
  await document.fonts.ready;
};
const qs = new URLSearchParams(location.search);
if (qs.has('t')) window.renderAt(parseFloat(qs.get('t')));
if (qs.has('play')) { const t0 = performance.now(); (function loop() { window.renderAt(((performance.now() - t0) / 1000) % DUR); requestAnimationFrame(loop); })(); }
})();
