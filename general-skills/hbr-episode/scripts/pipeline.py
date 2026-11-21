"""Episode video engine (run from the episode folder). Scenes -> 2.5D parallax shots -> HyperFrames render.

  python3 pipeline.py align    <voice.mp3>   # whisper word timings -> scene + sentence times
  python3 pipeline.py plan                   # shots (one camera move each) per scene
  python3 pipeline.py render  [first last]   # HyperFrames render per scene (resumable)
  python3 pipeline.py assemble <voice.mp3>   # concat + voice + SRT

Inputs: scenes.json (Saudi text + image prompts), plates/NN/{plate.jpg,depth.png}.
"""
import difflib, json, math, os, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path.cwd()                                    # the episode folder
SKILL = Path(__file__).resolve().parents[1]
SK = SKILL.parent / "parallax" / "scripts"
FPS = 25
W, H = (int(v) for v in os.environ.get("SIZE", "1920x1080").split("x"))   # 1080x1920 for native vertical
STEPS = int(os.environ.get("STEPS", 24))
WORK = Path(os.environ.get("WORK", ROOT / "parallax"))
SCENES = json.load(open(ROOT / "scenes.json"))[:int(os.environ.get("LIMIT", 999))]


# ---------- text alignment ----------
def norm(w):
    w = re.sub(r"[ً-ْـ]", "", w)            # tashkeel + tatweel
    w = re.sub("[أإآ]", "ا", w).replace("ة", "ه").replace("ى", "ي")
    return re.sub(r"[^\w]", "", w)

def tokens(text):
    return [t for t in (norm(x) for x in text.split()) if t]

def align(voice):
    WORK.mkdir(exist_ok=True)
    tj = WORK / "transcript.json"
    if not tj.exists():
        wav = WORK / "voice16k.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", voice, "-ar", "16000", "-ac", "1", str(wav)], check=True)
        subprocess.run(["npx", "hyperframes", "transcribe", str(wav), "--engine", "whisper", "--model", "small",
                        "--language", "ar", "--timeout", "7200000", "-d", str(WORK)], check=True, cwd=WORK)
    words = json.load(open(tj))
    words = words if isinstance(words, list) else words["words"]
    hyp = [norm(w["text"]) for w in words]
    # reference tokens, tagged with (scene, sentence)
    ref, tag, sents = [], [], []
    for si, s in enumerate(SCENES):
        for sj, sent in enumerate(re.split(r"(?<=[.!؟?…:])\s+", s["ar"].strip())):
            sents.append((si, sj, sent))
            for t in tokens(sent):
                ref.append(t); tag.append(len(sents) - 1)
    m = {}
    for a, b, n in difflib.SequenceMatcher(None, ref, hyp, autojunk=False).get_matching_blocks():
        for k in range(n):
            m[a + k] = b + k
    # first/last matched hyp word per sentence
    span = {}
    for ri, hi in m.items():
        s = span.setdefault(tag[ri], [hi, hi]); s[0] = min(s[0], hi); s[1] = max(s[1], hi)
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", voice]))
    out = []
    for k, (si, sj, sent) in enumerate(sents):
        if k in span:
            out.append(dict(scene=si, text=sent, start=words[span[k][0]]["start"], end=words[span[k][1]]["end"]))
        else:
            out.append(dict(scene=si, text=sent, start=None, end=None))
    # fill unmatched sentences by interpolation
    for k, o in enumerate(out):
        if o["start"] is None:
            prev = next((out[j]["end"] for j in range(k - 1, -1, -1) if out[j]["end"] is not None), 0.0)
            nxt = next((out[j]["start"] for j in range(k + 1, len(out)) if out[j]["start"] is not None), total)
            o["start"], o["end"] = prev, nxt
    # scene cut = midpoint of the pause between scenes, in whole frames
    cuts = [0]
    for si in range(1, len(SCENES)):
        last_prev = max(o["end"] for o in out if o["scene"] == si - 1)
        first = min(o["start"] for o in out if o["scene"] == si)
        cuts.append(round((last_prev + first) / 2 * FPS))
    cuts.append(round(total * FPS))
    json.dump(dict(sentences=out, cuts=cuts, words=words, total=total), open(WORK / "align.json", "w"),
              ensure_ascii=False, indent=1)
    miss = len(sents) - len(span)
    print(f"aligned {len(span)}/{len(sents)} sentences ({miss} interpolated); total {total/60:.2f} min")


# ---------- shot planning ----------
def subject_centre(depth_png):
    from PIL import Image
    import numpy as np
    d = np.asarray(Image.open(depth_png).convert("L").resize((192, 108)), dtype=np.float32) / 255
    m = d >= np.quantile(d, 0.9)
    ys, xs = np.nonzero(m)
    return float(xs.mean() / 192), float(ys.mean() / 108)

