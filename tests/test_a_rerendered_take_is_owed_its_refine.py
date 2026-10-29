"""The refine's one round per take (owner 2026-10-18) is one round per take BYTES.

Jekyll ep05 repair (2026-10-28): Jekyll was redrawn and T03, T06, T08, T10, T15, T17, T18 and T22
were rendered anew, but each had spent its one refine on the OLD bytes; `refined_out` counted it,
`pending` returned [] and the new faces would have shipped unrefined (the ep01 soft-faces class).
A decision recorded for other bytes refunds its round, like a STALE row's."""
from scripts.episode import face_refine as f


def test_a_decision_on_other_bytes_refunds_its_round():
    assert f.refund_of({"status": "refined", "take_sha8": "e7205b04"}, current="9fa669e0") == 1


def test_a_decision_on_these_bytes_refunds_nothing():
    assert f.refund_of({"status": "refined", "take_sha8": "9fa669e0"}, current="9fa669e0") == 0


def test_a_stale_row_still_refunds():
    assert f.refund_of({"status": next(iter(f.STALE)), "take_sha8": "x"}, current="x") == 1


def test_no_entry_refunds_nothing():
    assert f.refund_of(None, current="x") == 0
