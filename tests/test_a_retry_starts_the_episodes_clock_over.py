"""ep19, 2026-10-07 18:19Z: the take ladder ended at attempt 0 on the episode
clock -- the five-hour ceiling had been spent by the day's three plan climbs
(code faults, each relaunched by the owner's `retry`), so EYE_TAKES signed
keep_best over a frozen take, a hard cut and a clone, and the run went to
publish.  A retry is the owner's fresh launch: the clock starts over at it.
`run_budget.reset_clock(home)` stamps the home; `spent_before` counts only
the timing rows that ended after the stamp.  $0."""
from __future__ import annotations

import json
from pathlib import Path

from studio import run_budget


def rows(tmp: Path, ended: list[str], seconds: float = 1000.0) -> Path:
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "timing.jsonl").write_text("".join(
        json.dumps({"stage": "s", "started": e, "ended": e, "seconds": seconds, "ok": True}) + "\n"
        for e in ended), encoding="utf-8")
    return tmp


def test_rows_before_the_reset_do_not_count(tmp_path):
    home = rows(tmp_path, ["2026-10-07T10:00:00", "2026-10-07T12:00:00", "2026-10-07T14:00:00"])
    assert run_budget.spent_before(home) == 3000.0
    run_budget.reset_clock(home, at="2026-10-07T13:00:00")
    assert run_budget.spent_before(home) == 1000.0


def test_a_row_without_an_end_still_counts_and_no_stamp_changes_nothing(tmp_path):
    home = tmp_path / "ep"
    home.mkdir()
    (home / "timing.jsonl").write_text(json.dumps({"stage": "s", "seconds": 500.0}) + "\n", encoding="utf-8")
    run_budget.reset_clock(home, at="2026-10-07T13:00:00")
    assert run_budget.spent_before(home) == 500.0
    assert run_budget.spent_before(rows(tmp_path / "other", ["2026-10-07T10:00:00"])) == 1000.0


def test_reset_clock_stamps_now_by_default(tmp_path):
    stamp = run_budget.reset_clock(tmp_path)
    doc = json.loads((tmp_path / run_budget.CLOCK_RESET).read_text(encoding="utf-8"))
    assert doc["at"] == stamp and len(stamp) >= 19


def test_the_autopilots_retry_resets_the_clock(tmp_path, monkeypatch):
    from tests import autopilot_cli_fixtures as fx
    cli = fx.load()
    root = fx.book(tmp_path)
    home = root / "episodes" / "ep19"
    home.mkdir(parents=True)
    cli.retry(root, 19)
    assert (home / run_budget.CLOCK_RESET).exists()
