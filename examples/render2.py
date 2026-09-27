# v2 edit of segment 1 — applies the user's 9 review comments on top of the v1 paper cut-out style.
import sys, math, random, subprocess, functools, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render as R
from render import (W, H, ANIM, NAVY, MUST, PINK, CORAL, TEAL, CREAM, INK, RED, WOOD, PURPLE, GREEN, DARK,
                    SKINS, S, Sprite, Label, asset, place, pop, write, crayon_circle, note_fn, text_c, clamp,
                    ease_io, background, people, brain_fn, torn_mask, texturize, qmark_fn, font)
sys.path.insert(0, "v2")
import tracks as TK

SRC = "input.mp4"  # path to the source video
OUT = sys.argv[1] if len(sys.argv) > 1 else "v2/out.mp4"
FPS = 30
SRC_END = 70.54

# ---- output <-> source time: freeze at 1.3s (comment 1), 5s countdown replaces the pause 50.65-52.25 (comment 8)
FZ_AT, FZ_LEN = 1.3, 1.2
CD_S0, CD_S1, CD_LEN = 50.65, 52.25, 5.0
CD_T0 = CD_S0 + FZ_LEN
CD_T1 = CD_T0 + CD_LEN
T_END = CD_T1 + (SRC_END - CD_S1)


def o(s):
    """source time -> output time"""
    if s <= FZ_AT:
        return s
    if s < CD_S0:
        return s + FZ_LEN
    return s - CD_S1 + CD_T1


def src_of(t):
    """output time -> source time (None inside the countdown)"""
    if t < FZ_AT:
        return t
    if t < FZ_AT + FZ_LEN:
        return FZ_AT
    if t < CD_T0:
        return t - FZ_LEN
    if t < CD_T1:
        return None
    return CD_S1 + (t - CD_T1)


# ---- camera (comment 4): punch-ins and slow pushes on the speaker, keyed in source time
CAM = [  # (src time, zoom, focus x, focus y)
    (0.0, 1.22, 1000, 520), (1.45, 1.22, 1000, 520), (1.6, 1.0, 960, 540),
    (3.2, 1.0, 960, 540), (3.4, 1.14, 1030, 520), (6.2, 1.2, 1030, 520),
    (6.3, 1.0, 960, 540), (6.45, 1.0, 960, 540), (6.6, 1.12, 980, 420), (8.3, 1.12, 980, 420), (8.45, 1.0, 960, 540),
    (11.4, 1.0, 960, 540), (15.2, 1.1, 1000, 560), (15.3, 1.0, 960, 540), (15.45, 1.08, 980, 500), (18.3, 1.08, 980, 500),
    (18.45, 1.0, 960, 540), (28.2, 1.06, 960, 480),
    (45.2, 1.0, 960, 540), (50.7, 1.08, 960, 520),
]


def cam(s):
    for (t0, z0, x0, y0), (t1, z1, x1, y1) in zip(CAM, CAM[1:]):
        if t0 <= s < t1:
            p = ease_io((s - t0) / (t1 - t0))
            return z0 + (z1 - z0) * p, x0 + (x1 - x0) * p, y0 + (y1 - y0) * p
    return CAM[-1][1:]


def crop_origin(z, fx, fy):
    cw, ch = W / z, H / z
    return clamp(fx - cw / 2, 0, W - cw), clamp(fy - ch / 2, 0, H - ch), cw, ch


def apply_cam(img, s):
    z, fx, fy = cam(s)
    if z <= 1.001:
        return img, (0, 0, 1.0)
    x0, y0, cw, ch = crop_origin(z, fx, fy)
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch)), (x0, y0, z)


def scr(p, camv):
    x0, y0, z = camv
    return ((p[0] - x0) * z, (p[1] - y0) * z)


def jar(name, s, camv):
    """screen-space jar body centre and zoom for a tracked jar (lid centre + offset down to the body)"""
    lid = TK.at(name, s)
    z = camv[2]
    x, y = scr((lid[0], lid[1] + 70), camv)
    return x, y, z


