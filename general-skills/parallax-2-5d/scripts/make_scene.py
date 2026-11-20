"""Write a HyperFrames sub-composition that animates one still image as 2.5D depth parallax.

The scene reads assets/scenes/<id>/plate.jpg and depth.png (white = near) from the project.

  python3 -I make_scene.py --project <dir> --id <scene-id> --duration 3 \
      [--size 1080x1920] [--preset push-in] [--params '{"cx":[0.4,0.55]}'] [--mood warm|cold|none]

Presets (all overridable by --params; each value is [start, end]):
  push-in, pull-out, pan-left, pan-right, rise, descend, reveal-zoom, orbit-left, orbit-right
Params:
  cx, cy   window centre in image uv (0..1)          zoom   1 = image fits the frame's short fit
  sx, sy   camera swing = parallax strength (uv)      focus  depth that stays still (0 far .. 1 near)
  ease     GSAP ease for the whole move (string)
"""
import argparse, json, random
from pathlib import Path

PRESETS = {
    "push-in":     dict(zoom=[1.0, 1.18], sx=[-0.015, 0.015], focus=0.55),
    "pull-out":    dict(zoom=[1.2, 1.0], sx=[0.015, -0.015], focus=0.55),
    "pan-left":    dict(cx=[0.62, 0.38], zoom=[1.08, 1.12], sx=[0.03, -0.03], focus=0.5),
    "pan-right":   dict(cx=[0.38, 0.62], zoom=[1.08, 1.12], sx=[-0.03, 0.03], focus=0.5),
    "rise":        dict(cy=[0.6, 0.42], zoom=[1.1, 1.15], sy=[0.025, -0.025], focus=0.5),
    "descend":     dict(cy=[0.4, 0.6], zoom=[1.1, 1.15], sy=[-0.025, 0.025], focus=0.5),
    "reveal-zoom": dict(zoom=[1.0, 1.55], sx=[-0.012, 0.012], sy=[0.012, -0.008], focus=0.7),
    "orbit-left":  dict(zoom=[1.1, 1.14], sx=[0.04, -0.04], focus=0.6),
    "orbit-right": dict(zoom=[1.1, 1.14], sx=[-0.04, 0.04], focus=0.6),
}
DEF = dict(cx=[0.5, 0.5], cy=[0.5, 0.5], zoom=[1.0, 1.12], sx=[0, 0], sy=[0, 0], focus=0.5, ease="sine.inOut")

ap = argparse.ArgumentParser()
ap.add_argument("--project", required=True); ap.add_argument("--id", required=True)
ap.add_argument("--duration", type=float, required=True); ap.add_argument("--size", default="1080x1920")
ap.add_argument("--preset", default="push-in", choices=sorted(PRESETS))
ap.add_argument("--params", default="{}"); ap.add_argument("--mood", default="warm", choices=["warm", "cold", "none"])
ap.add_argument("--motes", type=int, default=22)
a = ap.parse_args()
W, H = (int(v) for v in a.size.lower().split("x"))
P = {**DEF, **PRESETS[a.preset], **json.loads(a.params)}
sid, D = a.id, a.duration

rnd = random.Random(f"parallax-{sid}")
motes = [] if a.mood == "none" else [
    (i, rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(2, 6), rnd.uniform(-50, 50),
     rnd.uniform(-140, -30), rnd.uniform(0.25, 0.7)) for i in range(a.motes)]
col = {"warm": "255,210,140", "cold": "215,230,245", "none": "0,0,0"}[a.mood]
glow = {"warm": "rgba(255,180,100,0.20)", "cold": "rgba(160,195,230,0.16)", "none": "rgba(0,0,0,0)"}[a.mood]
mote_html = "\n".join(
    f'      <i id="{sid}-m{i}" class="{sid}-mote" style="left:{x:.0f}px;top:{y:.0f}px;width:{2*r:.1f}px;height:{2*r:.1f}px;opacity:{o:.2f}"></i>'
    for i, x, y, r, dx, dy, o in motes)
mote_js = ",".join(f"[{i},{dx:.1f},{dy:.1f}]" for i, x, y, r, dx, dy, o in motes)
flicker = "" if a.mood == "none" else f"""
      const n = Math.max(2, Math.round(D / 0.35));
      for (let j = 0; j < n; j++) tl.to("#{sid}-glow", {{ opacity: j % 2 ? 1 : 0.75, duration: D / n, ease: "sine.inOut" }}, j * D / n);"""

