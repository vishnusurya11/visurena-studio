"""P13 (Jekyll Kawajiri ep01 retro): no false brain parks, a log per launch,
runtime-only dirty.  Every outward call is a fake; nothing spends."""
from __future__ import annotations

import json
from dataclasses import replace

import pytest

from studio import autopilot as ap
from studio import episode_drive
from studio.autopilot import Signals, State
from tests import autopilot_cli_fixtures as fx
from tests.test_autopilot_derives_state_from_disk import SHA, rows, signals

NEW = "b" * 40
REFUSED = "ep01: REFUSED: qc FAIL in 12 for these exact bytes"


def failed(**kw) -> Signals:
    """A drive that ended 1 on a log the table sends to the brain."""
    base = signals(drive_rows=rows(("start",), ("run", "failed"), ("end", 1)), log_tail=REFUSED,
                   failed_sha=SHA)
    return replace(base, **kw)


# ---- runtime-only dirty ----------------------------------------------------------

@pytest.mark.parametrize("mark", [" M", "??"])
@pytest.mark.parametrize("path", ["tests/test_x.py", "docs/audit/x.md", "architecture/index.html", "library/b/x.json",
                                  "logs/a.log", "README.md", "studio/notes.md", ".claude/skills/episode/SKILL.md"])
def test_dirty_ignores_tests_docs_skills_architecture_and_md(mark, path):
    assert episode_drive.dirty(f"{mark} {path}\n") is False


@pytest.mark.parametrize("mark", [" M", "??"])
@pytest.mark.parametrize("path", ["studio/comfy.py", "studio/stages.yaml", "studio/gates.yaml", "studio/models.py",
                                  "scripts/episode/drive.py", "episode.py"])
def test_dirty_still_holds_on_studio_stages_gates_models_and_root_scripts(mark, path):
    assert episode_drive.dirty(f"{mark} {path}\n") is (not path.endswith(".md"))


# ---- a dirty tree / a moved head never reach the brain -----------------------------

def test_a_dirty_tree_never_asks_the_brain():
    got = ap.derive(failed(porcelain=" M studio/comfy.py\n"), 1)
    assert got.state is State.WAIT_TREE and got.reason == "tree_dirty"


def test_the_code_dirty_signal_alone_holds_the_brain():
    assert ap.derive(failed(code_dirty=True), 1).state is State.WAIT_TREE


def test_a_failure_on_an_older_commit_relaunches_once_without_the_brain():
    got = ap.derive(failed(head_sha=NEW), 1)
    assert got.state is State.IDLE and got.reason == "head_moved"


def test_a_failure_at_this_head_on_a_clean_tree_keeps_todays_path():
    assert ap.derive(failed(), 1).state is State.NEEDS_BRAIN


def test_a_stale_park_verdict_on_a_dirty_tree_is_not_a_brain_turn():
    s = failed(brain_verdict={"verdict": "park"}, porcelain=" M studio/a.py")
    assert ap.derive(s, 1).state is State.WAIT_TREE


def test_exhausted_brain_attempts_do_not_park_a_dirty_tree():
    s = failed(brain_attempts=3, porcelain=" M studio/a.py")
    assert ap.derive(s, 1).state is State.WAIT_TREE


def test_failed_sha_is_the_last_sha_the_ledger_names():
    assert ap.failed_sha(rows(("start",), ("run", "failed"))) == SHA
    assert ap.failed_sha([]) is None


# ---- judge_verdict ---------------------------------------------------------------

def _judge(tmp_path, porcelain="", head="abc123def\n", failed_sha=None, verdict="park"):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path)
    d.git = lambda *a: porcelain if a[0] == "status" else head
    out = cli.judge_verdict(book, fx.CODEX, 1, {"verdict": verdict, "why": "w"}, d, failed_sha=failed_sha)
    return out, cli.rows_of(book / "autopilot" / "parked.jsonl"), d


def test_a_park_verdict_on_a_dirty_tree_or_a_moved_head_is_rejected(tmp_path):
    out, parked, _ = _judge(tmp_path, porcelain=" M studio/comfy.py\n")
    assert out["action"] == "brain_rejected" and parked == []
    out, parked, _ = _judge(tmp_path, failed_sha="0" * 40)
    assert out["action"] == "brain_rejected" and parked == []


def test_a_park_verdict_on_a_clean_tree_at_the_same_head_parks(tmp_path):
    out, parked, _ = _judge(tmp_path, failed_sha="abc123def")
    assert out["action"] == "park" and len(parked) == 1


def test_a_park_with_no_failed_sha_on_a_clean_tree_parks(tmp_path):
    assert _judge(tmp_path)[0]["action"] == "park"


# ---- the supervisor: wait_tree, step_guard, the brief --------------------------------

def _events(cli, book):
    return cli.rows_of(book / "autopilot" / "events.jsonl")


