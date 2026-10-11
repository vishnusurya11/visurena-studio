#!/usr/bin/env python
"""The continuity slice's HOUSE replay (verdict S §6). GPU, local, $0 -- run only
in an owner-approved GPU window; it writes only under --out.

    uv run python scripts/refs/place_replay.py <book_id> --out=<dir>

Two WotW cases, each ONE 2511 edit of the place's master (decision 2026-10-10):
  * ep26 villa_front: narrators_home/wide_establishing, abandoned -- the forced
    door, dust, the smashed privet and red weed (the shipped panel showed the
    intact ep01 house);
  * ep27 study_reverse: narrators_study/wide_establishing seen from its opposite
    wall (the shipped `reverse` was a fresh room drawn from words).
Each lands as <case>.png beside a strip: master | variant | the shipped picture.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home  # noqa: E402

CASES = {
    "ep26_villa_abandoned": ("narrators_home", "wide_establishing",
                             "the front door stands forced open on its hinge, dust on every window sill, "
                             "the privet hedge smashed and trailing red weed", "wide_establishing"),
    "ep27_study_reverse": ("narrators_study", "wide_establishing",
                           "the camera turned round to face the opposite wall of this same room, "
                           "its door and bookcase now in view", "reverse"),
}
"""case -> (location, master view, the one change, the shipped view to compare)."""


def sources(book: Path, case: str) -> tuple[Path, Path]:
    """(the master the edit starts from, the shipped picture it is compared with)."""
    loc, master, _, shipped = CASES[case]
    folder = Path(book) / "refs" / "locations" / loc
    return folder / f"{master}.png", folder / f"{shipped}.png"


def run_case(book: Path, case: str, out: Path, edit) -> Path:
    """One edit of the master into `out`, then its strip."""
    from scripts.refs import look_replay, places
    master, shipped = sources(book, case)
    target = out / f"{case}.png"
    edit(places.derive_prompt(CASES[case][2]), master, target)
    trio = out / f"{case}_strip_master_variant.png"
    look_replay.strip(master, target, trio)
    look_replay.strip(trio, shipped, out / f"{case}_strip.png")
    return target


def comfy_edit():
    from studio.comfy import run, stage_image

    def edit(prompt: str, source: Path, target: Path) -> None:
        made = run("image_qwen_image_edit_2511_single_image",
                   {"prompt": prompt, "image_1": stage_image(source), "lightning": True, "seed": 2026101})[0]
        shutil.copyfile(made, target)
    return edit


def main(book_id: str, out: str) -> int:
    book, folder = episode_home.book_dir(book_id), Path(out)
    folder.mkdir(parents=True, exist_ok=True)
    for case in CASES:
        print(f"  {case}: {run_case(book, case, folder, comfy_edit())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], next(a.split("=", 1)[1] for a in sys.argv if a.startswith("--out="))))
