"""The default suite's one rehearsal (2026-10-21_ep02_proof DESIGN 3): one checkpoint and one fault,
under 60 s, through the REAL autopilot tick in a fenced child process.

The sandbox is built from tests/fixtures only (no HDD read): a one-take ep02 at `after_12` whose
last drive stopped at G-STANDING, and the supervisor's heartbeat torn mid-write (F18 on the
supervisor's own record).  At this checkpoint the tick launches NO drive and submits NO take: what
it pins is the real tick reading the torn record, rebuilding it and ending HELD_PUBLISH named, with
no traceback, nothing reaching outside the sandbox, and a recovery trace on disk.  Like every
rehearsal it is REFUSED while the real Task Scheduler entry is enabled (DESIGN's hard rule, asked by
the harness itself), and then it skips with that reason.
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


def test_one_checkpoint_one_fault_through_the_real_tick_ends_named_under_a_minute(tmp_path):
    began = time.monotonic()
    box = tiny_sandbox(tmp_path, run_id="smoke")
    out = rehearse.run_scenario("smoke", results=tmp_path / "results", box=box)
    if rehearse.skippable(out):
        pytest.skip(f"refused, as DESIGN's hard rule says, even on a fixture sandbox: {out['blocked']}")
    doc = json.loads((tmp_path / "results" / "smoke.json").read_text(encoding="utf-8"))
    rows = {r["check"]: r for r in doc["rows"]}
    assert out["supervisor"]["terminal"] == "HELD_PUBLISH", out
    assert out["supervisor"]["tick_errors"] == 0
    failed = {k: r["detail"] for k, r in rows.items() if not r["passed"]}
    assert not failed, failed
    assert {"A-caps", "A-noupload", "A-named", "A-real", "A-torn", "A-ledger", "A-served", "smoke"} <= set(rows)
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


def live_library(tmp_path: Path, autopilot_pid: int) -> Path:
    """A stand-in library whose records name the live autopilot loop the way the real one writes them."""
    lib = tmp_path / "library"
    (lib / ".autopilot").mkdir(parents=True)
    (lib / ".device").mkdir()
    (lib / "2026_book" / "autopilot").mkdir(parents=True)
    (lib / ".autopilot" / "supervisor.lock").write_text(json.dumps({"pid": autopilot_pid}))
    (lib / ".autopilot" / "heartbeat.json").write_text(json.dumps({"ts": 1.0, "tick": 3}))
    (lib / ".autopilot" / "gpu.lock").write_text(json.dumps({"drive_pid": autopilot_pid}))
    (lib / "2026_book" / "autopilot" / "status.json").write_text(json.dumps({"supervisor_pid": autopilot_pid}))
    (lib / "2026_book" / "autopilot" / "events.jsonl").write_text("{}\n")
    (lib / ".device" / "gpu_util.jsonl").write_text(json.dumps({"ts": time.time()}) + "\n")
    return lib


def guard_moved(monkeypatch, paths: list[Path]) -> None:
    monkeypatch.setattr(rehearse.guard, "snapshot", lambda p: {})
    monkeypatch.setattr(rehearse.guard, "named_paths", lambda: [])
    monkeypatch.setattr(rehearse.guard, "touched", lambda a, b: [f"REAL LIBRARY TOUCHED: {p}" for p in paths])


def test_the_guard_excuses_a_path_only_when_its_content_names_the_live_writer(tmp_path, monkeypatch):
    lib = live_library(tmp_path, autopilot_pid=56132)
    book = lib / "2026_book" / "autopilot"
    mine = [lib / ".device" / "gpu_util.jsonl", lib / ".autopilot", lib / ".autopilot" / "heartbeat.json",
            lib / ".autopilot" / "supervisor.lock", book, book / "status.json", book / "events.jsonl"]
    guard_moved(monkeypatch, mine)
    r = rehearse.guard_row({}, writers=lambda: {"gpu_ledger.py": 4242, "autopilot.py": 56132}, since=time.time() - 60)
    assert r["passed"] is True, r["detail"]
    assert "gpu_ledger.py pid 4242" in r["detail"] and "autopilot.py pid 56132" in r["detail"]
    assert rehearse.guard_row({}, writers=lambda: {"gpu_ledger.py": 4242, "autopilot.py": 777})["passed"] is False


@pytest.mark.parametrize("rel", [".autopilot/gpu.lock", "2026_book/autopilot/parked.jsonl", "2026_book/episodes/ep02"])
def test_the_guard_never_excuses_a_path_the_live_writer_does_not_sign(tmp_path, monkeypatch, rel):
    lib = live_library(tmp_path, autopilot_pid=56132)
    guard_moved(monkeypatch, [lib / rel])
    assert rehearse.guard_row({}, writers=lambda: {"gpu_ledger.py": 4242, "autopilot.py": 56132})["passed"] is False


def test_the_gpu_ledger_is_excused_only_for_rows_it_wrote_since_the_snapshot(tmp_path, monkeypatch):
    lib = live_library(tmp_path, autopilot_pid=1)
    guard_moved(monkeypatch, [lib / ".device" / "gpu_util.jsonl"])
    assert rehearse.guard_row({}, writers=lambda: {"gpu_ledger.py": 4242}, since=time.time() + 60)["passed"] is False


def test_a_live_writer_inside_the_rehearsal_tree_is_never_excused():
    rows = [ProcInfo(os.getpid(), None, "python scripts/episode/gpu_ledger.py"), ProcInfo(999999, None, "python gpu_ledger.py")]
    assert rehearse.live_writers(table=lambda: rows) == {"gpu_ledger.py": 999999}


# ---- boundaries: the checkpoint maker, a bounded run, a commit mid-run -----------------------

def home_with_log(tmp_path: Path, text: str) -> Path:
    home = tmp_path / "library" / "b" / "episodes" / "ep01"
    home.mkdir(parents=True)
    (home / "drive_run01.log").write_text(text, encoding="utf-8")
    return home


def test_the_last_run_names_the_highest_step_it_started(tmp_path):
    home = home_with_log(tmp_path, "--- step 08 (panels) | x ---\nPAUSED AT BOUNDARY | ep01 | before step 09\n")
    assert supervisor.latest_step(home) == 8
    (home / "drive_run02.log").write_text("--- step 09 (shoot) | x ---\nPAUSED AT BOUNDARY | ep01 | G-TAKE before rung r2 #2\n")
    assert supervisor.latest_step(home) == 9 and not supervisor.BEFORE_STEP.search(supervisor.last_log(home))


@pytest.fixture
def shimmed(tmp_path):
    """studio.step_runner with S0a's between-steps stop installed for after_08, undone after."""
    from studio import step_runner
    from studio.rehearsal import checkpoint_stop
    box = tmp_path / "box"
    (box / "checkpoints").mkdir(parents=True)
    undo = checkpoint_stop.shim(step_runner, box, ("after_08",))
    yield box
    undo()


