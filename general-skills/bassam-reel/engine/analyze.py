#!/usr/bin/env python3
"""Study a reference video: contact sheets, hard cuts, luminance rhythm, tempo, onsets.

  python3 analyze.py reference.mp4 outdir [--fps 5]
Writes outdir/sheet_XX.jpg (8 s each, timestamped) and outdir/report.txt.
"""
import subprocess, sys, os, numpy as np
src, out = sys.argv[1], sys.argv[2]; fps = float(sys.argv[sys.argv.index('--fps') + 1]) if '--fps' in sys.argv else 5
os.makedirs(out, exist_ok=True)
D = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src], capture_output=True, text=True).stdout)
for i in range(int(np.ceil(D / 8))):
    a = i * 8
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(a), '-t', '8', '-i', src, '-vf', f"fps={fps},scale=288:-1,drawtext=text='%{{eif\\:t+{a}\\:d}}.%{{eif\\:mod(t*10\\,10)\\:d}}':x=4:y=4:fontsize=18:fontcolor=yellow:box=1:boxcolor=black@0.7,tile=8x{int(np.ceil(8 * fps / 8))}", '-frames:v', '1', os.path.join(out, f'sheet_{i:02d}.jpg')], check=True)
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-vf', 'fps=25,scale=64:48,format=gray', '-f', 'rawvideo', '-'], capture_output=True).stdout
f = np.frombuffer(raw, np.uint8).reshape(-1, 48, 64).astype(float); d = np.abs(np.diff(f, axis=0)).mean((1, 2)); lum = f.mean((1, 2))
cuts = [(i + 1) / 25 for i in range(len(d)) if d[i] > 18 and d[i] > 2.5 * np.median(d[max(0, i - 5):i + 6])]
sr = 22050; a = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True).stdout, np.float32)
rep = [f'duration {D:.2f}s', f'hard cuts ({len(cuts)}): ' + ' '.join(f'{c:.2f}' for c in cuts), 'luminance /0.5s: ' + ' '.join(str(int(lum[min(len(lum) - 1, int(t * 25))])) for t in np.arange(0, D, .5))]
if len(a) > sr:
    hop, win = 512, 1024; fr = sr / hop
    M = np.log1p(np.array([np.abs(np.fft.rfft(a[i:i + win] * np.hanning(win))) for i in range(0, len(a) - win, hop)]))
    flux = np.maximum(np.diff(M, axis=0), 0).sum(1); flux = (flux - flux.mean()) / flux.std()
    ac = np.correlate(flux, flux, 'full')[len(flux) - 1:]; lags = np.arange(len(ac)) / fr; m = (lags > 60 / 180) & (lags < 60 / 70)
    per = lags[m][np.argmax(ac[m])]; bpm = 60 / per
    pk = [i / fr for i in range(1, len(flux) - 1) if flux[i] > 2.2 and flux[i] >= flux[i - 1] and flux[i] >= flux[i + 1]]
    ph = np.angle(np.mean(np.exp(2j * np.pi * np.array(pk) / per))) / (2 * np.pi) * per % per if pk else 0
    rms = [20 * np.log10(np.sqrt((a[int(t * sr):int((t + 1) * sr)] ** 2).mean()) + 1e-9) for t in range(int(D))]
    off = [round(((c - ph) / per - round((c - ph) / per)) * per * 1000) for c in cuts]
    rep += [f'tempo ~{bpm:.1f} BPM (beat {per:.3f}s, phase {ph:.3f}s)', 'onsets: ' + ' '.join(f'{x:.2f}' for x in pk), 'loudness dB/s: ' + ' '.join(str(int(x)) for x in rms), 'cut offset from nearest beat (ms): ' + ' '.join(map(str, off))]
open(os.path.join(out, 'report.txt'), 'w').write('\n'.join(rep)); print('\n'.join(rep))
