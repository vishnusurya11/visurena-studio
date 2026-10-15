"""The girl across T05, T06 and T07 beside her new sheet (owner 2026-10-15).

    make_girl_strip.py <out.jpg> [<takes dir>]

One row per take, six frames evenly spread (ffmpeg), the sheet_front at the left of
every row at the same height.  <takes dir> defaults to the episode's live takes.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[4]
BOOK = ROOT / "library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde"
TAKES = BOOK / "episodes/ep01/takes/r2v"
SHEET = BOOK / "refs/characters/child_of_hyde_incident/sheet_front.png"
H, N = 384, 6


def frames(video: Path) -> list[Image.Image]:
    """Six frames evenly spread through the take (OpenCV; the shell has no ffprobe)."""
    import cv2
    cap = cv2.VideoCapture(str(video))
    count, out = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), []
    for k in range(N):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(count * (k + 0.5) / N))
        ok, bgr = cap.read()
        if ok:
            im = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
            out.append(im.resize((round(im.width * H / im.height), H)))
    cap.release()
    return out


def row(sheet: Image.Image, video: Path) -> Image.Image:
    pics = [sheet] + frames(video)
    canvas = Image.new("RGB", (sum(p.width for p in pics), H + 24), (15, 16, 18))
    x = 0
    for p in pics:
        canvas.paste(p, (x, 24))
        x += p.width
    ImageDraw.Draw(canvas).text((6, 5), f"sheet_front | {video.name}", fill=(230, 230, 230))
    return canvas


def main(out: Path, takes: Path) -> None:
    s = Image.open(SHEET).convert("RGB")
    sheet = s.resize((round(s.width * H / s.height), H))
    rows = [row(sheet, takes / f"T{i:02d}.mp4") for i in (5, 6, 7)]
    canvas = Image.new("RGB", (max(r.width for r in rows), sum(r.height for r in rows)), (15, 16, 18))
    y = 0
    for r in rows:
        canvas.paste(r, (0, y))
        y += r.height
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, quality=90)
    print(out)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) > 2 else TAKES)
