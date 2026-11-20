---
name: still-to-3d-shot
description: Turns one reference still into a short, realistic, editable 3D shot without any video model. Solves the still's camera from its vanishing points, builds the room in Tesseract with scripts and matching textures, has two critic agents compare every round to the reference, animates one slow camera move with a few small story events, adds sound effects timed to the picture, path-traces it, and opens on a grey clay view that wipes to the render as proof it is 3D. Use for "make a 3D scene from this image", "realistic scene without a video model", "cinematic establishing shot", "حوّل الصورة لمشهد ثلاثي الأبعاد", "مشهد 3D واقعي", or an opening or B-roll shot for a documentary.
---

# Still to 3D shot

One generated still becomes a 10 to 15 second shot that is real geometry, real lights and a real camera. Because the result is one editable Tesseract project, the camera can be moved and the shot rendered again; a video model cannot do that.

The method is Mirage's, from the thread in [references/thread.md](references/thread.md) (a 13 second, 312 frame kitchen shot). This skill is the order of work, the checks, and one tool the method needs that Tesseract does not ship: a camera solver.

## What it needs

| Need | What to use |
| --- | --- |
| 3D engine | Tesseract with its `tesseract-3d` skill and the `tsrct` CLI. Install: `npx skills add mirage-hq/Tesseract`, pick the 3D skill, then follow that skill's `references/installation.md`. |
| Stills and textures | Any image model. In this repo: the `gpt-image-2` skill. |
| Sound effects | ElevenLabs sound effects (`POST /v1/sound-generation`), or any SFX source. Simple tones are synthesised with ffmpeg. |
| Mixing, the proof wipe | ffmpeg |

Three things to settle before starting:

- **Tesseract is not bundled here.** Its terms do not allow redistributing it, and installing it means accepting them: free for personal and commercial use below US$1M yearly revenue, usage telemetry on by default (`tsrct telemetry disable`). Ask the user before the first install on a machine.
- **Path tracing wants a GPU.** The source shot took about 45 minutes for 312 frames at 1080p and 128 samples on one RTX PRO 6000. On a machine with no GPU (Mesa lavapipe) expect it to be far slower: render a 16-sample still first, time it, and tell the user the estimate before any full export.
- **Follow the `tesseract-3d` skill for every Tesseract action.** Property names and commands come from `tsrct project schema`, never from memory or from this file.

## Workflow

Stop for the user at the two gates.

### 1. Reference still

One image is the art direction for the whole shot: layout, materials, light, mood.

- Write the prompt as a place with a lighting story (the source: "a messy 80s kitchen, rainy night, full moon"). Ask for a wide interior with clear straight edges in two directions: counters, floor boards, window frames. The camera solve needs them.
- No people in the room. Anything alive is added later as a 2D card (step 4).
- Generate at the delivery aspect ratio and do not crop it afterwards: cropping moves the optical centre and breaks the solve.
- **Gate:** the user picks the still.

### 2. Solve the camera

Find the lens and the camera pose that took the picture, so the 3D room lines up with it.

1. Open the still and read pixel coordinates of straight edges: at least two that run left to right in the room, at least two that run into the room at right angles to them, and if possible two verticals. Spread them across the frame.
2. Pick one upright thing of known size that stands on the floor (a worktop is about 0.9 m, a door about 2.0 m) and note its foot and its top.
3. Run the solver:

```bash
python3 scripts/solve_camera.py --size 1920x1080 \
  --x-lines "x1,y1,x2,y2;x1,y1,x2,y2" --z-lines "…;…" --y-lines "…;…" \
  --ref "footx,footy,topx,topy,0.9"
```

It prints the focal length for a 36 mm sensor, field of view, tilt, roll, heading and eye height (the source shot solved to 21 mm and 134 cm). `--selftest` checks the maths.

4. Create the Scene3D camera with a physical lens of that focal length and sensor, at that eye height, tilt, roll and heading. Set `pixelsPerMeter` once and build everything in metres.
5. Check the solve before building anything: put grey boxes where the floor, the back wall and one counter are, render a raster preview, and blend it over the still at half strength:

```bash
ffmpeg -i ref.png -i blockout.png -filter_complex "[0][1]blend=all_mode=average" -frames:v 1 overlay.png
```

The box edges must run along the still's edges. If they fan out or pinch, re-mark the lines; do not fix it by nudging the camera by eye.

