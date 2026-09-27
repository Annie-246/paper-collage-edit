# Edit of segment 6: the myth of the exceptional minority success story.
# Real photos (Wikimedia Commons) of the people named + crowds, media, criticism letters, drawn in the paper style.
import sys, math, random, subprocess
from PIL import Image, ImageDraw
import render as R
from render import (W, H, ANIM, NAVY, MUST, PINK, CORAL, TEAL, CREAM, INK, RED, WOOD, PURPLE, GREEN, DARK,
                    SKINS, S, Label, asset, place, pop, write, clamp, ease_io, background, people)
from render2 import tag, crop_origin
from render4 import framed, photo
from render5 import slam, oscar_fn, angry_fn
from render6 import book_fn, magnifier_fn

SRC = "input.mp4"  # path to the source video
OUT = sys.argv[1] if len(sys.argv) > 1 else "output.mp4"
FPS = 30
WHITE = (252, 248, 236)
A = "v7/assets/"

CAM = [(0.0, 1.0, 960, 540), (19.0, 1.0, 960, 540), (29.9, 1.08, 1000, 480),
       (55.2, 1.0, 960, 540), (64.0, 1.06, 1000, 480), (69.3, 1.0, 960, 540), (70.1, 1.0, 960, 540),
       (70.25, 1.12, 1000, 460), (73.6, 1.12, 1000, 460), (91.7, 1.0, 960, 540), (100.3, 1.06, 1000, 500)]


def cam(t):
    for (t0, z0, x0, y0), (t1, z1, x1, y1) in zip(CAM, CAM[1:]):
        if t0 <= t < t1:
            p = ease_io((t - t0) / (t1 - t0))
            return z0 + (z1 - z0) * p, x0 + (x1 - x0) * p, y0 + (y1 - y0) * p
    return CAM[-1][1:]


def apply_cam(img, t):
    z, fx, fy = cam(t)
    if z <= 1.001:
        return img
    x0, y0, cw, ch = crop_origin(z, fx, fy)
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))


def ph(name, w, h):
    return photo(A + name, w, h)


# ---------- drawings ----------
def laurel_fn(d, img, p):
    # two leafy branches curving up into a wreath
    cx, cy, r = p + 160, p + 150, 118
    for side in (-1, 1):
        for i in range(8):
            a = math.radians(100 + i * 21)
            x, y = cx + side * r * math.sin(a), cy - r * math.cos(a)
            tx, ty = side * math.cos(a), math.sin(a)
            nx, ny = -ty, tx
            pts = [(x - tx * 30, y - ty * 30), (x + nx * 13, y + ny * 13), (x + tx * 30, y + ty * 30), (x - nx * 13, y - ny * 13)]
            d.polygon(pts, fill=(84, 150, 70) if i % 2 else (110, 176, 84))
    d.ellipse([cx - 16, cy + r - 10, cx + 16, cy + r + 22], fill=RED)


def confetti(c, t, t0, seed, n=40):
    if t < t0:
        return
    r = random.Random(seed)
    d = ImageDraw.Draw(c)
    cols = [RED, MUST, TEAL, CORAL, INK, PINK]
    for _ in range(n):
        x0, sp, ph0 = r.uniform(0, W), r.uniform(260, 520), r.uniform(0, 6)
        y = -40 + (t - t0) * sp - r.uniform(0, 300)
        if 0 < y < H:
            x = x0 + 30 * math.sin(t * 3 + ph0)
            s = r.randint(10, 20)
            d.rectangle([x, y, x + s, y + s * 0.6], fill=r.choice(cols) + (255,))


def newspaper_fn(img_photo):
    def fn(d, img, p):
        d.rectangle([p, p, p + 760, p + 900], fill=(244, 240, 228))
        f1, f2, f3 = R.font(46), R.font(80), R.font(28)
        d.text((p + 40, p + 30), "THE DAILY NEWS", font=f1, fill=DARK)
        d.line([(p + 30, p + 95), (p + 730, p + 95)], fill=DARK, width=4)
        d.text((p + 40, p + 110), "A POST-RACIAL", font=f2, fill=DARK)
        d.text((p + 40, p + 200), "AMERICA?", font=f2, fill=RED)
        img.alpha_composite(img_photo, (p + 40, p + 310))
        for y in range(p + 330 + img_photo.height, p + 880, 34):
            d.line([(p + 40, y), (p + 720, y)], fill=(170, 164, 150), width=10)
    return fn


