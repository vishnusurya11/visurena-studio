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


HARD_LISTS = ("ONE PER TAKE : [", "TAKE LENGTH  : [", "CONTRACT :", "QUOTE        : [")
"""The checker's top-level rows that are HARD and list-formed; EXPECTS TEXT
and SHEET TEXT print the same way and are informational (ep16: TAKE LENGTH
was invisible to the repairer and three rounds deferred over 0.05 s)."""


def fault_rows(stdout: str) -> list[str]:
    return [l.strip() for l in stdout.splitlines()
            if (l.startswith("    ") or any(k in l for k in HARD_LISTS))
            and "advisory" not in l and "not applicable" not in l and l.strip()]


def battery_rows(book_id: str, number: int) -> tuple[bool, list[str]]:
    rc = subprocess.run([sys.executable, "scripts/episode/plan_check.py", book_id, str(number)],
                        capture_output=True, text=True, cwd=str(Path(__file__).resolve().parents[2]))
    return "VERDICT      : clean" in rc.stdout, fault_rows(rc.stdout)


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


def phantom_context(book) -> tuple[dict, set]:
    """(names, place_words) the phantom cures measure with -- the GATE'S own
    inputs, from the book's refs.json when it exists."""
    from studio import house_style, plan_gates
    path = book / "refs" / "refs.json"
    refs = episode_home.read_json(path).get("refs") or [] if path.exists() else []
    return plan_gates.person_tokens(refs), house_style.place_words()


def rewrite_round(book, path, rows: list[str]) -> bool:
    """The ONE paid round per repair run: setups whose G-PHANTOM / G-LIGHT rows
    survived the mechanical table are rewritten through the workhorse tier
    (guard_spend fires inside the caller), written through the contract."""
    import re
    bad = [r for r in rows if re.search(r"G-PHANTOM|G-LIGHT: setup", r)]
    setups = sorted({m.group(1) for r in bad if (m := re.search(r"setup '([^']+)'", r))})
    if not setups:
        return False
    doc = episode_home.read_json(path)
    doc, uncured = pc.rewrite_setups(doc, *phantom_context(book), setups)
    Episode(**doc)
    episode_home.write_plan(path, doc)
    print(f"llm round: {len(setups) - len(uncured)} setup(s) rewritten, "
          f"{len(uncured)} kept their faults for the writer")
    return True


def shot_indices(rows: list[str]) -> list[int]:
    import re
    return sorted({int(m.group(1)) for r in rows for m in [re.search(r"shot (\d+)", r)] if m})


def apply(doc: dict, rows: list[str], book, number: int = 0,
          rate: float = 3.0) -> tuple[dict, list[str]]:
    """Every cured family once per round; the rows nothing cures come back.
    `rate` is the narrator's measured words/s -- THE CHECKER'S RATE, or the
    holds algebra cures numbers the battery never measures (ep16: 8.05 s at
    2.54 read as 7.5 s at the default 3.0 and the clamp saw nothing)."""
    legal = {p[:-5] for p in os.listdir(book / "analysis" / "props")} \
        if (book / "analysis" / "props").exists() else set()
    uncured, names = [], set()
    for row in rows:
        name = pc.cure_for(row)
        (names.add(name) if name else uncured.append(row))
    chapter = None
    if names & {"source_spans", "quote_trim"}:
        from studio import plan_brief
        chapter = plan_brief.chapter_text(book, number)
        if chapter is None:     # never a silent pass: the rows come back uncured
            uncured += [r for r in rows if pc.cure_for(r) in ("source_spans", "quote_trim")]
            names -= {"source_spans", "quote_trim"}
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
        elif name == "close_crowds":
            doc = pc.close_crowds(doc)
        elif name == "strip_phantoms":
            doc, _ = pc.strip_phantoms(doc, *phantom_context(book))
        elif name == "holds":
            doc = pc.holds(doc, rate=rate)
        elif name == "edge_cases":
            doc = pc.edge_cases(doc)
        elif name == "source_spans":
            doc = pc.source_spans(doc, chapter)
        elif name == "quote_trim":
            import seq_boards  # sibling module, lazy so the importlib-loaded test never needs it
            doc = pc.quote_trim(doc, seq_boards.book_words(book))
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
        from studio import plan_gates
        doc, uncured = apply(doc, rows, book, number, rate=plan_gates.series_rate(book, number))
        try:
            Episode(**doc)
            episode_home.write_plan(path, doc)
        except Exception as bad:
            print(f"round {round_}: a cure broke the contract, draft kept: {str(bad)[:140]}")
            return 1
        print(f"round {round_}: {len(rows) - len(uncured)} fault row(s) cured, "
              f"{len(uncured)} creative row(s) remain")
        if (uncured and len(uncured) == len(rows)) or not rows:
            break   # nothing this table cures, or nothing collected: stop looping
    clean, rows = battery_rows(book_id, number)
    if not clean and rewrite_round(book, path, rows):
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
