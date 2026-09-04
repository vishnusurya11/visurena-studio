"""Ordering the slate: hook -> answer -> threat -> (title) -> button, each
line chosen for the slot it will occupy from its MEASURED seconds.

A slot is a trough in the delivered cue; a line never gets `atempo`d into
one (0.85 buys 15%; a 2.5 s line cannot enter a 1.43 s slot).  The line is
chosen for the slot instead, and a line that does not fit any slot of its
role is passed over for the next of the same function.
"""
from __future__ import annotations

import pytest

from studio.trailer_dialogue import DUCK_OVERRUN, MAX_DUCKS, fits, names_figure, order_lines, speech_seconds
from studio.trailer_stage_spec import SlateLine, Slot

BEAT = 0.5


def line(text, function, speaker="sherlock_holmes", score=1.0, **kw):
    return SlateLine(text=text, speaker=speaker, function=function, pool="screenplay",
                     score=score, **kw)


AFGHAN = line("You have been in Afghanistan, I perceive.", "hook")
EASIER = line("It was easier to perceive it than to explain it.", "exposition", "john_watson")
DEATH = line("There is death in one and life in the other.", "threat")
HOPE_THREAT = line("There is a great deal of blood on my hands.", "threat", "jefferson_hope")
NO_DATA = line("No data yet.", "button")
FERRIER = line("I guess you are the daughter of John Ferrier.", "stakes", "jefferson_hope")
NAMES = line("Jefferson Hope did this to us all.", "stakes", "john_watson")
WATSON_KNOWS = line("I perceive nothing of what you perceive.", "stakes", "john_watson")


def slots(*seconds):
    out, start = [], 10.0
    for s in seconds:
        out.append(Slot(start=start, end=start + s))
        start += s + 4.0
    return out


class TestFit:
    def test_a_line_occupies_whole_beats_inside_the_slot(self):
        """Starts on beat 2, ends a beat before the return: a 4-beat slot
        holds a 2-beat line and not a 3-beat one."""
        slot = Slot(start=0.0, end=2.0)
        assert fits(0.9, slot, BEAT)
        assert not fits(1.2, slot, BEAT)

    def test_without_a_grid_the_slot_is_the_seconds(self):
        assert fits(1.9, Slot(start=0.0, end=2.0), None)
        assert not fits(2.1, Slot(start=0.0, end=2.0), None)

    def test_a_line_may_overrun_a_rubato_slot_by_one_release(self):
        """Scarlet run 6: slots of 2.6 and 2.0 s, the best hook 3.3 s, three
        runs of music_only.  The bed's mid band ducks under every line for as
        long as it runs (08-assemble), so a line may end after the trough by
        up to the ducker's release; it is a duck, and ducks are budgeted."""
        assert DUCK_OVERRUN == 1.0 and MAX_DUCKS == 2
        assert fits(3.3, Slot(start=0.0, end=2.6), None, overrun=DUCK_OVERRUN)
        assert not fits(3.7, Slot(start=0.0, end=2.6), None, overrun=DUCK_OVERRUN)

    def test_on_a_metre_grid_the_return_downbeat_is_never_crossed(self):
        assert not fits(1.2, Slot(start=0.0, end=2.0), BEAT, overrun=DUCK_OVERRUN)