def tv_fn(d, img, p):
    d.rounded_rectangle([p, p, p + 820, p + 560], 40, fill=(70, 60, 64))
    d.rounded_rectangle([p + 30, p + 30, p + 790, p + 490], 26, fill=(20, 20, 24))
    d.line([(p + 300, p + 560), (p + 240, p + 640)], fill=(70, 60, 64), width=16)
    d.line([(p + 520, p + 560), (p + 580, p + 640)], fill=(70, 60, 64), width=16)
    for x in (p + 700, p + 750):
        d.ellipse([x, p + 505, x + 32, p + 537], fill=MUST)


def spotlight_fn(d, img, p):
    d.polygon([(p + 190, p), (p + 230, p), (p + 400, p + 480), (p + 20, p + 480)], fill=(255, 240, 170, 170))
    d.ellipse([p + 20, p + 440, p + 400, p + 520], fill=(255, 236, 150))


def door_fn(d, img, p):
    d.rectangle([p, p, p + 240, p + 380], fill=(120, 80, 50))
    d.polygon([(p + 20, p + 20), (p + 170, p + 60), (p + 170, p + 400), (p + 20, p + 360)], fill=(250, 214, 120))
    d.ellipse([p + 140, p + 200, p + 160, p + 220], fill=DARK)


def stairs2_fn(d, img, p):
    for i in range(5):
        d.rectangle([p + i * 170, p + 520 - i * 110, p + i * 170 + 170, p + 620], fill=(214, 168, 108))
        d.line([(p + i * 170, p + 520 - i * 110), (p + i * 170 + 170, p + 520 - i * 110)], fill=(160, 110, 60), width=8)


def wall_fn(d, img, p):
    for r in range(5):
        for c in range(8):
            off = 45 if r % 2 else 0
            x, y = p + c * 95 - off, p + r * 55
            if x < p or x + 88 > p + 720:
                continue
            d.rectangle([x, y, x + 88, y + 48], fill=(176, 84, 60))


def envelope_fn(d, img, p):
    d.rectangle([p, p, p + 260, p + 170], fill=(248, 240, 220))
    d.polygon([(p, p), (p + 130, p + 95), (p + 260, p)], fill=(228, 214, 186))
    d.rectangle([p + 196, p + 14, p + 244, p + 58], fill=RED)


def comment_fn(text, who):
    fnt, fn2 = R.font(54), R.font(30)
    bb = fnt.getbbox(text)
    w = max(460, bb[2] - bb[0] + 140)

    def fn(d, img, p):
        d.rounded_rectangle([p, p, p + w, p + 160], 26, fill=(255, 255, 255))
        d.polygon([(p + 60, p + 160), (p + 110, p + 160), (p + 50, p + 200)], fill=(255, 255, 255))
        d.ellipse([p + 20, p + 20, p + 80, p + 80], fill=(150, 160, 175))
        d.text((p + 100, p + 22), who, font=fn2, fill=(120, 120, 130))
        d.text((p + 100 - bb[0], p + 70), text, font=fnt, fill=DARK)
    return (w, 200), fn


def comment(key, text, who="người dùng ẩn danh"):
    size, fn = comment_fn(text, who)
    return asset(key, lambda: R.Sprite(size, fn, border=6, seed=hash(key) % 90))


def tv_screen(c, img, cx, cy, st, s):
    """TV sprite with a photo on its screen."""
    place(c, S("tv", (820, 640), tv_fn, seed=130, border=8), cx, cy, st, s, 0, key=90)
    if s > 0.95 and img is not None:
        m = img.copy()
        m.thumbnail((740, 440))
        c.alpha_composite(m.convert("RGBA"), (int(cx - m.width / 2), int(cy - 35 - m.height / 2)))


def strike_line(c, x0, x1, y, t, t0, dur=0.3):
    if t < t0:
        return
    p = ease_io(clamp((t - t0) / dur))
    ImageDraw.Draw(c).line([(x0, y), (x0 + (x1 - x0) * p, y - 10 * p)], fill=RED + (255,), width=14)


