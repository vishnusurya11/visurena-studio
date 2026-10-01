"""ep16 (2026-10-01): the holds cure unpacked pair (16,17) and pushed shot 16
to 8.05 s -- 0.05 past the take budget -- and could not see it, because its
seconds model lacked the checker's handles (2 x 0.25 s) and breaths (0.70 s
between lines).  Three repair rounds deferred over a number the cure could not
measure.  The cure now measures LIKE the checker (plan_check.projected), and
holds ends by clamping any single shot past the budget.  The repairer also
collects the checker's top-level list rows (TAKE LENGTH was invisible to it)
and stops looping when it collects nothing.  $0: arithmetic."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from studio import plan_cures as pc

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pr", ROOT / "scripts" / "episode" / "plan_repair.py")
pr = importlib.util.module_from_spec(spec)
sys.modules["pr"] = pr
spec.loader.exec_module(pr)

RATE = 2.54


def doc_with(shots, lines):
    return {"shots": shots, "lines": lines}


def test_the_cure_counts_handles_and_breaths_like_the_checker():
    doc = doc_with([{"index": 0, "setup": "a", "beat_s": 0.2, "coda_s": 0.3}],
                   [{"shot": 0, "text": "five words sit right here"},
                    {"shot": 0, "text": "and five more words follow"}])
    got = pc._shot_secs(doc, RATE)[0]
    want = 2 * 0.25 + 10 / RATE + 0.70 * 1 + 0.2 + 0.3
    assert abs(got - want) < 1e-6


def test_holds_clamps_a_shot_past_the_take_budget():
    # shot 0 projects past 8.0 on its codas; its setup partner keeps the pair split
    long = {"index": 0, "setup": "a", "beat_s": 1.36, "coda_s": 2.5}
    partner = {"index": 1, "setup": "a", "beat_s": 0.6, "coda_s": 0.3}
    doc = doc_with([long, partner],
                   [{"shot": 0, "text": " ".join(["w"] * 10)}])    # ~8.30 s with holds
    before = pc._shot_secs(doc, RATE)[0]
    assert before > 8.0                                            # the ep16 state
    cured = pc.holds(doc, rate=RATE)
    secs = pc._shot_secs(cured, RATE)
    assert secs[0] <= 8.0                                          # clamped
    assert secs[0] + secs[1] > 8.0                                 # the pair stays unpacked


def test_take_length_routes_to_holds():
    assert pc.cure_for("TAKE LENGTH  : [(16, 8.05)] (at 2.54 words/s, budget 8.0 s)") == "holds"


def test_fault_rows_sees_the_checkers_top_level_lists():
    out = ("CONTRACT OK: x | 26 shots | 147s projected\n"
           "TAKE LENGTH  : [(16, 8.05)] (at 2.54 words/s, budget 8.0 s)\n"
           "ONE PER TAKE : [(9, 10)]\n"
           "EXPECTS TEXT : [7]\n"
           "    G-LIGHT: setup 'x' names no light source\n"
           "VERDICT      : REFUSED\n")
    rows = pr.fault_rows(out)
    assert any(r.startswith("TAKE LENGTH") for r in rows)
    assert any(r.startswith("ONE PER TAKE") for r in rows)
    assert any("G-LIGHT" in r for r in rows)
    assert not any("EXPECTS TEXT" in r for r in rows)   # informational, never a repair target
