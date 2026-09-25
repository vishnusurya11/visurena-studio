"""The signers refuse an empty note, so a judge's summary always says something:
how many reads found no fault, or every fault by kind and place."""
from __future__ import annotations

from studio.judges.verdict import Fault, Verdict, summary


def test_a_clean_verdict_says_how_many_reads_found_nothing():
    v = Verdict(judge="panel_eye", version="1", passed=True, confidence=1.0, reads=23)
    assert v.summary().strip() and "23" in v.summary()


def test_a_clean_verdict_with_no_reads_still_says_something():
    v = Verdict(judge="plan", version="1", passed=True, confidence=0.0, reads=0)
    assert v.summary().strip()


def test_a_faulted_verdict_names_every_fault_by_kind_and_place():
    v = Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=3,
                faults=[Fault(kind="identity", where="T07"), Fault(kind="lag", where="T09")])
    text = summary(v)
    assert "identity" in text and "T07" in text and "lag" in text and "T09" in text


def test_a_terminal_verdict_says_which_rung_ended_it():
    v = Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=3,
                faults=[Fault(kind="lag", where="T09")], terminal="keep_best")
    assert "keep_best" in v.summary()