html = f"""<template>
  <style>
    #root {{ position: absolute; inset: 0; overflow: hidden; background: #0d0f14; }}
    #{sid}-gl {{ position: absolute; inset: 0; width: 100%; height: 100%; }}
    #{sid}-fx {{ position: absolute; inset: 0; }}
    .{sid}-mote {{ position: absolute; border-radius: 50%; background: rgba({col},0.85); box-shadow: 0 0 8px 2px rgba({col},0.45); }}
    #{sid}-glow {{ position: absolute; inset: 0; background: radial-gradient(ellipse at 28% 32%, {glow} 0%, rgba(0,0,0,0) 62%); mix-blend-mode: screen; }}
    #{sid}-vig {{ position: absolute; inset: 0; background: radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 48%, rgba(8,10,14,0.6) 100%); }}
  </style>
  <div id="root" data-composition-id="{sid}" data-width="{W}" data-height="{H}">
    <canvas id="{sid}-gl" width="{W}" height="{H}"></canvas>
    <div id="{sid}-fx">
{mote_html}
    </div>
    <div id="{sid}-glow"></div>
    <div id="{sid}-vig"></div>
  </div>
  <script>
    (function () {{
      const D = {D}, CW = {W}, CH = {H};
      const P = {json.dumps({k: P[k] for k in ("cx", "cy", "zoom", "sx", "sy", "focus")})};
      const cv = document.getElementById("{sid}-gl");
      const gl = cv.getContext("webgl", {{ preserveDrawingBuffer: true, premultipliedAlpha: false }});
      const vs = "attribute vec2 a;varying vec2 v;void main(){{v=a*0.5+0.5;v.y=1.0-v.y;gl_Position=vec4(a,0.,1.);}}";
      const fs = `precision highp float;varying vec2 v;uniform sampler2D img,dep;
        uniform vec2 c,sw,win;uniform float f;
        void main(){{
          vec2 uv=c+(v-0.5)*win;
          vec2 hit=uv+sw*(0.0-f);
          for(int i=0;i<48;i++){{                       // march near -> far, first surface hit wins
            float t=1.0-float(i)/47.0;
            vec2 s=uv+sw*(t-f);
            if(texture2D(dep,s).r>=t){{hit=s;break;}}
          }}
          gl_FragColor=vec4(texture2D(img,clamp(hit,0.001,0.999)).rgb,1.0);
        }}`;
      const sh = (t, s) => {{ const o = gl.createShader(t); gl.shaderSource(o, s); gl.compileShader(o); return o; }};
      const pr = gl.createProgram();
      gl.attachShader(pr, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, fs));
      gl.linkProgram(pr); gl.useProgram(pr);
      gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,1,1]), gl.STATIC_DRAW);
      const la = gl.getAttribLocation(pr, "a"); gl.enableVertexAttribArray(la); gl.vertexAttribPointer(la, 2, gl.FLOAT, false, 0, 0);
      const U = n => gl.getUniformLocation(pr, n);
      let ready = false, base = [1, 1];
      function tex(unit, im) {{
        const t = gl.createTexture(); gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, t);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, im);
        [gl.TEXTURE_WRAP_S, gl.TEXTURE_WRAP_T].forEach(k => gl.texParameteri(gl.TEXTURE_2D, k, gl.CLAMP_TO_EDGE));
        [gl.TEXTURE_MIN_FILTER, gl.TEXTURE_MAG_FILTER].forEach(k => gl.texParameteri(gl.TEXTURE_2D, k, gl.LINEAR));
      }}
      const load = s => new Promise((ok, no) => {{ const i = new Image(); i.onload = () => ok(i); i.onerror = no; i.src = s; }});
      const state = {{ p: 0 }}, L = (r, k) => r[0] + (r[1] - r[0]) * k;
      function draw() {{
        if (!ready) return;
        const k = state.p, z = L(P.zoom, k);
        gl.uniform2f(U("c"), L(P.cx, k), L(P.cy, k)); gl.uniform2f(U("sw"), L(P.sx, k), L(P.sy, k));
        gl.uniform2f(U("win"), base[0] / z, base[1] / z); gl.uniform1f(U("f"), P.focus);
        gl.viewport(0, 0, CW, CH); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      }}
      const done = Promise.all([load("assets/scenes/{sid}/plate.jpg"), load("assets/scenes/{sid}/depth.png")]).then(([im, dp]) => {{
        const ia = im.width / im.height, fa = CW / CH;    // cover-fit window in image uv
        base = fa < ia ? [fa / ia, 1] : [1, ia / fa];
        tex(0, im); tex(1, dp); gl.uniform1i(U("img"), 0); gl.uniform1i(U("dep"), 1); ready = true; draw();
      }});
      window.__hf = window.__hf || {{}}; window.__hf.buildReady = window.__hf.buildReady || {{}};
      window.__hf.buildReady["{sid}"] = done;

      const tl = gsap.timeline({{ paused: true }});
      tl.fromTo(state, {{ p: 0 }}, {{ p: 1, duration: D, ease: {json.dumps(P["ease"])}, onUpdate: draw }}, 0);
      [{mote_js}].forEach(([i, dx, dy]) => {{
        tl.fromTo("#{sid}-m" + i, {{ x: 0, y: 0 }}, {{ x: dx, y: dy, duration: D, ease: "none" }}, 0);
      }});{flicker}
      window.__timelines["{sid}"] = tl;
    }})();
  </script>
</template>
"""
out = Path(a.project) / "compositions" / f"{sid}.html"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html, encoding="utf-8")
host = f'''<div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html"
  data-start="START" data-duration="{D}" data-track-index="1" data-track-kind="graphics"
  data-width="{W}" data-height="{H}" style="z-index: 2"></div>'''
print(out); print("host for index.html (set START):"); print(host)
