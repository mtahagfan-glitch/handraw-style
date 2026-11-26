# Channel drawing style (from episode 4)

The old style (ink line art on aged paper, muted accents) reads as a sketch. The new style is cinematic: it holds
up at 1440p, gives the parallax camera clear depth layers, and stands out in the feed.

Prepend this to every scene prompt (visual language only: the scene itself comes from the script):

```
Noir graphic-novel painting: bold confident black ink brushwork over painted greyscale tones, cinematic
chiaroscuro lighting, limited palette of charcoal, bone white and one crimson red accent, rough dry-brush texture
and subtle screen-print grain, strong silhouettes and deep shadows, realistic proportions and expressive faces,
widescreen film-still composition, no text, no letters. Scene:
```

Collage accent (hook scenes, chapter openers, thumbnails; at most 1 in 5 scenes), added after the prefix:

```
Behind the main subject a few torn-paper collage fragments and flat crimson-red paper blocks are layered into the
background (never covering faces, at most two red shapes), film grain and fine halftone texture.
```

Rules
- One focal subject per scene and one red object that matters to the sentence (a flag, a jeep, a cap). Red is
  the story's pointer, not decoration.
- Full collage (the reference poster look: many torn photo fragments, extra faces and hands) only for the
  thumbnail and the first hook frame. In story scenes it invents people that are not in the story and is hard to
  read in 10 s.
- Keep the scene composition simple, with a clear foreground, middle and background, so depth.sh separates them.
- Vertical shorts: same prefix, `1088x1920`, subject in the middle third (the top and bottom carry captions).
- Tested on episode 3 scenes 1, 12 and 34 (`output/style-lab/compare.jpg`): old ink, full collage, noir
  painting. The noir painting won; the collage accent mix still needs its 3-scene test.
