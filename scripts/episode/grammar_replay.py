#!/usr/bin/env python
"""Replay the anime-TV grammar's gates over every plan on disk (2026-10-17).

    uv run python scripts/episode/grammar_replay.py <codex> [<codex> ...] [--out=<file.json>]

Reads each `episodes/epNN/plan.json` of the named books (and any extra plan file
given as `<codex>:<epNN>/<file>`), with that episode's recorded voice, and prints
per plan: the shot count, the size mix, the face share, the pushes and the fault
count of every grammar gate.  The calibration a gate is hardened on: a wall that
fires on an owner-approved episode for a reason the owner has not ruled against
stays advice.  Reads plan.json files by name only (the HDD rule).  $0.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home, framing_grammar as fg, grammar_battery, plan_gates  # noqa: E402
from studio.episode_spec import Episode  # noqa: E402

GATE = re.compile(r"^(G-[A-Z]+)")


def plan_paths(book: Path) -> list[Path]:
    """Every episode's plan.json, in episode order (one glob, one folder level)."""
    return sorted((book / "episodes").glob("ep[0-9][0-9]/plan.json"))


def load(path: Path, book: Path) -> Episode | None:
    """The plan at the series rate; None when the contract refuses it."""
    number = int(path.parent.name[2:4])
    try:
        return Episode(**plan_gates.at_series_rate(episode_home.read_json(path), book, number))
    except Exception:          # a historical plan the contract no longer reads is reported, not judged
        return None


def mix(episode) -> dict:
    """Size counts, the face share, pushes and the locked share of a plan."""
    shots = fg.cut(episode)
    verbs = Counter(fg.verb(s) for s in shots)
    return {"shots": len(shots), "sizes": dict(Counter(s.size for s in shots)),
            "face_share": round(sum(fg.face_shot(s) for s in shots) / len(shots), 2),
            "pushes": verbs.get("push_slow", 0), "locked_share": round(verbs.get("locked", 0) / len(shots), 2)}


def gate_counts(rows: list[str]) -> dict[str, int]:
    return dict(Counter(m.group(1) for r in rows if (m := GATE.match(r))))


def replay(book: Path, path: Path) -> dict:
    """One plan's row: its mix and its grammar fault counts, at its own voice."""
    number = int(path.parent.name[2:4])
    plan_gates.use_voice(book, number)
    episode = load(path, book)
    if episode is None:
        return {"book": book.name, "plan": str(path.relative_to(book)), "refused_by_contract": True}
    rate = plan_gates.series_rate(book, number)
    rows = grammar_battery.faults(episode, rate)
    return {"book": book.name, "plan": str(path.relative_to(book)), **mix(episode),
            "faults": gate_counts(rows), "rows": rows}


def targets(args: list[str]) -> list[tuple[Path, Path]]:
    """(book, plan path) for each `<codex>` (every episode) or `<codex>:<rel path>`."""
    out = []
    for arg in args:
        codex, _, rel = arg.partition(":")
        book = episode_home.book_dir(codex)
        out += [(book, book / "episodes" / rel)] if rel else [(book, p) for p in plan_paths(book)]
    return out


def main(argv: list[str]) -> int:
    out = next((a.split("=", 1)[1] for a in argv if a.startswith("--out=")), "")
    rows = [replay(book, path) for book, path in targets([a for a in argv if not a.startswith("--")])]
    for r in rows:
        print(r["plan"], {k: r.get(k) for k in ("shots", "face_share", "pushes", "locked_share", "faults")})
    if out:
        Path(out).write_text(json.dumps(rows, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
