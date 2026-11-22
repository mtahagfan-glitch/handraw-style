"""Motion-graphics inserts for the channel, rendered with HyperFrames in the ink-on-paper look.

  python3 mg.py <template> '<json params>' <out.webm|out.mp4> [--size 1920x1080] [--dur 4]

Templates (Arabic text is shaped by the browser; font = Amiri Bold from assets/fonts):
  stat      {"num": 8, "suffix": "", "prefix": "", "label": "أهداف في البطولة", "sub": "رقم قياسي"}
            big number counts up, label underneath. Full card on dark paper (mp4) or transparent (webm).
  name      {"name": "كيليان مبابي", "role": "مهاجم فرنسا · 19 سنة"}           lower third, slides in, transparent.
  timeline  {"items": [["1986","مارادونا"],["2014","نهائي ضايع"],["2022","اللقب"]], "title": "..."}
  map       {"bg": "plate.jpg", "points": [[0.32,0.40,"روساريو"],[0.62,0.30,"برشلونة"]], "title": "..."}
            ink line draws from point to point (x,y as 0-1 of the frame) over a picture.
  quote     {"text": "...", "who": "..."}                                   big quote card.

.webm renders keep transparency: overlay them on the scene with
  ffmpeg -i scene.mp4 -c:v libvpx-vp9 -i card.webm -filter_complex "[0][1]overlay=enable='between(t,2,6)'" ...
(the -c:v libvpx-vp9 before the webm input is what keeps its alpha).
"""
import argparse, json, shutil, subprocess, tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
FONT = SKILL / 'assets' / 'fonts' / 'Amiri-Bold.ttf'       # channel font for video text: Amiri
ap = argparse.ArgumentParser(); ap.add_argument('tpl'); ap.add_argument('params'); ap.add_argument('out')
ap.add_argument('--size', default='1920x1080'); ap.add_argument('--dur', type=float, default=4.0)
a = ap.parse_args(); P = json.loads(a.params); W, H = map(int, a.size.split('x')); D = a.dur
ALPHA = a.out.endswith(('.webm', '.mov'))
GOLD, RED, PAPER, INK = '#ffd23f', '#e0312a', '#efe6d2', '#141414'
BG = 'transparent' if ALPHA else f'radial-gradient(ellipse at 50% 45%, #2a2621 0%, #0f0e0c 75%)'

