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
  trace     {"shapes":[{"type":"circle","x":.5,"y":.6,"r":.08},{"type":"arrow","from":[.2,.3],"to":[.45,.55]},
             {"type":"underline","x":.3,"y":.7,"w":.2}], "label":{"text":"هذا هو الحد","x":.5,"y":.25}}
            red ink marks draw themselves over the scene (webm). Point at the one detail the sentence is about.
  chapter   {"num": "الجزء الثاني", "title": "الهروب"}     ink floods, title stamps, ink drains, title parks in the
            corner (webm, ~4.5 s). Put one on every music section change: the viewer feels the new part.
  dots      {"n": 40, "hit": 5, "label": "طلقة", "hit_label": "خمس منها أصابته"}   one dot per unit, hits turn red (mp4 card)
  stamp     {"text": "خرق للهدنة", "x": .5, "y": .45}       rubber stamp slams on, misregistered then aligned (webm)
  measure   {"cm": 27, "label": "أطول دودة", "max": 30}     ruler draws, red bar grows to the length (webm)
  cctv      {"label": "كاميرا مراقبة · بانمونجوم"}          REC, brackets, scanlines for scenes told from real CCTV (webm, whole scene);
            when overlaying, also grade the scene: -vf "hue=s=0.35,noise=alls=10:allf=t" so it reads as footage

  kinetic   {"lines":["كل مهمة","بجلسة لحالها"], "hi":["بجلسة"], "theme":"light|dark", "img":"cutout.png", "arrow":true,
             "arrow_from":[.18,.48], "arrow_to":[.36,.58], "color":"#e0312a"}
            fast explainer beat: spotlight paper or dark stage, words pop in one by one with an RGB-split fringe that settles,
            coloured keywords, slow push + hit-shake, optional cut-out object with shadow and a hand-drawn arrow (mp4 card).
            Best in shorts: one beat per 1.5-3 s, 2-4 words per line.
  board     {"title":"...", "notes":[["الخطوة 1","..."],["الخطوة 2","..."],["الخطوة 3","..."]]}
            investigation board: pinned paper notes pop in and a red string draws between them (mp4). For plots, suspects, steps.
  chart     {"label":"...", "values":[2,5,3,8,6,12], "value":"+300%"}   glowing line chart draws, value pops (mp4)

Use a graphic only when it makes the sentence land harder (a number to remember, the detail to look at, a new part).
Never two at once, never on a moving (Flow/Veo) shot, and keep at least one plain scene between graphics.

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
    n = len(pts); step = (D - 2.4) / max(1, n - 1)   # leave ~1.5 s to read the last point
    js = ("const L=document.getElementById('rt').getTotalLength();gsap.set('#rt',{strokeDashoffset:0});"
          f"tl.from('#tt',{{opacity:0,duration:.4}},0.1).from('#p0',{{scale:0,duration:.3,ease:'back.out(3)'}},0.2).from('#l0',{{opacity:0,duration:.3}},0.3)"
          f".fromTo('#rt',{{attr:{{'stroke-dasharray':`0 ${{L}}`}}}},{{attr:{{'stroke-dasharray':`${{L}} 0`}},duration:{step*(n-1):.2f},ease:'power1.inOut'}},0.5)"
          + ''.join(f".from('#p{i}',{{scale:0,duration:.3,ease:'back.out(3)'}},{0.5+step*i:.2f}).from('#l{i}',{{opacity:0,duration:.3}},{0.55+step*i:.2f})" for i in range(1, n))
          + f".to('#root',{{opacity:0,duration:.35}},{D-0.35});")
elif a.tpl == 'quote':
    body = f"""<div class="c o" id="q" style="top:{H*0.26}px;padding:0 {W*0.12}px;font-size:{86*u}px;line-height:1.45">«{P['text']}»</div>
<div class="c o" id="w" style="top:{H*0.72}px;font-size:{56*u}px;color:{GOLD}">— {P.get('who','')}</div>"""
    js = f"tl.from('#q',{{opacity:0,y:{30*u},duration:.6}},0.1).from('#w',{{opacity:0,duration:.4}},0.9).to('#root',{{opacity:0,duration:.35}},{D-0.35});"
