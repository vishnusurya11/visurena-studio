"""Step 02 of the episode stage: brief -> write -> plan_check -> improve (at
most twice) -> lock -> the PLAN signature.

A fake writer and a fake capture stand in for the agent and the gate script;
nothing here calls a model, and `plan_check` is never launched.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from scripts.episode import step_02_plan as step
from studio import db, episode_home, plan_verdict
from studio.escalate import Escalation
from studio.episode_spec import Episode
from studio.stage_run import StageContext
from tests.test_episode_writer import canned_plan

REFUSED_OUT = "CONTRACT OK: The Yard | 24 shots | 140s projected\nPLAN GATES   : 1\n    G-SCALE shot 4: a close with no cell\n  advisory: L8 shot 2: 'walks' with no pace word\nVERDICT      : REFUSED\n"
CLEAN_OUT = "CONTRACT OK: The Yard | 24 shots | 140s projected\nVERDICT      : clean -- lines may render\n"


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    return connection


@pytest.fixture()
def ctx(conn, tmp_path, monkeypatch):
    codex_id = db.insert_codex(conn, "Book", codex_id="20260901000001")
    book = tmp_path / "book"
    context = StageContext(conn, codex_id, book, "episode", unit="ep03", number=3,
                           logs_root=tmp_path / "logs", busy=lambda: False,
                           hold=tmp_path / "RENDER_HOLD", launch=lambda cmd: 0)
    context.home = episode_home.home(book, 3)
    context.home.mkdir(parents=True)
    context.extra = []
    monkeypatch.setattr(step, "plan_brief", SimpleNamespace(build=lambda b, n, targets=None: {"number": n}))
    return context


class Writer:
    """A fake episode_writer: the canned plan every time; records the refusals it was given."""

    def __init__(self):
        self.calls = []

    def write(self, brief, refusals=None, usage=None):
        self.calls.append(refusals)
        return Episode.model_validate(canned_plan(brief["number"]))


class Capture:
    """A fake gate: hands out (rc, out) in order, then repeats the last."""

    def __init__(self, *results):
        self.results, self.commands = list(results), []

    def __call__(self, cmd):
        self.commands.append(cmd)
        return self.results.pop(0) if len(self.results) > 1 else self.results[0]


def _wire(ctx, monkeypatch, *gate_results):
    writer, gate = Writer(), Capture(*gate_results)
    monkeypatch.setattr(step, "episode_writer", writer)
    ctx.capture = gate
    return writer, gate


def _plan(ctx):
    return episode_home.plan_path(ctx.book_dir, ctx.number)


def _placed(ctx):
    return ctx.home / "placed.json"


# ---- the module's contract ----------------------------------------------------------

def test_the_step_declares_itself():
    assert (step.STEP_ID, step.NAME, step.GPU, step.MAX_IMPROVE) == ("02", "plan", False, 2)


def test_capture_script_builds_the_same_argv_as_run_script(ctx):
    ctx.capture = lambda cmd: (7, " ".join(cmd))
    rc, out = ctx.capture_script("scripts/episode/plan_check.py")
    assert rc == 7 and out.endswith("scripts/episode/plan_check.py 20260901000001 3")


# ---- done ----------------------------------------------------------------------------

def test_no_plan_is_not_done(ctx):
    assert step.done(ctx) is False


def test_a_plan_with_a_current_verdict_is_done(ctx):
    episode_home.write_plan(_plan(ctx), canned_plan())
    assert step.done(ctx) is False
    plan_verdict.sign(_plan(ctx), "read")
    assert step.done(ctx) is True


def test_a_plan_that_already_ran_downstream_is_grandfathered(ctx):
    """placed.json beside plan.json: the timeline was built from it, so it was judged
    before verdict files existed."""
    episode_home.write_plan(_plan(ctx), canned_plan())
    _placed(ctx).write_text("{}", encoding="utf-8")
    assert step.done(ctx) is True


def test_a_stale_verdict_is_not_done(ctx):
    episode_home.write_plan(_plan(ctx), canned_plan())
    plan_verdict.sign(_plan(ctx), "read")
    episode_home.write_plan(_plan(ctx), {**canned_plan(), "title": "Rewritten"})
    assert step.done(ctx) is False


# ---- run -----------------------------------------------------------------------------

def test_a_missing_plan_is_written_through_write_plan_then_the_plan_gate_parks(ctx, monkeypatch):
    writer, gate = _wire(ctx, monkeypatch, (0, CLEAN_OUT))
    written = []
    real = episode_home.write_plan
    monkeypatch.setattr(step.episode_home, "write_plan", lambda out, doc: written.append(out) or real(out, doc))
    with pytest.raises(Escalation) as parked:
        step.run(ctx)
    assert written == [_plan(ctx)]
    assert parked.value.gate == "PLAN" and parked.value.verdict == "episodes/ep03/plan.verdict.json"
    assert parked.value.ask == "read the plan and sign"
    assert json.loads(_plan(ctx).read_text(encoding="utf-8"))["title"] == "The Yard"
    assert writer.calls == [None]
    assert gate.commands[0][-3:] == ["scripts/episode/plan_check.py", "20260901000001", "3"]


def test_two_refusals_then_a_pass_locks_the_plan(ctx, monkeypatch):
    writer, gate = _wire(ctx, monkeypatch, (1, REFUSED_OUT), (1, REFUSED_OUT), (0, CLEAN_OUT))
    with pytest.raises(Escalation) as parked:
        step.run(ctx)
    assert parked.value.gate == "PLAN" and parked.value.verdict.endswith("plan.verdict.json")
    assert len(writer.calls) == 3 and writer.calls[0] is None
    assert writer.calls[1] == ["CONTRACT OK: The Yard | 24 shots | 140s projected", "PLAN GATES   : 1",
                               "    G-SCALE shot 4: a close with no cell", "VERDICT      : REFUSED"]
    assert _plan(ctx).exists() and not (ctx.home / "plan.refused.json").exists()


def test_three_refusals_escalate_naming_two_rounds(ctx, monkeypatch):
    writer, gate = _wire(ctx, monkeypatch, (1, REFUSED_OUT))
    with pytest.raises(Escalation) as parked:
        step.run(ctx)
    assert len(writer.calls) == 3 and len(gate.commands) == 3
    assert parked.value.gate == "PLAN" and parked.value.verdict == "episodes/ep03/plan.json"
    assert "after 2 rounds" in parked.value.ask and "refusals in the log" in parked.value.ask
    assert not _plan(ctx).exists(), "a refused draft is not left where the next run would take it as written"
    assert (ctx.home / "plan.refused.json").exists()
    logged = ctx.tracker.log_path.read_text(encoding="utf-8")
    assert "G-SCALE shot 4" in logged


def test_an_existing_unsigned_plan_is_not_rewritten_only_parked(ctx, monkeypatch):
    writer, gate = _wire(ctx, monkeypatch, (0, CLEAN_OUT))
    episode_home.write_plan(_plan(ctx), {**canned_plan(), "title": "Kept"})
    with pytest.raises(Escalation):
        step.run(ctx)
    assert writer.calls == [] and gate.commands == []
    assert json.loads(_plan(ctx).read_text(encoding="utf-8"))["title"] == "Kept"


def test_rewrite_writes_a_new_plan_when_nothing_ran_downstream(ctx, monkeypatch):
    writer, _ = _wire(ctx, monkeypatch, (0, CLEAN_OUT))
    episode_home.write_plan(_plan(ctx), {**canned_plan(), "title": "Old"})
    ctx.extra = ["--rewrite"]
    with pytest.raises(Escalation):
        step.run(ctx)
    assert len(writer.calls) == 1
    assert json.loads(_plan(ctx).read_text(encoding="utf-8"))["title"] == "The Yard"


def test_a_plan_that_ran_downstream_is_never_rewritten(ctx, monkeypatch):
    writer, gate = _wire(ctx, monkeypatch, (0, CLEAN_OUT))
    episode_home.write_plan(_plan(ctx), {**canned_plan(), "title": "Ran"})
    _placed(ctx).write_text("{}", encoding="utf-8")
    ctx.extra = ["--rewrite"]
    step.run(ctx)
    assert writer.calls == [] and gate.commands == []
    assert json.loads(_plan(ctx).read_text(encoding="utf-8"))["title"] == "Ran"


def test_a_signed_plan_runs_through_without_parking(ctx, monkeypatch):
    writer, _ = _wire(ctx, monkeypatch, (0, CLEAN_OUT))
    episode_home.write_plan(_plan(ctx), canned_plan())
    plan_verdict.sign(_plan(ctx), "read")
    step.run(ctx)
    assert writer.calls == []


def test_refusal_lines_keep_the_gate_text_and_drop_advisories_and_blanks():
    assert step.refusal_lines("A\n\n  advisory: x\nB\n") == ["A", "B"]


def test_the_runner_skips_a_grandfathered_unit(ctx, monkeypatch):
    from studio import step_runner
    _wire(ctx, monkeypatch, (0, CLEAN_OUT))
    episode_home.write_plan(_plan(ctx), canned_plan())
    _placed(ctx).write_text("{}", encoding="utf-8")
    assert step_runner.run_steps(ctx, [step]) == "completed"
    assert db.unit_status(ctx.conn, ctx.codex_id, "episode", "ep03") == {"02": "skipped"}


def test_the_runner_records_the_plan_gate_as_escalated(ctx, monkeypatch):
    from studio import step_runner
    _wire(ctx, monkeypatch, (0, CLEAN_OUT))
    assert step_runner.run_steps(ctx, [step]) == "escalated"
    assert db.unit_status(ctx.conn, ctx.codex_id, "episode", "ep03") == {"02": "escalated"}


def test_help_prints_without_a_book(capsys):
    from studio import step_cli
    assert step_cli.main(step, ["step_02_plan.py", "--help"]) == 0
    assert "plan" in capsys.readouterr().out


# ---- a draft the contract refuses is a refusal, not a crash (ep12, 2026-09-24) ----------

class ContractBreaker(Writer):
    """First draft breaks the Episode contract (the agent's parse raises); then canned."""

    def write(self, brief, refusals=None, usage=None):
        self.calls.append(refusals)
        if len(self.calls) == 1:
            Episode.model_validate({"number": "not a number"})
        return Episode.model_validate(canned_plan(brief["number"]))


def test_a_draft_the_contract_refuses_goes_back_to_the_writer(ctx, monkeypatch):
    """ep12's first draft said 'slowly' on four shots; the contract raised inside the
    agent's parse and killed the step before the improve loop could quote it back."""
    writer = ContractBreaker()
    monkeypatch.setattr(step, "episode_writer", writer)
    ctx.capture = Capture((0, CLEAN_OUT))
    with pytest.raises(Escalation):
        step.run(ctx)
    assert len(writer.calls) == 2 and writer.calls[0] is None
    assert any("number" in line for line in writer.calls[1])
    assert _plan(ctx).exists()


def test_every_refusal_so_far_goes_back_to_the_writer(ctx, monkeypatch):
    """ep12: 'slowly' refused in round 0, 'crawl' in round 1, the style line in
    round 2 -- each draft was written from scratch and saw only the last round's
    refusals, so it traded one fault for another. The writer is shown them all."""
    writer, _ = _wire(ctx, monkeypatch, (1, "VERDICT      : REFUSED\n    G-A first\n"),
                      (1, "VERDICT      : REFUSED\n    G-B second\n"), (0, CLEAN_OUT))
    with pytest.raises(Escalation):
        step.run(ctx)
    third = writer.calls[2]
    assert any("G-A first" in line for line in third) and any("G-B second" in line for line in third)
