#!/usr/bin/env python
"""The automated plan repairer: plan_check -> the cure table -> clean, in
seconds, with no writer call.

    uv run python scripts/episode/plan_repair.py <codex_id> <episode> [--from-aside]

MEASURED (docs/audit/2026-10-01_plan_hours_debate.md): 97% of ep14-15's plan
hours were paid rewrites of MECHANICAL faults.  This loop applies the cure
table (studio/plan_cures) to every fault plan_check names, up to ROUNDS
times, writing through the contract each round.  It exits 0 on a clean
battery; on faults with no cure (the CREATIVE kind -- story, coverage,
invented) it exits 1 listing exactly what the writer must answer, one field
at a time."""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home, plan_cures as pc  # noqa: E402
from studio.episode_home import episode_arg  # noqa: E402
from studio.episode_spec import Episode  # noqa: E402

ROUNDS = 6


def battery_rows(book_id: str, number: int) -> tuple[bool, list[str]]:
    rc = subprocess.run([sys.executable, "scripts/episode/plan_check.py", book_id, str(number)],
                        capture_output=True, text=True, cwd=str(Path(__file__).resolve().parents[2]))
    clean = "VERDICT      : clean" in rc.stdout
    rows = [l.strip() for l in rc.stdout.splitlines()
            if (l.startswith("    ") or "CONTRACT :" in l or "ONE PER TAKE : [" in l)
            and "advisory" not in l and "not applicable" not in l and l.strip()]
    return clean, rows


def series_pin_values(book) -> dict:
    """The series' look/aspect off the newest SIGNED episode, else the house."""
    from studio import plan_gates
    for n in range(27, 0, -1):
        p = episode_home.home(book, n) / "plan.json"
        v = episode_home.home(book, n) / "plan.verdict.json"
        if p.exists() and v.exists():
            doc = episode_home.read_json(p)
            if doc.get("look"):
                return {"look": doc["look"], "aspect": plan_gates.series_aspect(book)}
    return {"look": "", "aspect": plan_gates.series_aspect(book)}


def shot_indices(rows: list[str]) -> list[int]:
    import re
    return sorted({int(m.group(1)) for r in rows for m in [re.search(r"shot (\d+)", r)] if m})


def apply(doc: dict, rows: list[str], book) -> tuple[dict, list[str]]:
    """Every cured family once per round; the rows nothing cures come back."""
    legal = {p[:-5] for p in os.listdir(book / "analysis" / "props")} \
        if (book / "analysis" / "props").exists() else set()
    uncured, names = [], set()
    for row in rows:
        name = pc.cure_for(row)
        (names.add(name) if name else uncured.append(row))
    for name in names:
        if name == "renumber":
            doc = pc.renumber(doc)
        elif name == "light_directions":
            doc = pc.light_directions(doc)
        elif name == "head_fractions":
            doc = pc.head_fractions(doc)
        elif name == "pace_words":
            doc = pc.pace_words(doc)
        elif name == "button_beat":
            doc = pc.button_beat(doc)
        elif name == "vary_heads":
            doc = pc.vary_heads(doc, shot_indices([r for r in rows if pc.cure_for(r) == "vary_heads"]))
        elif name == "legal_props":
            doc = pc.legal_props(doc, legal)
        elif name == "holds":
            doc = pc.holds(doc)
        elif name == "edge_cases":
            doc = pc.edge_cases(doc)
        elif name == "pin_series":
            doc = pc.pin_series(doc, **series_pin_values(book))
    return doc, uncured


def main(book_id: str, number: int, from_aside: bool = False) -> int:
    book = episode_home.book_dir(book_id)
    home = episode_home.home(book, number)
    path = home / "plan.json"
    if from_aside or not path.exists():
        aside = home / "plan.deferred.json"
        if not aside.exists():
            raise SystemExit(f"no plan and no aside under {home}")
        doc = json.load(io.open(aside, encoding="utf-8"))["draft"]
        Episode(**doc)
        episode_home.write_plan(path, doc)
        print("aside draft restored to plan.json")
    for round_ in range(1, ROUNDS + 1):
        clean, rows = battery_rows(book_id, number)
        if clean:
            print(f"BATTERY CLEAN after {round_ - 1} repair round(s)")
            return 0
        doc = episode_home.read_json(path)
        doc, uncured = apply(doc, rows, book)
        try:
            Episode(**doc)
            episode_home.write_plan(path, doc)
        except Exception as bad:
            print(f"round {round_}: a cure broke the contract, draft kept: {str(bad)[:140]}")
            return 1
        print(f"round {round_}: {len(rows) - len(uncured)} fault row(s) cured, "
              f"{len(uncured)} creative row(s) remain")
        if uncured and len(uncured) == len(rows):
            break
    clean, rows = battery_rows(book_id, number)
    if clean:
        print("BATTERY CLEAN")
        return 0
    print("CREATIVE faults remain -- the writer's, one field at a time:")
    for r in rows:
        print("  ", r[:160])
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], episode_arg(sys.argv), "--from-aside" in sys.argv))
