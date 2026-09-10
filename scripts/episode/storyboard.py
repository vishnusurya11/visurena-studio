#!/usr/bin/env python
"""Draw the storyboard with gpt-image and cut every panel into a shot's first frame.

    uv run python scripts/episode/storyboard.py <codex_id> <episode>           # sheets + panels
    uv run python scripts/episode/storyboard.py <codex_id> <episode> --review  # contact sheet

Per setup: the shots in cut order, spread evenly over 3x3 sheets; each sheet
is drawn from the plate, the setup's character sheets and the previous sheet
of the same scene; each panel is cropped and conformed to 768x1344 as
`frames/SNN.png`.  Spare cells are drawn as alternate angles so no cell is
black; they are not cropped out.  The prompt is written beside a sheet ONLY
when the sheet is drawn, so the record is the prompt that made it.  PAID
step (owner's go, 2026-09-10); sheets on disk are never redrawn.
"""
from __future__ import annotations

import base64
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_board as board
from studio import episode_home
from studio.episode_spec import Episode
from studio.llm import _load_dotenv
from studio.trailer_refs import visual_description

W, H = 768, 1344
PEEK = 0.3


WHITE = 200
MAX_TRIM = 0.06
"""A gutter reads as a near-white edge; up to 6 % of a side is trimmed.
Measured on the corridor sheet: three panels kept a white bottom edge with
the flat 1.5 % trim, because that sheet's gutter under row one was wider."""


def strip_white_edges(image, white: int = WHITE, max_trim: float = MAX_TRIM):
    """Cut every edge row or column whose mean luminance says gutter."""
    import numpy as np

    grey = np.asarray(image.convert("L"), dtype=float)
    h, w = grey.shape
    top, bottom, left, right = 0, h, 0, w
    while top < h * max_trim and grey[top].mean() > white:
        top += 1
    while bottom > h * (1 - max_trim) and grey[bottom - 1].mean() > white:
        bottom -= 1
    while left < w * max_trim and grey[:, left].mean() > white:
        left += 1
    while right > w * (1 - max_trim) and grey[:, right - 1].mean() > white:
        right -= 1
    return image.crop((left, top, right, bottom))


def conform(src: Path, dst: Path, box=None) -> Path:
    from PIL import Image

    image = Image.open(src).convert("RGB")
    if box:
        image = strip_white_edges(image.crop(box))
    scale = max(W / image.width, H / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
    left, top = (resized.width - W) // 2, (resized.height - H) // 2
    resized.crop((left, top, left + W, top + H)).save(dst)
    return dst


def physicals(book: Path) -> dict[str, str]:
    return {r["entity_id"]: visual_description(r.get("physical", ""))
            for r in episode_home.read_json(book / "refs" / "refs.json")["refs"]
            if r.get("kind") == "character"}


def draw(prompt: str, images: list[Path], out: Path) -> Path:
    """One sheet from gpt-image, references attached in order.  Cached on disk."""
    if out.exists():
        return out
    _load_dotenv()
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    handles = [open(p, "rb") for p in images]
    try:
        result = client.images.edit(model=board.MODEL, image=handles, prompt=prompt,
                                    size=f"{board.CANVAS[0]}x{board.CANVAS[1]}",
                                    quality="high", n=1)
    finally:
        for h in handles:
            h.close()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(result.data[0].b64_json))
    refs = "\n".join(str(p) for p in images)
    out.with_suffix(".prompt.txt").write_text(f"{prompt}\n\nreferences, in order:\n{refs}\n",
                                              encoding="utf-8")
    return out


def sheets(book: Path, episode: Episode, frames_dir: Path) -> None:
    looks = physicals(book)
    for name, setup in episode.setups.items():
        refs = [frames_dir / f"plate_{name}.png"]
        refs += [book / "refs" / "characters" / f"char-{who}.png" for who in setup.cast]
        previous: Path | None = None
        for k, group in enumerate(board.chunks([s for s in episode.shots if s.setup == name])):
            text = board.prompt(group, setup.described, setup.cast, looks, previous is not None)
            sheet = draw(text, refs + ([previous] if previous else []),
                         frames_dir / f"board_{name}_{k}.png")
            for i, shot in enumerate(group):
                conform(sheet, frames_dir / f"S{shot.index:02d}.png", board.panel_box(i))
            print(f"  sheet {name} {k}: shots {[s.index for s in group]} -> {sheet}", flush=True)
            previous = sheet


def grids(book_id: str, number: int) -> None:
    book = episode_home.book_dir(book_id)
    sheets(book, episode_home.load_plan(book, number), episode_home.frames_dir(book, number))


# ---- the review contact sheet, after the round -----------------------------

def still(take: Path, at: float, out: Path) -> Path:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{at:.3f}", "-i", str(take),
                    "-frames:v", "1", "-vf", "scale=256:-2", str(out)], check=True)
    return out


def contact(rows: list[tuple[Path, ...]], out: Path) -> Path:
    """One row per shot: panel | take start | take end.  The END frame is where
    every drift of iterations 1-2 showed (a window appearing, a hand raised,
    a vessel gone red); the start frame alone passed them all."""
    from PIL import Image

    tiles = [tuple(Image.open(p).resize((256, 448)) for p in row) for row in rows]
    width = len(tiles[0]) if tiles else 3
    page = Image.new("RGB", (width * 268, len(tiles) * 452), "black")
    for i, row in enumerate(tiles):
        for j, tile in enumerate(row):
            page.paste(tile, (j * 268, i * 452))
    page.save(out)
    return out


def review(book_id: str, number: int) -> None:
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    home = episode_home.home(book, number)
    work = home / "work"
    work.mkdir(exist_ok=True)
    records = {r["index"]: r for r in
               episode_home.read_json(episode_home.shots_dir(book, number) / "shots.json")}
    rows = []
    for shot in episode.shots:
        if shot.index not in records:
            continue
        take = book / records[shot.index]["rel_path"]
        rows.append((home / "frames" / f"S{shot.index:02d}.png",
                     still(take, PEEK, work / f"take{shot.index:02d}.png"),
                     still(take, max(records[shot.index]["placed_seconds"] - 0.1, 0.0),
                           work / f"end{shot.index:02d}.png")))
    out = contact(rows, home / "review.png")
    print(f"{len(rows)} shots -> {out}", flush=True)


if __name__ == "__main__":
    entry = review if "--review" in sys.argv else grids
    entry(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 1)
