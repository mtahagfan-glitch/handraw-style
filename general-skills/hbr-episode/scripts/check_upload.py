"""Pre-upload check for a finished video: does it meet YouTube (long or Shorts) delivery and channel standards?

  python3 check_upload.py <video> [--shorts]

Checks: container/codec, resolution and aspect, frame rate, duration (Shorts ≤ 3 min), audio codec/rate/channels,
integrated loudness (channel target -14 LUFS ±2) and true peak (≤ -1 dBTP), long silences, black stretches,
and file size against the 400 MB send limit. Prints PASS / WARN / FAIL per line; exit 1 on any FAIL.
"""
import json, re, subprocess, sys
v = sys.argv[1]; SH = '--shorts' in sys.argv
pr = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', v]))
vs = next(s for s in pr['streams'] if s['codec_type'] == 'video'); au = next((s for s in pr['streams'] if s['codec_type'] == 'audio'), None)
dur = float(pr['format']['duration']); size = int(pr['format']['size']) / 2**20; W, H = vs['width'], vs['height']
fps = eval(vs['avg_frame_rate']) if vs['avg_frame_rate'] != '0/0' else 0
rows = []; ok = lambda c, msg, warn=False: rows.append(('PASS' if c else ('WARN' if warn else 'FAIL'), msg))
ok(vs['codec_name'] in ('h264', 'hevc', 'vp9', 'av1'), f"video codec {vs['codec_name']}")
ok(vs.get('pix_fmt', '').startswith('yuv420'), f"pixel format {vs.get('pix_fmt')}", warn=True)
if SH:
    ok(H > W and abs(W / H - 9 / 16) < 0.02, f"Shorts aspect {W}x{H} (9:16)")
    ok(dur <= 180, f"Shorts duration {dur:.1f}s (≤ 180 s)"); ok(H >= 1920, f"height {H} (≥ 1920)", warn=True)
else:
    ok(W > H and abs(W / H - 16 / 9) < 0.02, f"aspect {W}x{H} (16:9)"); ok(H >= 1440, f"height {H} (1440p gets YouTube's better codec)", warn=True)
ok(23.9 <= fps <= 60.1, f"frame rate {fps:.2f}")
if au:
    ok(au['codec_name'] in ('aac', 'opus', 'mp3', 'pcm_s16le'), f"audio codec {au['codec_name']}")
    ok(int(au['sample_rate']) in (44100, 48000), f"sample rate {au['sample_rate']}"); ok(au.get('channels') == 2, f"channels {au.get('channels')}", warn=True)
    e = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', v, '-map', '0:a:0', '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    I = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', e)[-1]); TP = float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', e)[-1])
    ok(-16 <= I <= -12, f"loudness {I:.1f} LUFS (target -14 ±2)", warn=True); ok(TP <= -0.5, f"true peak {TP:.1f} dBTP (≤ -1)", warn=True)
    sil = re.findall(r'silence_duration: ([\d.]+)', subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', v, '-map', '0:a:0', '-af', 'silencedetect=n=-45dB:d=3', '-f', 'null', '-'], capture_output=True, text=True).stderr)
    ok(not sil, f"silences ≥ 3 s: {len(sil)}" + (f" (longest {max(map(float, sil)):.1f}s)" if sil else ''), warn=True)
else:
    ok(False, 'no audio stream')
blk = re.findall(r'black_duration:([\d.]+)', subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', v, '-vf', 'blackdetect=d=1.5:pix_th=0.08', '-an', '-f', 'null', '-'], capture_output=True, text=True).stderr)
ok(not blk, f"black stretches ≥ 1.5 s: {len(blk)}", warn=True)
ok(size <= 400, f"file size {size:.0f} MB (send limit 400 MB; YouTube itself takes up to 256 GB)", warn=True)
for s, m in rows: print(f"{s:4}  {m}")
print(f"duration {dur/60:.2f} min"); sys.exit(1 if any(s == 'FAIL' for s, _ in rows) else 0)
