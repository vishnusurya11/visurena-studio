#!/usr/bin/env python
"""Step 04 -- record: every line in its character's voice, measured and listened to.

    uv run python scripts/episode/step_04_record.py <codex_id> <n> [--redo=3,4]

Wraps scripts/episode/say_lines.py (local TTS + the ear, GPU) and then
scripts/episode/speaker_check.py (one speaker, one voice; CPU).  Done when
lines.json carries every line the plan names and the spread report exists.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home, step_cli  # noqa: E402

STEP_ID = "04"
NAME = "record"
GPU = True


def rendered(plan: dict, rows: list[dict]) -> bool:
    """Whether every line the plan names has a measured row."""
    have = {r.get("index") for r in rows}
    return all(line.get("index") in have for line in plan.get("lines") or [])


REVOICED = "speaker_revoiced.json"
"""review/<this>: the rounds of lines said again for a split voice."""
REVOICE_ROUNDS = 3
"""ep21 (2026-10-08): round one cured nine of ten pairs; the tenth wanted a
line round one's cover had not chosen."""


def split_lines(report: dict, said: set[int] = frozenset()) -> list[int]:
    """The fewest lines that cover every pair under its floor (greedy: the
    line in most uncovered pairs first, a line not yet said again before one
    that was, then by name).  ep21: ten narrator pairs, three lines."""
    pairs = [tuple(p) for row in report.values() if isinstance(row, dict) and not row.get("ok", True)
             for p in row.get("under") or []]
    chosen: list[str] = []
    while pairs:
        counts: dict[str, int] = {}
        for pair in pairs:
            for stem in pair:
                counts[stem] = counts.get(stem, 0) + 1
        pick = min(counts, key=lambda s: (-counts[s], int(s[1:]) in said, s))
        chosen.append(pick)
        pairs = [p for p in pairs if pick not in p]
    return sorted(int(s[1:]) for s in chosen)


def rounds(ctx) -> list[list[int]]:
    """The revoice rounds taken; a flat list is the one-round file of 15:33Z."""
    path = ctx.home / "review" / REVOICED
    if not path.exists():
        return []
    doc = episode_home.read_json(path)
    return [doc] if doc and not isinstance(doc[0], list) else doc


def done(ctx) -> bool:
    """Every line recorded AND the voice check read: a split voice is done
    only when it holds or REVOICE_ROUNDS rounds were said again (ep21: the
    split surfaced at the upload door, after every picture -- the report
    merely existed)."""
    plan, sheet = ctx.home / "plan.json", ctx.home / "audio" / "lines" / "lines.json"
    spread = ctx.home / "review" / "speaker_check.json"
    if not (plan.exists() and sheet.exists() and spread.exists()):
        return False
    report = episode_home.read_json(spread)
    unlisted = any(isinstance(r, dict) and not r.get("ok", True) and "under" not in r for r in report.values())
    if (unlisted or split_lines(report)) and len(rounds(ctx)) < REVOICE_ROUNDS:
        return False            # a split, or a split written before its pairs were kept
    return rendered(episode_home.read_json(plan), episode_home.read_json(sheet))


def voiceless(ctx) -> list[str]:
    """This plan's speakers with no design clip at book level: cast them first,
    just in time, so the line never waits on the bible for a voice."""
    from studio import cast_home
    plan = episode_home.read_json(ctx.home / "plan.json")
    who = {line.get("speaker") or line.get("who") for line in plan.get("lines") or []}
    return sorted(w for w in who if w and not cast_home.clip(ctx.book_dir, w).exists())


def run(ctx) -> None:
    if missing := voiceless(ctx):
        ctx.run_script("scripts/cast/cast_voices.py", f"--only={','.join(missing)}", gpu=GPU, clock="cast")
    extra = getattr(ctx, "extra", None) or []
    ctx.run_script("scripts/episode/say_lines.py", *extra, gpu=GPU, clock="lines")
    ctx.run_script("scripts/episode/speaker_check.py", clock="speaker_check")
    revoice(ctx)


def revoice(ctx) -> None:
    """A split voice: the covering lines said again on a fresh seed and the
    voice checked again, up to REVOICE_ROUNDS rounds; the door judges the rest."""
    spread = ctx.home / "review" / "speaker_check.json"
    while spread.exists() and len(taken := rounds(ctx)) < REVOICE_ROUNDS:
        said = {i for r in taken for i in r}
        lines = split_lines(episode_home.read_json(spread), said)
        if not lines:
            return
        ctx.run_script("scripts/episode/say_lines.py", f"--redo={','.join(map(str, lines))}",
                       gpu=GPU, clock="lines")
        episode_home.write_json(ctx.home / "review" / REVOICED, taken + [lines])
        ctx.run_script("scripts/episode/speaker_check.py", clock="speaker_check")


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
