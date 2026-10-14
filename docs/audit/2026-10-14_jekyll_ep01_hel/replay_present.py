"""Replay G-PRESENT over every plan on disk of WotW, Scarlet and Jekyll ($0, CPU).

    uv run python docs/audit/2026-10-14_jekyll_ep01_hel/replay_present.py

Prints one row per plan: G-PRESENT faults (appears mid-scene / an unshown entrance
or exit) and G-PRESENT-WIDE advisories (a wide leaves someone out), and whether the
battery would count G-PRESENT hard (nothing drawn) or as advice (rendered)."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from studio import episode_spec as spec, plan_gates  # noqa: E402

BOOKS = {"wotw": "20260827135508_the-war-of-the-worlds", "scarlet": "20260822113400_a-study-in-scarlet",
         "jekyll": "20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde"}


def kind(f: str) -> str:
    """The fault's family, for the totals."""
    return "appears" if "appears mid-scene" in f else "wide_drop" if "leaves out" in f else "unshown_move"


def episode_of(path: Path):
    doc = json.loads(path.read_text(encoding="utf-8"))
    try:
        return spec.Episode(**doc)
    except Exception:
        return spec.Episode.model_construct(shots=[spec.Shot.model_construct(**s, enters=[], exits=[])
                                                   for s in doc["shots"]])


def main() -> None:
    total = Counter()
    for short, folder in BOOKS.items():
        book = ROOT / "library" / folder
        names = plan_gates.names_from_refs(json.loads((book / "refs" / "refs.json").read_text(encoding="utf-8"))["refs"])
        for plan in sorted((book / "episodes").glob("ep[0-9][0-9]/plan.json")):
            e = episode_of(plan)
            found = plan_gates.present_faults(e, names) + plan_gates.present_advisories(e, names)
            drawn = (plan.parent / "storyboard" / "grids").exists() or (plan.parent / "takes").exists()
            by = Counter(kind(f) for f in found)
            total.update({f"{short}_{k}": v for k, v in by.items()})
            print(f"{short:8} {plan.parent.name}  {len(found):3d}  {dict(by)}  {'advice (rendered)' if drawn else 'HARD'}")
            for f in found:
                print("     ", f[:190])
    print("TOTAL", dict(total))


if __name__ == "__main__":
    main()
