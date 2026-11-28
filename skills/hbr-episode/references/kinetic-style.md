# Kinetic explainer style (motion graphics)

Taken from a fast Arabic explainer short the owner liked (Nov 2026). Visual language only, so it works for any story.

What makes it work
- **One idea per beat, 1.5-3 s each.** 2-4 words per line, at most two lines; the picture changes as often as the
  sentence does. Nothing stays on screen after the voice has moved on.
- **Words pop in one by one** (scale down from 160%, blur to sharp, slight overshoot), timed to the voice.
- **One or two keywords in colour** (channel red `#e0312a`; teal or green only for a contrasting idea). The rest
  is black on light paper or bone white on dark.
- **Two stages that alternate:** a light paper stage with a soft spotlight and a heavy dark vignette, and a dark
  stage. Switching stage is the beat change; a faint grid on the light stage gives the "desk" feel.
- **RGB-split fringe** (red/cyan offset) on new elements that settles in a fraction of a second, plus a 0.2 s hit
  shake when a line lands and a slow push-in over the whole beat.
- **Cut-out objects**, black-and-white with a soft drop shadow, sitting under the words (a vial, a passport, a
  brain, a folder): the noun of the sentence made physical. Hand-drawn arrows draw themselves toward them.
- **Investigation board** for plots and steps: paper notes with tape pop in one by one, a red string joins them.
- **Glowing line chart** that draws itself for growth or decline.

Templates (`scripts/mg.py`): `kinetic`, `board`, `chart` (mp4 cards; `compose.py` treats them as full cards).

Where to use it
- **Shorts and «سالفة في دقيقة»:** this is their main graphic language. Alternate drawn scenes with kinetic beats:
  hook line as a kinetic beat in the first second, then drawing, beat, drawing.
- **Long episodes:** sparingly, for the key sentence of a part ("ما في مكان.. بعيد كفاية"), the plan of a plot
  (board) and numbers that change (chart). Never two in a row, never over a Flow/Veo shot.
- Cut-out objects: draw them with gpt-image-2 on a plain white background ("isolated object, studio cut-out,
  black-and-white ink, soft shadow") or crop one from a scene; keep them black-and-white so the red stays the accent.
