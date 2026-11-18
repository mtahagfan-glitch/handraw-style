"""Channel intro ("حبر وسالفة") in the ink style: ink blot -> logo -> title -> tagline -> 3-image montage -> close.

  python3 make_intro.py [--voice intro_voice.wav] [--out intro.mp4] [--dur 12]

With --voice, the animation stretches to the recording's length and the voice is mixed over music and sound accents.
Montage images are any three illustrations from earlier videos (paths in MONTAGE).
"""
import argparse, os, subprocess, wave
import numpy as np, skia
from skia import textlayout as tl

HERE = os.path.dirname(os.path.abspath(__file__))
CH = os.path.dirname(HERE)
OUT = os.path.join(CH, '..')
W, H, FPS = 1920, 1080, 25
PAPER = (242, 234, 218); INK = (16, 14, 12); RED = (214, 34, 40); GOLD = (232, 182, 60)
MONTAGE = [(os.path.join(OUT, 'milan-ultras/plates/28/plate.jpg'), 'جرايم'),
           (os.path.join(OUT, 'messi-2026/plates/01/plate.jpg'), 'كورة'),
           (os.path.join(OUT, 'milan-ultras/plates/14/plate.jpg'), 'أسرار')]
TITLE, TAG = 'حبر وسالفة', 'القصة كاملة.. بالرسم وباللهجة اللي تفهمها'

