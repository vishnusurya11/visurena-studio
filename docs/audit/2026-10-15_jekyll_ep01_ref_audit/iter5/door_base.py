"""Owner decision 2026-10-15 (item 7): ONE door base picture for the house, every setup that shows
the door a one-step state of it.

The episode's three doors (03_visual_qa.md fault 1) came from three pictures: the base
`wide_establishing.png` (a plank door with an eye in a black splat), its night state (the same
plank door), and a second FRESH master `court_entry_pavement.png` (an arched brick court). The
door the audits liked -- the grey gable block, the blistered red-black door in its recess above
two steps, the kerb lamp -- exists only in the door_day anchor panel (T00-T02, T22).

So the base is that anchor with the two men taken out: ONE 2511 edit of a picture already drawn,
never a fresh room from words. The old pictures go to superseded/; `places.py --draw` then derives
each state (day scorch, night, pavement, as the setups name them) as ONE edit of this base.

    uv run python docs/audit/2026-10-15_jekyll_ep01_ref_audit/iter5/door_base.py
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "refs"))

import places  # noqa: E402

BOOK = ROOT / "library" / "20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde"
LOC = BOOK / "refs" / "locations" / "black_mail_house_door"
ANCHOR = BOOK / "episodes" / "ep01" / "storyboard" / "anchors" / "door_day.png"
STAMP = "2026-10-15_three_doors"
PROMPT = ("Remove the two men in hats and the cane from the pavement at the left. Keep everything else "
          "exactly as it is: the grey plaster gable block, the blistered red-black door in its recess above "
          "its two stone steps, the iron gas lamp at the kerb, the shop fronts at both edges, the cobbles and "
          "the grey daylight, seen from the same camera position. The pavement where the men stood is bare "
          "flagstones.")


def retire() -> None:
    """Every old door picture to superseded/, under one stamp."""
    old = LOC / "superseded"
    old.mkdir(exist_ok=True)
    for png in sorted(LOC.glob("*.png")):
        png.replace(old / f"{png.stem}_{STAMP}.png")


def main() -> None:
    retire()
    target = LOC / "wide_establishing.png"
    places.qwen_edit(BOOK)(PROMPT, ANCHOR, target)
    places.record_master(BOOK, "black_mail_house_door", "wide_establishing")
    print(f"door base -> {target}")


if __name__ == "__main__":
    main()
