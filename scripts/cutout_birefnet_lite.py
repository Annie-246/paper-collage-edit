import glob, os
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
from rembg import remove, new_session
s = new_session("birefnet-general-lite")
fs = sorted(glob.glob("v3/raw/*.png"))
for i, f in enumerate(fs):
    o = f.replace("raw", "cut")
    if os.path.exists(o):
        continue
    cut = remove(Image.open(f), session=s)
    r, g, b, a = cut.split()
    m = np.asarray(a) > 120
    m = ndimage.binary_fill_holes(m)  # close holes (e.g. between hands over the shirt)
    src = Image.open(f).convert("RGB")
    a = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    out = src.convert("RGBA"); out.putalpha(a)
    out.save(o)
    print(f"{i+1}/{len(fs)}", flush=True)
print("DONE", flush=True)