def test_the_real_runner_stops_in_front_of_a_due_checkpoint_and_only_between_steps(tmp_path, shimmed, capsys):
    from studio import boundary, step_runner
    from studio.rehearsal import checkpoint_stop
    from tests.proof_runner_fixture import run_real_steps, step
    home, ran = tmp_path / "home", []
    home.mkdir()

    def mid_step(ctx):                                  # a take's or a rung's own check never sees the stop
        ran.append(("08", step_runner.boundary.requested(home), boundary.requested(home)))
    out = run_real_steps([step("07", done=True), step("08", mid_step), step("09", lambda ctx: ran.append("09"))], home)
    assert out == boundary.OUTCOME and out.step == "09" and ran == [("08", False, False)]
    assert supervisor.BEFORE_STEP.search(capsys.readouterr().out).group(1) == "09"
    assert checkpoint_stop.pending(shimmed) == "after_08" and not (home / boundary.FLAG).exists()


def test_a_rehearsal_child_asking_for_checkpoints_gets_the_stop_when_the_runner_loads(tmp_path):
    import subprocess
    import sys
    box = tmp_path / "box"
    (box / "checkpoints").mkdir(parents=True)
    code = ("import sys; sys.path.insert(0, {repo!r}); from studio.rehearsal import trace; "
            "trace.install({{'trace': False, 'checkpoints': ['after_08']}}, box={box!r}); "
            "from tests.proof_runner_fixture import run_real_steps, step; "
            "print('OUTCOME', run_real_steps([step('08', done=True), step('09')], {home!r}))")
    done = subprocess.run([sys.executable, "-c", code.format(repo=str(rehearse.settings.REPO), box=str(box), home=str(tmp_path))],
                          capture_output=True, text=True, timeout=60, cwd=rehearse.settings.REPO)
    assert "OUTCOME paused_at_boundary" in done.stdout, done.stdout + done.stderr
    assert "before step 09" in done.stdout and (box / "checkpoint.pending").is_file()


def test_a_relaunch_past_a_made_checkpoint_runs_on(tmp_path, shimmed):
    from tests.proof_runner_fixture import run_real_steps, step
    (shimmed / "checkpoints" / "after_08").mkdir()
    ran: list = []
    assert run_real_steps([step("08", done=True), step("09", lambda ctx: ran.append("09"))], tmp_path) == "completed"
    assert ran == ["09"]


def test_the_checkpoint_maker_copies_a_pending_checkpoint_once_the_drive_is_down(tmp_path):
    from studio.rehearsal import checkpoint_stop
    box = tiny_sandbox(tmp_path, run_id="cp")
    checkpoint_stop.mark(box, "after_08")
    state = {"made": []}
    supervisor.checkpoint_tick(box, alive=True, state=state)
    assert state["made"] == []                             # never while the drive still runs
    supervisor.checkpoint_tick(box, alive=False, state=state)
    supervisor.checkpoint_tick(box, alive=False, state=state)
    assert state["made"] == ["after_08"] and (box / "checkpoints" / "after_08" / "library").is_dir()
    assert checkpoint_stop.pending(box) is None


