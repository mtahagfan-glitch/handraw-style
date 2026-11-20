"""Beat-locked music bed + SFX generated from the reel timeline.

python3 audio.py timeline.json out.wav
timeline.json = {"bpm":129, "dur":48.2, "scenes":[{"type","t0","t1","in","hit","energy"}...]}

Energy per scene (auto from type unless the scene sets "energy"):
  hit     – hook: impacts, no groove
  full    – four-on-the-floor, clap on 2/4, 8th hats, bass
  flurry  – full + 16th hats + arp, every cut gets a tick
  break   – pads + soft pulse only (the calm, narrative middle)
  none    – pad tail only
"""
import json, sys
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

T = json.load(open(sys.argv[1])); OUT = sys.argv[2]
SR = 48000; BPM = T.get('bpm', 129); BEAT = 60 / BPM
DUR = T['dur']; N = int(SR * (DUR + .2))
rng = np.random.default_rng(T.get('seed', 7))
L = np.zeros(N); R = np.zeros(N)

def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x)
def lp(x, f): return sosfilt(butter(2, f, 'low', fs=SR, output='sos'), x)
def hp(x, f): return sosfilt(butter(2, f, 'high', fs=SR, output='sos'), x)
def tt(d): return np.arange(int(d * SR)) / SR
def note(n): return 440 * 2 ** ((n - 69) / 12)
def add(sig, t, g=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N or t < 0: return
    sig = sig[:N - i]
    L[i:i + len(sig)] += sig * g * np.cos((pan + 1) * np.pi / 4) * 1.414
    R[i:i + len(sig)] += sig * g * np.sin((pan + 1) * np.pi / 4) * 1.414

def kick():
    t = tt(.5); f = 45 + 120 * np.exp(-t * 30); ph = 2 * np.pi * np.cumsum(f) / SR
    return np.tanh(1.8 * np.sin(ph) * np.exp(-t * 7))
def clap():
    t = tt(.3); n = rng.normal(0, 1, len(t)); s = np.zeros(len(t))
    for k, o in enumerate([0, .01, .021]):
        i = int(o * SR); s[i:] += n[:len(t) - i] * np.exp(-t[:len(t) - i] * (70 if k < 2 else 17))
    return bp(s, 900, 4500) * .5
def hat(open_=False):
    t = tt(.22 if open_ else .05); return hp(rng.normal(0, 1, len(t)), 7500) * np.exp(-t * (16 if open_ else 80)) * .32
def saw(f, t): return 2 * ((f * t) % 1) - 1
def pad(notes, d, g, cut):
    t = tt(d); s = sum(saw(note(n + dt), t + rng.random()) for n in notes for dt in (-.07, 0, .07))
    return lp(s / (len(notes) * 3), cut) * np.minimum(1, t / .3) * np.minimum(1, (d - t) / .35) * g
def pluck(n):
    t = tt(.35); return lp((saw(note(n), t) + .5 * saw(note(n + 12.03), t)) * np.exp(-t * 12), 3500)
def sub(n, d):
    t = tt(d); return np.tanh(1.7 * np.sin(2 * np.pi * note(n) * t)) * np.minimum(1, t / .01) * np.exp(-t * 1.5)
IR = lp(rng.normal(0, 1, int(1.8 * SR)) * np.exp(-np.arange(int(1.8 * SR)) / SR * 3.5), 5000)
def verb(x, mix=.3):
    w = fftconvolve(x, IR) * .03; o = np.zeros(len(w)); o[:len(x)] += x; return o * (1 - mix) + w * mix
def impact(g=1.0):
    t = tt(2.2); f = 32 + 65 * np.exp(-t * 6)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.7) + lp(rng.normal(0, 1, len(t)), 3500) * np.exp(-t * 10) * .45
    return verb(np.tanh(1.5 * s), .35) * g
def whoosh(d=.5, up=True):
    t = tt(d); x = t / d; n = rng.normal(0, 1, len(t)); o = np.zeros(len(t))
    for k, (lo, hi) in enumerate([(300, 700), (700, 1500), (1500, 3000), (3000, 6500)]):
        c = (k + .5) / 4; c = c if up else 1 - c; o += bp(n, lo, hi) * np.exp(-((x - c) ** 2) / .03)
    return o * np.sin(np.pi * x) ** 1.5 * .9
