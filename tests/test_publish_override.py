"""A human who WATCHED it may knowingly ship a cut the machine gates refuse.

Episode 2 iteration 3: `qc.passed` is false on 4 missing cuts and 7 of 19 takes
fail cut-landing, and the owner watched the file and said ship it.  Both of
those gates answer "is this the best cut we could make", and the owner is the
only one who can answer "is this good enough to show strangers".

So the override is REAL but NARROW:

  * it covers the QUALITY gates only -- qc.passed and the DQ roll-up
  * it never covers `already uploaded`: that is not a judgement, it is a fact,
    and overriding it puts a second copy on the channel
  * it never covers `--watched` or `--audited`: those ARE the human, and an
    override that waived them would be a human waiving himself
  * it requires a REASON, recorded in the ledger, because an override nobody
    can read afterwards is indistinguishable from a bug
"""
from studio import youtube_publish as yp

DIRTY = dict(qc={"passed": False}, dq_failed=["T00", "T05", "T08"], privacy="public",
             watched="abc12345", digest="abc12345", already=None, audited=True)


def test_without_an_override_the_quality_gates_refuse():
    out = yp.refusals(**DIRTY)
    assert any("passed:false" in r for r in out)
    assert any("takes failed DQ" in r for r in out)


def test_an_override_clears_the_quality_gates():
    assert yp.refusals(**DIRTY, override="owner watched it, POC") == []


def test_an_override_never_clears_an_already_uploaded_master():
    """Not a judgement -- a fact. Overriding it puts a second copy on the channel."""
    out = yp.refusals(**{**DIRTY, "already": {"video_id": "abc", "at": "2026-09-13"}},
                      override="ship it")
    assert any("already uploaded as abc" in r for r in out)


def test_an_override_never_stands_in_for_the_human():
    """--watched and --audited ARE the human; an override cannot waive them."""
    out = yp.refusals(**{**DIRTY, "watched": ""}, override="ship it")
    assert any("watch the file" in r for r in out)
    out = yp.refusals(**{**DIRTY, "audited": False}, override="ship it")
    assert any("forces private" in r for r in out)


def test_a_blank_override_is_no_override():
    """An override with no reason is a silenced gate, which is a bug in disguise."""
    assert yp.refusals(**DIRTY, override="   ") != []


def test_the_clean_path_is_unchanged():
    clean = dict(qc={"passed": True}, dq_failed=[], privacy="private",
                 watched="abc12345", digest="abc12345", already=None)
    assert yp.refusals(**clean) == []


def test_the_overrides_are_reported_for_the_ledger():
    """What was waived has to be readable afterwards."""
    waived = yp.waived({"passed": False}, ["T00", "T05"], override="owner watched it")
    assert waived["reason"] == "owner watched it"
    assert waived["qc_passed"] is False
    assert waived["dq_failed"] == ["T00", "T05"]
    assert yp.waived({"passed": True}, [], override="") is None
