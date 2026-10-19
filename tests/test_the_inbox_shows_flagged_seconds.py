"""The inbox row of a unit that shipped with flags says how many takes ship flagged and for how
many seconds of the master (Jekyll Kawajiri ep01: 9 flagged takes shipped and the owner's only
line was `shipped with flags, not acknowledged`).  Reads takes/work/flagged_takes.json (K7), where assemble writes it.  $0."""
from __future__ import annotations

import json

from studio.command_center import views

CODEX = "20260827135504"


def _library(tmp_path, rows):
    room = tmp_path / f"{CODEX}_a-book" / "episodes" / "ep01" / "takes" / "work"
    room.mkdir(parents=True)
    if rows is not None:
        (room / "flagged_takes.json").write_text(json.dumps(rows), encoding="utf-8")
    return tmp_path


def test_the_line_is_n_flagged_takes_over_total_seconds():
    rows = [{"take": "T07", "seconds_in_master": 2.5}, {"take": "T10", "seconds_in_master": 3.0}]
    assert views.flagged_line(rows) == "2 flagged takes / 5.5 s"
    assert views.flagged_line(rows[:1]) == "1 flagged take / 2.5 s"
    assert views.flagged_line([]) == ""


def test_the_reason_carries_the_line_when_the_unit_wrote_the_file(tmp_path):
    lib = _library(tmp_path, [{"take": "T07", "seconds_in_master": 2.5}])
    assert views.flagged_reason(lib, CODEX, "ep01") == f"{views.FLAGGED_REASON} · 1 flagged take / 2.5 s"


def test_the_reason_is_unchanged_without_the_file(tmp_path):
    lib = _library(tmp_path, None)
    assert views.flagged_reason(lib, CODEX, "ep01") == views.FLAGGED_REASON
    assert views.flagged_reason(tmp_path / "nowhere", CODEX, "ep01") == views.FLAGGED_REASON
