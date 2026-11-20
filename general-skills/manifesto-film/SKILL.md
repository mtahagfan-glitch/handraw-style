---
name: manifesto-film
description: Edit a cinematic brand manifesto film in the style of Anthropic's 72-second "What we make of this moment" spot — a wordmark that decodes letter by letter on cream paper, a chain of "هل نقدر / Can we…?" questions told ONE WORD PER SHOT over cinematic footage (small serif type, occasional giant smeared, scattered or spread words), a breath (space/earth push-in), a fast proof montage of real projects labelled "\ project-slug \" in mono over macro textures, a closing serif sentence whose key word cycles through client names/logos, and the wordmark again. Film look (heavy grain, halation, vignette, gate weave, muted warm grade) and a cinematic score with a piano note per word. Use when the user asks for a video "زي إعلان Anthropic", "بأسلوب أنثروبيك", a manifesto, brand film, mysterious/surreal/artistic trailer-like edit ("زي تريلر Fable"), a vision/mission video, or a cinematic word-by-word edit. Renders locally to MP4 (16:9, 9:16 or 4:3).
---

# Manifesto film

Reference analysis (with corrections to a third-party analysis): `references/breakdown.md`.
Visual reference: `references/frames/` (timestamped contact sheets at 4 fps plus `details.jpg`).

The film works because **the sentence is the edit**: every word gets its own image, so the viewer reads and
watches at the same time. The images are cinematic and literal to the word. The type is quiet. The rhythm
accelerates from reading pace to a fast proof montage, then stops dead on paper.

## Engine
This skill uses the shared engine in `.claude/skills/bassam-reel/engine/` (same `build.py`, same `reel.json`
format). Set these at the top of `reel.json`:
```json
{"format":{"w":1920,"h":1080,"fps":25}, "bpm":90, "look":"film", "audio":"manifesto", "chromeOn":false, "grain":0.14}
```
- `look:"film"` adds per-frame gate weave, flicker, dust, warm/teal grade and vignette in the page, plus a
  final FFmpeg pass with halation (screen-blended highlight bloom), temporal grain and a lens vignette.
- `audio:"manifesto"`: a drone bed with a piano note on every word, ticks while the logo decodes, a riser in
  the breath, a driving pulse with a pluck per slug in the proof montage, and soft chords on the paper.
- `bpm` here is the **reading pulse**. At 90 BPM, 1 word = 1 beat = 0.67 s. Use `wordBeats` 0.75 for a
  faster read, or `beats` on a shot to hold it.

Build: `python3 .claude/skills/bassam-reel/engine/build.py reels/<name>/reel.json` (`--sheet` for stills).
Full example: `examples/manifesto-demo.json`.

## Scenes for this style
| scene | role | key props |
|---|---|---|
| `decode` | wordmark builds char by char, glyph flicker; `smear:true` stretches it out into the next scene | `text`, `font` (`grotesk` default), `size`, `buildBeats`, `glyphs` |
| `words` | **the manifesto**: one word (or a few) per shot over media | `shots:[{src, words, fx, beats, pos, positions, size, zoom, dim}]`, `wordBeats`, `size`, `font` (`serif`) |
| `full` | the breath: slow push into one image | `src`, `zoomTo` (e.g. 1.9), `zoomEase:"in"` |
| `slugs` | proof montage with `\ slug \` labels | `items:[{src, t}]`, `per` (0.5 beats) |
| `swap` | closing serif sentence; one slot cycles through names or logos, then line 2 types in | `before`, `default`, `after`, `slot:[{t, box} or {img}]`, `per`, `slotAt`, `line2` |

Word `fx` values: `fade` (default, small serif) · `big` (fills the frame) · `smear` (big, then stretches out with
motion blur; pair with the next shot) · `spread` (the shot's words accumulate at `positions` [[x,y]…], e.g.
«Map / an / entire») · `scatter` (letters fly in and assemble; Latin only, since Arabic letters must stay joined).

Transitions: `in:"smear"` (logo to first shot), `"dissolve"` (into the breath and onto the paper), and
hard cuts everywhere else.

## Workflow
1. **Write the manifesto first.** 6–13 short questions on the theme (هل نقدر… / Can we…), each 2–6 words,
   then one closing sentence with a swappable key word. Arabic reads RTL, and the engine keeps word order and
   direction correct.
2. **One image per word.** For every word, pick the most literal and cinematic shot (a clip or still).
   Vary scale (macro, wide, face, aerial). Ask the user for footage, or generate it with Flow/Veo, using a
   short prompt per shot: `"cinematic 35mm film still, <subject>, shallow depth of field, natural light, muted warm grade, film grain"`.
   Macro textures for the slug montage: `"extreme macro of <texture>, vivid organic colour, 16mm film"`.
3. **Proof montage:** 10–30 real project slugs, kebab-case (`\ khalidiyah-12694m2 \`), each on a texture
   or frame. **Use real projects only and never invent clients.**
4. **Closing:** «ما نصنعه بهذه اللحظة، / سيصنع هذه اللحظة.», with the slot cycling the user's clients,
   projects or places. Use logo images (`{img}`) only with the user's permission.
5. Stills → check → render → verify (`--sheet`; check that words are readable at phone size; loudness −14 LUFS).

## Rules
1. A word never sits on an unrelated image. If no literal shot exists, use a texture.
2. Small type is the default (`size` around 60 at 1080p for Arabic, 46 for Latin). Big or smear only once or
   twice per film, on the emotional word.
3. Every question ends on its own shot with the "؟", and the next question starts on a new subject.
4. Energy: reading pace → breath (4–5 beats, slow) → fast montage (½ beat each) → stillness on paper (8 beats) → logo.
5. Keep the grade unified. The film look covers mismatched sources, but avoid footage with burnt-in text or
   UI (finished ads, screen captures).
6. Use the same wordmark animation to open and close.
7. Do not use Anthropic's name, logo or exact slogan in the user's work. Take the grammar, not the brand.

## Format notes
16:9 is native. For 9:16, set `format` to 1080×1920; the words stay centred, use `spread` positions within
x .2–.8, and vertical footage fits best.
