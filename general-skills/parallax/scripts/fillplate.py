# Background plate: remove subject (alpha from cutout), fill hole by push-pull pyramid, then soften the fill.
import sys, numpy as np
from PIL import Image, ImageFilter
plate, cut, out = sys.argv[1:4]
img = np.asarray(Image.open(plate).convert("RGB")).astype(np.float32)
a = Image.open(cut).split()[-1].filter(ImageFilter.MaxFilter(31))
known = (np.asarray(a) < 20).astype(np.float32)
def rs(x, size):
    return np.asarray(Image.fromarray(x.astype(np.float32), "F").resize(size, Image.BILINEAR))
def pushpull(c, w):
    H, W = w.shape
    if min(H, W) <= 4: 
        s = (c*w).sum()/max(w.sum(),1e-4); return np.full_like(c, s)
    sz = (max(W//2,1), max(H//2,1))
    cw = rs(c*w, sz); ww = rs(w, sz)
    cs = np.where(ww > 1e-4, cw/np.maximum(ww,1e-4), 0)
    coarse = pushpull(cs, np.clip(ww*4,0,1))
    up = rs(coarse, (W, H))
    return c*w + up*(1-w)
res = np.stack([pushpull(img[...,i], known) for i in range(3)], -1)
fill = np.asarray(Image.fromarray(res.clip(0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(8))).astype(np.float32)
res = img*known[...,None] + fill*(1-known[...,None])
Image.fromarray(res.clip(0,255).astype(np.uint8)).save(out, quality=92)
