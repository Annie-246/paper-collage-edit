# Edit of segment 3: hand-anchored word chips, framed photos / stock clips / Pocahontas, paper cut-out style.
import sys, math, random, subprocess, functools, json
import numpy as np
from PIL import Image, ImageDraw
import render as R
from render import (W, H, ANIM, NAVY, MUST, PINK, CORAL, TEAL, CREAM, INK, RED, WOOD, PURPLE, GREEN, DARK,
                    S, Label, asset, place, pop, write, note_fn, text_c, clamp, ease_io, background, people)
import render2 as V2
from render2 import tag

SRC = "input.mp4"  # path to the source video
OUT = sys.argv[1] if len(sys.argv) > 1 else "output.mp4"
FPS = 30
HANDS = json.load(open("v4/hands.json"))
WHITE = (252, 248, 236)

CAM = [  # (time, zoom, focus x, focus y)
    (0.0, 1.0, 1000, 540), (11.4, 1.0, 1000, 540),
    (31.2, 1.0, 1000, 540), (34.8, 1.1, 1010, 480),
    (50.2, 1.12, 1010, 470), (52.9, 1.12, 1010, 470), (53.05, 1.0, 1000, 540), (61.8, 1.08, 1000, 500),
    (67.6, 1.0, 1000, 540), (72.0, 1.0, 1000, 540), (77.8, 1.1, 1000, 500),
    (91.3, 1.12, 1010, 470), (94.6, 1.12, 1010, 470), (94.75, 1.0, 1000, 540),
]


def cam(t):
    for (t0, z0, x0, y0), (t1, z1, x1, y1) in zip(CAM, CAM[1:]):
        if t0 <= t < t1:
            p = ease_io((t - t0) / (t1 - t0))
            return z0 + (z1 - z0) * p, x0 + (x1 - x0) * p, y0 + (y1 - y0) * p
    return CAM[-1][1:]


def apply_cam(img, t):
    z, fx, fy = cam(t)
    if z <= 1.001:
        return img, (0, 0, 1.0)
    x0, y0, cw, ch = V2.crop_origin(z, fx, fy)
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch)), (x0, y0, z)


# ---------- hand-anchored chips (comment 4) ----------
PHONE = (1000, 790)  # the hand holding the phone rests around here


def gesture_hand(t):
    """palm centre of the free (gesturing) hand near time t, or None."""
    f0 = int(t * FPS)
    for d in range(0, 13):
        for f in (f0 - d, f0 + d):
            if 0 <= f < len(HANDS) and HANDS[f]:
                best = max(HANDS[f], key=lambda h: math.hypot(h[0] - PHONE[0], h[1] - PHONE[1]))
                if math.hypot(best[0] - PHONE[0], best[1] - PHONE[1]) > 170:
                    return best[0], min(best[1], best[2])
    return None


FACE = (840, 110, 1230, 640)
_chip_pos = {}


def chip_pos(key, t0, w, h, side_hint, camv):
    if key in _chip_pos:
        return _chip_pos[key]
    hp = gesture_hand(t0)
    if hp is not None:
        x0, y0, z = camv
        hx, hy = (hp[0] - x0) * z, (hp[1] - y0) * z
        right = hx > 1020
        cx = hx + (w / 2 + 30 if right else -(w / 2 + 30))
        cy = hy - h / 2 - 20
    else:
        right = side_hint > 0
        cx, cy = (1560 if right else 400), 360
    # keep clear of the face (face box follows the camera zoom); switch side or shrink if a side is too narrow
    x0c, y0c, zc = camv
    fx0, fy0 = (FACE[0] - x0c) * zc, (FACE[1] - y0c) * zc
    fx1, fy1 = (FACE[2] - x0c) * zc, (FACE[3] - y0c) * zc
    k = 1.0
    if cy + h / 2 > fy0 and cy - h / 2 < fy1 and cx + w / 2 > fx0 and cx - w / 2 < fx1:
        room_l, room_r = fx0 - 50, W - fx1 - 50
        if (right and w > room_r and room_l > room_r) or (not right and w > room_l and room_r > room_l):
            right = not right
        room = room_r if right else room_l
        k = min(1.0, room / w)
        w, h = w * k, h * k
        cx = fx1 + 25 + w / 2 if right else fx0 - 25 - w / 2
    cx = clamp(cx, w / 2 + 30, W - w / 2 - 30)
    cy = clamp(cy, h / 2 + 40, H - h / 2 - 40)
    # avoid chips already placed in the same moment
    down = cy < 560
    for _ in range(10):
        hit = None
        for (ox, oy, ow, oh, ot, _k) in _chip_pos.values():
            if abs(ot - t0) < 6 and abs(ox - cx) < (ow + w) / 2 and abs(oy - cy) < (oh + h) / 2 + 10:
                hit = (oy, oh)
                break
        if hit is None:
            break
        oy, oh = hit
        cy = oy + (oh + h) / 2 + 18 if down else oy - (oh + h) / 2 - 18
        if cy > H - h / 2 - 40 or cy < h / 2 + 40:
            down = not down
            cy = clamp(cy, h / 2 + 40, H - h / 2 - 40)
    _chip_pos[key] = (cx, cy, w, h, t0, k)
    return _chip_pos[key]


