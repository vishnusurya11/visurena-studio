"""The trailer stage runner — the blind path.

One command, one time ceiling, no questions.  It may only run on a book whose
screenplay COMPLETED, it runs the registry's steps in file order, and every
rung a step climbs is written to learnings.jsonl through the run context so
the retrospect has numbers instead of memory.
"""
from __future__ import annotations

import types

import pytest

import trailer
from studio import db
from studio.learnings import Learning, load
from studio.run_budget import TRAILER_SHARES, Budget
from studio.trailer_run import RunContext


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    return connection


def _book(conn, codex_id="20260901000001"):
    return db.insert_codex(conn, "Book", codex_id=codex_id)


def _finish_screenplay(conn, codex_id):
    db.add_event(conn, codex_id, "screenplay", "05", "completed")


def _ctx(conn, tmp_path):
    return RunContext(conn, _book(conn), tmp_path / "book", logs_root=tmp_path / "logs")


def _step(step_id, fn):
    return types.SimpleNamespace(STEP_ID=step_id, NAME="x", run=fn)


class TestReadiness:
    def test_needs_a_completed_screenplay(self, conn):
        codex_id = _book(conn)
        assert trailer.ready(conn) == []
        _finish_screenplay(conn, codex_id)
        assert trailer.ready(conn) == [codex_id]

    def test_a_finished_trailer_is_not_ready_again(self, conn):
        codex_id = _book(conn)
        _finish_screenplay(conn, codex_id)
        db.add_event(conn, codex_id, "trailer", trailer.FINAL_STEP_ID, "completed")
        assert trailer.ready(conn) == []

    def test_the_codex_table_knows_the_stage(self, conn):
        codex_id = _book(conn)
        db.mark_stage(conn, codex_id, "trailer", "running")
        assert db.get_codex(conn, codex_id)["trailer_status"] == "running"


class TestOlderDatabase:
    def test_main_migrates_a_database_made_before_the_stage_existed(self, tmp_path, monkeypatch):
        """The real library.db predates the trailer columns; the first real run died
        on `no such column: trailer_status`.  main() owns the migration."""
        monkeypatch.setattr(db, "STAGES", ("analysis", "screenplay"))
        connection = db.get_connection(tmp_path / "old.db")
        db.init_db(connection)
        codex_id = _book(connection)
        monkeypatch.setattr(db, "STAGES", ("analysis", "screenplay", "trailer"))
        monkeypatch.setattr(trailer.paths, "book_dir", lambda cid: tmp_path / "book")
        monkeypatch.setattr(trailer, "load_steps", lambda: [])
        trailer.main([codex_id], connection)
        assert db.get_codex(connection, codex_id)["trailer_status"] == "completed"


class TestRegistry:
    def test_ten_steps_in_order(self):
        ids = [s["id"] for s in trailer.load_registry()["steps"]]
        assert ids == [f"{n:02d}" for n in range(1, 11)]

    def test_final_step_is_the_last_registry_entry(self):
        assert trailer.load_registry()["steps"][-1]["id"] == trailer.FINAL_STEP_ID


class TestRunStep:
    def test_brackets_the_step_with_events(self, conn, tmp_path):
        ctx = _ctx(conn, tmp_path)
        trailer.run_step(ctx, _step("01", lambda codex_id, ctx: None))
        events = [r["event"] for r in conn.execute(
            "SELECT event FROM events WHERE stage='trailer' AND step_id='01' "
            "ORDER BY event_ts")]
        assert events == ["started", "completed"]

    def test_a_crash_is_recorded_and_re_raised(self, conn, tmp_path):
        ctx = _ctx(conn, tmp_path)

        def boom(codex_id, ctx):
            raise RuntimeError("ffmpeg died")
        with pytest.raises(RuntimeError):
            trailer.run_step(ctx, _step("08", boom))
        row = conn.execute("SELECT detail FROM events WHERE event='failed'").fetchone()
        assert "ffmpeg died" in row["detail"]

    def test_a_refusal_that_exits_is_a_failure_not_an_exit(self, conn, tmp_path):
        """assemble.py and build_plan.py still REFUSE with SystemExit, which is not
        an Exception: unconverted, it would skip the failed event and leave the
        stage marked running."""
        ctx = _ctx(conn, tmp_path)

        def refuse(codex_id, ctx):
            raise SystemExit("REFUSED: every shot is the same length")
        with pytest.raises(RuntimeError, match="same length"):
            trailer.run_step(ctx, _step("08", refuse))
        row = conn.execute("SELECT detail FROM events WHERE event='failed'").fetchone()
        assert "same length" in row["detail"]

    def test_the_budget_is_opened_for_the_step(self, conn, tmp_path):
        ctx = _ctx(conn, tmp_path)
        seen = {}
        trailer.run_step(ctx, _step("07", lambda c, ctx: seen.update(
            step=ctx.budget.step, left=ctx.budget.remaining("07"))))
        assert seen["step"] == "07" and seen["left"] > 200 * 60

    def test_the_banner_reads_the_budget_of_the_step_it_opens(self, conn, tmp_path, capsys):
        """Run 10 printed '-199 min left' for step 08: the banner was read
        while 07 was still the open step, so 07's five hours were charged
        against 08's ten minutes.  The gate inside the step was right; the
        number printed was not."""
        ctx = _ctx(conn, tmp_path)
        clock = [0.0]
        ctx.budget = Budget(6 * 3600, TRAILER_SHARES, clock=lambda: clock[0])
        trailer.run_step(ctx, _step("07", lambda c, ctx: clock.__setitem__(0, 200 * 60)))
        trailer.run_step(ctx, _step("08", lambda c, ctx: None))
        assert "--- step 08 (x) | 20 min left ---" in capsys.readouterr().out

    def test_degradations_are_summarised_on_the_completed_event(self, conn, tmp_path):
        ctx = _ctx(conn, tmp_path)

        def step(codex_id, ctx):
            ctx.learn(Learning(step="05", gate="similarity", action="card", terminal=True))
        trailer.run_step(ctx, _step("05", step))
        row = conn.execute("SELECT detail FROM events WHERE event='completed'").fetchone()
        assert "1 rung" in row["detail"]
        assert load(ctx.learnings_path)[0].action == "card"


class TestContext:
    def test_learnings_live_beside_the_trailer(self, conn, tmp_path):
        ctx = _ctx(conn, tmp_path)
        assert ctx.learnings_path == tmp_path / "book" / "trailer" / "main" / "learnings.jsonl"

    def test_learn_also_logs_a_warning_line(self, conn, tmp_path):
        ctx = _ctx(conn, tmp_path)
        ctx.learn(Learning(step="03", gate="slots", measured=0, threshold=1,
                           action="more_seeds"))
        assert '"WARNING"' in ctx.tracker.log_path.read_text(encoding="utf-8")