def test_tree_told_counts_from_this_wait_not_an_old_one(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    clock = [1_000_000.0]
    d = fx.deps(tmp_path, "WAIT_TREE", now=lambda: clock[0])
    cli.tick(book, fx.CODEX, d, 1)                        # wait opens
    d.derive = lambda s, n: fx.derived("IDLE", "launch")
    clock[0] += 100 * 3600
    cli.tick(book, fx.CODEX, d, 2)                        # the tree cleared: the wait closes
    d.derive = lambda s, n: fx.derived("WAIT_TREE", "tree_dirty")
    clock[0] += 3600
    cli.tick(book, fx.CODEX, d, 3)                        # a NEW wait, one hour old at most
    cli.tick(book, fx.CODEX, d, 4)
    assert d.calls["notify"] == []
    assert [r["event"] for r in _events(cli, book) if r["event"].startswith(("wait", "tree"))] \
        == ["wait_tree", "tree_clear", "wait_tree"]


def test_wait_tree_exit_row_carries_the_seconds_waited(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    clock = [1_000_000.0]
    d = fx.deps(tmp_path, "WAIT_TREE", now=lambda: clock[0])
    cli.tick(book, fx.CODEX, d, 1)
    d.derive = lambda s, n: fx.derived("IDLE", "launch")
    clock[0] += 900
    cli.tick(book, fx.CODEX, d, 2)
    clear = [r for r in _events(cli, book) if r["event"] == "tree_clear"][0]
    assert clear["waited_s"] == 900


def test_a_boundary_resume_is_not_a_relaunch_against_the_step_cap(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    home = book / "episodes" / "ep01"
    home.mkdir(parents=True)
    d = fx.deps(tmp_path)
    for _ in range(9):
        assert cli.step_guard(book, 1, "step 09 ok", d, why="boundary_resume") is None
    assert cli.step_guard(book, 1, "step 09 ok", d, why="head_moved") is None


def test_a_plain_relaunch_is_still_counted_by_the_step_guard(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    (book / "episodes" / "ep01").mkdir(parents=True)
    d = fx.deps(tmp_path)
    got = [cli.step_guard(book, 1, "step 09 ok", d, why="relaunch") for _ in range(12)]
    assert "step_cap" in got


def test_a_second_launch_keeps_the_first_launchs_log_and_the_newest_sorts_last(tmp_path):
    from scripts.episode import drive
    (tmp_path / "drive_run01.log").write_text("first", encoding="utf-8")
    (tmp_path / "drive_run02.log").write_text("second", encoding="utf-8")
    n = drive.first_log_number(tmp_path)
    assert n == 3
    (tmp_path / f"drive_run{n:02d}.log").write_text("third", encoding="utf-8")
    assert sorted(tmp_path.glob("drive_run*.log"))[-1].read_text(encoding="utf-8") == "third"
    assert (tmp_path / "drive_run01.log").read_text(encoding="utf-8") == "first"


def test_the_brain_brief_carries_the_log_tail_and_the_refusal_lines(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    home = book / "episodes" / "ep01"
    home.mkdir(parents=True)
    lines = [f"noise {i}" for i in range(60)] + ["G-DEAD refused T01", "CAP 2/2 step 09", "tail end"]
    (home / "drive_run01.log").write_text("\n".join(lines), encoding="utf-8")
    pk = cli.packet_extras(home, 20)
    assert pk["log_tail"].splitlines()[-1] == "tail end" and len(pk["log_tail"].splitlines()) == 40
    assert pk["refusals"] == ["G-DEAD refused T01", "CAP 2/2 step 09"]


def test_the_refusals_are_the_last_twelve_matching_lines(tmp_path):
    cli = fx.load()
    (tmp_path / "drive_run01.log").write_text("\n".join(f"REFUSED {i}" for i in range(30)), encoding="utf-8")
    assert cli.packet_extras(tmp_path, 20)["refusals"][0] == "REFUSED 18"


def test_brain_prompt_names_failed_sha_head_and_the_log(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    seen = {}

    class Core:
        @staticmethod
        def brief(home, tail, faults, learnings, spent, orders):
            seen["tail"] = tail
            return tail
    packet = {"reason": "r", "last_line": "L", "failed_sha": "aaaa1111", "head": "bbbb2222",
              "log_tail": "x\ny", "refusals": ["REFUSED z"], "commits_since": ["bbbb2222 fix"]}
    cli.brain_prompt(Core, book, 1, packet)
    for word in ("aaaa1111", "bbbb2222", "REFUSED z", "bbbb2222 fix", "x"):
        assert word in seen["tail"]


def test_the_run_row_carries_the_step_the_run_stopped_in():
    from scripts.episode import drive
    log = "STEP 08 start 10:00\nstuff\nSTEP 09 start 10:30\nREFUSED: qc FAIL\n"
    row = drive.run_row(3, "sha", log)
    assert row["step"] == "09" and row["outcome"] == "refused"
    assert "step" not in drive.run_row(1, "sha", "no steps here")
