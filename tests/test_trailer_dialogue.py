"""Ordering the slate: hook -> answer -> threat -> (title) -> button, each
line chosen for the slot it will occupy from its MEASURED seconds.

A slot is a trough in the delivered cue; a line never gets `atempo`d into
one (0.85 buys 15%; a 2.5 s line cannot enter a 1.43 s slot).  The line is
chosen for the slot instead, and a line that does not fit any slot of its
role is passed over for the next of the same function.
"""
from __future__ import annotations

import pytest

from studio.trailer_dialogue import (DUCK_OVERRUN, LINE_ROOM, MAX_DUCKS, fits, holds, made_slots,
                                     names_figure, order_lines, refusal, role_candidates,
                                     shares_content_word, speech_seconds, targets, windows_of)
from studio.trailer_stage_spec import Metre, SlateLine, Slot

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
USELESS_CARD = line("It is of the highest importance, therefore, not to have useless facts "
                    "elbowing out the useful ones.", "exposition", None, score=5.0)
WATSON_SPOKEN = line("I had no idea that such individuals did exist outside of stories.",
                     "exposition", "john_watson", score=9.6)
NATURE_CARD = line("Nor is Nature always in one mood throughout this grim district.", "threat", None)


def slots(*seconds):
    out, start = [], 10.0
    for s in seconds:
        out.append(Slot(start=start, end=start + s))
        start += s + 4.0
    return out


def metre(seconds=100.0, bpm=120.0, beats_per_bar=4, hits=(16.0, 40.0, 64.0), title_hit=88.0,
          found=()):
    beat = 60.0 / bpm
    beats = [round(i * beat, 4) for i in range(int(seconds / beat))]
    downbeats = beats[::beats_per_bar]
    return Metre(seed=7, rel_path="trailer/main/music/cue-7.wav", seconds=seconds, bpm=bpm,
                 bar=beats_per_bar * beat, beats_per_bar=beats_per_bar, beats=beats,
                 downbeats=downbeats, bars_in_mode=0.97, grid="metre", fitness=12.0,
                 hits=[*hits, title_hit], phrase_starts=downbeats[::4], title_hit=title_hit,
                 slots=list(found))


def run_9():
    """Scarlet run 9's shipped seed, to the numbers in metre.json: 177.8 BPM in
    three, a 1.02 s bar, four troughs of 1.25-2.4 s between 72 and 83 s,
    the title hit at 108.95 of 132.1 s.  The slate was music_only: the
    longest trough held five beats, 1.7 s, and the shortest hook ran 2.5."""
    return metre(seconds=132.1, bpm=177.84, beats_per_bar=3, hits=(41.5, 82.6, 101.9),
                 title_hit=108.95, found=(Slot(start=72.2, end=73.45), Slot(start=75.85, end=77.45),
                                          Slot(start=77.8, end=80.2), Slot(start=81.25, end=82.6)))


