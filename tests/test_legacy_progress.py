"""v1's progress source (progress tracker spec, read side): the board derives
progress events from what a run already writes -- the drive log's banners and
take lines, the events table, the runner log's ladder rungs, drive.jsonl and
file mtimes -- and folds them with the same `fold()` v2 will feed from
progress.jsonl.  Fixtures are frozen real files."""
from __future__ import annotations

import json
from pathlib import Path

from studio import progress
from studio.command_center import legacy_progress as lp

FIX = Path(__file__).resolve().parent / "fixtures" / "progress"
EP14 = (FIX / "ep14_drive_run02.log").read_text(encoding="utf-8")
EP17_LOG = (FIX / "ep17_drive_run01.log").read_text(encoding="utf-8")
FRAMES = {f"T{i:02d}": 150 for i in range(30)}


def _runner_rows() -> list[dict]:
    return [json.loads(l) for l in (FIX / "ep17_runner.log").read_text(encoding="utf-8").splitlines() if l]


def _ledger() -> list[dict]:
    return [json.loads(l) for l in (FIX / "ep17_drive.jsonl").read_text(encoding="utf-8").splitlines() if l]


def test_the_banner_names_the_run():
    assert lp.banner_run(EP17_LOG) == "20260827135508__episode__20261005004347"
    assert lp.banner_run("nothing here") is None


def test_the_banners_name_the_steps():
    names = lp.step_names(EP14)
    assert names["09"] == "shoot" and names["01"] == "bind" and names["10"] == "edit"


def test_db_rows_of_this_run_become_step_events():
    rows = [{"event_ts": "2026-10-05T00:43:47Z", "step_id": "01", "event": "skipped", "run_id": "r"},
            {"event_ts": "2026-10-05T00:43:48Z", "step_id": "02", "event": "started", "run_id": "r"},
            {"event_ts": "2026-10-05T00:20:00Z", "step_id": "02", "event": "started", "run_id": "older"}]
    evs = lp.db_step_events(rows, "r", {"02": "plan"})
    assert [(e["step"], e["state"]) for e in evs] == [("01", "skip"), ("02", "start")]
    assert evs[1]["name"] == "plan" and evs[1]["t"] > evs[0]["t"]


def test_the_shoot_log_gives_a_plan_per_queue_line_and_four_landings():
    evs = lp.take_events(EP14, FRAMES, {}, step_t=100.0)
    plans = [e for e in evs if e["ev"] == "plan"]
    items = [e for e in evs if e["ev"] == "item"]
    assert len(plans) == 3 and len(plans[1]["items"]) == 30   # the provisional plan, then one per queue line
    assert set(i for i, _ in plans[2]["items"]) - set(plans[2]["kept"]) == {"T05", "T13", "T19"}
    assert [(e["item"], e["weight"], e["secs"]) for e in items][:2] == [("T07", 141, 491.0), ("T05", 158, 517.0)]


def test_the_folded_shoot_is_thirty_of_thirty():
    state = progress.fold(lp.take_events(EP14, FRAMES, {}, step_t=100.0))
    assert progress.counts(state)[:2] == (30, 30)


def test_a_shoot_with_no_queue_line_yet_keeps_what_is_on_disk():
    log = "--- step 09 (shoot) | x ---\n"
    evs = lp.take_events(log, {"T00": 100, "T01": 120}, {"T00": 50.0, "T01": 500.0}, step_t=100.0)
    assert evs[0]["kept"] == ["T00"] and len(evs[0]["items"]) == 2


def test_a_landing_carries_the_mp4_time_only_from_this_step():
    log = "--- step 09 (shoot) | x ---\n  queueing 1 takes in one go: T01\n  T01 shots [1] 120f 5.00s in 99s\n"
    old = lp.take_events(log, {"T01": 120}, {"T01": 50.0}, step_t=100.0)
    new = lp.take_events(log, {"T01": 120}, {"T01": 150.0}, step_t=100.0)
    assert old[-1]["t"] is None and new[-1]["t"] == 150.0


def test_no_shoot_banner_means_no_take_events():
    assert lp.take_events(EP17_LOG, FRAMES, {}, step_t=1.0) == []


def test_the_runner_log_gives_the_ladder_rungs():
    rows = [{"ts": "2026-10-03T19:23:15Z", "step_id": "ladders", "msg": "PLAN: measured 6.0 vs None -> keep_best (terminal)"},
            {"ts": "2026-10-03T19:22:46Z", "step_id": "ladders", "msg": "PLAN: measured 6.0 vs None -> fresh_brief"},
            {"ts": "2026-10-03T19:23:16Z", "step_id": "02", "msg": "PLAN: plan.verdict.json written"}]
    rungs = lp.runner_rounds(rows)
    assert [(r["gate"], r["measured"], r["action"], r["terminal"]) for r in rungs] == [
        ("PLAN", 6.0, "keep_best", True), ("PLAN", 6.0, "fresh_brief", False)]


def test_ep17s_runner_log_reads_its_rungs():
    assert any(r["gate"] == "PLAN" for r in lp.runner_rounds(_runner_rows()))


def test_the_ledger_gives_the_outcome_of_this_launchs_run():
    rows = [{"event": "start"}, {"event": "run", "n": 1, "outcome": "refused"}, {"event": "end"},
            {"event": "start"}, {"event": "run", "n": 1, "outcome": "deferred"}]
    assert lp.ledger_outcome(rows, 1) == "deferred"
    assert lp.ledger_outcome(rows, 2) is None
    assert lp.ledger_outcome(_ledger(), 1) is None


def test_the_drive_ended_only_after_its_last_start():
    assert lp.drive_ended([{"event": "start"}, {"event": "end"}]) is True
    assert lp.drive_ended([{"event": "end"}, {"event": "start"}]) is False


def test_the_log_says_completed():
    assert lp.log_outcome("x\n=== EPISODE completed | a ===\n") == "completed"
    assert lp.log_outcome(EP17_LOG) is None


def test_the_refusal_sentence_is_the_runner_logs():
    words = lp.refusal(_runner_rows())
    assert words.startswith("plan_check refused") and "\n" not in words


def test_panels_from_mtimes_land_after_the_step_started():
    evs = lp.panel_events(["00", "01", "02"], {"00": 10.0, "01": 200.0}, step_t=100.0)
    state = progress.fold(evs)
    assert progress.counts(state)[:2] == (2, 3)
    assert state["landed"] == {"01": 200.0}


def test_derive_folds_ep17_at_the_plan(tmp_path):
    home = tmp_path / "episodes" / "ep17"
    home.mkdir(parents=True)
    (home / "drive_run01.log").write_text(EP17_LOG, encoding="utf-8")
    (home / "drive.jsonl").write_text((FIX / "ep17_drive.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
    rows = [{"event_ts": "2026-10-05T00:43:47.74Z", "step_id": "01", "event": "skipped",
             "run_id": "20260827135508__episode__20261005004347"},
            {"event_ts": "2026-10-05T00:43:47.81Z", "step_id": "02", "event": "started",
             "run_id": "20260827135508__episode__20261005004347"}]
    got = lp.derive(home, rows, _runner_rows())
    state = progress.fold(got["events"])
    assert state["step"] == "02" and state["steps"]["02"]["name"] == "plan"
    assert state["outcome"] is None and got["run_id"].endswith("20261005004347")
    assert got["signals"] and got["last_words"]
