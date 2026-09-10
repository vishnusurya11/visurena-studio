#!/usr/bin/env python
"""Derive every shot's time from the measured lines: `episodes/epNN/placed.json`.

    uv run python scripts/episode/timeline.py <codex_id> <episode>

Runs after `say_lines.py` and before any picture.  The result is the source
of every shot time downstream (panels are one per shot, takes are cut to
these seconds, the mix lays lines at these `at`s, QC checks against them).
Refuses if the measured runtime leaves the 120-180 s band.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home, episode_timeline
from studio.episode_spec import MAX_SECONDS, MIN_SECONDS


def main(book_id: str, number: int) -> None:
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    measured = {r["index"]: r["seconds"]
                for r in episode_home.read_json(episode_home.lines_dir(book, number) / "lines.json")}
    missing = [line.index for line in episode.lines if line.index not in measured]
    if missing:
        raise SystemExit(f"lines not rendered yet: {missing}")
    placed = episode_timeline.place(episode, measured)
    faults = episode_timeline.misaligned(placed)
    if faults:
        raise SystemExit("the sync rule is broken:\n  " + "\n  ".join(faults))
    out = episode_home.write_json(episode_home.home(book, number) / "placed.json", placed)
    holes = episode_timeline.holes(placed)
    speech = sum(l["seconds"] for l in placed["lines"])
    print(f"runtime {placed['duration_s']:.1f}s | speech {speech:.1f}s "
          f"({speech / placed['duration_s']:.0%}) | holes over 1.5 s: {holes} -> {out}", flush=True)
    if not MIN_SECONDS <= placed["duration_s"] <= MAX_SECONDS:
        raise SystemExit(f"measured runtime {placed['duration_s']:.1f} s is outside "
                         f"{MIN_SECONDS:.0f}-{MAX_SECONDS:.0f}: add or cut lines in the plan")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1)
