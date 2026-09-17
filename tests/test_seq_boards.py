"""The sheet runner spends only on a retry that can say what to change.

Measured on episode 10: the mountain sheet's first draw was refused by
`white_lines()` alone (Q02_0's prompted moonlit rifle barrel), `strict_prefix()`
returned "" because there was no duplicate and no ladder regression to name,
and the strict retry drew the byte-identical prompt again for $0.13 -- the
strict sheet differs from the first by two blank lines.  A retry with no new
instruction is a re-roll, and a re-roll is refused here, with its reason.

And the report carries the alternate pairs (Q26_0 / Q26_0A at 0.718 over
ALIKE) as an advisory row: an alternate feeds no take, so it buys no retry.
"""
import importlib.util
from pathlib import Path

import pytest
from PIL import Image

from studio import house_style
from studio.episode_spec import Setup

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def boards():
    spec = importlib.util.spec_from_file_location("sb_runner", ROOT / "scripts/episode/seq_boards.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Drawer:
    """A drawer that spends nothing: every draw is counted and writes a grey square."""
    def __init__(self):
        self.drew = []

    def draw(self, text, refs, out, size, approved=None):
        self.drew.append(text)
        Image.new("L", (64, 64), 120).save(out)
        return out

    def conform(self, src, dst, box=None):
        Image.new("L", (16, 16), 120).save(dst)
        return dst


SETUP = Setup(described="A mountain trail by night.", cast=[])
GROUP = [{"shot": 0, "sub": 0, "size": "wide", "path": 0.0, "faces": [], "frame": "Wide of the trail.",
          "camera": "on the trail at a rider's eye, a 35mm lens", "motion": "the riders halt",
          "at_rest": "The riders stand in the CENTRE.", "end_frame": "", "changed": "", "crowd": ""},
         {"shot": 2, "sub": 0, "size": "insert", "path": None, "faces": [], "frame": "Insert on a rifle.",
          "camera": "an arm's length from the stock, a 90mm lens", "motion": "the hand tightens",
          "at_rest": "The stock crosses the CENTRE.", "end_frame": "", "changed": "", "crowd": ""}]


@pytest.fixture
def quiet(boards, monkeypatch, tmp_path):
    """Every pixel gate answered without pixels; the drawer is the only thing under test."""
    (tmp_path / "cells").mkdir()
    (tmp_path / "sheets").mkdir()
    monkeypatch.setattr(boards.sheet_gate, "sheet_findings", lambda *a, **k: [])
    monkeypatch.setattr(boards.board, "cell_boxes", lambda grey, cols, rows: [(0, 0, 8, 8)] * (cols * rows))
    monkeypatch.setattr(boards.board, "bands", lambda grey, axis: [(0, 1)] if axis == 1 else [])  # 2 by 1
    monkeypatch.setattr(boards, "look_of", lambda cells, name: [])
    monkeypatch.setattr(boards.sq, "alt_duplicates", lambda cells, segs: [])
    house_style.adopt("", "")
    return tmp_path


def draw(boards, root, drawer):
    report = {"sheets": [], "dropped_ends": []}
    entry = boards.draw_sheet(drawer, root, "trail", 0, GROUP, [], (2, 1, (2048, 1024)), SETUP, {}, [],
                              report, aspect="1:1")
    return entry, report


def test_no_strict_retry_without_a_named_offender(boards, monkeypatch, quiet, capsys):
    monkeypatch.setattr(boards, "white_lines", lambda cells: ["Q02_0.png"])
    monkeypatch.setattr(boards.sq, "duplicates", lambda cells, segs: [])
    drawer = Drawer()
    entry, report = draw(boards, quiet, drawer)
    assert len(drawer.drew) == 1
    assert entry["strict"] is False and len(report["sheets"]) == 1
    assert "Q02_0.png" in entry["strict_refused"] and "re-roll" in entry["strict_refused"]
    out = capsys.readouterr().out
    assert "strict retry refused" in out and "white_lines_in" in out


def test_a_named_duplicate_still_earns_the_strict_retry(boards, monkeypatch, quiet):
    monkeypatch.setattr(boards, "white_lines", lambda cells: [])
    answers = iter([[("Q00_0", "Q02_0")], []])
    monkeypatch.setattr(boards.sq, "duplicates", lambda cells, segs: next(answers))
    drawer = Drawer()
    entry, report = draw(boards, quiet, drawer)
    assert len(drawer.drew) == 2
    assert drawer.drew[1].startswith("STRICT: panels Q00_0 and Q02_0")
    assert entry["strict"] is True and "strict_refused" not in entry


def test_the_refusal_names_every_fault_the_prefix_cannot_address(boards):
    said = boards.reroll_reason({"white_lines_in": ["Q02_0.png"], "gutters_ok": False,
                                 "duplicates": [], "regressions": []})
    assert "white_lines_in ['Q02_0.png']" in said and "gutters_ok False" in said
    assert "redraw_panel" in said


# ---- D5  the alternate row is advisory --------------------------------------

def test_the_report_carries_alternate_pairs_and_clean_ignores_them(boards, monkeypatch, quiet):
    monkeypatch.setattr(boards, "white_lines", lambda cells: [])
    monkeypatch.setattr(boards.sq, "duplicates", lambda cells, segs: [])
    monkeypatch.setattr(boards.sq, "alt_duplicates", lambda cells, segs: [("Q26_0", "Q26_0A")])
    drawer = Drawer()
    entry, _report = draw(boards, quiet, drawer)
    assert entry["alternate_duplicates"] == [("Q26_0", "Q26_0A")]
    assert boards.clean(entry) is True and len(drawer.drew) == 1
