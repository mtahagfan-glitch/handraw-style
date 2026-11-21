# Native vertical shorts

Cutting a landscape scene into 9:16 wastes two thirds of the drawing. Better shorts:
1. When planning the episode, choose 3–5 short stretches (45–80 s, hook → cliffhanger) and list their scenes.
2. Generate those scenes a second time in portrait (`portrait_16_9` / 1024×1536) with the same prompt and character
   sheet, upscale (`upscale.py` makes 1440×2560), depth as usual, into `plates_v/NN/`.
3. Render vertical: `SIZE=1080x1920 WORK=$PWD/parallax_v python3 "$SK/scripts/pipeline.py" plan|render` with
   `plates_v` linked as `plates` in a sub-folder for the short (same scenes.json subset and align.json).
4. `shorts.py` sees a portrait video and fills the frame (no blurred copy); title on top, captions, end card.
5. If time is short, the landscape fallback (picture in the middle over a blurred copy) is still fine.
Post shorts 1–2 days before the long video, captions from `captions.md`, link to the full video pinned.