css = f"""@font-face{{font-family:L;src:url(assets/Amiri-Bold.ttf);font-weight:700}}
*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:{W}px;height:{H}px;overflow:hidden;background:{'transparent' if ALPHA else '#0f0e0c'}}}
#root{{position:relative;width:100%;height:100%;background:{BG};font-family:L;font-weight:700;line-height:1.35;direction:rtl;color:{PAPER}}}
.c{{position:absolute;left:0;right:0;text-align:center}}
.o{{-webkit-text-stroke:{max(4,H//180)}px {INK};paint-order:stroke fill;text-shadow:0 {H//200}px 0 {INK}}}
.grain{{position:absolute;inset:0;opacity:.10;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence baseFrequency='.9'/%3E%3C/filter%3E%3Crect width='300' height='300' filter='url(%23n)'/%3E%3C/svg%3E")}}"""
u = H / 1080
if a.tpl == 'stat':
    body = f"""<div class="c o" id="num" style="top:{H*0.22}px;font-size:{340*u}px;color:{GOLD}">{P.get('prefix','')}<span id="n">0</span>{P.get('suffix','')}</div>
<div class="c o" id="lab" style="top:{H*0.60}px;font-size:{96*u}px">{P['label']}</div>
<div class="c" id="bar" style="top:{H*0.75}px;margin:auto;width:{W*0.32}px;height:{10*u}px;background:{RED};transform-origin:right"></div>
<div class="c o" id="sub" style="top:{H*0.79}px;font-size:{60*u}px;color:{GOLD}">{P.get('sub','')}</div>"""
    js = f"""const o={{v:0}};tl.from('#num',{{scale:.6,opacity:0,duration:.5,ease:'back.out(2)'}},0.1)
.to(o,{{v:{P['num']},duration:1.2,ease:'power2.out',onUpdate:()=>document.getElementById('n').textContent=Math.round(o.v)}},0.2)
.from('#lab',{{y:{40*u},opacity:0,duration:.5}},0.7).from('#bar',{{scaleX:0,duration:.5,ease:'power3.out'}},1.0)
.from('#sub',{{opacity:0,duration:.4}},1.3).to('#root',{{opacity:0,duration:.35}},{D-0.35});"""
elif a.tpl == 'name':
    body = f"""<div id="box" style="position:absolute;right:{90*u}px;bottom:{120*u}px;padding:{18*u}px {44*u}px {22*u}px;background:{PAPER};border-right:{14*u}px solid {RED};box-shadow:{10*u}px {10*u}px 0 {INK}">
<div id="nm" style="font-size:{78*u}px;color:{INK};line-height:1.45">{P['name']}</div>
<div id="rl" style="font-size:{44*u}px;color:#7a2018;line-height:1.5">{P.get('role','')}</div></div>"""
    js = f"""tl.from('#box',{{x:{500*u},opacity:0,duration:.55,ease:'power3.out'}},0.1).from('#nm',{{opacity:0,duration:.3}},0.45)
.from('#rl',{{opacity:0,y:{14*u},duration:.3}},0.6).to('#box',{{x:{500*u},opacity:0,duration:.4,ease:'power2.in'}},{D-0.45});"""
elif a.tpl == 'timeline':
    it = P['items']; n = len(it); x0, x1 = W * 0.88, W * 0.12
    dots = ''.join(f"""<div class="d" id="d{i}" style="position:absolute;left:{x0+(x1-x0)*i/max(1,n-1)-14*u}px;top:{H*0.55-14*u}px;width:{28*u}px;height:{28*u}px;border-radius:50%;background:{GOLD};border:{5*u}px solid {INK}"></div>
<div class="o" id="y{i}" style="position:absolute;width:{360*u}px;text-align:center;left:{x0+(x1-x0)*i/max(1,n-1)-180*u}px;top:{H*0.40}px;font-size:{80*u}px;color:{GOLD}">{y}</div>
<div class="o" id="t{i}" style="position:absolute;width:{380*u}px;text-align:center;left:{x0+(x1-x0)*i/max(1,n-1)-190*u}px;top:{H*0.60}px;font-size:{50*u}px">{t}</div>""" for i, (y, t) in enumerate(it))
    body = f"""<div class="c o" id="tt" style="top:{H*0.14}px;font-size:{90*u}px">{P.get('title','')}</div>
<div id="ln" style="position:absolute;left:{x1}px;width:{x0-x1}px;top:{H*0.55-3*u}px;height:{6*u}px;background:{PAPER};transform-origin:right"></div>{dots}"""
    step = (D - 1.6) / n
    js = "tl.from('#tt',{opacity:0,y:-30,duration:.4},0.1).from('#ln',{scaleX:0,duration:%.2f,ease:'none'},0.3)" % (step * n) + ''.join(
        f".from('#d{i}',{{scale:0,duration:.3,ease:'back.out(3)'}},{0.3+step*i+0.1:.2f}).from('#y{i}',{{opacity:0,y:20,duration:.3}},{0.3+step*i+0.15:.2f}).from('#t{i}',{{opacity:0,duration:.3}},{0.3+step*i+0.3:.2f})" for i in range(n)) + f".to('#root',{{opacity:0,duration:.35}},{D-0.35});"
