---
name: bassam-reel
description: Edit and animate Arabic motion-graphics videos in the "Bassam" editorial-recap style — a question hook with a giant chrome number, a persistent editorial frame (year rule + project/discipline labels), one idea per bar cut to a ~129 BPM grid, value-flipping backgrounds, object-to-object transitions, a fast AI-image flurry, a calm narrative break, stats, a collage of all work, "+أكثر" and a handle. Use whenever the user asks to make, edit, montage or animate a video "بأسلوب بسام", "زي مقطع بسام", a recap/portfolio/showreel ("ايش سويت آخر …"), a project or brand reel, a real-estate or product promo in this editorial style, or hands over images/clips/text and asks for a professional motion-graphics edit. Renders locally (Playwright + FFmpeg) to MP4 with beat-synced music and SFX, in 4:3, 16:9 or 9:16.
---

# Bassam reel

The reference (`references/breakdown.md`) is a 48 s Arabic recap of 70 days of work. What makes it look
professional is not effects. It is **discipline**: one idea per bar, every cut on the beat, the background
value flips on every scene, each object turns into the next one, a quiet editorial frame holds it all
together, and the ending answers the opening.

The engine in `engine/` turns a `reel.json` storyboard into a finished MP4. You write the storyboard and
supply the assets. The engine handles timing, motion, chrome, grain, music and SFX.

## Workflow

1. **Intake (ask once, only for what's missing).** Format (default 4:3 1440×1080 like the reference, or
   9:16 1080×1920 for TikTok/Reels/Snap, or 16:9), the hook question, the projects/sections with their
   name · category · discipline, the assets (images, clips, logos), numbers worth counting, the end handle,
   and whether they have a licensed music track (else the engine synthesises one).
2. **Storyboard first.** Write `reels/<name>/reel.json` (see `examples/demo-recap.json`). Plan in bars:
   - 15 s ≈ 8 bars · 30 s ≈ 16 bars · 48 s ≈ 26 bars at 129 BPM (1 bar = 1.86 s).
   - Arc: **hook (1 bar)** → identity/brand (2–4) → projects (1–2 bars each) → **flurry (1–2)** →
     **break (3–6, energy "break", calmer scenes: nodes/scale/spot)** → stats (1) → grid (1) → more (¾) → handle (¾).
   - Check the rules below against the storyboard *before* rendering.
3. **Preview stills:** `python3 .claude/skills/bassam-reel/engine/build.py reels/<name>/reel.json --sheet`
   (one still per scene midpoint plus `out/stills_sheet.jpg`). Look at the sheet. Fix layout and text overflow.
   For a specific moment use `--stills 1.2,6.5`.
4. **Render:** `python3 .claude/skills/bassam-reel/engine/build.py reels/<name>/reel.json` writes
   `out/<name>.mp4` and `out/<name>_sheet.jpg`. Takes about 0.15 s per frame across 3 workers, so a 30 s reel
   renders in about 1 min.
5. **Verify** (below), then deliver the MP4 and list what's assumed (generated music, illustrative visuals).

To study a new reference first:
`python3 .claude/skills/bassam-reel/engine/analyze.py ref.mp4 out/ref` writes timestamped contact sheets
plus cuts, tempo, onsets and the offset of each cut from the beat.

## The rules (check every storyboard against these)

1. **One idea per bar.** A scene is 4 beats by default. Use 2 beats only for punches, and ½ beat only inside a flurry.
2. **Cut on the beat, animate between beats.** The engine places every scene start on a beat. Inside a scene,
   things land on whole and half beats (tiles and likes pop on 16ths).
3. **Flip the value every scene.** Dark → cream/paper → saturated colour → dark. Never put two consecutive
   scenes on the same background.
4. **Transform, don't cut, between related ideas.** Use `in:"push"` (horizontal whip with motion blur),
   `"zoom"`, `"iris"`, or a `ripple` scene whose disc becomes the next background. Keep hard cuts for
   new chapters and the flurry.
5. **The editorial frame is the glue.** Every scene gets a `label` ("المشروع · النوع") and a `role`
   (the discipline). Hide the frame only on the hook, more and handle.
