# Edit of segment 5: post-racial society dilemma (Obama -> Māori haka in the NZ parliament).
# 0–27.4s of the source is black (voice-over) -> full-screen footage collages; then the speaker at a desk.
import sys, math, subprocess
from PIL import Image, ImageDraw
import render as R
from render import (W, H, ANIM, NAVY, MUST, PINK, CORAL, TEAL, CREAM, INK, RED, WOOD, PURPLE, GREEN, DARK,
                    S, Label, asset, place, pop, write, clamp, ease_io, background, people)
from render2 import tag, scrim, crop_origin
from render4 import framed, photo
from render5 import Clip, slam, dashed

SRC = "input.mp4"  # path to the source video
OUT = sys.argv[1] if len(sys.argv) > 1 else "output.mp4"
FPS = 30
WHITE = (252, 248, 236)
A = "v6/assets/"
PARL_T0, PARL_T1 = 10.1, 27.65  # parliament haka footage (with its own sound)

CLIPS = {"obama": Clip("v6/clips/obama.mp4", 0.0), "parl": Clip("v6/clips/parl.mp4", PARL_T0, (1280, 720)),
         "kapa": Clip("v6/clips/kapa.mp4", 34.0, (1280, 720))}

CAM = [(27.4, 1.0, 960, 540), (34.0, 1.08, 960, 520), (49.5, 1.0, 960, 540), (51.2, 1.0, 960, 540),
       (51.35, 1.1, 960, 520), (58.6, 1.12, 960, 520), (58.8, 1.0, 960, 540)]


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


# ---------- drawings ----------
def ballot_fn(d, img, p):
    d.rectangle([p + 20, p + 120, p + 300, p + 330], fill=(120, 150, 200))
    d.rectangle([p + 110, p + 118, p + 210, p + 134], fill=DARK)
    d.polygon([(p + 120, p + 125), (p + 200, p + 125), (p + 190, p), (p + 130, p)], fill=(250, 248, 236))
    d.line([(p + 140, p + 30), (p + 180, p + 30)], fill=INK, width=5)
    d.line([(p + 140, p + 55), (p + 175, p + 55)], fill=INK, width=5)


def book_fn(d, img, p):
    d.rectangle([p, p, p + 300, p + 360], fill=NAVY)
    d.rectangle([p + 20, p + 20, p + 280, p + 340], fill=(64, 72, 150))
    d.rectangle([p + 290, p + 10, p + 310, p + 350], fill=(236, 230, 214))
    fnt = R.font(48)
    for i, ln in enumerate(("QUY", "TẮC")):
        bb = fnt.getbbox(ln)
        d.text((p + 150 - (bb[2] - bb[0]) / 2 - bb[0], p + 110 + i * 70), ln, font=fnt, fill=MUST)


def magnifier_fn(d, img, p):
    d.line([(p + 220, p + 220), (p + 330, p + 330)], fill=(120, 80, 50), width=36)
    d.ellipse([p, p, p + 260, p + 260], fill=(60, 60, 70))
    d.ellipse([p + 22, p + 22, p + 238, p + 238], fill=(200, 230, 245))
    d.arc([p + 50, p + 50, p + 200, p + 200], 200, 260, fill=(255, 255, 255), width=10)


def space_fn(d, img, p):
    d.rounded_rectangle([p, p, p + 1060, p + 700], 30, fill=(236, 226, 200))
    d.rounded_rectangle([p + 24, p + 24, p + 1036, p + 676], 22, fill=(214, 196, 150))
    for r in range(3):
        d.rectangle([p + 90, p + 380 + r * 90, p + 970, p + 420 + r * 90], fill=(150, 100, 60))


def asker_fn(d, img, p):
    d.ellipse([p + 60, p, p + 180, p + 120], fill=(40, 36, 44))
    d.rounded_rectangle([p + 20, p + 130, p + 220, p + 330], 60, fill=(40, 36, 44))


# ---------- full-screen scenes ----------
def sc_obama(t, st):
    c = background(NAVY, 30, True).copy().convert("RGBA")
    framed(c, CLIPS["obama"].get(t), 720, 560, st, 1.0, -1.5, key=1)
    place(c, tag("t_ob", "Barack Obama", INK, 76), 1560, 250, st, pop(t, 0.9), 3, key=2)
    write(c, "2008", 1560, 420, t, 2.4, 0.5, 170, MUST, "c")
    place(c, tag("t_hst", "HẬU SẮC TỘC", CORAL, 84), 1560, 640, st, pop(t, 5.6), -4, key=3)
    write(c, "“post-racial”", 1560, 760, t, 5.9, 0.6, 60, WHITE, "c")
    slam(c, "t_bm", "ĐÃ BIẾN MẤT?", RED, 1560, 920, st, t, 9.2, 84, 5)
    return c


