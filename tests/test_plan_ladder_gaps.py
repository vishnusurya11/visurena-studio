"""C7 (Jekyll Kawajiri ep01 retro): two gaps in the plan ladder.

(a) G-LIMB's cure ran only on a restore; a fresh writer draft reached the battery uncured.
(b) The stuck rule needs no progress in COUNT (a fall of one row is progress, same ids or not), and
    plan.climb.json keeps the stuck baseline so a resumed climb does not forget it.
"""
from __future__ import annotations

import json
from pathlib import Path

from studio import episode_home, plan_cures, plan_gates, plan_ladder
from studio.episode_spec import Episode
from tests.test_a_climb_that_moves_no_row_stops import IMPROVE, TIER, Ctx, desk_with_plan, rows
from tests.test_a_limb_needs_its_body import OLD_27, ep01, with_27


class LimbWriter:
    """Writes ep01's plan with shot 27 in the wording that floats a sleeve."""

    def write(self, brief, refusals=None, previous=None, _agent=None, **kw):
        return Episode.model_validate(with_27(OLD_27))


def shot_27(plan: Path) -> dict:
    return next(s for s in episode_home.read_json(plan)["shots"] if s["index"] == 27)


def test_a_fresh_writer_draft_gets_the_limb_cure_before_the_battery(tmp_path):
    desk = plan_ladder.Desk(Ctx(tmp_path), tmp_path / "plan.json", writer=LimbWriter())
    desk.brief = {}
    desk.write(None)
    shot = shot_27(desk.plan)
    assert shot["at_rest"].endswith(plan_cures.BODY_CLAUSE)
    assert not plan_gates.limb_hit(shot["size"], " ".join(shot[k] for k in ("frame", "at_rest", "motion")))


def test_a_limb_cure_that_raises_keeps_the_draft(tmp_path, monkeypatch):
    def boom(doc):
        raise RuntimeError("cure bug")
    monkeypatch.setattr(plan_cures, "body_clause", boom)
    desk = plan_ladder.Desk(Ctx(tmp_path), tmp_path / "plan.json", writer=LimbWriter())
    desk.brief = {}
    desk.write(None)
    assert not shot_27(desk.plan)["at_rest"].endswith(plan_cures.BODY_CLAUSE)


def test_six_rows_to_five_on_the_same_ids_is_progress_in_count(tmp_path):
    desk, writer = desk_with_plan(tmp_path)
    desk.take(IMPROVE, 0, rows("G-TWO", "G-PRESENT", "G-AIM", "G-AIM", "G-AIM", "G-LAID"))
    desk.take(IMPROVE, 1, rows("G-TWO", "G-PRESENT", "G-AIM", "G-AIM", "G-LAID"))
    desk.take(TIER, 0, rows("G-TWO", "G-PRESENT", "G-AIM", "G-AIM"))
    assert len(writer.calls) == 3 and not desk.stuck


def test_the_same_count_on_the_same_ids_is_still_stuck(tmp_path):
    desk, writer = desk_with_plan(tmp_path)
    desk.take(IMPROVE, 0, rows("G-TWO", "G-AIM"))
    desk.take(IMPROVE, 1, rows("G-TWO", "G-AIM"))
    assert len(writer.calls) == 1 and desk.stuck


def valid_desk(home: Path):
    """A desk whose plan on disk is a real (contract-valid) draft, so a restore can re-write it."""
    desk, writer = desk_with_plan(home)
    episode_home.write_plan(desk.plan, ep01())
    return desk, writer


def test_a_resumed_climb_keeps_the_stuck_baseline(tmp_path):
    desk, _ = valid_desk(tmp_path)
    desk.take(IMPROVE, 0, rows("G-TWO", "G-AIM"))
    saved = json.loads(desk.climb_path().read_text(encoding="utf-8"))
    assert saved["prev_keys"] == {"battery": True, "keys": {"G-TWO": 1, "G-AIM": 1}}
    again, writer = valid_desk(tmp_path)
    again.restore(lambda: rows("G-TWO", "G-AIM"))
    assert again.prev_keys == desk.prev_keys
    again.take(IMPROVE, 1, rows("G-TWO", "G-AIM"))
    assert again.stuck and writer.calls == []


def test_an_old_checkpoint_without_a_baseline_resumes_with_none(tmp_path):
    desk, _ = valid_desk(tmp_path)
    desk.take(IMPROVE, 0, rows("G-TWO"))
    saved = json.loads(desk.climb_path().read_text(encoding="utf-8"))
    saved.pop("prev_keys")
    desk.climb_path().write_text(json.dumps(saved), encoding="utf-8")
    again, _ = valid_desk(tmp_path)
    again.restore(lambda: rows("G-TWO"))
    assert again.prev_keys is None
