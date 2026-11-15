# Raw depth output -> 16-bit-ish smoothed 8-bit PNG at source size (white = near).
import sys, numpy as np
from PIL import Image, ImageFilter
raw, W, H, src, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]
d = np.fromfile(raw, dtype=np.float32).reshape(H, W)
lo, hi = np.percentile(d, 1), np.percentile(d, 99.5)
d = ((d - lo) / (hi - lo)).clip(0, 1)
size = Image.open(src).size
im = Image.fromarray((d * 255).astype(np.uint8)).resize(size, Image.BICUBIC).filter(ImageFilter.GaussianBlur(2))
im.save(out)
