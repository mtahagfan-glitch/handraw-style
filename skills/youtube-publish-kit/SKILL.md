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

## Research (optional)

`skills/youtube-research/` holds TubeLab's title, thumbnail, ideation and script-breakdown skills. They need the TubeLab connector and a TubeLab account; without it, use the rules above.

## Channel

Name, avatar and bio live in `output/channel/`. Keep the thumbnail style and headline font the same across videos so the channel is recognisable.