def chip(c, key, text, color, t, t0, t1, st, camv, size=62, side=1, tcol=(255, 255, 255), rot=None):
    s = pop(t, t0, t1, 0.3)
    if s <= 0:
        return None
    size = int(size * 1.2)
    lb = tag(key, text, color, size, tcol)
    img = lb.get(0)
    cx, cy, w, h, _, k = chip_pos(key, t0, img.width, img.height, side, camv)
    r = rot if rot is not None else random.Random(key).uniform(-6, 6)
    place(c, lb, cx, cy, st, s * k, r, key=hash(key) % 50)
    return cx, cy, w, h


def strike_box(c, box, t, t0, dur=0.25):
    if t < t0 or box is None:
        return
    cx, cy, w, h = box
    p = ease_io(clamp((t - t0) / dur))
    x0, x1 = cx - w / 2 + 10, cx + w / 2 - 10
    ImageDraw.Draw(c).line([(x0, cy + 10), (x0 + (x1 - x0) * p, cy - 6 * p)], fill=(40, 30, 30, 255), width=12)


# ---------- framed media (comment 5): torn white paper print + tape ----------
@functools.lru_cache(None)
def paper_frame(w, h, seed):
    fn = lambda d, img, p: d.rectangle([p, p, p + w, p + h], fill=(252, 250, 242))
    return R.build_sprite((w, h), fn, seed, border=12)


def tape_fn(d, img, p):
    d.rectangle([p, p, p + 150, p + 44], fill=(246, 232, 170, 200))


def framed(c, media, cx, cy, st, scale=1.0, rot=0.0, key=0):
    """media (RGB/RGBA PIL) on a torn white paper frame with two tape strips; boils with the stop-motion step."""
    m = media.convert("RGBA")
    pad = 22
    fr = paper_frame(m.width + 2 * pad, m.height + 2 * pad, st % 3).copy()
    off = (fr.width - m.width) // 2
    fr.alpha_composite(m, (off, off))
    tp = S("tape", (150, 44), tape_fn, seed=90, border=0)
    tpi = tp.get(0)
    for tx, tr in ((off + 30, 8), (fr.width - off - 180, -7)):
        ti = tpi.rotate(tr, expand=True)
        fr.alpha_composite(ti, (int(tx), max(0, off - 40)))
    place(c, fr, cx, cy, st, scale, rot, key=key)


@functools.lru_cache(None)
def photo(path, maxw, maxh):
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    k = min(maxw / im.width, maxh / im.height)
    return bg.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)


class Clip:
    """sequential 1280x720 reader for a pre-cut illustration clip, starting at scene time t_start."""
    def __init__(self, path, t_start):
        self.path, self.t0 = path, t_start
        self.p, self.idx, self.img = None, -1, None

    def get(self, t):
        if self.p is None:
            self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", self.path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                      stdout=subprocess.PIPE)
        f = max(0, int((t - self.t0) * FPS))
        while self.idx < f:
            b = self.p.stdout.read(1280 * 720 * 3)
            if len(b) < 1280 * 720 * 3:
                break
            self.idx += 1
            self.img = Image.frombytes("RGB", (1280, 720), b)
        return self.img if self.img is not None else Image.new("RGB", (1280, 720))


CLIPS = {"parl": Clip("v4/clips/parl.mp4", 35.3), "globe": Clip("v4/clips/globe.mp4", 39.05),
         "dance": Clip("v4/clips/dance.mp4", 43.95), "poca": Clip("v4/clips/poca.mp4", 96.45)}


