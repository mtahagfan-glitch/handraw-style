---
name: parallax-2-5d
description: Turn still images into MagnatesMedia-style 2.5D / 3D parallax shots (camera pans, push-ins and orbits where near objects move faster than far ones) inside a HyperFrames video, free and local. Use when the user asks for parallax, 2.5D, "3D photo", depth motion, Ken Burns with depth, or MagnatesMedia-style animation of images, in any project.
---

# 2.5D depth parallax for stills

A depth map per image (Depth Anything V2 Small, run locally) drives a WebGL shader that shifts
every pixel by its depth while a virtual camera pans, pushes or orbits. No layer cutting, no
inpainting, no paid service. Output is a normal HyperFrames scene, so it renders, seeks and
edits like any other.

Requirements: Node 22, Python 3 with numpy + Pillow, curl, a HyperFrames project
(`npx hyperframes init <dir>`; read the `hyperframes` skill for the composition contract).
First run downloads the model (~99 MB) and, if HyperFrames has not already, onnxruntime-node,
into `~/.cache/parallax-2-5d`.

`SK` below = this skill's folder (the directory containing this file).

## Steps

1. **Pick images that parallax well.** Clear depth: something near (candle, railing, hand),
   a subject in the middle, a far background. Flat images (posters, top-down documents,
   screenshots) give little effect; use a plain zoom for those. Generate at the video's aspect
   when possible (9:16 for reels). In ElevenLabs the aspect is a node setting, not prompt text.
   A wider image still works: the camera pans across it, but crops look softer.
2. **Per scene**, inside the project:
   ```sh
   mkdir -p assets/scenes/<id>
   cp <image> assets/scenes/<id>/plate.jpg          # jpg; convert png with ffmpeg -i x.png -q:v 2 plate.jpg
   bash "$SK/scripts/depth.sh" assets/scenes/<id>/plate.jpg assets/scenes/<id>/depth.png
   ```
   Look at depth.png: white must be near. If a key object is the wrong shade, the move will
   tear around it; choose a gentler preset or lower the swing.
3. **Write the scene:**
   ```sh
   python3 -I "$SK/scripts/make_scene.py" --project . --id <id> --duration 2.5 \
     --size 1080x1920 --preset pan-right --mood warm \
     --params '{"cx":[0.40,0.55],"cy":[0.45,0.42]}'
   ```
   It prints the host `<div>`; paste it into `index.html` with the right `data-start`.
   Presets and tuning: [camera moves](references/camera-moves.md).
4. **Check and look:** `npx hyperframes check`, then `npx hyperframes snapshot --at <t1>,<t2>`
   at the start and end of each scene and read the frames. Fix framing with `cx/cy/zoom`.
   WebGL "GPU stall due to ReadPixels" warnings are harmless.
5. **Render** when approved: `npx hyperframes render --fps 24 --quality delivery -o out.mp4`
   (match the fps of any footage in the cut).

## Rules that keep it looking right

- Swing (`sx`/`sy`) 0.01–0.04. Above that, edges smear. Bigger move = more zoom, not more swing.
- One move per shot, eased (`sine.inOut`). Shots of 2–4 s; cut on the sentence.
- `focus` = the depth that stays pinned: put it on the subject (0.5–0.7), so the background
  drifts behind it and the foreground sweeps past.
- Text over a bright plate (paper, sky) needs a dark scrim behind the caption.
- Dust motes + candle flicker come from `--mood`; use `none` for clean or corporate looks.
  Keep motes ≤ 25 per scene (HyperFrames warns on many heavy overlays).

## Other tools

- Tesseract (Mirage, `tsrct`): can do the same with a custom WGSL shader and a displacement
  map, or as a Scene3D mesh. Heavier; on Linux without a GPU it needs Mesa lavapipe. Use this
  skill first; reach for Tesseract only for a real 3D scene.
- `scripts/fillplate.py` + `npx hyperframes remove-background`: the older two-layer method
  (cutout + filled background). Works only for people (the matting model is human-only).
