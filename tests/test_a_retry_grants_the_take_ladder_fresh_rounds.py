"""Owner, 2026-10-07 19:40Z: 'do the iterations and DQ check and finish it; we
have the five-hour limit per episode, use it.'  ep19's take ladder went
keep_best at attempt 0 on the owner's relaunch because ROUNDS_CAP (2) counts
rounds ACROSS resumes.  A retry stamps the clock (run_budget.reset_clock);
rounds taken before the stamp are an earlier attempt's.  The per-take attempt
cap and the progress breaker still bound the work.  $0."""
from __future__ import annotations

import json
import time
from pathlib import Path

from studio import run_budget, take_ladder as tl


def _room_with_rounds(tmp_path: Path, ats: list[float]) -> Path:
    room = tmp_path / "takes" / "r2v"
    room.mkdir(parents=True)
    (room / tl.LADDER_FILE).write_text(json.dumps({"rounds": [{"why": "x", "at": at} for at in ats]}), encoding="utf-8")
    return room


def test_rounds_before_the_stamp_do_not_count():
    now = time.time()
    room = _room_with_rounds(Path(tl.__file__).parent / ".." / "tests" / "_tmp_rounds" if False else Path(__import__("tempfile").mkdtemp()), [now - 7200, now - 3600, now - 10])
    assert tl.rounds_of(room) == 3
    assert tl.rounds_of(room, since=now - 100) == 1
    assert tl.rounds_of(room, since=now + 1) == 0


def test_the_clock_reset_epoch_reads_the_stamp(tmp_path):
    assert run_budget.clock_reset_epoch(tmp_path) == 0.0
    run_budget.reset_clock(tmp_path)
    assert abs(run_budget.clock_reset_epoch(tmp_path) - time.time()) < 5


def test_a_capped_room_is_curable_again_after_a_reset(tmp_path, monkeypatch):
    now = time.time()
    room = _room_with_rounds(tmp_path, [now - 7200, now - 3600])
    verdict = type("V", (), {"faults": []})()
    monkeypatch.setattr(tl, "route", lambda v, r, try_i=1: {"seed": {2: []}})
    assert tl.still_curable(room, verdict) is False                       # the cap, as before
    assert tl.still_curable(room, verdict, since=now - 100) is True       # a fresh attempt's rounds
