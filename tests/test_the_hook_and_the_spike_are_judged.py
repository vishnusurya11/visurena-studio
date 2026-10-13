"""The plan judge rewards drama, not breadth (Jekyll ep01 review, 2026-10-13).

The episode opened on 15 s of character sketch because the judge asked every
row to be "shown or told" in order -- a `nonscene` row of habits included --
and the chapter's spike (Hyde tramples the child) was told, never shown.  The
critic now LISTS the chapter's threat and its key event with the shots that
show them and the lines that tell them; code judges:

- G-HOOK: the opening shot or the opening line carries the threat;
- G-SPIKE: the key event is shown by at least one shot, not only told;
- a `nonscene` row may be folded away without a fault.  $0, canned readings."""
from __future__ import annotations

from studio.judges import plan as pj
from tests.plan_reader_fixtures import BRIEF, plan, reading


def _with(base, **fields):
    return base.model_copy(update={k: pj.__dict__[cls].model_validate(v) for k, (cls, v) in fields.items()})


def _threat(shots, lines, span="the door"):
    return ("Threat", {"span": span, "shots": shots, "lines": lines})


def _spike(shots, lines, span="he took the cup from her hand"):
    return ("Spike", {"span": span, "shots": shots, "lines": lines})


def test_an_old_reading_without_threat_or_spike_still_loads_and_faults_nothing_new():
    good = reading("good")
    assert good.threat.span == "" and good.spike.span == ""
    assert pj.hook_faults([good]) == [] and pj.spike_faults([good]) == []


def test_an_opening_that_carries_no_threat_is_a_hook_fault():
    read = _with(reading("good"), threat=_threat([5], [6]))
    got = pj.hook_faults([read] * 3)
    assert len(got) == 1 and got[0].kind == "story" and "G-HOOK" in got[0].note


def test_an_opening_shot_or_line_on_the_threat_passes():
    assert pj.hook_faults([_with(reading("good"), threat=_threat([0], []))] * 3) == []
    assert pj.hook_faults([_with(reading("good"), threat=_threat([], [0]))] * 3) == []


def test_a_spike_told_only_by_lines_is_a_spike_fault():
    read = _with(reading("good"), spike=_spike([], [9]))
    got = pj.spike_faults([read] * 3)
    assert len(got) == 1 and "G-SPIKE" in got[0].note


def test_a_spike_shown_in_a_shot_passes():
    assert pj.spike_faults([_with(reading("good"), spike=_spike([10], [9]))] * 3) == []


def test_one_reading_of_three_is_no_majority():
    told = _with(reading("good"), spike=_spike([], [9]))
    shown = _with(reading("good"), spike=_spike([10], [9]))
    assert pj.spike_faults([told, shown, shown]) == []


def test_a_nonscene_row_may_be_folded_without_a_fault():
    brief = {**BRIEF, "scenes": [{"n": 1, "type": "nonscene", "summary": "The narrator describes his habits."},
                                 *BRIEF["scenes"]]}
    read = reading("good")
    read = read.model_copy(update={"coverage": [c.model_copy(update={"event": c.event + 1}) for c in read.coverage]})
    assert pj.foldable(brief) == {0}
    v = pj.judge(plan("known_good"), brief, [read] * 3)
    assert not [f for f in v.faults if f.kind == "coverage"]
