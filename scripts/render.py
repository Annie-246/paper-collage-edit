# Paper cut-out collage edit library (torn-paper / crayon / stop-motion style)
import math, random, subprocess, sys, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

SRC = "input.mp4"  # path to the source video
OUT = sys.argv[1] if len(sys.argv) > 1 else "out.mp4"
T_START = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
T_END = float(sys.argv[3]) if len(sys.argv) > 3 else 72.9
import os

# Output canvas: PAPER_ASPECT=16:9 (default, 1920x1080) or 9:16 (1080x1920). Must be set before importing render.
ASPECT = os.environ.get("PAPER_ASPECT", "16:9")
W, H = (1080, 1920) if ASPECT == "9:16" else (1920, 1080)
FPS, ANIM = 30, 12
VERTICAL = H > W
CX, CY = W // 2, H // 2
# content-safe box (x0, y0, x1, y1): 9:16 keeps clear of TikTok/Reels/Shorts UI (top bar, caption + buttons)
SAFE = (60, 220, W - 160, H - 480) if VERTICAL else (80, 60, W - 80, H - 60)
# ffmpeg filter that fits any source to the canvas (cover + center crop), e.g. a 16:9 source into 9:16
FIT = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"

NAVY = (40, 44, 110); MUST = (243, 194, 66); PINK = (240, 166, 186); CORAL = (232, 118, 88)
TEAL = (44, 150, 134); CREAM = (247, 242, 228); INK = (46, 72, 168); RED = (206, 64, 56)
WOOD = (214, 168, 108); PURPLE = (108, 76, 142); GREEN = (96, 170, 90); DARK = (52, 40, 40)
SKINS = [(255, 226, 198), (236, 194, 152), (200, 142, 100), (146, 98, 64), (96, 62, 42)]
HAIRS = [(230, 186, 90), (40, 30, 30), (120, 72, 40), (188, 86, 48), (28, 22, 22)]
SHIRTS = [TEAL, CORAL, INK, (230, 120, 160), GREEN]
FONT_A = "fonts/Pangolin-Regular.ttf"
FONT_B = "fonts/PatrickHand-Regular.ttf"


@functools.lru_cache(None)
def font(size, f=FONT_A):
    return ImageFont.truetype(f, size)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out_back(p):
    c1 = 1.9; c3 = c1 + 1
    return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2


def ease_io(p):
    return p * p * (3 - 2 * p)


