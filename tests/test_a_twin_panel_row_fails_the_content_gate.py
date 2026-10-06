"""A panel whose twin ask reads two figures as one person fails the content
gate, and an unreadable twin ask on these sizes fails it too -- never a
silent pass.

G-TWIN-PANEL wiring: `row_for` runs the dedicated ask only when
`twin_applies` says so, records the counts on the row for the audit sheet,
and both reads are monkeypatched to canned answers (the FakeModel pattern) so
no comfy, no GPU, no spend.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from studio import episode_home, panel_content as pc

from scripts.episode import panel_content_check as pcc

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "tests" / "fixtures" / "episodes" / "ep05_plan.json"


def book_of(tmp_path: Path):
    """A book with the ep05 plan and a refs row for its one hearth face."""
    book = tmp_path / "book"
    home = book / "episodes" / "ep05"
    home.mkdir(parents=True)
    shutil.copy(PLAN, home / "plan.json")
    (book / "refs").mkdir()
    (book / "refs" / "refs.json").write_text(json.dumps({"chapter": 5, "refs": [
        {"entity_id": "john_watson", "kind": "character",
         "physical": "Man of 32 with a thin waxed moustache and a sunburnt face."}]}),
        encoding="utf-8")
    ep = episode_home.load_plan(book, 5)
    shot = ep.shot(9)                      # hearth_night, medium, one named face
    return book, shot, ep.setups[shot.setup]


def test_a_two_figure_one_distinct_medium_panel_fails_with_the_twin_fault(tmp_path, monkeypatch):
    book, shot, setup = book_of(tmp_path)
    monkeypatch.setattr(pcc, "read", lambda path, seed=11: pc.Seen(people=2))
    monkeypatch.setattr(pcc, "read_twins",
                        lambda path, seed=17: pc.Twins(2, 1, ["man in a grey waistcoat x2"]))
    row = pcc.row_for(book, shot, setup, Path("shot_09.png"))
    assert not row["passed"]
    assert any(f.startswith("twin:") and "man in a grey waistcoat x2" in f for f in row["faults"])
    assert (row["figures"], row["distinct"]) == (2, 1)
    assert row["twins"] == ["man in a grey waistcoat x2"]


def test_an_unreadable_twin_ask_is_a_fault_never_a_silent_pass(tmp_path, monkeypatch):
    book, shot, setup = book_of(tmp_path)

    def unreadable(path, seed=17):
        raise pc.Unreadable("the twin read has no distinct")

    monkeypatch.setattr(pcc, "read", lambda path, seed=11: pc.Seen(people=2))
    monkeypatch.setattr(pcc, "read_twins", unreadable)
    row = pcc.row_for(book, shot, setup, Path("shot_09.png"))
    assert not row["passed"]
    assert any(f.startswith("unread: twin") for f in row["faults"])


def test_a_one_figure_panel_never_asks(tmp_path, monkeypatch):
    book, shot, setup = book_of(tmp_path)
    asked = []

    def recorder(path, seed=17):
        asked.append(path)
        return pc.Twins(1, 1, [])

    monkeypatch.setattr(pcc, "read", lambda path, seed=11: pc.Seen(people=1))
    monkeypatch.setattr(pcc, "read_twins", recorder)
    row = pcc.row_for(book, shot, setup, Path("shot_09.png"))
    assert asked == [] and row["passed"]


def test_two_distinct_figures_add_no_twin_fault(tmp_path, monkeypatch):
    """The extra figure still fails the people gate; the twin gate stays quiet."""
    book, shot, setup = book_of(tmp_path)
    monkeypatch.setattr(pcc, "read", lambda path, seed=11: pc.Seen(people=2))
    monkeypatch.setattr(pcc, "read_twins", lambda path, seed=17: pc.Twins(2, 2, []))
    row = pcc.row_for(book, shot, setup, Path("shot_09.png"))
    assert not any(f.startswith("twin:") for f in row["faults"])
