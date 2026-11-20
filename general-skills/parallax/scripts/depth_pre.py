# Prepare float32 NCHW tensor for Depth Anything V2 (ImageNet norm), sides multiple of 14.
import sys, numpy as np
from PIL import Image
src, out, H = sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 518
im = Image.open(src).convert("RGB"); w, h = im.size
W = round(w * H / h / 14) * 14
x = np.asarray(im.resize((W, H), Image.BICUBIC)).astype(np.float32) / 255.0
x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
x.transpose(2, 0, 1)[None].astype(np.float32).tofile(out)
print(W, H)
