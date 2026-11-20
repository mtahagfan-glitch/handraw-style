#!/usr/bin/env python3
"""Build a reel from reel.json.

  python3 build.py path/to/reel.json                 # full render -> <dir>/out/<name>.mp4
  python3 build.py path/to/reel.json --stills 1.2,6,14   # quick look at chosen seconds
  python3 build.py path/to/reel.json --sheet          # stills at every scene midpoint + contact sheet
  options: --workers 3  --crf 18  --no-audio  --keep-frames

Asset paths in reel.json are relative to reel.json. Any media value can be:
  "img.jpg"                          still image
  {"video":"clip.mp4","start":1.2,"speed":1.5}   video (frames are pre-extracted)
"""
import argparse, json, os, shutil, subprocess, sys, hashlib, math
HERE = os.path.dirname(os.path.abspath(__file__))

def sh(cmd, **kw): return subprocess.run(cmd, check=True, **kw)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('reel'); ap.add_argument('--stills'); ap.add_argument('--sheet', action='store_true')
    ap.add_argument('--workers', type=int, default=3); ap.add_argument('--crf', type=int, default=18); ap.add_argument('--no-audio', action='store_true'); ap.add_argument('--keep-frames', action='store_true')
    a = ap.parse_args()
    src = os.path.abspath(a.reel); base = os.path.dirname(src); name = os.path.splitext(os.path.basename(src))[0]
    reel = json.load(open(src)); fmt = reel.setdefault('format', {'w': 1440, 'h': 1080, 'fps': 25}); fps = fmt.get('fps', 25)
    out = os.path.join(base, 'out'); bdir = os.path.join(out, '_build'); os.makedirs(bdir, exist_ok=True)
    for f in ('index.html', 'engine.js', 'fonts.css'): shutil.copy(os.path.join(HERE, f), bdir)
    if not os.path.exists(os.path.join(bdir, 'fonts')): shutil.copytree(os.path.join(HERE, 'fonts'), os.path.join(bdir, 'fonts'))

    def resolve(v):
        if isinstance(v, str) and os.path.splitext(v)[1].lower() in ('.jpg', '.jpeg', '.png', '.webp', '.svg', '.gif'):
            p = v if os.path.isabs(v) else os.path.join(base, v)
            if not os.path.exists(p): sys.exit(f'missing asset: {v}')
            return {'src': 'file://' + p}
        if isinstance(v, str) and os.path.splitext(v)[1].lower() in ('.mp4', '.mov', '.webm', '.m4v'): v = {'video': v}
        if isinstance(v, dict) and 'video' in v:
            p = v['video'] if os.path.isabs(v['video']) else os.path.join(base, v['video'])
            if not os.path.exists(p): sys.exit(f'missing video: {v["video"]}')
            hsh = hashlib.md5((p + str(fmt)).encode()).hexdigest()[:10]; d = os.path.join(out, '_v', hsh)
            if not os.path.exists(os.path.join(d, 'done')):
                os.makedirs(d, exist_ok=True); big = max(fmt['w'], fmt['h'])
                sh(['ffmpeg', '-v', 'error', '-y', '-i', p, '-vf', f"fps={fps},scale='if(gt(iw,ih),-2,{big})':'if(gt(iw,ih),{big},-2)'", '-q:v', '3', os.path.join(d, '%05d.jpg')])
                open(os.path.join(d, 'done'), 'w').close()
            n = len([f for f in os.listdir(d) if f.endswith('.jpg')])
            r = {'seq': 'file://' + d, 'n': n, 'fps': fps}
            for k in ('start', 'speed', 'pos'):
                if k in v: r[k] = v[k]
            return r
        if isinstance(v, dict) and isinstance(v.get('src'), str) and set(v) <= {'src', 'pos'} and not v['src'].startswith('file://'): v = dict(v); v['src'] = resolve(v['src'])['src']; return v
        if isinstance(v, list): return [resolve(x) for x in v]
        if isinstance(v, dict): return {k: resolve(x) for k, x in v.items()}
        return v
    data = resolve(reel)
    open(os.path.join(bdir, 'data.js'), 'w').write('window.REEL=' + json.dumps(data, ensure_ascii=False) + ';')

    W, H = fmt['w'], fmt['h']; html = os.path.join(bdir, 'index.html'); rj = os.path.join(HERE, 'render.js')
    # timeline (computed the same way as the engine)
    bpm = reel.get('bpm', 129); beat = 60 / bpm; t = reel.get('offset', 0); scenes = []
    for s in reel['scenes']:
        ev = []
        if s['type'] == 'words':
            wb = s.get('wordBeats', 1); acc = 0
            for shot in s.get('shots', []):
                ws = [w for w in shot.get('words', '').split() if w]; sb = shot.get('beats') or max(len(ws), 1) * wb
                for j in range(len(ws)): ev.append(t + (acc + j * sb / max(len(ws), 1)) * beat)
                acc += sb
            b = s.get('beats') or acc
        elif s['type'] == 'slugs': b = s.get('beats') or len(s.get('items', [])) * s.get('per', .5); ev = [t + k * s.get('per', .5) * beat for k in range(len(s.get('items', [])))]
        else: b = s.get('beats', 4)
        scenes.append({'type': s['type'], 't0': t, 't1': t + b * beat, 'in': s.get('in', 'cut'), 'hit': s.get('hit'), 'energy': s.get('energy'), 'per': s.get('per', .5), 'drop': s.get('drop'), 'events': ev}); t += b * beat
    dur = t + reel.get('tail', 0)
    print(f'{name}: {len(scenes)} scenes, {dur:.2f}s @ {bpm} BPM ({dur / beat:.0f} beats), {W}x{H}@{fps}')

    if a.stills or a.sheet:
        ts = [float(x) for x in a.stills.split(',')] if a.stills else [round((s['t0'] + s['t1']) / 2, 2) for s in scenes]
        sd = os.path.join(out, 'stills'); shutil.rmtree(sd, ignore_errors=True)
        sh(['node', rj, html, sd, str(W), str(H), 'stills'] + [str(x) for x in ts])
        cols = 4 if W >= H else 6; tw = 480 if W >= H else 270
        sh(['ffmpeg', '-v', 'error', '-y', '-pattern_type', 'glob', '-i', os.path.join(sd, 'still_*.jpg'), '-vf', f'scale={tw}:-1,tile={cols}x{math.ceil(len(ts) / cols)}', '-frames:v', '1', os.path.join(out, 'stills_sheet.jpg')])
        print('stills ->', sd, '| sheet ->', os.path.join(out, 'stills_sheet.jpg')); return

    fd = os.path.join(out, 'frames'); shutil.rmtree(fd, ignore_errors=True); os.makedirs(fd)
    nf = int(round(dur * fps)); k = a.workers; step = math.ceil(nf / k); procs = []
    for i in range(k):
        s0, s1 = i * step, min(nf, (i + 1) * step)
        if s0 < s1: procs.append(subprocess.Popen(['node', rj, html, fd, str(W), str(H), str(fps), str(s0), str(s1)]))
    for p in procs:
        if p.wait() != 0: sys.exit('render failed')
    mp4 = os.path.join(out, name + '.mp4'); cmd = ['ffmpeg', '-v', 'error', '-y', '-framerate', str(fps), '-i', os.path.join(fd, 'f%05d.jpg')]
    if not a.no_audio:
        wav = os.path.join(out, 'master.wav')
        if reel.get('music'):
            m = reel['music'] if os.path.isabs(reel['music']) else os.path.join(base, reel['music'])
            sh(['ffmpeg', '-v', 'error', '-y', '-ss', str(reel.get('musicOffset', 0)), '-i', m, '-t', f'{dur:.3f}', '-af', f'afade=t=out:st={max(0, dur - .8):.2f}:d=.8,loudnorm=I=-14:TP=-1:LRA=9', '-ar', '48000', wav])
        else:
            tj = os.path.join(out, 'timeline.json'); json.dump({'bpm': bpm, 'dur': dur, 'scenes': scenes, 'style': reel.get('audio', 'beat')}, open(tj, 'w'))
            raw = os.path.join(out, 'synth.wav'); sh([sys.executable, os.path.join(HERE, 'audio.py'), tj, raw])
            sh(['ffmpeg', '-v', 'error', '-y', '-i', raw, '-af', 'loudnorm=I=-14:TP=-1:LRA=9', '-ar', '48000', wav])
        cmd += ['-i', wav, '-c:a', 'aac', '-b:a', '256k', '-shortest']
    if reel.get('look') == 'film':
        cmd += ['-filter_complex', "[0:v]format=gbrp,split[a][b];[b]colorlevels=rimin=0.72:gimin=0.72:bimin=0.72,gblur=sigma=16[g];[a][g]blend=all_mode=screen:all_opacity=0.28,noise=alls=9:allf=t,vignette=PI/6,format=yuv420p[v]", '-map', '[v]'] + (['-map', '1:a'] if not a.no_audio else [])
    cmd += ['-maxrate', '18M', '-bufsize', '36M'] if reel.get('look') == 'film' else []
    cmd += ['-c:v', 'libx264', '-preset', 'medium', '-crf', str(a.crf), '-pix_fmt', 'yuv420p', '-movflags', '+faststart', mp4]; sh(cmd)
    sh(['ffmpeg', '-v', 'error', '-y', '-i', mp4, '-vf', f"fps={min(4, 48 / dur):.3f},scale={'240' if W >= H else '135'}:-1,tile=8x6", '-frames:v', '1', os.path.join(out, name + '_sheet.jpg')])
    if not a.keep_frames: shutil.rmtree(fd, ignore_errors=True)
    print('done ->', mp4)

if __name__ == '__main__': main()