# ---------- speaker overlays (face ≈ x 860–1150, y 230–500) ----------
def ov_open(c, t, st):
    out = 3.45
    place(c, S("laurel", (320, 300), laurel_fn, seed=131, border=6), 360, 380, st, pop(t, 0.3, out), 0, key=1)
    place(c, tag("t_tv", "TÔN VINH", MUST, 88, DARK), 360, 620, st, pop(t, 0.6, out), -4, key=2)
    ps = people()
    for i in range(3):
        place(c, ps[2 + i], 1440 + i * 150, 500, st, 0.5 * pop(t, 2.8 + i * 0.1, out), (i - 1) * 5, key=3 + i)
    place(c, tag("t_ts", "nhóm THIỂU SỐ", CORAL, 72), 1590, 720, st, pop(t, 3.0, out), 3, key=6)


def ov_single(c, t, st):
    out = 29.9
    place(c, S("spot", (420, 520), spotlight_fn, seed=132, border=0, shadow=False), 360, 420, st, pop(t, 20.9, out), 0, key=10)
    place(c, people()[4], 360, 560, st, 0.6 * pop(t, 21.1, out), 0, key=11)
    place(c, tag("t_tgdl", "TẤM GƯƠNG ĐƠN LẺ", INK, 70), 360, 830, st, pop(t, 22.5, out), -3, key=12)
    slam(c, "t_at", "ẢO TƯỞNG", RED, 1580, 330, st, t, 25.3, 104, 5)
    write(c, "về sự bình đẳng", 1580, 460, t, 26.2, 0.5, 64, WHITE, "c", t1=out)
    place(c, S("door", (240, 400), door_fn, seed=133, border=8), 1480, 740, st, pop(t, 28.5, out), -3, key=13)
    place(c, tag("t_ch", "cơ hội cho MỌI NGƯỜI?", TEAL, 58), 1640, 980, st, pop(t, 29.2, out), 3, key=14)


TERMS = [("Race", TEAL, 57.4, 330, 300, -6), ("Ethnicity", CORAL, 58.2, 1600, 260, 5),
         ("Nationality", INK, 59.5, 380, 620, 4), ("Indigeneity", PURPLE, 60.3, 1570, 580, -4)]


def ov_terms(c, t, st):
    out = 63.9
    for k, col, t0, x, y, rot in TERMS:
        place(c, tag("tm_" + k, k, col, 92), x, y, st, pop(t, t0, out), rot, key=hash(k) % 30)
    slam(c, "t_nhan", "không chỉ là NHÃN GỌI có sẵn", RED, 960, 930, st, t, 62.5, 70, -2)


def ov_society(c, t, st):
    out = 73.5
    place(c, S("magn", (330, 330), magnifier_fn, seed=134, border=8), 360, 420, st, pop(t, 71.4, out), 8, key=20)
    place(c, tag("t_nm", "được NHẤN MẠNH", CORAL, 66), 360, 700, st, pop(t, 71.7, out), -3, key=21)
    slam(c, "t_xhqd", "XÃ HỘI QUYẾT ĐỊNH", RED, 1500, 360, st, t, 70.2, 80, 3)
    place(c, tag("t_yn", "mang ý nghĩa gì?", INK, 66), 1560, 620, st, pop(t, 73.0, out), -2, key=22)


def ov_hidden(c, t, st):
    framed(c, ph("../../v5/assets/vnn-2.jpg", 520, 360), 380, 380, st, pop(t, 94.3, 98.2), -4, key=30)
    place(c, tag("t_vd", "vai diễn “tích cực”", GREEN, 64), 380, 650, st, pop(t, 94.6, 98.2), 3, key=31)
    framed(c, ph("whiten_1.jpg", 380, 480), 1570, 420, st, pop(t, 96.8), 4, key=32)
    place(c, tag("t_ved", "tiêu chuẩn VẺ ĐẸP", PINK, 64, DARK), 1570, 760, st, pop(t, 97.1), -3, key=33)
    place(c, S("book", (310, 360), book_fn, seed=121, border=8), 380, 460, st, pop(t, 98.5), -4, key=34)
    place(c, tag("t_qd", "quy định “công bằng”", INK, 60), 380, 750, st, pop(t, 98.8), 3, key=35)


