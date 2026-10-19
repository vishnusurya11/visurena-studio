"""The rail keeps a step's history across rewinds (Jekyll Kawajiri ep01 19:28: the owner's
rewind to 06 started a new run, and the card, reading only the newest run, blanked 08 and 09
-- steps with 1 h 06 m and 58 m of work).  A step with spans says `done earlier`; `waiting`
stands only for a step with zero spans.  $0: the frozen ep01 ledger."""
from __future__ import annotations

import json
from pathlib import Path

from studio import run_fold
from studio.command_center import progress_view as pv
from test_progress_card_api import board  # noqa: F401  (the fixture)

FIX = Path(__file__).resolve().parent / "fixtures" / "ep01_ledger"


def _folded(upto: int | None = None) -> dict:
    rows = [json.loads(x) for x in (FIX / "timing.jsonl").read_text(encoding="utf-8").splitlines() if x]
    return run_fold.totals(rows[:upto])


def _rail(*ids: str) -> list[dict]:
    return [{"id": i, "name": f"s{i}", "state": "waiting", "secs": None, "end": None, "median_s": None,
             "retries": 0} for i in ids]


def _by(steps: list[dict]) -> dict:
    return {s["id"]: s for s in steps}


def test_after_the_19_28_rewind_08_and_09_read_done_earlier_with_their_time():
    got = _by(pv.with_history(_rail("06", "07", "08", "09", "10"), _folded(84), kept={"08", "09"}))
    assert got["08"]["state"] == "done" and got["08"]["fin"] == "done earlier 39m"
    assert got["09"]["state"] == "done" and "done earlier" in got["09"]["fin"]


def test_a_step_that_will_run_again_says_redo_pending():
    steps = [{**s, "will_run": True} for s in _rail("08")]
    got = _by(pv.with_history(steps, _folded(84), kept=set()))["08"]
    assert got["state"] == "earlier" and got["fin"] == "done earlier 39m · redo pending"


def test_waiting_stands_only_for_a_step_with_no_spans():
    got = _by(pv.with_history(_rail("08", "13"), _folded(84), kept=set()))
    assert got["08"]["state"] == "earlier" and got["13"]["state"] == "waiting" and not got["13"].get("fin")


def test_a_step_that_ran_this_run_is_left_alone():
    steps = [{**_rail("08")[0], "state": "running", "fin": ""}]
    assert pv.with_history(steps, _folded(84), kept=set()) == steps


def test_a_two_second_step_still_has_its_history():
    got = _by(pv.with_history(_rail("05"), _folded(), kept={"05"}))["05"]
    assert got["fin"] == "done earlier 2s"


def test_make_steps_is_the_one_reader():
    rows = [json.loads(x) for x in (FIX / "timing.jsonl").read_text(encoding="utf-8").splitlines() if x]
    assert pv.make_steps(rows, None)["08"]["secs"] == run_fold.totals(rows)["08"]["secs"]
    assert pv.make_steps(rows, None)["09"]["secs"] > 7000          # the -421.1 s row no longer shaves it


# --- the debt lines (P15: owed units, the 6 h hard stop, flagged seconds, fixes waiting) ---


def test_the_debt_text_names_the_owed_band_the_hard_stop_the_flags_and_the_fixes():
    from studio import eta
    owed = eta.owed_eta([192] * 3, [], now=1_800_000_000.0, work_s=3600.0)
    flagged = [{"take": "T07", "seconds_in_master": 2.5}]
    got = pv.debt_text(3, owed, flagged, 2, 3600.0, lambda t: "9:40 pm")
    assert got.startswith("3 takes owed · ")
    assert "hard stop 9:40 pm · 1h00 of 6h used" in got
    assert "1 flagged take ships, 2.5 s total" in got and "2 fixes waiting for the next pause" in got


def test_nothing_owed_and_nothing_flagged_leaves_only_the_hard_stop():
    from studio import eta
    owed = eta.owed_eta([], [], now=1_800_000_000.0, work_s=60.0)
    assert pv.debt_text(0, owed, [], 0, 60.0, lambda t: "9:40 pm") == "hard stop 9:40 pm · 0h01 of 6h used"


def test_a_band_past_the_hard_stop_is_said_so():
    from studio import eta
    owed = eta.owed_eta([192] * 28, [], now=1_800_000_000.0, work_s=6 * 3600.0 - 600.0)
    assert "past the hard stop" in pv.debt_text(28, owed, [], 0, 6 * 3600.0 - 600.0, lambda t: "9:40 pm")


def test_the_flagged_takes_are_read_from_the_k7_file(tmp_path):
    (tmp_path / "work_r2v").mkdir()
    (tmp_path / "work_r2v" / "flagged_takes.json").write_text(
        json.dumps([{"take": "T07", "shot": 7, "seconds_in_master": 2.0, "severity": "high"}]), encoding="utf-8")
    assert [r["take"] for r in pv.flagged_takes(tmp_path)] == ["T07"]
    assert pv.flagged_takes(tmp_path / "nope") == []


def test_the_fixes_waiting_count_starts_from_the_running_sha(tmp_path):
    ledger = [{"event": "start", "sha": "aaa111"}, {"event": "end"}, {"event": "start", "sha": "bbb222"}]
    (tmp_path / "drive.jsonl").write_text("\n".join(json.dumps(r) for r in ledger), encoding="utf-8")
    assert pv.running_sha(tmp_path) == "bbb222"
    seen = []
    assert pv.fixes_waiting(tmp_path, 0.0, count=lambda sha: seen.append(sha) or 3) == 3 and seen == ["bbb222"]
    assert pv.fixes_waiting(tmp_path / "none", 0.0, count=lambda sha: 9) == 0


def test_the_whole_card_keeps_history_for_a_step_the_newest_run_never_touched(board):
    from test_progress_card_api import _drive, _progress
    import time
    (board["home"] / "timing.jsonl").write_text((FIX / "timing.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
    got = {s["id"]: s for s in _progress(board, _drive(time.time() - 3600))["steps"]}
    assert "waiting" not in {got[i]["state"] for i in ("03", "07", "08")}
    assert all(got[i]["fin"] for i in ("03", "07", "08"))
    assert "03" in got and got["01"]["state"] != "earlier"
