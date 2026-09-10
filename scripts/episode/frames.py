#!/usr/bin/env python
"""One empty 9:16 plate per setup, and a reference sheet for every speaker.

    uv run python scripts/episode/frames.py <codex_id> <episode>

These are what the storyboard is drawn FROM (gpt-image gets the plate and the
sheets as references); the video model never sees them.  Emptiness is stated
in the plate prompt because a plate with a figure carries that figure into
every panel.  Every plate leaves at exactly 768x1344, H3's 9:16 canvas.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home
from studio.comfy import run
from studio.episode_spec import Episode, Setup
from studio.trailer_refs import character_prompt, location_prompt

W, H = 768, 1344
SEED_BASE = 61000
PLATE_WORKFLOW = "image_krea2_turbo_t2i"

STAMFORD = ("A young man of about twenty-five, stout and round-faced with a fresh "
            "complexion, fair side-whiskers, wearing a dark frock coat, grey waistcoat "
            "and a white collar; a hospital dresser.")
"""The book never describes Stamford; a sheet needs a body.  Invented once, here."""


def conform(src: Path, dst: Path) -> Path:
    """Centre-crop and scale any image to the H3 canvas.  Never stretch."""
    from PIL import Image

    image = Image.open(src).convert("RGB")
    scale = max(W / image.width, H / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
    left, top = (resized.width - W) // 2, (resized.height - H) // 2
    resized.crop((left, top, left + W, top + H)).save(dst)
    return dst


def sheet_for(book: Path, who: str, palette: str, seed: int) -> Path:
    """The character's reference sheet, made once if the trailer never needed it.
    The book's `refs.json` is not touched: it is the trailer's record."""
    dest = book / "refs" / "characters" / f"char-{who}.png"
    if dest.exists():
        return dest
    physical = STAMFORD if who == "stamford" else who.replace("_", " ")
    made = run(PLATE_WORKFLOW, {"prompt": character_prompt(physical, palette),
                                "aspect_ratio": "16:9 (Widescreen)", "megapixels": 1.0,
                                "seed": seed, "steps": 8, "filename_prefix": f"ep_sheet_{who}"})
    dest.write_bytes(made[0].read_bytes())
    return dest


def plate(name: str, setup: Setup, palette: str, out: Path, seed: int) -> Path:
    if out.exists():
        return out
    made = run(PLATE_WORKFLOW, {"prompt": location_prompt(setup.described, palette),
                                "aspect_ratio": "9:16 (Portrait Widescreen)", "megapixels": 1.0,
                                "seed": seed, "steps": 8, "filename_prefix": f"ep_plate_{name}"})
    return conform(made[0], out)


def main(book_id: str, number: int) -> None:
    book = episode_home.book_dir(book_id)
    episode: Episode = episode_home.load_plan(book, number)
    out_dir = episode_home.frames_dir(book, number)
    out_dir.mkdir(parents=True, exist_ok=True)
    palette = episode_home.read_json(book / "refs" / "refs.json")["palette"]
    seed = SEED_BASE + number * 1000
    for i, (name, setup) in enumerate(episode.setups.items()):
        made = plate(name, setup, palette, out_dir / f"plate_{name}.png", seed + i)
        print(f"  plate {name}: {made}", flush=True)
        for j, who in enumerate(setup.cast):
            sheet_for(book, who, palette, seed + 500 + j)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1)
