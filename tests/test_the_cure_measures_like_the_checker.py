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
           "G-LIGHT      : 1\n"
           "    G-LIGHT: setup 'x': `described` names no light source with a direction"
           " -- say where it comes from\n"
           "TAKE LENGTH  : [(16, 8.05)] (at 2.54 words/s, budget 8.0 s)\n"
           "ONE PER TAKE : [(9, 10)]\n"
           "EXPECTS TEXT : [7]\n"
           "VERDICT      : REFUSED\n")
    rows = pr.fault_rows(out)
    assert any(r.startswith("TAKE LENGTH") for r in rows)
    assert any(r.startswith("ONE PER TAKE") for r in rows)
    assert any("G-LIGHT" in r for r in rows)
    assert not any("EXPECTS TEXT" in r for r in rows)   # informational, never a repair target


def test_apply_routes_the_checkers_rate_into_holds(monkeypatch):
    seen = {}
    monkeypatch.setattr(pc, "holds", lambda doc, rate=3.0: seen.setdefault("rate", rate) or doc)
    pr.apply({"shots": [], "lines": []}, ["ONE PER TAKE : [(1, 2)]"], Path("."), rate=2.54)
    assert seen["rate"] == 2.54


def test_holds_patches_the_hole_after_a_lines_last_word():
    """ep16: the 6.14 s hole at shot 23 was the VOICED shot's own 2.5 s coda
    plus its silent successor -- a hole starts where speech ENDS, so the cap
    covers the voiced shot's coda plus every unvoiced shot that follows it,
    at HOLE_WALL_S - 0.5, shaved from the largest holds first."""
    a = {"index": 0, "setup": "a", "beat_s": 1.5, "coda_s": 2.5}   # voiced, long coda
    b = {"index": 1, "setup": "a", "beat_s": 1.0, "coda_s": 2.1}   # silent
    c = {"index": 2, "setup": "a", "beat_s": 0.1, "coda_s": 0.1}   # voiced again
    doc = doc_with([a, b, c], [{"shot": 0, "text": "two words"},
                               {"shot": 2, "text": "one line here"}])
    hole = 2.5 + pc._shot_secs(doc, RATE)[1]
    assert hole > pc.HOLE_WALL_S                                   # the ep16 state
    cured = pc.holds(doc, rate=RATE)
    secs = pc._shot_secs(cured, RATE)
    coda0 = float({s["index"]: s for s in cured["shots"]}[0]["coda_s"])
    assert coda0 + secs[1] <= pc.HOLE_WALL_S - 0.4                 # patched with margin
    silent_only = doc_with([dict(a), dict(b), dict(c)], [{"shot": 2, "text": "one line here"}])
    cured2 = pc.holds(silent_only, rate=RATE)
    secs2 = pc._shot_secs(cured2, RATE)
    assert secs2[0] + secs2[1] <= pc.HOLE_WALL_S - 0.4             # a fully silent run too