6. **Type voices.** The hook uses `ruqaa`/`naskh`, which is emotional and classical. Statements use
   `display`/`kufi`. Oversized words (`device.bleed`, `stroke`) should break the frame edges. Use one
   accent colour per scene. Iridescent chrome appears only in the hook (and AI flurry images).
7. **Show the work.** Each project scene proves something: a counter, construction lines, a measurement
   bracket, a post with likes, a stats card.
8. **Energy curve.** Hook hit → build → flurry peak → calm break (music drops, slower scenes) → stats/grid
   rise → resolve. Set `energy` on the scenes. Put `drop:true` on the scene after a break to get a riser into it.
9. **Bookend.** The hook asks a question («ايش سويت آخر 70 يوم؟») and the ending answers it
   («+أكثر» → handle).
10. **Numbers in Arabic text** are bidi-isolated automatically. Write units as `م²`, `ألف`, `مليون`, and keep
    digits Western (0–9) unless the user asks for Arabic-Indic.

Visual reference: `references/frames/` holds timestamped contact sheets of the original at 5 fps, plus a
full-size frame of the chrome. Look at them when matching the style.

## Scenes (full props in `references/scenes.md`)
`hook` · `title` · `full` · `tiles` · `construct` · `stroke` · `palette` · `ripple` · `glyph` · `halo` ·
`counter` · `helix` · `device` · `appicon` · `likes` · `flurry` · `scale` · `nodes` · `spot` · `bounce` ·
`stats` · `grid` · `more` · `handle`

How to map user content to scenes:
| User has… | Use |
|---|---|
| a logo / brand mark | `tiles` → `construct` → `stroke` (wordmark) → `palette` |
| a wordmark or Arabic name | `stroke` or `glyph` |
| an app / social account / content | `device` (screen recording or screenshot in a phone), `appicon`, `likes`, `bounce`, `stats` |
| a big number (followers, m², views) | `counter`, or `scale` (`measure`) for physical size |
| many AI or visual outputs | `flurry` (`per` .5, `card` true) |
| a process or a set of linked ideas | `nodes` |
| a hero product or object | `spot`, `scale` |
| footage (drone, b-roll) | `full` with a caption, or as `src` inside any scene |
| everything at the end | `grid` |

## Format notes
- **4:3 (1440×1080)** is the reference look. **9:16 (1080×1920)**: layouts auto-adapt (chrome margins,
  tile grid 4×7, phone larger, stats stacked). Check the stills sheet, since bleed words and sides need
  shorter text vertically.
- `theme` in reel.json overrides colours (`cream`, `paper`, `ink`, `accent`, `orange`, `lilac`…).
- `chrome:{left,right}` sets the top rule ends (years by default). `grain` sets grain opacity (default .07).
- Music: `"music":"track.mp3","musicOffset":12.3` with `bpm` set to the track's tempo (run `analyze.py`
  on the track to get BPM and phase, and set `offset` so the first downbeat lines up). Without music, a
  129 BPM bed with impacts, whooshes, ticks and pops is generated from the storyboard.

## Verify before delivering
- Look at `out/<name>_sheet.jpg`: values alternate scene to scene, no text overflows or overlaps the chrome,
  and no scene is empty.
- Check every transition with a strip:
  `ffmpeg -i out/x.mp4 -vf "select='between(t,T-0.3,T+0.5)',scale=360:-1,tile=8x1" -frames:v 1 strip.jpg`.
- Listen-proxy: loudness is −14 LUFS (`ffmpeg -i out/x.mp4 -af ebur128 -f null -`). You cannot hear it,
  so say so and let the user listen.
- Tell the user what is illustrative or generated, and never invent facts or numbers for their projects.

## Assets that the engine does not draw
Iridescent 3D objects, vintage engravings, portraits and products come from the user, or from Flow /
Nano Banana image generation. Prompt pattern for the flurry look:
`"glossy iridescent chrome 3D <object>, holographic rainbow reflections, deep black background, studio lighting, ultra detailed, centered"`.