# ---------- full-screen scenes ----------
def sc_stars(t, st):
    c = background(MUST, 40).copy().convert("RGBA")
    write(c, "... trở nên thành công như", 960, 90, t, 3.7, 1.0, 72, NAVY, "c")
    for i, (img, name, t0, x, rot) in enumerate([("obama_0.jpg", "Barack Obama", 5.0, 360, -3),
                                                   ("oprah_1.jpg", "Oprah Winfrey", 5.8, 960, 2),
                                                   ("beyonce_5.jpg", "Beyoncé", 7.3, 1560, -2)]):
        framed(c, ph(img, 420, 480), x, 470, st, pop(t, t0, dur=0.35), rot, key=40 + i)
        place(c, tag("n_" + name, name, INK, 64), x, 790, st, pop(t, t0 + 0.2), -rot, key=43 + i)
    slam(c, "t_hmtc", "HÌNH MẪU TÍCH CỰC", RED, 760, 960, st, t, 9.0, 80, -3)
    place(c, tag("t_pbrc", "phá bỏ rào cản", TEAL, 64), 1440, 970, st, pop(t, 10.2), 4, key=46)
    confetti(c, t, 8.6, 1)
    return c


def sc_media(t, st):
    c = background(NAVY, 41, True).copy().convert("RGBA")
    news_ph = ph("crowd_1.jpg", 680, 380)
    place(c, S("newspaper", (760, 900), newspaper_fn(news_ph), seed=135, border=8), 480, 560, st, 0.95 * pop(t, 12.3, dur=0.4), -4, key=50)
    tv_screen(c, ph("orally_1.jpg", 740, 440), 1400, 470, st, pop(t, 12.8))
    place(c, tag("t_tt", "TRUYỀN THÔNG", CORAL, 78), 1400, 870, st, pop(t, 13.2), 3, key=51)
    place(c, tag("t_mc", "“minh chứng”", MUST, 64, DARK), 1060, 110, st, pop(t, 14.5), -4, key=52)
    slam(c, "t_hct", "XÃ HỘI HẬU CHỦNG TỘC?", RED, 1180, 990, st, t, 18.0, 70, -2)
    return c


def sc_climb(t, st):
    c = background(PINK, 42).copy().convert("RGBA")
    place(c, S("stairs2", (850, 620), stairs2_fn, seed=136, border=8), 700, 680, st, pop(t, 30.1), 0, key=60)
    k = ease_io(clamp((t - 31.5) / 3.6))
    step = min(4, int(k * 5))
    x, y = 360 + step * 170, 560 - step * 110
    place(c, people()[3], x, y - 40 * abs(math.sin(k * 15)), st, 0.5 * pop(t, 30.4), 0, key=61)
    place(c, S("oscar", (160, 310), oscar_fn, seed=100, border=8), 1120, 180, st, 0.7 * pop(t, 30.6), 6, key=62)
    place(c, tag("t_tn", "TÀI NĂNG", TEAL, 86), 1560, 300, st, pop(t, 31.8), -4, key=63)
    place(c, tag("t_cc", "+ CHĂM CHỈ", CORAL, 86), 1560, 500, st, pop(t, 33.0), 3, key=64)
    slam(c, "t_actc", "= AI CŨNG THÀNH CÔNG?", RED, 1380, 760, st, t, 34.5, 78, -3)
    return c


def sc_cheer(t, st):
    c = background(CORAL, 43).copy().convert("RGBA")
    write(c, "Trong một cộng đồng thiểu số...", 960, 80, t, 36.9, 1.0, 72, WHITE, "c")
    framed(c, ph("orally_0.jpg", 760, 480), 520, 470, st, pop(t, 37.3, dur=0.4), -3, key=70)
    framed(c, ph("bobama_2.jpg", 560, 420), 1440, 420, st, pop(t, 38.8, dur=0.4), 4, key=71)
    place(c, tag("t_1cn", "1 cá nhân thành công", INK, 66), 1440, 760, st, pop(t, 40.3), -3, key=72)
    slam(c, "t_th", "TUNG HÔ!", MUST, 760, 900, st, t, 41.9, 120, -5, DARK)
    confetti(c, t, 41.8, 2, 60)
    return c


