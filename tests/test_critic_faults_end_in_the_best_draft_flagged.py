"""The battery passes and the critic keeps finding a fault: after improve x2
and fresh_brief x1 (model_tier is for a battery that still refuses, and is
not taken), the terminal keeps the BEST draft -- the one the critic faulted
least -- writes it back as plan.json and signs it flagged in the judge's
name, faults listed, with an audit row.  Never a park."""
from __future__ import annotations

import json

from studio import audit_rows, episode_home, learnings, plan_verdict
from studio.episode_spec import Episode
from tests.plan_reader_fixtures import reading
from tests.test_episode_writer import canned_plan
from tests.test_step_02_plan import CLEAN_OUT, Capture, Writer, _plan, _wire, conn, ctx, step  # noqa: F401

TITLES = ("Draft A", "Draft B", "Draft C", "Draft D", "Draft E")


class Drafts(Writer):
    """A different title every call, so every draft has its own sha8."""

    def write(self, brief, refusals=None, usage=None, _agent=None):
        self.calls.append(refusals)
        self.agents.append(_agent)
        return Episode.model_validate({**canned_plan(brief["number"]), "title": TITLES[len(self.calls) - 1]})


class Critic:
    """Two faults on every draft but 'Draft B', which gets one."""

    def __init__(self):
        self.texts = []

    def __call__(self, plan_text, rows, k=3, **kw):
        self.texts.append(plan_text)
        one = reading("no_answer")
        two = one.model_copy(deep=True)
        two.claims[0].span = ""
        return [one if "Draft B" in plan_text else two] * k


def _run(ctx, monkeypatch):
    writer, critic = Drafts(), Critic()
    monkeypatch.setattr(step, "episode_writer", writer)
    monkeypatch.setattr(step.plan_reader, "read", critic)
    ctx.capture = Capture((0, CLEAN_OUT))
    step.run(ctx)
    return writer, critic


def test_the_best_draft_is_kept_and_signed_flagged(ctx, monkeypatch):
    writer, critic = _run(ctx, monkeypatch)
    assert [t[:7] for t in TITLES[:len(writer.calls)]] == ["Draft A", "Draft B", "Draft C", "Draft D"]
    assert len(critic.texts) == 4, "model_tier is not taken once a draft has passed the battery"
    assert json.loads(_plan(ctx).read_text(encoding="utf-8"))["title"] == "Draft B"
    doc = json.loads(plan_verdict.verdict_path(_plan(ctx)).read_text(encoding="utf-8"))
    assert doc["verdict"] == "APPROVE" and doc["flagged"] is True
    assert doc["signed_by"] == "judge:plan@1" and [f["kind"] for f in doc["faults"]] == ["answer"]
    assert plan_verdict.current(_plan(ctx)) and step.done(ctx)


def test_the_terminal_leaves_an_audit_row_and_a_terminal_learning(ctx, monkeypatch):
    _run(ctx, monkeypatch)
    rows = audit_rows.load(ctx.book_dir)
    assert len(rows) == 1 and rows[0].terminal == "keep_best" and rows[0].gate == "PLAN"
    assert rows[0].sha8 == plan_verdict.plan_sha8(_plan(ctx))
    assert rows[0].artefact == "episodes/ep03/plan.verdict.json"
    actions = [(row.action, row.terminal) for row in learnings.load(ctx.learnings_path)]
    assert actions == [("improve", False), ("improve", False), ("fresh_brief", False),
                       ("model_tier", False), ("keep_best", True)]


def test_the_writer_saw_the_critics_lines_and_the_fresh_brief_saw_none(ctx, monkeypatch):
    writer, _ = _run(ctx, monkeypatch)
    assert writer.calls[0] is None
    assert all(line.startswith("G-READER ") for line in writer.calls[1])
    assert writer.calls[3] is None


def test_a_draft_the_battery_refused_is_never_the_best(ctx, monkeypatch):
    """Draft B is refused by the battery this time; the best among the battery-clean
    drafts (two faults each) is the earliest, Draft A."""
    writer, critic = Drafts(), Critic()
    monkeypatch.setattr(step, "episode_writer", writer)
    monkeypatch.setattr(step.plan_reader, "read", critic)
    ctx.capture = Capture((0, CLEAN_OUT), (1, "VERDICT      : REFUSED\n    G-X shot 1\n"), (0, CLEAN_OUT))
    step.run(ctx)
    assert json.loads(_plan(ctx).read_text(encoding="utf-8"))["title"] == "Draft A"
    assert episode_home.plan_path(ctx.book_dir, 3).exists()