elif a.tpl == 'trace':
    # hand-drawn ink marks drawn on over a scene (transparent): circle a detail, point with an arrow, underline
    import math, random
    rnd = random.Random(7); paths = []
    for sh in P['shapes']:
        if sh['type'] == 'circle':
            cx, cy, r = sh['x'] * W, sh['y'] * H, sh['r'] * H; pts = []
            for k in range(0, 410, 10):                       # a bit more than one loop, wobbly like a pen
                t = math.radians(k - 100); rr = r * (1 + 0.06 * math.sin(k / 37) + rnd.uniform(-0.015, 0.015))
                pts.append(f'{cx + rr * 1.25 * math.cos(t):.0f} {cy + rr * math.sin(t):.0f}')
            paths.append('M ' + ' L '.join(pts))
        elif sh['type'] == 'arrow':
            (x0, y0), (x1, y1) = [(p[0] * W, p[1] * H) for p in (sh['from'], sh['to'])]
            mx, my = (x0 + x1) / 2 + (y1 - y0) * 0.15, (y0 + y1) / 2 - (x1 - x0) * 0.15
            paths.append(f'M {x0:.0f} {y0:.0f} Q {mx:.0f} {my:.0f} {x1:.0f} {y1:.0f}')
            ang = math.atan2(y1 - my, x1 - mx); L = 34 * u
            for d in (2.6, -2.6):
                paths.append(f'M {x1:.0f} {y1:.0f} L {x1 - L * math.cos(ang + d / 6):.0f} {y1 - L * math.sin(ang + d / 6):.0f}')
        elif sh['type'] == 'underline':
            x, y, w = sh['x'] * W, sh['y'] * H, sh['w'] * W
            paths.append(f'M {x:.0f} {y:.0f} Q {x + w / 2:.0f} {y + 9 * u:.0f} {x + w:.0f} {y - 4 * u:.0f}')
    svg = ''.join(f'<path class="pk" pathLength="1" d="{d}"/>' for d in paths)
    lb = P.get('label')
    lab = (f'<div id="lb" style="position:absolute;left:{lb["x"]*W}px;top:{lb["y"]*H}px;transform:translate(-50%,-50%);'
           f'font-size:{lb.get("size",60)*u}px;color:{INK};background:{PAPER};padding:{4*u}px {26*u}px {10*u}px;border-right:{10*u}px solid {RED};box-shadow:{8*u}px {8*u}px 0 {INK};white-space:nowrap">{lb["text"]}</div>') if lb else ''
    body = f"""<svg width="{W}" height="{H}" style="position:absolute;inset:0"><defs><filter id="rough"><feTurbulence baseFrequency="0.03" numOctaves="2" seed="3"/>
<feDisplacementMap in="SourceGraphic" scale="{6*u}"/></filter></defs><g filter="url(#rough)" fill="none" stroke="{RED}" stroke-width="{9*u}" stroke-linecap="round" stroke-linejoin="round">{svg}</g></svg>{lab}"""
    js = (f"gsap.set('.pk',{{strokeDasharray:1,strokeDashoffset:1}});"
          f"tl.to('.pk',{{strokeDashoffset:0,duration:.7,ease:'power2.inOut',stagger:.25}},0.15)"
          + (f".from('#lb',{{opacity:0,y:{12*u},duration:.35}},0.7)" if lb else '') + f".to('#root',{{opacity:0,duration:.35}},{D-0.35});")