def safe(c, z, s, f, pad=0.004):
    """Clamp a window centre so window + parallax offset stays inside the image."""
    lim = 0.5 - 0.5 / z - abs(s) * max(f, 1 - f) - pad
    return min(max(c, 0.5 - lim), 0.5 + lim)

MOVES = ["push-in", "pan-right", "reveal-zoom", "pan-left", "rise", "pull-out", "orbit-right", "descend", "orbit-left"]

def move_params(name, sub, k):
    sxv, syv = sub
    f = 0.5
    if name == "push-in":
        z, sx, sy, f = [1.12, 1.30], [-0.015, 0.015], [0, 0], 0.55
        cx, cy = [0.5, sxv], [0.5, syv]
    elif name == "pull-out":
        z, sx, sy, f = [1.30, 1.12], [0.015, -0.015], [0, 0], 0.55
        cx, cy = [sxv, 0.5], [syv, 0.5]
    elif name in ("pan-left", "pan-right"):
        z, sy, f = [1.22, 1.26], [0, 0], 0.45
        sx = [0.02, -0.02] if name == "pan-left" else [-0.02, 0.02]
        cx = [0.6, 0.4] if name == "pan-left" else [0.4, 0.6]
        cy = [syv * 0.3 + 0.35, syv * 0.3 + 0.35]
    elif name in ("rise", "descend"):
        z, sx, f = [1.24, 1.28], [0, 0], 0.5
        sy = [0.018, -0.018] if name == "rise" else [-0.018, 0.018]
        cy = [0.6, 0.4] if name == "rise" else [0.4, 0.6]
        cx = [sxv * 0.3 + 0.35] * 2
    elif name == "reveal-zoom":
        z, sx, sy, f = [1.12, 1.45], [-0.01, 0.01], [0.008, -0.006], 0.7
        cx, cy = [0.5, sxv], [0.5, syv]
    else:  # orbit
        z, sy, f = [1.18, 1.22], [0, 0], 0.6
        sx = [0.02, -0.02] if name == "orbit-left" else [-0.02, 0.02]
        cx, cy = [sxv * 0.4 + 0.3] * 2, [syv * 0.4 + 0.3] * 2
    sm = max(abs(v) for v in sx + sy)
    cx = [safe(c, zz, sm, f) for c, zz in zip(cx, z)]
    cy = [safe(c, zz, sm, f) for c, zz in zip(cy, z)]
    return dict(cx=[round(v, 4) for v in cx], cy=[round(v, 4) for v in cy], zoom=z, sx=sx, sy=sy, focus=f)

def plan():
    A = json.load(open(WORK / "align.json"))
    cuts, words = A["cuts"], A["words"]
    gaps = [((words[i]["end"] + words[i + 1]["start"]) / 2, words[i + 1]["start"] - words[i]["end"])
            for i in range(len(words) - 1)]
    shots, mv = [], 0
    for si in range(len(SCENES)):
        a, b = cuts[si], cuts[si + 1]
        sub = subject_centre(ROOT / "plates" / f"{si+1:02d}" / "depth.png")
        n = max(1, round((b - a) / FPS / 6.5))        # ~6.5 s per shot
        inner = []
        for j in range(1, n):
            tgt = (a + (b - a) * j / n) / FPS
            cand = [g for g in gaps if abs(g[0] - tgt) < 1.8 and a / FPS + 2 < g[0] < b / FPS - 2]
            t = max(cand, key=lambda g: g[1])[0] if cand else tgt
            inner.append(round(t * FPS))
        edges = [a] + sorted(set(inner)) + [b]
        for j in range(len(edges) - 1):
            name = MOVES[mv % len(MOVES)]; mv += 1
            shots.append(dict(scene=si + 1, id=f"s{si+1:02d}_{j+1}", f0=edges[j], f1=edges[j + 1],
                              preset=name, params=move_params(name, sub, mv)))
    json.dump(shots, open(WORK / "shots.json", "w"), indent=1)
    print(f"{len(shots)} shots, avg {sum(s['f1']-s['f0'] for s in shots)/len(shots)/FPS:.1f}s")


# ---------- render (one HyperFrames project per scene) ----------
INDEX = """<!doctype html>
<html lang="en" data-resolution="{res}"><head><meta charset="UTF-8" />
<meta name="viewport" content="width={w}, height={h}" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:{w}px;height:{h}px;overflow:hidden;background:#0d0f14}}
#root{{position:relative;width:100%;height:100%}}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{dur}" data-width="{w}" data-height="{h}">
{hosts}
</div>
<script>const tl = gsap.timeline({{ paused: true }}); window.__timelines["main"] = tl; tl.seek(0);</script>
</body></html>
"""

