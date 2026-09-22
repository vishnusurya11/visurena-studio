#!/usr/bin/env python
"""Every free gate on a plan, in one command, before anything renders.

    uv run python scripts/episode/plan_check.py <codex_id> <episode>

MEASURED on episode 11 (2026-09-17): thirteen line runs, because each edit --
the dialogue dial, the turn ratio, the projection, the sync rule, a shot longer
than a take, a landmark size off the ladder -- was found by the NEXT gate on
the road, after a GPU stage had already paid for the previous one.  This says
everything at once: the contract, G-LIGHT, the plan gates with G-NAMES and
G-RATE, the motion lints, the marks, the actor gate, the cast binding, the
per-shot take length at the narrator's measured rate, and the sheet gate's
text read.  Exit 1 on any refusal; advisories print.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from studio import actor_gate, episode_home, episode_ref_official as ro, episode_spec as spec, house_style, plan_gates, timeline_fresh
from studio import episode_takes as tk
from studio.episode_takes import BUDGET

HANDLE, BREATH = 0.25, 0.70


def contract(book: Path, number: int):
    """The plan under the contract, or every distinct refusal printed and None."""
    doc = episode_home.read_json(episode_home.home(book, number) / "plan.json")
    try:
        return spec.Episode(**doc)
    except Exception as e:  # pydantic's message carries every refusal
        seen = set()
        for m in re.finditer(r"^(\S+)\n  (?:Value error, )?(.{0,170})", str(e), re.M):
            if (k := (m.group(1), m.group(2)[:60])) not in seen:
                seen.add(k)
                print("CONTRACT:", m.group(1), "::", m.group(2))
        if not seen:
            print("CONTRACT:", str(e)[:600])
        return None


def long_shots(episode, rate: float, budget: float = BUDGET) -> list[tuple[int, float]]:
    """(shot, projected seconds) for every shot that projects past a take at the
    narrator's measured rate: handles, words, a breath between two lines, the
    beat and the coda.  The dry build finds these after the lines render."""
    out = []
    for s in episode.shots:
        words = [len(l.text.split()) for l in episode.lines if l.shot == s.index]
        seconds = 2 * HANDLE + sum(words) / rate + BREATH * max(0, len(words) - 1) + s.beat_s + s.coda_s
        if seconds > budget + 1e-6:
            out.append((s.index, round(seconds, 2)))
    return out


def projected(episode, rate: float) -> list[dict]:
    """Each shot as the timeline would place it, at the narrator's measured rate."""
    out = []
    for s in episode.shots:
        words = [len(l.text.split()) for l in episode.lines if l.shot == s.index]
        seconds = 2 * HANDLE + sum(words) / rate + BREATH * max(0, len(words) - 1) + s.beat_s + s.coda_s
        out.append({"index": s.index, "seconds": seconds, "setup": s.setup, "cuts": list(getattr(s, "cuts", []))})
    return out


def packed_shots(episode, rate: float) -> list[tuple[int, ...]]:
    """Runs of shots the take packer would put into ONE take (ep12 shot 21: a
    1.7 s reaction packed after a 5.5 s dialogue shot, an internal cut the
    model had to place).  One shot per take is the rule since episode 4."""
    return [tuple(run) for run in tk.groups(projected(episode, rate)) if len(run) > 1]


def unpaced_shots(episode) -> list[tuple[int, str]]:
    """(shot, gait word) where the frame, motion or at-rest has a person's gait
    and no pace word -- the dry build's L8, read on the plan before a sheet is
    paid for.  ADVISORY: the lint proper reads the BUILT prompt, where a
    wardrobe clause ("riding skirt") has been rewritten from the cast row."""
    out = []
    for s in episode.shots:
        body = " ".join([s.frame, s.motion, getattr(s, "at_rest", "") or ""])
        hits = ro.gaits(body)
        if hits and not any(p in body.lower() for p in ro.PACE):
            out.append((s.index, hits[0].group(0)))
    return out


