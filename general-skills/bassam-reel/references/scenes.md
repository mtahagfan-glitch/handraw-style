# Scene library — props reference

Every scene accepts the common keys:

| key | meaning |
|---|---|
| `type` | scene type (below) |
| `beats` | length in beats (default 4 = one bar). Use 2 for punchy beats, 0.5–1 inside flurries |
| `bg` / `fg` | background / main colour (hex). Chrome colour follows `bg` automatically |
| `label` | bottom-left chrome text: "project · category" |
| `role` | bottom-right chrome text: the discipline (تحريك، تصميم، مونتاج، تصوير…) |
| `chrome` | `false` hides the editorial frame (hook, more, handle) |
| `in` | transition into this scene: `cut` (default) · `push` (+`dir`:"right") · `zoom` · `iris` (+`cx`,`cy` in %) · `up` · `shrink` |
| `inBeats` | transition length in beats (default 0.5) |
| `hit` | flash + micro-shake + impact SFX on the downbeat (`true` or 0–1 strength) |
| `energy` | music energy for this scene: `hit` · `full` · `flurry` · `break` · `none` (auto from type) |
| `drop` | `true` puts a 1-bar riser before this scene |

Media values (`src`, `img`, `srcs[]`) can be `"file.jpg"`, `"clip.mp4"` or `{"video":"clip.mp4","start":2,"speed":1.5}`. Paths are relative to reel.json.

Fonts: `ruqaa` (Aref Ruqaa) · `naskh` (Amiri) · `display` (Alexandria) · `kufi` (Reem Kufi Fun) · `sans` (IBM Plex Sans Arabic) · `readex` (Readex Pro).

---

### hook — question + giant chrome number (open every recap with it)
`words: [{t, font, bg, fg, size, beats, style:"pop"|"slide"}]`, `big`, `bigSub`, `bigSize`, `bigBg`.
One word per beat; `slide` = horizontal whip with motion blur. The chrome number is faux-3D (16 extruded layers, rotating iridescent gradient).
```json
{"type":"hook","beats":4,"hit":0.5,"chrome":false,"words":[{"t":"ايش","font":"ruqaa","bg":"#050505"},{"t":"سويت آخر","font":"naskh","bg":"#F4F2EE","style":"slide"}],"big":"70","bigSub":"يوم؟"}
```

### title — general statement (most-used workhorse)
`text`, `sub`, `font`, `size`, `mode:"rise"|"blur"|"weight"|"type"`, `accent:["word"]`, `accentColor`, `align`, optional `src` (media behind, dimmed by `dim`).

### full — full-bleed photo/video with rising caption
`src`, `caption`, `size`, `zoom` (push amount, default .06).

### tiles — logo flashes on colour fields, then brand-tile grid
`mark` (text) or `img`, `font`, `size`, `flashes:[3 colours]`, `tileColors:[…]`, `seed`.

### construct — logo with geometric construction guides
`mark`/`img`, `guide` (line colour), `size`.

### stroke — huge outlined word draws itself while panning, then lands filled with a latin twin
`word`, `latin`, `font`, `size`, `bigScale` (outline size × H, default .95).

### palette — identity bar + colour rows splitting on beats
`title`, `titleBg`, `rows:[[colours],[colours]]`.

### ripple — concentric rings, then an ink disc irises over (use as a transition scene)
`color`, `iris` (disc colour). Next scene should start on the iris colour.

### glyph — wordmark built piece by piece (RTL steps) + typed credit
`word`, `font` (default kufi), `size`, `credit`, `steps`.

### halo — mark assembled from two slices, ring descends, coloured bokeh
`mark`/`img`, `ring`, `glowA`, `glowB`.

### counter — illustration/photo + number counting + disc pop
`img`, `from`, `to`, `unit`, `prefix`, `suffix`, `decimals`, `discColor`, `countBeats`.

### helix — generative DNA of dots collapsing into a soft cell
`colors:[…]`.

### device — phone mockup + oversized bleed words + optional word swap and side caption
`src` (screen media) or `mark`, `bleed:["word-right","word-left"]`, `side`, `swap:["عن","عندك"]`, `swapAt`, `swapEvery`, `sparkles`, `glow` (rgba colour).

### appicon — app icon with neon glow pulsing on beats
`mark`/`img`, `glow`, `fill`.

### likes — post card, icons multiply on 16ths, counter climbs
`img`, `title`, `text`, `icon:"thumb"|"heart"`, `color`, `count`, `step`.

### flurry — hard cuts every `per` beats (0.5 = 8ths, 0.25 = 16ths)
`srcs:[…]`, `per`, `card` (true = floating card with tilt instead of full-bleed). Give it `"energy":"flurry"`.

### scale — monumental object on a huge disc, tiny human, measurement bracket
`src`, `measure` ("5000 سنة"), `objW`, `objH`, `disc`, `discHi`, `zoomFrom`.

### nodes — glass cards one per beat, then connecting lines (triangle/network)
`src` (bg media, else generated starfield), `nodes:[{t,x,y,color}]` (x,y as 0–1), `every`, `closed`.

### spot — object in a hanging frame, frame falls, spotlight cone
`src`, `size`, `bg` (wall colour).

### bounce — platform icons pop, glossy ball bounces per beat
`icons:["yt","ig","tt","x","snap"]`, `bg`.

### stats — dashboard cards slide in, area charts draw
`title`, `chip`, `cards:[{k,v,color}]`.

### grid — collage of all work assembles tile by tile, then pulls back
`srcs:[…]`, `cols`.

### more — "+أكثر" gains a plus each beat while the background flips
`word`, `plus`, `flips:[colours]`.

### handle — letter-spaced end tag
`text`, `size`, `bg`, `fg`.

---
## Adding a new scene type
Add `S.mytype = (root, s) => { /* build DOM once */ return { update(b, sec) { /* pure function of b */ return { dark } } } }` in `engine/engine.js`.
Rules: never use `Math.random()` at draw time (use `rnd(seed)` at build time or `hash(i)`), animate only transform/opacity/filter/clip-path, and drive everything from `b` (local beats).

---
## Manifesto-film scenes (used by the `manifesto-film` skill; set `"look":"film","audio":"manifesto","chromeOn":false`)
- `decode` — `text`, `font` (grotesk), `size`, `buildBeats`, `glyphs`, `smear`
- `words` — `shots:[{src, words, fx: fade|big|smear|spread|scatter, beats, pos, positions, size, zoom, dim, bg, fg}]`, `wordBeats`, `size`, `font` (serif)
- `slugs` — `items:[{src, t}]`, `per`, `size`
- `swap` — `before`, `default`, `after`, `slot:[{t, box}|{img}]`, `per`, `slotAt`, `line2`, `typeBeats`
- `full` also takes `zoomTo` and `zoomEase:"in"` for long push-ins; transitions add `dissolve` and `smear`.
Fonts added: `serif` (Newsreader / Noto Naskh Arabic), `mono` (IBM Plex Mono), `grotesk` (Space Grotesk), `naskh2` (Noto Naskh Arabic).
