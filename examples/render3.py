# Edit of segment 2 in the same paper cut-out style as đoạn 1 (v2).
import sys, math, subprocess, functools, glob, random
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import render as R
from render import (W, H, ANIM, NAVY, MUST, PINK, CORAL, TEAL, CREAM, INK, RED, WOOD, PURPLE, GREEN, DARK,
                    SKINS, HAIRS, SHIRTS, S, Label, asset, place, pop, write, note_fn, text_c, clamp, ease_io,
                    background, people)
import render2 as V2
from render2 import arrow, tag, scrim

SRC = "input.mp4"  # path to the source video
OUT = sys.argv[1] if len(sys.argv) > 1 else "output.mp4"
FPS = 30
T_END = 67.45

CAM = [  # (time, zoom, focus x, focus y)
    (0.0, 1.25, 1000, 560), (3.8, 1.32, 1000, 540), (3.95, 1.12, 1000, 600), (11.0, 1.12, 1000, 600),
    (11.15, 1.2, 1000, 570), (17.6, 1.26, 1000, 560),
    (43.4, 1.12, 1000, 600), (47.3, 1.18, 1000, 580), (47.45, 1.28, 1000, 530), (49.8, 1.28, 1000, 530),
    (49.95, 1.14, 1000, 600), (53.5, 1.2, 1000, 580),
    (58.9, 1.0, 960, 540),
]


def cam(s):
    for (t0, z0, x0, y0), (t1, z1, x1, y1) in zip(CAM, CAM[1:]):
        if t0 <= s < t1:
            p = ease_io((s - t0) / (t1 - t0))
            return z0 + (z1 - z0) * p, x0 + (x1 - x0) * p, y0 + (y1 - y0) * p
    return CAM[-1][1:]


def apply_cam(img, s):
    z, fx, fy = cam(s)
    if z <= 1.001:
        return img
    x0, y0, cw, ch = V2.crop_origin(z, fx, fy)
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))


def strike(c, cx, cy, text, size, t, t0, dur=0.3):
    """red crayon line crossing out a written word"""
    if t < t0:
        return
    w = text_c(text, size, INK).width
    p = ease_io(clamp((t - t0) / dur))
    x0, x1 = cx - w / 2 - 12, cx + w / 2 + 12
    d = ImageDraw.Draw(c)
    d.line([(x0, cy + 8), (x0 + (x1 - x0) * p, cy + 8 - 14 * p)], fill=RED + (255,), width=11)


def overlay(frame, fn, t, st):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fn(c, t, st)
    frame = frame.convert("RGBA")
    frame.alpha_composite(c)
    return frame.convert("RGB")


