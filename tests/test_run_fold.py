"""studio/run_fold.py: the spans of an episode folded from its step markers, over the
frozen ep01 ledger (Jekyll Kawajiri, 2026-10-18).  $0: copies of the named records."""
from __future__ import annotations

import json
from pathlib import Path

from studio import run_fold

FIX = Path(__file__).resolve().parent / "fixtures" / "ep01_ledger"


def _rows() -> list[dict]:
    return [json.loads(x) for x in (FIX / "timing.jsonl").read_text(encoding="utf-8").splitlines() if x]


def _attempts() -> dict:
    return json.loads((FIX / "attempts.json").read_text(encoding="utf-8"))


def test_the_spans_equal_the_step_walls_of_07_08_and_09():
    totals, walls = run_fold.totals(_rows()), _attempts()
    assert abs(totals["07"]["secs"] - walls["wall.07"]["seconds"]) < 1.5
    assert abs(totals["08"]["secs"] - walls["wall.08"]["seconds"]) < 1.5
    assert abs(totals["09"]["secs"] - walls["wall.09"]["seconds"]) < 10.0     # the wall adds the step's closing


def test_the_negative_takes_row_adds_nothing():
    rows = _rows()
    bad = [r for r in rows if r["seconds"] < 0]
    assert [r["seconds"] for r in bad] == [-421.1]
    assert run_fold.totals(rows) == run_fold.totals([r for r in rows if r["seconds"] >= 0])


def test_ep01_has_four_rewinds_and_names_them():
    got = [(r["frm"], r["to"]) for r in run_fold.rewinds(_rows())]
    assert got == [("03", "02"), ("05", "02"), ("09", "06"), ("10", "09")]


def test_a_step_restarted_after_a_killed_attempt_is_no_rewind():
    rows = [_mark("10", "2026-10-18T21:18:55"), _mark("09", "2026-10-18T22:47:51")]
    assert run_fold.rewinds(rows) == []


def test_a_rewind_never_lowers_a_steps_total():
    rows = _rows()
    before = run_fold.totals(rows[:84])["08"]["secs"]       # up to the 19:28 rewind
    assert run_fold.totals(rows)["08"]["secs"] >= before > 0


def test_a_step_with_no_marker_has_no_spans():
    assert "13" in run_fold.totals(_rows()) and "99" not in run_fold.totals(_rows())


def test_progress_rows_are_read_when_present():
    ev = [{"ev": "step", "step": "08", "state": "start", "t": 100.0},
          {"ev": "step", "step": "08", "state": "done", "t": 160.0},
          {"ev": "step", "step": "09", "state": "start", "t": 160.0}]
    assert run_fold.from_progress(ev)["08"]["secs"] == 60.0


def test_the_home_reader_prefers_progress_jsonl(tmp_path):
    (tmp_path / "timing.jsonl").write_text((FIX / "timing.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
    assert "07" in run_fold.fold_home(tmp_path)
    (tmp_path / "progress.jsonl").write_text(json.dumps({"ev": "step", "step": "02", "state": "start", "t": 5.0})
                                             + "\n", encoding="utf-8")
    assert list(run_fold.fold_home(tmp_path)) == ["02"]


def _mark(step: str, ts: str) -> dict:
    return {"stage": f"step_{step}", "started": ts, "ended": ts, "seconds": 0.0, "event": "started"}


def test_the_killed_attempt_is_found_and_priced_to_the_next_marker():
    """R8: step 10 at 21:18:55 did no work until step 09 started again at 22:47:51 (the 41 min
    av3 hang plus its relaunch wait) -- spanless in timing.jsonl, so only the fold can name it."""
    got = run_fold.killed(_rows())
    assert [(k["step"], round(k["secs"] / 60, 1)) for k in got] == [("10", 88.9)]


def test_every_step_reports_charged_against_its_wall_where_a_wall_exists():
    totals, walls = run_fold.totals(_rows()), _attempts()
    gaps = {sid: totals[sid]["secs"] - walls[f"wall.{sid}"]["seconds"] for sid in totals if f"wall.{sid}" in walls}
    assert max(abs(g) for k, g in gaps.items() if k in ("06", "07", "08", "09", "10", "11")) < 10.0
