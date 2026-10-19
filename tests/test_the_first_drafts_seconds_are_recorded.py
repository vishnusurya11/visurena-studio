"""The first draft's seconds and tokens are a learnings row `draft` (Jekyll ep01 Kawajiri, 2026-10-18:
738 s of first draft sat in no row; learnings row 1 was rung 1's 374 s).  The wall is not moved.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.episode import step_02_plan as step  # noqa: E402
from studio import llm, plan_ladder  # noqa: E402


class Writer:
    def write(self, brief, refusals, previous=None, usage=None, **kw):
        usage.update(input_tokens=900, output_tokens=300, total_tokens=1200)
        raise llm.OverBudget("fake writer: stop after the tokens are counted")


class Ctx:
    def __init__(self, home: Path):
        self.home, self.book_dir, self.number, self.rows, self.said = home, home, 1, [], []

    def learn(self, row):
        self.rows.append(row)

    def log(self, msg, **kw):
        self.said.append(msg)


def clocked_desk(tmp_path, ticks):
    ctx = Ctx(tmp_path)
    desk = plan_ladder.Desk(ctx, tmp_path / "plan.json", writer=Writer())
    desk.brief = {"x": 1}
    clock = iter(ticks)
    desk.now = lambda: next(clock)
    return ctx, desk


def test_the_first_drafts_seconds_and_tokens_are_a_draft_row(tmp_path):
    ctx, desk = clocked_desk(tmp_path, [1000.0, 1738.0])
    step.first_draft(ctx, desk)
    (row,) = ctx.rows
    assert (row.step, row.gate, row.action) == ("02", "PLAN", "draft")
    assert row.seconds == 738.0 and row.measured == 1200
    assert "900 in" in row.note and "300 out" in row.note


def test_the_wall_is_not_moved_by_the_draft(tmp_path):
    ctx, desk = clocked_desk(tmp_path, [1000.0, 1738.0])
    step.first_draft(ctx, desk)
    assert desk.began is None and desk.usage is None


class Bare:
    """A StageContext run alone keeps no learnings."""

    def __init__(self, home: Path):
        self.home, self.book_dir, self.number = home, home, 1

    def log(self, msg, **kw):
        pass


def test_a_bare_context_without_learn_keeps_no_row(tmp_path):
    ctx = Bare(tmp_path)
    desk = plan_ladder.Desk(ctx, tmp_path / "plan.json", writer=Writer())
    desk.brief = {"x": 1}
    step.first_draft(ctx, desk)
    assert desk.usage is None
