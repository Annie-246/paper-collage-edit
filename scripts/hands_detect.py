import sys
# Per-frame hand detection (MediaPipe) for đoạn 3; stores palm-centre (landmark 9) + wrist of each hand.
import json, subprocess, numpy as np, mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions
opt = vision.HandLandmarkerOptions(base_options=BaseOptions(model_asset_path="models/hand_landmarker.task"), num_hands=2,
                                   running_mode=vision.RunningMode.VIDEO)
det = vision.HandLandmarker.create_from_options(opt)
F = sys.argv[1] if len(sys.argv) > 1 else "input.mp4"
p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", F, "-vf", "scale=960:540", "-f", "rawvideo", "-pix_fmt", "rgb24", "-r", "30", "-"], stdout=subprocess.PIPE)
out, n = [], 0
while True:
    b = p.stdout.read(960 * 540 * 3)
    if len(b) < 960 * 540 * 3:
        break
    a = np.frombuffer(b, np.uint8).reshape(540, 960, 3)
    r = det.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(a)), int(n * 1000 / 30))
    out.append([[round(lm[9].x * 1920), round(lm[9].y * 1080), round(lm[12].y * 1080)] for lm in r.hand_landmarks])
    n += 1
json.dump(out, open("hands.json", "w"))
print("DONE", n)
