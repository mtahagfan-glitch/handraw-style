"""Cut vertical shorts (1440x2560) from the episode body video.

  python3 shorts.py <work> <body_video> <out_dir> [shorts.json]     (run from the episode folder)

shorts.json: [{"first": 1, "last": 2, "title": "line 1|line 2", "end": "closing question"}]  (1-based scene numbers)
  "end": null (or "loop": true) -> no end card: the last line runs straight back into the first (standalone
  «سالفة في دقيقة» shorts are written to loop; send viewers on with YouTube's "Related video" link instead).
Captions are big, 2-3 words at a time, the spoken word lit gold (word times from Whisper's real timings).
<body_video> is the video BEFORE the intro is inserted (its timing matches <work>/align.json).
A vertical body video (native 9:16 render) fills the frame; a landscape one sits in the middle over a blurred copy.
"""
import json, subprocess, sys, os
from pathlib import Path
W, VID, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
SHORTS = json.load(open(sys.argv[4] if len(sys.argv) > 4 else 'shorts.json'))
a = json.load(open(f'{W}/align.json')); cuts = [c / 25 for c in a['cuts']]; S = a['sentences']
FONTS = str(Path(__file__).resolve().parents[1] / 'assets' / 'fonts'); os.makedirs(OUT, exist_ok=True)   # Amiri = channel video font
END = 3.0
wh = subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height','-of','csv=p=0',VID]).decode().split(',')
VERT = int(wh[1]) > int(wh[0])
def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"
WW = a.get('words', [])
def words(sent, t0, t1):
    """per-word times inside a sentence from the REAL word timings (Whisper), mapped onto the script's spelling by
    character position, so pauses inside a sentence hold the caption instead of running ahead of the voice.
    Falls back to letter-count estimates when Whisper has no words there."""
    w = sent.split(); ww = [x for x in WW if t0 - 0.15 <= x['start'] < t1 + 0.05]
    if not ww:
        tot = sum(len(x) + 2 for x in w) or 1; out = []; t = t0
        for x in w:
            d = (t1 - t0) * (len(x) + 2) / tot; out.append((x, t, t + d)); t += d
        return out
    if len(ww) == len(w):                                     # same word count: take Whisper's times one to one
        return [(x, ww[i]['start'], ww[i + 1]['start'] if i + 1 < len(w) else ww[i]['end']) for i, x in enumerate(w)]
    L = sum(len(x['text']) for x in ww) or 1; pos = 0; seg = []
    for x in ww: seg.append((pos / L, (pos + len(x['text'])) / L, x['start'], x['end'])); pos += len(x['text'])
    def at(f):
        for c0, c1, s_, e_ in seg:
            if f < c1 - 1e-9: return s_ + (e_ - s_) * max(0, f - c0) / max(1e-9, c1 - c0)
        return seg[-1][3]
    T = sum(len(x) for x in w) or 1; pos = 0; st = []
    for x in w: st.append(at(pos / T)); pos += len(x)
    starts = [x['start'] for x in ww]                        # snap to a real word onset when one is close
    st = [min(starts, key=lambda q: abs(q - t)) if min(abs(q - t) for q in starts) < 0.35 else t for t in st]
    st = [max(st[:i + 1]) for i in range(len(st))]           # keep them in order
    return [(x, st[i], st[i + 1] if i + 1 < len(w) else ww[-1]['end']) for i, x in enumerate(w)]
def karaoke(sent, t0, t1):
    """2-3 word groups; one event per word with that word in gold, the rest white"""
    ws = words(sent, t0, t1); ev_ = []; i = 0
    while i < len(ws):
        k = 3 if len(ws) - i not in (4,) else 2
        grp = ws[i:i + k]
        for j, (_, a_, b_) in enumerate(grp):
            txt = ' '.join((r'{\c&H0000D7FF&}' + g[0] + r'{\c&H00FFFFFF&}') if jj == j else g[0] for jj, g in enumerate(grp))
            ev_.append((txt, a_, b_))
        i += k
    return ev_
