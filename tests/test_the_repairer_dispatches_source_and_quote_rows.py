"""The repairer sees and routes the source/quote rows (2026-10-05): a failing
span row dispatches `source_spans`, the checker's top-level QUOTE list row is
collected (the ep16 TAKE LENGTH mechanism) and dispatches `quote_trim`, and a
'has no chapter span' row stays CREATIVE -- in particular it no longer falls
through to `legal_props` via that pattern's bare 'prop ' alternative (a no-op
cure that cost six wasted rounds).  No chapter text on disk skips both cures
so the rows come back uncured, never a silent pass."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from studio import plan_cures as pc

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "pr_sq", ROOT / "scripts" / "episode" / "plan_repair.py")
pr = importlib.util.module_from_spec(_spec)
sys.modules["pr_sq"] = pr
_spec.loader.exec_module(pr)


def test_a_failing_span_row_dispatches_source_spans():
    row = ("G-SOURCE shot 16: span 'And then followed such a concussion…' "
           "is not in the chapter, measured 0.75 against 0.85")
    assert pc.cure_for(row) == "source_spans"


def test_a_no_span_claim_row_stays_creative():
    row = "G-SOURCE shot 3: posture 'astride' has no chapter span, measured 0 against 1"
    assert pc.cure_for(row) is None


def test_a_no_span_prop_row_no_longer_falls_through_to_legal_props():
    row = "G-SOURCE shot 4: prop 'copper_pan' has no chapter span, measured 0 against 1"
    assert pc.cure_for(row) is None


def test_fault_rows_collects_the_quote_list_and_routes_it_to_quote_trim():
    out = ("CONTRACT OK: x | 26 shots | 147s projected\n"
           "QUOTE        : [(3, 14)]\n"
           "ONE PER TAKE : every shot its own take\n"
           "VERDICT      : REFUSED\n")
    rows = pr.fault_rows(out)
    assert any(r.startswith("QUOTE") for r in rows)
    assert pc.cure_for(next(r for r in rows if r.startswith("QUOTE"))) == "quote_trim"


def test_a_clean_quote_row_is_not_collected():
    rows = pr.fault_rows("QUOTE        : clean\nVERDICT      : clean -- lines may render\n")
    assert not any("QUOTE" in r for r in rows)


def test_apply_without_chapter_text_leaves_source_rows_uncured(monkeypatch, tmp_path):
    from studio import plan_brief
    monkeypatch.setattr(plan_brief, "chapter_text", lambda book, number: None)
    row = "G-SOURCE shot 4: span 'six riders stood about' is not in the chapter, measured 0.7 against 0.85"
    doc, uncured = pr.apply({"shots": [], "lines": []}, [row], tmp_path, number=7)
    assert row in uncured
