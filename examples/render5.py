# Edit of segment 4: the source picture is black, so every beat is a full-screen paper collage
# (drawings + archive photos/clips of Hattie McDaniel) timed to the voice.
import sys, math, random, subprocess, functools
from PIL import Image, ImageDraw
import render as R
from render import (W, H, ANIM, NAVY, MUST, PINK, CORAL, TEAL, CREAM, INK, RED, WOOD, PURPLE, GREEN, DARK,
                    SKINS, HAIRS, S, Label, asset, place, pop, write, text_c, clamp, ease_io, background, people)
from render2 import tag, scrim
from render4 import framed, photo

SRC = "input.mp4"  # path to the source video
OUT = sys.argv[1] if len(sys.argv) > 1 else "output.mp4"
FPS = 30
T_END = 69.2
WHITE = (252, 248, 236)
A = "v5/assets/"


class Clip:
    """sequential reader for a pre-cut 960x720 clip that starts playing at scene time t0."""
    def __init__(self, path, t0, size=(960, 720)):
        self.path, self.t0, self.size = path, t0, size
        self.p, self.idx, self.img = None, -1, None

    def get(self, t):
        w, h = self.size
        if self.p is None:
            self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", self.path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                      stdout=subprocess.PIPE)
        f = max(0, int((t - self.t0) * FPS))
        while self.idx < f:
            b = self.p.stdout.read(w * h * 3)
            if len(b) < w * h * 3:
                break
            self.idx += 1
            self.img = Image.frombytes("RGB", (w, h), b)
        return self.img if self.img is not None else Image.new("RGB", (w, h))


CLIPS = {"stage": Clip("v5/clips/oscar_stage.mp4", 14.2), "speech": Clip("v5/clips/oscar_speech.mp4", 30.2),
         "tray": Clip("v5/clips/gw_tray.mp4", 38.8), "window": Clip("v5/clips/gw_window.mp4", 43.3),
         "lc": Clip("v5/clips/lc.mp4", 60.4)}


# ---------- drawings ----------
def oscar_fn(d, img, p):
    gold, dk = (226, 180, 70), (170, 128, 40)
    d.ellipse([p + 60, p, p + 100, p + 40], fill=gold)
    d.polygon([(p + 50, p + 44), (p + 110, p + 44), (p + 98, p + 250), (p + 62, p + 250)], fill=gold)
    d.line([(p + 80, p + 60), (p + 80, p + 240)], fill=dk, width=4)
    d.rectangle([p + 40, p + 250, p + 120, p + 275], fill=DARK)
    d.rectangle([p + 25, p + 275, p + 135, p + 310], fill=(60, 50, 50))


def hattie_fn():
    return R.person_fn(SKINS[4], (28, 22, 22), CORAL, 0)


def cinema_fn(d, img, p):
    d.rectangle([p, p + 120, p + 900, p + 640], fill=(150, 52, 60))
    d.polygon([(p - 20, p + 120), (p + 450, p), (p + 920, p + 120)], fill=(120, 40, 50))
    d.rectangle([p + 120, p + 160, p + 780, p + 330], fill=MUST)
    for x in range(p + 130, p + 780, 40):
        d.ellipse([x, p + 166, x + 14, p + 180], fill=(255, 250, 220))
        d.ellipse([x, p + 310, x + 14, p + 324], fill=(255, 250, 220))
    f1, f2 = R.font(84), R.font(52)
    for txt, fnt, y in (("PREMIERE", f1, p + 186), ("ATLANTA – 1939", f2, p + 262)):
        bb = fnt.getbbox(txt)
        d.text((p + 450 - (bb[2] - bb[0]) / 2 - bb[0], y), txt, font=fnt, fill=DARK)
    d.rectangle([p + 360, p + 400, p + 540, p + 640], fill=(40, 30, 36))
    d.rectangle([p + 380, p + 420, p + 520, p + 640], fill=(250, 214, 120))
    for x in (p + 60, p + 640):
        d.rectangle([x, p + 400, x + 200, p + 520], fill=(250, 226, 160))


def rope_fn(d, img, p):
    for x in (p + 10, p + 370):
        d.rectangle([x, p + 40, x + 22, p + 230], fill=(200, 170, 70))
        d.ellipse([x - 8, p + 20, x + 30, p + 58], fill=(220, 190, 90))
    d.arc([p + 20, p + 20, p + 380, p + 170], 20, 160, fill=RED, width=16)