elif a.tpl == 'chapter':
    # chapter sting over the first seconds of a part (transparent): ink floods the frame, the title stamps in,
    # the ink drains away and the title shrinks into a corner label that stays a moment
    R = (W ** 2 + H ** 2) ** 0.5 / 2 + 60
    body = f"""<svg width="{W}" height="{H}" style="position:absolute;inset:0"><defs><filter id="bleed"><feTurbulence baseFrequency="0.012" numOctaves="3" seed="9"/>
<feDisplacementMap in="SourceGraphic" scale="{90*u}"/></filter></defs><circle id="ink" cx="{W/2}" cy="{H/2}" r="{R}" fill="{INK}" filter="url(#bleed)"/></svg>
<div id="grp" style="position:absolute;left:0;right:0;top:{H*0.36}px;text-align:center">
<div id="num" style="font-size:{48*u}px;color:{RED};letter-spacing:{2*u}px">{P.get('num','')}</div>
<div id="tt" style="font-size:{150*u}px;color:{PAPER};line-height:1.25">{P['title']}</div>
<div id="rule" style="margin:{6*u}px auto 0;width:{W*0.18}px;height:{8*u}px;background:{RED};transform-origin:right"></div></div>"""
    js = (f"tl.from('#ink',{{attr:{{r:0}},duration:.7,ease:'power3.in'}},0)"
          f".from('#num',{{opacity:0,y:-20,duration:.3}},0.55).from('#tt',{{opacity:0,scale:1.25,duration:.35,ease:'power4.out'}},0.65)"
          f".from('#rule',{{scaleX:0,duration:.4}},0.9)"
          f".to('#ink',{{attr:{{r:0}},duration:.7,ease:'power3.inOut'}},2.0)"
          f".to('#grp',{{top:{40*u},left:{W*0.62},right:{40*u},scale:.55,transformOrigin:'right top',duration:.7,ease:'power3.inOut'}},2.0)"
          f".to('#tt',{{webkitTextStroke:'{8*u}px {INK}',paintOrder:'stroke fill',duration:.1}},2.0)"
          f".to('#grp',{{opacity:0,duration:.4}},{D-0.4});")