rng = np.random.default_rng(7)
def noise(h, w, scale):
    from PIL import Image
    small = rng.random((h // scale + 2, w // scale + 2)).astype(np.float32)
    big = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(big, np.float32) / 255.0
N1 = 0.6 * noise(H, W, 40) + 0.4 * noise(H, W, 9)            # ragged ink edge
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
DIST = np.hypot(xx - W / 2, (yy - H / 2) * 1.15) / np.hypot(W / 2, H / 2 * 1.15)

def ease(t): t = min(max(t, 0.0), 1.0); return 1 - (1 - t) ** 3
def ramp(t, a, d): return ease((t - a) / d)
def back(t): t = min(max(t, 0.0), 1.0); c = 1.7; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2

def mask_img(a):
    m = (np.clip(a, 0, 1) * 255).astype(np.uint8)
    rgba = np.zeros((H, W, 4), np.uint8); rgba[..., 3] = m
    return skia.Image.fromarray(rgba, colorType=skia.ColorType.kRGBA_8888_ColorType)

def blot(r):        # 1 inside the ink blot of radius r (0..1.6), ragged edge
    return np.clip((r - (DIST + 0.18 * N1)) * 18, 0, 1)

def brush_wipe(p):  # right-to-left brush wipe, 0..1
    edge = (1 - p) * 1.25 - 0.12
    return np.clip(((xx / W) - edge + 0.09 * (N1 - 0.5)) * 14, 0, 1)

tf = skia.Typeface.MakeFromFile(os.path.join(CH, 'fonts/Lalezar.ttf'))
prov = tl.TypefaceFontProvider(); prov.registerTypeface(tf, 'L'); FC = tl.FontCollection(); FC.setDefaultFontManager(prov)
def para(t, size, rgb, a=1.0):
    ts = tl.TextStyle(); ts.setFontSize(size); ts.setColor(skia.Color(*rgb, int(255 * a))); ts.setFontFamilies(['L'])
    b = tl.ParagraphBuilder(tl.ParagraphStyle(), FC, skia.Unicodes.ICU.Make()); b.pushStyle(ts); b.addText('‫' + t + '‬')
    p = b.Build(); p.layout(4000); return p
def text_c(c, t, cy, size, rgb, a=1.0, reveal=1.0, outline=0):
    p = para(t, size, rgb, a); w = p.LongestLine; x = (W - w) / 2; top = cy - p.Height / 2
    c.save(); c.clipRect(skia.Rect.MakeLTRB(x + w * (1 - reveal) - 20, top - 40, x + w + 20, top + p.Height + 40))
    if outline:
        for dx, dy in [(-outline, 0), (outline, 0), (0, -outline), (0, outline)]: para(t, size, INK, a).paint(c, x + dx, top + dy)
    p.paint(c, x, top); c.restore(); return x, top, w, p.Height

def img(path):
    return skia.Image.open(path)
LOGO = img(os.path.join(CH, 'channel_avatar.png'))
PICS = [(img(p), w) for p, w in MONTAGE]
SAMP = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)

def paper(c):
    c.clear(skia.Color(*PAPER))
    p = skia.Paint(Color=skia.Color(120, 100, 70, 22)); c.drawRect(skia.Rect.MakeWH(W, H), p)

def frame(t, T):
    s = T / 12.0                      # all timings scale with the voice length
    surf = skia.Surface(W, H); c = surf.getCanvas(); paper(c)
    # 1 ink blot spreads (0 -> 1.1s), stays as background until the montage
    r = 1.7 * ramp(t, 0.15 * s, 1.0 * s)
    if r > 0:
        c.save(); c.drawImage(mask_img(blot(r)), 0, 0, paint=skia.Paint(ColorFilter=skia.ColorFilters.Blend(skia.Color(*INK), skia.BlendMode.kSrcIn))); c.restore()
    # 2 logo pops in the centre (1.0 -> 1.8s), moves up for the title
    lp = back((t - 1.0 * s) / (0.7 * s)); up = ramp(t, 2.0 * s, 0.6 * s); out = ramp(t, 5.2 * s, 0.4 * s) - ramp(t, 10.6 * s, 0.4 * s) * 0
    if lp > 0 and t < 5.6 * s or t > 10.4 * s:
        k = lp if t < 5.6 * s else ease((t - 10.4 * s) / (0.5 * s))
        size = 420 * k * (1 - 0.35 * up) if t < 5.6 * s else 300 * k
        cy = H / 2 - 170 * up if t < 5.6 * s else H / 2 - 120
        a = 1 - out if t < 5.6 * s else 1
        c.save(); path = skia.Path(); path.addCircle(W / 2, cy, size / 2); c.clipPath(path, doAntiAlias=True)
        c.drawImageRect(LOGO, skia.Rect.MakeXYWH(W / 2 - size / 2, cy - size / 2, size, size), SAMP, skia.Paint(Alphaf=a)); c.restore()
        ring = skia.Paint(AntiAlias=True, Color=skia.Color(*GOLD, int(255 * a)), Style=skia.Paint.kStroke_Style, StrokeWidth=8)
        c.drawCircle(W / 2, cy, size / 2 + 6, ring)
    # 3 title wipes in right-to-left (2.3 -> 3.2s) with a red brush underline
    if 2.2 * s < t < 5.7 * s or t > 10.5 * s:
        tr = ramp(t, 2.3 * s, 0.8 * s) if t < 6 * s else ramp(t, 10.6 * s, 0.5 * s)
        a = 1 - ramp(t, 5.2 * s, 0.4 * s) if t < 6 * s else 1
        cy = H / 2 + 120 if t < 6 * s else H / 2 + 150
        x, top, w, h = text_c(c, TITLE, cy, 210, (255, 255, 255), a, tr)
        u = ramp(t, 3.0 * s, 0.6 * s) if t < 6 * s else ramp(t, 11.0 * s, 0.5 * s)
        pen = skia.Paint(AntiAlias=True, Color=skia.Color(*RED, int(255 * a)), Style=skia.Paint.kStroke_Style, StrokeWidth=16, StrokeCap=skia.Paint.kRound_Cap)
        y0 = top + h + 6; c.drawLine(x + w, y0, x + w - w * u, y0 + 6 * u, pen)
        # 4 tagline types on word by word (3.6 -> 5.0s)
        if t < 6 * s:
            words = TAG.split(); n = int(len(words) * ramp(t, 3.6 * s, 1.2 * s) + 0.999)
            if n: text_c(c, ' '.join(words[:n]), cy + 235, 78, GOLD, a)
        else:
            text_c(c, 'اشترك.. عشان ما تفوتك السالفة الجاية', cy + 225, 72, GOLD, ramp(t, 11.2 * s, 0.4 * s))
    # 5 montage: three illustrations through brush wipes, slow push, big word label (5.5 -> 10.5s)
    for i, (pic, word) in enumerate(PICS):
        t0 = (5.5 + i * 1.7) * s; d = 1.9 * s
        if t0 <= t < t0 + d + 0.6 * s and t < 10.9 * s:
            p = ramp(t, t0, 0.55 * s); z = 1.06 + 0.08 * (t - t0) / d
            c.save()
            m = brush_wipe(p) if p < 1 else None
            layer = skia.Surface(W, H); lc = layer.getCanvas()
            dw, dh = W * z, H * z; lc.drawImageRect(pic, skia.Rect.MakeXYWH((W - dw) / 2, (H - dh) / 2, dw, dh), SAMP)
            shade = skia.Paint(Color=skia.Color(0, 0, 0, 70)); lc.drawRect(skia.Rect.MakeWH(W, H), shade)
            li = layer.makeImageSnapshot()
            if m is not None:
                ms = skia.Surface(W, H); mc = ms.getCanvas(); mc.drawImage(li, 0, 0)
                mc.drawImage(mask_img(m), 0, 0, paint=skia.Paint(BlendMode=skia.BlendMode.kDstIn)); li = ms.makeImageSnapshot()
            c.drawImage(li, 0, 0)
            wa = ramp(t, t0 + 0.35 * s, 0.35 * s)
            if wa > 0:
                sz = 260 * (1.25 - 0.25 * back((t - t0 - 0.35 * s) / (0.4 * s)))
                text_c(c, word, H / 2, sz, (255, 255, 255), wa, 1.0, outline=7)
            c.restore()
    fo = ramp(t, T - 0.45, 0.45)
    if fo > 0: c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=skia.Color(0, 0, 0, int(255 * fo))))
    # film grain + vignette
    g = skia.Paint(Color=skia.Color(0, 0, 0, 0)); g.setShader(skia.GradientShader.MakeRadial((W / 2, H / 2), W * 0.75, [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 110)]))
    c.drawRect(skia.Rect.MakeWH(W, H), g)
    return surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)[..., :3]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--voice'); ap.add_argument('--out', default=os.path.join(HERE, 'intro.mp4')); ap.add_argument('--dur', type=float, default=12.0)
    a = ap.parse_args()
    T = a.dur
    if a.voice:
        T = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', a.voice])) + 0.6
    n = int(T * FPS)
    silent = os.path.join(HERE, '_video.mp4')
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', silent], stdin=subprocess.PIPE)
    for i in range(n):
        ff.stdin.write(np.ascontiguousarray(frame(i / FPS, T)).tobytes())
    ff.stdin.close(); ff.wait()
    s = T / 12.0
    sfx = os.path.join(HERE, 'sfx')
    cues = [('ink.wav', 0.1), ('pop.wav', 1.0), ('whoosh.wav', 2.2), ('impact.wav', 3.0), ('whoosh.wav', 5.4), ('whoosh.wav', 7.1), ('whoosh.wav', 8.8), ('riser.wav', 9.4), ('impact.wav', 10.6)]
    inputs = ['-i', silent, '-stream_loop', '3', '-i', os.path.join(OUT, 'messi-2026/eleven/music/tense.mp3')]
    filt = f"[1:a]atrim=0:{T:.2f},afade=t=in:d=0.6,afade=t=out:st={T-1.2:.2f}:d=1.2,volume=0.55[m];"
    mix = ['[m]']
    for k, (f, t0) in enumerate(cues):
        inputs += ['-i', os.path.join(sfx, f)]; ms = int(t0 * s * 1000)
        filt += f"[{k+2}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms}[c{k}];"; mix.append(f'[c{k}]')
    if a.voice:
        inputs += ['-i', a.voice]; vi = len(cues) + 2
        filt += f"[{vi}:a]aresample=48000,aformat=channel_layouts=stereo,adelay=300|300,asplit=2[v1][v2];"
        filt += f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0[bg];[bg][v1]sidechaincompress=threshold=0.03:ratio=3:attack=20:release=400[duck];[v2][duck]amix=inputs=2:normalize=0"
    else:
        filt += f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0"
    filt += f",atrim=0:{T:.2f},alimiter=limit=0.89[out]"
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', filt, '-map', '0:v', '-map', '[out]', '-c:v', 'copy',
                    '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', a.out], check=True)
    os.remove(silent); print(a.out, round(T, 2), 's')

if __name__ == '__main__':
    main()