class TestOrder:
    def test_order_is_hook_answer_threat_button(self):
        slate = order_lines([DEATH, NO_DATA, EASIER, AFGHAN], slots(6, 6, 6, 6), "jefferson_hope",
                            beat=BEAT)
        assert [l.function for l in slate.lines] == ["hook", "exposition", "threat", "button"]
        assert slate.lines[0].text == AFGHAN.text

    def test_order_refuses_slate_without_hook(self):
        with pytest.raises(ValueError, match="hook"):
            order_lines([EASIER, DEATH, NO_DATA], slots(6, 6, 6), "jefferson_hope", beat=BEAT)

    def test_order_refuses_a_hook_with_nothing_after_it(self):
        with pytest.raises(ValueError):
            order_lines([AFGHAN, NO_DATA], slots(6, 6), "jefferson_hope", beat=BEAT)

    def test_the_answer_comes_from_another_speaker_and_relates(self):
        """Watson's line shares 'perceive' with Holmes's hook; Hope's does not,
        and Hope's ranks higher."""
        slate = order_lines([AFGHAN, FERRIER, WATSON_KNOWS, DEATH], slots(6, 6, 6),
                            "jefferson_hope", beat=BEAT)
        assert slate.lines[1].text == WATSON_KNOWS.text

    def test_the_threat_prefers_the_figure(self):
        slate = order_lines([AFGHAN, DEATH, HOPE_THREAT], slots(6, 6), "jefferson_hope", beat=BEAT)
        assert slate.lines[1].speaker == "jefferson_hope"

    def test_lines_are_capped_by_slots(self):
        """Two slots: the second must be the threat, not the exposition."""
        slate = order_lines([AFGHAN, EASIER, DEATH, NO_DATA], slots(6, 6), "x", beat=BEAT)
        assert len(slate.lines) == 2
        assert [l.function for l in slate.lines] == ["hook", "threat"] or \
            [l.function for l in slate.lines] == ["hook", "exposition"]


class TestMeasured:
    def test_line_chosen_for_slot_from_measured_seconds(self):
        """The predicted 3.3 s hook fits the 5 s slot (7 usable beats); measured
        at 4.1 s it does not, and the next hook is chosen instead."""
        short_hook = line("How are you?", "hook")
        assert speech_seconds(AFGHAN.text) <= 3.5
        measured = {AFGHAN.text: 4.1}
        slate = order_lines([AFGHAN, short_hook, DEATH], slots(5, 6), "x", beat=BEAT,
                            measured=measured)
        assert slate.lines[0].text == short_hook.text
        unmeasured = order_lines([AFGHAN, short_hook, DEATH], slots(5, 6), "x", beat=BEAT)
        assert unmeasured.lines[0].text == AFGHAN.text

    def test_a_line_is_never_stretched_into_a_slot(self):
        with pytest.raises(ValueError):
            order_lines([AFGHAN, DEATH], slots(1.5, 1.5), "x", beat=BEAT)


class TestDucks:
    RACHE = line("Rache, revenge.", "threat", "jefferson_hope")

    def test_run_6_hook_overruns_its_trough_and_the_threat_sits_inside_its_own(self):
        assert 2.6 < speech_seconds(AFGHAN.text) <= 2.6 + DUCK_OVERRUN
        slate = order_lines([AFGHAN, self.RACHE], slots(2.6, 2.0), "jefferson_hope", beat=None)
        assert [l.text for l in slate.lines] == [AFGHAN.text, self.RACHE.text]

    def test_at_most_two_lines_overrun(self):
        """Hook and answer each spend a duck; a threat that would need a third
        is passed over, and the slate is refused for want of one."""
        long_threat = line("There is a great deal of blood on my hands tonight.", "threat")
        assert all(speech_seconds(l.text) > 2.6 for l in (AFGHAN, EASIER, long_threat))
        with pytest.raises(ValueError):
            order_lines([AFGHAN, EASIER, long_threat], slots(2.6, 2.6, 2.6), "x", beat=None)
        slate = order_lines([AFGHAN, EASIER, long_threat, self.RACHE], slots(2.6, 2.6, 2.6), "x",
                            beat=None)
        assert [l.text for l in slate.lines] == [AFGHAN.text, EASIER.text, self.RACHE.text]


class TestFigure:
    def test_line_naming_the_figure_is_refused(self):
        assert names_figure(NAMES.text, "jefferson_hope")
        assert not names_figure(HOPE_THREAT.text, "jefferson_hope")
        slate = order_lines([AFGHAN, NAMES, WATSON_KNOWS, DEATH], slots(6, 6, 6), "jefferson_hope",
                            beat=BEAT)
        assert all(not names_figure(l.text, "jefferson_hope") for l in slate.lines)
        assert NAMES.text not in [l.text for l in slate.lines]

    def test_a_lower_case_common_word_is_not_a_name(self):
        assert not names_figure("I hope you are right.", "jefferson_hope")