# ---------- speaker overlays ----------
def balance_beam_fn(d, img, p):
    d.line([(p + 20, p + 30), (p + 500, p + 30)], fill=(120, 80, 50), width=16)
    for x, col in ((p + 70, R.SKINS[0]), (p + 450, R.SKINS[4])):
        d.line([(x, p + 30), (x - 60, p + 190)], fill=DARK, width=4)
        d.line([(x, p + 30), (x + 60, p + 190)], fill=DARK, width=4)
        d.chord([x - 90, p + 150, x + 90, p + 250], 0, 180, fill=(210, 170, 90))
        d.ellipse([x - 42, p + 110, x + 42, p + 194], fill=col)


def balance_stand_fn(d, img, p):
    d.rectangle([p + 110, p + 20, p + 130, p + 330], fill=(120, 80, 50))
    d.polygon([(p + 20, p + 360), (p + 220, p + 360), (p + 120, p + 300)], fill=(150, 100, 60))
    d.ellipse([p + 100, p, p + 140, p + 40], fill=MUST)


def warn_fn(d, img, p):
    d.polygon([(p + 190, p), (p + 380, p + 330), (p, p + 330)], fill=DARK)
    d.polygon([(p + 190, p + 40), (p + 345, p + 305), (p + 35, p + 305)], fill=MUST)
    d.text((p + 158, p + 90), "!", font=R.font(200), fill=DARK)


def ov_a(c, t, st, camv):
    # opening: drawings carry the idea, only one keyword per idea (user: less text, more pictures)
    # 1) "không hoàn toàn do sinh học" — DNA on the left
    s1 = pop(t, 0.4, 3.3)
    place(c, S("dna_a", (140, 360), R.dna_fn, seed=93, border=8), 360, 430, st, 1.15 * s1, 8 + 3 * math.sin(t * 2), key=1)
    write(c, "không chỉ", 360, 715, t, 1.4, 0.4, 84, RED, "c", t1=3.3)
    place(c, tag("kw_sh", "SINH HỌC", TEAL, 84), 360, 820, st, pop(t, 2.3, 3.3, 0.3), -4, key=2)
    # 2) "gắn ý nghĩa cho màu da" — skin swatches get meaning tags stuck on them, on the right
    s2 = pop(t, 4.5, 9.4)
    place(c, S("sw_a", (5 * 84 + 4 * 22, 84), R.swatches_fn(R.SKINS), seed=94, border=7), 1560, 420, st, 1.2 * s2, -2, key=3)
    for i, x in enumerate((1370, 1560, 1750)):
        place(c, asset(f"ym{i}", lambda i=i: Label("ý nghĩa?", 36, MUST, DARK, seed=95 + i)), x, 330, st,
              pop(t, 4.8 + i * 0.15, 9.4, 0.25), (-12, 6, -8)[i], key=4 + i)
    place(c, tag("kw_md", "MÀU DA", CORAL, 90), 1560, 610, st, pop(t, 5.5, 9.4, 0.3), 3, key=7)
    # 3) "đối xử" — a tilting balance, on the left
    s3 = pop(t, 6.3, 11.3)
    tilt = 11 * ease_io(clamp((t - 6.8) / 0.7))
    place(c, S("bal_stand", (240, 360), balance_stand_fn, seed=97, border=8), 360, 560, st, s3, 0, key=8)
    place(c, S("bal_beam", (520, 260), balance_beam_fn, seed=98, border=8), 360, 460, st, s3, -tilt, key=9)
    place(c, tag("kw_dx", "ĐỐI XỬ", INK, 90), 360, 830, st, pop(t, 6.6, 11.3, 0.3), -3, key=10)
    # 4) "hậu quả đáng kể" — warning sign slams in on the right
    s4 = pop(t, 10.1, 11.3, 0.25)
    shake = 6 * math.sin(t * 60) * clamp(1 - (t - 10.3) / 0.5) if t > 10.3 else 0
    place(c, S("warn", (380, 330), warn_fn, seed=99, border=9), 1560 + shake, 430, st, 1.1 * s4, 4, key=11)
    if t >= 10.25:
        p = clamp((t - 10.25) / 0.15)
        place(c, tag("kw_hq", "HẬU QUẢ", RED, 104), 1560, 700, st, (2.4 - 1.4 * p) * pop(t, 10.25, 11.3, 0.01), -5, key=12, jitter=False)
    # the three terms pop from the raised hand
    out = 16.3
    chip(c, "b1", "Ethnicity", TEAL, t, 12.95, out, st, camv, 80, -1, rot=-5)
    chip(c, "b2", "Nationality", CORAL, t, 13.95, out, st, camv, 80, -1, rot=4)
    chip(c, "b3", "Indigeneity", INK, t, 14.95, out, st, camv, 80, -1, rot=-3)


