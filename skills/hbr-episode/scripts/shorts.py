"""Cut vertical shorts (1440x2560) from the episode body video.

  python3 shorts.py <work> <body_video> <out_dir> [shorts.json]     (run from the episode folder)

shorts.json: [{"first": 1, "last": 2, "title": "line 1|line 2", "end": "closing question"}]  (1-based scene numbers)
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
def chunks(sent, t0, t1):
    w = sent.split(); n = max(1, round(len(w) / 4)); k = -(-len(w) // n); out = []
    tot = sum(len(x) for x in w) or 1; pos = 0; t = t0
    for i in range(0, len(w), k):
        part = w[i:i + k]; d = (t1 - t0) * sum(len(x) for x in part) / tot
        out.append((' '.join(part), t, t + d)); t += d
    return out
for n, sh in enumerate(SHORTS, 1):
    s0, s1 = cuts[sh['first'] - 1], cuts[sh['last']] - 0.15; dur = s1 - s0
    L = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 0", "", "[V4+ Styles]",
         "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
         "Style: Title,Amiri,92,&H00FFFFFF,&H0,&H00000000,&H0,-1,0,0,0,100,100,0,0,1,6,0,8,60,60,150,1",
         "Style: Cap,Amiri,88,&H0000D7FF,&H0,&H00000000,&H0,-1,0,0,0,100,100,0,0,1,7,0,8,70,70,1390,1",
         "Style: Brand,Amiri,55,&H00FFFFFF,&H0,&H00000000,&H0,-1,0,0,0,100,100,0,0,1,4,0,2,60,60,120,1",
         "Style: End,Amiri,101,&H00FFFFFF,&H0,&H00000000,&H0,-1,0,0,0,100,100,0,0,1,7,0,5,60,60,0,1",
         "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    ev = lambda st, a_, b_, t: L.append(f"Dialogue: 0,{ts(a_)},{ts(b_)},{st},,0,0,0,,{t}")
    ev('Title', 0, dur, sh['title'].replace('|', r'\N'))
    ev('Brand', 0, dur, 'حبر وسالفة')
    for x in S:
        if sh['first'] - 1 <= x['scene'] <= sh['last'] - 1:
            for txt, t0, t1 in chunks(x['text'], x['start'] - s0, x['end'] - s0):
                if t1 > 0 and t0 < dur: ev('Cap', max(0, t0), min(dur, t1), txt)
    ev('End', dur, dur + END, sh.get('end', '') + r'\N{\c&H1E1EE6&}القصة كاملة في القناة\N{\c&H00D7FF&\fs70}حبر وسالفة')
    ass = f'{OUT}/short{n}.ass'; open(ass, 'w').write('\n'.join(L) + '\n')
    f = (f"[0:v]trim={s0:.3f}:{s1:.3f},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={END},split=2[a][b];"
         + ("[a]scale=1440:2560:flags=lanczos,unsharp=5:5:0.3:5:5:0[v0];[b]nullsink;" if VERT else
         "[a]scale=-2:2560,crop=1440:2560,boxblur=40:5,eq=brightness=-0.35[bg];"
         "[b]scale=-2:1334:flags=lanczos,crop=1440:1334,unsharp=5:5:0.4:5:5:0[fg];[bg][fg]overlay=0:493[v0];") +
         f"[v0]drawbox=enable='gte(t,{dur:.2f})':x=0:y=0:w=iw:h=ih:color=black@0.78:t=fill,ass={ass}:fontsdir={FONTS}:shaping=complex,format=yuv420p[v];"
         f"[0:a]atrim={s0:.3f}:{s1:.3f},asetpts=PTS-STARTPTS,afade=t=out:st={dur-0.4:.2f}:d=0.4,apad=pad_dur={END}[au]")
    out = f'{OUT}/short{n}.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', VID, '-filter_complex', f, '-map', '[v]', '-map', '[au]', '-r', '25',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-maxrate', '14M', '-bufsize', '28M', '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', out], check=True)
    print(out, round(dur + END, 1), 's')
