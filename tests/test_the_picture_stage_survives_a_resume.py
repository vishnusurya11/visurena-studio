"""Five-hour plan fix 2 (2026-09-30): the picture stage is idempotent across
resumes.  ep14 lost 3.5 h because a reprose rewrote plan.json without
re-signing its verdict (plan sha 0f71db24 vs signature 1eb1993f, live on
disk), so every restart re-ran the plan ladder and redrew the grids; and the
climb's cap lived in process memory (`Climb.redrawn`), so waterloo_station was
redrawn 9 times against a cap of 2.  Now: a frame-only cure re-signs the same
verdict for the new bytes (step 03's resign pattern), and the climb is
remembered in storyboard/ladder.json, mirroring takes/r2v/ladder.json."""
from __future__ import annotations

import json
from pathlib import Path

from studio import panel_ladder, plan_verdict
from studio.judges.verdict import Fault


def plan_doc() -> dict:
    return {"shots": [{"index": 3, "frame": "A man stands by the window."}]}


def test_a_reprose_re_signs_the_plan_for_its_new_bytes(tmp_path, monkeypatch):
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps(plan_doc()), encoding="utf-8")
    plan_verdict.sign(plan, "judged pass", signed_by="judge:plan@1")
    assert plan_verdict.current(plan)
    # the contract's own refusals are tested elsewhere; here the write must land
    from studio import episode_home
    monkeypatch.setattr(episode_home, "write_plan",
                        lambda p, d: Path(p).write_text(json.dumps(d), encoding="utf-8") or Path(p))
    doc = panel_ladder.reprose(plan_doc(), 3, [Fault(kind="lettering", where="shot_03")])
    panel_ladder.write_cured(plan, doc)           # write_plan + re-sign, one call
    assert plan_verdict.current(plan)             # the signature follows the bytes
    said = plan_verdict.read(plan)
    assert "reprose" in said.get("note", "")
    assert said.get("signed_by") == "judge:plan@1"


def test_the_climb_is_remembered_on_disk_across_instances(tmp_path):
    board = tmp_path / "storyboard"
    board.mkdir(parents=True)
    assert panel_ladder.load_climbed(tmp_path) == []
    panel_ladder.remember_climbed(tmp_path, "ep14_waterloo_3x1_a")
    panel_ladder.remember_climbed(tmp_path, "ep14_biology_2x2")
    panel_ladder.remember_climbed(tmp_path, "ep14_waterloo_3x1_a")   # once each
    assert panel_ladder.load_climbed(tmp_path) == ["ep14_waterloo_3x1_a", "ep14_biology_2x2"]
    # a fresh Climb (a resume) starts with the remembered list, so CAP holds
    climb = panel_ladder.Climb(ctx=None, home=tmp_path, rebuild=lambda only=None: None,
                               redrawn=panel_ladder.load_climbed(tmp_path))
    assert len(climb.redrawn) == 2 and climb.cap == 2


def test_a_partial_content_read_merges_into_the_board_file(tmp_path):
    """A redraw re-reads ONLY its own panels (fix 2c): the partial rows land in
    panel_content.json beside the untouched rows, never wiping them."""
    board = tmp_path / "storyboard"
    board.mkdir(parents=True)
    old = [{"shot": 3, "passed": True, "faults": []}, {"shot": 5, "passed": False, "faults": ["clones"]}]
    (board / "panel_content.json").write_text(json.dumps(old), encoding="utf-8")
    merged = panel_ladder.merge_content_rows(old, [{"shot": 5, "passed": True, "faults": []},
                                                   {"shot": 7, "passed": True, "faults": []}])
    by = {r["shot"]: r for r in merged}
    assert by[3]["passed"] is True                 # untouched row kept
    assert by[5]["passed"] is True                 # re-read row replaced
    assert by[7]["passed"] is True                 # new row appended
    assert [r["shot"] for r in merged] == [3, 5, 7]