def ov_d(c, t, st, camv):
    out = 35.3
    chip(c, "d1", "song song với...", INK, t, 33.3, out, st, camv, 58, 1)
    chip(c, "d2", "lịch sử", TEAL, t, 34.0, out, st, camv, 76, 1)
    chip(c, "d3", "QUYỀN LỰC", RED, t, 34.85, out, st, camv, 84, 1)


def ov_h(c, t, st, camv):
    b = chip(c, "h1", "nhận diện khác biệt", TEAL, t, 51.5, 56.1, st, camv, 62, 1)
    strike_box(c, b, t, 52.9)
    chip(c, "h2", "TẠO RA một cách hiểu", RED, t, 53.6, 56.1, st, camv, 70, 1)
    chip(c, "h3", "không phải ai cũng", INK, t, 58.0, 61.9, st, camv, 58, 1)
    chip(c, "h4", "có QUYỀN ngang nhau", RED, t, 59.6, 61.9, st, camv, 66, 1)


def ov_k(c, t, st, camv):
    out = 77.9
    chip(c, "k0", "phim ảnh & truyền thông", INK, t, 67.8, 71.6, st, camv, 62, -1)
    chip(c, "k1", "nhấn mạnh đặc điểm nào?", TEAL, t, 72.9, out, st, camv, 56, -1)
    chip(c, "k2", "kể câu chuyện nào?", CORAL, t, 74.1, out, st, camv, 56, -1)
    chip(c, "k3", "ai được nói?", GREEN, t, 75.6, out, st, camv, 60, -1)
    chip(c, "k4", "ai bị nói thay?", RED, t, 76.9, out, st, camv, 60, -1)


def ov_m(c, t, st, camv):
    out = 96.5
    chip(c, "m1", "representation “tích cực”", GREEN, t, 93.9, out, st, camv, 60, 1)
    chip(c, "m2", "chưa chắc TIẾN BỘ", RED, t, 95.5, out, st, camv, 68, 1)


# ---------- full-screen scenes ----------
TERMS = {
    "eth": ("v4/assets/eth.webp", "Ethnicity", "tộc người", TEAL, (243, 214, 150),
            [("ngôn ngữ", 17.6), ("văn hóa", 18.3), ("lịch sử được chia sẻ", 19.1)], 16.3),
    "nat": ("v4/assets/nat.jpg", "Nationality", "quốc tịch", CORAL, (170, 205, 225),
            [("tư cách pháp lý", 22.6), ("cảm giác thuộc về", 23.6), ("một quốc gia", 24.3)], 20.45),
    "ind": ("v4/assets/ind.png", "Indigeneity", "tính bản địa", INK, (190, 214, 160),
            [("lịch sử cộng đồng", 26.6), ("bản sắc tập thể", 28.1), ("gắn bó lâu dài với vùng đất", 29.2)], 25.55),
}


def sc_term(key):
    path, title, sub, col, bg, words, t0 = TERMS[key]

    def fn(t, st):
        c = background(bg, hash(key) % 20).copy().convert("RGBA")
        framed(c, photo(path, 1000, 640), 640, 560, st, pop(t, t0 + 0.1, dur=0.4), -3, key=1)
        place(c, tag("tt_" + key, title, col, 96), 1450, 230, st, pop(t, t0 + 0.2), 3, key=2)
        write(c, sub, 1450, 370, t, t0 + 0.4, 0.4, 72, NAVY, "c")
        for i, (w, tw) in enumerate(words):
            write(c, "• " + w, 1150, 500 + i * 120, t, tw, 0.5, 70, NAVY)
        return c
    return fn


def media_scene(clipkey, bg, head, t_head, tags, stars=False):
    def fn(t, st):
        c = background(bg, hash(clipkey) % 20, stars).copy().convert("RGBA")
        frame = CLIPS[clipkey].get(t).resize((1120, 630), Image.BILINEAR)
        framed(c, frame, 960, 600, st, 1.0, -1.5, key=3)
        write(c, head[0], 960, 105, t, t_head, 0.7, 78, WHITE if stars or bg in (NAVY, PURPLE) else NAVY, "c")
        if len(head) > 1:
            write(c, head[1], 960, 200, t, head[2], 0.6, 80, MUST if stars or bg in (NAVY, PURPLE) else RED, "c")
        for (k, text, col, x, y, rot, tw, size) in tags:
            place(c, tag(k, text, col, size, DARK if col == MUST else (255, 255, 255)), x, y, st, pop(t, tw, dur=0.28), rot, key=hash(k) % 40)
        return c
    return fn


