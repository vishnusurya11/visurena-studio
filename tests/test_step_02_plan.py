"""Step 02 of the episode stage: brief -> write -> plan_check + the critic ->
the plan ladder (improve x2, fresh_brief, model_tier) -> the PLAN signature
in the judge's name, or the draft deferred when the battery never passes.

A fake writer, a fake capture and a fake reader stand in for the agent, the
gate script and the critic; nothing here calls a model, and `plan_check` is
never launched.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from scripts.episode import step_02_plan as step
from studio import db, episode_home, plan_verdict
from studio.episode_run import EpisodeContext
from studio.episode_spec import Episode
from tests.plan_reader_fixtures import reading
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
    context = EpisodeContext(conn, codex_id, book, "episode", unit="ep03", number=3,
                             logs_root=tmp_path / "logs", busy=lambda: False,
                             hold=tmp_path / "RENDER_HOLD", launch=lambda cmd: 0)
    context.home = episode_home.home(book, 3)
    context.home.mkdir(parents=True)
    context.extra = []
    monkeypatch.setattr(step.plan_ladder, "plan_brief",
                        SimpleNamespace(build=lambda b, n, targets=None: {"number": n}))
    return context


class Writer:
    """A fake episode_writer: the canned plan every time; records the refusals it was given."""

    def __init__(self):
        self.calls, self.agents = [], []

    def write(self, brief, refusals=None, usage=None, _agent=None):
        self.calls.append(refusals)
        self.agents.append(_agent)
        return Episode.model_validate(canned_plan(brief["number"]))


class Capture:
    """A fake gate: hands out (rc, out) in order, then repeats the last."""

    def __init__(self, *results):
        self.results, self.commands = list(results), []

    def __call__(self, cmd):
        self.commands.append(cmd)
        return self.results.pop(0) if len(self.results) > 1 else self.results[0]


class Reader:
    """A fake critic: the good reading three times; records every plan text it read."""

    def __init__(self, *readings):
        self.readings = list(readings) or [reading("good")]
        self.texts = []

    def __call__(self, plan_text, rows, k=3, **kw):
        self.texts.append(plan_text)
        return [self.readings[0]] * k


def _wire(ctx, monkeypatch, *gate_results, reader=None):
    writer, gate, critic = Writer(), Capture(*gate_results), reader or Reader()
    monkeypatch.setattr(step, "episode_writer", writer)
    monkeypatch.setattr(step.plan_reader, "read", critic)
    ctx.capture = gate
    return writer, gate


def _plan(ctx):
    return episode_home.plan_path(ctx.book_dir, ctx.number)


def _placed(ctx):
    return ctx.home / "placed.json"


def _verdict(ctx) -> dict:
    return json.loads(plan_verdict.verdict_path(_plan(ctx)).read_text(encoding="utf-8"))


# ---- the module's contract ----------------------------------------------------------

def test_the_step_declares_itself():
    assert (step.STEP_ID, step.NAME, step.GPU, step.MAX_IMPROVE, step.GATE) == ("02", "plan", False, 2, "PLAN")


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

def test_a_missing_plan_is_written_through_write_plan_then_judged_and_signed(ctx, monkeypatch):
    writer, gate = _wire(ctx, monkeypatch, (0, CLEAN_OUT))
    written = []
    real = episode_home.write_plan
    monkeypatch.setattr(step.plan_ladder.episode_home, "write_plan",
                        lambda out, doc: written.append(out) or real(out, doc))
    step.run(ctx)
    assert written == [_plan(ctx)]
    assert json.loads(_plan(ctx).read_text(encoding="utf-8"))["title"] == "The Yard"
    assert writer.calls == [None]
    assert gate.commands[0][-3:] == ["scripts/episode/plan_check.py", "20260901000001", "3"]
    doc = _verdict(ctx)
    assert doc["verdict"] == "APPROVE" and doc["signed_by"] == "judge:plan@1"
    assert doc["faults"] == [] and not doc.get("flagged")
    assert step.done(ctx) is True


def test_two_refusals_then_a_pass_locks_the_plan(ctx, monkeypatch):
    writer, gate = _wire(ctx, monkeypatch, (1, REFUSED_OUT), (1, REFUSED_OUT), (0, CLEAN_OUT))
    step.run(ctx)
    assert len(writer.calls) == 3 and writer.calls[0] is None
    assert writer.calls[1] == ["CONTRACT OK: The Yard | 24 shots | 140s projected", "PLAN GATES   : 1",
                               "    G-SCALE shot 4: a close with no cell", "VERDICT      : REFUSED"]
    assert _plan(ctx).exists() and not (ctx.home / step.plan_ladder.DEFERRED).exists()
    assert _verdict(ctx)["signed_by"] == "judge:plan@1" and plan_verdict.current(_plan(ctx))


def test_a_battery_that_keeps_refusing_defers_the_unit_after_the_whole_ladder(ctx, monkeypatch):
    writer, gate = _wire(ctx, monkeypatch, (1, REFUSED_OUT))
    step.run(ctx)
    assert len(writer.calls) == 5 and len(gate.commands) == 5
    assert not _plan(ctx).exists(), "a refused draft is not left where the next run would take it as written"
    assert (ctx.home / step.plan_ladder.DEFERRED).exists()
    assert not plan_verdict.verdict_path(_plan(ctx)).exists()
    logged = ctx.tracker.log_path.read_text(encoding="utf-8")
    assert "G-SCALE shot 4" in logged


def test_an_existing_unsigned_plan_is_not_rewritten_only_judged(ctx, monkeypatch):
    writer, gate = _wire(ctx, monkeypatch, (0, CLEAN_OUT))
    episode_home.write_plan(_plan(ctx), {**canned_plan(), "title": "Kept"})
    step.run(ctx)
    assert writer.calls == [] and len(gate.commands) == 1
    assert json.loads(_plan(ctx).read_text(encoding="utf-8"))["title"] == "Kept"
    assert _verdict(ctx)["signed_by"] == "judge:plan@1"


def test_rewrite_writes_a_new_plan_when_nothing_ran_downstream(ctx, monkeypatch):
    writer, _ = _wire(ctx, monkeypatch, (0, CLEAN_OUT))
    episode_home.write_plan(_plan(ctx), {**canned_plan(), "title": "Old"})
    ctx.extra = ["--rewrite"]
    step.run(ctx)
    assert len(writer.calls) == 1
    assert json.loads(_plan(ctx).read_text(encoding="utf-8"))["title"] == "The Yard"
    assert plan_verdict.current(_plan(ctx))


def test_a_plan_that_ran_downstream_is_never_rewritten(ctx, monkeypatch):
    writer, gate = _wire(ctx, monkeypatch, (0, CLEAN_OUT))
    episode_home.write_plan(_plan(ctx), {**canned_plan(), "title": "Ran"})
    _placed(ctx).write_text("{}", encoding="utf-8")
    ctx.extra = ["--rewrite"]
    step.run(ctx)
    assert writer.calls == [] and gate.commands == []
    assert json.loads(_plan(ctx).read_text(encoding="utf-8"))["title"] == "Ran"


def test_a_signed_plan_runs_through_without_a_second_judgement(ctx, monkeypatch):
    writer, gate = _wire(ctx, monkeypatch, (0, CLEAN_OUT))
    episode_home.write_plan(_plan(ctx), canned_plan())
    plan_verdict.sign(_plan(ctx), "read")
    step.run(ctx)
    assert writer.calls == [] and gate.commands == []


def test_refusal_lines_keep_the_gate_text_and_drop_advisories_and_blanks():
    assert step.refusal_lines("A\n\n  advisory: x\nB\n") == ["A", "B"]


def test_the_runner_skips_a_grandfathered_unit(ctx, monkeypatch):
    from studio import step_runner
    _wire(ctx, monkeypatch, (0, CLEAN_OUT))
    episode_home.write_plan(_plan(ctx), canned_plan())
    _placed(ctx).write_text("{}", encoding="utf-8")
    assert step_runner.run_steps(ctx, [step]) == "completed"
    assert db.unit_status(ctx.conn, ctx.codex_id, "episode", "ep03") == {"02": "skipped"}


def test_the_runner_completes_the_plan_step_on_the_judges_signature(ctx, monkeypatch):
    from studio import step_runner
    _wire(ctx, monkeypatch, (0, CLEAN_OUT))
    assert step_runner.run_steps(ctx, [step]) == "completed"
    assert db.unit_status(ctx.conn, ctx.codex_id, "episode", "ep03") == {"02": "completed"}
    assert _verdict(ctx)["signed_by"] == "judge:plan@1"


def test_help_prints_without_a_book(capsys):
    from studio import step_cli
    assert step_cli.main(step, ["step_02_plan.py", "--help"]) == 0
    assert "plan" in capsys.readouterr().out


# ---- a draft the contract refuses is a refusal, not a crash (2026-09-24) --------------

class ContractBreaker(Writer):
    """First draft breaks the Episode contract (the agent's parse raises); then canned."""

    def write(self, brief, refusals=None, usage=None, _agent=None):
        self.calls.append(refusals)
        if len(self.calls) == 1:
            Episode.model_validate({"number": "not a number"})
        return Episode.model_validate(canned_plan(brief["number"]))


def test_a_draft_the_contract_refuses_goes_back_to_the_writer(ctx, monkeypatch):
    """A first draft that breaks a contract rule raised inside the agent's parse and
    killed the step before the improve loop could quote it back."""
    writer = ContractBreaker()
    monkeypatch.setattr(step, "episode_writer", writer)
    monkeypatch.setattr(step.plan_reader, "read", Reader())
    ctx.capture = Capture((0, CLEAN_OUT))
    step.run(ctx)
    assert len(writer.calls) == 2 and writer.calls[0] is None
    assert any("number" in line for line in writer.calls[1])
    assert _plan(ctx).exists() and plan_verdict.current(_plan(ctx))


def test_every_refusal_so_far_goes_back_to_the_writer(ctx, monkeypatch):
    """Each draft is written from scratch: shown only the last round's refusals it
    traded one fault for another.  The writer is shown them all."""
    writer, _ = _wire(ctx, monkeypatch, (1, "VERDICT      : REFUSED\n    G-A first\n"),
                      (1, "VERDICT      : REFUSED\n    G-B second\n"), (0, CLEAN_OUT))
    step.run(ctx)
    third = writer.calls[2]
    assert any("G-A first" in line for line in third) and any("G-B second" in line for line in third)


def test_the_critics_faults_go_back_to_the_writer_as_gate_lines(ctx, monkeypatch):
    writer, _ = _wire(ctx, monkeypatch, (0, CLEAN_OUT), reader=Reader(reading("no_answer")))
    step.run(ctx)
    assert writer.calls[1] and all(line.startswith("G-READER ") for line in writer.calls[1])


def test_a_plan_edited_after_its_signature_is_not_grandfathered(ctx):
    """ep12: the plan was signed, ran downstream, then edited (shot 16 locked,
    extras declared); the runner said 'step 02 skipped: output exists' because a
    timeline sat beside it. Grandfathering is for a plan that never had a
    signature -- one whose signature went stale is judged again."""
    episode_home.write_plan(_plan(ctx), canned_plan())
    plan_verdict.sign(_plan(ctx), "read")
    _placed(ctx).write_text("{}", encoding="utf-8")
    episode_home.write_plan(_plan(ctx), {**canned_plan(), "title": "Edited after signing"})
    assert step.done(ctx) is False
