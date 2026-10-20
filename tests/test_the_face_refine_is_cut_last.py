"""The face refine is cut LAST for time (retro 2026-10-20 item 5, package C; owner veto list V2 not vetoed:
"cut last and park").

It was the FIRST thing cut (face_refine.cut: its price plus a 550 s re-measure had to fit), which is how
the clock silently re-creates the blur fault.  Now step 09 holds N takes x 81 s for the refine from its
start (ep01's repair refine: 972 s over 12 takes), a re-measure of unchanged bytes is cut before it, and
the refine itself is cut only when its own price leaves no reserve: it changes no take bytes (the paste
is made at the cut), so no check is owed after it.  A take still skipped for time ships flagged, and the
episode is NOT upload-ready: a FACE_REFINE terminal the publish lock holds for the owner.  Never auto-shipped.
The lanes' early refine and the tiny-face draw (a re-render) keep the old rule (face_refine.cut).
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from scripts.episode import face_refine as cli
from scripts.episode import step_09_shoot as step
from studio import face_refine as fr, learnings, publish_lock
from studio.run_budget import EPISODE_SHARES, Budget

LIMIT = 6 * 3600
OWED_AFTER = Budget(5 * 3600, EPISODE_SHARES).owed_after("09")
ROW = json.loads((Path(__file__).parent / "fixtures" / "ep01_face_list" / "repair_refine_row.json").read_text("utf-8"))


def budget_at(spent: float) -> Budget:
    now = [0.0]
    b = Budget(5 * 3600, EPISODE_SHARES, clock=lambda: now[0], limit=LIMIT)
    b.start("09")
    now[0] = spent
    return b


def ctx_at(tmp_path, spent=0.0):
    home = tmp_path / "episodes" / "ep01"
    ran, logged = [], []
    return SimpleNamespace(home=home, book_dir=tmp_path, number=1, budget=budget_at(spent), ran=ran, logged=logged,
                           log=lambda msg, **k: logged.append(msg),
                           learn=lambda row: learnings.record(home / "learnings.jsonl", row),
                           run_script=lambda script, *extra, **kw: ran.append((script, extra, kw)) or 0)


def test_a_refined_take_costs_81_s_as_measured_on_ep01():
    takes = ROW["note"].split()
    assert round(ROW["seconds"] / len(takes)) == fr.REFINE_TAKE_S == 81.0
    assert fr.reserve(12) == 12 * 81.0


def test_the_refine_runs_on_a_clock_that_holds_its_price_but_no_check_after_it():
    b = budget_at(LIMIT - OWED_AFTER - 400.0)
    assert not fr.cut_last(b, "09", 300.0)
    assert fr.cut(b, "09", 300.0), "the lanes and the tiny-face draw keep the old rule"


def test_the_refine_is_cut_when_its_own_price_leaves_no_reserve():
    assert fr.cut_last(budget_at(LIMIT - OWED_AFTER - 200.0), "09", 300.0)
    assert not fr.cut_last(None, "09", 10_000.0)


def write_cards(ctx, n: int) -> None:
    room = ctx.home / step.TAKES
    room.mkdir(parents=True, exist_ok=True)
    cards = [{"index": i, "shots": [i], "faces": ["a"]} for i in range(n)]
    (room / "prompts.json").write_text(json.dumps(cards), encoding="utf-8")


def test_step_09_holds_n_takes_x_81_s_from_its_start(tmp_path):
    ctx = ctx_at(tmp_path)
    write_cards(ctx, 12)
    assert step.refine_reserve(ctx) == 12 * 81.0
    step.say_reserve(ctx)
    assert any("REFINE RESERVE" in m and "12 take(s)" in m for m in ctx.logged)


def test_a_take_already_decided_holds_no_reserve(tmp_path):
    ctx = ctx_at(tmp_path)
    write_cards(ctx, 2)
    (ctx.home / step.TAKES / "T00.mp4").write_bytes(b"take")
    doc = {"T00": {"status": "refined", "take_sha8": cli.sha8(ctx.home / step.TAKES / "T00.mp4"), "people": []}}
    (ctx.home / step.TAKES / cli.DOC).write_text(json.dumps(doc), encoding="utf-8")
    assert step.refine_reserve(ctx) == 81.0


def test_a_take_whose_faces_already_read_holds_no_reserve(tmp_path):
    """ep01: ten takes the warp gate tracks at 120 px or more at their smallest are never refined."""
    ctx = ctx_at(tmp_path)
    write_cards(ctx, 2)
    dq = {"passed": True, "gates": [], "measures": {"warp": {"state": "pass", "share": 1.0,
                                                             "tracks": [{"median_px": 220.0, "min_px": 211.2}]}}}
    (ctx.home / step.TAKES / "T00.dq.json").write_text(json.dumps(dq), encoding="utf-8")
    assert step.refine_reserve(ctx) == 81.0


def test_the_re_measure_is_cut_before_the_refine(tmp_path):
    """The same clock: the 550 s re-measure fits alone, not beside the refine's reserve -- so it is cut,
    and the refine it made room for still runs."""
    ctx = ctx_at(tmp_path, spent=LIMIT - OWED_AFTER - 900.0)
    write_cards(ctx, 12)
    assert not ctx.budget.checks_cut("09", step.DQ_PASS_SECONDS)
    assert step.dq_flags(ctx) == ["--ceiling-spent"]
    assert not fr.cut_last(ctx.budget, "09", 800.0)


def test_a_refine_the_clock_cannot_hold_is_cut_last_and_recorded(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "owed", lambda book, n, among=None: {3: 220.0})
    cuts = []
    monkeypatch.setattr(cli, "record_cut", lambda room, indices, price, book, n, why="": cuts.append((indices, why)))
    ctx = ctx_at(tmp_path, spent=LIMIT - OWED_AFTER - 100.0)
    step.refine_rest(ctx)
    assert ctx.ran == [] and cuts and cuts[0][0] == [3] and "cut last" in cuts[0][1]
    assert any("REFINE CUT" in m for m in ctx.logged)


def cut_face() -> dict:
    rows = {5: {"smallest_px": 96.7, "pasted": False, "unpasted": [{"who": None, "px": 96.7}], "status": "cut",
                "by": "warp"}}
    return fr.face_list(rows)


def test_a_take_cut_for_time_holds_the_publish_for_the_owner(tmp_path):
    """Not upload-ready: the publish lock holds a FACE_REFINE terminal no judge can clear."""
    ctx = ctx_at(tmp_path)
    step.hold_publish(ctx, cli.cut_takes(cut_face()))
    held = publish_lock.stops(ctx.home, "abcd1234")
    assert any(s.startswith("FACE_REFINE ended flag") and "T05" in s for s in held)
    assert "FACE_REFINE" not in publish_lock.judge_waivers(ctx.home)


def test_a_later_refine_of_every_cut_take_releases_the_hold(tmp_path):
    ctx = ctx_at(tmp_path)
    step.hold_publish(ctx, ["T05"])
    step.hold_publish(ctx, [])
    assert not any(s.startswith("FACE_REFINE") for s in publish_lock.open_terminals(ctx.home))


def test_no_cut_and_no_hold_writes_nothing(tmp_path):
    ctx = ctx_at(tmp_path)
    step.hold_publish(ctx, [])
    assert not (ctx.home / "learnings.jsonl").exists()


def test_the_face_list_step_holds_the_publish_on_a_cut_take(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "face_list", lambda book, n: cut_face())
    ctx = ctx_at(tmp_path)
    (ctx.home / step.TAKES).mkdir(parents=True)
    step.face_list_note(ctx)
    assert any(t.startswith("FACE_REFINE") for t in publish_lock.open_terminals(ctx.home))
