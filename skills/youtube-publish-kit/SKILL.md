---
name: youtube-publish-kit
description: Prepares everything a finished video needs to go on YouTube, in Saudi-dialect Arabic: a thumbnail with a short Arabic headline, three title options with a hook, a description, chapters and tags. Run it after every video made in this repo without being asked, and for "ثمبنيل", "عنوان للفيديو", "وصف الفيديو", "جهّز الفيديو للنشر", "thumbnail", "title and description".
---

# YouTube publish kit

The owner asked for this after every video: do not wait to be asked. Deliver it with the final video, in `output/<project>/publish/`.

## What to deliver

1. **Thumbnail** `thumbnail.jpg`, 1280x720.
2. **Titles** three options, the recommended one first.
3. **Description** ready to paste.
4. **Chapters** from the final voice timing (only once the voice is final).
5. **Tags** 10 to 15, Arabic and English names.

Put 2 to 5 in one `publish.md`.

## Thumbnail

- Generate the picture with the `gpt-image-2` skill at `landscape_16_9`, quality `high`, in the video's own illustration style, with **no text in the image** and one third left dark and empty for the headline.
- One subject, one idea, readable at phone size. People are stylized, never a real person's likeness.
- Add the headline yourself with Skia's paragraph shaper (the same method as `skills/cinematic-film/scripts/engine.py`), so Arabic letters join. Font: Lalezar. White for the first line, red for the punch word, yellow for a small third line, each with a thick black outline.
- At most five words in total, and they must not repeat the title: the thumbnail says what the title leaves out.
- Look at the result before sending it.

## Title

- Saudi dialect, under 60 characters, the hook in the first five words.
- A real fact from the video, never something the video does not deliver.
- Shapes that fit this channel: a contradiction ("زعيم الألتراس اللي قتل أعز أصحابه"), a question the video answers, or a number with a consequence.

## Description

- First two lines are the hook: they show before "عرض المزيد" and in search.
- Then three to five bullet points of what the viewer will learn, the chapters, a line asking for a subscribe, and the sources.
- Say that the illustrations are drawn for the video and that the story follows published reporting.

## Shorts (after every long video)

Cut 3 to 5 vertical shorts from each finished long video, for TikTok and YouTube Shorts, without being asked.

- Pick stretches of 45 to 80 seconds that start on a hook and **end on an open question or a cliffhanger**, cut on scene boundaries so no sentence is clipped.
- `output/milan-ultras/shorts.py <work> <video> <out_dir>` builds them from `shorts.json` (first scene, last scene, a two-line title, a closing question): 1080x1920, the picture in the middle over a blurred copy, a title on top, burned captions from the voice timing, the channel name, and a 3 second end card that says "القصة كاملة في القناة".
- Arabic text is burned with ffmpeg's `ass` filter and `shaping=complex`. The `subtitles` filter has no shaping option and leaves boxes for some letters.
- Write `captions.md` with one caption per short: a hook line, "القصة كاملة في القناة", the full video's link (ask the owner for it once the video is published), and five hashtags.
- Look at one frame of each short and of the end card before sending.

## Research (optional)

`skills/youtube-research/` holds TubeLab's title, thumbnail, ideation and script-breakdown skills. They need the TubeLab connector and a TubeLab account; without it, use the rules above.

## Channel

Name, avatar and bio live in `output/channel/`. Keep the thumbnail style and headline font the same across videos so the channel is recognisable.