sc_parl = media_scene("parl", NAVY, ("Khi một nhà nước quyết định", "AI được công nhận là một nhóm sắc tộc?", 37.3), 36.4,
                      [("tg_cn", "công nhận?", MUST, 1480, 930, -6, 38.5, 70)], stars=True)
sc_globe = media_scene("globe", TEAL, ("Khi biên giới quốc gia xác định...",), 39.4,
                       [("tg_tv", "ai “thuộc về”", GREEN, 470, 880, -5, 40.7, 72),
                        ("tg_ng", "ai là “người ngoài”", RED, 1450, 880, 5, 42.1, 72)])
sc_dance = media_scene("dance", PURPLE, ("Khi một cộng đồng bản địa được mô tả là...",), 44.4,
                       [("tg_nt", "“nguyên thủy”", MUST, 420, 900, -7, 46.4, 70),
                        ("tg_tk", "“thuần khiết”", MUST, 960, 950, 4, 47.4, 70),
                        ("tg_gg", "“gần gũi với thiên nhiên”", MUST, 1440, 880, -4, 48.6, 64)])


def sc_repr(t, st):
    c = background(PURPLE, 16).copy().convert("RGBA")
    place(c, tag("t_repr", "REPRESENTATION", MUST, 150, DARK), 960, 400, st, pop(t, 63.5, dur=0.35), -3, key=5)
    write(c, "sự đại diện", 960, 600, t, 65.2, 0.5, 90, WHITE, "c")
    write(c, "= một vấn đề về", 820, 760, t, 66.2, 0.5, 76, WHITE, "c")
    place(c, tag("t_ql", "QUYỀN LỰC", RED, 90), 1360, 760, st, pop(t, 67.2, dur=0.3), 4, key=6)
    return c


def film_fn(d, img, p):
    d.rectangle([p, p, p + 1500, p + 420], fill=(40, 36, 44))
    for x in range(p + 20, p + 1500, 60):
        d.rectangle([x, p + 14, x + 30, p + 40], fill=(236, 230, 214))
        d.rectangle([x, p + 380, x + 30, p + 406], fill=(236, 230, 214))
    for i in range(3):
        x = p + 40 + i * 490
        d.rectangle([x, p + 60, x + 440, p + 360], fill=(236, 226, 200))


def sc_film(t, st):
    # a film strip: three frames, each shows the same group but labelled by the film
    c = background(CORAL, 17).copy().convert("RGBA")
    write(c, "Phim không cần nói thẳng", 900, 95, t, 78.2, 0.7, 80, WHITE, "c")
    place(c, tag("t_mr2", "“man rợ”", DARK, 60), 1480, 95, st, pop(t, 81.4, 88.0), 6, key=7)
    write(c, "nhưng nếu họ liên tục chỉ xuất hiện với...", 960, 205, t, 82.3, 0.9, 70, NAVY, "c")
    place(c, S("film", (1500, 420), film_fn, seed=91, border=8), 960, 580, st, pop(t, 78.3), -1, key=8)
    ps = people()
    words = [("bạo lực", 84.3), ("sự lạc hậu", 85.1), ("cần được “khai hóa”", 87.1)]
    for i, (w, tw) in enumerate(words):
        x = 960 + (i - 1) * 490
        place(c, ps[[2, 3, 4][i]], x, 575, st, 0.62 * pop(t, 78.8 + i * 0.15), 0, key=9 + i)
        place(c, tag(f"t_f{i}", w, RED, 72), x, 810, st, pop(t, tw, dur=0.28), (-5, 4, -3)[i], key=12 + i)
    if t >= 88.0:
        write(c, "= một HỆ THỐNG Ý NGHĨA", 960, 960, t, 88.9, 0.8, 84, WHITE, "c")
    return c


