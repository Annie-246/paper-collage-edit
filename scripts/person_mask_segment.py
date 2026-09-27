import sys
# Person masks (MediaPipe selfie segmenter) for the emphasis windows of đoạn 7 -> v8/masks/<frame>.png (480x270)
import os, subprocess, numpy as np, mediapipe as mp
from PIL import Image
from mediapipe.tasks.python import vision, BaseOptions
F = sys.argv[1] if len(sys.argv) > 1 else "input.mp4"
WINDOWS = [(10.9, 16.0), (19.9, 25.2), (38.8, 42.8)]
os.makedirs("v8/masks", exist_ok=True)
opt = vision.ImageSegmenterOptions(base_options=BaseOptions(model_asset_path="v8/selfie_segmenter.tflite"),
                                   running_mode=vision.RunningMode.VIDEO, output_confidence_masks=True)
seg = vision.ImageSegmenter.create_from_options(opt)
p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", F, "-vf", "scale=640:360", "-f", "rawvideo", "-pix_fmt", "rgb24", "-r", "30", "-"], stdout=subprocess.PIPE)
n = 0
while True:
    b = p.stdout.read(640 * 360 * 3)
    if len(b) < 640 * 360 * 3:
        break
    t = n / 30
    if any(a <= t < z for a, z in WINDOWS):
        a = np.frombuffer(b, np.uint8).reshape(360, 640, 3)
        r = seg.segment_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(a)), int(n * 1000 / 30))
        m = np.squeeze(r.confidence_masks[-1].numpy_view())
        Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).save(f"v8/masks/{n:05d}.png")
    n += 1
print("DONE", n, len(os.listdir("v8/masks")))
