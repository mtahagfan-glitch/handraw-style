# Consistent characters

1. For each person who appears in 3+ scenes, make a reference sheet once, in the channel style:
   `python3 <gpt-image-2 skill>/scripts/generate.py "character reference sheet of <who: age, build, hair, beard,
   kit/clothes, number>, front view, three-quarter view, profile, full body, ink line art on aged paper, muted
   colour accents, plain background, no text" --size landscape_16_9 --quality high -o chars/<name>`
   Stylised, never a photo likeness of a real person.
2. Generate every scene with that person by passing the sheet: `--image chars/<name>.png` and say in the prompt
   "same character as the reference sheet". Two characters → two `--image`.
3. Keep `chars/` in the episode folder and reuse the sheets in later episodes (same player, same look).
4. Contact-sheet check: faces, kit numbers and colours match across scenes; redo the odd ones.
