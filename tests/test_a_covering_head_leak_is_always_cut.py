"""ep24 (2026-10-09 02:10Z): T02 shipped at score 0 -- 8 frames of the place
plate before its panel, read as a hard jump and an unplanned cut.  Its leak
measure said a head cut COVERS it, but the router sends a take to one cure and
the move faults claimed it first; the re-render leaked again and the free head
cut never ran.  A covering leak is cut whatever else the take is routed to.

And a QC refusal is retried before the brain is asked: the cut and take steps
re-run themselves on a refused master (a quiet cue lifted, an unjudged take
measured); the brain read ep21's and ep24's as gates that gave up."""
from __future__ import annotations

from studio import autopilot, take_ladder
from studio.judges.verdict import Fault, Verdict


def fault(kind: str, **evidence) -> Fault:
    return Fault(kind=kind, where="T02", note=kind, evidence={"hard": True, **evidence})


def test_a_covering_leak_is_cut_beside_the_move_cure(tmp_path):
    verdict = Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, faults=[
        fault("leak", covers=True), fault("jump"), fault("cut-vote")])
    routed = take_ladder.route(verdict, tmp_path / "takes" / "r2v")
    assert 2 in routed.get("head_cut", {})
    assert 2 in routed.get("move_type", {})


def test_a_leak_that_does_not_cover_gets_no_head_cut(tmp_path):
    verdict = Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, faults=[
        fault("leak", covers=False), fault("jump")])
    assert 2 not in take_ladder.route(verdict, tmp_path / "takes" / "r2v").get("head_cut", {})


def test_a_qc_refusal_is_retried_before_the_brain():
    tail = "SystemExit: REFUSED: qc FAIL in qc_r2v.json; fix the cut before anyone watches it\n"
    assert autopilot.classify(tail, set())[:2] == ("retry", "qc_fail")