# ---- overlay helpers for the jar section
def dim_spot(frame, spots, a):
    """darken the whole frame except soft ellipses around the given spots (comment 1)."""
    if a <= 0.01:
        return frame
    w2, h2 = W // 4, H // 4
    yy, xx = np.mgrid[0:h2, 0:w2].astype(np.float32)
    hole = np.zeros((h2, w2), np.float32)
    for x, y, rx, ry in spots:
        d = np.sqrt(((xx - x / 4) / (rx / 4)) ** 2 + ((yy - y / 4) / (ry / 4)) ** 2)
        hole = np.maximum(hole, clamp_arr(1.6 - d))
    m = (1 - np.clip(hole, 0, 1)) * 0.62 * a
    m = np.array(Image.fromarray((m * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
    f = np.asarray(frame).astype(np.float32) * (1 - m[..., None])
    return Image.fromarray(f.astype(np.uint8))


def clamp_arr(a):
    return np.clip(a, 0, 1)


def arrow(c, p0, p1, t, t0, dur=0.3, color=RED, width=9, bend=0.18):
    """hand-drawn arrow growing from p0 to p1 with a bent shaft and a two-stroke head."""
    if t < t0:
        return
    p = ease_io(clamp((t - t0) / dur))
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    nx, ny = -(p1[1] - p0[1]) * bend, (p1[0] - p0[0]) * bend
    cx, cy = mx + nx, my + ny
    pts = []
    n = 24
    for i in range(int(n * p) + 1):
        u = i / n
        pts.append(((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * cx + u * u * p1[0],
                    (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * cy + u * u * p1[1]))
    d = ImageDraw.Draw(c)
    if len(pts) > 1:
        d.line(pts, fill=color + (255,), width=width, joint="curve")
    if p >= 0.98:
        ex, ey = pts[-1]
        px, py = pts[-3]
        ang = math.atan2(ey - py, ex - px)
        for da in (2.6, -2.6):
            d.line([(ex, ey), (ex + 38 * math.cos(ang + da), ey + 38 * math.sin(ang + da))], fill=color + (255,), width=width)


def ring(c, x, y, z, t, t0, color=RED):
    crayon_circle(c, x, y, 100 * z, 130 * z, t, t0, 0.4, color, 10)


def tag(key, text, color, size=78, tcol=(255, 255, 255)):
    return asset(key, lambda: Label(text, size, color, tcol, seed=hash(key) % 97, border=9))


def label_under(c, key, text, color, jx, jy, z, t, t0, t1, st, k):
    """big paper tag under a jar with an arrow pointing UP at it (comment 3); side placement if the jar sits low."""
    s = pop(t, t0, t1)
    if s <= 0:
        return
    low = clamp((jy - 620) / 150)  # 0 = jar held up, 1 = jar on the table
    lx = jx + 380 * low
    ly = jy + 300 * (1 - low) - 150 * low
    place(c, tag(key, text, color), lx, ly, st, s, -3 if k % 2 else 3, key=k)
    if s > 0.9:
        if low < 0.5:
            arrow(c, (lx, ly - 70), (jx, jy + 130 * z), t, t0 + 0.15, 0.25, color=(255, 255, 255), width=10, bend=0.08)
        else:
            arrow(c, (lx - 150, ly + 20), (jx + 90 * z, jy - 20), t, t0 + 0.15, 0.25, color=(255, 255, 255), width=10, bend=0.08)


# ---- speaker scenes (t = output time, s = source time)
def sp_jars(frame, t, s, st, camv):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    spots, dim = [], 0.0
    # comment 1: "3 lọ chất rắn mất nhãn" (0 - 2.6 out, freeze in the middle)
    if t < o(1.62):
        J = [jar(n, s, camv) for n in ("i1", "i2", "i3")]
        dim = clamp(t / 0.3) * (1 - clamp((t - o(1.45)) / 0.15))
        spots = [(x, y, 130 * z, 160 * z) for x, y, z in J]
        for i, (x, y, z) in enumerate(J):
            ring(c, x, y, z, t, 0.35 + i * 0.18)
        s_l = pop(t, 1.05, o(1.45))
        place(c, tag("t3lo", "3 lọ chất rắn mất nhãn", RED, 70), 960, 920, st, s_l, -2, key=1)
        if s_l > 0.9:
            arrow(c, (760, 860), (J[0][0] + 40, J[0][1] + 170 * J[0][2]), t, 1.2, 0.3, (255, 255, 255))
            arrow(c, (1160, 860), (J[2][0], J[2][1] + 170 * J[2][2]), t, 1.35, 0.3, (255, 255, 255), bend=-0.18)
    # comment 2: the two white jars "giống nhau?"
    elif o(3.3) <= t < o(6.28):
        A, B = jar("wA", s, camv), jar("wB", s, camv)
        dim = clamp((t - o(3.3)) / 0.3) * (1 - clamp((t - o(6.15)) / 0.12))
        spots = [(x, y, 130 * z, 160 * z) for x, y, z in (A, B)]
        ring(c, *A, t, o(4.2))
        ring(c, *B, t, o(4.45))
        s_l = pop(t, o(5.15), o(6.15))
        place(c, tag("tgiong", "giống nhau?", RED, 80), 1040, 960, st, s_l, 2, key=2)
        if s_l > 0.9:
            arrow(c, (860, 910), (A[0], A[1] + 150 * A[2]), t, o(5.25), 0.25, (255, 255, 255))
            arrow(c, (1220, 910), (B[0], B[1] + 150 * B[2]), t, o(5.35), 0.25, (255, 255, 255), bend=-0.18)
    # comment 3: "muối" / "đường" tags with arrows pointing up at each jar
    elif o(8.5) <= t < o(11.45):
        x, y, z = jar("salt", s, camv)
        label_under(c, "tmuoi", "MUỐI", TEAL, x, y, z, t, o(8.65), o(11.3), st, 3)
        if s >= 10.6:
            x, y, z = jar("sugar", s, camv)
            label_under(c, "tduong", "ĐƯỜNG", CORAL, x, y, z, t, o(10.75), o(11.3), st, 4)
    # comment 3 (bis): white + brown are the same
    elif o(11.45) <= t < o(15.28):
        A, B = jar("sugar", s, camv), jar("brown", s, camv)
        dim = clamp((t - o(11.5)) / 0.3) * (1 - clamp((t - o(15.15)) / 0.12))
        spots = [(x, y, 130 * z, 160 * z) for x, y, z in (A, B)]
        ring(c, *A, t, o(13.1))
        ring(c, *B, t, o(14.2))
        s_l = pop(t, o(14.85), o(15.15))
        place(c, tag("tgiong2", "giống nhau!", RED, 80), 1000, 960, st, s_l, -2, key=5)
        if s_l > 0.9:
            arrow(c, (820, 910), (A[0], A[1] + 150 * A[2]), t, o(14.95), 0.2, (255, 255, 255))
            arrow(c, (1180, 910), (B[0], B[1] + 150 * B[2]), t, o(15.0), 0.2, (255, 255, 255), bend=-0.18)
    elif o(15.28) <= t < o(18.45):
        A, B = jar("sugar", s, camv), jar("brown", s, camv)
        label_under(c, "tdtrang", "ĐƯỜNG TRẮNG", CORAL, *A, t, o(17.45), o(18.3), st, 6)
        label_under(c, "tdnau", "ĐƯỜNG NÂU", (176, 108, 58), *B, t, o(16.7), o(18.3), st, 7)
        s_n = pop(t, o(15.9), o(18.3))
        place(c, tag("tdeula", "đều là ĐƯỜNG", INK, 64), 960, 95, st, s_n, -1.5, key=8)
    frame = dim_spot(frame, spots, dim)
    frame = frame.convert("RGBA")
    frame.alpha_composite(c)
    return frame.convert("RGB")


def sp_brain(frame, t, s, st, camv):
    # comment 5: brain + "rất lười" on the RIGHT, "con người cũng vậy" pops on the LEFT for balance
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ts = s  # timings below are in source time
    t0 = 18.35
    ph = S("tear_patch", (600, 820), lambda d, i, p: d.rectangle([p, p, p + 600, p + 820], fill=(250, 232, 214)), seed=10, border=14)
    cx = 1580
    if ts >= t0:
        p = ease_io(clamp((ts - t0) / 0.4))
        img = ph.get(st)
        hh = int(img.height * p)
        if hh > 2:
            crop = img.crop((0, img.height - hh, img.width, img.height))
            c.alpha_composite(crop, (cx - img.width // 2, 560 + img.height // 2 - hh))
    lazy = ts < 20.3
    b = S("brain_sleep" if lazy else "brain_awake", (560, 430), brain_fn("sleep" if lazy else "smile"), seed=11 if lazy else 12)
    bs = pop(ts, 18.6, None, 0.45)
    bob = 6 * math.sin(ts * 3) if lazy else 0
    place(c, b, cx, 350 + bob, st, 0.82 * bs, 3, key=10)
    if lazy and bs > 0.8:
        for i, zc in enumerate("zzz"):
            if ts > 18.8 + i * 0.25:
                c.alpha_composite(text_c(zc, 50 + i * 12, NAVY), (1760 + i * 30, 150 - i * 45))
    write(c, "Não người", cx, 640, ts, 18.7, 0.4, 76, NAVY, "c")
    write(c, "rất LƯỜI", cx, 725, ts, 19.2, 0.4, 76, RED, "c")
    write(c, "1. nhìn 1 đặc điểm nổi bật", 1310, 815, ts, 20.5, 0.7, 42, NAVY)
    write(c, "2. vội phân loại", 1310, 870, ts, 22.6, 0.5, 42, NAVY)
    write(c, "3. suy diễn bản chất", 1310, 925, ts, 23.4, 0.6, 42, NAVY)
    # left panel
    lx = 340
    sl = pop(ts, 25.35, None, 0.4)
    place(c, S("n_human", (560, 700), note_fn(560, 700), seed=60), lx, 560, st, sl, -3, key=20)
    if sl > 0.9:
        write(c, "Với con người", lx, 330, ts, 25.6, 0.5, 64, NAVY, "c")
        write(c, "cũng làm", lx, 420, ts, 26.7, 0.35, 64, NAVY, "c")
        write(c, "điều tương tự!", lx, 505, ts, 27.3, 0.45, 64, RED, "c")
        for i in range(3):
            place(c, people()[i + 1], lx - 150 + i * 150, 740, st, 0.55 * pop(ts, 26.0 + i * 0.2), (i - 1) * 6, key=21 + i)
    frame = frame.convert("RGBA")
    frame.alpha_composite(c)
    return frame.convert("RGB")


@functools.lru_cache(None)
def scrim(top):
    a = np.zeros((H, W), np.float32)
    ys = np.arange(H, dtype=np.float32)
    if top:
        col = np.clip(1 - ys / 330, 0, 1) ** 1.3 * 0.82
    else:
        col = np.clip((ys - 700) / 380, 0, 1) ** 1.3 * 0.85
    a[:] = col[:, None]
    img = Image.new("RGBA", (W, H), (22, 18, 40, 0))
    img.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
    return img


def sp_question(frame, t, s, st, camv):
    # comment 7: question at top + bottom over dark scrims, nothing on the side
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a = clamp((s - 45.25) / 0.3)
    if a > 0:
        c.alpha_composite(scrim(True))
        c.alpha_composite(scrim(False))
    white = (252, 248, 236)
    write(c, "Theo các bạn...", W // 2, 58, s, 45.4, 0.5, 54, white, "c")
    write(c, "sắc tố da", 560, 150, s, 46.6, 0.4, 84, MUST, "c")
    write(c, "•", 770, 150, s, 47.5, 0.1, 84, white, "c")
    write(c, "màu tóc", 960, 150, s, 47.6, 0.35, 84, MUST, "c")
    write(c, "•", 1150, 150, s, 49.0, 0.1, 84, white, "c")
    write(c, "ngoại hình", 1380, 150, s, 49.1, 0.4, 84, MUST, "c")
    write(c, "... có THẬT hay KHÔNG?", W // 2, 960, s, 49.7, 0.55, 104, white, "c")
    frame = frame.convert("RGBA")
    if a < 1:
        c.putalpha(c.split()[3].point(lambda v: int(v * a)))
    frame.alpha_composite(c)
    return frame.convert("RGB")


# ---- full-screen scenes (fn(t_out, s, st))
def fs_shift(fn, shift):
    return lambda t, s, st: fn(s - shift, st)


def clock_fn(d, img, p):
    d.ellipse([p, p + 40, p + 520, p + 560], fill=CORAL)
    d.ellipse([p + 40, p + 80, p + 480, p + 520], fill=CREAM)
    for i in range(12):
        a = math.radians(i * 30)
        x, y = p + 260 + 190 * math.sin(a), p + 300 - 190 * math.cos(a)
        d.ellipse([x - 8, y - 8, x + 8, y + 8], fill=NAVY)
    for dx in (-150, 150):
        d.ellipse([p + 260 + dx - 70, p - 20, p + 260 + dx + 70, p + 90], fill=MUST)
    d.rectangle([p + 240, p + 10, p + 280, p + 50], fill=DARK)


def sc_countdown(t, s, st):
    # comment 8: full-screen 5s countdown (ticks are added in the audio pass)
    lt = t - CD_T0
    c = background(NAVY, 7, True).copy().convert("RGBA")
    shake = 3 * math.sin(lt * 40) if (lt % 1) < 0.15 else 0
    place(c, S("clock", (520, 560), clock_fn, seed=61, border=10), 960 + shake, 590, st, pop(lt, 0.0, dur=0.4), 0, key=30)
    if lt > 0.25:
        n = max(1, 5 - int(lt))
        ph = lt % 1
        sc = R.ease_out_back(clamp(ph / 0.25))
        num = text_c(str(n), 260, NAVY)
        num = num.resize((max(1, int(num.width * sc)), max(1, int(num.height * sc))), Image.BILINEAR)
        c.alpha_composite(num, (960 - num.width // 2, 610 - num.height // 2))
        # sweeping second hand (sweeps once per second, stop-motion stepped)
        a = math.radians(360 * (st % ANIM) / ANIM)
        d = ImageDraw.Draw(c)
        d.line([(960, 610), (960 + 150 * math.sin(a), 610 - 150 * math.cos(a))], fill=RED + (255,), width=8)
        d.ellipse([948, 598, 972, 622], fill=RED)
    write(c, "Bạn nghĩ sao?", 960, 150, lt, 0.2, 0.5, 96, (252, 248, 236), "c")
    return c


def sc_scope(t, s, st):
    # comment 6: "Trong phạm vi video hôm nay" alone full-screen first, then the concept cards
    c = background(PINK, 3).copy().convert("RGBA")
    shrink = ease_io(clamp((s - 39.2) / 0.45))
    if s < 39.2:
        write(c, "Trong phạm vi", 960, 430, s, 37.0, 0.55, 150, INK, "c")
        write(c, "video hôm nay", 960, 620, s, 37.8, 0.6, 150, RED, "c")
    else:
        n = S("n_scope", (900, 140), note_fn(900, 140, lined=False), seed=27)
        place(c, n, 960, 130, st, 0.4 + 0.6 * shrink, 1.5, key=50)
        if shrink > 0.95:
            c.alpha_composite(text_c("Trong phạm vi video hôm nay", 70, INK), (960 - text_c("Trong phạm vi video hôm nay", 70, INK).width // 2, 95))
    icons = {"race": (S("sw_skin", (5 * 84 + 4 * 22, 84), R.swatches_fn(SKINS), seed=28, border=6), 0.62),
             "eth": (S("lantern", (180, 240), R.lantern_fn, seed=29, border=6), 0.8),
             "nat": (S("passport", (160, 220), R.passport_fn, seed=30, border=6), 0.9),
             "ind": (S("land", (240, 210), R.land_fn, seed=31, border=6), 0.85)}
    flips = [None, 42.05, 43.35, 44.45]
    for i, (title, sub, _, kind) in enumerate(R.CARDS):
        x, y = 300 + i * 440, 600
        sc_ = pop(s, 39.4 + i * 0.2)
        fp = clamp((s - flips[i]) / 0.3) if i else 1.0
        sx = abs(1 - 2 * fp) if i else 1.0
        rot = [-3, 2, -2, 3][i]
        if fp < 0.5:
            place(c, S("card_back", (380, 470), R.back_fn, seed=32), x, y, st, sc_, rot, key=51 + i, sx=max(sx, 0.02))
        else:
            place(c, S(f"card{i}", (380, 470), R.card_fn(title, sub, kind), seed=33 + i), x, y, st, sc_, rot, key=51 + i, sx=max(sx, 0.02))
            ic, k = icons[kind]
            place(c, ic, x, y - 90, st, sc_ * k, rot, key=60 + i, sx=max(sx, 0.02))
    return c


CUT = sorted(glob.glob("v2/cut/*.png"))
CUT_T0 = 67.3


@functools.lru_cache(maxsize=4)
def cut_sprite(k):
    """person cut-out with our white torn-paper outline + shadow (comment 9)."""
    im = Image.open(CUT[k]).convert("RGBA")
    bb = im.split()[3].getbbox()
    im = im.crop((bb[0] - 40, bb[1] - 40, bb[2] + 40, bb[3]))
    sc = 0.85
    im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
    pad = 40
    big = Image.new("RGBA", (im.width + 2 * pad, im.height + pad), (0, 0, 0, 0))
    big.alpha_composite(im, (pad, pad))
    alpha = big.split()[3].point(lambda v: 255 if v > 100 else 0)
    bm = torn_mask(alpha, 13, k % 3)
    # keep the bottom edge straight (the body continues off-frame)
    out = Image.new("RGBA", big.size, (0, 0, 0, 0))
    sh = Image.new("RGBA", big.size, (30, 20, 40, 0))
    sh.putalpha(bm.point(lambda v: int(v * 0.35)).filter(ImageFilter.GaussianBlur(6)))
    out.alpha_composite(sh, (8, 10))
    pp = Image.new("RGBA", big.size, (252, 250, 242, 255))
    pp.putalpha(bm)
    out.alpha_composite(texturize(pp, 3, 0.05))
    out.alpha_composite(big)
    return out


def sc_term(t, s, st):
    c = background(MUST, 9).copy().convert("RGBA")
    k = int(clamp((s - CUT_T0) * ANIM, 0, len(CUT) - 1))
    sp = cut_sprite(k)
    # smaller and lower than the original framing
    c.alpha_composite(sp, (960 - sp.width // 2, H - sp.height + 20))
    write(c, "thuật ngữ", 960, 62, s, 68.9, 0.45, 70, NAVY, "c")
    place(c, asset("race_term", lambda: Label("RACE", 190, RED, seed=62, border=12)), 960, 215, st, pop(s, 69.7, dur=0.35), -3, key=70)
    return c


# ---- timeline in OUTPUT time: (start, end, kind, fn)
TL = [
    (0.0, o(18.4), "sp", sp_jars),
    (o(18.4), o(28.2), "sp", sp_brain),
    (o(28.2), o(33.8), "fs", fs_shift(R.sc_race, -0.7)),
    (o(33.8), o(37.0), "fs", fs_shift(R.sc_topic, -0.6)),
    (o(37.0), o(45.25), "fs", sc_scope),
    (o(45.25), CD_T0, "sp", sp_question),
    (CD_T0, CD_T1, "fs", sc_countdown),
    (CD_T1, o(58.4), "fs", fs_shift(R.sc_real, -2.2)),
    (o(58.4), o(67.6), "fs", fs_shift(R.sc_society, -2.1)),
    (o(67.6), 999, "fs", sc_term),
]
WIPE = 0.45


def seg_at(t):
    for i, sg in enumerate(TL):
        if sg[0] <= t < sg[1]:
            return i
    return len(TL) - 1


class Source:
    def __init__(self):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", R.FIT, "-f", "rawvideo", "-pix_fmt", "rgb24", "-r", "30", "-"],
                                  stdout=subprocess.PIPE)
        self.idx, self.img = -1, None

    def get(self, s):
        f = int(round(s * FPS))
        while self.idx < f:
            raw = self.p.stdout.read(W * H * 3)
            if len(raw) < W * H * 3:
                break
            self.idx += 1
            self.img = raw
        return Image.frombytes("RGB", (W, H), self.img)


_fs_cache = {}


def render_seg(i, t, st, src):
    a, b, kind, fn = TL[i]
    s = src_of(t)
    if kind == "fs":
        key = (i, st)
        if key not in _fs_cache:
            if len(_fs_cache) > 4:
                _fs_cache.clear()
            ss = s if s is not None else CD_S1
            _fs_cache[key] = fn(t, ss, st).convert("RGB")
        return _fs_cache[key]
    ss = s if s is not None else CD_S0
    frame, camv = apply_cam(src.get(ss), ss)
    return fn(frame, t, ss, st, camv)


def main():
    src = Source()
    pout = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                             "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "v2/video.mp4"],
                            stdin=subprocess.PIPE)
    nfr = int(T_END * FPS)
    for n in range(nfr):
        t = n / FPS
        st = int(t * ANIM)
        ta = st / ANIM
        s = src_of(t)
        if s is not None:
            src.get(s)  # keep the decoder in step
        i = seg_at(t)
        frame = None
        for j in range(1, len(TL)):
            tb = TL[j][0]
            if tb - WIPE / 2 <= t < tb + WIPE / 2 and not (TL[j - 1][2] == "sp" and TL[j][2] == "sp"):
                p = ease_io((t - (tb - WIPE / 2)) / WIPE)
                fa = render_seg(j - 1, t, st, src).copy()
                fb = render_seg(j, t, st, src)
                frame = R.torn_wipe(fa, fb, p, j)
                break
        if frame is None:
            frame = render_seg(i, t, st, src)
        pout.stdin.write(frame.tobytes())
        if n % 90 == 0:
            print(f"t={t:.1f}/{T_END:.1f}", flush=True)
    pout.stdin.close()
    pout.wait()


if __name__ == "__main__":
    main()
