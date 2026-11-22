# «سالفة في دقيقة» — standalone daily shorts

Weekly plan (owner's choice): 1 long episode + 7 shorts cut from it + 3–4 standalone «سالفة في دقيقة» = 10–11 shorts.

## Pick the story
- One person, one impossible-but-true moment, a turn at the end. Verifiable (two sources); put links in `meta.json`.
- Not tied to the current episode, but the same worlds: crime, mystery, war, survival, secrets.

## Write (110–140 words, 45–60 s)
- Line 1 is the whole hook in one sentence, said in the first 2 seconds, no intro, no channel name.
- 8 scenes, one per sentence group. Every scene adds a new fact; no setup lines.
- The last line runs back into the first (loop): e.g. it ends on the hook phrase, or with a half sentence that the
  opening line completes. Viewers who loop raise the replay rate, the strongest Shorts signal.
- Facts the owner must not get wrong (numbers, dates) are written as words, as they will read them.

## Make
1. `output/shorts-daily/<nn-slug>/`: `scenes.json`, `prompts.txt` (vertical 9:16 prompt + channel style), `meta.json`.
2. Drawings at `portrait_16_9`, upscale to 1440×2560 (`upscale.py`), depth maps.
3. Optional: 1 Flow/Veo moving shot for line 1 (the first second must move).
4. Owner records all scripts of the week in one take session; split per short on the long pauses; `align_real.py`.
5. `SIZE=1080x1920` pipeline `plan` + `render`, `mix.py` with one music section (no transitions), `assemble`.
6. `shorts.py <work> <body> <out> shorts.json` with `{"first":1,"last":8,"title":"..","end":null}`: full-frame,
   big karaoke captions, no end card (loop).
7. `check_upload.py <short> --shorts`.

## Post
- YouTube: set "Related video" to the latest long episode; pinned comment with the episode title.
- TikTok: same file; caption = hook question + 3–5 hashtags incl. #حبر_وسالفة.
- One every day or every other day, at the same hour.