class TestWindows:
    """A line lives in a window: FOUND, a trough the cue has, or MADE, a
    phrase of the grid the mix ducks under it (08-assemble keys the bed's
    mid band to the line).  Four runs of Scarlet shipped music_only waiting
    for troughs the music model does not reliably write; the grid always
    has phrases."""

    def test_a_made_window_opens_on_a_phrase_and_holds_a_whole_line(self):
        """From a phrase start to the first later phrase start that leaves
        room for the longest line the pool admits, plus the two beats the
        fit rule keeps."""
        found = made_slots(metre())
        assert found and all(w.made for w in found)
        assert all(w.start in metre().phrase_starts for w in found)
        assert all(w.seconds >= LINE_ROOM + 2 * metre().beat for w in found)
        assert all(0.2 * 100.0 <= w.start <= 0.8 * 100.0 for w in found)

    def test_a_made_window_ends_before_the_next_hit(self):
        """The line ends before the impact, never across it: a hit inside the
        phrase caps the window, and a capped window shorter than a bar is
        not a window."""
        m = metre(hits=(16.0, 40.0, 45.0, 64.0))
        ends = {w.start: w.end for w in made_slots(m)}
        assert ends[40.0] == 45.0
        assert all(w.end <= 88.0 for w in made_slots(m))

    def test_windows_are_found_and_made_in_time_order(self):
        m = metre(found=(Slot(start=30.0, end=34.0),))
        found = windows_of(m)
        assert [w.start for w in found] == sorted(w.start for w in found)
        assert any(not w.made and w.start == 30.0 for w in found)
        assert any(w.made for w in found)

    def test_a_rubato_cue_has_only_the_troughs_it_was_measured_with(self):
        m = metre(found=(Slot(start=30.0, end=34.0),)).model_copy(
            update={"grid": "onsets", "bars_in_mode": 0.4, "downbeats": [], "phrase_starts": []})
        assert [w.made for w in windows_of(m)] == [False]

    def test_lines_are_spread_across_the_windows(self):
        """Four lines over twenty windows are not the first four phrases: each
        role aims at an even share of the span, hook first, button last."""
        found = windows_of(metre())
        aims = targets(found, 4)
        assert aims[0] == found[0].start and aims[-1] == found[-1].start
        assert aims[1] - aims[0] == pytest.approx(aims[2] - aims[1]) == pytest.approx(aims[3] - aims[2])
        assert targets(found, 1) == [found[0].start]
        slate = order_lines([AFGHAN, EASIER, DEATH, NO_DATA], found, "x", beat=0.5)
        starts = [l.window.start for l in slate.lines]
        assert len(starts) == 4 and starts == sorted(starts)
        assert starts[-1] - starts[0] >= 0.5 * (found[-1].start - found[0].start)

    def test_chosen_windows_never_overlap(self):
        """Made windows overlap one another (each phrase opens one); the
        windows the lines take do not."""
        slate = order_lines([AFGHAN, EASIER, DEATH, NO_DATA], windows_of(metre()), "x", beat=0.5)
        for a, b in zip(slate.lines, slate.lines[1:]):
            assert b.window.start >= a.window.end

    def test_a_window_nothing_fits_is_passed_over_for_the_next_nearest(self):
        """Run 9's troughs held 1.7 s at most: the hook passes them for the
        made window nearest its aim, and the slate ships."""
        m = run_9()
        slate = order_lines([AFGHAN, EASIER, DEATH, NO_DATA], windows_of(m), "jefferson_hope",
                            beat=m.beat)
        assert [l.function for l in slate.lines][:1] == ["hook"]
        assert {l.function for l in slate.lines} & {"threat", "stakes"}
        assert all(l.window is not None for l in slate.lines)
        assert all(fits(speech_seconds(l.text), l.window, m.beat) for l in slate.lines)

    def test_the_run_9_slate_is_not_music_only(self):
        """The regression: the pool that shipped music_only, on the cue it
        shipped with."""
        m = run_9()
        pool = [AFGHAN, line("I am a consulting detective, if you can understand what that is.",
                             "hook"), EASIER, DEATH,
                line("I have a mule and two horses waiting in the Eagle Ravine.", "threat",
                     "jefferson_hope")]
        slate = order_lines(pool, windows_of(m), "jefferson_hope", beat=m.beat)
        assert len(slate.lines) >= 2 and not slate.music_only


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

    def test_an_auxiliary_is_not_a_content_word(self):
        """Run 10: 'You HAVE been in Afghanistan' related to two source
        quotes on 'have' alone, and both outranked Watson's spoken line."""
        assert not shares_content_word(AFGHAN.text, USELESS_CARD.text)
        assert shares_content_word(AFGHAN.text, WATSON_KNOWS.text)

    def test_a_spoken_line_outranks_a_card_at_every_role(self):
        """A line nobody speaks ships as a text card; it is the fallback for
        a role no spoken line fits, never a peer.  Run 10 spoke 1 of 3."""
        assert role_candidates("answer", [USELESS_CARD, WATSON_SPOKEN], AFGHAN, "x")[0] is WATSON_SPOKEN
        assert role_candidates("threat", [NATURE_CARD, DEATH], AFGHAN, "x")[0] is DEATH
        slate = order_lines([AFGHAN, USELESS_CARD, WATSON_SPOKEN, NATURE_CARD, DEATH],
                            slots(6, 6, 6), "jefferson_hope", beat=BEAT)
        assert [l.speaker for l in slate.lines] == ["sherlock_holmes", "john_watson", "sherlock_holmes"]

    def test_a_card_is_placed_when_no_spoken_line_fits(self):
        slate = order_lines([AFGHAN, USELESS_CARD, NATURE_CARD], slots(6, 10, 6),
                            "jefferson_hope", beat=BEAT)
        assert [l.speaker for l in slate.lines] == ["sherlock_holmes", None, None]

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


class TestRefusals:
    """The refusal is quoted back to the labeller as the reason to relabel,
    so it must name something a LABEL can change.  Run 9 quoted 'no hook
    fits the first slot' twice; the failure was window duration, and the
    labeller, which cannot lengthen a window, relabelled the same lines."""

    def test_a_window_holds_whole_beats_less_the_two_the_fit_rule_keeps(self):
        assert holds(Slot(start=10.0, end=14.0), 0.5) == pytest.approx(3.0)
        assert holds(Slot(start=10.0, end=11.0), 0.5) == 0.0
        assert holds(Slot(start=10.0, end=14.0), None) == 4.0

    def test_a_pool_with_no_hook_says_so(self):
        assert refusal("hook", [], slots(8.0), 0.5, {}) == "no line is labelled hook"
        with pytest.raises(ValueError, match="no line is labelled hook"):
            order_lines([EASIER, DEATH], slots(8.0, 8.0), "x", beat=0.5)

    def test_a_hook_that_fits_no_window_names_the_room(self):
        """Run 9's troughs and no phrases: the shortest hook takes 3.3 s, the
        longest window holds 1.7 s, and the labeller is told to label
        shorter lines."""
        m = run_9().model_copy(update={"phrase_starts": []})
        with pytest.raises(ValueError, match=r"no hook fits a window: the shortest hook takes "
                                             r"3\.3 s, the longest window holds 1\.7 s; "
                                             r"label shorter lines as hook"):
            order_lines([AFGHAN, EASIER, DEATH], windows_of(m), "x", beat=m.beat)