def hotel_fn(d, img, p):
    d.rectangle([p + 60, p + 110, p + 640, p + 800], fill=(236, 214, 176))
    d.rectangle([p + 20, p + 80, p + 680, p + 130], fill=(160, 110, 70))
    d.rectangle([p + 200, p, p + 500, p + 90], fill=NAVY)
    fnt = R.font(70)
    bb = fnt.getbbox("HOTEL")
    d.text((p + 350 - (bb[2] - bb[0]) / 2 - bb[0], p + 6), "HOTEL", font=fnt, fill=MUST)
    for r in range(4):
        for c in range(5):
            x, y = p + 100 + c * 108, p + 160 + r * 120
            d.rectangle([x, y, x + 70, y + 80], fill=(120, 170, 200))
    d.rectangle([p + 270, p + 640, p + 430, p + 800], fill=(90, 60, 40))
    d.rectangle([p + 240, p + 610, p + 460, p + 640], fill=RED)


def letter_fn(d, img, p):
    d.rectangle([p, p, p + 420, p + 280], fill=(250, 244, 226))
    d.polygon([(p, p), (p + 210, p + 150), (p + 420, p)], fill=(232, 220, 190))
    d.line([(p, p), (p + 210, p + 150), (p + 420, p)], fill=(190, 170, 130), width=4)


def table_long_fn(d, img, p):
    d.rounded_rectangle([p, p, p + 1000, p + 200], 40, fill=(250, 250, 244))
    for x in range(p + 80, p + 1000, 140):
        d.ellipse([x, p + 70, x + 60, p + 130], fill=(214, 206, 196))
    d.ellipse([p + 470, p + 40, p + 530, p + 100], fill=(240, 150, 170))


def table_small_fn(d, img, p):
    d.ellipse([p, p, p + 240, p + 160], fill=(250, 250, 244))
    d.ellipse([p + 90, p + 50, p + 150, p + 110], fill=(214, 206, 196))


def smile_fn(d, img, p):
    d.ellipse([p, p, p + 300, p + 300], fill=MUST)
    d.ellipse([p + 85, p + 90, p + 115, p + 140], fill=DARK)
    d.ellipse([p + 185, p + 90, p + 215, p + 140], fill=DARK)
    d.arc([p + 60, p + 110, p + 240, p + 250], 15, 165, fill=DARK, width=14)


def chain_fn(d, img, p):
    for i in range(7):
        x = p + i * 95
        if i % 2 == 0:
            d.ellipse([x, p, x + 120, p + 70], outline=(120, 120, 130), width=16)
        else:
            d.ellipse([x + 30, p + 18, x + 90, p + 52], outline=(150, 150, 160), width=14)


def angry_fn(d, img, p):
    d.ellipse([p, p, p + 280, p + 280], fill=RED)
    d.line([(p + 60, p + 80), (p + 125, p + 115)], fill=DARK, width=16)
    d.line([(p + 220, p + 80), (p + 155, p + 115)], fill=DARK, width=16)
    d.ellipse([p + 85, p + 120, p + 115, p + 155], fill=DARK)
    d.ellipse([p + 165, p + 120, p + 195, p + 155], fill=DARK)
    d.arc([p + 80, p + 180, p + 200, p + 260], 200, 340, fill=DARK, width=14)


def slam(c, key, text, color, x, y, st, t, t0, size, rot, tcol=(255, 255, 255)):
    """label that drops in huge and lands hard."""
    if t < t0:
        return
    p = clamp((t - t0) / 0.18)
    place(c, tag(key, text, color, size, tcol), x, y, st, 3.0 - 2.0 * p * p, rot, jitter=p >= 1, key=hash(key) % 40)


def dashed(c, x, y0, y1, t, t0, dur=0.6, color=RED):
    if t < t0:
        return
    p = clamp((t - t0) / dur)
    d = ImageDraw.Draw(c)
    y = y0
    while y < y0 + (y1 - y0) * p:
        d.line([(x, y), (x + 3, min(y + 34, y1))], fill=color + (255,), width=12)
        y += 58


