# Music

Library: `output/channel/music/library.json` (file, mood, use, best part, gain). Start every episode there.

## Planning sections
Split the story into 6–11 beats (hook, background, rise, crisis, comeback, climax, aftermath, ending). Give each a
mood from the library. In `episode.json`:
```json
{"file":"sky_master.wav","from":8,"to":12,"gain":0.58,"at":{"scene":9,"t":52}}
```
`at` lines up the track's best moment (second `t`) with a scene start or a spoken word. The section after the
intro sets `"transition": false` (the intro already separates them).

## New music
- Lyria 2 on fal: `python3 "$SK/scripts/music_gen.py" "<prompt>" <name>` (~30 s, good for stingers and loops).
- Longer, structured pieces: write a prompt for the owner to run in Google Flow Music; ask for WAV download;
  then `bash "$SK/scripts/master_music.sh" in out_master.wav` and add it to `library.json`.
- ElevenLabs Music when the subscription is sorted.
Prompt = genre + instruments + emotional arc + tempo + "instrumental, no vocals". Name a feel, not an artist.
