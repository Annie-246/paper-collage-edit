import sys
# Detect red jar lids per frame (0-18.5s) and follow named jars by nearest-neighbour from seeds.
import subprocess, json, numpy as np
from scipy import ndimage
F = sys.argv[1] if len(sys.argv) > 1 else "input.mp4"
W, H = 960, 540
p = subprocess.Popen(["ffmpeg", "-v", "error", "-t", "18.6", "-i", F, "-vf", "scale=960:540", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
det = []
while True:
    b = p.stdout.read(W * H * 3)
    if len(b) < W * H * 3:
        break
    a = np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(int)
    m = (a[..., 0] > 140) & (a[..., 0] - a[..., 1] > 90) & (a[..., 0] - a[..., 2] > 70)
    m = ndimage.binary_opening(m, iterations=1)
    lab, k = ndimage.label(m)
    objs = []
    for i, sl in enumerate(ndimage.find_objects(lab)):
        area = int((lab[sl] == i + 1).sum())
        cy, cx = ndimage.center_of_mass(lab == i + 1)
        hgt = (sl[0].stop - sl[0].start) * 2
        x, y = cx * 2, cy * 2
        lips = 930 < x < 1080 and 420 < y < 510 and hgt <= 36
        if area >= 120 and not lips:
            objs.append((x, y, area))
    det.append(objs)
json.dump(det, open("v2/det.json", "w"))
print(len(det))