# ---------- textures ----------
@functools.lru_cache(None)
def grain(w, h, seed=0, amp=0.10):
    r = np.random.default_rng(seed)
    n = r.normal(0, 1, (h // 2 + 1, w // 2 + 1)).astype(np.float32)
    n = np.array(Image.fromarray(n).resize((w, h), Image.BILINEAR))
    streak = r.normal(0, 1, (h // 3 + 1, 8)).astype(np.float32)
    streak = np.array(Image.fromarray(streak).resize((w, h), Image.BILINEAR))
    return 1 + amp * (0.6 * n + 0.4 * streak) / 1.5


def texturize(img, seed=0, amp=0.10):
    a = np.asarray(img).astype(np.float32)
    g = grain(img.width, img.height, seed % 5, amp)
    a[..., :3] = np.clip(a[..., :3] * g[..., None], 0, 255)
    return Image.fromarray(a.astype(np.uint8), img.mode)


@functools.lru_cache(None)
def background(color, seed=0, stars=False):
    img = Image.new("RGB", (W, H), color)
    d = ImageDraw.Draw(img)
    r = random.Random(seed)
    # faint crayon strokes like the reference's coloured-paper backgrounds
    for _ in range(90):
        x, y = r.randint(-100, W), r.randint(0, H)
        k = r.uniform(0.94, 1.06)
        c = tuple(int(clamp(v * k, 0, 255)) for v in color)
        d.line([(x, y), (x + r.randint(80, 260), y + r.randint(-20, 20))], fill=c, width=r.randint(6, 16))
    img = img.filter(ImageFilter.GaussianBlur(2))
    if stars:
        d = ImageDraw.Draw(img)
        for _ in range(60):
            x, y, s = r.randint(0, W), r.randint(0, H), r.randint(3, 7)
            d.polygon(star_pts(x, y, s * 1.6, s * 0.6), fill=(250, 226, 130))
    return texturize(img, seed, 0.07)


def star_pts(x, y, ro, ri, n=5, rot=-90):
    pts = []
    for i in range(n * 2):
        rr = ro if i % 2 == 0 else ri
        a = math.radians(rot + i * 180 / n)
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    return pts


# ---------- torn paper sprites ----------
def torn_mask(alpha, border, seed):
    """Dilate alpha and roughen the edge -> white torn-paper border mask."""
    m = alpha.filter(ImageFilter.MaxFilter(border * 2 + 1)) if border else alpha
    m = m.filter(ImageFilter.GaussianBlur(border * 0.6 + 1))
    r = np.random.default_rng(seed)
    w, h = m.size
    n = r.normal(0, 1, (h // 6 + 1, w // 6 + 1)).astype(np.float32)
    n = np.array(Image.fromarray(n).resize((w, h), Image.BILINEAR))
    fine = r.normal(0, 1, (h // 2 + 1, w // 2 + 1)).astype(np.float32)
    fine = np.array(Image.fromarray(fine).resize((w, h), Image.BILINEAR))
    a = np.asarray(m).astype(np.float32) + 38 * n + 18 * fine
    return Image.fromarray(((a > 128) * 255).astype(np.uint8))


def build_sprite(size, draw_fn, seed=0, border=9, paper=(252, 250, 242), shadow=True):
    pad = border * 3 + 14
    w, h = size[0] + 2 * pad, size[1] + 2 * pad
    base = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(base), base, pad)
    base = texturize(base, seed + 11, 0.09)
    alpha = base.split()[3]
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if border:
        bm = torn_mask(alpha, border, seed)
        if shadow:
            sh = Image.new("RGBA", (w, h), (30, 20, 40, 0))
            sh.putalpha(bm.point(lambda v: v * 0.32).filter(ImageFilter.GaussianBlur(5)))
            out.alpha_composite(sh, (5, 8))
        pp = Image.new("RGBA", (w, h), paper + (255,))
        pp.putalpha(bm)
        out.alpha_composite(texturize(pp, seed + 3, 0.05))
    out.alpha_composite(base)
    return out


class Sprite:
    """3 boil variants (different torn edges) cycled at stop-motion rate."""
    def __init__(self, size, draw_fn, border=9, paper=(252, 250, 242), shadow=True, seed=0):
        self.v = [build_sprite(size, draw_fn, seed * 7 + i, border, paper, shadow) for i in range(3)]

    def get(self, step):
        return self.v[step % 3]


def place(canvas, sprite, cx, cy, step, scale=1.0, rot=0.0, jitter=True, key=0, alpha=1.0, sx=1.0):
    if scale <= 0.01 or alpha <= 0.01 or sx <= 0.01:
        return
    img = sprite.get(step + key) if isinstance(sprite, Sprite) else sprite
    r = random.Random(step * 131 + key * 17)
    if jitter:
        rot += r.uniform(-0.9, 0.9)
        cx += r.uniform(-2, 2); cy += r.uniform(-2, 2)
    if scale != 1.0 or sx != 1.0:
        img = img.resize((max(1, int(img.width * scale * sx)), max(1, int(img.height * scale))), Image.BILINEAR)
    if abs(rot) > 0.05:
        img = img.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < 1:
        a = img.split()[3].point(lambda v: int(v * alpha))
        img = img.copy(); img.putalpha(a)
    canvas.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))


def pop(t, t0, t1=None, dur=0.35):
    """Scale for pop-in with overshoot, and quick shrink-out at t1."""
    if t < t0:
        return 0.0
    s = ease_out_back(clamp((t - t0) / dur))
    if t1 is not None and t > t1:
        s *= 1 - ease_io(clamp((t - t1) / 0.22))
    return s


# ---------- drawing parts ----------
def rrect(d, box, r, fill, outline=None, width=0):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


def draw_face(d, cx, cy, s=1.0, mood="smile"):
    e = 7 * s
    if mood == "sleep":
        for dx in (-22, 22):
            d.arc([cx + dx * s - 12 * s, cy - 8 * s, cx + dx * s + 12 * s, cy + 8 * s], 10, 170, fill=DARK, width=int(4 * s))
    else:
        for dx in (-22, 22):
            d.ellipse([cx + dx * s - e, cy - e, cx + dx * s + e, cy + e], fill=DARK)
    d.ellipse([cx - 44 * s, cy + 10 * s, cx - 26 * s, cy + 24 * s], fill=(242, 140, 150))
    d.ellipse([cx + 26 * s, cy + 10 * s, cx + 44 * s, cy + 24 * s], fill=(242, 140, 150))
    if mood == "sleep":
        d.ellipse([cx - 6 * s, cy + 18 * s, cx + 6 * s, cy + 28 * s], fill=DARK)
    else:
        d.arc([cx - 16 * s, cy + 4 * s, cx + 16 * s, cy + 28 * s], 20, 160, fill=DARK, width=int(4 * s))


def person_fn(skin, hair, shirt, style=0):
    def fn(d, img, p):
        cx = p + 100
        rrect(d, [p + 20, p + 190, p + 180, p + 330], 50, shirt)
        d.rectangle([cx - 18, p + 160, cx + 18, p + 200], fill=skin)
        if style == 1:  # long hair behind
            rrect(d, [cx - 78, p + 40, cx + 78, p + 230], 60, hair)
        d.ellipse([cx - 68, p + 40, cx + 68, p + 180], fill=skin)
        if style == 2:  # curly
            for i in range(9):
                a = math.radians(180 + i * 22.5)
                x, y = cx + 64 * math.cos(a), p + 108 + 64 * math.sin(a)
                d.ellipse([x - 26, y - 26, x + 26, y + 26], fill=hair)
        else:
            d.pieslice([cx - 72, p + 30, cx + 72, p + 170], 180, 360, fill=hair)
            d.polygon([(cx - 72, p + 100), (cx - 20, p + 60), (cx - 66, p + 130)], fill=hair)
        draw_face(d, cx, p + 118, 1.0)
    return fn


PEOPLE = None


def people():
    global PEOPLE
    if PEOPLE is None:
        styles = [1, 0, 2, 0, 1]
        PEOPLE = [Sprite((200, 340), person_fn(SKINS[i], HAIRS[i], SHIRTS[i], styles[i]), seed=40 + i) for i in range(5)]
    return PEOPLE


def jar_fn(content):
    def fn(d, img, p):
        rrect(d, [p + 20, p, p + 140, p + 40], 10, RED)
        for i in range(6):
            d.line([(p + 34 + i * 18, p + 6), (p + 34 + i * 18, p + 34)], fill=(170, 40, 40), width=3)
        rrect(d, [p, p + 40, p + 160, p + 230], 26, (236, 240, 244))
        rrect(d, [p + 10, p + 100, p + 150, p + 220], 20, content)
        r = random.Random(3)
        for _ in range(70):
            x, y = r.randint(p + 18, p + 142), r.randint(p + 106, p + 212)
            c = tuple(int(v * r.uniform(0.85, 1.05)) for v in content)
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=c)
        d.line([(p + 22, p + 60), (p + 22, p + 90)], fill=(255, 255, 255), width=8)
    return fn


def note_fn(w, h, color=CREAM, lined=True, spiral=False):
    def fn(d, img, p):
        d.rectangle([p, p, p + w, p + h], fill=color)
        if lined:
            for y in range(p + 70, p + h - 10, 44):
                d.line([(p + 10, y), (p + w - 10, y)], fill=(170, 190, 230), width=2)
            d.line([(p + 60, p + 10), (p + 60, p + h - 10)], fill=(236, 150, 150), width=2)
        if spiral:
            for x in range(p + 40, p + w - 20, 48):
                d.ellipse([x, p + 14, x + 18, p + 32], fill=(90, 80, 110))
                d.arc([x - 4, p - 18, x + 22, p + 26], 180, 360, fill=(150, 150, 160), width=5)
    return fn


def text_img(text, size, color=INK, f=FONT_A, stroke=0):
    fnt = font(size, f)
    bb = fnt.getbbox(text, stroke_width=stroke)
    img = Image.new("RGBA", (bb[2] - bb[0] + 20, bb[3] - bb[1] + 30), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((10 - bb[0], 12 - bb[1]), text, font=fnt, fill=color + (255,),
                             stroke_width=stroke, stroke_fill=color + (255,))
    return texturize(img, 5, 0.12)


@functools.lru_cache(None)
def text_c(text, size, color=INK, f=FONT_A):
    return text_img(text, size, color, f)


def write(canvas, text, x, y, t, t0, dur=None, size=56, color=INK, anchor="l", f=FONT_A, t1=None):
    """Handwriting-style reveal: left-to-right wipe, like the reference's pen writing."""
    if t < t0:
        return
    img = text_c(text, size, color, f)
    dur = dur or max(0.25, 0.045 * len(text))
    p = clamp((t - t0) / dur)
    if t1 is not None and t > t1:
        a = 1 - clamp((t - t1) / 0.2)
        if a <= 0:
            return
        img = img.copy(); img.putalpha(img.split()[3].point(lambda v: int(v * a)))
    cw = max(1, int(img.width * p))
    crop = img.crop((0, 0, cw, img.height))
    ox = x if anchor == "l" else x - img.width // 2
    canvas.alpha_composite(crop, (int(ox), int(y - img.height / 2)))


def crayon_circle(canvas, cx, cy, rx, ry, t, t0, dur=0.45, color=RED, width=9):
    if t < t0:
        return
    p = clamp((t - t0) / dur)
    d = ImageDraw.Draw(canvas)
    pts = []
    n = int(60 * p * 1.15) + 2
    for i in range(n):
        a = math.radians(-100 + i * 6.3)
        wob = 1 + 0.04 * math.sin(i * 0.7) + 0.05 * (i / 60)
        pts.append((cx + rx * wob * math.cos(a), cy + ry * wob * math.sin(a)))
    d.line(pts, fill=color + (235,), width=width, joint="curve")


def label_fn(text, size, color=CORAL, tcol=(255, 255, 255)):
    fnt = font(size)
    bb = fnt.getbbox(text)
    w, h = bb[2] - bb[0] + 50, bb[3] - bb[1] + 36

    def fn(d, img, p):
        d.rectangle([p, p, p + w, p + h], fill=color)
        d.text((p + 25 - bb[0], p + 18 - bb[1]), text, font=fnt, fill=tcol)
    return (w, h), fn


def Label(text, size, color=CORAL, tcol=(255, 255, 255), seed=0, border=7):
    sz, fn = label_fn(text, size, color, tcol)
    return Sprite(sz, fn, border=border, seed=seed)


def brain_fn(mood):
    def fn(d, img, p):
        pinkc = (241, 150, 172)
        lobes = [(150, 150, 120), (260, 110, 110), (370, 130, 110), (440, 220, 95), (360, 260, 120),
                 (220, 270, 120), (120, 240, 100), (280, 190, 130)]
        for x, y, r in lobes:
            d.ellipse([p + x - r, p + y - r, p + x + r, p + y + r], fill=pinkc)
        d.polygon([(p + 300, p + 330), (p + 360, p + 330), (p + 350, p + 420), (p + 310, p + 420)], fill=(230, 130, 150))
        fold = (204, 96, 124)
        r = random.Random(9)
        for _ in range(14):
            x, y = p + r.randint(90, 440), p + r.randint(70, 330)
            a0 = r.randint(0, 360)
            d.arc([x - 40, y - 26, x + 40, y + 26], a0, a0 + 150, fill=fold, width=7)
        d.line([(p + 270, p + 40), (p + 280, p + 160), (p + 262, p + 260)], fill=fold, width=7)
        cx, cy = p + 270, p + 225
        rrect(d, [cx - 70, cy - 36, cx + 70, cy + 44], 30, (246, 176, 192))
        draw_face(d, cx, cy, 1.2, mood)
    return fn


def lantern_fn(d, img, p):
    d.line([(p + 90, p), (p + 90, p + 30)], fill=DARK, width=5)
    rrect(d, [p + 50, p + 24, p + 130, p + 44], 6, (230, 180, 60))
    d.ellipse([p + 10, p + 36, p + 170, p + 176], fill=RED)
    for x in (50, 90, 130):
        d.arc([p + x - 40, p + 36, p + x + 40, p + 176], 270, 90, fill=(170, 40, 40), width=4)
    rrect(d, [p + 50, p + 168, p + 130, p + 188], 6, (230, 180, 60))
    for i in range(5):
        d.line([(p + 70 + i * 10, p + 188), (p + 70 + i * 10, p + 236)], fill=(230, 180, 60), width=4)


def passport_fn(d, img, p):
    rrect(d, [p, p, p + 160, p + 220], 14, NAVY)
    d.ellipse([p + 40, p + 50, p + 120, p + 130], outline=(236, 196, 90), width=6)
    d.line([(p + 80, p + 50), (p + 80, p + 130)], fill=(236, 196, 90), width=4)
    d.line([(p + 40, p + 90), (p + 120, p + 90)], fill=(236, 196, 90), width=4)
    fnt = font(26)
    d.text((p + 22, p + 160), "PASSPORT", font=fnt, fill=(236, 196, 90))


def land_fn(d, img, p):
    d.pieslice([p, p + 90, p + 240, p + 330], 180, 360, fill=GREEN)
    d.rectangle([p + 150, p + 110, p + 164, p + 180], fill=(120, 80, 50))
    d.ellipse([p + 118, p + 40, p + 196, p + 130], fill=(60, 140, 70))
    d.polygon([(p + 50, p + 150), (p + 90, p + 104), (p + 130, p + 150)], fill=(190, 110, 60))
    d.rectangle([p + 60, p + 150, p + 120, p + 200], fill=(236, 200, 140))
    d.rectangle([p + 82, p + 170, p + 98, p + 200], fill=(120, 80, 50))


def swatches_fn(cols, r=42, gap=22):
    def fn(d, img, p):
        for i, c in enumerate(cols):
            x = p + r + i * (2 * r + gap)
            d.ellipse([x - r, p, x + r, p + 2 * r], fill=c)
    return fn


def hair_fn(cols):
    def fn(d, img, p):
        for i, c in enumerate(cols):
            x = p + i * 104
            pts = []
            for k in range(20):
                y = k * 9
                pts.append((x + 40 + 14 * math.sin(k * 0.8), p + y))
            d.line(pts, fill=c, width=46, joint="curve")
    return fn


def dna_fn(d, img, p):
    for k in range(0, 360, 4):
        y = p + k
        x1 = p + 70 + 60 * math.sin(math.radians(k * 2))
        x2 = p + 70 - 60 * math.sin(math.radians(k * 2))
        d.ellipse([x1 - 9, y - 9, x1 + 9, y + 9], fill=CORAL)
        d.ellipse([x2 - 9, y - 9, x2 + 9, y + 9], fill=TEAL)
        if k % 24 == 0:
            d.line([(x1, y), (x2, y)], fill=(240, 220, 150), width=5)


def box_fn(color, text):
    def fn(d, img, p):
        rrect(d, [p, p, p + 280, p + 170], 12, color)
        d.line([(p + 10, p + 30), (p + 270, p + 30)], fill=tuple(int(v * 0.8) for v in color), width=6)
        fnt = font(52)
        bb = fnt.getbbox(text)
        d.text((p + 140 - (bb[2] - bb[0]) / 2 - bb[0], p + 70), text, font=fnt, fill=(255, 255, 255))
    return fn


def qmark_fn(d, img, p):
    d.text((p, p - 30), "?", font=font(300), fill=CORAL)


def hand_check_fn(d, img, p):
    d.line([(p + 10, p + 70), (p + 60, p + 120), (p + 160, p + 10)], fill=GREEN, width=30, joint="curve")


def stairs_fn(d, img, p):
    for i in range(3):
        d.rectangle([p + i * 330, p + 300 - i * 150, p + i * 330 + 330, p + 450], fill=(214, 168, 108))
        d.line([(p + i * 330, p + 300 - i * 150), (p + i * 330 + 330, p + 300 - i * 150)], fill=(170, 120, 70), width=8)


# ---------- asset registry ----------
A = {}


def asset(key, make):
    if key not in A:
        A[key] = make()
    return A[key]


def S(key, size, fn, **kw):
    return asset(key, lambda: Sprite(size, fn, **kw))


# ---------- scenes ----------
# Speaker-overlay scenes draw onto a transparent layer; full scenes draw complete frames.
def ov_intro(c, t, st):
    # 0 - 6.3 : "3 lọ chất rắn mất nhãn" / "2 lọ trắng giống nhau?"
    n1 = S("n_intro", (560, 260), note_fn(560, 260), seed=1)
    s = pop(t, 0.15, 6.1)
    place(c, n1, 360, 300, st, s, -4, key=1)
    if s > 0.9:
        write(c, "3 lọ chất rắn", 150, 250, t, 0.3, 0.5, 64, t1=1.9)
        write(c, "mất nhãn", 150, 330, t, 0.9, 0.4, 64, RED, t1=1.9)
        write(c, "2 lọ trắng...", 150, 250, t, 2.1, 0.6, 64)
        write(c, "giống nhau?", 150, 330, t, 5.0, 0.5, 64, RED)
    place(c, S("q_small", (180, 280), qmark_fn, seed=2), 560, 560, st, 0.45 * pop(t, 5.6, 6.1), 12, key=2)


def ov_jars(c, t, st):
    # 6.4 - 18.4 : notebook panel with the three jars and their real identity
    t_out = 18.2
    s = pop(t, 6.4, t_out)
    place(c, S("n_jars", (560, 760), note_fn(560, 760, lined=False, spiral=True), seed=3), 1620, 540, st, s, 2, key=3)
    if s < 0.9:
        return
    jw = S("jar_w", (160, 230), jar_fn((248, 248, 250)), seed=4)
    jb = S("jar_b", (160, 230), jar_fn((196, 126, 64)), seed=5)
    xs = [1460, 1620, 1780]
    write(c, "Thực tế...", 1400, 240, t, 6.5, 0.4, 54)
    place(c, jw, xs[0], 480, st, 0.8 * pop(t, 7.8, t_out), key=4)
    place(c, jw, xs[1], 480, st, 0.8 * pop(t, 9.6, t_out), key=5)
    place(c, jb, xs[2], 480, st, 0.8 * pop(t, 14.1, t_out), key=6)
    place(c, asset("l_muoi", lambda: Label("MUỐI", 40, TEAL, seed=6)), xs[0], 650, st, pop(t, 8.8, t_out), -6, key=7)
    place(c, asset("l_duong", lambda: Label("ĐƯỜNG", 38, CORAL, seed=7)), xs[1], 650, st, pop(t, 10.9, t_out), 5, key=8)
    place(c, asset("l_duong2", lambda: Label("ĐƯỜNG", 38, CORAL, seed=8)), xs[2], 650, st, pop(t, 16.3, t_out), -4, key=9)
    crayon_circle(c, 1700, 560, 185, 175, t, 14.9)
    write(c, "giống nhau!", 1620, 800, t, 15.0, 0.5, 58, RED, anchor="c")


def ov_brain(c, t, st):
    # 18.6 - 28.6 : paper tears open on the left, a lazy paper brain pops out
    t0, t_out = 18.5, 28.9
    ph = S("tear_patch", (600, 820), lambda d, i, p: d.rectangle([p, p, p + 600, p + 820], fill=(250, 232, 214)), seed=10, border=14)
    # tear reveal: the patch rises from the bottom with a ragged top edge
    if t >= t0:
        p = ease_io(clamp((t - t0) / 0.4))
        img = ph.get(st)
        hh = int(img.height * p)
        if hh > 2:
            crop = img.crop((0, img.height - hh, img.width, img.height))
            c.alpha_composite(crop, (360 - img.width // 2, 560 + img.height // 2 - hh))
    lazy = t < 20.4
    b = S("brain_sleep" if lazy else "brain_awake", (560, 430), brain_fn("sleep" if lazy else "smile"), seed=11 if lazy else 12)
    bs = pop(t, 18.8, t_out, 0.45)
    bob = 6 * math.sin(t * 3) if lazy else 0
    place(c, b, 360, 360 + bob, st, 0.82 * bs, -3, key=10)
    if lazy and bs > 0.8:
        for i, z in enumerate("zzz"):
            if t > 19.0 + i * 0.25:
                c.alpha_composite(text_c(z, 50 + i * 12, NAVY), (560 + i * 36, 170 - i * 45))
    write(c, "Não người", 110, 640, t, 19.0, 0.4, 70, NAVY, t1=25.3)
    write(c, "rất LƯỜI", 150, 720, t, 19.4, 0.4, 70, RED, t1=25.3)
    # the lazy shortcut, as a scribbled list
    if t < 25.3:
        write(c, "1. nhìn 1 đặc điểm nổi bật", 90, 810, t, 20.6, 0.7, 42, NAVY)
        write(c, "2. vội phân loại", 90, 865, t, 22.7, 0.5, 42, NAVY)
        write(c, "3. suy diễn bản chất", 90, 920, t, 23.5, 0.6, 42, NAVY)
    else:
        write(c, "Con người", 150, 660, t, 25.8, 0.4, 70, NAVY)
        write(c, "cũng vậy...", 150, 740, t, 26.3, 0.4, 70, RED)
        for i in range(3):
            place(c, people()[i + 1], 170 + i * 150, 900, st, 0.42 * pop(t, 26.8 + i * 0.2), (i - 1) * 6, key=11 + i)


def sc_race(t, st):
    # 28.6 - 34.4 : people differ outside -> society sorts them -> RACE
    c = background(MUST, 1).copy().convert("RGBA")
    ps = people()
    boxes = [(560, 860, TEAL), (960, 860, CORAL), (1360, 860, INK)]
    move = ease_io(clamp((t - 30.9) / 0.9))
    home = [(560 + (i - 2) * 220 + 400, 540) for i in range(5)]
    dest = [(boxes[g][0] + off, 760) for g, off in [(0, -50), (0, 50), (1, 0), (2, -50), (2, 50)]]
    for i, p in enumerate(ps):
        x = home[i][0] + (dest[i][0] - home[i][0]) * move
        y = home[i][1] + (dest[i][1] - home[i][1]) * move - 60 * math.sin(math.pi * move)
        place(c, p, x, y, st, (0.9 - 0.25 * move) * pop(t, 28.8 + i * 0.22), (i - 2) * 3, key=20 + i)
    for i, (bx, by, col) in enumerate(boxes):
        place(c, S(f"box{i}", (280, 170), box_fn(col, "ABC"[i]), seed=21 + i), bx, by, st, pop(t, 30.7 + i * 0.12), key=30 + i)
    n = S("n_race_head", (820, 150), note_fn(820, 150, lined=False), seed=24)
    place(c, n, 960, 140, st, pop(t, 29.3, 32.0), -2, key=35)
    if t < 32.0:
        write(c, "Khác biệt bên ngoài", 960, 140, t, 29.5, 0.6, 72, INK, "c")
    place(c, asset("race_big", lambda: Label("RACE", 110, RED, seed=25, border=10)), 760, 150, st, pop(t, 32.0, dur=0.3), -5, key=36)
    write(c, "= cách phân loại con người", 1000, 170, t, 32.7, 0.8, 58, NAVY)
    return c


def sc_topic(t, st):
    # 34.4 - 37.8 : notebook, "Chủ đề hôm nay: RACE" written by hand
    c = background(WOOD, 2).copy().convert("RGBA")
    place(c, S("nb_topic", (1180, 760), note_fn(1180, 760, spiral=True), seed=26), 960, 560, st, 1.0, -1.5, key=40)
    write(c, "Chủ đề hôm nay:", 520, 360, t, 34.9, 0.9, 78, INK)
    write(c, "RACE", 960, 620, t, 35.9, 0.8, 230, INK, "c")
    crayon_circle(c, 960, 625, 330, 150, t, 36.8, 0.5)
    return c


CARDS = [("Race", "chủng tộc", 38.5, "race"), ("Ethnicity", "tộc người", 43.5, "eth"),
         ("Nationality", "quốc tịch", 44.9, "nat"), ("Indigeneity", "tính bản địa", 45.9, "ind")]


def card_fn(title, sub, kind):
    def fn(d, img, p):
        d.rectangle([p, p, p + 380, p + 470], fill=CREAM)
        fnt, fs = font(62), font(40)
        bb = fnt.getbbox(title)
        d.text((p + 190 - (bb[2] - bb[0]) / 2 - bb[0], p + 320), title, font=fnt, fill=INK)
        bb = fs.getbbox(sub)
        d.text((p + 190 - (bb[2] - bb[0]) / 2 - bb[0], p + 400), sub, font=fs, fill=CORAL)
    return fn


def back_fn(d, img, p):
    d.rectangle([p, p, p + 380, p + 470], fill=NAVY)
    d.text((p + 130, p + 90), "?", font=font(240), fill=MUST)


def sc_concepts(t, st):
    # 37.8 - 47.2 : four concept cards, flipped over as each term is spoken
    c = background(PINK, 3).copy().convert("RGBA")
    n = S("n_scope", (900, 140), note_fn(900, 140, lined=False), seed=27)
    place(c, n, 960, 130, st, pop(t, 37.9), 1.5, key=50)
    write(c, "Trong video hôm nay", 960, 130, t, 38.1, 0.7, 76, INK, "c")
    icons = {"race": (S("sw_skin", (5 * 84 + 4 * 22, 84), swatches_fn(SKINS), seed=28, border=6), 0.62),
             "eth": (S("lantern", (180, 240), lantern_fn, seed=29, border=6), 0.8),
             "nat": (S("passport", (160, 220), passport_fn, seed=30, border=6), 0.9),
             "ind": (S("land", (240, 210), land_fn, seed=31, border=6), 0.85)}
    for i, (title, sub, tf, kind) in enumerate(CARDS):
        x, y = 300 + i * 440, 600
        appear = 38.5 if i == 0 else 40.7 + i * 0.2
        s = pop(t, appear)
        # flip: squash horizontally, swap face at the midpoint
        fp = clamp((t - tf) / 0.3) if i else 1.0
        sx = abs(1 - 2 * fp) if i else 1.0
        rot = [-3, 2, -2, 3][i]
        if fp < 0.5:
            place(c, S("card_back", (380, 470), back_fn, seed=32), x, y, st, s, rot, key=51 + i, sx=max(sx, 0.02))
        else:
            place(c, S(f"card{i}", (380, 470), card_fn(title, sub, kind), seed=33 + i), x, y, st, s, rot, key=51 + i, sx=max(sx, 0.02))
            ic, sc = icons[kind]
            place(c, ic, x, y - 90, st, s * sc, rot, key=60 + i, sx=max(sx, 0.02))
    return c


def ov_question(c, t, st):
    # 47.4 - 54.1 : "Sắc tố da, màu tóc, ngoại hình... có thật không?"
    t_out = 54.0
    s = pop(t, 47.5, t_out)
    place(c, S("n_q", (600, 520), note_fn(600, 520), seed=35), 360, 470, st, s, -3, key=70)
    if s > 0.9:
        write(c, "Theo bạn...", 110, 300, t, 47.6, 0.5, 56, INK)
        write(c, "• sắc tố da", 110, 390, t, 48.7, 0.4, 56, INK)
        write(c, "• màu tóc", 110, 470, t, 49.7, 0.4, 56, INK)
        write(c, "• ngoại hình", 110, 550, t, 51.0, 0.4, 56, INK)
        write(c, "có thật không?", 110, 650, t, 51.9, 0.5, 64, RED)
    place(c, S("sw_skin_q", (5 * 84 + 4 * 22, 84), swatches_fn(SKINS), seed=36, border=6), 1620, 330, st, 0.8 * pop(t, 48.8, t_out), 4, key=71)
    place(c, S("hair_q", (5 * 104, 180), hair_fn(HAIRS), seed=37, border=6), 1620, 540, st, 0.7 * pop(t, 49.8, t_out), -3, key=72)
    place(c, S("q_big", (180, 280), qmark_fn, seed=38), 1640, 800, st, pop(t, 52.0, t_out), 8 + 6 * math.sin(t * 5), key=73)


def sc_real(t, st):
    # 54.1 - 60.4 : biological traits are real
    c = background(NAVY, 4, True).copy().convert("RGBA")
    place(c, S("sw_skin2", (5 * 84 + 4 * 22, 84), swatches_fn(SKINS), seed=39, border=7), 1080, 330, st, 1.2 * pop(t, 55.2), -2, key=80)
    place(c, S("hair2", (5 * 104, 180), hair_fn(HAIRS), seed=41, border=7), 1080, 600, st, 1.1 * pop(t, 56.6), 2, key=81)
    write(c, "sắc tố da", 1080, 200, t, 55.3, 0.5, 60, (250, 236, 200), "c")
    write(c, "màu tóc", 1080, 780, t, 56.7, 0.5, 60, (250, 236, 200), "c")
    place(c, S("dna", (140, 360), dna_fn, seed=42, border=7), 380, 470, st, 1.1 * pop(t, 57.9), 10 + 3 * math.sin(t * 2), key=82)
    n = S("n_bio", (520, 130), note_fn(520, 130, lined=False), seed=43)
    place(c, n, 380, 820, st, pop(t, 58.1), -3, key=83)
    write(c, "đặc điểm sinh học", 380, 820, t, 58.2, 0.6, 58, INK, "c")
    place(c, asset("real", lambda: Label("CÓ THẬT", 96, GREEN, seed=44, border=10)), 1500, 900, st, pop(t, 59.8, dur=0.3), -8, key=84)
    place(c, S("check", (180, 140), hand_check_fn, seed=45, border=7), 1780, 860, st, pop(t, 60.0, dur=0.3), key=85)
    return c


def sc_society(t, st):
    # 60.4 - 69.6 : society picks some traits -> racial categories -> meanings & hierarchy
    c = background(PURPLE, 5).copy().convert("RGBA")
    place(c, S("sw_skin3", (5 * 84 + 4 * 22, 84), swatches_fn(SKINS), seed=46, border=7), 960, 150, st, 1.15 * pop(t, 60.5), key=90)
    n = S("n_soc", (620, 120), note_fn(620, 120, lined=False), seed=47)
    place(c, n, 400, 150, st, pop(t, 61.2, 66.6), -3, key=91)
    write(c, "Xã hội lựa chọn...", 400, 150, t, 61.4, 0.7, 56, INK, "c", t1=66.6)
    # red crayon marks on the chosen swatches (x of swatch i = 960 - 2*121 + i*121 at scale 1.15)
    xs = [960 + (i - 2) * 106 * 1.15 for i in range(5)]
    crayon_circle(c, xs[0], 150, 62, 62, t, 62.1, 0.3, (250, 90, 80), 8)
    crayon_circle(c, xs[4], 150, 62, 62, t, 62.5, 0.3, (250, 90, 80), 8)
    # boxes: category A/B/C, later lifted onto hierarchy steps
    lift = ease_io(clamp((t - 69.0) / 0.6))
    place(c, S("stairs", (990, 450), stairs_fn, seed=48, border=8), 960, 860, st, pop(t, 68.9, dur=0.3), key=92)
    base = [(560, 760), (960, 760), (1360, 760)]
    step_y = [850, 700, 550]
    step_x = [630, 960, 1290]
    ps = people()
    groups = [(0, 1), (2,), (3, 4)]
    cols = [TEAL, CORAL, INK]
    for g in range(3):
        bx = base[g][0] + (step_x[g] - base[g][0]) * lift
        by = base[g][1] + (step_y[g] - base[g][1]) * lift
        s = pop(t, 63.8 + g * 0.2)
        for k, pi in enumerate(groups[g]):
            off = (k - (len(groups[g]) - 1) / 2) * 90
            place(c, ps[pi], bx + off, by - 110, st, 0.62 * s, 0, key=93 + pi)
        place(c, S(f"box{g}", (280, 170), box_fn(cols[g], "ABC"[g]), seed=21 + g), bx, by, st, s, key=30 + g)
        place(c, asset(f"tag{g}", lambda g=g: Label("ý nghĩa?", 34, MUST, DARK, seed=50 + g)), bx + 120, by - 120, st,
              pop(t, 67.4 + g * 0.2), 10 - g * 8, key=100 + g)
    write(c, "racial categories", 960, 320, t, 65.5, 0.7, 70, (250, 236, 200), "c", t1=68.8)
    write(c, "thứ bậc xã hội", 520, 360, t, 69.1, 0.5, 70, MUST, "c")
    return c


def ov_term(c, t, st):
    # 69.6 - end : "...chúng ta có thuật ngữ RACE"
    s = pop(t, 69.8)
    place(c, S("nb_term", (560, 560), note_fn(560, 560, spiral=True), seed=55), 1610, 520, st, s, 3, key=110)
    if s > 0.9:
        write(c, "Thuật ngữ:", 1380, 380, t, 70.8, 0.5, 64, INK)
        write(c, "RACE", 1610, 560, t, 71.5, 0.6, 170, RED, "c")
        crayon_circle(c, 1610, 565, 230, 110, t, 72.2, 0.4, INK, 8)


# timeline: (start, end, kind, fn)
TL = [(0.0, 6.35, "ov", ov_intro), (6.35, 18.45, "ov", ov_jars), (18.45, 28.6, "ov", ov_brain),
      (28.6, 34.45, "full", sc_race), (34.45, 37.8, "full", sc_topic), (37.8, 47.25, "full", sc_concepts),
      (47.25, 54.1, "ov", ov_question), (54.1, 60.45, "full", sc_real), (60.45, 69.65, "full", sc_society),
      (69.65, 99, "ov", ov_term)]
WIPE = 0.45


def seg_at(t):
    for i, s in enumerate(TL):
        if s[0] <= t < s[1]:
            return i
    return len(TL) - 1


_ov_cache = {}


def render_seg(i, t, st, spk):
    a, b, kind, fn = TL[i]
    if kind == "full":
        key = (i, st)
        if key not in _ov_cache:
            _ov_cache.clear()
            _ov_cache[key] = fn(t, st).convert("RGB")
        return _ov_cache[key]
    key = (i, st)
    if key not in _ov_cache:
        _ov_cache.clear()
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fn(layer, t, st)
        _ov_cache[key] = layer
    base = spk.convert("RGBA")
    base.alpha_composite(_ov_cache[key])
    return base.convert("RGB")


@functools.lru_cache(None)
def wipe_edge(seed):
    r = np.random.default_rng(seed)
    n = r.normal(0, 1, H // 8 + 1).astype(np.float32)
    n = np.interp(np.arange(H), np.arange(len(n)) * 8, n)
    f = r.normal(0, 1, H // 2 + 1).astype(np.float32)
    f = np.interp(np.arange(H), np.arange(len(f)) * 2, f)
    return 22 * n + 7 * f


def torn_wipe(fa, fb, p, seed):
    """Torn-paper page turn: B slides over A with a ragged white paper edge."""
    edge = W * 1.1 - p * (W * 1.2) + wipe_edge(seed)
    xs = np.arange(W)[None, :]
    a, b = np.asarray(fa), np.asarray(fb)
    m = xs > edge[:, None]
    white = (xs > edge[:, None] - 16) & ~m
    out = np.where(m[..., None], b, a).copy()
    out[white] = (250, 247, 238)
    return Image.fromarray(out)


def main():
    cmd_in = ["ffmpeg", "-v", "error", "-ss", str(T_START), "-i", SRC, "-t", str(T_END - T_START),
              "-vf", FIT, "-f", "rawvideo", "-pix_fmt", "rgb24", "-r", str(FPS), "-"]
    cmd_out = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
               "-i", "-", "-ss", str(T_START), "-t", str(T_END - T_START), "-i", SRC, "-map", "0:v", "-map", "1:a",
               "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
               "-shortest", OUT]
    pin = subprocess.Popen(cmd_in, stdout=subprocess.PIPE)
    pout = subprocess.Popen(cmd_out, stdin=subprocess.PIPE)
    n = 0
    while True:
        raw = pin.stdout.read(W * H * 3)
        if len(raw) < W * H * 3:
            break
        t = T_START + n / FPS
        st = int(t * ANIM)
        ta = st / ANIM  # stop-motion: animation advances on 12fps steps
        spk = Image.frombytes("RGB", (W, H), raw)
        i = seg_at(t)
        frame = None
        # torn wipe around each boundary where the scene kind changes or a full scene follows
        for j in range(1, len(TL)):
            tb = TL[j][0]
            if tb - WIPE / 2 <= t < tb + WIPE / 2:
                p = ease_io((t - (tb - WIPE / 2)) / WIPE)
                fa = render_seg(j - 1, ta, st, spk).copy()
                fb = render_seg(j, ta, st, spk)
                if TL[j - 1][2] == "ov" and TL[j][2] == "ov":
                    frame = None  # overlay->overlay: no wipe, pops handle it
                else:
                    frame = torn_wipe(fa, fb, p, j)
                break
        if frame is None:
            frame = render_seg(i, ta, st, spk)
        pout.stdin.write(frame.tobytes())
        n += 1
        if n % 60 == 0:
            print(f"t={t:.1f}", flush=True)
    pout.stdin.close(); pout.wait()


if __name__ == "__main__":
    main()
