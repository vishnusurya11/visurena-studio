"""Fleet C A8 (2026-10-22): the clock report says what the retakes cost, per episode.

One serial GPU makes render COUNT the lever (100 episodes at 6 h is 600 machine hours), yet the
report summed stage rows and never split first draws from retakes: ep01's first draws priced at
33 min sat inside 84.7 min of render spans with no line saying how much was retakes.  The report
reads takes/r2v/renders.jsonl: first draws, retakes by reason, and lost renders, in minutes."""
from __future__ import annotations

import json

import pytest

from studio import episode_clock as ck


@pytest.fixture
def book(tmp_path, monkeypatch):
    monkeypatch.setattr(ck.episode_home, "home", lambda b, n: tmp_path / f"ep{n:02d}")
    return tmp_path


def renders(book, rows: list[dict]) -> None:
    room = book / "ep01" / "takes" / "r2v"
    room.mkdir(parents=True)
    (room / "renders.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


ROWS = [{"index": 1, "ok": True, "render_s": 120.0, "tries": 0},
        {"index": 2, "ok": True, "render_s": 180.0, "tries": 0},
        {"index": 1, "ok": True, "render_s": 90.0, "tries": 1, "retake_why": "frozen"},
        {"index": 2, "ok": True, "render_s": 60.0, "tries": 1, "retake_why": "seam"},
        {"index": 2, "ok": True, "render_s": 30.0, "tries": 2, "retake_why": "seam"},
        {"index": 3, "ok": False, "waited_s": 45.0, "tries": 0, "lost": "interrupted"}]


def test_three_retakes_are_counted_in_minutes_by_reason(book):
    ck.stamp(book, 1, "takes", 0, 600)
    renders(book, ROWS)
    line = ck.render_line(ck.render_rows(book, 1))
    assert line == "renders: 2 first draws 5.0 min | 3 retakes 3.0 min (seam 2, frozen 1) | 1 lost 0.8 min"
    assert line in ck.report(book, 1)


def test_a_row_written_before_the_round_was_kept_counts_by_order(book):
    """renders.jsonl rows from before fleet C A1 carry no `tries`: an index seen before is a retake."""
    renders(book, [{"index": 4, "ok": True, "render_s": 60.0}, {"index": 4, "ok": True, "render_s": 60.0}])
    assert ck.render_line(ck.render_rows(book, 1)) == "renders: 1 first draw 1.0 min | 1 retake 1.0 min (unnamed 1)"


def test_an_episode_with_no_render_rows_says_nothing(book):
    ck.stamp(book, 1, "plan", 0, 60)
    assert ck.render_rows(book, 1) == [] and "renders:" not in ck.report(book, 1)
