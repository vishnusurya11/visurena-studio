"""Jekyll ep07 retro S5: a hand edit wrote 'slowly' into shot 07's motion; the Episode contract
refused it only at step 01's load, after launch (runs 11-12).  The launch preflight now loads the
plan: a contract failure is `refuse now`, and bytes that moved outside a recorded cure since the
plan's verdict are said as `will re-plan at step 02` -- never a refusal, because the take ladder's
own cures rewrite plan.json through plan_provenance.record."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from scripts.episode import drive
from studio import autopilot as ap
from studio import plan_provenance, plan_verdict

FIXTURE = Path(__file__).parent / "fixtures" / "jekyll_ep07_plan.json"


def _book(tmp_path) -> tuple[Path, Path]:
    book = tmp_path / "20990101000000_a-book"
    plan = book / "episodes" / "ep07" / "plan.json"
    plan.parent.mkdir(parents=True)
    shutil.copy(FIXTURE, plan)
    plan_verdict.verdict_path(plan).write_text(json.dumps(
        {"plan_sha8": plan_verdict.plan_sha8(plan), "verdict": "APPROVE"}), encoding="utf-8")
    return book, plan


def _edit(plan: Path, motion: str) -> None:
    doc = json.loads(plan.read_text(encoding="utf-8"))
    doc["shots"][7]["motion"] = motion
    plan.write_text(json.dumps(doc, indent=1), encoding="utf-8")


def test_a_signed_plan_says_nothing(tmp_path):
    book, _plan = _book(tmp_path)
    assert drive.plan_lines(book, 7) == []


def test_a_plan_that_fails_the_contract_refuses_now(tmp_path):
    book, plan = _book(tmp_path)
    _edit(plan, "Jekyll drifts slowly back from the sill")
    lines = drive.plan_lines(book, 7)
    assert len(lines) == 1 and lines[0].startswith("refuse now: plan.json fails the Episode contract")


def test_a_hand_edit_outside_a_cure_is_said_as_a_re_plan(tmp_path):
    book, plan = _book(tmp_path)
    _edit(plan, "Jekyll steps back one whole tread from the sill")
    assert drive.plan_lines(book, 7) == [
        "will re-plan at step 02: plan.json changed outside a recorded cure since its verdict"]


def test_a_recorded_cure_says_nothing(tmp_path):
    book, plan = _book(tmp_path)
    before = plan_verdict.plan_sha8(plan)
    _edit(plan, "Jekyll steps back one whole tread from the sill")
    plan_provenance.record(plan, before, ["gait_edit"])
    assert drive.plan_lines(book, 7) == []


def test_no_plan_yet_says_nothing(tmp_path):
    assert drive.plan_lines(tmp_path / "20990101000000_a-book", 7) == []


def test_a_contract_failure_in_the_log_parks_by_name():
    tail = ("pydantic_core._pydantic_core.ValidationError: 1 validation error for Episode\nshots.7\n"
            "  Value error, 'motion' asks for a slow shot ('slowly')")
    kind, reason, _ = ap.classify(tail, set())
    assert kind == "park" and reason.startswith("plan_contract:")
