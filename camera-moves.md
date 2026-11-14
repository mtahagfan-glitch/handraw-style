# Camera moves

Every value is `[start, end]` over the shot, except `focus` and `ease`. Image uv: 0,0 = top-left.

| Preset | Feel | Use for |
|---|---|---|
| `push-in` | slow dolly toward the subject | establishing, tension building |
| `pull-out` | reveal of the surroundings | endings, "and then…" |
| `pan-left` / `pan-right` | camera slides past objects, strongest parallax | wide images, rooms, shelves, landscapes |
| `rise` / `descend` | crane up / down | tall subjects, stairs, buildings |
| `reveal-zoom` | slow push onto one detail | the reveal: a name, a face, a document |
| `orbit-left` / `orbit-right` | the scene turns slightly around the focus | portraits, objects on a desk |

## Tuning

- **Where the shot lands:** set `cx`/`cy` end values on the subject. A window at `zoom` 1
  covers the frame; e.g. a 16:9 image in a 9:16 frame shows a slice 31% wide, so keep `cx`
  between 0.16 and 0.84.
- **Stronger depth:** raise swing a little (0.03 → 0.04) and add zoom; lower `focus` toward the
  background to make the foreground sweep more.
- **Tearing / smeared edges** around a near object: reduce swing, or move `focus` closer to that
  object's depth.
- **Soft image:** the slice is being upscaled. Generate at the output aspect and 2K, or reduce zoom.

## Example (ep01 of The Last Storyteller, 9:16, 16:9 sources)

```text
A new book on the shelf   pan-right   {"cx":[0.40,0.52],"cy":[0.46,0.42],"zoom":[1.0,1.15],"sx":[-0.03,0.03],"focus":0.6}
Empty library at dawn     pan-left    {"cx":[0.56,0.30],"zoom":[1.05,1.15],"sx":[0.03,-0.03],"focus":0.4}   --mood cold
Hand opens the book       push-in     {"cx":[0.42,0.47],"cy":[0.60,0.64],"zoom":[1.15,1.35],"sx":[-0.025,0.025],"sy":[0.01,-0.01],"focus":0.55}
The first page            reveal-zoom {"cx":[0.50,0.54],"cy":[0.50,0.46],"zoom":[1.0,1.45],"focus":0.7}
```
