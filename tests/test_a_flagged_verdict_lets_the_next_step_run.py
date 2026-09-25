"""A flagged verdict is a signature: the next step runs on it.  The flag rides in
the file (the audit sheet finds it); the unit never parks on it."""
from __future__ import annotations

import json

from studio import eye_verdict as ev, plan_verdict, refs_verdict


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