def sc_question(t, st):
    # the success story becomes a stick to question everyone else still facing barriers
    c = background(TEAL, 44).copy().convert("RGBA")
    write(c, "Dư luận biến họ thành “cái cớ”...", 960, 80, t, 42.7, 1.0, 72, WHITE, "c")
    framed(c, ph("obama_0.jpg", 300, 360), 330, 450, st, pop(t, 42.8), -4, key=80)
    place(c, comment("cm1", "“Người ta làm được, sao bạn không?”"), 1040, 260, st, pop(t, 43.8), -2, key=81)
    slam(c, "t_cv", "CHẤT VẤN", RED, 330, 800, st, t, 45.1, 88, -4)
    framed(c, ph("blm_1.jpg", 720, 460), 1320, 620, st, pop(t, 45.6, dur=0.4), 3, key=82)
    place(c, S("wall", (720, 280), wall_fn, seed=137, border=8), 1320, 930, st, pop(t, 47.6), 0, key=83)
    place(c, tag("t_rc", "RÀO CẢN XÃ HỘI", DARK, 66), 1320, 930, st, pop(t, 47.8), -2, key=84)
    return c


LETTERS = [("lt1", "“Tại bạn LƯỜI thôi!”", 49.8, 470, 330, -4), ("lt2", "“Không đủ giỏi thì đừng than”", 52.0, 1350, 300, 3),
           ("lt3", "“Cố gắng hơn đi!”", 53.3, 560, 640, 2)]


def sc_blame(t, st):
    c = background(PURPLE, 45).copy().convert("RGBA")
    write(c, "Quy kết...", 960, 80, t, 48.7, 0.6, 76, WHITE, "c")
    r = random.Random(7)
    for i in range(7):
        x0, y0 = r.uniform(100, 1800), r.uniform(200, 1000)
        fly = clamp((t - 48.8 - i * 0.18) / 0.5)
        if fly > 0:
            place(c, S("env", (260, 170), envelope_fn, seed=138, border=6), x0 + (1 - fly) * 600, y0 - (1 - fly) * 300, st,
                  0.8, r.uniform(-25, 25), key=90 + i)
    for k, text, t0, x, y, rot in LETTERS:
        place(c, comment(k, text, "bình luận"), x, y, st, pop(t, t0), rot, key=hash(k) % 30)
    slam(c, "t_lb", "LƯỜI BIẾNG", RED, 1450, 560, st, t, 50.0, 84, -6)
    slam(c, "t_tnl", "THIẾU NĂNG LỰC", RED, 1380, 760, st, t, 52.2, 80, 4)
    slam(c, "t_dd", "ĐẠO ĐỨC?", RED, 700, 900, st, t, 53.6, 84, -3)
    return c


DIFFS = [("ngoại hình", "../../v4/assets/eth.webp", 65.7, TEAL), ("văn hóa", "../../v6/assets/kapa_35.jpg", 66.3, CORAL),
         ("nguồn gốc", "../../v4/assets/nat.jpg", 67.3, INK), ("đất đai", "../../v4/assets/ind.png", 68.5, GREEN)]


def sc_diffs(t, st):
    c = background((243, 214, 150), 46).copy().convert("RGBA")
    write(c, "Con người có những khác biệt về...", 960, 80, t, 64.2, 1.0, 72, NAVY, "c")
    for i, (w, path, t0, col) in enumerate(DIFFS):
        x = 250 + i * 473
        framed(c, ph(path, 400, 300), x, 470, st, pop(t, t0, dur=0.35), (-3, 2, -2, 3)[i], key=100 + i)
        place(c, tag("d_" + w, w, col, 70), x, 740, st, pop(t, t0 + 0.15), (3, -3, 2, -2)[i], key=104 + i)
    return c


