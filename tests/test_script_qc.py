"""The finished cut, measured against the page it promised to be."""
from __future__ import annotations

import pytest

from studio import script_qc
from studio.script_qc import ScriptQC


def a_report(**kw) -> ScriptQC:
    fields = {"seconds": 53.5, "promised": 53.5,
              "shares": {"M1": 0.25, "M2": 0.45, "M3": 0.30},
              "speech": 0.30, "title_at": 0.84, "lufs": -14.1, "peak": -2.2}
    fields.update(kw)
    return ScriptQC(**fields)


def test_a_cut_that_kept_its_promises_passes():
    assert a_report().delivered and a_report().misses == []


def test_a_missing_first_act_is_named():
    """THE run 19 FAILURE, as a measurement.  It shipped M1 at 1% of 106 s and
    QC reported nothing, because nothing had said the trailer should have a
    first act at all."""
    starved = a_report(shares={"M1": 0.01, "M2": 0.61, "M3": 0.38})
    assert "act_M1" in starved.misses and not starved.delivered


def test_a_cut_that_is_not_the_page_is_named():
    """The picture drifting from the page means the cut stopped being the
    thing that was written."""
    assert "runtime" in a_report(seconds=49.0).misses


def test_a_trailer_nobody_speaks_in_is_named():
    """Run 19 measured speech at 0.115 and the owner said "no dialogues"."""
    assert "speech" in a_report(speech=0.115).misses


def test_loudness_and_peak_are_measured_on_the_master():
    assert "loudness" in a_report(lufs=-19.0).misses
    assert "peak" in a_report(peak=-0.2).misses
    assert a_report(lufs=-13.0, peak=-2.0).delivered


def test_the_title_position_is_reported_even_when_nothing_gates_it():
    """Nobody has published a measured distribution of title-card position
    over a trailer corpus, so this is recorded rather than gated -- a number
    to compare once there is something to compare it to."""
    assert a_report(title_at=0.10).delivered
    assert a_report().title_at == 0.84
