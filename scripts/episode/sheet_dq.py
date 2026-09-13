#!/usr/bin/env python
"""The DQ that runs BEFORE the images are generated (owner, 2026-09-11).

    uv run python scripts/episode/sheet_dq.py <codex_id> <episode> [--setup=corridor]

Builds every sheet prompt of every setup exactly as `seq_boards.py` will build
it, runs `studio.sheet_gate` over the TEXT, prints one verdict line per setup
and writes `frames/sheet_dq.json`.

It draws nothing.  A run costs $0, touches no GPU and calls no API, which is
the whole argument for it: a sheet that carries a hard finding cannot come
back right, and refusing it here saves the $0.13-$0.20 draw, the strict redraw
after it, and the GPU-hours spent animating whatever came back.

`seq_boards.draw_setup` should refuse to spend on a setup whose report here
says `passed: false`; a watch prints and spends.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import episode_home, sheet_gate, episode_seq_board as sq, sheet_gate as gate


def seq_boards():
    """The runner, for its `physicals()`: one reading of refs.json, not two."""
    spec = importlib.util.spec_from_file_location("ep_seq_boards", ROOT / "scripts/episode/seq_boards.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sheet_report(k: int, group: list[dict], route: list[int], grid: tuple, setup, physical: dict,
                 aspect: str = "9:16") -> dict:
    """One sheet: its prompt built, its text gated, its findings named."""
    prompt = sq.prompt(group, setup, physical, previous=False, first=(k == 0), geography=route,
                       aspect=aspect)
    found = gate.sheet_findings(group, setup, prompt, grid)
    return {"sheet": k, "grid": f"{grid[0]}x{grid[1]}", "canvas": list(grid[2]),
            "panels": [gate.panel_key(s) for s in group], "prompt_chars": len(prompt),
            "verdict": gate.verdict(found), "findings": [f.as_dict() for f in found]}


def setup_report(episode, name: str, physical: dict) -> dict:
    """Every sheet of one setup, and whether a draw may be paid for."""
    setup, aspect = episode.setups[name], getattr(episode, "aspect", "9:16")
    groups = sq.sheets(sq.segments(episode.shots, name), setup, aspect)
    sheets = [sheet_report(k, group, route, grid, setup, physical, aspect)
              for k, (group, route, grid) in enumerate(groups)]
    found = [f for s in sheets for f in s["findings"]]
    return {"setup": name, "passed": all(s["verdict"]["passed"] for s in sheets), "sheets": sheets,
            "hard": sum(1 for f in found if f["hard"]), "watch": sum(1 for f in found if not f["hard"]),
            "findings": found}


def report(episode, physical: dict, only: str | None = None) -> dict:
    """The whole episode: one verdict per setup and one for the plan."""
    setups = [setup_report(episode, name, physical) for name in episode.setups if not only or name == only]
    return {"episode": episode.number, "passed": all(s["passed"] for s in setups),
            "hard": sum(s["hard"] for s in setups), "watch": sum(s["watch"] for s in setups),
            "setups": setups}


def counts(found: list[dict]) -> str:
    """`CAMERA 1, CROWD 3` -- which checks fired, most first."""
    tally: dict[str, int] = {}
    for f in found:
        tally[f["check"]] = tally.get(f["check"], 0) + 1
    return ", ".join(f"{k} {v}" for k, v in sorted(tally.items(), key=lambda kv: (-kv[1], kv[0])))


def rows(whole: dict) -> list[str]:
    """One line per setup, the shape the owner reads on the run card."""
    return [f"{s['setup']:<10} {len(s['sheets'])} sheet(s) {len(s['sheets'][0]['panels']) if s['sheets'] else 0:>2} "
            f"panels  {'PASS' if s['passed'] else 'FAIL'}  hard {s['hard']:>2} watch {s['watch']:>2}  "
            f"{counts(s['findings'])}".rstrip() for s in whole["setups"]]


def main(book_id: str, number: int, only: str | None = None) -> dict:
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    physicals = seq_boards().physicals(book)
    whole = report(episode, physicals, only)
    whole["contract"] = sheet_gate.contract_faults(physicals)  # a contract cut short is invisible harm
    for line in rows(whole):
        print(line)
    for f in whole["contract"]:
        print(f"  CONTRACT {f['panel']:<14} {f['detail'][:90]}")
    for finding in [f for s in whole["setups"] for f in s["findings"] if f["hard"]]:
        print(f"  FAIL {finding['check']:<14} {finding['panel']:<8} {finding['text'][:80]}")
    out = episode_home.write_json(episode_home.frames_dir(book, number) / "sheet_dq.json", whole)
    print(f"{'PASS' if whole['passed'] else 'FAIL'}  hard {whole['hard']} watch {whole['watch']} -> {out}")
    return whole


if __name__ == "__main__":
    setup = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--setup=")), None)
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 1, setup)
