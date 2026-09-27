# Edit of segment 7: hegemony / "who benefits?" — adds EMPHASIS moments where the background goes dark
# (MediaPipe person mask) so the speaker + one keyword pop out.
import sys, math, random, subprocess, functools, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render as R
from render import (W, H, ANIM, NAVY, MUST, PINK, CORAL, TEAL, CREAM, INK, RED, WOOD, PURPLE, GREEN, DARK,
                    S, Label, asset, place, pop, write, clamp, ease_io, background, people, brain_fn, note_fn, crayon_circle)
from render2 import tag, crop_origin
from render4 import framed, photo
from render5 import slam
from render6 import book_fn, magnifier_fn
from render7 import tv_fn, tv_screen

SRC = "input.mp4"  # path to the source video
OUT = sys.argv[1] if len(sys.argv) > 1 else "output.mp4"
FPS = 30
WHITE = (252, 248, 236)
CUT = 15.83  # shot change: seated -> standing at the whiteboard


# ---------- emphasis: darken everything except the speaker ----------
EMPH = [(11.1, 15.8), (20.1, 25.1), (39.0, 42.7)]


def emph_amount(t):
    for a, b in EMPH:
        if a - 0.3 <= t <= b + 0.3:
            return ease_io(clamp((t - a + 0.3) / 0.3)) * (1 - ease_io(clamp((t - b) / 0.3)))
    return 0.0


@functools.lru_cache(maxsize=8)
def person_mask(n):
    path = f"v8/masks/{n:05d}.png"
    if not os.path.exists(path):
        return None
    m = Image.open(path).resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6))
    a = np.asarray(m).astype(np.float32) / 255
    return np.clip((a - 0.25) / 0.5, 0, 1)