def sc_tv(t, st):
    c = background(NAVY, 47, True).copy().convert("RGBA")
    write(c, "Truyền thông khắc họa nhóm người qua...", 960, 75, t, 74.9, 1.2, 70, WHITE, "c")
    cur = ph("../../v5/assets/vnn-2.jpg", 740, 440) if t < 80.4 else ph("../../v5/assets/sots.jpg", 740, 440)
    tv_screen(c, cur, 700, 470, st, pop(t, 73.8))
    place(c, tag("t_cg", "cách gọi nhân vật", CORAL, 64), 1500, 300, st, pop(t, 79.1), -3, key=110)
    place(c, tag("t_kc", "cách kể chuyện", TEAL, 64), 1500, 460, st, pop(t, 80.3), 3, key=111)
    place(c, tag("t_ll", "LẶP LẠI hình ảnh", MUST, 70, DARK), 1500, 620, st, pop(t, 81.1), -2, key=112)
    # the same image repeated along a film strip
    for i in range(4):
        if t > 81.3 + i * 0.15:
            framed(c, ph("../../v5/assets/vnn-2.jpg", 260, 170), 250 + i * 330, 900, st, 1.0, (-2, 2, -1, 1)[i], key=113 + i)
    slam(c, "t_dbt", "“ĐIỀU BÌNH THƯỜNG”", RED, 1500, 900, st, t, 85.3, 78, -4)
    return c


def sc_hate(t, st):
    c = background(CORAL, 48).copy().convert("RGBA")
    write(c, "Phân biệt chủng tộc", 700, 250, t, 88.3, 0.7, 92, WHITE, "c")
    write(c, "không phải lúc nào cũng là", 700, 380, t, 89.1, 1.0, 70, NAVY, "c")
    place(c, tag("t_cgck", "căm ghét CÔNG KHAI", RED, 90), 700, 560, st, pop(t, 90.7), -3, key=120)
    place(c, S("angry", (280, 280), angry_fn, seed=110, border=10), 1480, 480, st, pop(t, 90.8), 8, key=121)
    blm = ph("blm_0.jpg", 520, 330)
    framed(c, blm, 1480, 850, st, pop(t, 87.2), 4, key=122)
    return c


TL = [(0.0, 3.5, "sp", ov_open), (3.5, 12.15, "fs", sc_stars), (12.15, 18.95, "fs", sc_media),
      (18.95, 30.0, "sp", ov_single), (30.0, 35.65, "fs", sc_climb), (35.65, 42.45, "fs", sc_cheer),
      (42.45, 48.55, "fs", sc_question), (48.55, 55.25, "fs", sc_blame), (55.25, 64.0, "sp", ov_terms),
      (64.0, 69.25, "fs", sc_diffs), (69.25, 73.65, "sp", ov_society), (73.65, 86.7, "fs", sc_tv),
      (86.7, 91.75, "fs", sc_hate), (91.75, 999, "sp", ov_hidden)]
WIPE = 0.45
_cache = {}


def seg_at(t):
    for i, sg in enumerate(TL):
        if sg[0] <= t < sg[1]:
            return i
    return len(TL) - 1


def render_seg(i, t, st, raw):
    kind, fn = TL[i][2], TL[i][3]
    if kind == "fs":
        key = (i, st)
        if key not in _cache:
            if len(_cache) > 4:
                _cache.clear()
            _cache[key] = fn(t, st).convert("RGB")
        return _cache[key]
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fn(c, t, st)
    f = apply_cam(raw, t).convert("RGBA")
    f.alpha_composite(c)
    return f.convert("RGB")


def frame_at(t, raw):
    st = int(t * ANIM)
    for j in range(1, len(TL)):
        tb = TL[j][0]
        if tb - WIPE / 2 <= t < tb + WIPE / 2 and not (TL[j - 1][2] == "sp" and TL[j][2] == "sp"):
            p = ease_io((t - (tb - WIPE / 2)) / WIPE)
            return R.torn_wipe(render_seg(j - 1, t, st, raw).copy(), render_seg(j, t, st, raw), p, j)
    return render_seg(seg_at(t), t, st, raw)


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
        pout.stdin.write(frame_at(n / FPS, Image.frombytes("RGB", (W, H), b)).tobytes())
        n += 1
        if n % 90 == 0:
            print(f"t={n / FPS:.1f}", flush=True)
    pout.stdin.close()
    pout.wait()


if __name__ == "__main__":
    main()
