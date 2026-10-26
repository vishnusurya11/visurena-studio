"""The cure ledger: plan.cures.jsonl records every mechanical write's
from->to sha8, and `chain` answers whether a plan's bytes moved ONLY through
recorded cures.  A gap -- a hand edit nobody recorded -- breaks the chain,
which fails safe: the critic reads once (ep18: a clean mechanical cure lapsed
the signature and step 02 re-entered the paid climb, $1.05)."""
from __future__ import annotations

import json

from studio import plan_provenance, plan_verdict


def write_plan_bytes(plan, doc):
    plan.write_text(json.dumps(doc), encoding="utf-8")
    return plan_verdict.plan_sha8(plan)


def test_two_recorded_rounds_chain_their_cure_names_in_order(tmp_path):
    plan = tmp_path / "plan.json"
    signed = write_plan_bytes(plan, {"v": 1})
    before = signed
    write_plan_bytes(plan, {"v": 2})
    plan_provenance.record(plan, before, ["holds", "renumber"])
    before = plan_verdict.plan_sha8(plan)
    write_plan_bytes(plan, {"v": 3})
    plan_provenance.record(plan, before, ["clamp_beds"])
    got = plan_provenance.chain(tmp_path, signed, plan_verdict.plan_sha8(plan))
    assert got == ["holds", "renumber", "clamp_beds"]


def test_a_hand_edit_between_rounds_breaks_the_chain(tmp_path):
    plan = tmp_path / "plan.json"
    signed = write_plan_bytes(plan, {"v": 1})
    before = signed
    write_plan_bytes(plan, {"v": 2})
    plan_provenance.record(plan, before, ["holds"])
    write_plan_bytes(plan, {"v": "hand-edited"})                    # nobody recorded this write
    before = plan_verdict.plan_sha8(plan)
    write_plan_bytes(plan, {"v": 3})
    plan_provenance.record(plan, before, ["renumber"])
    assert plan_provenance.chain(tmp_path, signed, plan_verdict.plan_sha8(plan)) is None


def test_identical_sha8s_are_an_empty_chain(tmp_path):
    assert plan_provenance.chain(tmp_path, "aaaa1111", "aaaa1111") == []


def test_no_ledger_at_all_is_no_chain(tmp_path):
    assert plan_provenance.chain(tmp_path, "aaaa1111", "bbbb2222") is None
    assert plan_provenance.rows(tmp_path) == []


def test_rows_skips_blank_and_broken_lines(tmp_path):
    (tmp_path / plan_provenance.CURES_FILE).write_text(
        '{"from_sha8": "a", "to_sha8": "b", "cures": ["holds"]}\n\nnot json\n', encoding="utf-8")
    assert plan_provenance.rows(tmp_path) == [{"from_sha8": "a", "to_sha8": "b", "cures": ["holds"]}]


def test_the_ledger_lives_beside_the_plan(tmp_path):
    plan = tmp_path / "plan.json"
    assert plan_provenance.cures_path(plan) == tmp_path / "plan.cures.jsonl"


def test_no_op_rounds_and_a_replayed_older_row_do_not_break_the_chain(tmp_path):
    """Jekyll ep02, 2026-10-26: five cure rounds that moved no bytes (from == to) and a
    second climb that replayed the older draft's row (e09 -> 653) sat between the
    signature and a recorded owner-order write, and the walker read them as a write
    nobody recorded -- so a recorded fix could never be re-signed."""
    plan = tmp_path / "plan.json"
    older = write_plan_bytes(plan, {"v": 0})
    signed = write_plan_bytes(plan, {"v": 1})
    ledger = tmp_path / plan_provenance.CURES_FILE
    rows = [{"from_sha8": older, "to_sha8": signed, "cures": ["strip_amounts"]},
            {"from_sha8": signed, "to_sha8": signed, "cures": ["strip_amounts"]},
            {"from_sha8": older, "to_sha8": signed, "cures": ["lock_two_shot"]},
            {"from_sha8": signed, "to_sha8": signed, "cures": ["lock_two_shot"]}]
    ledger.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    write_plan_bytes(plan, {"v": 2})
    plan_provenance.record(plan, signed, ["owner_order_shot9"])
    assert plan_provenance.chain(tmp_path, signed, plan_verdict.plan_sha8(plan)) == ["owner_order_shot9"]


def test_an_unrecorded_write_after_no_op_rounds_still_breaks_the_chain(tmp_path):
    plan = tmp_path / "plan.json"
    signed = write_plan_bytes(plan, {"v": 1})
    plan_provenance.record(plan, signed, ["holds"])                  # a round that moved nothing
    write_plan_bytes(plan, {"v": "hand-edited"})                    # nobody recorded this write
    assert plan_provenance.chain(tmp_path, signed, plan_verdict.plan_sha8(plan)) is None
