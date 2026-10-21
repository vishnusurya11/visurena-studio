"""The default suite's one rehearsal (2026-10-21_ep02_proof DESIGN 3): one checkpoint, one take, one
fault, under 60 s, through the REAL autopilot tick in a fenced child process.

The sandbox is built from tests/fixtures only (no HDD read): a one-take ep02 at `after_12` whose
last drive stopped at G-STANDING, and the supervisor's heartbeat torn mid-write (F18 on the
supervisor's own record).  The real tick must read the torn record, rebuild it and end HELD_PUBLISH
named, with no traceback, nothing reaching outside the sandbox, and a recovery trace on disk.
The supervisor's own helpers (pid ancestry, the terminal and tick-cap rules, the in-process
hand-over) are pinned here too, on fakes."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.proof import rehearse
from studio.command_center.procs import ProcInfo
from studio.rehearsal import asserts, supervisor
from tests.proof_sandbox_fixture import tiny_sandbox


def test_one_checkpoint_one_take_one_fault_ends_named_under_a_minute(tmp_path):
    began = time.monotonic()
    box = tiny_sandbox(tmp_path, run_id="smoke")
    out = rehearse.run_scenario("smoke", results=tmp_path / "results", box=box, cleared=True)
    doc = json.loads((tmp_path / "results" / "smoke.json").read_text(encoding="utf-8"))
    rows = {r["check"]: r for r in doc["rows"]}
    assert out["supervisor"]["terminal"] == "HELD_PUBLISH", out
    assert out["supervisor"]["tick_errors"] == 0
    failed = {k: r["detail"] for k, r in rows.items() if not r["passed"]}
    assert not failed, failed
    assert {"A-caps", "A-noupload", "A-named", "A-real", "A-torn", "A-ledger", "smoke"} <= set(rows)
    assert all(set(asserts.ROW_KEYS) <= set(r) for r in doc["rows"])
    assert rows["smoke"]["n_points"] == 1 and rows["smoke"]["n_distinct"] == 1
    assert out["trace"] and any(f == "scripts/episode/autopilot.py" for f, _ in out["trace_lines"])
    assert time.monotonic() - began < 60


# ---- the supervisor's own rules, on fakes ------------------------------------------------

def test_the_tree_is_every_descendant_of_the_supervisor_and_of_any_pid_it_ever_held():
    parents = {10: 1, 11: 10, 12: 11, 20: 1, 30: 99}
    assert supervisor.descendants(parents, {10}) == {10, 11, 12}
    assert supervisor.descendants(parents, {10, 99}) == {10, 11, 12, 99, 30}     # an orphan of a dead drive


def test_the_process_table_is_filtered_to_the_tree():
    rows = [ProcInfo(11, None, "drive.py 9999 2"), ProcInfo(20, None, "drive.py 2026 2"), ProcInfo(12, None, "x")]
    known: set = set()
    got = supervisor.tree_procs(10, known, table=lambda: rows, parents=lambda: {11: 10, 12: 11, 20: 1})
    assert [p.pid for p in got] == [11, 12] and known == {11, 12}


def test_the_drive_argv_carries_the_run_id_tail():
    argv = supervisor.drive_argv_for("r1")("9999", 2)
    assert argv[-1] == "--rehearsal=r1" and "scripts/episode/drive.py" in argv and argv[-3:-1] == ["9999", "2"]


def test_a_terminal_is_read_only_for_the_rehearsed_unit():
    assert supervisor.terminal_of({"episode": {"n": 2, "state": "HELD_PUBLISH"}}, 2) == "HELD_PUBLISH"
    assert supervisor.terminal_of({"episode": {"n": 3, "state": "PARKED"}}, 2) is None
    assert supervisor.terminal_of({"episode": {"n": None, "state": "COMPLETE"}}, 2) == "COMPLETE"
    assert supervisor.terminal_of({"episode": {"n": 2, "state": "RUNNING"}}, 2) is None
    assert supervisor.terminal_of(None, 2) is None


def fake_autopilot(states: list[str]):
    ticks = iter(states)
    return SimpleNamespace(
        claim_supervisor=lambda deps: True, adopt=lambda book, deps: None, event=lambda book, row: row,
        hand_over=lambda book, codex, deps, born: None,
        tick=lambda book, codex, deps, i: {"episode": {"n": 2, "state": next(ticks), "action": "launch"}})


def deps_stub():
    return SimpleNamespace(git=lambda *a: "abc\n", sleep=lambda s: None, procs=lambda: [])


def test_the_loop_stops_at_the_terminal(tmp_path):
    ap = fake_autopilot(["IDLE", "RUNNING", "HELD_PUBLISH"])
    out = supervisor.loop(ap, tmp_path, "9999", 2, deps_stub(), expected=3, every=0, wall_s=60)
    assert out["terminal"] == "HELD_PUBLISH" and out["ticks"] == 3 and not out["capped"]


def test_twice_the_expected_acting_ticks_is_a_failure_not_a_wait(tmp_path):
    ap = fake_autopilot(["IDLE"] * 50)
    out = supervisor.loop(ap, tmp_path, "9999", 2, deps_stub(), expected=2, every=0, wall_s=60)
    assert out["terminal"] is None and out["capped"] == "ticks" and out["acting"] == 5


def test_a_tick_that_raises_is_counted_and_the_loop_goes_on(tmp_path):
    ap = fake_autopilot(["HELD_PUBLISH"])
    real = ap.tick
    calls = {"n": 0}

    def tick(*a):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("torn")
        return real(*a)
    ap.tick = tick
    out = supervisor.loop(ap, tmp_path, "9999", 2, deps_stub(), expected=2, every=0, wall_s=60)
    assert out["terminal"] == "HELD_PUBLISH" and out["tick_errors"] == 1


def test_a_moved_head_is_handed_over_in_process_never_to_a_spawned_successor(tmp_path):
    ap = fake_autopilot(["RUNNING", "HELD_PUBLISH"])
    heads = iter(["def456", None])
    ap.hand_over = lambda book, codex, deps, born: next(heads)
    out = supervisor.loop(ap, tmp_path, "9999", 2, deps_stub(), expected=2, every=0, wall_s=60)
    assert out["handovers"] == ["def456"] and out["born"] == "def456"


def test_a_kill_request_kills_the_rest_of_the_drive_tree_once(tmp_path):
    (tmp_path / "kill.request").write_text(json.dumps({"fault": {"kind": "kill_at_write"}, "pid": 5}))
    killed = []
    engine = SimpleNamespace(kill_run_tree=lambda rows, codex, n: killed.append((codex, n)) or [6, 7])
    deps = SimpleNamespace(engine=engine, procs=lambda: [])
    assert supervisor.kill_on_request(tmp_path, deps, "9999", 2) == [6, 7]
    assert supervisor.kill_on_request(tmp_path, deps, "9999", 2) == []
    assert killed == [("9999", 2)] and (tmp_path / "kill.done").exists()


def test_the_notify_capture_appends_one_row_per_message(tmp_path):
    say = supervisor.notify_to(tmp_path)
    say("ep02 HELD before upload")
    rows = [json.loads(line) for line in (tmp_path / "notify.jsonl").read_text().splitlines()]
    assert rows[0]["text"] == "ep02 HELD before upload" and rows[0]["source"] == "autopilot"


@pytest.mark.skipif(os.name != "nt", reason="the parent map reads the Windows process table")
def test_the_parent_map_knows_this_process_and_its_parent():
    parents = supervisor.parent_map()
    assert parents.get(os.getpid()) == os.getppid()


def test_a_scenario_whose_packages_are_absent_says_which():
    assert rehearse.missing_packages("smoke") == []
    assert set(rehearse.missing_packages("F1", present=lambda m: False)) >= {"studio.rehearsal.fake_comfy"}


def test_the_stage_copies_the_fixture_into_the_sandbox_book(tmp_path):
    box = tiny_sandbox(tmp_path, run_id="stage")
    book = rehearse.stage(box, rehearse.SCENARIOS / "smoke")
    assert (book / "episodes" / "ep02" / "drive.jsonl").is_file()
    assert (box / "library" / ".autopilot" / "heartbeat.json").is_file()
    assert book.parent == box / "library"


def test_the_guard_excuses_only_a_named_live_writer_outside_the_rehearsal(monkeypatch):
    lib = rehearse.settings.REPO / "library"
    moved = [f"REAL LIBRARY TOUCHED: {lib / '.device' / 'gpu_util.jsonl'}", f"REAL LIBRARY TOUCHED: {lib / '.autopilot'}",
             f"REAL LIBRARY TOUCHED: {lib / '.autopilot' / 'heartbeat.json'}",
             f"REAL LIBRARY TOUCHED: {lib / '2026_book' / 'autopilot'}"]
    monkeypatch.setattr(rehearse.guard, "snapshot", lambda paths: {})
    monkeypatch.setattr(rehearse.guard, "named_paths", lambda: [])
    monkeypatch.setattr(rehearse.guard, "touched", lambda a, b: moved)
    r = rehearse.guard_row({}, writers=lambda: {"gpu_ledger.py": 4242, "autopilot.py": 56132})
    assert r["passed"] is True and "gpu_ledger.py pid 4242" in r["detail"] and "autopilot.py pid 56132" in r["detail"]
    assert rehearse.guard_row({}, writers=lambda: {"gpu_ledger.py": 4242})["passed"] is False
    monkeypatch.setattr(rehearse.guard, "touched", lambda a, b: [f"REAL LIBRARY TOUCHED: {lib / '2026_book' / 'episodes' / 'ep02'}"])
    assert rehearse.guard_row({}, writers=lambda: {"gpu_ledger.py": 4242, "autopilot.py": 56132})["passed"] is False


def test_a_live_writer_inside_the_rehearsal_tree_is_never_excused():
    rows = [ProcInfo(os.getpid(), None, "python scripts/episode/gpu_ledger.py"), ProcInfo(999999, None, "python gpu_ledger.py")]
    assert rehearse.live_writers(table=lambda: rows) == {"gpu_ledger.py": 999999}


# ---- boundaries: the checkpoint maker, a bounded run, a commit mid-run -----------------------

def home_with_log(tmp_path: Path, text: str) -> Path:
    home = tmp_path / "library" / "b" / "episodes" / "ep01"
    home.mkdir(parents=True)
    (home / "drive_run01.log").write_text(text, encoding="utf-8")
    return home


def test_a_stop_in_front_of_a_step_names_that_step_and_a_rung_stop_names_none(tmp_path):
    home = home_with_log(tmp_path, "--- step 08 (panels) | x ---\nPAUSED AT BOUNDARY | ep01 | before step 09\n")
    assert supervisor.stopped_before(home) == "09" and supervisor.latest_step(home) == 8
    (home / "drive_run02.log").write_text("--- step 09 (shoot) | x ---\nPAUSED AT BOUNDARY | ep01 | G-TAKE before rung r2 #2\n")
    assert supervisor.stopped_before(home) is None and supervisor.latest_step(home) == 9


def test_the_checkpoint_maker_copies_a_drive_stopped_before_a_step_once(tmp_path):
    box = tiny_sandbox(tmp_path, run_id="cp")
    home = box / "library" / "x" / "episodes" / "ep01"
    home.mkdir(parents=True)
    (home / "drive_run01.log").write_text("PAUSED AT BOUNDARY | ep01 | before step 09\n")
    state = {"made": []}
    supervisor.checkpoint_tick(box, home, alive=False, state=state)
    supervisor.checkpoint_tick(box, home, alive=False, state=state)
    assert state["made"] == ["after_08"] and (box / "checkpoints" / "after_08" / "library").is_dir()


def test_the_checkpoint_maker_asks_a_running_drive_to_stop_only_after_it_made_progress(tmp_path):
    from studio import boundary
    home = home_with_log(tmp_path, "--- step 09 (shoot) | x ---\n")
    state = {"made": [], "stopped_at": time.time() + 3600}
    supervisor.checkpoint_tick(tmp_path, home, alive=True, state=state)
    assert not boundary.requested(home)                     # nothing landed since the last stop
    state["stopped_at"] = time.time() - 60
    (home / "T00.graph.json").write_text("{}")              # an artifact landed after the stop
    supervisor.checkpoint_tick(tmp_path, home, alive=True, state=state)
    assert boundary.requested(home)


def test_a_bounded_run_asks_for_the_boundary_past_its_step_and_ends_there(tmp_path):
    from studio import boundary
    home = home_with_log(tmp_path, "--- step 09 (shoot) | x ---\n")
    assert supervisor.bounded_tick(home, alive=True, bound="09") is None and not boundary.requested(home)
    (home / "drive_run01.log").write_text("--- step 09 (shoot) | x ---\n--- step 10 (edit) | x ---\n")
    assert supervisor.bounded_tick(home, alive=True, bound="09") is None and boundary.requested(home)
    (home / "drive_run01.log").write_text("--- step 10 (edit) | x ---\nPAUSED AT BOUNDARY | ep01 | before step 11\n")
    assert supervisor.bounded_tick(home, alive=False, bound="09") == "BOUNDED"


def test_a_planted_commit_lands_in_the_sandbox_repo_at_its_tick(tmp_path):
    box = tiny_sandbox(tmp_path, run_id="commit")
    manifest = {"faults": [{"kind": "commit", "tick": 2, "path": None}]}
    assert supervisor.commit_tick(box, manifest, 1) == []
    assert len(supervisor.commit_tick(box, manifest, 2)) == 1


def test_the_loop_ends_on_the_word_its_pre_tick_hook_returns(tmp_path):
    ap = fake_autopilot(["RUNNING"] * 5)
    words = iter([None, None, "BOUNDED"])
    out = supervisor.loop(ap, tmp_path, "9999", 2, deps_stub(), expected=5, every=0, wall_s=60,
                          before=lambda run: next(words))
    assert out["terminal"] == "BOUNDED" and out["ticks"] == 3 and len(out["states"]) == 2


def test_a_refused_rehearsal_writes_its_blocked_row_and_never_raises(tmp_path, monkeypatch):
    def refuse():
        from studio.rehearsal import activate
        raise activate.RehearsalRefused("the real Task Scheduler entry visurena-autopilot is enabled")
    monkeypatch.setattr(rehearse, "refuse_if_live", refuse)
    monkeypatch.setattr(rehearse, "missing_packages", lambda sid: [])
    out = rehearse.run_scenario("F1", results=tmp_path / "results")
    doc = json.loads((tmp_path / "results" / "F1.json").read_text(encoding="utf-8"))
    assert out["blocked"] and doc["rows"][0]["passed"] is False and "refused" in doc["rows"][0]["instrument_state"]


def test_a_fault_scenario_restores_from_the_newest_s0a_sandbox_holding_its_checkpoint(tmp_path):
    old, new = tmp_path / "ckpt_ep01_aaa", tmp_path / "ckpt_ep01_bbb"
    (old / "checkpoints" / "after_08").mkdir(parents=True)
    (new / "checkpoints" / "after_05").mkdir(parents=True)
    os.utime(old, (1, 1))
    assert rehearse.checkpoint_box(1, "after_08", base=tmp_path) == old
    assert rehearse.checkpoint_box(1, "after_05", base=tmp_path) == new
    assert rehearse.checkpoint_box(1, "after_12", base=tmp_path) is None


def test_every_evidence_path_is_made_absolute_under_the_sandbox(tmp_path):
    book = tmp_path / "library" / "b"
    rows = rehearse.anchored([{"evidence": ["tripwire.jsonl", "autopilot/status.json", str(tmp_path / "abs.json")]}],
                             tmp_path, book)
    assert rows[0]["evidence"] == [str(tmp_path / "tripwire.jsonl"), str(book / "autopilot" / "status.json"),
                                   str(tmp_path / "abs.json")]
