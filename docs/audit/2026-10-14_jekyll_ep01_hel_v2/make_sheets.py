"""Jekyll HEL ep01 v2 audit media ($0, CPU + ffmpeg):

    uv run python docs/audit/2026-10-14_jekyll_ep01_hel_v2/make_sheets.py <master.mp4> <walk takes T03,T04,...>

- frames_every_10s.jpg: the master every 10 s, stamped with time and shot;
- gait/T<NN>_strip.jpg: 12 fps crops over the first 4 s of each walking take (12 per row);
- master_preview720.mp4: a 720p H.264 preview held under 25 MB.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EP = ROOT / "library" / "20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde" / "episodes" / "ep01"


def duration(video: Path) -> float:
    import cv2
    cap = cv2.VideoCapture(str(video))
    seconds = cap.get(cv2.CAP_PROP_FRAME_COUNT) / (cap.get(cv2.CAP_PROP_FPS) or 24.0)
    cap.release()
    return float(seconds)


def frame(video: Path, at: float, width: int) -> Image.Image:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{at:.3f}", "-i", str(video), "-frames:v", "1",
                          "-vf", f"scale={width}:-2", "-f", "image2pipe", "-vcodec", "png", "-"],
                         capture_output=True, check=True).stdout
    from io import BytesIO
    return Image.open(BytesIO(raw)).convert("RGB")


def shot_at(at: float) -> str:
    placed = json.loads((EP / "placed.json").read_text(encoding="utf-8"))
    for s in placed.get("shots", []):
        if s.get("t_start", 0) <= at < s.get("t_end", 0):
            return f"shot {s.get('index')}"
    return "card"


def sheet(images: list[Image.Image], labels: list[str], cols: int, out: Path) -> None:
    w, h = images[0].size
    rows = (len(images) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * w, rows * h), (15, 16, 18))
    pen = ImageDraw.Draw(canvas)
    for i, (im, label) in enumerate(zip(images, labels)):
        x, y = (i % cols) * w, (i // cols) * h
        canvas.paste(im, (x, y))
        pen.rectangle([x, y, x + 8 * len(label) + 8, y + 16], fill=(0, 0, 0))
        pen.text((x + 4, y + 2), label, fill=(255, 220, 0))
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, quality=88)


def every_10s(master: Path) -> Path:
    total = duration(master)
    times = [t + 0.5 for t in range(0, int(total), 10)]
    out = HERE / "frames_every_10s.jpg"
    sheet([frame(master, t, 384) for t in times], [f"{t:05.1f}s {shot_at(t)}" for t in times], 5, out)
    return out


def gait_strip(take: str) -> Path:
    video = EP / "takes" / "r2v" / f"{take}.mp4"
    times = [i / 12 for i in range(48) if i / 12 < duration(video) - 0.1]
    out = HERE / "gait" / f"{take}_strip.jpg"
    sheet([frame(video, t, 256) for t in times], [f"{take} {t:.2f}s" for t in times], 12, out)
    return out


def preview(master: Path) -> Path:
    out = HERE / "master_preview720.mp4"
    kbps = int(24 * 8 * 1024 / duration(master)) - 130
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(master), "-vf", "scale=720:720", "-c:v", "libx264",
                    "-b:v", f"{kbps}k", "-maxrate", f"{kbps}k", "-bufsize", f"{2 * kbps}k", "-preset", "slow",
                    "-c:a", "aac", "-b:a", "128k", str(out)], check=True)
    return out


if __name__ == "__main__":
    m = Path(sys.argv[1])
    print(every_10s(m))
    for t in (sys.argv[2].split(",") if len(sys.argv) > 2 and sys.argv[2] else []):
        print(gait_strip(t))
    p = preview(m)
    print(p, round(p.stat().st_size / 1e6, 1), "MB")
