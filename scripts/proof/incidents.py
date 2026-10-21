"""Tally every recorded way a run stopped, by class, and map each class to a rehearsal scenario.

    uv run --no-sync python scripts/proof/incidents.py [--out <incidents.json>] [--root <library>]

DESIGN 2026-10-21_ep02_proof 4.5 (package P2).  Read-only, $0, minutes: Jekyll ep01 and the
last 10 War of the Worlds and last 10 Study in Scarlet episodes, each record opened BY NAME,
one file at a time (studio/rehearsal/incidents.py).  Classes come from
scripts/proof/incidents_map.yaml; a class no rule knows is UNCOVERED.  Writes
results/incidents.json beside the design (git-ignored) and prints the first line as its path."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import settings  # noqa: E402
from studio.rehearsal import incidents  # noqa: E402

MAP = Path(__file__).resolve().parent / "incidents_map.yaml"
OUT = ROOT / "docs" / "audit" / "2026-10-21_ep02_proof" / "results" / "incidents.json"
BOOKS = (("20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde", [1]),
         ("20260827135508_the-war-of-the-worlds", 10),
         ("20260822113400_a-study-in-scarlet", 10))
"""(book folder, the episode numbers or how many of the last to read)."""


def plan_of(root: Path, books=None) -> list[tuple[str, list[int]]]:
    """Each book's episode numbers: a list as given, a count as that many of the last."""
    books = BOOKS if books is None else books
    return [(name, want if isinstance(want, list) else incidents.episode_numbers(Path(root) / name, last=want))
            for name, want in books]


def report_lines(out: dict, path: Path) -> list[str]:
    """The printed summary: the path first, then each episode's ledger and the coverage row."""
    lines = [str(path)]
    for ep, row in out["episodes"].items():
        d = row["drive"]
        if row.get("records") == "absent":
            lines.append(f"{ep}: drive records absent (no drive.jsonl): not in the sample, never 0 incidents")
            continue
        lines.append(f"{ep}: start {d.get('start', 0)} end {d.get('end', 0)} | incidents {row['incidents']}"
                     f" | {', '.join(f'{k} x{v}' for k, v in d.get('outcomes', {}).items())}")
    sample = out.get("sample") or {}
    lines.append(f"sample: {sample.get('read', 0)} episodes with drive records, {sample.get('absent', 0)} absent")
    lines.append(f"classes recorded {out['recorded']}, mapped to a scenario {out['mapped']}, "
                 f"UNCOVERED {len(out['uncovered'])}")
    lines += [f"  {cid}: {row['count']} -> {row['scenario']}" for cid, row in out["classes"].items()]
    return lines


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out", type=Path, default=OUT)
    p.add_argument("--root", type=Path, default=settings.REAL_LIBRARY)
    args = p.parse_args(argv)
    out = incidents.survey(plan_of(args.root), args.root, incidents.load_rules(MAP))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("\n".join(report_lines(out, args.out.resolve())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