def emphasize(frame, t):
    k = emph_amount(t)
    if k <= 0:
        return frame
    m = person_mask(int(round(t * FPS)))
    if m is None:
        return frame
    f = np.asarray(frame).astype(np.float32)
    grey = f.mean(axis=2, keepdims=True)
    dark = (grey * 0.35 + f * 0.1) * 0.55 + np.array([10, 8, 22], np.float32)
    bg = f * (1 - k) + dark * k
    out = bg * (1 - m[..., None]) + f * m[..., None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


# ---------- drawings ----------
def track_fn(d, img, p):
    d.rectangle([p, p, p + 1700, p + 560], fill=(196, 92, 70))
    for i in range(5):
        d.line([(p, p + i * 140), (p + 1700, p + i * 140)], fill=(250, 246, 236), width=8)
    d.rectangle([p + 1540, p, p + 1560, p + 560], fill=(250, 246, 236))
    for r in range(8):
        for c in range(2):
            if (r + c) % 2 == 0:
                d.rectangle([p + 1560 + c * 28, p + r * 70, p + 1588 + c * 28, p + r * 70 + 70], fill=DARK)


def money_fn(d, img, p):
    d.ellipse([p, p + 80, p + 260, p + 330], fill=(120, 170, 90))
    d.polygon([(p + 90, p + 90), (p + 170, p + 90), (p + 200, p + 20), (p + 60, p + 20)], fill=(120, 170, 90))
    d.rectangle([p + 80, p + 80, p + 180, p + 100], fill=(90, 130, 60))
    d.text((p + 92, p + 130), "$", font=R.font(140), fill=(250, 236, 150))


def crown_fn(d, img, p):
    d.polygon([(p, p + 160), (p + 20, p + 30), (p + 90, p + 100), (p + 150, p), (p + 210, p + 100), (p + 280, p + 30), (p + 300, p + 160)], fill=MUST)
    d.rectangle([p, p + 150, p + 300, p + 200], fill=(226, 170, 50))
    for x in (p + 60, p + 150, p + 240):
        d.ellipse([x - 14, p + 162, x + 14, p + 190], fill=RED)


def chain_x_fn(d, img, p):
    for i in range(5):
        x = p + i * 80
        d.ellipse([x, p + 40, x + 110, p + 110], outline=(130, 130, 140), width=16)


def puppet_fn(d, img, p):
    d.rounded_rectangle([p + 40, p, p + 360, p + 60], 20, fill=(150, 100, 60))
    for x in (p + 90, p + 200, p + 310):
        d.line([(x, p + 60), (x, p + 330)], fill=(240, 236, 220), width=4)
    d.ellipse([p + 150, p + 150, p + 250, p + 250], fill=R.SKINS[1])
    d.rounded_rectangle([p + 130, p + 250, p + 270, p + 420], 40, fill=TEAL)


def signpost_fn(d, img, p):
    d.rectangle([p + 140, p + 60, p + 170, p + 420], fill=(120, 80, 50))
    d.polygon([(p, p + 60), (p + 250, p + 60), (p + 300, p + 110), (p + 250, p + 160), (p, p + 160)], fill=MUST)
    d.polygon([(p + 310, p + 190), (p + 60, p + 190), (p + 10, p + 240), (p + 60, p + 290), (p + 310, p + 290)], fill=CORAL)


# ---------- speaker overlays ----------
def ov_media(c, t, st):
    # "khi nhiều nhóm người đã xuất hiện hơn trên truyền thông, vấn đề có thật sự được giải quyết?"
    out = 4.8
    s = pop(t, 0.6, out)
    if s > 0:
        tv_screen(c, None, 330, 420, st, 0.62 * s)
        if s > 0.95:
            for i, f in enumerate(("obama_0.jpg", "oprah_1.jpg", "beyonce_5.jpg")):
                im = photo("v7/assets/" + f, 140, 170)
                c.alpha_composite(im, (int(330 - 225 + i * 150), int(398 - 100)))
    place(c, tag("t_xh", "xuất hiện NHIỀU HƠN", TEAL, 62), 330, 690, st, pop(t, 1.7, out), -3, key=1)
    slam(c, "t_gq", "ĐÃ ĐƯỢC GIẢI QUYẾT?", RED, 1600, 420, st, t, 3.9, 70, 4)


def ov_benefit(c, t, st):
    # EMPHASIS 1 — "ai là người được hưởng lợi?"
    out = 15.75
    write(c, "Và quan trọng nhất...", 360, 250, t, 11.3, 0.6, 64, WHITE, "c", t1=out)
    slam(c, "t_ai", "AI", MUST, 360, 440, st, t, 12.4, 170, -4, DARK)
    write(c, "được HƯỞNG LỢI?", 360, 640, t, 13.2, 0.6, 84, WHITE, "c", t1=out)
    place(c, S("money", (260, 330), money_fn, seed=140, border=8), 1560, 380, st, pop(t, 13.4, out), 6, key=2)
    place(c, S("crown", (300, 200), crown_fn, seed=141, border=8), 1600, 720, st, pop(t, 13.7, out), -8, key=3)
    write(c, "khi cách nhìn này tiếp tục tồn tại", 960, 980, t, 14.0, 1.2, 60, WHITE, "c", t1=out)


def ov_hegemony(c, t, st):
    # EMPHASIS 2 — the key term
    out = 25.0
    write(c, "Một cách giải thích:", 1500, 170, t, 20.3, 0.6, 60, WHITE, "c", t1=out)
    slam(c, "t_heg", "HEGEMONY", MUST, 1500, 330, st, t, 22.9, 120, -3, DARK)
    write(c, "bá quyền văn hóa", 1500, 490, t, 24.0, 0.6, 84, WHITE, "c", t1=out)
    framed(c, photo("v8/assets/gramsci_2.jpg", 260, 310), 1440, 770, st, pop(t, 23.4, out), 4, key=4)
    write(c, "Antonio Gramsci", 1440, 1030, t, 23.8, 0.5, 48, WHITE, "c", t1=out)


def ov_choice(c, t, st):
    # "…thay vì nhận ra đó cũng là một sự lựa chọn, chịu ảnh hưởng bởi điều kiện xã hội và chính trị"
    out = 38.9
    place(c, S("signpost", (320, 420), signpost_fn, seed=142, border=8), 300, 460, st, pop(t, 35.7, out), -3, key=5)
    place(c, tag("t_lc", "một SỰ LỰA CHỌN", CORAL, 70), 300, 780, st, pop(t, 35.9, out), 3, key=6)
    place(c, tag("t_xh2", "xã hội", TEAL, 76), 1500, 380, st, pop(t, 37.5, out), -4, key=7)
    place(c, tag("t_ct", "chính trị", INK, 76), 1560, 560, st, pop(t, 38.3, out), 4, key=8)


def ov_shape(c, t, st):
    # EMPHASIS 3 — "ai là người có khả năng định hình cái lẽ thường đó?"
    out = 42.65
    place(c, S("puppet", (400, 430), puppet_fn, seed=143, border=8), 300, 440, st, pop(t, 39.8, out), 0, key=9)
    slam(c, "t_ai2", "AI", MUST, 1500, 330, st, t, 40.0, 160, 4, DARK)
    write(c, "định hình", 1500, 520, t, 41.1, 0.4, 84, WHITE, "c", t1=out)
    slam(c, "t_lt", "LẼ THƯỜNG?", RED, 1500, 690, st, t, 41.8, 96, -3)


# ---------- full-screen scenes ----------
def sc_start(t, st):
    # same rules, different starting points
    c = background(TEAL, 50).copy().convert("RGBA")
    write(c, "Cùng một quy tắc...", 960, 80, t, 5.0, 0.8, 76, WHITE, "c")
    place(c, S("track", (1700, 560), track_fn, seed=144, border=10), 960, 600, st, pop(t, 4.9, dur=0.4), 0, key=10)
    place(c, S("book", (310, 360), book_fn, seed=121, border=8), 1680, 190, st, 0.5 * pop(t, 6.3), 8, key=11)
    ps = people()
    # lanes hold people()[0, 4, 1, 3]; the lighter the skin, the further ahead the start line (privilege)
    starts = [1060, 260, 700, 470]
    lanes = [390, 530, 670, 810]
    d = ImageDraw.Draw(c)
    if t >= 5.2:
        for i in range(4):
            x = starts[i] - 55
            d.line([(x, lanes[i] - 62), (x, lanes[i] + 62)], fill=(252, 248, 236, 255), width=12)
    run = ease_io(clamp((t - 8.9) / 2.0))
    for i in range(4):
        x = starts[i] + 380 * run  # same speed for everyone: the gaps never close
        place(c, ps[[0, 4, 1, 3][i]], x, lanes[i] - 10, st, 0.42 * pop(t, 5.3 + i * 0.1), 0, key=12 + i)
    if t >= 8.4:
        # gap arrows from the furthest-back start to each other start
        p = ease_io(clamp((t - 8.4) / 0.4))
        back = min(range(4), key=lambda i: starts[i])
        for i in range(4):
            if i == back:
                continue
            y = lanes[i] + 50
            x0, x1 = starts[back] - 55, starts[i] - 55
            d.line([(x0, y), (x0 + (x1 - x0) * p, y)], fill=MUST + (255,), width=8)
            if p > 0.95:
                d.polygon([(x1, y), (x1 - 26, y - 14), (x1 - 26, y + 14)], fill=MUST + (255,))
    place(c, tag("t_dxp", "khác ĐIỂM XUẤT PHÁT", CORAL, 70), 560, 1010, st, pop(t, 8.5), -3, key=16)
    slam(c, "t_cb", "CÔNG BẰNG?", RED, 1440, 1000, st, t, 10.5, 90, 4)
    return c


def sc_hidden(t, st):
    # "racism chưa biến mất, nó chỉ thay đổi cách xuất hiện, khó nhận ra hơn"
    c = background((236, 226, 206), 51).copy().convert("RGBA")
    fade = 1 - 0.8 * ease_io(clamp((t - 18.3) / 1.4))
    word = R.text_c("RACISM", 260, RED)
    w = word.copy()
    w.putalpha(w.split()[3].point(lambda v: int(v * fade)))
    c.alpha_composite(w, (960 - w.width // 2, 400 - w.height // 2))
    write(c, "chưa BIẾN MẤT", 960, 150, t, 16.9, 0.6, 84, NAVY, "c")
    place(c, S("magn2", (330, 330), magnifier_fn, seed=145, border=8),
          1360 - 380 * ease_io(clamp((t - 19.3) / 0.6)), 470, st, pop(t, 19.2), 8, key=20)
    place(c, tag("t_tdcx", "chỉ đổi cách xuất hiện", INK, 66), 560, 780, st, pop(t, 18.2), -3, key=21)
    slam(c, "t_knr", "khó NHẬN RA hơn", RED, 1320, 900, st, t, 19.5, 80, 3)
    return c


def sc_commonsense(t, st):
    # power without force: repetition makes one view "common sense"
    c = background(PURPLE, 52).copy().convert("RGBA")
    write(c, "Quyền lực không cần", 480, 100, t, 25.4, 0.7, 70, WHITE, "c")
    place(c, S("chain_x", (440, 150), chain_x_fn, seed=146, border=6), 480, 300, st, pop(t, 26.8), 0, key=30)
    place(c, tag("t_eb", "ÉP BUỘC", DARK, 84), 480, 470, st, pop(t, 27.1), -3, key=31)
    if t > 27.4:
        p = ease_io(clamp((t - 27.4) / 0.3))
        ImageDraw.Draw(c).line([(260, 480), (260 + 440 * p, 480 - 20 * p)], fill=RED + (255,), width=16)
    # repeated messages -> the mind accepts
    for i in range(3):
        place(c, S("tv", (820, 640), tv_fn, seed=130, border=8), 1180 + i * 60, 260 + i * 40, st, 0.32 * pop(t, 28.9 + i * 0.25), -4 + 4 * i, key=32 + i)
    place(c, tag("t_qt", "QUEN THUỘC", MUST, 76, DARK), 1330, 520, st, pop(t, 31.1), 4, key=35)
    place(c, S("brain_awake", (560, 430), brain_fn("smile"), seed=12), 1330, 790, st, 0.62 * pop(t, 32.2), 0, key=36)
    slam(c, "t_lt2", "“LẼ THƯỜNG”", RED, 540, 800, st, t, 33.5, 110, -4)
    return c


def sc_end(t, st):
    c = background(WOOD, 53).copy().convert("RGBA")
    place(c, S("nb_end", (1400, 720), note_fn(1400, 720, spiral=True), seed=147), 960, 560, st, pop(t, 42.9, dur=0.35), -1, key=40)
    write(c, "Bước đầu tiên để tạo ra BÌNH ĐẲNG", 330, 330, t, 43.9, 1.1, 76, INK)
    write(c, "là biết ĐẶT CÂU HỎI", 330, 470, t, 45.8, 0.7, 100, RED)
    write(c, "về những điều ta vẫn xem là", 330, 610, t, 46.7, 1.0, 70, INK)
    write(c, "HIỂN NHIÊN", 330, 740, t, 48.3, 0.5, 110, INK)
    crayon_circle(c, 640, 745, 330, 90, t, 48.8, 0.4)
    place(c, S("q_end", (180, 280), R.qmark_fn, seed=148), 1480, 700, st, pop(t, 48.9), 10, key=41)
    return c


TL = [(0.0, 4.85, "sp", ov_media), (4.85, 11.05, "fs", sc_start), (11.05, 15.83, "sp", ov_benefit),
      (15.83, 20.05, "fs", sc_hidden), (20.05, 25.2, "sp", ov_hegemony), (25.2, 34.0, "fs", sc_commonsense),
      (34.0, 38.95, "sp", ov_choice), (38.95, 42.8, "sp", ov_shape), (42.8, 999, "fs", sc_end)]
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
    f = emphasize(raw, t).convert("RGBA")
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
