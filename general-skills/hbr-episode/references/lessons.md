# Lessons from the first episodes (Milan ultras, Messi 2026)

Read before starting an episode; add to it after each one.

## Voice and timing
- The owner's real voice beat the cloned voice. Keep real recordings; the clone is only for fixes.
- Pause trimming must check the audio, not only word timings: Whisper mistimes words, and a "gap" can hold
  speech (it cut «تسعطعش» from «عمره تسعطعش اسمه كيليان مبابي»). `align_real.py` checks the energy.
- Scene cuts land 0.2 s after a sentence ends; a shot split mid-sentence feels like a jump — merge it.

## Music
- One mood for 18 minutes is flat. Split the score into sections that follow the story beats (6–11 per episode).
- Abrupt music changes confused the viewer: every section change now gets riser → soft boom → 0.45 s → fade-in.
- Line up the best part of a track (its lift, its hit) with the exact sentence it belongs to (`at` in episode.json).
- Generated tracks mastered to -14 LUFS sit ~2 dB too loud next to the old beds: gain 0.58–0.68.
- Prompts that say "calm enough to sit under a voice" make bland music. Ask for emotion and arc; ducking handles the voice.
- The owner liked the older ElevenLabs tension/bed cues — reuse what works, whatever the source.
- Never use copyrighted references (Einaudi, Brand X…) directly; describe their feel instead.

## Picture
- gpt-image-2 drawings are 1088×608: upscale before rendering or the 1440p export looks soft.
  SeedVR keeps the ink and paper; ESRGAN anime models turn it into cartoon.
- One real moving shot at the climax (the sprint) was the most-remembered moment. Use 2–3 per episode.
- Keep faces consistent with a character sheet; without it the same person changes between scenes.

## Delivery
- Files sent to the owner must be under the upload limit (now 400 MB): HEVC copy at ~2.7 Mbps 1440p.
- The container disk is small (a few GB): delete superseded renders and parts as you go.
- The background-task limit is 2 hours: long renders must be resumable and restarted.

## Hook and persuasion (marketing ideas that transfer to storytelling)
- **Visual hook**: start inside the action (the stadium, the crime scene), not with context. The first frame moves.
- **Answer the doubt early**: if the story sounds unbelievable, show the proof (date, source, number) in the first
  minute, before the viewer starts doubting.
- **Anchor with contrast**: give the reference number first, then the surprising one (the record he broke, the
  normal age vs his age). A stat card makes the contrast stick.
- **Shorts are the free sample**: a short gives the best 45 s and ends on the open question; the long video is the
  full answer. Each short points to the long video.
