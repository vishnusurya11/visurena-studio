"""C3_verdict #1 (T1): the plan climb checkpoints its best draft every rung.

`Desk.best` and `Desk.drafts` lived only in memory until the terminal, so a
killed climb restarted from whatever draft was on disk.  Four cut climbs
restarted worse than their best (ep17 1 -> 38, ep22 35 -> 46, ep26 5 -> 6,
ep13 0 -> 22).  plan.climb.json now holds the best draft, the battery-passed
drafts, the merged refusals and the rungs done; a resume restores the DRAFTS
and re-judges them under today's battery -- never trusting an old verdict
when the code moved -- and a signature or a deferral retires the file."""
from __future__ import annotations

import json

import pytest

from scripts.episode import step_02_plan as step
from studio import episode_home, plan_ladder, plan_verdict
from studio.deferral import Deferred
from studio.episode_spec import Episode
from tests.plan_reader_fixtures import reading
from tests.test_episode_writer import canned_plan
from tests.test_step_02_plan import CLEAN_OUT, Reader, conn, ctx  # noqa: F401

LINES = {"A": ["G-SCALE shot 4: a close with no cell"],
         "B": ["G-SCALE shot 4: a close with no cell", "G-CROWD shot 2: six walk-ons", "G-LIGHT shot 9: noon"],
         "C": ["G-LIGHT shot 9: noon", "G-ARTICLE shot 1: a the"]}


class Killed(RuntimeError):
    """The drive killed mid-rung (Stop-Process runs no finally)."""


class Writer:
    """Writes the titled drafts in order; raises Killed when the titles run out."""

    def __init__(self, *titles):
        self.titles, self.previous, self.refusals = list(titles), [], []

    def write(self, brief, refusals=None, usage=None, _agent=None, previous=None):
        self.previous.append(previous)
        self.refusals.append(refusals)
        if not self.titles:
            raise Killed("killed in the rung")
        return Episode.model_validate({**canned_plan(brief["number"]), "title": self.titles.pop(0)})


def battery_by_title(ctx, clean=()):
    """plan_check by the draft's title: the refusal lines of LINES, clean for `clean`."""
    def capture(cmd):
        plan = episode_home.plan_path(ctx.book_dir, ctx.number)
        if not plan.exists():
            return 1, "no plan"
        title = episode_home.read_json(plan)["title"]
        if title in clean:
            return 0, CLEAN_OUT
        return 1, "\n".join(LINES[title]) + "\n"
    return capture


def _wire(ctx, monkeypatch, writer, clean=(), reader=None):
    monkeypatch.setattr(step, "episode_writer", writer)
    monkeypatch.setattr(step.plan_reader, "read", reader or Reader())
    ctx.capture = battery_by_title(ctx, clean)


def _climb(ctx):
    return ctx.home / plan_ladder.CLIMB


def _killed_after_rung_one(ctx, monkeypatch):
    """Round 0 writes A (1 line, the best), improve #1 writes B (3 lines), improve #2 is killed."""
    _wire(ctx, monkeypatch, Writer("A", "B"))
    with pytest.raises(Killed):
        step.run(ctx)


def test_a_killed_climb_leaves_its_best_draft_on_disk(ctx, monkeypatch):
    _killed_after_rung_one(ctx, monkeypatch)
    doc = json.loads(_climb(ctx).read_text(encoding="utf-8"))
    assert doc["best"]["doc"]["title"] == "A" and doc["best"]["n"] == 1
    assert episode_home.read_json(step.plan_of(ctx))["title"] == "B"      # the last draft is the worse one
    assert set(LINES["A"] + LINES["B"]) <= set(doc["refusals"])
    assert doc["rungs_done"] == 1 and doc["escalated"] is True
    assert doc["code_sha8"] == plan_ladder.code_sha8() and doc["plan_sha8"]


def test_the_resume_edits_the_best_draft_with_every_refusal(ctx, monkeypatch):
    _killed_after_rung_one(ctx, monkeypatch)
    writer = Writer("C", "C")
    _wire(ctx, monkeypatch, writer)
    with pytest.raises(Deferred):
        step.run(ctx)
    assert writer.previous[0]["title"] == "A", "the resume edits the best draft, not the last"
    assert set(LINES["A"] + LINES["B"]) <= set(writer.refusals[0])
    assert len(writer.previous) == 2, "one improve left, then model_tier: the done rung is not re-run"


def test_a_moved_code_sha_rejudges_and_a_now_clean_draft_signs(ctx, monkeypatch):
    _killed_after_rung_one(ctx, monkeypatch)
    monkeypatch.setattr(plan_ladder, "code_sha8", lambda: "moved000")
    writer = Writer()
    _wire(ctx, monkeypatch, writer, clean=("A",))
    step.run(ctx)
    assert episode_home.read_json(step.plan_of(ctx))["title"] == "A"
    assert plan_verdict.current(step.plan_of(ctx)) and writer.previous == []


def test_a_signed_plan_leaves_no_checkpoint(ctx, monkeypatch):
    _wire(ctx, monkeypatch, Writer("B", "A"), clean=("A",))
    step.run(ctx)
    assert plan_verdict.current(step.plan_of(ctx)) and not _climb(ctx).exists()


def test_a_deferral_retires_the_checkpoint(ctx, monkeypatch):
    _wire(ctx, monkeypatch, Writer("B", "B", "B", "B"))
    with pytest.raises(Deferred):
        step.run(ctx)
    assert (ctx.home / plan_ladder.DEFERRED).exists() and not _climb(ctx).exists()


def _signed_bytes(ctx, monkeypatch, checkpoint: bool) -> tuple[bytes, bytes]:
    for path in (step.plan_of(ctx), plan_verdict.verdict_path(step.plan_of(ctx))):
        path.unlink(missing_ok=True)
    if not checkpoint:
        monkeypatch.setattr(plan_ladder.Desk, "checkpoint", lambda self: None)
    _wire(ctx, monkeypatch, Writer("B", "A"), clean=("A",), reader=Reader(reading("good")))
    step.run(ctx)
    plan = step.plan_of(ctx)
    return plan.read_bytes(), plan_verdict.verdict_path(plan).read_bytes()


def test_a_clean_climb_signs_the_same_bytes_with_and_without_the_checkpoint(ctx, monkeypatch):
    kept = _signed_bytes(ctx, monkeypatch, checkpoint=True)
    assert kept == _signed_bytes(ctx, monkeypatch, checkpoint=False)


def test_the_ladder_after_done_rungs_drops_them():
    names = lambda ladder: [r.name for r in ladder.rungs for _ in range(r.tries)]  # noqa: E731
    assert names(plan_ladder.ladder_after(0)) == ["improve", "improve", "model_tier"]
    assert names(plan_ladder.ladder_after(1)) == ["improve", "model_tier"]
    assert names(plan_ladder.ladder_after(3)) == []