elif a.tpl == 'map':
    pts = P['points']; path = 'M ' + ' L '.join(f'{x*W:.0f} {y*H:.0f}' for x, y, _ in pts)
    marks = ''.join(f"""<div id="p{i}" style="position:absolute;left:{x*W-16*u}px;top:{y*H-16*u}px;width:{32*u}px;height:{32*u}px;border-radius:50%;background:{RED};border:{5*u}px solid {PAPER}"></div>
<div class="o" id="l{i}" style="position:absolute;width:{400*u}px;text-align:center;left:{x*W-200*u}px;top:{y*H-110*u}px;font-size:{64*u}px">{nm}</div>""" for i, (x, y, nm) in enumerate(pts))
    bg = f'<img src="assets/bg.jpg" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;filter:brightness(.55) sepia(.25)">' if P.get('bg') else ''
    body = f"""{bg}<svg width="{W}" height="{H}" style="position:absolute;inset:0"><path id="rt" d="{path}" fill="none" stroke="{GOLD}" stroke-width="{9*u}" stroke-linecap="round" stroke-dasharray="{22*u} {14*u}"/></svg>{marks}
<div class="c o" id="tt" style="top:{H*0.06}px;font-size:{84*u}px">{P.get('title','')}</div>"""
    n = len(pts); step = (D - 1.4) / max(1, n - 1)
    js = ("const L=document.getElementById('rt').getTotalLength();gsap.set('#rt',{strokeDashoffset:0});"
          f"tl.from('#tt',{{opacity:0,duration:.4}},0.1).from('#p0',{{scale:0,duration:.3,ease:'back.out(3)'}},0.2).from('#l0',{{opacity:0,duration:.3}},0.3)"
          f".fromTo('#rt',{{attr:{{'stroke-dasharray':`0 ${{L}}`}}}},{{attr:{{'stroke-dasharray':`${{L}} 0`}},duration:{step*(n-1):.2f},ease:'power1.inOut'}},0.5)"
          + ''.join(f".from('#p{i}',{{scale:0,duration:.3,ease:'back.out(3)'}},{0.5+step*i:.2f}).from('#l{i}',{{opacity:0,duration:.3}},{0.55+step*i:.2f})" for i in range(1, n))
          + f".to('#root',{{opacity:0,duration:.35}},{D-0.35});")
elif a.tpl == 'quote':
    body = f"""<div class="c o" id="q" style="top:{H*0.26}px;padding:0 {W*0.12}px;font-size:{86*u}px;line-height:1.45">«{P['text']}»</div>
<div class="c o" id="w" style="top:{H*0.72}px;font-size:{56*u}px;color:{GOLD}">— {P.get('who','')}</div>"""
    js = f"tl.from('#q',{{opacity:0,y:{30*u},duration:.6}},0.1).from('#w',{{opacity:0,duration:.4}},0.9).to('#root',{{opacity:0,duration:.35}},{D-0.35});"
else:
    raise SystemExit('unknown template ' + a.tpl)

html = f"""<!doctype html><html lang="ar" data-resolution="{'landscape' if W > H else 'portrait'}"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width={W}, height={H}"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script><style>{css}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{D}" data-width="{W}" data-height="{H}">
{'' if ALPHA else '<div class="grain"></div>'}{body}</div>
<script>const tl=gsap.timeline({{paused:true}});{js}window.__timelines["main"]=tl;tl.seek(0);</script></body></html>"""
p = Path(tempfile.mkdtemp(prefix='mg_'))
for f in ('hyperframes.json', 'package.json', 'meta.json'): shutil.copy(SKILL / 'assets' / 'hf-template' / f, p / f)
(p / 'assets').mkdir(); shutil.copy(FONT, p / 'assets' / 'Amiri-Bold.ttf')
if a.tpl == 'map' and P.get('bg'): shutil.copy(P['bg'], p / 'assets' / 'bg.jpg')
(p / 'index.html').write_text(html)
fmt = ['--format', 'webm'] if a.out.endswith('.webm') else ['--format', 'mov'] if a.out.endswith('.mov') else []
subprocess.run(['npx', 'hyperframes', 'render', '--fps', '25', '--quality', 'delivery', *fmt, '-o', str(Path(a.out).resolve())],
               check=True, cwd=p, stdout=subprocess.DEVNULL, stderr=open(p / 'render.log', 'w'))
shutil.rmtree(p); print(a.out)
