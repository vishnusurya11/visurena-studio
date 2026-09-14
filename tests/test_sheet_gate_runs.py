"""The free gate runs before the paid draw, and a bad grid is not a clean sheet.

TWO HOLES IN THE DRAW PATH, both found 2026-09-13:

  G1 `sheet_gate` HAS NEVER RUN ON AN EPISODE.  430 lines, nine checks, four of
     them HARD -- imported by `scripts/episode/sheet_dq.py` and by its own test,
     and by nothing on the path that spends the money.  Proof: `sheet_dq.json`
     exists for ep01 and ep02 and does NOT exist for ep03, the episode that
     shipped.  `sheet_dq.py`'s own docstring states the wiring as an aspiration:
     "`seq_boards.draw_setup` should refuse to spend on a setup whose report here
     says `passed: false`".  It did not.

  G2 `clean()` IGNORED `gutters_ok`.  It is computed on every attempt and only
     ever reached `report["passed"]`, which nothing reads -- `takes_r2v` takes
     cells off disk.  MEASURED: `seq_corner_wall_0.png` returned FOUR column
     bands instead of two, so `cell_boxes` fell back to cutting the sheet in
     thirds; those cells are 663 px against the true 675-693 and every one
     needed a bottom trim, i.e. gutter leaking into the panel.  A sheet that is
     otherwise clean with `gutters_ok: false` was accepted, with misaligned
     cells, and no retry.
"""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def boards():
    spec = importlib.util.spec_from_file_location("sb", ROOT / "scripts/episode/seq_boards.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def entry(**kw):
    base = {"duplicates": [], "regressions": [], "white_lines_in": [], "gutters_ok": True}
    return base | kw


# ---- G2  a misaligned cut is not clean -------------------------------------

def test_a_sheet_whose_gutters_were_not_found_is_not_clean(boards):
    """corner_wall: four column bands, cells cut in thirds, every one trimmed."""
    assert not boards.clean(entry(gutters_ok=False))


def test_a_sheet_with_found_gutters_and_no_faults_is_clean(boards):
    assert boards.clean(entry())


def test_the_other_three_faults_still_refuse(boards):
    assert not boards.clean(entry(duplicates=[("Q00_0", "Q00_0E")]))
    assert not boards.clean(entry(regressions=[2]))
    assert not boards.clean(entry(white_lines_in=["Q00_0.png"]))


# ---- G1  the gate is on the draw path --------------------------------------

def test_the_draw_path_imports_the_gate(boards):
    """A gate reachable only from a separate manual command is a gate that does
    not run: ep03 has no sheet_dq.json at all."""
    assert hasattr(boards, "sheet_gate")


def test_a_hard_text_finding_refuses_before_the_draw(boards, monkeypatch):
    """The last free moment: `draw_sheet` must raise before `sb.draw` spends."""
    from studio.sheet_gate import Finding

    monkeypatch.setattr(boards.sheet_gate, "sheet_findings",
                        lambda *a, **k: [Finding("affirmative", "1", "asks for an absence", hard=True)])
    drew = []

    class Board:
        def draw(self, *a, **k):
            drew.append(a)
            raise AssertionError("the draw must not be reached")

    with pytest.raises(SystemExit, match="affirmative"):
        boards.refuse_on_text([{"shot": 0, "sub": 0}], object(), "a prompt", (3, 3, (2048, 2048)), "hall")
    assert drew == []


def test_a_watch_finding_prints_and_does_not_refuse(boards, monkeypatch, capsys):
    """Only HARD findings stop a run; the advisory half is the reason the gate
    was worth writing and must not become a blocker."""
    from studio.sheet_gate import Finding

    monkeypatch.setattr(boards.sheet_gate, "sheet_findings",
                        lambda *a, **k: [Finding("crowd", "2", "no background life named", hard=False)])
    boards.refuse_on_text([{"shot": 0, "sub": 0}], object(), "a prompt", (3, 3, (2048, 2048)), "hall")
    assert "crowd" in capsys.readouterr().out


def test_a_clean_sheet_says_nothing_and_proceeds(boards, monkeypatch, capsys):
    monkeypatch.setattr(boards.sheet_gate, "sheet_findings", lambda *a, **k: [])
    boards.refuse_on_text([{"shot": 0, "sub": 0}], object(), "a prompt", (3, 3, (2048, 2048)), "hall")
    assert capsys.readouterr().out == ""


def test_accept_dirty_draws_anyway_and_says_what_it_waived(boards, monkeypatch, capsys):
    """The escape is sanctioned and LOGGED. A gate with no way past it gets
    commented out, and a waiver nobody can read afterwards is a bug."""
    from studio.sheet_gate import Finding

    monkeypatch.setattr(boards.sheet_gate, "sheet_findings",
                        lambda *a, **k: [Finding("TWINS", "Q22_0", "the same picture as Q12_0",
                                                 hard=True, note="overlap 0.886")])
    monkeypatch.setattr(boards, "ACCEPT_DIRTY", True)
    boards.refuse_on_text([{"shot": 0, "sub": 0}], object(), "a prompt", (3, 3, (2048, 2048)), "hall")
    out = capsys.readouterr().out
    assert "ACCEPT-DIRTY" in out and "0.886" in out


def test_without_the_flag_the_refusal_names_the_escape(boards, monkeypatch):
    """A refusal that does not say how to proceed is a wall, not a gate."""
    from studio.sheet_gate import Finding

    monkeypatch.setattr(boards.sheet_gate, "sheet_findings",
                        lambda *a, **k: [Finding("TWINS", "Q22_0", "the same picture", hard=True)])
    monkeypatch.setattr(boards, "ACCEPT_DIRTY", False)
    with pytest.raises(SystemExit, match="--accept-dirty"):
        boards.refuse_on_text([{"shot": 0, "sub": 0}], object(), "a prompt", (3, 3, (2048, 2048)), "hall")
