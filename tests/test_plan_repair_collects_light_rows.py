"""The G-LIGHT row-emission fix (ep18, 2026-10-05): plan_check printed the
G-LIGHT fault list as a ONE-LINE repr, which `plan_repair.fault_rows` -- a
collector of 4-space-indented rows -- never saw, so the already-written
`light_directions` cure never dispatched and the writer deferred.  The checker
now prints indented rows like every other gate; this file documents both sides
of the bug it kills.  No API."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from studio import plan_cures as pc

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("pr_light", ROOT / "scripts" / "episode" / "plan_repair.py")
pr = importlib.util.module_from_spec(_spec)
sys.modules["pr_light"] = pr
_spec.loader.exec_module(pr)

NEW = ("CONTRACT OK: x | 26 shots | 147s projected\n"
       "G-LIGHT      : 1\n"
       "    G-LIGHT: setup 'street': `described` names no light source with a direction"
       " -- say where it comes from\n"
       "VERDICT      : REFUSED\n")

OLD = ("CONTRACT OK: x | 26 shots | 147s projected\n"
       "G-LIGHT      : [\"G-LIGHT: setup 'street': `described` names no light source\"]\n"
       "VERDICT      : REFUSED\n")


def test_the_new_indented_rows_are_collected_and_route_to_the_cure():
    rows = [r for r in pr.fault_rows(NEW) if "G-LIGHT" in r]
    assert rows and pc.cure_for(rows[0]) == "light_directions"


def test_the_old_one_line_repr_was_never_collected():
    assert pr.fault_rows(OLD) == []     # the measured root cause of the ep18 deferral


def test_phantom_context_builds_names_from_the_books_refs(tmp_path):
    (tmp_path / "refs").mkdir()
    (tmp_path / "refs" / "refs.json").write_text(
        '{"refs": [{"kind": "character", "entity_id": "curate", "display": "the curate"}]}',
        encoding="utf-8")
    names, place_words = pr.phantom_context(tmp_path)
    assert names == {"curate": "curate"} and isinstance(place_words, set)
    assert pr.phantom_context(tmp_path / "nowhere")[0] == {}


def test_rewrite_round_rewrites_only_the_matching_setups(monkeypatch, tmp_path):
    seen = {}
    monkeypatch.setattr(pr.episode_home, "read_json", lambda p: {"setups": {}})
    monkeypatch.setattr(pr.pc, "rewrite_setups",
                        lambda doc, names, pw, setups, caller=None:
                        (seen.setdefault("setups", setups), []) and (doc, []))
    monkeypatch.setattr(pr, "Episode", lambda **doc: None)
    monkeypatch.setattr(pr.episode_home, "write_plan",
                        lambda p, d: seen.setdefault("wrote", True))
    monkeypatch.setattr(pr, "phantom_context", lambda book: ({}, set()))
    rows = ["G-PHANTOM setup 'aperture' (described): sentence 'x' names 'curate', measured 1 against 0",
            "G-LIGHT: setup 'street': `described` names no light source with a direction",
            "G-MOVES plan: distinct catalog moves over 20 shots, measured 3 against 8"]
    assert pr.rewrite_round(tmp_path, tmp_path / "plan.json", rows) is True
    assert seen["setups"] == ["aperture", "street"] and seen["wrote"]


def test_rewrite_round_without_matching_rows_pays_nothing():
    assert pr.rewrite_round(Path("."), Path("plan.json"), ["G-MOVES plan: x"]) is False
