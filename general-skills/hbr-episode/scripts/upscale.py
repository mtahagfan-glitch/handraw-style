"""Upscale scene drawings with SeedVR (fal.ai) so the 1440p export stays sharp. Keeps the ink/paper look
(ESRGAN 'anime' models flatten the paper texture: do not use them).

  python3 upscale.py imgs/ plates/          (run from the episode folder; FAL_KEY in the env)

For every imgs/NN.png -> plates/NN/plate.jpg at 2560x1440 (or 1440x2560 for portrait), skipping done ones.
depth.png does not need redoing (the shader samples it by UV).
"""
import base64, json, os, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
def up(p):
    out = dst / p.stem / 'plate.jpg'
    if out.exists() and max(Image.open(out).size) >= 2560: return
    uri = 'data:image/png;base64,' + base64.b64encode(p.read_bytes()).decode()
    req = urllib.request.Request('https://fal.run/fal-ai/seedvr/upscale/image', json.dumps({'image_url': uri, 'upscale_factor': 3}).encode(),
                                 {'Authorization': 'Key ' + os.environ['FAL_KEY'], 'Content-Type': 'application/json'})
    url = json.load(urllib.request.urlopen(req, timeout=900))['image']['url']
    tmp = dst / p.stem / 'up.png'; tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_bytes(urllib.request.urlopen(url).read())
    im = Image.open(tmp).convert('RGB'); size = (2560, 1440) if im.width >= im.height else (1440, 2560)
    im.resize(size, Image.LANCZOS).save(out, quality=95); tmp.unlink(); print('ok', p.name, flush=True)
with ThreadPoolExecutor(4) as ex: list(ex.map(up, sorted(src.glob('*.png'))))
