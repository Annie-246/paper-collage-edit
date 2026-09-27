# Minimal starting point: one overlay scene on the speaker + one full-screen paper scene, torn-wipe between.
# Works for both canvases; lay out with CX/CY/SAFE instead of fixed 1920x1080 coordinates.
#   python template.py input.mp4 output.mp4 [duration]                  -> 16:9
#   PAPER_ASPECT=9:16 python template.py input.mp4 output.mp4 [duration] -> 9:16
import sys
ARGS, sys.argv = sys.argv[1:], sys.argv[:1]  # render.py parses sys.argv at import
import render as R
from render import W, H, CX, CY, SAFE, VERTICAL, NAVY, MUST, CORAL, TEAL, INK, S, place, pop, write, note_fn, Label

x0, y0, x1, y1 = SAFE
U = min(W, H) / 1080  # size unit: same visual size on both canvases


def ov_hook(c, t, st):
    # keyword chip at the top of the safe area (away from the face on both canvases)
    place(c, Label("TỪ KHOÁ", int(80 * U), CORAL, seed=1), CX, y0 + int(90 * U), st, pop(t, 0.4), -3, key=1)
    write(c, "câu hỏi mở đầu?", CX, y1 - int(120 * U), t, 0.8, 0.7, int(96 * U), MUST, "c")


def sc_idea(t, st):
    c = R.background(TEAL, seed=2).convert("RGBA")
    nw, nh = (x1 - x0 - 40, int((y1 - y0) * 0.55)) if VERTICAL else (1180, 700)
    place(c, S("note_idea", (nw, nh), note_fn(nw, nh, spiral=True), seed=3), CX, CY, st, pop(t, 3.0), -1.5, key=2)
    write(c, "Ý chính", CX, CY - nh // 4, t, 3.3, 0.6, int(120 * U), INK, "c")
    write(c, "một hình + một keyword", CX, CY + nh // 8, t, 3.9, 0.8, int(64 * U), NAVY, "c")
    return c


if __name__ == "__main__":
    R.SRC = ARGS[0]
    R.OUT = ARGS[1]
    R.T_START, R.T_END = 0.0, float(ARGS[2]) if len(ARGS) > 2 else 6.0
    R.TL = [(0.0, 2.8, "ov", ov_hook), (2.8, 99, "full", sc_idea)]
    R.main()
