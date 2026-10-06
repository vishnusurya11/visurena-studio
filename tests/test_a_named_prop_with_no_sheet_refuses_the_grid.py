"""G-SHEET-DRAWN: `pack_refs.props_named`'s `(sheet := prop_sheet(...))` filter
silently DROPPED a named-but-undrawn prop, so the machine vanished from grid and
take with no fault anywhere.  `undrawn_named` returns exactly that set and the
grid refuses loudly instead of rendering without the machine.  tmp tree, $0."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))

import grids  # noqa: E402
from studio import pack_refs  # noqa: E402


def book_of(tmp_path, drawn: bool):
    (tmp_path / "analysis" / "props").mkdir(parents=True)
    (tmp_path / "analysis" / "props" / "fighting_machine.json").write_text(json.dumps(
        {"name": "the Martian fighting-machine", "aliases": ["tripod", "Titan"],
         "profile": {"physical": "A walking engine.", "scale": "A hundred feet high."}}),
        encoding="utf-8")
    if drawn:
        sheet = tmp_path / "refs" / "props" / "fighting_machine" / "sheet.png"
        sheet.parent.mkdir(parents=True)
        sheet.write_bytes(b"png")
    return tmp_path


class _Prose:
    def __init__(self, frame):
        self.frame, self.motion, self.at_rest = frame, "", ""


def test_undrawn_named_is_the_named_but_undrawn_set(tmp_path):
    book = book_of(tmp_path, drawn=False)
    prose = "a tripod striding over the pines"
    assert pack_refs.undrawn_named(book, ["fighting_machine"], prose) == ["fighting_machine"]
    assert pack_refs.undrawn_named(book, ["fighting_machine"], "the narrator at the reins") == []


def test_a_drawn_sheet_is_not_in_the_set(tmp_path):
    book = book_of(tmp_path, drawn=True)
    assert pack_refs.undrawn_named(book, ["fighting_machine"], "a tripod strides") == []


def test_the_grid_refuses_instead_of_dropping_the_machine(tmp_path):
    book = book_of(tmp_path, drawn=False)
    with pytest.raises(SystemExit, match="fighting_machine"):
        grids.props_of(book, ["fighting_machine"], [_Prose("a tripod striding over the pines")])


def test_a_drawn_prop_still_stages_normally(tmp_path):
    book = book_of(tmp_path, drawn=True)
    got = grids.props_of(book, ["fighting_machine"], [_Prose("a tripod striding over the pines")])
    assert [p["name"] for p in got] == ["the Martian fighting-machine"]
