"""`Verdict.confidence` is the share of reads that were readable: a count,
never a feeling.  It lives in [0, 1]; no reads is no confidence."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from studio.judges import verdict as jv


def test_confidence_is_readable_over_reads():
    assert jv.confidence(3, 4) == 0.75
    assert jv.confidence(4, 4) == 1.0


def test_no_reads_is_no_confidence():
    assert jv.confidence(0, 0) == 0.0


def test_more_readable_than_read_is_refused():
    with pytest.raises(ValueError):
        jv.confidence(5, 4)


def test_the_model_holds_the_bounds():
    with pytest.raises(ValidationError):
        jv.Verdict(judge="x", version="1", passed=True, confidence=1.5)
    with pytest.raises(ValidationError):
        jv.Verdict(judge="x", version="1", passed=True, confidence=-0.1)


def test_the_signer_names_judge_and_version():
    v = jv.Verdict(judge="take_eye", version="2", passed=True, confidence=1.0, reads=3)
    assert v.signer == "judge:take_eye@2" == jv.signer("take_eye", "2")
