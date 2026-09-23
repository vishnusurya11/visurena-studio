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

from studio.episode_home import episode_arg
from studio import episode_seq_board as sq
from studio import house_style
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


def plate_prompt(setup: Setup, where: str, light: str) -> str:
    """The plate's prompt: the place, the light, and the setup's own words.

    NEVER THE PALETTE.  ep09's palette objects -- "gold ripe wheat, red road
    dust and deep green pine" -- were drawn as a gold wheat foreground into
    five of six plates, including the bare rock shoulder (report, cause 8).
    The plate's light comes from the SETUP, which names its own source with a
    direction (G-LIGHT holds it to that); the plan's `light` is the default
    for a setup that has none."""
    own = not house_style.setup_faults(setup.described, setup.outdoors)
    return location_prompt(setup.described, where if own else f"{where}, {light}")


PLATE_ROLLS = 3
"""Letterboxed rolls before the run stops: ep11's parlour at night came back
padded with white bars on two seeds running, and nothing refused it."""
ROLL_STEP = 100


def plate_rolled(draw, out: Path, seed: int) -> Path:
    """Draw with `draw(seed)` until the picture fills its frame; a letterboxed
    roll is kept beside the plate as `rejected/<name>.bars<k>.png`."""
    from PIL import Image

    from studio import plate_gate

    for k in range(PLATE_ROLLS):
        made = conform(draw(seed + k * ROLL_STEP), out)
        if not plate_gate.letterboxed(Image.open(made)):
            return made
        aside = out.parent / "rejected" / f"{out.stem}.bars{k + 1}{out.suffix}"
        aside.parent.mkdir(parents=True, exist_ok=True)
        made.replace(aside)
    raise SystemExit(f"{out.name}: letterboxed on {PLATE_ROLLS} seeds; the prompt draws a wide picture -- "
                     f"say the room closes on four sides and the camera stands inside it")


def plate(name: str, setup: Setup, where: str, light: str, out: Path, seed: int) -> Path:
    if out.exists():
        return out

    def draw(s: int) -> Path:
        return run(PLATE_WORKFLOW, {"prompt": plate_prompt(setup, where, light),
                                    "aspect_ratio": canvas.comfy_ratio(ASPECT), "megapixels": 1.0,
                                    "seed": s, "steps": 8, "filename_prefix": f"ep_plate_{name}"})[0]

    return plate_rolled(draw, out, seed)


def refuse_unlit(episode: Episode) -> None:
    """G-LIGHT, before the first plate: a plan whose light is missing,
    directionless, shadowless or an inventory draws nothing."""
    if bad := house_style.faults(episode):
        raise SystemExit("G-LIGHT refuses the plan:\n  " + "\n  ".join(bad))


def main(book_id: str, number: int) -> None:
    book = episode_home.book_dir(book_id)
    episode: Episode = episode_home.load_plan(book, number)
    global W, H, ASPECT
    # THE RUN DECLARES ITS PLACE AND ITS LIGHT before it makes anything.
    # Episode 8 was drawn and rendered saying "1881 London" over an 1847 Utah
    # desert because the palette reached the location plate alone; episode 9
    # was drawn under a colour inventory with no direction and no black.
    house_style.adopt(episode.where, episode.light)
    refuse_unlit(episode)
    ASPECT, (W, H) = episode.aspect, canvas.size(episode.aspect)
    out_dir = sq.plates_in(episode_home.boards_dir(book, number))
    out_dir.mkdir(parents=True, exist_ok=True)
    seed = SEED_BASE + number * 1000
    for i, (name, setup) in enumerate(episode.setups.items()):
        made = plate(name, setup, house_style.where(), house_style.light(),
                     out_dir / f"plate_{name}.png", seed + i)
        print(f"  plate {name}: {made}", flush=True)
        for who in setup.cast:
            sheet_for(book, who)


if __name__ == "__main__":
    main(sys.argv[1], episode_arg(sys.argv))
