"""F11 (architecture/plan/2026-10-05_self_curing_pipeline.md): between writer
rounds only `ghost_limbs` ran for free, so the paid writer was re-asked about
$0 faults every round and re-added them -- ep19 carried G-CROWD-CLOSE on the
same four shots through improve, improve, fresh_brief.  Now every draft
Desk.write lands gets plan_repair's mechanical table (no llm path) BEFORE the
battery re-judges it, at most MECH_ROUNDS rounds, each write recorded in the
cure ledger; the hook never raises.  The battery is monkeypatched: $0, no
subprocess, no model."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

from studio import episode_home, plan_cures, plan_ladder, plan_provenance
from studio.episode_spec import Episode
from tests.test_episode_writer import canned_plan

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))
import plan_repair  # noqa: E402

CROWD = "a dozen onlookers press along the rail"
CROWD_ROW = "    G-CROWD-CLOSE shot 10: a close shot carries a crowd"


class CrowdWriter:
    """A fake writer whose every draft puts a crowd on the close shot 10."""

    def write(self, brief, refusals=None, previous=None, _agent=None, **kw):
        plan = canned_plan(3)
        plan["shots"][10]["crowd"] = CROWD
        return Episode.model_validate(plan)


class Battery:
    """A fake plan_check: dirty with `rows` until the plan's crowd is gone."""

    def __init__(self, plan: Path, rows: list[str], always: bool = False):
        self.plan, self.rows, self.always, self.calls = plan, rows, always, 0

    def __call__(self, book_id: str, number: int):
        self.calls += 1
        crowded = json.loads(self.plan.read_text(encoding="utf-8"))["shots"][10].get("crowd")
        dirty = self.always or bool(crowded)
        return (not dirty), (self.rows if dirty else [])


def desk_at(tmp_path, home: bool = True):
    book = tmp_path / "20990101000000_test-book"
    plan = episode_home.home(book, 3) / "plan.json" if home else tmp_path / "plan.json"
    plan.parent.mkdir(parents=True, exist_ok=True)
    desk = plan_ladder.Desk(SimpleNamespace(book_dir=book, number=3), plan, writer=CrowdWriter())
    desk.brief = {}
    return desk


def shot_10(desk) -> dict:
    return json.loads(desk.plan.read_text(encoding="utf-8"))["shots"][10]


def test_a_crowd_on_a_close_shot_is_cured_before_the_battery_judges(tmp_path, monkeypatch):
    desk = desk_at(tmp_path)
    monkeypatch.setattr(plan_repair, "battery_rows", Battery(desk.plan, [CROWD_ROW]))
    desk.write(None)
    assert not shot_10(desk).get("crowd")


def test_the_cure_write_is_recorded_in_the_ledger(tmp_path, monkeypatch):
    desk = desk_at(tmp_path)
    monkeypatch.setattr(plan_repair, "battery_rows", Battery(desk.plan, [CROWD_ROW]))
    desk.write(None)
    rows = plan_provenance.rows(desk.plan.parent)
    assert [r["cures"] for r in rows] == [["close_crowds"]]


def test_a_cure_that_breaks_the_contract_leaves_the_draft_as_written(tmp_path, monkeypatch):
    def breaking(doc):
        doc["shots"][10]["size"] = "not_a_size"
        return doc

    desk = desk_at(tmp_path)
    monkeypatch.setattr(plan_repair, "battery_rows", Battery(desk.plan, [CROWD_ROW]))
    monkeypatch.setattr(plan_cures, "close_crowds", breaking)
    desk.write(None)
    assert shot_10(desk)["crowd"] == CROWD and shot_10(desk)["size"] == "close"
    assert plan_provenance.rows(desk.plan.parent) == []


def test_a_failing_battery_never_raises_and_keeps_the_draft(tmp_path, monkeypatch):
    def boom(book_id, number):
        raise RuntimeError("plan_check crashed")

    desk = desk_at(tmp_path)
    monkeypatch.setattr(plan_repair, "battery_rows", boom)
    desk.write(None)
    assert shot_10(desk)["crowd"] == CROWD


def test_at_most_two_mechanical_rounds_run(tmp_path, monkeypatch):
    desk = desk_at(tmp_path)
    battery = Battery(desk.plan, [CROWD_ROW], always=True)
    monkeypatch.setattr(plan_repair, "battery_rows", battery)
    desk.write(None)
    assert battery.calls <= plan_ladder.MECH_ROUNDS == 2


def test_a_plan_outside_the_episode_home_is_never_battery_checked(tmp_path, monkeypatch):
    desk = desk_at(tmp_path, home=False)
    battery = Battery(desk.plan, [CROWD_ROW])
    monkeypatch.setattr(plan_repair, "battery_rows", battery)
    desk.write(None)
    assert battery.calls == 0 and shot_10(desk)["crowd"] == CROWD


def test_a_book_without_a_codex_id_is_never_battery_checked(tmp_path, monkeypatch):
    book = tmp_path / "book"
    plan = episode_home.plan_path(book, 3)
    plan.parent.mkdir(parents=True)
    battery = Battery(plan, [CROWD_ROW])
    monkeypatch.setattr(plan_repair, "battery_rows", battery)
    desk = plan_ladder.Desk(SimpleNamespace(book_dir=book, number=3), plan, writer=CrowdWriter())
    desk.brief = {}
    desk.write(None)
    assert battery.calls == 0


def test_the_desk_pass_never_takes_an_llm_path(tmp_path, monkeypatch):
    def paid(*a, **k):
        raise AssertionError("an llm cure ran inside the desk's free pass")

    from studio import move_llm
    monkeypatch.setattr(move_llm, "cure_unfixed", paid)
    monkeypatch.setattr(plan_cures, "rebalance_heads", lambda doc, idx: (doc, [10]))
    row = "    G-MOVES shot 10: the move repeats"
    assert plan_cures.cure_for(row) == "rebalance_heads"
    doc, uncured, _ = plan_repair.apply_each(canned_plan(3), [row], Path("."), 3, llm=False)
    assert uncured == [row]
