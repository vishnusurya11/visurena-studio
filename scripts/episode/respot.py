#!/usr/bin/env python
"""Re-spot the sub-shot cuts to the MEASURED lines.

    uv run python scripts/episode/respot.py <codex_id> <episode>

The plan's `at_s` values were placed against projected line lengths (3.0
words a second); after `say_lines.py` each shot's real length is known, so
every cut is scaled by measured/projected, kept on the MIN_SUB grid, and the
plan is rewritten.  Owner's idea (2026-09-10): build the picture from the
audio timeline, phrase by phrase.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio.episode_home import episode_arg
from studio import episode_home
from studio.episode_spec import BREATH, HANDLE, MIN_SUB, Episode


def measured_seconds(episode: Episode, shot, measured: dict[int, float]) -> float:
    lines = episode.lines_of(shot.index)
    return 2 * HANDLE + sum(measured[l.index] for l in lines) + BREATH * max(len(lines) - 1, 0) + shot.beat_s + shot.coda_s


def respot(cuts: list[float], projected: float, measured: float, minimum: float = MIN_SUB) -> list[float]:
    """Scale the cut offsets, then push them apart / pull them in so every
    sub-shot, including the last, keeps `minimum` seconds."""
    scale = measured / projected if projected else 1.0
    latest = math.floor((min(projected, measured) - minimum) * 100) / 100  # floored: the validator only knows projected
    out, last = [], 0.0
    for at in cuts:
        at = min(max(round(at * scale, 2), last + minimum), latest)
        if at - last < minimum - 1e-9:  # nowhere left for this sub-shot (or any after it)
            break
        out.append(at)
        last = at
    return out


def main(book_id: str, number: int) -> None:
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    measured = {r["index"]: r["seconds"] for r in episode_home.read_json(episode_home.lines_dir(book, number) / "lines.json")}
    plan = episode_home.read_json(episode_home.home(book, number) / "plan.json")
    moved = 0
    for shot in episode.shots:
        if not shot.cuts:
            continue
        before = [c.at_s for c in shot.cuts]
        after = respot(before, episode.shot_seconds(shot), measured_seconds(episode, shot, measured))
        entry = next(s for s in plan["shots"] if s["index"] == shot.index)
        entry["cuts"] = [dict(c, at_s=at) for c, at in zip(entry["cuts"], after)]
        moved += before != after
        print(f"  shot {shot.index:02d}: {before} -> {after}", flush=True)
    Episode(**plan)
    episode_home.write_json(episode_home.home(book, number) / "plan.json", plan)
    print(f"re-spotted {moved} shots", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], episode_arg(sys.argv))
