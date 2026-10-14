"""Rulers + compare sheet for the RTX VSR arms (one-off bench, 2026-10-14).

    uv run --no-sync python docs/audit/2026-10-14_rtx_vsr_test/tools/measure.py

Every arm is judged at the 1536 delivery size: D (3072) is area-downsampled to 1536 first,
and also measured natively. Rulers come from scripts/bench/rulers.py:
  lap      Laplacian variance (sharpness; reported only, it failed calibration in phase 0)
  banding  comb index of the dark smooth luma histogram (lower = better)
  texture  mid-band DoG energy (higher = more detail)
plus crispness = 95th percentile Sobel magnitude on the ink-line crop (higher = crisper edges).
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parents[2]))
from scripts.bench import rulers  # noqa: E402

ARMS = ["A", "B", "C", "D", "U2", "Dd"]
SHEET = ["A", "B", "C", "Dd"]  # Dd = 4x ULTRA area-resized to 1536 on the GPU, encoded once at 1536
LABEL = {"A": "A lanczos 2x (today)", "B": "B VSR 2x HIGHBITRATE_ULTRA", "C": "C DEBLUR_ULTRA 1x + B",
         "D": "D VSR 4x ULTRA (shown at 1536)", "U2": "U2 VSR 2x ULTRA (round 0)"}
FRAME = 84                     # the crop frame, same index in every arm
CROPS = {                      # name: (take, x, y) in 768 source px, 160 px boxes
    "face": ("T17", 264, 150), "ink lines": ("T17", 530, 360),
    "night gradient": ("T03", 180, 140), "trampling": ("T06", 290, 500)}
BOX = 160


def grey(rgb):
    return rgb.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)


def at1536(rgb):
    return cv2.resize(rgb, (1536, 1536), interpolation=cv2.INTER_AREA) if rgb.shape[0] != 1536 else rgb


def frame_at(video, n):
    cap = cv2.VideoCapture(str(video))
    cap.set(cv2.CAP_PROP_POS_FRAMES, n)
    ok, bgr = cap.read()
    cap.release()
    return bgr[:, :, ::-1].copy()


def crop(rgb, x, y):
    return rgb[2 * y:2 * (y + BOX), 2 * x:2 * (x + BOX)]


def crisp(g):
    sx, sy = cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)
    return float(np.percentile(np.hypot(sx, sy), 95))


def whole(video, native=False):
    rows = []
    for rgb in rulers.frames(video):
        g = grey(rgb if native else at1536(rgb))
        rows.append({"lap": rulers.laplacian(g), "banding": rulers.banding(g), "texture": rulers.texture(g)})
    return {k: round(float(np.median([r[k] for r in rows])), 4) for k in rows[0]}


def crop_rulers(arm):
    out = {}
    for name, (take, x, y) in CROPS.items():
        g = grey(crop(at1536(frame_at(HERE / "arms" / f"{take}_{arm}.mp4", FRAME)), x, y))
        out[name] = {"lap": round(rulers.laplacian(g), 1), "banding": round(rulers.banding(g), 4),
                     "crisp": round(crisp(g), 1)}
    return out


def sheet(path):
    tiles = []
    for name, (take, x, y) in CROPS.items():
        row = [crop(at1536(frame_at(HERE / "arms" / f"{take}_{a}.mp4", FRAME)), x, y) for a in SHEET]
        native = frame_at(HERE / "arms" / f"{take}_D.mp4", FRAME)[4 * y + 160:4 * y + 480, 4 * x + 160:4 * x + 480]
        tiles.append(np.hstack([*row, native]))
        tiles[-1] = np.vstack([label(f"{name}  ({take})", tiles[-1].shape[1], 28), tiles[-1]])
    heads = ["A lanczos 2x", "B HIGHBITRATE_ULTRA 2x", "C DEBLUR+B 2x", "D 4x ULTRA, area ->1536", "D 4x native 3072, 100% (centre)"]
    top = np.hstack([label(h, 320, 34) for h in heads])
    cv2.imwrite(str(path), np.vstack([top, *tiles])[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 95])


def label(text, w, h):
    img = np.full((h, w, 3), 15, np.uint8)
    cv2.putText(img, text, (6, h - 9), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (235, 235, 235), 1, cv2.LINE_AA)
    return img


def main():
    res = {"whole_1536": {}, "whole_native_D": {}, "crops": {}}
    for arm in ARMS:
        res["whole_1536"][arm] = {t: whole(HERE / "arms" / f"{t}_{arm}.mp4") for t in ("T17", "T03", "T06")}
        res["crops"][arm] = crop_rulers(arm)
    res["whole_native_D"] = {t: whole(HERE / "arms" / f"{t}_D.mp4", native=True) for t in ("T17", "T03", "T06")}
    (HERE / "rulers.json").write_text(json.dumps(res, indent=1))
    sheet(HERE / "compare.jpg")
    print(json.dumps(res["crops"], indent=1))


if __name__ == "__main__":
    main()