def sc_poca(t, st):
    # Pocahontas (1995): the "positive" but idealised image
    c = background(MUST, 18).copy().convert("RGBA")
    frame = CLIPS["poca"].get(t).resize((1180, 664), Image.BILINEAR)
    framed(c, frame, 960, 560, st, 1.0, 1.2, key=14)
    write(c, "Pocahontas (1995)", 960, 90, t, 96.9, 0.6, 60, NAVY, "c")
    tg = [("tp1", "cao quý", GREEN, 330, 330, -6, 99.0), ("tp2", "hòa bình", TEAL, 1600, 300, 5, 99.9),
          ("tp3", "gần gũi thiên nhiên", GREEN, 360, 760, 4, 100.6),
          ("tp4", "LÝ TƯỞNG HÓA", RED, 1560, 720, -5, 103.8), ("tp5", "đóng khung trong quá khứ", RED, 1300, 990, 3, 105.2)]
    for (k, text, col, x, y, rot, tw) in tg:
        if t < 108.8:
            place(c, tag(k, text, col, 74), x, y, st, pop(t, tw, 108.8, 0.28), rot, key=hash(k) % 40)
    if t >= 109.0:
        place(c, tag("t_stereo", "STEREOTYPE vẫn tồn tại", RED, 120), 960, 460, st, pop(t, 109.5, dur=0.3), -4, key=20)
        place(c, S("n_poca", (1300, 250), note_fn(1300, 250, lined=False), seed=92), 960, 800, st, pop(t, 111.6), -1, key=21)
        write(c, "…chỉ dưới một hình thức ngầm", 960, 745, t, 111.8, 0.7, 80, NAVY, "c")
        write(c, "để xã hội “dễ chấp nhận hơn”", 960, 855, t, 113.3, 0.7, 80, RED, "c")
    return c


def overlay(fn):
    def run(frame, t, st, camv):
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fn(c, t, st, camv)
        f = frame.convert("RGBA")
        f.alpha_composite(c)
        return f.convert("RGB")
    return run


TL = [
    (0.0, 16.3, "sp", overlay(ov_a)),
    (16.3, 20.45, "fs", sc_term("eth")), (20.45, 25.55, "fs", sc_term("nat")), (25.55, 31.2, "fs", sc_term("ind")),
    (31.2, 35.5, "sp", overlay(ov_d)),
    (35.5, 39.25, "fs", sc_parl), (39.25, 44.15, "fs", sc_globe), (44.15, 50.2, "fs", sc_dance),
    (50.2, 62.0, "sp", overlay(ov_h)),
    (62.0, 67.6, "fs", sc_repr),
    (67.6, 78.0, "sp", overlay(ov_k)),
    (78.0, 91.3, "fs", sc_film),
    (91.3, 96.7, "sp", overlay(ov_m)),
    (96.7, 999, "fs", sc_poca),
]
LIVE = {sc_parl, sc_globe, sc_dance, sc_poca}  # scenes with moving video: no stop-motion caching
WIPE = 0.45
_cache = {}


def seg_at(t):
    for i, sg in enumerate(TL):
        if sg[0] <= t < sg[1]:
            return i
    return len(TL) - 1


def render_seg(i, t, st, raw):
    a, b, kind, fn = TL[i]
    if kind == "fs":
        if fn in LIVE:
            return fn(t, st).convert("RGB")
        key = (i, st)
        if key not in _cache:
            if len(_cache) > 4:
                _cache.clear()
            _cache[key] = fn(t, st).convert("RGB")
        return _cache[key]
    frame, camv = apply_cam(raw, t)
    return fn(frame, t, st, camv)


def main():
    pin = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", R.FIT, "-f", "rawvideo", "-pix_fmt", "rgb24", "-r", "30", "-"], stdout=subprocess.PIPE)
    pout = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                             "-i", "-", "-i", SRC, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], stdin=subprocess.PIPE)
    n = 0
    while True:
        b = pin.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            break
        t = n / FPS
        st = int(t * ANIM)
        raw = Image.frombytes("RGB", (W, H), b)
        frame = None
        for j in range(1, len(TL)):
            tb = TL[j][0]
            if tb - WIPE / 2 <= t < tb + WIPE / 2:
                p = ease_io((t - (tb - WIPE / 2)) / WIPE)
                frame = R.torn_wipe(render_seg(j - 1, t, st, raw).copy(), render_seg(j, t, st, raw), p, j)
                break
        if frame is None:
            frame = render_seg(seg_at(t), t, st, raw)
        pout.stdin.write(frame.tobytes())
        n += 1
        if n % 90 == 0:
            print(f"t={t:.1f}", flush=True)
    pout.stdin.close()
    pout.wait()


if __name__ == "__main__":
    main()
