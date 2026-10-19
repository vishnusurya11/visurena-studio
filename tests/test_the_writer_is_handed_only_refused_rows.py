"""A printed line is not a fault (Jekyll ep01 Kawajiri, 2026-10-18).  The plan battery printed 65
lines holding 20 real detail rows; each line became a Fault, so `near` could never fire and the
writer's REFUSED block was mostly clean headers.  `real_rows` keeps the detail lines under a
refusing header and the CONTRACT lines, nothing else.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from studio import plan_ladder  # noqa: E402

FIX = Path(__file__).parent / "fixtures" / "ep01_replay" / "P01"


def printout() -> list[str]:
    return (FIX / "round1_printout.txt").read_text(encoding="utf-8").splitlines()


def test_the_round_one_printout_is_65_lines_and_20_real_rows():
    verdict = plan_ladder.battery_verdict(printout())
    rows = plan_ladder.real_rows(verdict)
    assert len(printout()) == 65 and len(verdict.faults) == 65
    assert len(rows) == 20


def test_no_header_no_clean_line_and_no_duplicate_crowd_list_reaches_the_writer():
    rows = plan_ladder.real_rows(plan_ladder.battery_verdict(printout()))
    assert not any(r.endswith(": clean") or r.startswith(("VERDICT", "CONTRACT OK", "EXPECTS TEXT")) for r in rows)
    assert not any(r.startswith("G-CROWD      :") for r in rows)
    assert sum("G-CROWD shot" in r for r in rows) == 2


def test_the_writer_prompt_lines_are_the_real_rows():
    verdict = plan_ladder.battery_verdict(printout())
    assert plan_ladder.refusal_lines_of(verdict) == plan_ladder.real_rows(verdict)
    assert len(printout()) - len(plan_ladder.refusal_lines_of(verdict)) >= 40


def test_a_contract_refusal_is_a_row_and_contract_ok_is_not():
    lines = ["CONTRACT OK: Story | 3 shots", "CONTRACT shot 4: the cast is empty"]
    assert plan_ladder.real_rows(plan_ladder.battery_verdict(lines)) == ["CONTRACT shot 4: the cast is empty"]


def test_a_refusal_with_no_printout_header_is_kept_whole():
    verdict = plan_ladder.battery_verdict(["MONEY: the wall refused the call"])
    assert plan_ladder.real_rows(verdict) == ["MONEY: the wall refused the call"]


def one_row_printout() -> list[str]:
    return ["CONTRACT OK: Story | 3 shots", "G-LIGHT      : clean", "GRAMMAR      : 1",
            "    G-TWO shot 26: a two-person reaction is a locked medium two-shot",
            "CAST BOUND   : all bound", "VERDICT      : REFUSED"]


def test_a_one_row_printout_is_near_and_the_rung_edits_the_draft(tmp_path):
    from tests.test_a_climb_that_moves_no_row_stops import desk_with_plan
    desk, writer = desk_with_plan(tmp_path)
    verdict = plan_ladder.battery_verdict(one_row_printout())
    assert len(verdict.faults) > plan_ladder.CONVERGED
    desk.take(plan_ladder.Rung(plan_ladder.MODEL_TIER, 1.0), 0, verdict)
    assert writer.calls and writer.calls[0]["previous"] is not None


def test_judged_only_and_tier_one_still_answer_on_the_same_printout():
    verdict = plan_ladder.battery_verdict(printout())
    assert plan_ladder.tier_one(verdict) == []
    assert plan_ladder.judged_only(verdict) is True
    with_cast = plan_ladder.battery_verdict(printout()[:-1] + ["CAST BOUND   : ['poole']", "VERDICT      : REFUSED"])
    assert plan_ladder.tier_one(with_cast) == ["CAST BOUND   : ['poole']"]
    assert plan_ladder.judged_only(with_cast) is False


def test_tier_one_left_reads_the_header_from_a_signature():
    from studio import plan_tags
    assert plan_tags.builder_lines(printout()) == []
