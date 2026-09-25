"""The master rubric: a judge answers `n` and FLAGS it -- `flagged_by` and the
evidence beside the answer.  A waiver stays the owner's word; an `n` with
neither clears nothing.  Flags ride into the upload ledger beside the waivers."""
from __future__ import annotations

from scripts.episode import eye_review as er
from studio import youtube_publish as yp

DIGEST = "abc12345"
PATH = "review/eye_abc12345.json"


def filled(answers=None, *, flagged=None, waived=None) -> dict:
    rubric = er.blank_rubric(DIGEST, "master.mp4", f"contact_{DIGEST}.png", 5.0, 24)
    for field, _q in er.RUBRIC:
        cell = rubric["rubric"][field]
        cell["answer"] = (answers or {}).get(field, "y")
        cell["waived_because"] = (waived or {}).get(field, "")
        if field in (flagged or {}):
            cell["flagged_by"], cell["evidence"] = flagged[field]
    rubric["notes"] = "measured, not watched"
    return rubric


FLAG = ("judge:master_eye@1", {"p5_luma": 16.5, "wall": 8})


def test_an_n_carrying_a_judge_flag_clears():
    rubric = filled({"shadow": "n"}, flagged={"shadow": FLAG})
    assert er.refusals(rubric, DIGEST, PATH) == []
    assert er.flags(rubric) == {"shadow": {"flagged_by": FLAG[0], "evidence": FLAG[1]}}
    assert er.waivers(rubric) == {}


def test_an_n_with_neither_a_waiver_nor_a_flag_does_not():
    out = er.refusals(filled({"board": "n"}), DIGEST, PATH)
    assert len(out) == 1 and "board" in out[0]


def test_a_flag_without_evidence_is_a_feeling_not_a_flag():
    rubric = filled({"board": "n"}, flagged={"board": ("judge:master_eye@1", {})})
    assert er.flags(rubric) == {}
    assert er.refusals(rubric, DIGEST, PATH) != []


def test_a_flag_beside_a_y_is_not_a_flag():
    assert er.flags(filled(flagged={"story": FLAG})) == {}


def test_the_ledger_carries_flags_beside_waivers():
    eye = yp.eye_record(DIGEST, "judge:master_eye@1",
                        waived={}, flags={"shadow": {"flagged_by": FLAG[0], "evidence": FLAG[1]}})
    assert eye["waived"] == {} and eye["flags"]["shadow"]["flagged_by"] == "judge:master_eye@1"
    assert eye["sha8"] == DIGEST and eye["reviewed_by"] == "judge:master_eye@1"
