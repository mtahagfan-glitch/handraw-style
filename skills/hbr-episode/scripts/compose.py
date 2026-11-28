"""Put the moving shots and the motion graphics into the rendered parallax scenes.

  WORK=$PWD/parallax_real python3 compose.py [first last]       (run from the episode folder)

Reads  : <WORK>/video/NN.mp4 (parallax renders, exact frame counts), episode.json
         "motion":   [{"scene": 2, "file": "flow/02.mp4", "at": 0, "len": 4.0}]           seconds inside the scene
         "graphics": [{"scene": 18, "at": 1.5, "tpl": "dots", "dur": 4.5, ...}]          files in mg/ (from mg.py),
                     named mg/<NN>_<tpl>_<index in the list>.(mp4|webm)
Writes : <WORK>/video_comp/NN.mp4, same frame count as the parallax scene, then assemble with
         VDIR=video_comp python3 pipeline.py assemble <audio>
Moving shots and full-card graphics dissolve in and out (0.3 s); transparent overlays sit on top;
scenes with a cctv overlay are also graded (desaturated, grain) so they read as surveillance footage.
"""
import json, os, subprocess, sys
from pathlib import Path

FPS = 25; WORK = Path(os.environ.get('WORK', 'parallax_real')); OUT = WORK / 'video_comp'; OUT.mkdir(exist_ok=True)
ep = json.load(open('episode.json')); G = ep.get('graphics', []); M = ep.get('motion', [])
FULL = {'stat', 'dots', 'timeline', 'quote', 'kinetic', 'board', 'chart'}
n_sc = len(json.load(open('scenes.json')))
first, last = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (1, n_sc)

def frames(p):
    return int(subprocess.check_output(['ffprobe', '-v', 'error', '-count_packets', '-select_streams', 'v:0', '-show_entries',
                                        'stream=nb_read_packets', '-of', 'csv=p=0', str(p)]).decode().strip().strip(','))
for s in range(first, last + 1):
    base = WORK / 'video' / f'{s:02d}.mp4'; out = OUT / f'{s:02d}.mp4'
    n = frames(base); dur = n / FPS
    mot = [m for m in M if m['scene'] == s and Path(m['file']).exists()]
    gr = [(k, g) for k, g in enumerate(G) if g['scene'] == s]
    if not mot and not gr:
        os.link(base, out) if not out.exists() else None; continue
    inp = ['-i', str(base)]; f = '[0:v]setpts=PTS-STARTPTS,format=yuv420p'
    if any(g['tpl'] == 'cctv' for _, g in gr): f += ',hue=s=0.35,noise=alls=10:allf=t'
    f += '[v0];'; cur = 'v0'; i = 1
    for m in mot:
        at, ln = float(m['at']), min(float(m['len']), dur - float(m['at']))
        fo = f",fade=t=out:st={ln-0.3:.2f}:d=0.3:alpha=1" if at + ln < dur - 0.05 else ''
        fi = ",fade=t=in:st=0:d=0.3:alpha=1" if at > 0.05 else ''
        inp += ['-i', m['file']]
        f += (f"[{i}:v]scale=1920:1080:flags=lanczos,fps={FPS},trim=0:{ln:.2f},setpts=PTS-STARTPTS,format=yuva420p{fi}{fo},"
              f"setpts=PTS+{at:.2f}/TB[m{i}];[{cur}][m{i}]overlay=eof_action=pass:format=auto[c{i}];"); cur = f'c{i}'; i += 1
    for k, g in gr:
        ext = 'mp4' if g['tpl'] in FULL else 'webm'; p = Path(f"mg/{s:02d}_{g['tpl']}_{k}.{ext}")
        if not p.exists(): print('missing', p); continue
        at = float(g.get('at', 0)); d = float(g['dur']) if g['dur'] != 'scene' else dur
        if ext == 'webm':
            inp += ['-c:v', 'libvpx-vp9', '-i', str(p)]; pre = f"[{i}:v]format=yuva420p,"
        else:
            inp += ['-i', str(p)]; pre = f"[{i}:v]format=yuva420p,fade=t=in:st=0:d=0.25:alpha=1,fade=t=out:st={d-0.3:.2f}:d=0.3:alpha=1,"
        f += f"{pre}setpts=PTS-STARTPTS+{at:.2f}/TB[g{i}];[{cur}][g{i}]overlay=eof_action=pass:format=auto[c{i}];"; cur = f'c{i}'; i += 1
    f += f"[{cur}]tpad=stop_mode=clone:stop=-1,trim=end_frame={n},setpts=PTS-STARTPTS,format=yuv420p[v]"
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *inp, '-filter_complex', f, '-map', '[v]', '-r', str(FPS), '-an',
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', '-pix_fmt', 'yuv420p', str(out)], check=True)
    assert frames(out) == n, (s, frames(out), n)
    print(f'scene {s:02d}: {len(mot)} moving, {len(gr)} graphics', flush=True)
