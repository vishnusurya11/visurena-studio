"""Step 03b (2026-09-28): cells are written FROM the drawn place picture -- the
vision model lists the fixed things by frame third and band, code writes the
setup's geometry and every shot's at_rest behind the writer's subject sentence.
A plan the battery then refuses keeps the writer's cells; the step never parks."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.episode import step_03b_cells as step
from studio import cells_from_picture as cells, db, episode_home, picture_read, plan_verdict
from studio.stage_run import StageContext
from tests.test_episode_writer import canned_plan

CODEX = "20260901000001"
SAID = ('Here you go: [{"thing": "iron bed", "x": "LEFT", "y": "MIDDLE", "depth": "near", "size": "large"}, '
        '{"thing": "dormer window", "x": "RIGHT", "y": "TOP", "depth": "far", "size": "small"}, '
        '{"thing": "a man", "x": "CENTRE", "y": "MIDDLE"}, {"thing": "deal table", "x": "SIDEWAYS", "y": "MIDDLE"}]')


def test_the_read_keeps_only_the_closed_vocabulary():
    rows = picture_read.parse(SAID)
    assert [r["thing"] for r in rows] == ["iron bed", "dormer window", "a man"]
    assert rows[2] == {"thing": "a man", "x": "CENTRE", "y": "MIDDLE", "depth": "far", "size": "large"}
    assert picture_read.parse("no list here") == [] and not picture_read.readable("[]")


def test_a_cell_keeps_the_subject_and_restates_the_room_by_frame_position():
    things = picture_read.parse(SAID)[:2]
    shot = {"index": 3, "setup": "attic", "size": "medium",
            "at_rest": "The brother sits at the deal table; the bed fills the near-left edge; the door stands at the rear."}
    got = cells.at_rest_of(shot, things)
    assert got.startswith("The brother sits at the deal table.")
    assert "iron bed stands at the MIDDLE LEFT, near" in got and "dormer window shows small at the TOP RIGHT" in got
    assert "near-left edge" not in got
    assert cells.at_rest_of({**shot, "size": "close"}, things).count("The ") == 2   # the subject and one thing


def test_the_rewrite_keeps_the_contract_on_a_real_plan():
    from studio.episode_spec import Episode
    doc = canned_plan(4)
    setup = next(iter(doc["setups"]))
    out = cells.rewrite(doc, {setup: picture_read.parse(SAID)})
    Episode.model_validate(out)
    assert "MIDDLE LEFT" in out["setups"][setup]["geometry"]
    assert all("MIDDLE LEFT" in s["at_rest"] for s in out["shots"] if s["setup"] == setup)


def ctx_for(tmp_path) -> StageContext:
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    db.insert_codex(conn, "Book", codex_id=CODEX)
    ctx = StageContext(conn, CODEX, tmp_path / "book", "episode", unit="ep04", number=4,
                       logs_root=tmp_path / "logs", busy=lambda: False, hold=tmp_path / "HOLD", launch=lambda cmd: 0)
    ctx.home = episode_home.home(ctx.book_dir, 4)
    ctx.extra = []
    doc = canned_plan(4)
    doc["setups"]["room"].update(location="yard", view="wide_establishing")
    episode_home.write_json(ctx.home / "plan.json", doc)
    place = ctx.book_dir / "refs" / "locations" / "yard" / "wide_establishing.png"
    place.parent.mkdir(parents=True)
    place.write_bytes(b"png")
    return ctx


def test_the_step_writes_the_cells_resigns_the_verdict_and_is_done(tmp_path, monkeypatch):
    ctx = ctx_for(tmp_path)
    plan = ctx.home / "plan.json"
    plan_verdict.sign(plan, "holds", signed_by="judge:plan@1", flagged=True, faults=[{"kind": "story"}])
    monkeypatch.setattr(step, "READ", lambda path: picture_read.parse(SAID))
    monkeypatch.setattr(step, "CHECK", lambda ctx: (0, "clean"))
    assert not step.done(ctx)
    step.run(ctx)
    assert step.done(ctx) and plan_verdict.current(plan)
    signed = plan_verdict.read(plan)
    assert signed["flagged"] is True and signed["signed_by"] == "judge:plan@1" and "03b" in signed["note"]
    assert "MIDDLE LEFT" in episode_home.read_json(plan)["setups"]["room"]["geometry"]
    assert step.stamp(ctx.home)["from_picture"] is True


def test_a_plan_the_battery_refuses_keeps_the_writers_cells_and_still_finishes(tmp_path, monkeypatch):
    ctx = ctx_for(tmp_path)
    plan = ctx.home / "plan.json"
    before = plan.read_bytes()
    monkeypatch.setattr(step, "READ", lambda path: picture_read.parse(SAID))
    monkeypatch.setattr(step, "CHECK", lambda ctx: (1, "G-SCALE shot 1: ..."))
    step.run(ctx)
    assert plan.read_bytes() == before and step.done(ctx)
    assert step.stamp(ctx.home)["from_picture"] is False