elif a.tpl == 'dots':
    # one dot per unit (shots fired, people, years...), then the ones that matter turn red: "40 shots, 5 hit"
    n, hit = int(P['n']), int(P.get('hit', 0)); cols = min(10, n); rows = -(-n // cols); g = 118 * u
    x0, y0 = W / 2 - (cols - 1) * g / 2, H * 0.36 - (rows - 1) * g / 2
    order = list(range(n)); import random; random.Random(4).shuffle(order); red = set(order[:hit])
    dots = ''.join(f'<div class="dt{" hr" if i in red else ""}" style="position:absolute;left:{x0 + (i % cols) * g - 32*u}px;top:{y0 + (i // cols) * g - 32*u}px;'
                   f'width:{64*u}px;height:{64*u}px;border-radius:50%;background:{PAPER};border:{4*u}px solid {INK}"></div>' for i in range(n))
    body = f"""{dots}<div class="c o" id="l1" style="top:{H*0.70}px;font-size:{80*u}px"><span id="cnt">0</span> {P.get('label','')}</div>
<div class="c o" id="l2" style="top:{H*0.81}px;font-size:{64*u}px;color:{RED}">{P.get('hit_label','')}</div>"""
    js = (f"const o={{v:0}};tl.from('.dt',{{scale:0,duration:.18,ease:'back.out(3)',stagger:{1.4/n:.4f}}},0.1)"
          f".to(o,{{v:{n},duration:1.4,ease:'none',onUpdate:()=>document.getElementById('cnt').textContent=Math.round(o.v)}},0.1)"
          f".from('#l1',{{opacity:0,duration:.3}},0.1)"
          f".to('.hr',{{backgroundColor:'{RED}',scale:1.35,duration:.25,stagger:.18,ease:'back.out(4)'}},1.8)"
          f".to('.dt:not(.hr)',{{opacity:.35,duration:.4}},1.8).from('#l2',{{opacity:0,y:20,duration:.35}},2.5)"
          f".to('#root',{{opacity:0,duration:.35}},{D-0.35});")
elif a.tpl == 'stamp':
    # a rubber stamp slams onto the scene, two ink passes misregistered then snapping together (transparent)
    rot = P.get('rot', -8)
    one = lambda col, i: (f'<div id="s{i}" style="position:absolute;left:{P.get("x",.5)*W}px;top:{P.get("y",.5)*H}px;transform:translate(-50%,-50%) rotate({rot}deg);'
                          f'padding:{6*u}px {70*u}px {30*u}px;border:{12*u}px solid {col};border-radius:{10*u}px;color:{col};font-size:{120*u}px;line-height:1.5;white-space:nowrap;mix-blend-mode:multiply">{P["text"]}</div>')
    body = one('#1d1d1d', 1) + one(RED, 2)
    js = (f"tl.from('#s1,#s2',{{scale:2.2,opacity:0,duration:.22,ease:'power4.in'}},0.15)"
          f".fromTo('#s1',{{x:{-14*u},y:{8*u}}},{{x:0,y:0,duration:.35,ease:'power2.out'}},0.37)"
          f".fromTo('#s2',{{x:{12*u},y:{-6*u}}},{{x:0,y:0,duration:.35,ease:'power2.out'}},0.37)"
          f".to('#s1',{{opacity:0,duration:.2}},0.75).to('#root',{{opacity:0,duration:.35}},{D-0.35});")
elif a.tpl == 'measure':
    # an ink ruler draws out and a red bar grows to the length: makes a size physical (transparent)
    cm = float(P['cm']); full = float(P.get('max', max(30, cm + 3))); x, y, w = P.get('x', .18) * W, P.get('y', .80) * H, P.get('w', .64) * W
    ticks = ''.join(f'<div style="position:absolute;right:{x + w * k / full}px;top:{y - (22 if k % 5 == 0 else 12) * u}px;width:{3*u}px;height:{(22 if k % 5 == 0 else 12)*u}px;background:{INK}"></div>' for k in range(int(full) + 1))
    body = f"""<div id="rl" style="position:absolute;right:{x - 10*u}px;top:{y - 40*u}px;width:{w + 20*u}px;height:{80*u}px;background:{PAPER};border:{4*u}px solid {INK};transform-origin:right"></div>
<div id="tk">{ticks}</div><div id="bar" style="position:absolute;right:{x}px;top:{y + 6*u}px;width:{w * cm / full}px;height:{22*u}px;background:{RED};transform-origin:right"></div>
<div class="o" id="val" style="position:absolute;right:{x + w * cm / full - 60*u}px;top:{y - 250*u}px;font-size:{130*u}px;color:{GOLD}"><span id="n">0</span> سم</div>
<div class="o" id="lab" style="position:absolute;right:{x}px;top:{y + 50*u}px;font-size:{56*u}px">{P.get('label','')}</div>"""
    js = (f"const o={{v:0}};tl.from('#rl',{{scaleX:0,duration:.5,ease:'power3.out'}},0.1).from('#tk div',{{opacity:0,duration:.05,stagger:.012}},0.3)"
          f".from('#bar',{{scaleX:0,duration:1.4,ease:'power2.inOut'}},0.8)"
          f".to(o,{{v:{cm},duration:1.4,ease:'power2.inOut',onUpdate:()=>document.getElementById('n').textContent=Math.round(o.v)}},0.8)"
          f".from('#val',{{opacity:0,duration:.3}},0.8).from('#lab',{{opacity:0,duration:.4}},1.6).to('#root',{{opacity:0,duration:.35}},{D-0.35});")
elif a.tpl == 'cctv':
    # surveillance-footage dressing for scenes retold from real camera footage (transparent, lasts the whole scene)
    m = 46 * u; br = lambda s: f'<div style="position:absolute;{s};width:{90*u}px;height:{90*u}px;border-color:{PAPER};border-style:solid;opacity:.9"></div>'
    body = (br(f'left:{m}px;top:{m}px;border-width:{5*u}px 0 0 {5*u}px') + br(f'right:{m}px;top:{m}px;border-width:{5*u}px {5*u}px 0 0')
            + br(f'left:{m}px;bottom:{m}px;border-width:0 0 {5*u}px {5*u}px') + br(f'right:{m}px;bottom:{m}px;border-width:0 {5*u}px {5*u}px 0')
            + f"""<div style="position:absolute;inset:0;background:rgba(8,12,10,.30)"></div><div style="position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(0,0,0,.10) 0 {2*u}px,transparent {2*u}px {5*u}px)"></div>
<div style="position:absolute;inset:0;box-shadow:inset 0 0 {220*u}px rgba(0,0,0,.55)"></div>
<div id="rec" style="position:absolute;left:{m+30*u}px;top:{m+26*u}px;font-family:monospace;font-size:{38*u}px;color:{PAPER};direction:ltr"><span id="dot" style="color:{RED}">●</span> REC</div>
<div style="position:absolute;right:{m+30*u}px;top:{m+18*u}px;font-size:{42*u}px;color:{PAPER};background:rgba(0,0,0,.55);padding:{2*u}px {20*u}px {8*u}px">{P.get('label','')}</div>""")
    js = f"tl.from('#root',{{opacity:0,duration:.3}},0);for(let t=0;t<{D};t+=1)tl.to('#dot',{{opacity:0,duration:.01}},t+.5).to('#dot',{{opacity:1,duration:.01}},t+1);tl.to('#root',{{opacity:0,duration:.3}},{D-0.3});"
elif a.tpl == 'kinetic':
    # kinetic-typography beat (fast explainer look): spotlight paper (light) or dark stage, 1-3 short lines pop in word by
    # word, keywords coloured, RGB-split fringe that settles, slow camera push with a small hit-shake; optional cut-out
    # object (B&W photo/PNG) with drop shadow and a hand-drawn arrow drawing toward it. Full card (mp4).
    light = P.get('theme', 'light') == 'light'; HI = set(P.get('hi', [])); col = P.get('color', RED)
    fg = '#1b1b1b' if light else PAPER
    eh = '80% 48%' if H > W else '62% 58%'
    stage = (f"radial-gradient(ellipse {eh} at 50% 44%, #f4f2ee 0%, #d9d6d0 50%, #7a7772 84%, #2a2927 100%)" if light
             else "radial-gradient(ellipse 60% 55% at 50% 42%, #2b2927 0%, #121110 70%, #050505 100%)")
    grid = (f'<div style="position:absolute;inset:0;opacity:{.16 if light else .08};background-image:linear-gradient({fg} 1px,transparent 1px),'
            f'linear-gradient(90deg,{fg} 1px,transparent 1px);background-size:{56*u}px {56*u}px;-webkit-mask:radial-gradient(ellipse 45% 40% at 50% 60%,#000,transparent)"></div>'
            if P.get('grid', True) else '')
    k = 0; rows = ''; ty = P.get('y', .30 if P.get('img') else .40)
    for li, line in enumerate(P['lines']):
        ws = ''
        for w in line.split():
            c = col if w in HI else fg; ws += f'<span class="w" id="w{k}" style="color:{c}">{w}</span> '; k += 1
        size = (P.get('size', 120) if li == 0 else P.get('size2', P.get('size', 120) * .62)) * u
        rows += f'<div class="c" style="position:relative;font-size:{size}px;line-height:1.45">{ws}</div>'
    img = ''
    if P.get('img'):
        img = (f'<img id="obj" src="assets/obj.png" style="position:absolute;left:50%;top:{P.get("img_y",.62)*H}px;height:{P.get("img_h",.34)*H}px;'
               f'transform:translate(-50%,-50%);filter:grayscale(1) contrast(1.15) drop-shadow({18*u}px {26*u}px {22*u}px rgba(0,0,0,.45))"/>')
    arrow = ''
    if P.get('arrow'):
        ax, ay = P.get('arrow_from', [.18, .48]); bx, by = P.get('arrow_to', [.36, .58])
        x1, y1, x2, y2 = ax*W, ay*H, bx*W, by*H; mx, my = (x1+x2)/2 + (y2-y1)*.25, (y1+y2)/2 - (x2-x1)*.25
        arrow = (f'<svg style="position:absolute;inset:0" width="{W}" height="{H}"><path id="ar" d="M{x1},{y1} Q{mx},{my} {x2},{y2}" fill="none" stroke="{fg}" '
                 f'stroke-width="{7*u}" stroke-linecap="round"/><path id="ah" d="M{x2-30*u},{y2-14*u} L{x2},{y2} L{x2-12*u},{y2-32*u}" fill="none" stroke="{fg}" '
                 f'stroke-width="{7*u}" stroke-linecap="round" stroke-linejoin="round"/></svg>')
    css += (f"#cam{{position:absolute;inset:0;background:{stage}}}.w{{display:inline-block;text-shadow:{6*u}px 0 0 rgba(255,40,40,.55),{-6*u}px 0 0 rgba(0,210,220,.55)}}"
            f".settle .w{{text-shadow:{1.5*u}px 0 0 rgba(255,40,40,.35),{-1.5*u}px 0 0 rgba(0,210,220,.35)}}"
            f"#obj{{outline:none}}.vig{{position:absolute;inset:0;box-shadow:inset 0 0 {260*u}px rgba(0,0,0,{.55 if light else .8})}}")
    body = (f'<div id="cam">{grid}<div id="txt" style="position:absolute;left:{W*.06}px;right:{W*.06}px;top:{ty*H}px;transform:translateY(-50%)">{rows}</div>'
            f'{img}{arrow}<div class="vig"></div></div>')
    js = (f"tl.fromTo('#cam',{{scale:1.0}},{{scale:1.06,duration:{D},ease:'none'}},0)"
          f".from('.w',{{scale:1.6,opacity:0,filter:'blur({10*u}px)',duration:.28,stagger:{P.get('stagger',.22)},ease:'back.out(2.2)'}},0.15)"
          f".to('#cam',{{x:{8*u},y:{-5*u},duration:.05,yoyo:true,repeat:3}},0.15)"
          f".add(()=>document.getElementById('txt').classList.add('settle'),{0.25 + k*P.get('stagger',.22)})")
    if P.get('img'): js += f".from('#obj',{{y:{80*u},opacity:0,rotation:-4,duration:.6,ease:'power3.out'}},{0.3 + k*0.15})"
    if P.get('arrow'):
        js += (f";const ar=document.getElementById('ar'),L=ar.getTotalLength();gsap.set(ar,{{strokeDasharray:L,strokeDashoffset:L}});"
               f"tl.to(ar,{{strokeDashoffset:0,duration:.45,ease:'power2.inOut'}},{0.6 + k*0.18}).from('#ah',{{opacity:0,duration:.1}},{1.05 + k*0.18})")
    js += f";tl.to('#root',{{opacity:0,duration:.3}},{D-0.3});"
elif a.tpl == 'board':
    # investigation board: paper notes pinned on a dark wall pop in one by one and a red string draws between them (mp4)
    notes = P['notes']; n = len(notes)
    pos = P.get('pos') or ([[.32, .26], [.68, .44], [.32, .62], [.68, .80]] if H > W else [[.82, .34], [.61, .68], [.39, .34], [.18, .68]])[:n]   # right-to-left zigzag
    nw = (.42 if H > W else .19) * W
    cards = ''
    for i, (nt, ns) in enumerate(notes):
        x, y = pos[i]; r = [-4, 3, -2, 5][i % 4]
        cards += (f'<div class="nt" id="n{i}" style="position:absolute;left:{x*W}px;top:{y*H}px;width:{nw}px;transform:translate(-50%,-50%) rotate({r}deg);'
                  f'background:#ebe7df;padding:{26*u}px {30*u}px;box-shadow:{14*u}px {20*u}px {24*u}px rgba(0,0,0,.55);color:#1b1b1b">'
                  f'<div style="position:absolute;top:{-14*u}px;left:50%;width:{90*u}px;height:{30*u}px;margin-left:{-45*u}px;background:rgba(230,225,210,.75);transform:rotate(-3deg)"></div>'
                  f'<div style="font-size:{62*u}px;color:{RED}">{nt}</div><div style="font-size:{46*u}px;line-height:1.5">{ns}</div>'
                  f'<div style="height:{8*u}px;width:60%;margin-top:{14*u}px;background:rgba(0,0,0,.12)"></div></div>')
    pts = ' '.join(f'{pos[i][0]*W},{pos[i][1]*H}' for i in range(n))
    title = f'<div class="c" style="top:{H*.06}px;font-size:{64*u}px;color:{PAPER};background:rgba(0,0,0,.5);display:inline-block;left:50%;right:auto;transform:translateX(-50%);padding:{4*u}px {30*u}px {12*u}px">{P["title"]}</div>' if P.get('title') else ''
    css += f"#wall{{position:absolute;inset:0;background:radial-gradient(ellipse 70% 60% at 50% 45%,#2c2a27,#0c0b0a)}}"
    body = (f'<div id="wall"></div><svg style="position:absolute;inset:0" width="{W}" height="{H}"><polyline id="str" points="{pts}" fill="none" stroke="{RED}" '
            f'stroke-width="{6*u}" stroke-linejoin="round"/></svg>{cards}{title}')
    js = ("const s=document.getElementById('str');let L=0;const P=s.points;for(let i=1;i<P.numberOfItems;i++){const a=P.getItem(i-1),b=P.getItem(i);L+=Math.hypot(b.x-a.x,b.y-a.y)}"
          "gsap.set(s,{strokeDasharray:L,strokeDashoffset:L});"
          f"tl.from('.nt',{{scale:1.4,opacity:0,duration:.35,stagger:.45,ease:'back.out(2)'}},0.2)"
          f".to(s,{{strokeDashoffset:0,duration:{max(1.0, n*.45)},ease:'power1.inOut'}},0.5)"
          f".fromTo('#root',{{scale:1}},{{scale:1.05,duration:{D},ease:'none'}},0).to('#root',{{opacity:0,duration:.3}},{D-0.3});")
elif a.tpl == 'chart':
    # a glowing line chart zig-zags up (or down) across a dark stage, the value pops at the end (mp4)
    vals = P.get('values', [2, 5, 3, 8, 6, 12]); mx = max(vals); n = len(vals)
    x0, x1, y0, y1 = .18*W, .82*W, .78*H, .30*H
    pts = ' '.join(f'{x0 + (x1-x0)*i/(n-1)},{y0 - (y0-y1)*v/mx}' for i, v in enumerate(vals))
    css += "#st{position:absolute;inset:0;background:radial-gradient(ellipse 60% 55% at 50% 45%,#262422,#080808)}"
    body = (f'<div id="st"></div><svg style="position:absolute;inset:0" width="{W}" height="{H}"><polyline id="ln" points="{pts}" fill="none" stroke="#f2f0ea" '
            f'stroke-width="{8*u}" stroke-linejoin="miter" style="filter:drop-shadow(0 0 {14*u}px rgba(255,255,255,.6))"/></svg>'
            f'<div class="c o" id="lab" style="top:{H*.10}px;font-size:{90*u}px">{P.get("label","")}</div>'
            f'<div class="o" id="val" style="position:absolute;left:{x1 - 40*u}px;top:{y1 - 190*u}px;font-size:{120*u}px;color:{RED};direction:ltr">{P.get("value","")}</div>')
    js = ("const s=document.getElementById('ln');let L=0;const P=s.points;for(let i=1;i<P.numberOfItems;i++){const a=P.getItem(i-1),b=P.getItem(i);L+=Math.hypot(b.x-a.x,b.y-a.y)}"
          "gsap.set(s,{strokeDasharray:L,strokeDashoffset:L});"
          f"tl.from('#lab',{{opacity:0,y:{30*u},duration:.4}},0.1).to(s,{{strokeDashoffset:0,duration:1.6,ease:'power2.inOut'}},0.3)"
          f".from('#val',{{scale:1.8,opacity:0,duration:.3,ease:'back.out(2)'}},1.8).to('#root',{{opacity:0,duration:.3}},{D-0.3});")
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
if a.tpl == 'kinetic' and P.get('img'): shutil.copy(P['img'], p / 'assets' / 'obj.png')
(p / 'index.html').write_text(html)
fmt = ['--format', 'webm'] if a.out.endswith('.webm') else ['--format', 'mov'] if a.out.endswith('.mov') else []
subprocess.run(['npx', 'hyperframes', 'render', '--fps', '25', '--quality', 'delivery', *fmt, '-o', str(Path(a.out).resolve())],
               check=True, cwd=p, stdout=subprocess.DEVNULL, stderr=open(p / 'render.log', 'w'))
shutil.rmtree(p); print(a.out)