def measured_or_projected(book: Path, number: int, episode, rate: float) -> list[dict]:
    """The timeline's own shots when it has been written, else the projection."""
    placed = episode_home.home(book, number) / "placed.json"
    if placed.exists():
        if why := timeline_fresh.stale(episode, episode_home.read_json(placed)):
            raise SystemExit(f"TIMELINE     : {why[0]}")
        by = {s.index: s for s in episode.shots}
        return [dict(s, setup=by[s["index"]].setup, cuts=list(by[s["index"]].cuts))
                for s in episode_home.read_json(placed)["shots"] if s["index"] in by]
    return projected(episode, rate)


def sheet_text(book_id: str, number: int) -> int:
    """The sheet gate's text-only read, as `sheet_dq.py` prints it; hard count."""
    run = subprocess.run([sys.executable, str(Path(__file__).with_name("sheet_dq.py")), book_id, str(number)],
                         capture_output=True, text=True, errors="replace")
    tail = [l for l in run.stdout.splitlines() if l.strip()][-8:]
    for line in tail:
        print("   ", line[:150])
    m = re.search(r"(PASS|FAIL)\s+hard (\d+)", run.stdout)
    return int(m.group(2)) if m else 1


def main(book_id: str, number: int) -> int:
    book = episode_home.book_dir(book_id)
    ep = contract(book, number)
    if ep is None:
        return 1
    print("CONTRACT OK:", ep.title, "|", len(ep.shots), "shots |", f"{ep.projected_seconds():.0f}s projected")
    hard = 0
    unlit = house_style.faults(ep)
    print("G-LIGHT      :", unlit or "clean"); hard += len(unlit)
    rate = plan_gates.series_rate(book, number)
    for n in plan_gates.advisories(ep, plan_gates.series_lines(book, number), rate=rate):
        print("  advisory:", n[:150])
    pg = plan_gates.faults(ep)
    print("PLAN GATES   :", len(pg) or "clean"); hard += len(pg)
    for f in pg:
        print("   ", f[:170])
    mf = ep.still_motions()
    bad = [(i, c) for i, c, w in mf if c in spec.HARD_MOTION]
    print("MOTION hard  :", bad or "clean"); hard += len(bad)
    for i, c, w in mf:
        print(f"    {c} shot {i}: {w[:140]}")
    refs = episode_home.read_json(book / "refs" / "refs.json")["refs"]
    crossed, vague = spec.plan_marks(ep, refs)
    print("MARKS        :", crossed or "clean", "| unmeasured", len(vague)); hard += len(crossed)
    actors = actor_gate.hard_episode(ep)
    print("ACTOR        :", actors or "clean"); hard += len(actors)
    import seq_boards  # noqa: E402
    unbound = seq_boards.unbound_cast(book, ep)
    print("CAST BOUND   :", unbound or "all bound"); hard += len(unbound)
    lifted, _ = spec.quoted_lines([l.model_dump() for l in ep.lines], seq_boards.book_words(book))
    print("QUOTE        :", [(l["index"], l["lifted"]) for l in lifted] or "clean"); hard += len(lifted)
    packed = [tuple(run) for run in tk.groups(measured_or_projected(book, number, ep, rate)) if len(run) > 1]
    print("ONE PER TAKE :", packed or "every shot its own take"); hard += len(packed)
    for i, word in unpaced_shots(ep):
        print(f"  advisory: L8 shot {i}: {word!r} with no pace word (the built prompt may differ)")
    long = long_shots(ep, rate)
    print(f"TAKE LENGTH  : {long or 'every shot inside a take'} (at {rate:.2f} words/s, budget {BUDGET} s)")
    hard += len(long)
    import takes_r2v  # noqa: E402  -- the take builder's own refusals, before it is asked to build
    for refuse in (takes_r2v.refuse_long_shots, takes_r2v.refuse_still_motions):
        try:
            refuse(ep)
        except SystemExit as e:
            print("TAKE BUILDER :", str(e)[:170]); hard += 1
    print("SHEET TEXT   :")
    hard += sheet_text(book_id, number)
    print("VERDICT      :", "REFUSED" if hard else "clean -- lines may render")
    return 1 if hard else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], int(sys.argv[2])))