# ---------- scenes (t = source time) ----------
def sc_intro(t, st):
    c = background(NAVY, 20, True).copy().convert("RGBA")
    write(c, "1940", 290, 170, t, 0.1, 0.6, 210, MUST, "c")
    place(c, S("oscar", (160, 310), oscar_fn, seed=100, border=8), 290, 640, st, 1.35 * pop(t, 0.9), -4, key=1)
    framed(c, photo(A + "hattie.jpg", 380, 490), 760, 450, st, pop(t, 2.4, dur=0.4), -3, key=2)
    place(c, tag("t_hat", "Hattie McDaniel", INK, 72), 760, 830, st, pop(t, 2.6), 2, key=3)
    place(c, tag("t_mam", "vai MAMMY", CORAL, 70), 760, 960, st, pop(t, 5.1), -3, key=4)
    framed(c, photo(A + "vnn.jpg", 520, 460), 1470, 420, st, pop(t, 6.0, dur=0.4), 3, key=5)
    place(c, tag("t_first", "NGƯỜI DA ĐEN ĐẦU TIÊN", RED, 62), 1470, 800, st, pop(t, 6.3), -3, key=6)
    place(c, tag("t_osc", "giành giải OSCAR", MUST, 74, DARK), 1470, 940, st, pop(t, 7.9), 4, key=7)
    return c


def sc_premiere(t, st):
    c = background(PURPLE, 21).copy().convert("RGBA")
    place(c, S("cinema", (900, 640), cinema_fn, seed=101, border=10), 760, 560, st, pop(t, 9.1, dur=0.4), -1, key=10)
    ps = people()
    for i, pi in enumerate((0, 1)):
        walk = ease_io(clamp((t - 10.6 - i * 0.4) / 2.6))
        x = 380 + i * 110 + (760 - 380 - i * 110) * walk
        place(c, ps[pi], x, 800, st, 0.55 * pop(t, 9.6 + i * 0.2) * (1 - 0.5 * walk), 0, key=11 + i)
    place(c, S("hattie_p", (200, 340), hattie_fn(), seed=102), 1560, 720, st, 0.8 * pop(t, 9.9), 0, key=13)
    place(c, S("rope", (400, 240), rope_fn, seed=103, border=6), 1560, 830, st, pop(t, 10.1), 0, key=14)
    slam(c, "t_nv", "KHÔNG ĐƯỢC VÀO", RED, 1580, 450, st, t, 10.1, 68, -4)
    place(c, tag("t_dvt", "diễn viên da trắng", INK, 54), 520, 980, st, pop(t, 13.4), 3, key=15)
    return c


def sc_stage(t, st):
    c = background(NAVY, 22, True).copy().convert("RGBA")
    write(c, "Lễ trao giải Oscar – 1940", 960, 80, t, 14.5, 0.8, 80, WHITE, "c")
    framed(c, CLIPS["stage"].get(t).resize((1000, 750), Image.BILINEAR), 960, 590, st, 1.0, -1.5, key=20)
    return c


def sc_hotel(t, st):
    c = background(TEAL, 23).copy().convert("RGBA")
    write(c, "Khách sạn tổ chức lễ trao giải", 640, 70, t, 18.8, 0.7, 64, WHITE, "c")
    place(c, S("hotel", (700, 800), hotel_fn, seed=104, border=10), 640, 600, st, 0.92 * pop(t, 18.8, dur=0.4), 0, key=21)
    swing = 5 * math.sin((t - 19.0) * 5) * clamp(1 - (t - 19.0) / 1.6) if t > 19 else 0
    slam(c, "t_wo", "WHITES ONLY", DARK, 640, 780, st, t, 19.0, 96, swing)
    place(c, tag("t_kd", "không đón khách da đen", RED, 60), 1460, 300, st, pop(t, 20.7), -4, key=22)
    write(c, "nhà sản xuất phải xin...", 1460, 470, t, 22.5, 0.7, 60, WHITE, "c")
    place(c, S("letter", (420, 280), letter_fn, seed=105, border=8), 1460, 700, st, pop(t, 22.8), 5, key=23)
    slam(c, "t_dc", "ĐẶC CÁCH", RED, 1480, 720, st, t, 23.5, 90, -12)
    return c