def sc_parl(t, st):
    c = background(TEAL, 31).copy().convert("RGBA")
    k = ease_io(clamp((t - 15.3) / 0.6))  # the footage shrinks to the left when the argument starts
    fr = CLIPS["parl"].get(t)
    sc = 1.08 - 0.33 * k
    framed(c, fr, 960 - 470 * k, 590 - 30 * k, st, sc, -1 + k * 0.5, key=10)
    if t < 15.4:
        write(c, "Quốc hội New Zealand", 960, 80, t, 12.9, 0.7, 76, WHITE, "c")
        place(c, tag("t_nsm", "NGHỊ SĨ MĀORI", CORAL, 78), 420, 960, st, pop(t, 11.6, 15.3), -4, key=11)
        place(c, tag("t_haka", "haka", MUST, 84, DARK), 900, 990, st, pop(t, 12.4, 15.3), 5, key=12)
        slam(c, "t_ngl", "NGHỊCH LÝ", RED, 1520, 960, st, t, 14.4, 96, -5)
    else:
        write(c, "Một số người cho rằng...", 1400, 90, t, 15.7, 0.8, 70, WHITE, "c")
        place(c, S("ballot", (320, 330), ballot_fn, seed=120, border=8), 1180, 390, st, pop(t, 18.2), -3, key=13)
        place(c, tag("t_gd", "GIÁN ĐOẠN", RED, 70), 1180, 620, st, pop(t, 18.4), 4, key=14)
        place(c, S("book", (310, 360), book_fn, seed=121, border=8), 1700, 390, st, pop(t, 20.4), 4, key=15)
        place(c, tag("t_qt", "NGƯỢC QUY TẮC", INK, 60), 1630, 640, st, pop(t, 20.6), -3, key=16)
        slam(c, "t_cm", "CÙNG MỘT CHUẨN MỰC", MUST, 1420, 860, st, t, 25.6, 84, -3, DARK)
    return c


def sc_kapa(t, st):
    c = background(CORAL, 32).copy().convert("RGBA")
    write(c, "Với người Māori...", 960, 80, t, 34.1, 0.6, 80, WHITE, "c")
    framed(c, CLIPS["kapa"].get(t), 960, 560, st, 1.02, 1.2, key=20)
    place(c, tag("t_kcl", "không chỉ là điệu nhảy", INK, 64), 470, 970, st, pop(t, 35.9), -3, key=21)
    slam(c, "t_bs", "BẢN SẮC", RED, 1560, 250, st, t, 38.4, 96, 6)
    slam(c, "t_tnvh", "TIẾNG NÓI VĂN HÓA", MUST, 1420, 970, st, t, 39.4, 84, -4, DARK)
    return c


def sc_space(t, st):
    # "haka bị xem là gây gián đoạn -> bị đặt ra ngoài những hình thức phù hợp trong không gian chính trị"
    c = background(PURPLE, 33).copy().convert("RGBA")
    write(c, "Khi haka bị xem là “gây gián đoạn”...", 960, 75, t, 40.6, 1.0, 72, WHITE, "c")
    place(c, S("space", (1060, 700), space_fn, seed=122, border=10), 640, 600, st, pop(t, 40.7, dur=0.4), 0, key=30)
    place(c, tag("t_kgct", "KHÔNG GIAN CHÍNH TRỊ", NAVY, 60), 640, 290, st, pop(t, 48.6), -2, key=31)
    ps = people()
    for i in range(5):
        place(c, ps[i % 2], 290 + i * 170, 520, st, 0.5 * pop(t, 41.0 + i * 0.08), 0, key=32 + i)
    place(c, tag("t_ph", "“PHÙ HỢP”", GREEN, 70), 640, 830, st, pop(t, 47.8), 3, key=37)
    # the haka photo starts inside the room, then is pushed out of it
    out = ease_io(clamp((t - 45.9) / 0.8))
    x = 900 + (1560 - 900) * out
    framed(c, photo(A + "kapa_82.jpg", 440, 300), x, 470 + 60 * out, st, pop(t, 41.3, dur=0.35), 6 * out - 3, key=38)
    place(c, tag("t_ggd", "GÂY GIÁN ĐOẠN?", RED, 62), x, 690 + 60 * out, st, pop(t, 42.7), -5, key=39)
    if out >= 0.99:
        place(c, tag("t_ngoai", "bị đặt RA NGOÀI", MUST, 68, DARK), 1560, 900, st, pop(t, 46.8), 4, key=40)
    return c


