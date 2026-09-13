#!/usr/bin/env python
"""ONE character's identity BUST, drawn locally and free.

    uv run python scripts/episode/cast_bust.py <codex_id> <who>

A chapter that brings a character nobody has drawn is a row in the episode
skill's entry table, and this is the script that serves it.

`scripts/trailer/build_refs.py` also draws busts, but it draws the WHOLE cast
and then REWRITES `refs/refs.json` from what it drew -- which deletes every
hand-authored `wardrobe`, `sheet` and `cards` block on every character already
bound.  Chapter II of A Study in Scarlet needed exactly one new bust (the
commissionaire, who speaks the episode's last line), so it needed a scalpel and
not the hammer.

The bust is LOCAL: Krea2 turbo on the owner's own GPU, no money.  Only the
wardrobe CARD costs anything, and that is `cast_cards.py --draw`, already
gated at ESCALATE.

The body is never invented here.  A character the book has not bound in
refs.json is refused, because inventing a description is how "fair
side-whiskers" entered a clean-shaven man's record and reached his sheet.
"""
from __future__ import annotations

import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import cast_refs, episode_home
from studio.trailer_refs import character_prompt

SEED_BASE = 40000
"""The same base `build_refs.py` uses, so a bust drawn here and a bust drawn
there are the same family of picture."""


def seed_for(who: str, tries: int = 0) -> int:
    """A stable seed from the entity id, so redrawing a character is the same
    picture rather than a lottery.  `build_refs.py` seeds by list POSITION,
    which means inserting one character reshuffles everybody after it.

    `tries` nudges it, because the stability cuts both ways: a bust that came
    back contradicting its own contract would come back identical on the same
    seed however the words were sharpened."""
    return SEED_BASE + zlib.crc32(who.encode("utf-8")) % 100_000 + tries


def prompt_for(book: Path, who: str) -> str:
    """The bust prompt: the body first, then the frame, then the palette."""
    row = cast_refs.row(book, who)
    palette = episode_home.read_json(book / "refs" / "refs.json")["palette"]
    return character_prompt(row.get("physical", ""), palette)


def target(book: Path, who: str) -> Path:
    """Where this character's bust lives, as the row itself declares."""
    return cast_refs.bust(book, who)


def render(prompt: str, prefix: str, seed: int, dest: Path) -> Path:
    """The one ComfyUI call.  Injected in tests so no test touches the GPU."""
    from studio.comfy import run

    written = run("image_krea2_turbo_t2i", {
        "prompt": prompt, "aspect_ratio": "1:1 (Square)", "megapixels": 1.0,
        "seed": seed, "steps": 8, "filename_prefix": prefix})
    if not written:
        raise RuntimeError(f"{prefix} produced no image")
    dest.write_bytes(written[0].read_bytes())
    return dest


def supersede(path: Path) -> Path | None:
    """Keep the picture being replaced, free and on disk, before replacing it."""
    import shutil
    import time

    if not path.exists():
        return None
    kept = path.parent / ".superseded" / f"{path.stem}.{time.strftime('%Y%m%dT%H%M%S')}.png"
    kept.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, kept)
    return kept


def draw(book: Path, who: str, render=render, redraw: bool = False, tries: int = 1) -> Path:
    """The bust, drawn once.  A bust on disk is never redrawn unless asked: it
    is the identity every later picture of this person is bound to.

    `redraw` is for the one case that earns it -- the picture contradicts its
    own contract, so the reference and the words are saying different things,
    which is exactly what `cast_cards --check` refuses.  Sharpen the words in
    refs.json first, then redraw; the old picture is kept."""
    out = target(book, who)
    if out.exists():
        if not redraw:
            return out
        supersede(out)
    said = prompt_for(book, who)
    out.parent.mkdir(parents=True, exist_ok=True)
    return render(said, f"REF-{cast_refs.row(book, who)['ref_id']}",
                  seed_for(who, tries if redraw else 0), out)


def main(argv: list[str]) -> None:
    book = episode_home.book_dir(argv[1])
    tries = next((int(a.split("=", 1)[1]) for a in argv if a.startswith("--tries=")), 1)
    made = draw(book, argv[2], redraw="--redraw" in argv, tries=tries)
    print(made)


if __name__ == "__main__":
    main(sys.argv)