# ---------- speaker overlays ----------
def ov_intro(c, t, st):
    # "Vậy Race hay còn gọi là chủng tộc, thực chất là gì?" — text top + bottom over dark gradients
    a = clamp((t - 0.2) / 0.3) * (1 - clamp((t - 3.8) / 0.15))
    if a <= 0:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.alpha_composite(scrim(True))
    layer.alpha_composite(scrim(False))
    white = (252, 248, 236)
    write(layer, "Vậy, RACE hay còn gọi là", W // 2, 70, t, 0.5, 0.7, 60, white, "c")
    write(layer, "CHỦNG TỘC", W // 2, 175, t, 2.4, 0.4, 100, MUST, "c")
    write(layer, "thực chất là gì?", W // 2, 960, t, 3.0, 0.5, 110, white, "c")
    if a < 1:
        layer.putalpha(layer.split()[3].point(lambda v: int(v * a)))
    c.alpha_composite(layer)


def ov_define(c, t, st):
    # definition built line by line on the right; "skin pigmentation" on the left
    out = 17.45
    s = pop(t, 4.0, out)
    place(c, S("n2_def", (600, 640), note_fn(600, 640, spiral=True), seed=71), 1590, 500, st, s, 2, key=2)
    if s > 0.9:
        x = 1330
        write(c, "Race là...", x, 250, t, 4.1, 0.4, 66, INK)
        write(c, "một hệ thống do", x, 340, t, 5.3, 0.5, 50, INK)
        write(c, "XÃ HỘI tạo ra", x, 400, t, 6.3, 0.45, 56, RED)
        write(c, "– để phân loại con người", x, 480, t, 7.3, 0.6, 44, INK)
        write(c, "– dựa trên đặc điểm", x, 550, t, 8.7, 0.5, 44, INK)
        write(c, "   nhìn thấy được", x, 605, t, 9.9, 0.4, 44, INK)
        write(c, "– gắn ý nghĩa &", x, 680, t, 15.7, 0.4, 44, INK)
        write(c, "   vị trí trong xã hội", x, 735, t, 16.2, 0.5, 44, RED)
    s2 = pop(t, 11.1, out)
    place(c, S("n2_skin", (540, 620), note_fn(540, 620, lined=False), seed=72), 360, 520, st, s2, -3, key=3)
    if s2 > 0.9:
        place(c, tag("t_skinpig", "skin pigmentation", CORAL, 54), 360, 300, st, pop(t, 11.2, out), -4, key=4)
        place(c, S("sw_skin_d2", (5 * 84 + 4 * 22, 84), R.swatches_fn(SKINS), seed=73, border=6), 360, 430, st, 0.9 * pop(t, 11.4, out), 2, key=5)
        write(c, "sắc tố da", 360, 525, t, 11.5, 0.4, 52, NAVY, "c")
        place(c, S("hair_d2", (5 * 104, 180), R.hair_fn(HAIRS), seed=74, border=6), 360, 680, st, 0.75 * pop(t, 12.0, out), -2, key=6)
        write(c, "tóc, nét ngoại hình", 360, 790, t, 12.3, 0.6, 46, NAVY, "c")


HALL = Image.open("assets/stuart_hall.jpg").convert("RGBA").resize((210, 280), Image.LANCZOS)


def portrait_fn(d, img, p):
    img.alpha_composite(HALL, (p, p))


def ov_hall(c, t, st):
    # Stuart Hall + "floating signifier"; then "Race = tự nhiên, bất biến" crossed out
    sh = pop(t, 44.3, 49.75)
    place(c, S("n2_hall", (460, 620), note_fn(460, 620, lined=False), seed=75), 370, 500, st, sh, -2, key=10)
    if sh > 0.9:
        place(c, S("hall_photo", (210, 280), portrait_fn, seed=76, border=8), 370, 365, st, pop(t, 44.4), 3, key=11)
        write(c, "Stuart Hall", 370, 585, t, 44.6, 0.5, 66, INK, "c")
        write(c, "(1932 – 2014)", 370, 650, t, 45.1, 0.4, 40, NAVY, "c")
        write(c, "nhà lý luận văn hoá", 370, 705, t, 45.4, 0.5, 40, NAVY, "c")
    # floating signifier bobs gently, as if it drifts
    bob = 14 * math.sin(t * 2.4)
    fl = pop(t, 47.4, 53.35)
    place(c, S("n2_float", (440, 250), note_fn(440, 250, lined=False), seed=79), 1560, 540, st, fl, 2, key=14)
    place(c, tag("t_float", "floating signifier", INK, 66), 1560, 360 + bob, st, fl, 3 * math.sin(t * 1.7), key=12)
    if fl > 0.9:
        write(c, "= cái biểu đạt", 1560, 490, t, 48.6, 0.4, 54, NAVY, "c")
        write(c, "trôi nổi", 1560, 580, t, 49.2, 0.3, 60, RED, "c")
    rn = pop(t, 50.7, 53.35)
    place(c, S("n2_nat", (460, 440), note_fn(460, 440), seed=77), 370, 520, st, rn, -2, key=13)
    if rn > 0.9:
        write(c, "Race =", 370, 390, t, 50.8, 0.3, 80, INK, "c")
        write(c, "tự nhiên", 370, 500, t, 51.0, 0.3, 70, INK, "c")
        write(c, "bất biến", 370, 600, t, 51.2, 0.3, 70, INK, "c")
        strike(c, 370, 500, "tự nhiên", 70, t, 52.3)
        strike(c, 370, 600, "bất biến", 70, t, 53.0)


CUT = sorted(glob.glob("v3/cut/*.png"))
SLAM_T = 66.75
CUT_T0, CUT_BOX, CUT_SC = 58.9, (260, 150, 1760, 1080), 0.86


@functools.lru_cache(maxsize=4)
def cut_frame(k):
    """whole frame cut-out scaled with a fixed factor (no per-frame recentering) + white torn outline."""
    im = Image.open(CUT[k]).convert("RGBA")
    im = im.crop(CUT_BOX)
    im = im.resize((int(im.width * CUT_SC), int(im.height * CUT_SC)), Image.LANCZOS)
    alpha = im.split()[3].point(lambda v: 255 if v > 100 else 0)
    bm = R.torn_mask(alpha, 13, k % 3)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (30, 20, 40, 0))
    sh.putalpha(bm.point(lambda v: int(v * 0.35)).filter(ImageFilter.GaussianBlur(6)))
    out.alpha_composite(sh, (8, 10))
    pp = Image.new("RGBA", im.size, (252, 250, 242, 255))
    pp.putalpha(bm)
    out.alpha_composite(R.texturize(pp, 3, 0.05))
    out.alpha_composite(im)
    return out


def sc_end(t, st):
    # ending: both speakers cut out, smaller, on paper background; the question on top
    c = background(PINK, 15).copy().convert("RGBA")
    k = int(clamp((t - CUT_T0) * ANIM, 0, len(CUT) - 1))
    sp = cut_frame(k)
    c.alpha_composite(sp, ((W - sp.width) // 2, H - sp.height + 40))
    write(c, "Race là một social construction...", W // 2, 85, t, 60.7, 0.8, 78, INK, "c")
    write(c, "Vậy RACISM cũng chỉ là", W // 2, 215, t, 63.8, 0.6, 108, NAVY, "c")
    write(c, "tưởng tượng thôi?", W // 2, 350, t, 65.3, 0.5, 124, RED, "c")
    # "KHÔNG PHẢI ĐÂU!" slams into the screen: huge -> normal in 0.18s, then the frame shakes
    ti = SLAM_T
    if t >= ti - 0.18:
        p = clamp((t - (ti - 0.18)) / 0.18)
        sc = 3.2 - 2.2 * p * p
        place(c, tag("t_khong_big", "KHÔNG PHẢI ĐÂU!", RED, 135), 960, 905, st, sc, -6, key=21, jitter=False)
    if t >= ti:
        k = clamp(1 - (t - ti) / 0.4)
        r = random.Random(int(t * 30))
        dx, dy = int(r.uniform(-22, 22) * k), int(r.uniform(-22, 22) * k)
        if k > 0:
            c = ImageChops.offset(c, dx, dy)
    return c


# ---------- full-screen scenes ----------
def divider_fn(d, img, p):
    d.rectangle([p, p, p + 14, p + 780], fill=(252, 250, 242))


def sc_simple(t, st):
    # "Nói đơn giản": body traits are real | grouping them into races + meanings is socially constructed
    c = background(MUST, 11).copy().convert("RGBA")
    place(c, S("n2_simple", (620, 120), note_fn(620, 120, lined=False), seed=80), 960, 95, st, pop(t, 17.8), -1.5, key=30)
    write(c, "Nói đơn giản...", 960, 95, t, 17.9, 0.6, 66, INK, "c")
    place(c, S("divider", (14, 780), divider_fn, seed=81, border=4), 960, 600, st, pop(t, 18.2), 0, key=31)
    # left: real
    write(c, "Đặc điểm cơ thể", 480, 250, t, 19.5, 0.6, 70, NAVY, "c")
    place(c, S("sw_skin_s", (5 * 84 + 4 * 22, 84), R.swatches_fn(SKINS), seed=82, border=7), 480, 400, st, pop(t, 19.8), -2, key=32)
    place(c, S("hair_s", (5 * 104, 180), R.hair_fn(HAIRS), seed=83, border=7), 480, 580, st, 0.85 * pop(t, 20.1), 2, key=33)
    place(c, tag("t_real", "CÓ THẬT", GREEN, 84), 440, 840, st, pop(t, 21.0, dur=0.3), -6, key=34)
    place(c, S("check_s", (180, 140), R.hand_check_fn, seed=84, border=7), 690, 810, st, pop(t, 21.2, dur=0.3), key=35)
    # right: constructed
    write(c, "Gom thành chủng tộc", 1440, 250, t, 23.9, 0.7, 64, NAVY, "c")
    cols = [TEAL, CORAL, INK]
    ps = people()
    for g in range(3):
        bx = 1200 + g * 240
        s = pop(t, 24.2 + g * 0.15)
        place(c, ps[[0, 2, 4][g]], bx, 400, st, 0.5 * s, 0, key=36 + g)
        place(c, S(f"box{g}", (280, 170), R.box_fn(cols[g], "ABC"[g]), seed=21 + g), bx, 490, st, 0.8 * s, key=40 + g)
        place(c, asset(f"tag{g}", lambda g=g: Label("ý nghĩa?", 34, MUST, DARK, seed=50 + g)), bx + 70, 380, st,
              pop(t, 25.7 + g * 0.15), 10 - g * 8, key=44 + g)
    place(c, tag("t_xhkt", "XÃ HỘI KIẾN TẠO", INK, 64), 1440, 700, st, pop(t, 27.0, dur=0.3), -4, key=47)
    place(c, tag("t_notreal", "KHÔNG CÓ THẬT", RED, 72), 1440, 860, st, pop(t, 27.8, dur=0.3), 5, key=48)
    return c


def sc_labels(t, st):
    # "người da trắng được cho là văn minh hơn, người da màu kém văn minh hơn, một cộng đồng nào đó là man rợ"
    c = background(PURPLE, 12).copy().convert("RGBA")
    write(c, "Và cứ thế, những nhãn dán ra đời...", 960, 110, t, 29.3, 0.9, 64, (252, 248, 236), "c")
    ps = people()
    place(c, ps[0], 420, 520, st, 0.95 * pop(t, 30.2), -2, key=50)
    place(c, ps[3], 960, 520, st, 0.95 * pop(t, 32.7), 2, key=51)
    for i, pi in enumerate((1, 2, 4)):
        place(c, ps[pi], 1400 + i * 110, 540, st, 0.6 * pop(t, 35.5 + i * 0.1), (i - 1) * 5, key=52 + i)
    # labels slapped on like stickers
    place(c, tag("t_vm", "“văn minh hơn”", MUST, 60, DARK), 420, 800, st, pop(t, 31.6, dur=0.25), -7, key=55)
    place(c, tag("t_kvm", "“kém văn minh hơn”", MUST, 60, DARK), 960, 800, st, pop(t, 33.7, dur=0.25), 5, key=56)
    place(c, tag("t_mr", "“man rợ”", MUST, 60, DARK), 1510, 800, st, pop(t, 36.9, dur=0.25), -5, key=57)
    return c


QUESTION = [("Ai đã quyết định những khác biệt nào trên cơ thể", INK),
            ("đáng được dùng để phân loại con người?", INK),
            ("Và vì sao những khác biệt ấy lại được gắn với", INK),
            ("những giá trị như văn minh, trí tuệ hay sự thấp kém?", RED)]


def sc_question(t, st):
    c = background(NAVY, 13, True).copy().convert("RGBA")
    place(c, S("n2_q", (1560, 700), note_fn(1560, 700), seed=85), 960, 560, st, 1.0, -1, key=60)
    starts = [37.9, 38.9, 40.2, 41.3]
    ys = [330, 420, 620, 710]
    for (line, col), t0, y in zip(QUESTION, starts, ys):
        write(c, line, 230, y, t, t0, 0.9, 62, col)
    place(c, S("q_s1", (180, 280), R.qmark_fn, seed=86), 1780, 330, st, 0.45 * pop(t, 38.0), 12, key=61)
    place(c, S("q_s2", (180, 280), R.qmark_fn, seed=87), 150, 820, st, 0.4 * pop(t, 40.3), -10, key=62)
    return c


def sc_meaning(t, st):
    # "Một đặc điểm cơ thể có thể được diễn giải..." + time / society / power
    c = background(WOOD, 14).copy().convert("RGBA")
    place(c, S("n2_mean", (1400, 600), note_fn(1400, 600, spiral=True), seed=88), 960, 440, st, 1.0, -1, key=70)
    lines = [("Một đặc điểm cơ thể có thể được diễn giải", INK, 53.7), ("theo những cách hoàn toàn khác nhau", INK, 54.4),
             ("tùy vào AI ĐANG CÓ QUYỀN", RED, 55.1), ("đặt tên và định nghĩa nó.", INK, 55.7)]
    for i, (ln, col, t0) in enumerate(lines):
        write(c, ln, 340, 280 + i * 100, t, t0, 0.6, 62, col)
    for i, (w, t0, col) in enumerate([("thời kỳ", 56.0, TEAL), ("xã hội", 56.7, CORAL), ("quyền lực", 57.9, RED)]):
        place(c, tag(f"t_m{i}", w, col, 60), 560 + i * 400, 900, st, pop(t, t0, dur=0.3), (-4, 3, -3)[i], key=71 + i)
    return c


TL = [
    (0.0, 3.95, "ov", ov_intro), (3.95, 17.7, "ov", ov_define),
    (17.7, 28.85, "fs", sc_simple), (28.85, 37.75, "fs", sc_labels), (37.75, 43.45, "fs", sc_question),
    (43.45, 53.5, "ov", ov_hall), (53.5, 58.9, "fs", sc_meaning), (58.9, 99, "fs", sc_end),
]
WIPE = 0.45
_cache = {}


def seg_at(t):
    for i, sg in enumerate(TL):
        if sg[0] <= t < sg[1]:
            return i
    return len(TL) - 1


def render_seg(i, t, st, raw):
    a, b, kind, fn = TL[i]
    if kind == "fs" and fn is sc_end and t >= SLAM_T - 0.2:
        return fn(t, st).convert("RGB")
    if kind == "fs":
        key = (i, st)
        if key not in _cache:
            if len(_cache) > 4:
                _cache.clear()
            _cache[key] = fn(t, st).convert("RGB")
        return _cache[key]
    return overlay(apply_cam(raw, t), fn, t, st)


def main():
    pin = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", R.FIT, "-f", "rawvideo", "-pix_fmt", "rgb24", "-r", "30", "-"], stdout=subprocess.PIPE)
    pout = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                             "-i", "-", "-i", SRC, "-i", "v3/thump.wav", "-filter_complex",
                             f"[2:a]adelay={int(SLAM_T*1000)}|{int(SLAM_T*1000)}[th];[1:a][th]amix=inputs=2:duration=first:normalize=0[a]",
                             "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
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
            if tb - WIPE / 2 <= t < tb + WIPE / 2 and not (TL[j - 1][2] == "ov" and TL[j][2] == "ov"):
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
