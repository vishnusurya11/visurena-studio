"""Step 09's substep 09_07: the face refine.  Inside the lanes a take is refined the
moment it passes its dq (tests/test_face_refine_runs_in_the_gpu_lane.py); after the
ladder, any selected take still owed one (a retake, a swapped attempt) is refined in
one GPU run -- or cut first when the clock's reserve needs the time.  A context
double records the scripts; nothing renders."""
from __future__ import annotations

from types import SimpleNamespace

from scripts.episode import face_refine as cli
from scripts.episode import step_09_shoot as step
from studio import take_overlap
from studio.run_budget import EPISODE_SHARES, Budget


def ctx_at(tmp_path, spent=0.0):
    now = [0.0]
    budget = Budget(5 * 3600, EPISODE_SHARES, clock=lambda: now[0], limit=6 * 3600)
    budget.start("09")
    now[0] = spent
    ran, logged = [], []
    ctx = SimpleNamespace(home=tmp_path / "home", book_dir=tmp_path, number=1, budget=budget, ran=ran,
                          logged=logged, log=lambda msg, **k: logged.append(msg),
                          run_script=lambda script, *extra, **kw: ran.append((script, extra, kw)) or 0)
    return ctx


def test_what_the_ladder_left_owed_is_refined_in_one_gpu_run(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "owed", lambda book, n, among=None: {7: 330.0, 2: 110.0})
    ctx = ctx_at(tmp_path)
    step.refine_rest(ctx)
    assert ctx.ran == [(step.REFINE, ("2", "7"), {"gpu": True})]


def test_nothing_owed_runs_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "owed", lambda book, n, among=None: {})
    ctx = ctx_at(tmp_path)
    step.refine_rest(ctx)
    assert ctx.ran == []


def test_a_short_clock_cuts_the_refine_and_records_it(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "owed", lambda book, n, among=None: {3: 220.0})
    cuts = []
    monkeypatch.setattr(cli, "record_cut", lambda room, indices, price, book, n: cuts.append((indices, price)))
    owed_after = Budget(5 * 3600, EPISODE_SHARES).owed_after("09")
    ctx = ctx_at(tmp_path, spent=6 * 3600 - owed_after - 600.0)
    step.refine_rest(ctx)
    assert ctx.ran == [] and cuts == [([3], 220.0)]
    assert any("REFINE CUT" in m for m in ctx.logged)


def test_the_lanes_carry_the_refine_bookkeeping(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(take_overlap, "shoot", lambda ctx, base, **kw: seen.update(kw))
    ctx = ctx_at(tmp_path)
    step.shoot(ctx, "--approved=render")
    assert isinstance(seen.get("refine"), take_overlap.Refines)
