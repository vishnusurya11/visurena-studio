#!/usr/bin/env python
"""The deterministic prompt lint (P1-P18) on one episode's take prompts, plan and files.

    uv run python scripts/episode/prompt_lint.py <book dir> <episode>

Reads episodes/epNN/takes/r2v/prompts.json, plan.json, refs/refs.json and
refs/look.json; prints every fault, then "PROMPT LINT: clean" or
"PROMPT LINT: <N> faults"; exit 1 on any fault.  $0, read-only.  Adds the
grid-side lint (studio/grid_lint.py) when that module exists.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import prompt_lint as pl


def grid_faults(book: Path, number: int) -> list[str]:
    """studio.grid_lint's faults when it is installed; nothing otherwise."""
    try:
        from studio import grid_lint
    except ImportError:
        return []
    run = getattr(grid_lint, "episode_faults", None) or getattr(grid_lint, "lint_episode", None)
    got = run(book, number) if run else []
    if isinstance(got, dict):
        return [f"{k} {f}" for k, fs in got.items() for f in (fs if isinstance(fs, list) else [fs])]
    return list(got or [])


def lines(report: dict) -> list[str]:
    """One printable line per fault, each led by where it was found."""
    out = [f"T{idx:02d} {f}" for idx, fs in sorted(report["takes"].items()) for f in fs]
    out += [f"plan {f}" for f in report["plan"]]
    out += [f"files {f}" for f in report["files"]]
    return out + [f"grid {f}" for f in report.get("grid", [])]


def main(argv: list[str]) -> int:
    """Print every fault and the verdict line; 1 on any fault."""
    if len(argv) != 2:
        print(__doc__)
        return 2
    book, number = Path(argv[0]), int(argv[1])
    report = {**pl.lint_episode(book, number), "grid": grid_faults(book, number)}
    found = lines(report)
    for line in found:
        print(line)
    print(f"PROMPT LINT: {len(found)} faults" if found else "PROMPT LINT: clean")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