### 3. Build

Write scripts that emit the Tesseract action batches. A script per group is easy to rerun after a critic's fix list; hand-edited JSON is not.

Build from large to small, and render a preview after each group:

1. Room shell: floor, walls, ceiling, window and door openings.
2. Fixed furniture: cabinets, counters, shelves.
3. Appliances and anything that will move or light up.
4. Props, clutter and decals. Mess is what makes a room read as real.
5. Materials, then lights. Match the still's light sources one by one (window, lamp, screen glow); do not add fill lights the still does not have.

Textures: crop the matching area of the still, give it to the image model as the style reference, and ask for a flat, evenly lit, tileable surface (no shadows, no perspective). Lighting comes from the scene, not from the texture.

Critics: after each round, two independent critic agents compare the path-traced preview with the still and return a numbered fix list. Use the `tesseract-3d` skill's critic review as written (an art director and a specialist for the scene's purpose, at least 8.5 from both, at most three rounds). Give them the still and the render side by side, and ask for differences in layout, scale, material and light, in that order.

**Gate:** show the user the still and the matched render side by side.

### 4. Animate

Keep it small. The source shot has one camera move and four events.

- **Camera:** one slow move, usually a push-in. No cuts.
- **Story events:** two or three things that happen in order and cause each other. The source: a microwave turntable spins while its display counts down; at :00 it beeps three times and its lamp goes out.
- **Weather and atmosphere in depth:** rain, snow or dust on three planes at different distances, so the camera move gives them parallax.
- **Flashes are real lights:** lightning, a passing car, a TV. Key a light in the scene so the flash lands on every surface and reflection.
- **One reveal:** a single frame or beat that rewards a second viewing (the source hides a creature in the yard, visible only in the closest lightning strike).

Verify with filmstrips at each event's time: a stored keyframe is not proof that anything moved.

### 5. Sound

List every sound with its picture time first, then make them.

- Ambiences and hits (rain, hum, thunder): generate as sound effects, one file per sound.
- Simple tones (beeps, clicks): synthesise them; a generator is worse at exact pitch and length.

```bash
ffmpeg -f lavfi -i "sine=frequency=2000:duration=0.18" -af "afade=t=out:st=0.14:d=0.04" beep.wav
```

- Time each sound to its picture event, to the frame. Thunder follows its flash by distance ÷ 343 m/s: a strike 1 km away is heard 2.9 s later, a close one almost at once. Closer strikes are also louder and sharper.
- Keep the ambience under the events, and duck it briefly around the loudest hit.

### 6. Render

1. Path-traced stills at the event times with `--samples 16`. Fix what they show.
2. A one-second export at the final size, frame rate and samples (128 by default). Read the seconds per frame it reports, multiply by the frame count, and tell the user the estimate.
3. Full export. On Linux the bundle has no H.264 encoder: pass the external ffmpeg flags from the `tesseract-3d` install guide.
4. Check consecutive frames for shimmer in still areas; raise the samples if there is any.

### 7. Proof and honesty

- **Open on clay.** Render the same camera move with every material replaced by one neutral grey, then wipe from the clay version to the final render in the first two seconds. It shows the viewer the shot is geometry. Both clips stay in step, so the camera move and the sound are not shifted (an `xfade` would delay the final render by the wipe's offset):

```bash
ffmpeg -i clay.mp4 -i final.mp4 -filter_complex \
  "[0][1]blend=all_expr='if(lte(X,W*clip((T-0.8)/1.2,0,1)),B,A)'" -c:v libx264 -crf 16 -pix_fmt yuv420p shot.mp4
```

- **Say what is 2D.** The source lists its cheats: the view outside the window is a relit 2D backplate, and the rain and the creature are 2D cards. Use the same cheats (anything outside the room, anything organic, anything too small to model), and list them when handing over.
- **Deliver** the `.tsrct` project, the video, the reference still, the solved camera values and the list of 2D elements.

## Mistakes to avoid

- Building before the blockout overlay matches. Every later step inherits a wrong camera.
- Baked shadows or perspective in a generated texture: it fights the scene's lights.
- More than one camera move, or events that do not cause each other: the shot stops reading as one moment.
- Judging realism from raster previews. Critics and the user see path-traced frames only.
- Promising a render time from the source's GPU. Time a short export on the machine that will render.
