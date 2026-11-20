"""Channel intro ("حبر وسالفة") in the ink style: ink blot -> logo -> title -> tagline -> 3-image montage -> close.

  python3 make_intro.py [--voice intro_voice.wav] [--out intro.mp4] [--dur 12]

With --voice, the animation stretches to the recording's length and the voice is mixed over music and sound accents.
Montage images are any three illustrations from earlier videos (paths in MONTAGE).
"""
import argparse, json, os, subprocess, wave
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
TITLE, TAG = 'حبر وسالفة', 'القصة كاملة.. بالرسم وباللهجة اللي تحبها'
SUB = 'القصص اللي سمعت نصّها بس'
# animation cues in seconds for a 12 s intro (scaled to other lengths); --cues gives exact times from the recording
DEFAULT = dict(blot=0.1, logo=0.6, title=1.1, sub=2.5, m0=5.0, m1=6.0, m2=7.0, mend=8.2, tag=8.6, subscribe=10.2)
CUES = None

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
    K = CUES if CUES else {k: v * T / 12.0 for k, v in DEFAULT.items()}
    surf = skia.Surface(W, H); c = surf.getCanvas(); paper(c)
    r = 1.7 * ramp(t, K['blot'], 0.9)                                      # 1 ink blot fills the frame
    if r > 0:
        c.drawImage(mask_img(blot(r)), 0, 0, paint=skia.Paint(ColorFilter=skia.ColorFilters.Blend(skia.Color(*INK), skia.BlendMode.kSrcIn)))
    def logo(size, cy, a):
        c.save(); path = skia.Path(); path.addCircle(W / 2, cy, size / 2); c.clipPath(path, doAntiAlias=True)
        c.drawImageRect(LOGO, skia.Rect.MakeXYWH(W / 2 - size / 2, cy - size / 2, size, size), SAMP, skia.Paint(Alphaf=a)); c.restore()
        c.drawCircle(W / 2, cy, size / 2 + 6, skia.Paint(AntiAlias=True, Color=skia.Color(*GOLD, int(255 * a)), Style=skia.Paint.kStroke_Style, StrokeWidth=8))
    def title(cy, rev, und, a):
        x, top, w, h = text_c(c, TITLE, cy, 210, (255, 255, 255), a, rev)
        pen = skia.Paint(AntiAlias=True, Color=skia.Color(*RED, int(255 * a)), Style=skia.Paint.kStroke_Style, StrokeWidth=16, StrokeCap=skia.Paint.kRound_Cap)
        y0 = top + h * 0.80; c.drawLine(x + w, y0, x + w - w * und, y0 + 6 * und, pen)
    m0 = K['m0']
    if t < m0 + 0.3:                                                       # 2 welcome: logo, title, "the stories you only heard half of"
        a = 1 - ramp(t, m0 - 0.1, 0.3)
        logo(300 * back((t - K['logo']) / 0.6), H / 2 - 170, a) if t > K['logo'] else None
        if t > K['title']: title(H / 2 + 110, ramp(t, K['title'], 0.7), ramp(t, K['title'] + 0.5, 0.5), a)
        if t > K['sub']:
            words = SUB.split(); n = int(len(words) * ramp(t, K['sub'], 1.4) + 0.999)
            text_c(c, ' '.join(words[:n]), H / 2 + 330, 76, GOLD, a)
    ends = [K['m1'], K['m2'], K['mend']]
    for i, (pic, word) in enumerate(PICS):                                 # 3 montage, one picture per spoken word
        t0 = [K['m0'], K['m1'], K['m2']][i]; t1 = ends[i]
        if t0 <= t < t1 + 0.35:
            p = ramp(t, t0, 0.35); z = 1.05 + 0.06 * (t - t0) / max(0.5, t1 - t0)
            layer = skia.Surface(W, H); lc = layer.getCanvas(); dw, dh = W * z, H * z
            lc.drawImageRect(pic, skia.Rect.MakeXYWH((W - dw) / 2, (H - dh) / 2, dw, dh), SAMP)
            lc.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=skia.Color(0, 0, 0, 80))); li = layer.makeImageSnapshot()
            if p < 1:
                ms = skia.Surface(W, H); mc = ms.getCanvas(); mc.drawImage(li, 0, 0)
                mc.drawImage(mask_img(brush_wipe(p)), 0, 0, paint=skia.Paint(BlendMode=skia.BlendMode.kDstIn)); li = ms.makeImageSnapshot()
            c.drawImage(li, 0, 0)
            sz = 280 * (1.25 - 0.25 * back((t - t0) / 0.3))
            text_c(c, word, H / 2, sz, (255, 255, 255), ramp(t, t0, 0.15), 1.0, outline=7)
    if t >= K['mend']:                                                     # 4 back on ink: logo, title, tagline, then subscribe
        r2 = 1.7 * ramp(t, K['mend'], 0.5)
        if r2 < 1.7: c.drawImage(mask_img(blot(r2)), 0, 0, paint=skia.Paint(ColorFilter=skia.ColorFilters.Blend(skia.Color(*INK), skia.BlendMode.kSrcIn)))
        else: c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=skia.Color(*INK)))
        logo(260 * back((t - K['mend'] - 0.2) / 0.5), H / 2 - 190, 1)
        title(H / 2 + 70, ramp(t, K['mend'] + 0.2, 0.5), 1.0 if t > K['mend'] + 0.6 else 0, 1)
        if t < K['subscribe']: text_c(c, TAG, H / 2 + 290, 78, GOLD, ramp(t, K['tag'], 0.4))
        else: text_c(c, 'اشترك.. عشان ما تفوتك السالفة الجاية', H / 2 + 290, 78, GOLD, ramp(t, K['subscribe'], 0.4))
    fo = ramp(t, T - 0.45, 0.45)
    if fo > 0: c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=skia.Color(0, 0, 0, int(255 * fo))))
    # film grain + vignette
    g = skia.Paint(Color=skia.Color(0, 0, 0, 0)); g.setShader(skia.GradientShader.MakeRadial((W / 2, H / 2), W * 0.75, [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 110)]))
    c.drawRect(skia.Rect.MakeWH(W, H), g)
    return surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)[..., :3]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--voice'); ap.add_argument('--out', default=os.path.join(HERE, 'intro.mp4')); ap.add_argument('--dur', type=float, default=12.0); ap.add_argument('--cues', help='JSON of cue times (seconds, voice already offset)')
    a = ap.parse_args()
    global CUES
    if a.cues: CUES = json.loads(open(a.cues).read()) if a.cues.endswith('.json') else json.loads(a.cues)
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
    K = CUES if CUES else {k: v * T / 12.0 for k, v in DEFAULT.items()}
    sfx = os.path.join(HERE, 'sfx')
    cues = [('ink.wav', K['blot']), ('pop.wav', K['logo']), ('whoosh.wav', K['title'] - 0.1), ('impact.wav', K['title'] + 0.6),
            ('whoosh.wav', K['m0'] - 0.2), ('whoosh.wav', K['m1'] - 0.2), ('whoosh.wav', K['m2'] - 0.2), ('impact.wav', K['mend'] + 0.2)]
    inputs = ['-i', silent, '-stream_loop', '3', '-i', os.path.join(OUT, 'messi-2026/eleven/music/tense.mp3')]
    filt = f"[1:a]atrim=0:{T:.2f},afade=t=in:d=0.6,afade=t=out:st={T-1.2:.2f}:d=1.2,volume=0.55[m];"
    mix = ['[m]']
    for k, (f, t0) in enumerate(cues):
        inputs += ['-i', os.path.join(sfx, f)]; ms = max(0, int(t0 * 1000))
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
