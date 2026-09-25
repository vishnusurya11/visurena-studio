"""A judge's `n` carries `flagged_by` and `evidence` and clears eye_review's
refusals on that; `waived_because` is never written by a judge, and a rubric a
person answered is never written over."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.episode import eye_review as er
from studio.judges import master_eye as me
from studio.judges.verdict import Fault, Verdict

DIGEST = "abc12345"


def flagged_board() -> Verdict:
    return Verdict(judge="master_eye", version="1", passed=False, confidence=1.0, reads=30,
                   faults=[Fault(kind="board", where="master",
                                 evidence={"off": {2: 0.075, 4: 0.09}, "share": 0.5, "wall": {"cell": 0.5}})])


def test_an_n_is_flagged_with_evidence_and_no_waiver():
    doc = me.rubric(flagged_board(), DIGEST)
    cell = doc["rubric"]["board"]
    assert cell["answer"] == "n" and cell["flagged_by"] == "judge:master_eye@1"
    assert cell["evidence"]["off"] == {2: 0.075, 4: 0.09}
    assert all(c["waived_because"] == "" for c in doc["rubric"].values())
    assert er.waivers(doc) == {}
    assert er.flags(doc) == {"board": {"flagged_by": "judge:master_eye@1", "evidence": cell["evidence"]}}
    assert er.refusals(doc, DIGEST, Path("review/eye_abc12345.json")) == []


def test_a_bare_n_would_not_clear_so_the_flag_is_what_clears():
    doc = me.rubric(flagged_board(), DIGEST)
    del doc["rubric"]["board"]["flagged_by"]
    out = er.refusals(doc, DIGEST, Path("review/eye_abc12345.json"))
    assert len(out) == 1 and "board" in out[0]


def test_the_judge_writes_its_rubric_but_never_over_a_persons(tmp_path):
    path = me.write_rubric(tmp_path, DIGEST, flagged_board(), master="master_r2v.mp4")
    assert path == tmp_path / "review" / f"eye_{DIGEST}.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["sha8"] == DIGEST and doc["master"] == "master_r2v.mp4" and doc["rubric"]["board"]["answer"] == "n"
    owner = er.blank_rubric(DIGEST, "master_r2v.mp4", "c.png", 5.0, 30)
    owner["rubric"]["shadow"]["answer"] = "y"
    owner["reviewed_by"] = "owner"
    path.write_text(json.dumps(owner), encoding="utf-8")
    me.write_rubric(tmp_path, DIGEST, flagged_board())
    assert json.loads(path.read_text(encoding="utf-8")) == owner


def test_a_blank_rubric_is_written_over(tmp_path):
    blank = er.blank_rubric(DIGEST, "m", "c", 5.0, 30)
    er.write_blank(er.rubric_path(tmp_path, DIGEST), blank)
    path = me.write_rubric(tmp_path, DIGEST, flagged_board())
    assert json.loads(path.read_text(encoding="utf-8"))["reviewed_by"] == "judge:master_eye@1"
