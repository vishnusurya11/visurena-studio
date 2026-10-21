"""The fault injectors F1-F18 (2026-10-21_ep02_proof DESIGN 3.2) and the fault scenarios.

The injectors run in the default suite: each plants exactly its fault in a sandbox (a manifest row
for the fake engine or the fakes, a kill at write k in a child, a dropped supervisor with a stale
gpu.lock, a commit in <sandbox>/git, a planted precondition gap, a torn record).  The scenarios
themselves run the real pipeline and are marked `rehearsal` (excluded by default)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from studio import settings
from studio.rehearsal import faults
from tests.proof_sandbox_fixture import tiny_sandbox


@pytest.fixture
def box(tmp_path):
    return tiny_sandbox(tmp_path)


def manifest(box: Path) -> dict:
    return json.loads((box / "rehearsal.json").read_text(encoding="utf-8"))


def test_an_engine_fault_is_a_manifest_row_the_fake_engine_reads(box):
    faults.add(box, faults.engine("exec_error", 3, "ref2v_take"))
    faults.add(box, faults.engine("corrupt", 1, "ref2v_take", detail="no_audio"))
    rows = manifest(box)["faults"]
    assert rows[0] == {"kind": "exec_error", "on": "submit#3", "workflow": "ref2v_take"}
    assert rows[1]["detail"] == "no_audio"
    with pytest.raises(ValueError):
        faults.engine("meteor", 1)
    with pytest.raises(ValueError):
        faults.engine("corrupt", 1, detail="sideways")


def test_each_fakes_fault_lands_at_the_key_its_fake_reads(box):
    for row in (faults.worker_death("whisper", 4), faults.rate_limit(2), faults.brain_failed(1),
                faults.oauth_expired(), faults.brain_stream(["relaunch", "park"])):
        faults.add(box, row)
    doc = manifest(box)
    assert doc["faults"] == []                                   # P3's parser sees only its own kinds
    assert doc["worker_die_at"] == {"whisper": 4}                # P4 fake_workers
    assert doc["sdk_faults"] == [{"on": 2, "kind": "rate_limit"}, {"on": 1, "kind": "error"}]   # P4 fake_sdk
    assert doc["youtube"] == "invalid_grant"                     # P4 fake_publish
    assert doc["brain_stream"] == ["relaunch", "park"]           # brain_script


def test_the_harness_own_faults_never_reach_the_fake_engine(box):
    faults.add(box, faults.kill_at_write("k", "s", 1, "09"))
    faults.add(box, {"kind": "commit", "tick": 2, "path": None})
    doc = manifest(box)
    assert doc["faults"] == [] and [r["kind"] for r in doc["harness_faults"]] == ["kill_at_write", "commit"]
    assert faults.kill_rows(doc, step="09")[0]["site"] == "s"


def test_a_row_no_fake_reads_is_refused_not_dropped(box):
    with pytest.raises(ValueError, match="no fake reads"):
        faults.add(box, {"kind": "meteor"})


def test_a_point_starts_from_a_manifest_with_no_fault_of_any_kind(box):
    for row in (faults.worker_death("whisper", 4), faults.oauth_expired(), faults.engine("crash", 1)):
        faults.add(box, row)
    doc = {**manifest(box), **faults.CLEAN}
    assert not doc["faults"] and not doc["sdk_faults"] and not doc["worker_die_at"] and doc["youtube"] == "refuse"


def test_a_kill_at_write_k_stops_the_child_before_its_kth_write_and_asks_for_the_tree(tmp_path):
    box = tmp_path / "box"
    book = box / "library" / "b" / "episodes" / "ep02"
    book.mkdir(parents=True)
    row = faults.kill_at_write("episodes/ep##/x##.txt", "<string>:1", 2, None)
    code = ("import sys; sys.path.insert(0, {repo!r}); from studio.rehearsal import faults; "
            "faults.arm({{'harness_faults': [{row!r}]}}, {box!r}); "
            "[open({d!r} + '/x%02d.txt' % i, 'w').write('x') for i in range(5)]")
    done = subprocess.run([sys.executable, "-c", code.format(repo=str(settings.REPO), row=row, box=str(box), d=str(book))],
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == faults.KILLED, done.stderr
    assert sorted(p.name for p in book.iterdir()) == ["x00.txt"]          # the 2nd write never happened
    asked = faults.kill_requested(box)
    assert asked["fault"]["occurrence"] == 2 and asked["pid"] > 0


def test_a_kill_row_for_another_step_arms_nothing():
    assert faults.kill_rows({"harness_faults": [faults.kill_at_write("k", "s", 1, "10")]}, step="09") == []


def test_a_kill_for_step_09_fires_inside_the_episode_process_only_while_the_runner_is_in_09(tmp_path):
    box = tmp_path / "box"
    home = box / "library" / "b" / "episodes" / "ep02"
    home.mkdir(parents=True)
    row = faults.kill_at_write("episodes/ep##/x##.txt", "<string>:1", 1, "09")
    code = ("import sys; sys.path.insert(0, {repo!r}); from studio.rehearsal import faults; "
            "from tests.proof_runner_fixture import run_real_steps, step; "
            "w = lambda name: (lambda ctx: open({d!r} + '/' + name, 'w').write('x')); "
            "faults.arm({{'harness_faults': [{row!r}]}}, {box!r}); "
            "run_real_steps([step('08', w('x08.txt')), step('09', w('x09.txt')), step('10', w('x10.txt'))])")
    done = subprocess.run([sys.executable, "-c", code.format(repo=str(settings.REPO), row=row, box=str(box), d=str(home))],
                          capture_output=True, text=True, timeout=60, cwd=settings.REPO)
    assert done.returncode == faults.KILLED, done.stdout + done.stderr
    assert sorted(p.name for p in home.iterdir()) == ["x08.txt"]          # 08 wrote; 09 died before its write
    assert faults.kill_requested(box)["step"] == "09"


def test_the_drive_is_the_topmost_ancestor_below_the_supervisor():
    parents = {30: 20, 20: 10, 10: 1}                         # episode 30 <- drive 20 <- supervisor 10
    assert faults.drive_root(parents, 30, supervisor=10) == 20
    assert faults.drive_root(parents, 30, supervisor=None) == 30           # no supervisor named: only itself
    assert faults.drive_root({30: 30}, 30, supervisor=10) == 30            # a loop in the map ends the walk


def test_the_tree_kill_takes_the_drive_first_and_every_other_process_of_it_never_the_killer():
    killed: list = []
    parents = {30: 20, 31: 20, 32: 31, 20: 10, 40: 10}
    got = faults.kill_tree(30, 10, parents=lambda: parents, kill=killed.append)
    assert got == killed == [20, 31, 32]                                   # 40 is another child of the supervisor


@pytest.mark.skipif(sys.platform != "win32", reason="the parent map is Toolhelp32's")
def test_a_kill_at_write_kills_the_whole_drive_at_once_so_the_drive_never_handles_the_exit(tmp_path):
    box = tmp_path / "box"
    home = box / "library" / "b" / "episodes" / "ep02"
    home.mkdir(parents=True)
    mark = tmp_path / "drive_handled_the_exit.txt"
    row = faults.kill_at_write("episodes/ep##/x##.txt", "<string>:1", 1, None)
    child = ("import sys; sys.path.insert(0, {repo!r}); from studio.rehearsal import faults; "
             "faults.arm({{'harness_faults': [{row!r}]}}, {box!r}); open({d!r} + '/x01.txt', 'w').write('x')"
             ).format(repo=str(settings.REPO), row=row, box=str(box), d=str(home))
    drive = (f"import subprocess, sys, time; p = subprocess.Popen([sys.executable, '-c', {child!r}]); p.wait(); "
             f"time.sleep(3); open({str(mark)!r}, 'w').write(str(p.returncode))")
    env = {**os.environ, faults.SUPERVISOR_ENV: str(os.getpid())}
    done = subprocess.run([sys.executable, "-c", drive], capture_output=True, text=True, timeout=60, env=env)
    asked = faults.kill_requested(box)
    assert done.returncode != 0 and not mark.exists(), done.stdout + done.stderr
    assert asked["killed"] and asked["killed"][0] != asked["pid"]


def test_a_dropped_supervisor_leaves_a_stale_lock_and_an_old_heartbeat(box):
    pid = faults.dead_pid()
    faults.drop_supervisor(box, pid, episode=2, now=10_000.0)
    root = box / "library" / ".autopilot"
    assert json.loads((root / "gpu.lock").read_text())["drive_pid"] == pid
    assert json.loads((root / "heartbeat.json").read_text())["ts"] < 10_000.0 - 600


def test_a_sandbox_commit_moves_only_the_sandbox_head(box):
    before = subprocess.run(["git", "-C", str(box / "git"), "rev-parse", "HEAD"], capture_output=True, text=True).stdout
    sha = faults.sandbox_commit(box)
    guarded = faults.sandbox_commit(box, "scripts/episode/takes_r2v.py")
    log = subprocess.run(["git", "-C", str(box / "git"), "log", "--name-only", "--format=%H"], capture_output=True,
                         text=True).stdout
    assert sha != before.strip() and guarded != sha and "scripts/episode/takes_r2v.py" in log


def test_a_planted_gap_removes_exactly_the_named_record_or_field(tmp_path):
    book = tmp_path / "book"
    (book / "source").mkdir(parents=True)
    (book / "source" / "book.json").write_text(json.dumps({"series": "s", "display_title": "d", "title": "t"}))
    (book / "cast").mkdir()
    (book / "cast" / "voices.json").write_text(json.dumps({"poole": {"v": 1}, "utterson": {"v": 2}}))
    (book / "refs" / "places").mkdir(parents=True)
    (book / "refs" / "places" / "door.png").write_bytes(b"x")
    doc = {"gaps": [{"record": "source/book.json", "field": "series"}, {"record": "cast/voices.json", "key": "poole"},
                    {"path": "refs/places/door.png"}]}
    planted = faults.plant_all(book, doc)
    assert len(planted) == 3
    assert json.loads((book / "source" / "book.json").read_text()) == {"display_title": "d", "title": "t"}
    assert list(json.loads((book / "cast" / "voices.json").read_text())) == ["utterson"]
    assert not (book / "refs" / "places" / "door.png").exists()


def test_a_gap_that_names_a_record_the_book_lacks_is_reported_not_invented(tmp_path):
    assert faults.plant(tmp_path, {"path": "refs/none.png"}) == {"path": "refs/none.png", "planted": False, "present": True}
    assert faults.plant(tmp_path, {"kind": "unresolved_name", "what": "a servant"})["present"] is False


def test_a_preconditions_report_row_names_its_file_or_field(tmp_path):
    sheet = {"kind": "base_sheet", "what": "poole", "note": "refs.json names refs/characters/poole/sheet.png; the file is absent"}
    assert faults.gap_target(sheet) == {"path": "refs/characters/poole/sheet.png"}
    assert faults.gap_target({"kind": "place_picture", "what": "utterson_house/bedroom"}) ==         {"path": "refs/locations/utterson_house/bedroom.png"}
    assert faults.gap_target({"kind": "book_field", "what": "series"}) == {"record": "source/book.json", "field": "series"}


def test_a_torn_record_keeps_a_strict_prefix_of_its_bytes(tmp_path):
    rec = tmp_path / "attempts.json"
    rec.write_text(json.dumps({"wall.09": {"rounds": 3, "seconds": 7438.8}}))
    size = rec.stat().st_size
    kept = faults.tear(rec)
    assert 0 < kept < size and rec.read_bytes() == json.dumps({"wall.09": {"rounds": 3, "seconds": 7438.8}}).encode()[:kept]
    with pytest.raises(ValueError):
        json.loads(rec.read_text())


def test_a_record_kind_resolves_under_the_episode_or_the_book(tmp_path):
    book = tmp_path / "book"
    assert faults.record_path(book, 2, "attempts.json") == book / "episodes" / "ep02" / "attempts.json"
    assert faults.record_path(book, 2, "autopilot/status.json") == book / "autopilot" / "status.json"
    assert faults.record_path(tmp_path / "library" / "b", 2, ".autopilot/heartbeat.json") == \
        tmp_path / "library" / ".autopilot" / "heartbeat.json"


def test_the_token_note_fake_answers_from_the_manifest():
    assert faults.token_note({})() is None
    assert faults.token_note({"youtube": "refuse"})() is None
    assert "invalid_grant" in faults.token_note({"youtube": "invalid_grant"})()


# ---- the scenarios (the real pipeline; excluded by default) ----------------------------------

def fault_ids() -> list[str]:
    """Every fault scenario of the harness table: the list cannot drift from what rehearse.py runs."""
    from scripts.proof import rehearse
    return [k for k in rehearse.TABLE if k.startswith("F")]


def test_the_rehearsal_list_is_the_harness_table():
    assert {"F1", "F8", "F15", "F17"} <= set(fault_ids())


@pytest.mark.rehearsal
@pytest.mark.parametrize("scenario", fault_ids())
def test_a_fault_scenario_writes_its_counted_rows(scenario, tmp_path):
    from scripts.proof import rehearse
    out = rehearse.run_scenario(scenario, results=tmp_path / "results", wall=4 * 3600.0)
    if rehearse.skippable(out):
        pytest.skip(f"{scenario} did not run: {out['blocked']}")
    assert not out.get("blocked"), out                    # a checkpoint or prepare() failure is a FAILURE
    rows = json.loads((tmp_path / "results" / f"{scenario}.json").read_text())["rows"]
    assert rows and all(set(rehearse.ROW_KEYS) <= set(r) for r in rows)
    assert out["scenario"] == scenario
