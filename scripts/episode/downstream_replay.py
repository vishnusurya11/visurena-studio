#!/usr/bin/env python
"""The steps after the plan sign, replayed read-only on a signed plan.json -- $0, no GPU.

    uv run python scripts/episode/downstream_replay.py <codex_id> <episode>

Jekyll Kawajiri ep01 (2026-10-18) parked three times for CODE-RULER faults, 10 minutes of
wall time: step 05's packer read the legacy 8 s budget on a grammar plan (5d3dc08) and
step 06's lint read a band no panel yet satisfied (5c23230).  Each ruler was a free check
a script could have run the moment the plan was signed.  Three checks:

  1. step_05 `packed()` returns [] (the timeline never packs a pair the take builder won't);
  2. `plan_cures.holds` on a deep copy moves no shot's seconds past HOLD_TOL_S;
  3. the takes_r2v prompt lint runs dry (skipped without a book).

It reads the named plan.json (and the recorded voice) and writes nothing beside it.  ADVISORY:
it prints ruler rows and exits 1 on any; nothing drives it.  It becomes a blocker only once it
is clean on ep01 and on one WotW plan.
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from studio import episode_home, episode_spec as spec, plan_cures, plan_gates  # noqa: E402

HOLD_TOL_S = 0.25
"""One handle (plan_check.HANDLE): the rulers round to a hundredth, so a plan cured to the
G-HOLE wall (ep01: 5.5) sits within a few hundredths of where holds would shave it."""


def load(plan) -> dict:
    """The plan doc: a dict as given, or the named plan.json read once."""
    if isinstance(plan, dict):
        return plan
    return json.loads(Path(plan).read_text(encoding="utf-8"))


@contextmanager
def voiced(voice: dict | None):
    """Every projection inside reads this voice, then the process's own comes back."""
    token = plan_gates.VOICE.set(dict(voice or {}))
    try:
        yield
    finally:
        plan_gates.VOICE.reset(token)


@contextmanager
def measured_as(step05, doc: dict, rate: float):
    """step 05's `placed_of` reads the plan's own projection (no timeline on disk is read)."""
    import plan_check
    ep = spec.Episode(**doc)
    rows = plan_check.projected(ep, rate, voice=bool(plan_gates.VOICE.get()))
    old = step05.placed_of
    step05.placed_of = lambda book, number: {"shots": [{"index": r["index"], "seconds": r["seconds"]} for r in rows]}
    try:
        yield
    finally:
        step05.placed_of = old


def packed_runs(doc: dict, rate: float, voice: dict | None = None, step05=None) -> list[list[int]]:
    """step 05's own `packed()` on the plan's projected timeline, in a throwaway home."""
    if step05 is None:
        import step_05_timeline as step05
    with tempfile.TemporaryDirectory() as tmp, voiced(voice), measured_as(step05, doc, rate):
        home = episode_home.home(Path(tmp), 1)
        home.mkdir(parents=True)
        (home / "plan.json").write_text(json.dumps(doc), encoding="utf-8")
        return step05.packed(SimpleNamespace(book_dir=Path(tmp), number=1))


def holds_drift(doc: dict, rate: float, voice: dict | None = None) -> list[str]:
    """A ruler row per shot the hold cure would still move past HOLD_TOL_S."""
    with voiced(voice):
        before = plan_cures._shot_secs(doc, rate)
        after = plan_cures._shot_secs(plan_cures.holds(copy.deepcopy(doc), rate), rate)
    return [f"RULER holds would move shot {i} by {after[i] - before[i]:+.2f} s"
            for i in sorted(before) if abs(after[i] - before[i]) > HOLD_TOL_S]


def replay(plan, rate: float | None = None, voice: dict | None = None, step05=None, lint=None) -> list[str]:
    """Every ruler row (empty = clean); `lint(doc, rate)` is the dry prompt lint, skipped when None."""
    doc = load(plan)
    rate = rate or doc.get("words_per_second") or spec.STUDIO_RATE
    rows = []
    if pairs := packed_runs(doc, rate, voice, step05):
        rows.append(f"RULER step 05 packs {pairs} into one take on a plan the take builder cuts one shot per take")
    rows += holds_drift(doc, rate, voice)
    with voiced(voice):
        rows += [f"RULER prompt lint: {row}" for row in (lint(doc, rate) if lint else [])]
    return rows


def book_lint(book: Path, number: int):
    """The dry prompt lint of this book: takes_r2v's own, as G-TAKELINT runs it."""
    def lint(doc: dict, rate: float) -> list[str]:
        import plan_check
        import takes_r2v
        ep = spec.Episode(**doc)
        try:
            return takes_r2v.dry_faults(book, ep, number, plan_check.projected(ep, rate, voice=False), rate=rate)
        except SystemExit as why:
            return [f"dry build refused: {str(why)[:150]}"]
    return lint


def main(book_id: str, number: int) -> int:
    book = episode_home.book_dir(book_id)
    path = episode_home.plan_path(book, number)
    rows = replay(path, rate=plan_gates.series_rate(book, number),
                  voice=plan_gates.voice_of(book, number), lint=book_lint(book, number))
    print("DOWNSTREAM REPLAY:", f"{len(rows)} ruler fault(s)" if rows else "clean", "(advisory)")
    for row in rows:
        print("   ", row[:170])
    return 1 if rows else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], int(sys.argv[2])))