def test_a_relaunch_copies_a_pending_checkpoint_first_without_its_own_open_launch_log(tmp_path):
    from studio.rehearsal import checkpoint_stop
    box = tiny_sandbox(tmp_path, run_id="relaunch")
    home = box / "library" / "b" / "episodes" / "ep01"
    home.mkdir(parents=True)
    (home / "drive_launch01.log").write_text("ran\n")
    (home / "drive_launch02.log").write_text("")           # the autopilot opened it just before drive_argv
    checkpoint_stop.mark(box, "after_08")
    argv = supervisor.drive_argv_for("r1", box)("9999", 1)
    copied = box / "checkpoints" / "after_08" / "library" / "b" / "episodes" / "ep01"
    assert argv[-1] == "--rehearsal=r1" and checkpoint_stop.pending(box) is None
    assert (copied / "drive_launch01.log").is_file() and not (copied / "drive_launch02.log").exists()


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
    manifest = {"harness_faults": [{"kind": "commit", "tick": 2, "path": None}]}
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


def test_a_fixture_scenario_is_refused_too_while_the_real_scheduler_entry_is_enabled(tmp_path, monkeypatch):
    def refuse():
        from studio.rehearsal import activate
        raise activate.RehearsalRefused("the real Task Scheduler entry visurena-autopilot is enabled")
    monkeypatch.setattr(rehearse, "refuse_if_live", refuse)
    box = tiny_sandbox(tmp_path, run_id="refused")
    out = rehearse.run_scenario("smoke", results=tmp_path / "results", box=box)
    assert out["blocked"] and rehearse.skippable(out) and not (box / "supervisor.json").exists()


def test_a_row_whose_instrument_failed_never_fails_the_point_and_is_listed():
    good, hole = asserts.row("A-real", True, []), asserts.a_canned([{"class": "canned", "prompt_id": "c"}], [])
    sup = {"terminal": "HELD_PUBLISH", "tick_errors": 0}
    assert rehearse.point_passed(sup, [good, hole]) == (True, ["A-canned"])
    assert rehearse.point_passed(sup, [asserts.row("A-real", False, []), hole]) == (False, ["A-canned"])
    assert rehearse.point_passed({"terminal": None}, [good]) == (False, [])


def test_a_cut_is_the_kill_moment_or_any_drive_end_of_this_run(tmp_path):
    home = tmp_path / "library" / "b" / "episodes" / "ep01"
    home.mkdir(parents=True)
    (tmp_path / "kill.done").write_text(json.dumps({"ts": 1792600000.0, "pid": 7}))
    rows = [{"event": "start", "ts": "2026-10-21T10:00:00+00:00"}, {"event": "end", "ts": "2026-10-21T10:05:00+00:00", "code": 0},
            {"event": "end", "ts": "2026-10-21T10:09:00+00:00", "code": 137}]
    (home / "drive.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    ends = [asserts.epoch("2026-10-21T10:05:00+00:00"), asserts.epoch("2026-10-21T10:09:00+00:00")]
    assert rehearse.deaths(tmp_path, home, since=0.0) == sorted([1792600000.0, *ends])
    assert rehearse.deaths(tmp_path, home, since=ends[0] + 1) == sorted([1792600000.0, ends[1]])


def test_a_sweep_whose_replayed_point_traces_differently_is_an_instrument_failure():
    sc = rehearse.TABLE["F10"]
    results = [{"id": "F10:k=1", "passed": True, "trace": "aaa"}, {"id": "F10:k=2", "passed": True, "trace": "bbb"}]
    same = rehearse.summary_row(sc, results, 2, stability=[{"point": "F10:k=1", "same": True}])
    assert same["passed"] is True and "stable 1/1" in same["instrument_state"]
    moved = rehearse.summary_row(sc, results, 2, stability=[{"point": "F10:k=1", "same": False}])
    assert asserts.instrument_failed(moved) and "unstable" in moved["detail"]
    never = rehearse.summary_row(sc, results, 2, stability=[])
    assert never["passed"] is False and "no replay" in never["detail"]


def test_the_stability_check_replays_one_point_and_compares_its_signature():
    first = {"id": "F10:k=1", "trace": "aaa", "trace_lines": [["studio/comfy.py", 3]]}
    again = {"id": "F10:k=1", "trace": "aaa", "trace_lines": [["studio/comfy.py", 3]]}
    assert sweep_stability(first, again) == {"point": "F10:k=1", "same": True, "signatures": ["aaa", "aaa"], "only": []}
    again = {"id": "F10:k=1", "trace": "ccc", "trace_lines": [["studio/comfy.py", 3], ["scripts/episode/drive.py", 40]]}
    got = sweep_stability(first, again)
    assert got["same"] is False and got["only"] == [["scripts/episode/drive.py", 40]]


def sweep_stability(first, again):
    from studio.rehearsal import sweep
    return sweep.stability(first, again)


def test_every_evidence_path_is_made_absolute_under_the_sandbox(tmp_path):
    book = tmp_path / "library" / "b"
    rows = rehearse.anchored([{"evidence": ["tripwire.jsonl", "autopilot/status.json", str(tmp_path / "abs.json")]}],
                             tmp_path, book)
    assert rows[0]["evidence"] == [str(tmp_path / "tripwire.jsonl"), str(book / "autopilot" / "status.json"),
                                   str(tmp_path / "abs.json")]
