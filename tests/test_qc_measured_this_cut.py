"""The QC report has to be about the cut you are uploading.

THIS HAPPENED, 2026-09-13, and no gate could see it:

    19:43  master_iter5.mp4 written                    sha8 f5ddd2a3
    19:49  qc_r2v.json written  -- measured f5ddd2a3
    20:02  master_iter6.mp4 / master_r2v.mp4 written   sha8 f8bf7814
    20:04  uploaded to YouTube, public                 sha8 f8bf7814

A take was swapped and the master re-cut, and the publish ladder read a report
that had never seen the file it was clearing.  Had that report said PASS, an
unmeasured cut would have gone public with no override at all.

The fix is not another judgement.  `already` is the model: a FACT, with no
override, because waiving a fact only records a falsehood.  Whether the report
describes this file is the same kind of thing -- you cannot waive a measurement
you did not take.
"""
import pytest

from studio import youtube_publish as yp


def refuse(**kw):
    base = dict(qc={"passed": True, "sha8": "f8bf7814"}, dq_failed=[], privacy="private",
                watched="", digest="f8bf7814", already=None, audited=False, override="")
    return yp.refusals(**(base | kw))


def said(out):
    return " | ".join(out)


def test_a_report_that_measured_this_cut_is_accepted():
    assert refuse() == []


def test_a_report_that_measured_a_DIFFERENT_cut_refuses():
    """The exact ep03 shape: the report is about f5ddd2a3, the file is f8bf7814."""
    out = refuse(qc={"passed": True, "sha8": "f5ddd2a3"})
    assert out and "f5ddd2a3" in said(out)


def test_the_refusal_names_both_hashes_so_it_can_be_acted_on():
    out = said(refuse(qc={"passed": True, "sha8": "f5ddd2a3"}))
    assert "f5ddd2a3" in out and "f8bf7814" in out


def test_an_override_cannot_waive_it():
    """An override covers the two QUALITY judgements. This is not a judgement --
    it is the absence of a measurement, and a waiver would record a falsehood."""
    out = refuse(qc={"passed": True, "sha8": "f5ddd2a3"},
                 override="owner watched it and said ship it")
    assert out


def test_a_report_with_no_sha8_at_all_refuses():
    """Every report written before this rule existed. Re-running qc is free."""
    out = refuse(qc={"passed": True})
    assert out and "sha8" in said(out).lower()


def test_the_quality_gates_are_untouched_by_this_rule():
    """A stale-report refusal must not mask or replace the existing ladder."""
    out = said(refuse(qc={"passed": False, "sha8": "f8bf7814"}))
    assert "passed:false" in out
