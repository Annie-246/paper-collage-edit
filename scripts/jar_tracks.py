# Named jar tracks (source time, full-res lid centre) built from per-frame red-lid detections.
import json, numpy as np
DET = json.load(open("v2/det.json"))
FPS = 30


def follow(t0, t1, seed, maxjump=90):
    f0, f1 = int(round(t0 * FPS)), min(int(round(t1 * FPS)), len(DET) - 1)
    pos = np.array(seed, float)
    # snap seed to nearest detection
    out = {}
    for f in range(f0, f1 + 1):
        c = [np.array(d[:2]) for d in DET[f]]
        if c:
            dists = [np.linalg.norm(x - pos) for x in c]
            j = int(np.argmin(dists))
            if dists[j] < maxjump:
                pos = c[j]
        out[f] = pos.copy()
    return out


def smooth(tr, k=5):
    fs = sorted(tr)
    arr = np.array([tr[f] for f in fs])
    pad = np.pad(arr, ((k, k), (0, 0)), mode="edge")
    ker = np.ones(2 * k + 1) / (2 * k + 1)
    sm = np.stack([np.convolve(pad[:, i], ker, "valid") for i in range(2)], 1)
    return {f: sm[i] for i, f in enumerate(fs)}


def merge(*parts):
    out = {}
    for p in parts:
        out.update(p)
    fs = sorted(out)
    full = {}
    for a, b in zip(fs, fs[1:]):
        full[a] = out[a]
        for f in range(a + 1, b):
            w = (f - a) / (b - a)
            full[f] = out[a] * (1 - w) + out[b] * w
    full[fs[-1]] = out[fs[-1]]
    return full


TRACKS = {
    "i1": smooth(follow(0, 2.0, (693, 473))),
    "i2": smooth(follow(0, 2.0, (789, 466))),
    "i3": smooth(follow(0, 2.0, (1308, 486))),
    "wA": smooth(follow(3.3, 6.5, (746, 492))),
    "wB": smooth(follow(3.3, 6.5, (1309, 500))),
    "salt": smooth(follow(8.3, 11.6, (1244, 474))),
    "sugar": smooth(follow(9.8, 18.6, (722, 488))),
    "brown": smooth(merge(follow(11.2, 12.3, (1226, 900)), follow(12.5, 18.6, (1180, 556)))),
}


def at(name, t):
    tr = TRACKS[name]
    f = int(round(t * FPS))
    fs = sorted(tr)
    f = min(max(f, fs[0]), fs[-1])
    return tr[f]


if __name__ == "__main__":
    for n, tr in TRACKS.items():
        fs = sorted(tr)
        print(n, " ".join(f"{f/30:.1f}:({tr[f][0]:.0f},{tr[f][1]:.0f})" for f in fs[::10]))
