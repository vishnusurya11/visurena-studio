"""A flagged verdict is a signature: the next step runs on it.  The flag rides in
the file (the audit sheet finds it); the unit never parks on it."""
from __future__ import annotations

import json

from pathlib import Path

from studio import eye_verdict as ev, plan_verdict, refs_verdict

ROOT = Path(__file__).resolve().parents[1]


def _pictures(folder):
    folder.mkdir(parents=True, exist_ok=True)
    p = folder / "shot_01.png"
    p.write_bytes(b"\x01" * 8)
    return [p]


def test_a_flagged_eye_verdict_passes_and_require_returns_it(tmp_path):
    pics = _pictures(tmp_path / "storyboard")
    ev.sign(tmp_path / "storyboard", pics, "flagged", "clones at shot_01",
            signed_by="judge:panel_eye@1", faults=[{"kind": "clones", "where": "shot_01"}],
            terminal="keep_best")
    assert ev.passed(tmp_path / "storyboard", pics)
    got = ev.require(tmp_path / "storyboard", pics, "EYE", "look")
    assert got["verdict"] == "flagged" and got["signed_by"] == "judge:panel_eye@1"


def test_a_flagged_plan_verdict_is_current(tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text('{"a": 1}', encoding="utf-8")
    out = plan_verdict.sign(plan, "story fault kept best", signed_by="judge:plan@1",
                            faults=[{"kind": "story", "where": "turn"}], flagged=True)
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["verdict"] == "APPROVE" and doc["flagged"] is True
    assert doc["signed_by"] == "judge:plan@1" and doc["faults"][0]["kind"] == "story"
    assert plan_verdict.current(plan)


def test_a_judged_pack_with_faults_listed_is_current(tmp_path):
    book = tmp_path / "book"
    (book / "refs").mkdir(parents=True)
    (book / "refs" / "pack.jsonl").write_text('{"path": "refs/x.png"}\n', encoding="utf-8")
    refs_verdict.sign(book, "style outlier flagged", signed_by="judge:look@1",
                      faults=[{"kind": "style", "where": "refs/x.png"}])
    got = refs_verdict.current(book)
    assert got and got["signed_by"] == "judge:look@1" and got["faults"][0]["kind"] == "style"


def test_a_board_the_eye_kept_flagged_is_not_a_park_for_the_takes(tmp_path):
    """ep14 (2026-09-30): the panel eye climbed its ladder and signed keep_best
    flagged over lettered station panels; panel_content.json still said 'shots
    [5, 8, 9] failed' and step 09 refused -- an owner-waiver park the 2026-09-24
    decision forbids.  With a CURRENT eye signature the machine's failed rows
    are the judge's recorded faults, not a wall; a MISSING or stale verdict
    still refuses."""
    import json
    from PIL import Image
    from scripts.episode import step_08_panels as step
    from studio import eye_verdict
    from studio.judges.verdict import Fault, Verdict
    home = tmp_path
    board = home / "storyboard"
    board.mkdir()
    (home / "plan.json").write_text(json.dumps(
        {"shots": [{"index": 0}, {"index": 1}]}), encoding="utf-8")
    for i in (0, 1):
        Image.new("RGB", (8, 8), (i, 0, 0)).save(board / f"shot_{i:02d}.png")
    rows = [{"shot": 0, "passed": True}, {"shot": 1, "passed": False}]
    for name in ("panel_dq.json", "panel_content.json"):
        (board / name).write_text(json.dumps(rows), encoding="utf-8")
    assert any("failed the panel gate" in why for why in step.panel_refusals(home))
    flagged = Verdict(judge="panel_eye", version="1", passed=False, confidence=1.0, reads=2,
                      terminal="keep_best", faults=[Fault(kind="lettering", where="shot_01")])
    eye_verdict.sign_verdict(board, step.panels_of(board), flagged)
    assert step.panel_refusals(home) == []
    (board / "shot_01.png").write_bytes(b"changed")           # the verdict is about other bytes
    assert step.panel_refusals(home) != []


def test_the_take_builder_honours_the_same_signature(tmp_path, monkeypatch):
    """takes_r2v carries its own copy of the panel wall; it reads the eye too."""
    import json
    import sys
    from PIL import Image
    from studio import eye_verdict
    from studio.judges.verdict import Fault, Verdict
    sys.path.insert(0, str(ROOT / "scripts" / "episode"))
    import takes_r2v
    board = tmp_path / "storyboard"
    board.mkdir()
    for i in (0, 1):
        Image.new("RGB", (8, 8), (i, 0, 0)).save(board / f"shot_{i:02d}.png")
    rows = [{"shot": 0, "passed": True}, {"shot": 1, "passed": False}]
    for name in ("panel_dq.json", "panel_content.json"):
        (board / name).write_text(json.dumps(rows), encoding="utf-8")

    class Shot:
        index = 0
    class Ep:
        shots = [Shot(), type("S1", (), {"index": 1})()]
    monkeypatch.setattr(takes_r2v.episode_home, "home", lambda book, number: tmp_path)
    import pytest
    with pytest.raises(SystemExit, match="failed the panel gate"):
        takes_r2v.refuse_failed_panels(tmp_path, 14, Ep())
    flagged = Verdict(judge="panel_eye", version="1", passed=False, confidence=1.0, reads=2,
                      terminal="keep_best", faults=[Fault(kind="lettering", where="shot_01")])
    eye_verdict.sign_verdict(board, sorted(board.glob("shot_*.png")), flagged)
    takes_r2v.refuse_failed_panels(tmp_path, 14, Ep())