def sc_table(t, st):
    c = background(WOOD, 24).copy().convert("RGBA")
    write(c, "Dù là người chiến thắng...", 960, 80, t, 25.7, 0.8, 76, WHITE, "c")
    ps = people()
    order = (0, 1, 0, 1, 0, 1)
    for i, pi in enumerate(order):
        place(c, ps[pi], 290 + i * 180, 400, st, 0.42 * pop(t, 26.0 + i * 0.08), 0, key=30 + i)
    place(c, S("table_long", (1000, 200), table_long_fn, seed=106, border=8), 740, 560, st, pop(t, 25.9), 0, key=36)
    for i, pi in enumerate(order):
        place(c, ps[pi], 290 + i * 180, 740, st, 0.42 * pop(t, 26.2 + i * 0.08), 0, key=37 + i)
    place(c, S("hattie_p", (200, 340), hattie_fn(), seed=102), 1640, 450, st, 0.55 * pop(t, 27.3), 0, key=43)
    place(c, S("table_small", (240, 160), table_small_fn, seed=107, border=8), 1640, 600, st, pop(t, 27.3), 0, key=44)
    place(c, S("oscar", (160, 310), oscar_fn, seed=100, border=8), 1740, 540, st, 0.45 * pop(t, 27.5), 0, key=45)
    dashed(c, 1400, 220, 900, t, 28.6)
    slam(c, "t_br", "BÀN RIÊNG", RED, 1640, 870, st, t, 28.0, 96, -5)
    return c


def sc_equal(t, st):
    # audience question over Hattie's acceptance speech: text top + bottom on dark gradients
    fr = CLIPS["speech"].get(t).resize((1920, 1440), Image.BILINEAR).crop((0, 150, 1920, 1230))
    c = R.texturize(fr, 3, 0.05).convert("RGBA")
    c.alpha_composite(scrim(True))
    c.alpha_composite(scrim(False))
    write(c, "Chúng ta có thể gọi đó là", 960, 62, t, 30.7, 0.6, 58, WHITE, "c")
    write(c, "BÌNH ĐẲNG không?", 960, 170, t, 31.9, 0.5, 110, MUST, "c")
    write(c, "được công nhận tài năng trên sân khấu...", 960, 960, t, 33.2, 0.9, 70, WHITE, "c", t1=35.2)
    write(c, "nhưng MÀU DA quyết định", 960, 900, t, 35.4, 0.6, 76, MUST, "c")
    write(c, "được bước vào đâu, ngồi cạnh ai", 960, 1000, t, 37.3, 0.8, 76, WHITE, "c")
    return c


def sc_tray(t, st):
    c = background(CORAL, 25).copy().convert("RGBA")
    write(c, "Gone with the Wind (1939)", 960, 75, t, 39.2, 0.7, 76, WHITE, "c")
    framed(c, CLIPS["tray"].get(t).resize((920, 690), Image.BILINEAR), 960, 590, st, 1.0, 1.5, key=50)
    slam(c, "t_nh", "NGƯỜI HẦU", RED, 1600, 900, st, t, 42.0, 96, -6)
    place(c, tag("t_gdt", "cho gia đình da trắng", INK, 58), 360, 900, st, pop(t, 42.5), 4, key=51)
    return c


def sc_window(t, st):
    c = background(MUST, 26).copy().convert("RGBA")
    write(c, "Mammy không hề yếu thế", 700, 75, t, 44.4, 0.7, 76, NAVY, "c")
    framed(c, CLIPS["window"].get(t).resize((880, 660), Image.BILINEAR), 700, 590, st, 1.0, -1.5, key=52)
    place(c, tag("t_mm", "MẠNH MẼ", TEAL, 84), 1560, 330, st, pop(t, 46.3), -5, key=53)
    place(c, tag("t_tn", "CÓ TIẾNG NÓI", CORAL, 78), 1560, 530, st, pop(t, 47.1), 4, key=54)
    place(c, tag("t_tm", "trách mắng Scarlett", RED, 66), 1560, 730, st, pop(t, 48.3), -3, key=55)
    return c


def sc_happy(t, st):
    c = background(PINK, 27).copy().convert("RGBA")
    framed(c, photo(A + "vnn-1.jpg", 760, 440), 520, 460, st, pop(t, 49.7, dur=0.4), -4, key=60)
    place(c, S("smile", (300, 300), smile_fn, seed=108, border=10), 1420, 380, st, pop(t, 51.2), 6 * math.sin(t * 4), key=61)
    slam(c, "t_happy", "“HAPPY”", MUST, 1420, 640, st, t, 51.5, 110, -6, DARK)
    place(c, S("chain", (700, 70), chain_fn, seed=109, border=6), 960, 860, st, pop(t, 52.2), 2, key=62)
    place(c, tag("t_nl", "với việc làm NÔ LỆ?", RED, 70), 960, 980, st, pop(t, 52.4), -2, key=63)
    return c