def chunks(sent, t0, t1):
    w = sent.split(); n = max(1, round(len(w) / 4)); k = -(-len(w) // n); out = []
    tot = sum(len(x) for x in w) or 1; pos = 0; t = t0
    for i in range(0, len(w), k):
        part = w[i:i + k]; d = (t1 - t0) * sum(len(x) for x in part) / tot
        out.append((' '.join(part), t, t + d)); t += d
    return out
for n, sh in enumerate(SHORTS, 1):
    s0, s1 = cuts[sh['first'] - 1], cuts[sh['last']] - 0.15; dur = s1 - s0
    LOOP = sh.get('loop') or sh.get('end', '') is None; E = 0.0 if LOOP else END
    # Encoding -1 below = auto RTL base direction: without it libass orders colour-tagged Arabic words left-to-right
    L = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 0", "", "[V4+ Styles]",
         "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
         "Style: Title,Amiri,270,&H00FFFFFF,&H0,&H00000000,&H0,-1,0,0,0,100,100,0,0,1,6,0,8,60,60,150,-1",
         "Style: Cap,Amiri,330,&H00FFFFFF,&H0,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,8,3,8,40,40,1330,-1",
         "Style: Brand,Amiri,120,&H00FFFFFF,&H0,&H00000000,&H0,-1,0,0,0,100,100,0,0,1,4,0,2,60,60,120,-1",
         "Style: End,Amiri,220,&H00FFFFFF,&H0,&H00000000,&H0,-1,0,0,0,100,100,0,0,1,7,0,5,60,60,0,-1",
         "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    ev = lambda st, a_, b_, t: L.append(f"Dialogue: 0,{ts(a_)},{ts(b_)},{st},,0,0,0,,{t}")
    # libass fits ascent+descent into Fontsize and Amiri's are tall, so its glyphs come out ~57% of a normal font: sizes are big on purpose: place the two title lines by hand
    for j, line in enumerate(sh['title'].split('|')[:2]):
        ev('Title', 0, dur, (r'{\an8\pos(540,-20)\c&H00D7FF&}' if j == 0 else r'{\an8\pos(540,165)\fs200}') + line)
    ev('Brand', 0, dur, 'حبر وسالفة')
    for x in S:
        if sh['first'] - 1 <= x['scene'] <= sh['last'] - 1:
            for txt, t0, t1 in karaoke(x['text'], x['start'] - s0, x['end'] - s0):
                if t1 > 0 and t0 < dur: ev('Cap', max(0, t0), min(dur, t1), txt)
    if not LOOP: ev('End', dur, dur + END, sh.get('end', '') + r'\N{\c&H1E1EE6&}القصة كاملة في القناة\N{\c&H00D7FF&\fs150}حبر وسالفة')
    ass = f'{OUT}/short{n}.ass'; open(ass, 'w').write('\n'.join(L) + '\n')
    f = (f"[0:v]trim={s0:.3f}:{s1:.3f},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={E},split=2[a][b];"
         + ("[a]scale=1440:2560:flags=lanczos,unsharp=5:5:0.3:5:5:0[v0];[b]nullsink;" if VERT else
         "[a]scale=-2:2560,crop=1440:2560,boxblur=40:5,eq=brightness=-0.35[bg];"
         "[b]scale=-2:1334:flags=lanczos,crop=1440:1334,unsharp=5:5:0.4:5:5:0[fg];[bg][fg]overlay=0:493[v0];") +
         f"[v0]drawbox=enable='gte(t,{dur:.2f})':x=0:y=0:w=iw:h=ih:color=black@0.78:t=fill,ass={ass}:fontsdir={FONTS}:shaping=complex,format=yuv420p[v];"
         f"[0:a]atrim={s0:.3f}:{s1:.3f},asetpts=PTS-STARTPTS,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,afade=t=out:st={dur-(0.15 if LOOP else 0.4):.2f}:d={0.15 if LOOP else 0.4},apad=pad_dur={E}[au]")
    out = f'{OUT}/short{n}.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', VID, '-filter_complex', f, '-map', '[v]', '-map', '[au]', '-r', '25',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-maxrate', '14M', '-bufsize', '28M', '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', out], check=True)
    print(out, round(dur + E, 1), 's')
