---
name: hbr-episode
description: End-to-end production of a «حبر وسالفة» episode — Saudi-dialect narrated story with hand-drawn ink illustrations in 2.5D parallax, the owner's own voice, scored music sections with transitions, motion-graphics inserts, a moving hook, 1440p export, thumbnail, publish kit and native vertical shorts. Use for any new episode or re-cut of the channel ("حلقة جديدة", "نبدأ المقطع", "سوّ الفيديو", "حبر وسالفة"), and when improving the channel's pipeline.
---

# حبر وسالفة — episode pipeline

One folder per episode: `output/<slug>/`. Run every script **from that folder**. `SK` = this skill's folder.
Shared channel assets live in `output/channel/` (fonts, intro, music library, SFX library, avatar/banner).
Lessons from the first two episodes are in [references/lessons.md](references/lessons.md): read it first.

## 0. Pick the story and plan the episode

- Topics: true stories with a twist (football, crime, secrets). Check that published reporting supports every claim.
- Structure every long video: **hook (≤30 s, the most dramatic moment, told out of order) → channel intro → story**.
  The hook ends on a question; the story answers it at the end.
- Write `scenes.json`: `[{"ar": "<Saudi-dialect narration>", "img": "<English image prompt>"}]`, one drawing per
  scene, a scene every 10–20 s of narration. Image prompts follow the channel style (ink line art on aged paper,
  muted colour accents, gold/blue light); describe what is seen, never ask for text in the image.
- Mark in `episode.json` (see `scripts/mix.py` docstring for the full schema):
  - `music` sections (see [references/music.md](references/music.md)),
  - `motion` — 2–3 scenes that become real moving shots ([references/motion-hooks.md](references/motion-hooks.md)),
  - `graphics` — stat cards, name tags, timeline, map, quotes (below),
  - `characters` — recurring people that need a reference sheet ([references/characters.md](references/characters.md)).
- Plan the shorts at the same time and draw their key scenes vertical ([references/vertical-shorts.md](references/vertical-shorts.md)).

## 1. Drawings

1. Character sheets first for recurring people, then every scene with the `gpt-image-2` skill
   (`landscape_16_9`, quality high), passing the character sheet with `--image` so faces stay the same.
2. Look at a contact sheet of all scenes before going on; redo the weak ones.
3. Upscale: `python3 "$SK/scripts/upscale.py" imgs/ plates/` (SeedVR on fal → `plates/NN/plate.jpg` 2560×1440).
4. Depth: `bash "$SK/../parallax/scripts/depth.sh" plates/NN/plate.jpg plates/NN/depth.png` per scene.

## 2. Voice

The owner records the narration (their own voice is the channel's voice) and sends `real/raw.m4a`.
- Word timings: ElevenLabs Scribe (`creative_transcribe_audio`) → `real/stt.json`, or Whisper via
  `npx hyperframes transcribe`. Ask before spending ElevenLabs credits.
- `python3 "$SK/scripts/align_real.py" --check` (match rate, retakes), then without `--check`
  → `parallax_real/voice.wav` + `align.json`. It shortens pauses > 0.75 s but never cuts a "pause" that still has
  voice in it (Whisper mistimes words; that bug once cut a player's age out of a sentence).
- Listen to the joins around every removed pause in the first minute before rendering.

## 3. Picture

```sh
export WORK=$PWD/parallax_real
python3 "$SK/scripts/pipeline.py" plan            # shots.json: one camera move per ~6.5 s
python3 "$SK/scripts/pipeline.py" render          # one HyperFrames render per scene, resumable
```
Rendering is ~2 frames/s on CPU (an 18-min episode ≈ 4 h). Run it in the background; a 2-hour limit kills it,
just start it again — finished scenes are skipped. Merge two shots of a scene by editing `shots.json` when a cut
lands mid-sentence.

- **Moving shots**: `python3 "$SK/scripts/motion.py" plates/NN/plate.jpg veo/NN.mp4 "<motion only>"` then splice
  over the parallax scene with `xfade` so the action peaks on the spoken word ([motion-hooks](references/motion-hooks.md)).
- **Graphics**: `python3 "$SK/scripts/mg.py" <stat|name|timeline|map|quote> '<json>' out.(mp4|webm)`.
  `.mp4` = full card (cut it in as its own beat), `.webm` = transparent overlay (name tags on a scene).
  Use: a name tag the first time each key person appears, a stat card for every number the viewer must remember,
  a map when the story travels, a timeline for "years of failure" stretches. 4–8 graphics per episode.
  Overlay: `ffmpeg -i video/NN.mp4 -c:v libvpx-vp9 -i tag.webm -filter_complex "[0][1]overlay=enable='between(t,1,5)'" ...`
  (keep the scene's exact frame count).

## 4. Sound

`W=parallax_real python3 "$SK/scripts/mix.py"` → `parallax_real/final_audio.wav`:
voice, an SFX on every scene cut (rules in `episode.json`), music sections ducked under the voice, and a
riser + soft boom + breath at every music change so the viewer feels a new chapter. Then
`python3 "$SK/scripts/pipeline.py" assemble parallax_real/final_audio.wav` → `parallax_real_25d.mp4` + `.srt`.
Watch every music change and the first 2 minutes before exporting.

## 5. Export

`bash "$SK/scripts/final.sh" parallax_real <slug>` → hook + intro + story at 2560×1440 (YouTube gives 1440p
uploads its better codec, so even 1080p viewers see a sharper picture), shifted `.srt`, `<slug>_times.json`
(chapter times), and `<slug>_1440p_hevc.mp4` under 400 MB for sending. Disk is small: delete superseded renders.

## 6. Publish kit, thumbnail, shorts

- `youtube-publish-kit` skill: thumbnail, 3 titles, description, chapters (from `<slug>_times.json`), tags.
  Thumbnail at **2560×1440**: upscale the drawing with SeedVR, then draw the headline with Skia at that size
  (JPEG ≤ 2 MB).
- Shorts: `python3 "$SK/scripts/shorts.py" parallax_real parallax_real_25d.mp4 shorts_hd` (1440×2560, burned
  captions, end card «القصة كاملة في القناة») + `captions.md`. Better: render the short's scenes natively
  vertical ([vertical-shorts](references/vertical-shorts.md)).
- Post shorts 1–2 days **before** the long video as teasers, and pin the long video link in each.

## 7. After publishing

A week after release, review retention with the owner: [references/retention-review.md](references/retention-review.md).
Write what was learnt into `references/lessons.md` so the next episode starts better.

## Generators available

- Images: `gpt-image-2` skill (fal). Upscale: SeedVR (fal). Video: Kling / Veo on fal (`motion.py`).
- Music: library in `output/channel/music/library.json` first; new cue via `music_gen.py` (Lyria 2 on fal) or a
  prompt for the owner to run in Google Flow Music ([music.md](references/music.md)). Do not lock onto one source.
- ElevenLabs is connected (voice design, SFX, Scribe). Ask the owner before spending its credits until they say the
  subscription issue is solved.
- Google Flow / Flow Music have no API: when they are the best tool, hand the owner a ready prompt and the exact
  part of the result to keep.
