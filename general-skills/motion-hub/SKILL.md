---
name: motion-hub
description: Router for the nashatak-jahez TikTok motion-graphics work. Use when asked to make, plan, script, voice, or analyze a short motion-graphics video. Picks the right tool/skill from skills-hub/registry.json.
---
# Motion hub
Project: Arabic (RTL) TikTok motion graphics for kindergarten-teacher activities. Brand: `nashatak-jahez-identity/` (tokens.css, logo/, IBM Plex Sans Arabic, ONE amber accent per frame).

1. Read `skills-hub/registry.json`, pick by task, read only that repo's own SKILL.md/README, not all of them.
2. Routing (herk-edit-kit skills are installed in .claude/skills and load on their own):
   - Brand reel / teaser in the CLAUDE MOTION REEL style: motion-showreel.
   - Arabic editorial recap / portfolio / project reel "بأسلوب بسام" (question hook, year-rule frame, beat cuts, +أكثر ending): bassam-reel.
   - Cinematic brand manifesto / mysterious trailer-like edit "زي إعلان Anthropic" (one word per shot, film look, \ slug \ montage, swap sentence, decoding wordmark): manifesto-film.
   - TikTok/Reels from footage: short-form-edit; from scratch: make-a-video; long talking-head: edit-video, video-storytelling.
   - Transitions, palettes, GSAP timing: hyperframes, gsap, style-library.
   - Build/render the video: remotion (default) or hyperframes/openfilm if a lighter HTML flow is wanted.
   - Motion craft, timing, kinetic type, TikTok safe areas: motion-skills, motion-director.
   - Script + hook: youtube-agent-skill hook formulas.
   - Voiceover: omnivoice (test Arabic first), else ElevenLabs MCP.
   - Study a reference video: claude-video, then rea-video/reelmimic if style transfer is wanted.
   - Trend research: social-research (needs API key; ask first).
3. Format defaults: 1080x1920, 30fps, 15-30s, hook in first 2s, captions in safe area, Arabic RTL, brand tokens only.
4. Install only what the task needs (`skills-hub/install.sh <id>`), and tell the user what was installed.
