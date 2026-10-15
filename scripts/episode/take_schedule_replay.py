#!/usr/bin/env python
"""Replay an episode's step-09 clock under the two lanes (studio/take_schedule).

    uv run python scripts/episode/take_schedule_replay.py <codex_id> <n> [--vl-load=60]

Reads the episode's OWN seconds -- timing.jsonl (stage rows), takes/r2v/
phases.jsonl (each render) and takes/r2v/ladder.json (each round's faults) --
for round 0 and each retake round after it (a resume's re-render is no round),
and prints three wall clocks for the same renders and the same checks:

    serial        today's order: render all, check all, read, judge, per round
    overlap_only  today's rounds, each check run beside its round's renders
    overlapped    the decision: firsts and early retakes streamed with their
                  checks, one VL batch, the late cures and round 2 in one job

`--vl-load` is the VL model's load per content batch (not in any row; it is
counted the same in every arm).  Decision 2026-10-14-gpu-never-waits-for-checks.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_clock, episode_home, take_ladder, take_schedule as ts  # noqa: E402
from studio.judges.verdict import Fault  # noqa: E402

STEP09 = {"takes", "take_dq", "take_content", "strip", "take_eye"}
EYE_BORNE = frozenset({"content", "clones", "unread", "twin", "identity"})
"""Faults the VL read or the eye finds: never known to the CPU lane."""
VL_LOAD_S = 60.0


def round_zero(rows: list[dict]) -> int:
    """The first render row that is no retake and no empty resume."""
    return next(k for k, r in enumerate(rows) if r["stage"] == "takes"
                and "--retake" not in r.get("note", "") and float(r["seconds"]) > 60)


def opens_round(r: dict, first: bool) -> bool:
    return r["stage"] == "takes" and (first or "--retake" in r.get("note", ""))


def step09_cycles(rows: list[dict], most: int = 3) -> list[list[dict]]:
    """Round 0 and each retake round after it, each with the checks that
    followed its renders; a resume's re-render and its checks, and every
    other stage, are no round."""
    out: list[list[dict]] = []
    live = False
    for r in rows[round_zero(rows):]:
        if opens_round(r, not out):
            out.append([r])
            live = True
        elif live and r["stage"] in STEP09 - {"takes"}:
            out[-1].append(r)
        else:
            live = False
    return out[:most]


def retakes_of(cycle: list[dict]) -> list[int]:
    return episode_clock.indices_in(cycle[0].get("note", ""))


def renders(phases: list[dict], retakes: list[list[int]]) -> tuple[tuple, list[tuple]]:
    """(round 0 as (take, s) in render order, each later round's (take, s))."""
    seen: set[int] = set()
    first = []
    for p in phases:
        if p["take"] in seen:
            break
        seen.add(p["take"])
        first.append((p["take"], float(p["prompt_s"])))
    rest, used = phases[len(first):], set()
    later = []
    for named in retakes:
        picks = [next(k for k, p in enumerate(rest) if p["take"] == i and k not in used) for i in named]
        used |= set(picks)
        later.append(tuple((rest[k]["take"], float(rest[k]["prompt_s"])) for k in picks))
    return tuple(first), later


def early_of(faults: dict[str, list[str]]) -> frozenset[int]:
    """Takes whose dq rows ALONE route to a render cure (a move or a seed)."""
    out = set()
    for take, kinds in faults.items():
        dq = [Fault(kind=k, where=f"T{int(take):02d}") for k in kinds if k not in EYE_BORNE]
        if dq and take_ladder.cure_of(dq) in ("move_type", "seed"):
            out.add(int(take))
    return frozenset(out)


def seconds(cycle: list[dict], stage: str) -> float:
    return sum(float(r["seconds"]) for r in cycle if r["stage"] == stage)


def costs_of(cyc: list[list[dict]], first: tuple, later: list[tuple], vl_load_s: float) -> ts.Costs:
    """Per-take seconds from round 0 (and round 1 for a retake's attempts)."""
    n0, eyes = len(first), [r for c in cyc for r in c if r["stage"] == "take_eye"]
    retake_dq = (seconds(cyc[1], "take_dq") / len(later[0])) if later and later[0] else seconds(cyc[0], "take_dq") / n0
    return ts.Costs(dq_s=seconds(cyc[0], "take_dq") / n0, dq_retake_s=retake_dq,
                    content_s=max(0.0, seconds(cyc[0], "take_content") - vl_load_s) / n0,
                    vl_load_s=vl_load_s, eye_s=sum(float(r["seconds"]) for r in eyes) / max(1, len(eyes)),
                    strip_s=seconds(cyc[0], "strip"),
                    launch_s=max(0.0, seconds(cyc[0], "takes") - ts.rendered_s(first)))


def model(cyc: list[list[dict]], phases: list[dict], ladder: list[dict],
          vl_load_s: float = VL_LOAD_S) -> tuple[ts.Rounds, ts.Costs]:
    first, later = renders(phases, [retakes_of(c) for c in cyc[1:3]])
    early = early_of((ladder[0] if ladder else {}).get("faults") or {}) if later else frozenset()
    rounds = ts.Rounds(first=first, round1=later[0] if later else (), round2=later[1] if len(later) > 1 else (),
                       early=early)
    return rounds, costs_of(cyc, first, later, vl_load_s)


def project(rows: list[dict], phases: list[dict], ladder: list[dict], vl_load_s: float = VL_LOAD_S) -> dict:
    cyc = step09_cycles(rows)
    rounds, costs = model(cyc, phases, ladder, vl_load_s)
    return {"measured_s": sum(float(r["seconds"]) for c in cyc for r in c), "serial_s": ts.serial(rounds, costs).wall_s,
            "overlap_only_s": ts.overlap_only(rounds, costs).wall_s,
            "overlapped_s": ts.overlapped(rounds, costs).wall_s,
            "gpu_idle_serial_s": ts.serial(rounds, costs).idle_s,
            "gpu_idle_overlapped_s": ts.overlapped(rounds, costs).idle_s,
            "early": sorted(rounds.early), "costs": costs.__dict__}


def lines_of(path: Path) -> list[dict]:
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def main(book_id: str, number: int, vl_load_s: float) -> dict:
    home = episode_home.home(episode_home.book_dir(book_id), number)
    room = home / "takes" / "r2v"
    ladder = json.loads((room / "ladder.json").read_text(encoding="utf-8")).get("rounds", []) \
        if (room / "ladder.json").exists() else []
    got = project(lines_of(home / "timing.jsonl"), lines_of(room / "phases.jsonl"), ladder, vl_load_s)
    saved = got["serial_s"] - got["overlapped_s"]
    print(json.dumps(got, indent=1))
    print(f"serial {got['serial_s']:.0f} s -> overlapped {got['overlapped_s']:.0f} s: "
          f"{saved:.0f} s saved ({saved / got['serial_s']:.0%}); measured window {got['measured_s']:.0f} s")
    return got


if __name__ == "__main__":
    vl = next((float(a.split("=", 1)[1]) for a in sys.argv if a.startswith("--vl-load=")), VL_LOAD_S)
    main(sys.argv[1], int(sys.argv[2]), vl)
