"""C3_verdict #3 (T0, D1): the honest clock times the PROCESS, not the step.

`episode_clock.timed` stamps its timing.jsonl row in a `finally`, and a
Windows Stop-Process runs no finally: 398 of 3,499 machine-minutes over WotW
ep19-27 sat in killed steps the clock never saw.  Now every episode run opens
a row in clock.jsonl, a daemon thread beats clock.open.json every 60 s, a
clean exit closes the row, and the next run closes an orphan as `killed` at
its last beat.  What the ceiling is charged with is the UNION of the run
spans (overlaps counted once), plus the legacy timing rows from before the
first run row."""
from __future__ import annotations

import json
import time

from studio import run_budget, run_clock


class FakeClock:
    def __init__(self, t: float = 1_000_000.0):
        self.t = t

    def __call__(self) -> float:
        return self.t


def test_a_clean_run_is_one_closed_row(tmp_path):
    now = FakeClock()
    run_clock.open_run(tmp_path, "r1", now=now)
    now.t += 600
    run_clock.close_run(tmp_path, now=now)
    rows = run_clock.rows(tmp_path)
    assert [(r["run_id"], r["how"], r["seconds"]) for r in rows] == [("r1", "closed", 600.0)]
    assert not (tmp_path / run_clock.OPEN).exists()
    assert run_clock.spent(tmp_path) == 600.0


def test_a_killed_run_counts_to_its_last_beat(tmp_path):
    now = FakeClock()
    run_clock.open_run(tmp_path, "r1", now=now)
    for _ in range(3):
        now.t += run_clock.BEAT_S
        run_clock.beat(tmp_path, "r1", now=now)
    now.t += 45                                   # killed 45 s after the last beat: no finally ran
    assert run_clock.spent(tmp_path) == 3 * run_clock.BEAT_S
    now.t += 3600                                 # the next launch, an hour later
    run_clock.open_run(tmp_path, "r2", now=now)
    killed = run_clock.rows(tmp_path)[0]
    assert (killed["run_id"], killed["how"], killed["seconds"]) == ("r1", "killed", 180.0)


def test_overlapping_and_nested_spans_count_once():
    assert run_clock.union([(0, 100), (50, 150), (60, 70), (200, 260)]) == 210.0
    assert run_clock.union([]) == 0.0


def test_overlapping_runs_on_disk_count_once(tmp_path):
    rows = [{"run_id": "a", "started": 0.0, "ended": 1000.0, "how": "closed"},
            {"run_id": "b", "started": 400.0, "ended": 1500.0, "how": "killed"}]
    (tmp_path / run_clock.CLOCK).write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    assert run_clock.spent(tmp_path) == 1500.0


def test_legacy_timing_rows_count_until_the_first_run_row(tmp_path):
    timing = [{"stage": "plan", "seconds": 300.0, "ended": "2026-10-01T10:00:00"},
              {"stage": "takes", "seconds": 999.0, "ended": "2026-10-11T12:00:00"}]
    (tmp_path / "timing.jsonl").write_text("".join(json.dumps(r) + "\n" for r in timing), encoding="utf-8")
    from datetime import datetime
    first = datetime.fromisoformat("2026-10-11T11:00:00").timestamp()
    now = FakeClock(first)
    run_clock.open_run(tmp_path, "r1", now=now)
    now.t += 1200
    run_clock.close_run(tmp_path, now=now)
    assert run_clock.spent(tmp_path) == 300.0 + 1200.0      # the 12:00 row lies inside the run span


def test_a_home_with_no_run_rows_reads_its_timing_rows(tmp_path):
    (tmp_path / "timing.jsonl").write_text(json.dumps({"seconds": 250.5}) + "\n", encoding="utf-8")
    assert run_clock.spent(tmp_path) == 250.5
    assert run_clock.spent(tmp_path / "nowhere") == 0.0


def test_the_budget_is_charged_with_the_run_clock(tmp_path):
    now = FakeClock()
    run_clock.open_run(tmp_path, "r1", now=now)
    now.t += 4000
    run_clock.beat(tmp_path, "r1", now=now)
    assert run_budget.spent_before(tmp_path) == 4000.0


def test_the_heartbeat_thread_beats_and_closes(tmp_path):
    with run_clock.running(tmp_path, "r1", every=0.05):
        time.sleep(0.3)
        live = json.loads((tmp_path / run_clock.OPEN).read_text(encoding="utf-8"))
        assert live["last_beat"] > live["started"]
    assert run_clock.rows(tmp_path)[-1]["how"] == "closed"
    assert not (tmp_path / run_clock.OPEN).exists()


def test_spans_before_a_moment_are_the_earlier_runs(tmp_path):
    now = FakeClock()
    run_clock.open_run(tmp_path, "r1", now=now)
    now.t += 100
    run_clock.close_run(tmp_path, now=now)
    t0 = now.t + 50
    assert run_clock.spent_before(tmp_path, t0) == 100.0
    assert run_clock.spent_before(tmp_path, now.t - 200) == 0.0


def test_an_episode_run_is_one_clock_row(tmp_path, monkeypatch):
    import episode
    from studio import step_runner
    from tests.test_episode_runner import CODEX, _opts, book, conn  # noqa: F401
    from studio import db, episode_home
    monkeypatch.setattr(episode_home, "book_dir", lambda codex_id: tmp_path / "book")
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "Book", codex_id=CODEX)
    for step in step_runner.load_steps("episode"):
        monkeypatch.setattr(step, "done", lambda ctx: True)
    assert episode.main([CODEX, "1"], conn=connection, tools=(), **_opts(tmp_path)) == 0
    home = episode_home.home(tmp_path / "book", 1)
    assert [r["how"] for r in run_clock.rows(home)] == ["closed"]
    assert not (home / run_clock.OPEN).exists()


def test_the_progress_view_reads_the_run_clock(tmp_path):
    from studio.command_center import progress_view
    now = FakeClock()
    run_clock.open_run(tmp_path, "r1", now=now)
    now.t += 700
    run_clock.beat(tmp_path, "r1", now=now)          # killed: no timing row was ever written
    assert progress_view.work_before(tmp_path, now.t + 3600) == 700.0