def riser(d=1.0):
    t = tt(d); x = t / d; f = 220 * 2 ** (x * 3)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * .25 + hp(rng.normal(0, 1, len(t)), 1600) * .6) * x ** 2.3
def tick(f=2600):
    t = tt(.025); return np.sin(2 * np.pi * f * t) * np.exp(-t * 260)
def pop(f0=520):
    t = tt(.17); f = f0 * (1 + 1.2 * (1 - np.exp(-t * 40))); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 22)

CH = [[62, 65, 69], [58, 62, 65], [65, 69, 72], [60, 64, 67]]; ROOT = [38, 34, 41, 36]
def bar(t): return int(round(t / BEAT) // 4) % 4

AUTO = {'hook': 'hit', 'flurry': 'flurry', 'likes': 'flurry', 'grid': 'flurry', 'nodes': 'break', 'scale': 'break', 'spot': 'break',
        'handle': 'none', 'ripple': 'full', 'more': 'full', 'helix': 'break'}
POPS = {'tiles': (1.6, 3.6, .125), 'likes': (.8, 4.0, .125), 'grid': (0, 1.2, .125), 'bounce': (0, 1.5, .5), 'nodes': (0, 2.25, .75), 'palette': (.5, 2.0, .5), 'glyph': (0, 1.75, .35)}


def piano(n, d=1.6):
    t = tt(d); f = note(n)
    s = sum(np.sin(2 * np.pi * f * k * t) * (.6 ** (k - 1)) * np.exp(-t * (2.2 + k)) for k in range(1, 5))
    return s * np.minimum(1, t / .004) * .5
def drone(n, d, g=.2, cut=900):
    t = tt(d); s = sum(np.sin(2 * np.pi * note(n + o) * t + rng.random() * 6) for o in (0, 7, 12, -12)) / 4
    return lp(s, cut) * np.minimum(1, t / 1.2) * np.minimum(1, (d - t) / 1.2) * g
def softkick():
    t = tt(.4); f = 40 + 60 * np.exp(-t * 25); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
if T.get('style') == 'manifesto':
    MEL = [69, 72, 76, 74, 72, 69, 67, 69, 64, 67, 72, 71]; mi = 0
    add(verb(drone(45, DUR, .16, 700), .5), 0, 1)
    for sc in T['scenes']:
        t0, t1, ty = sc['t0'], sc['t1'], sc['type']; nb = round((t1 - t0) / BEAT)
        if ty == 'decode':
            add(verb(drone(57, t1 - t0 + .5, .12, 2000), .6), t0, 1)
            for k in range(int(3 * 8)): add(tick(2200 + 900 * hash_ if (hash_ := (k * 37 % 11) / 11) else 2200), t0 + k * BEAT / 8, .06, (k % 2) - .5)
        if ty == 'words':
            for i, e in enumerate(sc.get('events', [])):
                add(verb(piano(MEL[mi % len(MEL)]), .45), e, .32, (mi % 3 - 1) * .3); mi += 1
            for k in range(0, nb, 2): add(softkick(), t0 + k * BEAT, .35)
        if ty == 'full':
            add(riser(t1 - t0), t0, .5); add(verb(drone(52, t1 - t0, .14, 1600), .6), t0, 1)
        if ty == 'slugs':
            for k in range(nb):
                tb = t0 + k * BEAT; add(softkick(), tb, .6); add(hat(), tb + BEAT / 2, .35, .3); add(sub(ROOT[bar(tb)], .8), tb, .3)
            for i, e in enumerate(sc.get('events', [])): add(pluck(MEL[i % len(MEL)] + 0), e, .09, (i % 2) - .5); add(tick(3200), e, .08)
        if ty == 'swap':
            for k in range(nb): add(verb(piano([57, 60, 64, 67][k % 4], 2.5), .5), t0 + k * BEAT, .18)
        if sc.get('in') in ('smear', 'zoom', 'push'): add(whoosh(.6), t0 - .35, .5)
        if sc.get('hit'): add(impact(.6), t0)
    mix = hp(np.stack([L, R]), 28).T
    mix = np.tanh(mix / (np.abs(mix).max() + 1e-9) * 1.1) / np.tanh(1.1)
    fl = int(1.5 * SR); mix[-fl:] *= np.linspace(1, 0, fl)[:, None] ** 2
    wavfile.write(OUT, SR, (mix * .89 * 32767).astype(np.int16)); print('audio', OUT); sys.exit(0)

for sc in T['scenes']:
    t0, t1 = sc['t0'], sc['t1']; en = sc.get('energy') or AUTO.get(sc['type'], 'full'); nb = round((t1 - t0) / BEAT)
    # pads everywhere except hook, brighter in break
    for k in range(0, nb, 4):
        tb = t0 + k * BEAT; c = CH[bar(tb)]; d = min(4, nb - k) * BEAT + .05
        if en != 'hit':
            add(pad([n - 12 for n in c] + [c[0]], d, .2 if en in ('break', 'none') else .13, 2200 if en == 'break' else 1400), tb, 1, -.3)
            add(pad(c, d, .1, 1800), tb, 1, .3)
    for k in range(nb):
        tb = t0 + k * BEAT; pos = round(tb / BEAT) % 4
        if en in ('full', 'flurry'):
            add(kick(), tb, .85)
            if pos in (1, 3): add(clap(), tb, .7, .05)
            add(hat(), tb + BEAT / 2, .5, -.25)
            if pos == 0: add(sub(ROOT[bar(tb)], 1.0), tb, .5)
        if en == 'flurry':
            for q in (1, 3): add(hat(), tb + q * BEAT / 4, .35, .3)
            c = CH[bar(tb)]
            for q in range(2): add(pluck([c[0] + 12, c[1] + 12, c[2] + 12, c[1] + 12][(k * 2 + q) % 4]), tb + q * BEAT / 2, .1, .4 - .8 * q)
        if en == 'break':
            if pos == 0: add(kick(), tb, .45); add(sub(ROOT[bar(tb)], 1.6), tb, .35)
            add(pluck(CH[bar(tb)][k % 3] + 24), tb, .05, (k % 2) - .5)
    # transitions & hits
    kind = sc.get('in', 'cut')
    if kind in ('push', 'zoom', 'up', 'iris', 'shrink'): add(whoosh(.5, kind != 'shrink'), t0 - .32, .75)
    if sc.get('hit') or sc['type'] == 'hook': add(impact(1.0 if sc.get('hit') else .6), t0)
    elif kind == 'cut' and en in ('full', 'flurry'): add(impact(.3), t0)
    if sc.get('drop'): add(riser(4 * BEAT), t0 - 4 * BEAT, .7)
    if sc['type'] == 'counter':
        for j in range(1, 22): p = j / 23; add(tick(2400 + 300 * (j % 2)), t0 + (.2 + 1.6 * (-np.log2(1 - p) / 10)) * BEAT, .14, (j % 2) - .5)
    if sc['type'] == 'flurry':
        per = sc.get('per', .5)
        for k in range(int(nb / per)): add(tick(3000), t0 + k * per * BEAT, .18)
    if sc['type'] in POPS:
        a, b, st = POPS[sc['type']]; x = a
        while x < min(b, nb): add(pop(480 + 40 * ((x * 8) % 6)), t0 + x * BEAT, .22, ((x * 8) % 2) - .5); x += st
    if sc['type'] == 'hook':
        for k in range(nb): add(pop(420 + k * 60), t0 + k * BEAT, .25)
    if sc['type'] == 'more':
        for k in range(nb): add(impact(.35), t0 + k * BEAT)
    if sc['type'] == 'stroke': add(whoosh(1.2, True), t0, .4)
    if sc['type'] == 'handle': add(verb(pad(CH[0], 3, .2, 1200), .55), t0, 1)

mix = hp(np.stack([L, R]), 28).T
mix = np.tanh(mix / (np.abs(mix).max() + 1e-9) * 1.25) / np.tanh(1.25)
fl = int(.8 * SR); mix[-fl:] *= np.linspace(1, 0, fl)[:, None] ** 2
wavfile.write(OUT, SR, (mix * .89 * 32767).astype(np.int16))
print('audio', OUT, round(len(mix) / SR, 2), 's')
