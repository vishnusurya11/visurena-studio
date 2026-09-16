#!/usr/bin/env python
"""One empty plate per setup, and a reference sheet for every speaker.

    uv run python scripts/episode/frames.py <codex_id> <episode>

These are what the storyboard is drawn FROM (gpt-image gets the plate and the
sheets as references); the video model never sees them.  Emptiness is stated
in the plate prompt because a plate with a figure carries that figure into
every panel.  Every plate leaves at exactly the plan's own canvas (`studio/canvas.py`).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_seq_board as sq
from studio import canvas, episode_home
from studio.comfy import run
from studio.episode_spec import Episode, Setup
from studio.trailer_refs import location_prompt

W, H = canvas.size("9:16")
"""Rebound from the plan in `main`: the plan carries the aspect."""
ASPECT = "9:16"
SEED_BASE = 61000
PLATE_WORKFLOW = "image_krea2_turbo_t2i"

def conform(src: Path, dst: Path) -> Path:
    """Centre-crop and scale any image to the H3 canvas.  Never stretch."""
    from PIL import Image

    image = Image.open(src).convert("RGB")
    scale = max(W / image.width, H / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
    left, top = (resized.width - W) // 2, (resized.height - H) // 2
    resized.crop((left, top, left + W, top + H)).save(dst)
    return dst


def sheet_for(book: Path, who: str) -> Path:
    """The character's identity BUST.

    A character the book has not bound has no invented body.  `step_02_refs.py`
    is the only thing that may create one, because it is the only thing that
    reads the render back and compares it with the words; `frames.py` inventing
    a description is how "fair side-whiskers" entered a clean-shaven man's
    record and reached his rendered sheet.
    """
    dest = book / "refs" / "characters" / f"char-{who}.png"
    if not dest.exists():
        raise SystemExit(f"{who} has no cast sheet: run step_02_refs.py, "
                         f"do not invent a body here")
    return dest


def plate(name: str, setup: Setup, palette: str, out: Path, seed: int) -> Path:
    if out.exists():
        return out
    made = run(PLATE_WORKFLOW, {"prompt": location_prompt(setup.described, palette),
                                "aspect_ratio": canvas.comfy_ratio(ASPECT), "megapixels": 1.0,
                                "seed": seed, "steps": 8, "filename_prefix": f"ep_plate_{name}"})
    return conform(made[0], out)


def main(book_id: str, number: int) -> None:
    book = episode_home.book_dir(book_id)
    episode: Episode = episode_home.load_plan(book, number)
    global W, H, ASPECT
    ASPECT, (W, H) = episode.aspect, canvas.size(episode.aspect)
    out_dir = sq.plates_in(episode_home.boards_dir(book, number))
    out_dir.mkdir(parents=True, exist_ok=True)
    # THE EPISODE'S OWN PALETTE WINS. The book's ends "1881 London", which is
    # right for Part One and wrong for every chapter from the eighth on.
    palette = episode.palette or episode_home.read_json(book / "refs" / "refs.json")["palette"]
    seed = SEED_BASE + number * 1000
    for i, (name, setup) in enumerate(episode.setups.items()):
        made = plate(name, setup, palette, out_dir / f"plate_{name}.png", seed + i)
        print(f"  plate {name}: {made}", flush=True)
        for who in setup.cast:
            sheet_for(book, who)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1)
