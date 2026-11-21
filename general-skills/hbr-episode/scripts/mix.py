"""Final soundtrack for an episode: voice + scene-cut SFX + music sections with transitions + ducking.

  W=parallax_real python3 mix.py          (run from the episode folder)

Reads  : <W>/align.json, <W>/voice.wav, scenes.json, episode.json
Writes : <W>/sfx.wav, <W>/final_audio.wav

episode.json
{
  "music": [                                   # one entry per section, in order; "from"/"to" are scene indices
    {"file": "tense.mp3", "from": 0, "to": 2, "gain": 1.25},          #   (0-based: the cut where that scene starts)
    {"file": "sky_master.wav", "from": 8, "to": 12, "gain": 0.58,
     "at": {"scene": 9, "t": 52}},             # track second 52 lands on the start of scene index 9
    {"file": "legend_master.wav", "from": 60, "to": "end", "gain": 0.68,
     "at": {"word": "ولحكا", "t": 120}}        # ... or on a spoken word
  ],
  "sfx": {"rules": [["red card|penalty", "whistle"], ["celebrat|erupting", "net"]]},
  "inserts": [{"file": "farewell/commentary.wav", "after_scene": 65}]   # real audio laid after a scene's last sentence
}
Music files are looked up in the episode folder first, then in output/channel/music (the channel library).
Every music boundary (except the first) gets a transition: riser into the cut, soft boom on it, 0.45 s of air,
then the new track fades in. Old cue levels: ElevenLabs beds ~1.0-1.25, Lyria masters (-14 LUFS) ~0.58-0.7.
"""
import json, os, re, subprocess, wave
from pathlib import Path
import numpy as np

W = os.environ.get('W', 'parallax_real'); SR = 48000; FPS = 25
CH = Path(__file__).resolve().parents[3] / 'output' / 'channel'
a = json.load(open(f'{W}/align.json')); cuts = [c / FPS for c in a['cuts']]; total = a['total']
sc = json.load(open('scenes.json')); EP = json.load(open('episode.json'))
n = int(total * SR) + SR; buf = np.zeros(n, np.float32)

def sfx_file(k):
    for p in (Path('sfx') / f'el_{k}.wav', CH / 'sfx' / f'el_{k}.wav', CH / 'sfx' / f'{k}.wav'):
        if p.exists(): return p
    raise FileNotFoundError(k)

def load(k, db):
    w = wave.open(str(sfx_file(k))); x = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float32) / 32768
    if w.getnchannels() == 2: x = x[::2]
    nz = np.nonzero(np.abs(x) > 0.01 * np.abs(x).max())[0]; x = x[nz[0]:nz[-1] + 1].copy()
    f = min(int(0.15 * SR), len(x) // 2); x[-f:] *= np.linspace(1, 0, f); g = min(480, len(x) // 4); x[:g] *= np.linspace(0, 1, g)
    return x / np.abs(x).max() * 10 ** (db / 20)

LEVEL = dict(swish=-18, drum=-17, boom=-10, page=-19, crowd=-22, riser=-17, whistle=-22, kick=-18, net=-20, heart=-16, chant=-23)
L = {}
for k, d in LEVEL.items():
    try: L[k] = load(k, d)
    except FileNotFoundError: pass

def put(x, t):
    i = max(0, int(t * SR)); j = min(n, i + len(x)); buf[i:j] += x[:j - i]

def cut_at(k): return total if k == 'end' else cuts[k]

MUS = EP['music']
TR = {m['from'] for m in MUS[1:] if m.get('transition', True)}
rules = [(re.compile(r, re.I), s) for r, s in EP.get('sfx', {}).get('rules', [])]
rot = ['swish', 'drum', 'page', 'swish']; last = None; r = 0; used = {}
for k in range(1, len(sc)):
    p = sc[k].get('img', ''); t = cuts[k]
    if k in TR and 'riser' in L:
        put(L['riser'], t - len(L['riser']) / SR + 0.05); put(L['boom'] * 0.6, t + 0.02); last = 'boom'; continue
    c = next((s for rx, s in rules if rx.search(p) and s in L), None)
    if c is None or c == last:
        for _ in range(4):
            c = rot[r % 4]; r += 1
            if c != last: break
    put(L[c], t + 0.02 if c in ('boom', 'kick', 'net') else t - {'crowd': 0.5, 'chant': 0.5, 'swish': 0.35}.get(c, 0.1))
    last = c; used[c] = used.get(c, 0) + 1
print('sfx', used)
x = (np.clip(buf, -1, 1) * 32767).astype('<i2')
w = wave.open(f'{W}/sfx.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(np.repeat(x, 2).tobytes()); w.close()

def track(f):
    for p in (Path(f), CH / 'music' / f):
        if p.exists(): return str(p)
    raise FileNotFoundError(f)

inp = ['-i', f'{W}/voice.wav', '-i', f'{W}/sfx.wav']; f = ''; labs = []; vox = ['[0:a]']
for j, ins in enumerate(EP.get('inserts', [])):
    s = max(x['end'] for x in a['sentences'] if x['scene'] == ins['after_scene'] - 1) + 0.25
    inp += ['-i', ins['file']]; ms = int(s * 1000)
    f += f"[{len(inp)//2 - 1}:a]aresample={SR},aformat=channel_layouts=stereo,adelay={ms}|{ms},apad[ins{j}];"; vox.append(f'[ins{j}]')
for i, m in enumerate(MUS):
    s, e = cut_at(m['from']), cut_at(m['to'])
    at = m.get('at'); off = m.get('offset', 0)
    if at and 'scene' in at: off = at['t'] - (cuts[at['scene']] - s)
    if at and 'word' in at: off = at['t'] - (next(w['start'] for w in a['words'] if w['text'] == at['word']) - s)
    tin = m['from'] in TR; tout = m['to'] in TR
    s0 = s + 0.45 if tin else max(0, s - 1.5); off0 = max(0, off - (s - s0))
    end = e + 0.25 if tout else (e + 1.5 if e < total else e); d = end - s0
    fi = 2.0 if tin else 3; fo = 2.2 if tout else 3
    inp += ['-stream_loop', '8', '-i', track(m['file'])]
    idx = sum(1 for z in inp if z == '-i') - 1
    f += (f"[{idx}:a]aresample={SR},aformat=channel_layouts=stereo,atrim={off0:.2f}:{off0+d:.2f},asetpts=PTS-STARTPTS,"
          f"afade=t=in:d={fi},afade=t=out:st={d-fo:.2f}:d={fo},volume={m.get('gain',1.0)},adelay={int(s0*1000)}|{int(s0*1000)}[m{i}];")
    labs.append(f'[m{i}]')
f += (f"{''.join(vox)}amix=inputs={len(vox)}:normalize=0[vc];{''.join(labs)}amix=inputs={len(labs)}:normalize=0,volume=0.6[m];"
      f"[vc]asplit=2[v1][v2];[m][v1]sidechaincompress=threshold=0.03:ratio=2:attack=30:release=600[duck];"
      f"[v2][duck][1:a]amix=inputs=3:normalize=0,volume=0.5dB,atrim=0:{total:.2f},alimiter=limit=0.84:level=false[out]")
subprocess.run(['ffmpeg', '-v', 'error', '-y', *inp, '-filter_complex', f, '-map', '[out]', '-ar', str(SR), '-c:a', 'pcm_s16le',
                f'{W}/final_audio.wav'], check=True)
print('wrote', f'{W}/final_audio.wav')