def render(first=1, last=None):
    last = last or len(SCENES)
    shots = json.load(open(WORK / "shots.json"))
    tmpl = SKILL / "assets" / "hf-template"
    for si in range(first, last + 1):
        out = WORK / "video" / f"{si:02d}.mp4"
        if out.exists():
            continue
        ss = [s for s in shots if s["scene"] == si]
        p = WORK / "proj" / f"{si:02d}"
        if p.exists(): shutil.rmtree(p)
        p.mkdir(parents=True)
        for f in ("hyperframes.json", "package.json", "meta.json"):
            if (tmpl / f).exists(): shutil.copy(tmpl / f, p / f)
        base = ss[0]["f0"]; hosts = []
        for s in ss:
            d = (s["f1"] - s["f0"]) / FPS
            (p / "assets" / "scenes" / s["id"]).mkdir(parents=True)
            for f in ("plate.jpg", "depth.png"):
                os.link(ROOT / "plates" / f"{si:02d}" / f, p / "assets" / "scenes" / s["id"] / f)
            r = subprocess.run(["python3", "-I", str(SK / "make_scene.py"), "--project", str(p), "--id", s["id"],
                                "--duration", f"{d:.2f}", "--size", f"{W}x{H}", "--preset", s["preset"],
                                "--mood", "none", "--params", json.dumps(s["params"])],
                               check=True, capture_output=True, text=True).stdout
            comp = p / "compositions" / f"{s['id']}.html"   # CPU-only render: halve the depth-march steps
            t = comp.read_text(); assert "i<48" in t and "/47.0" in t
            comp.write_text(t.replace("i<48", f"i<{STEPS}").replace("/47.0", f"/{STEPS - 1}.0"))
            host = r.split("host for index.html (set START):\n", 1)[1].strip()
            hosts.append(host.replace('data-start="START"', f'data-start="{(s["f0"]-base)/FPS:.2f}"'))
        dur = (ss[-1]["f1"] - base) / FPS
        (p / "index.html").write_text(INDEX.format(dur=f"{dur:.2f}", hosts="\n".join(hosts), w=W, h=H, res="landscape" if W > H else "portrait"))
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["npx", "hyperframes", "render", "--fps", str(FPS), "--quality", "delivery",
                        "-o", str(out.with_suffix(".tmp.mp4"))], check=True, cwd=p,
                       stdout=subprocess.DEVNULL, stderr=open(p / "render.log", "w"))
        # force exact frame count so 60 scenes never drift against the voice
        n = ss[-1]["f1"] - base
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out.with_suffix(".tmp.mp4")),
                        "-vf", f"tpad=stop_mode=clone:stop=50,trim=end_frame={n},setpts=PTS-STARTPTS",
                        "-r", str(FPS), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                        "-pix_fmt", "yuv420p", str(out)], check=True)
        out.with_suffix(".tmp.mp4").unlink()
        print(f"scene {si:02d} done ({n} frames)", flush=True)


# ---------- retime (fit already-rendered scenes to a new voice, no re-render) ----------
def retime(src="parallax"):
    """Stretch/squeeze each rendered scene from ROOT/<src>/video to the scene lengths in WORK/align.json."""
    from concurrent.futures import ThreadPoolExecutor
    cuts = json.load(open(WORK / "align.json"))["cuts"]
    (WORK / "video").mkdir(parents=True, exist_ok=True)
    def one(i):
        a, out = ROOT / src / "video" / f"{i:02d}.mp4", WORK / "video" / f"{i:02d}.mp4"
        n0 = int(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                          "stream=nb_frames", "-of", "csv=p=0", str(a)]).decode().strip().strip(","))
        n = cuts[i] - cuts[i - 1]
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(a), "-vf",
                        f"setpts=PTS*{n / n0:.6f},fps={FPS},tpad=stop_mode=clone:stop=50,trim=end_frame={n},setpts=PTS-STARTPTS",
                        "-r", str(FPS), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                        "-pix_fmt", "yuv420p", str(out)], check=True)
        return n / n0
    with ThreadPoolExecutor(2) as ex:
        r = list(ex.map(one, range(1, len(SCENES) + 1)))
    print(f"retimed {len(r)} scenes, speed factor min {min(r):.2f} max {max(r):.2f} mean {sum(r)/len(r):.2f}")


# ---------- assemble ----------
def s2t(x):
    ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def assemble(voice):
    A = json.load(open(WORK / "align.json"))
    lst = WORK / "video" / "list.txt"
    lst.write_text("".join(f"file '{i:02d}.mp4'\n" for i in range(1, len(SCENES) + 1)))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", voice,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", str(WORK.parent / f"{WORK.name}_25d.mp4")], check=True)
    srt = [f"{k}\n{s2t(o['start'])} --> {s2t(o['end'])}\n{o['text']}\n" for k, o in enumerate(A["sentences"], 1)]
    (WORK.parent / f"{WORK.name}_25d.srt").write_text("\n".join(srt))
    print(f"wrote {WORK.name}_25d.mp4 / .srt")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "align": align(sys.argv[2])
    elif cmd == "plan": plan()
    elif cmd == "render": render(*(int(x) for x in sys.argv[2:4]))
    elif cmd == "retime": retime(*sys.argv[2:3])
    elif cmd == "assemble": assemble(sys.argv[2])