def sc_hate(t, st):
    c = background(NAVY, 28, True).copy().convert("RGBA")
    write(c, "Và nếu vậy, phân biệt chủng tộc", 960, 220, t, 53.6, 1.0, 84, WHITE, "c")
    write(c, "có nhất thiết phải là", 960, 350, t, 55.8, 0.6, 84, WHITE, "c")
    place(c, S("angry", (280, 280), angry_fn, seed=110, border=10), 1560, 640, st, pop(t, 57.2), 8, key=64)
    slam(c, "t_hate", "SỰ CĂM GHÉT?", RED, 880, 640, st, t, 57.3, 130, -4)
    return c


ROLES = [("sots", A + "sots.jpg", 59.4, ("McDaniel đóng vai người hầu", "trong phim Song of the South", "của Disney")),
         ("lc", None, 60.5, ("McDaniel đóng vai người hầu", "Mom Beck trong phim", "The Little Colonel (1935)")),
         ("alice", A + "alice.jpg", 61.6, ("McDaniel trong vai người hầu", "Malena Burns trong phim", "Alice Adams (1935)"))]


def sc_roles(t, st):
    c = background((243, 214, 150), 29).copy().convert("RGBA")
    write(c, "Hay nó tồn tại TINH VI hơn nhiều...", 960, 85, t, 58.6, 1.0, 84, NAVY, "c")
    for i, (k, path, t0, cap) in enumerate(ROLES):
        x = 330 + i * 630
        media = CLIPS["lc"].get(t).resize((480, 360), Image.BILINEAR) if path is None else photo(path, 500, 360)
        framed(c, media, x, 400, st, pop(t, t0, dur=0.4), (-3, 2, -2)[i], key=70 + i)
        for j, ln in enumerate(cap):
            write(c, ln, x, 690 + j * 62, t, t0 + 0.3 + j * 0.3, 0.6, 44, NAVY if j == 0 else RED, "c")
    # the closing question takes over the collage
    if t >= 64.0:
        a = clamp((t - 64.0) / 0.5)
        dim = Image.new("RGBA", (W, H), (22, 18, 40, int(200 * a)))
        c.alpha_composite(dim)
        write(c, "Khi xã hội đã QUEN với bất bình đẳng", 960, 430, t, 64.1, 1.0, 84, WHITE, "c")
        write(c, "đến mức KHÔNG CÒN NHẬN RA?", 960, 590, t, 66.7, 0.8, 110, MUST, "c")
    return c


TL = [(0.0, 9.0, sc_intro), (9.0, 14.3, sc_premiere), (14.3, 18.65, sc_stage), (18.65, 25.45, sc_hotel),
      (25.45, 30.45, sc_table), (30.45, 38.95, sc_equal), (38.95, 43.5, sc_tray), (43.5, 49.5, sc_window),
      (49.5, 53.35, sc_happy), (53.35, 58.4, sc_hate), (58.4, 99, sc_roles)]
LIVE = {sc_stage, sc_equal, sc_tray, sc_window, sc_roles}
WIPE = 0.45
_cache = {}


def seg_at(t):
    for i, sg in enumerate(TL):
        if sg[0] <= t < sg[1]:
            return i
    return len(TL) - 1


def render_seg(i, t, st):
    fn = TL[i][2]
    if fn in LIVE:
        return fn(t, st).convert("RGB")
    key = (i, st)
    if key not in _cache:
        if len(_cache) > 4:
            _cache.clear()
        _cache[key] = fn(t, st).convert("RGB")
    return _cache[key]


def frame_at(t):
    st = int(t * ANIM)
    for j in range(1, len(TL)):
        tb = TL[j][0]
        if tb - WIPE / 2 <= t < tb + WIPE / 2:
            p = ease_io((t - (tb - WIPE / 2)) / WIPE)
            return R.torn_wipe(render_seg(j - 1, t, st).copy(), render_seg(j, t, st), p, j)
    return render_seg(seg_at(t), t, st)


def main():
    pout = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                             "-i", "-", "-i", SRC, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], stdin=subprocess.PIPE)
    for n in range(int(T_END * FPS)):
        pout.stdin.write(frame_at(n / FPS).tobytes())
        if n % 90 == 0:
            print(f"t={n / FPS:.1f}", flush=True)
    pout.stdin.close()
    pout.wait()


if __name__ == "__main__":
    main()