# ---------- speaker overlays ----------
def ov_who(c, t, st):
    # "ai là người tạo ra những chuẩn mực được xem là 'bình thường'?"
    s = pop(t, 29.9, 33.95)
    place(c, S("asker", (240, 330), asker_fn, seed=123, border=8), 380, 430, st, s, 0, key=50)
    place(c, S("q_who", (180, 280), R.qmark_fn, seed=124), 520, 300, st, 0.55 * s, 12, key=51)
    place(c, tag("t_ai", "AI tạo ra chuẩn mực?", INK, 66), 380, 720, st, pop(t, 30.3, 33.95), -3, key=52)
    framed(c, photo(A + "kapa_35.jpg", 460, 300), 1560, 380, st, pop(t, 31.0, 33.95), 4, key=53)
    slam(c, "t_bt", "“BÌNH THƯỜNG”?", RED, 1560, 700, st, t, 32.2, 88, -5)


def ov_power(c, t, st):
    # "cần xem xét quyền lực và lịch sử phía sau những quy tắc tưởng như trung lập"
    out = 54.4
    place(c, S("book", (310, 360), book_fn, seed=121, border=8), 380, 420, st, pop(t, 50.0, out), -4, key=60)
    place(c, tag("t_tl", "“TRUNG LẬP”?", CORAL, 76), 380, 720, st, pop(t, 53.8, out), 3, key=61)
    place(c, S("magnifier", (330, 330), magnifier_fn, seed=125, border=8), 1560, 380, st, pop(t, 50.9, out), 8, key=62)
    place(c, tag("t_ql", "QUYỀN LỰC", RED, 80), 1560, 660, st, pop(t, 51.3, out), -4, key=63)
    place(c, tag("t_ls", "LỊCH SỬ", INK, 80), 1560, 810, st, pop(t, 52.1, out), 3, key=64)
    # the big question this raises
    slam(c, "t_xhhct", "XÃ HỘI HẬU CHỦNG TỘC?", MUST, 960, 150, st, t, 57.4, 84, -2, DARK)


def ov_final(c, t, st):
    # closing question to the audience: top + bottom over dark gradients
    a = clamp((t - 58.8) / 0.3)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.alpha_composite(scrim(True))
    layer.alpha_composite(scrim(False))
    write(layer, "Nếu bình đẳng là đối xử NHƯ NHAU...", W // 2, 70, t, 59.0, 1.0, 68, WHITE, "c")
    write(layer, "liệu có thật sự CÔNG BẰNG?", W // 2, 180, t, 63.4, 0.7, 104, MUST, "c")
    write(layer, "khi chính chuẩn mực “giống nhau” đó được hình thành", W // 2, 905, t, 64.9, 1.2, 60, WHITE, "c")
    write(layer, "trong một xã hội bất bình đẳng về QUYỀN LỰC & VĂN HÓA?", W // 2, 995, t, 67.8, 1.2, 62, MUST, "c")
    if a < 1:
        layer.putalpha(layer.split()[3].point(lambda v: int(v * a)))
    c.alpha_composite(layer)


TL = [(0.0, 10.1, "fs", sc_obama), (10.1, 27.65, "fs", sc_parl),
      (27.65, 34.0, "sp", ov_who), (34.0, 40.45, "fs", sc_kapa), (40.45, 49.55, "fs", sc_space),
      (49.55, 58.75, "sp", ov_power), (58.75, 99, "sp", ov_final)]
LIVE = {sc_obama, sc_parl, sc_kapa, sc_space}
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
        if fn in LIVE:
            return fn(t, st).convert("RGB")
        key = (i, st)
        if key not in _cache:
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
    d0, dur = PARL_T0, PARL_T1 - PARL_T0
    pout = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                             "-i", "-", "-i", SRC, "-i", "v6/parl_audio.wav", "-filter_complex",
                             f"[2:a]atrim=0:{dur:.2f},volume=0.45,afade=t=in:d=0.4,afade=t=out:st={dur - 0.6:.2f}:d=0.6,"
                             f"adelay={int(d0 * 1000)}|{int(d0 * 1000)}[h];[1:a][h]amix=inputs=2:duration=first:normalize=0[a]",
                             "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
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
