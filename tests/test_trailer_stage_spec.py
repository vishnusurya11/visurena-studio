"""The contracts the ten trailer steps hand each other.

The pydantic model IS the spec: a step's output that does not validate is a
failed step, and a gate the blueprint names is a validator here when it is a
property of the artifact alone.
"""
import math

import pytest
from pydantic import ValidationError

from studio.trailer_music import PINNED_DURATION
from studio.trailer_stage_spec import (
    MAX_LINES, CueCut, SPEECH_CEILING_PER_100S, LineSlate, Metre, QCReport, SlateLine, Slot, StorySpec, syllables)


def story(**over):
    base = dict(lead="holmes", figure="hope", turn_scene=12, resolution_scenes=[20, 21, 22],
                restricted_scenes=[22], narrator="watson", register="detective",
                thesis=None)
    base.update(over)
    return StorySpec(**base)


class TestThesis:
    def test_syllables_counts_vowel_groups(self):
        assert syllables("nobody is who they say") == 7

    def test_seven_syllables_is_the_ceiling(self):
        story(thesis="nobody is who they say")
        with pytest.raises(ValidationError):
            story(thesis="nobody is ever who they say they are")

    def test_a_proper_noun_is_refused(self):
        with pytest.raises(ValidationError):
            story(thesis="the truth about Holmes")

    def test_sentence_initial_capital_is_not_a_proper_noun(self):
        story(thesis="Nobody is who they say")

    def test_past_tense_is_refused(self):
        with pytest.raises(ValidationError):
            story(thesis="nobody was who they said")


class TestVocalEligibility:
    def test_needs_thesis_and_a_vocal_register(self):
        assert not story().vocal_eligible()
        assert not story(register="gothic").vocal_eligible()
        assert not story(thesis="the dead keep their own").vocal_eligible()
        assert story(register="gothic", thesis="the dead keep their own").vocal_eligible()

    def test_register_is_an_enum_not_prose(self):
        with pytest.raises(ValidationError):
            story(register="moody and atmospheric")


class TestMetre:
    def metre(self, **over):
        base = dict(seed=1, rel_path="trailer/music/cue-1.flac", seconds=100.0, bpm=88.0,
                    bar=2.72, beats=[0.0, 0.68, 1.36, 2.04, 2.72], downbeats=[0.0, 2.72],
                    bars_in_mode=0.9, grid="metre", fitness=10.0,
                    slots=[Slot(start=40.0, end=45.0)])
        base.update(over)
        return Metre(**base)

    def test_beats_must_increase(self):
        with pytest.raises(ValidationError):
            self.metre(beats=[0.0, 0.5, 0.4])

    def test_downbeats_are_a_subset_of_beats(self):
        with pytest.raises(ValidationError):
            self.metre(downbeats=[0.0, 2.7])

    def test_a_rubato_cue_is_on_the_onset_grid(self):
        with pytest.raises(ValidationError):
            self.metre(bars_in_mode=0.4, grid="metre")

    def test_beat_seconds(self):
        assert self.metre().beat == 0.68

    def test_a_slot_shorter_than_a_bar_is_refused(self):
        with pytest.raises(ValidationError):
            self.metre(slots=[Slot(start=40.0, end=41.0)])


def line(**over):
    base = dict(text="You have been in Afghanistan, I perceive", speaker="holmes",
                function="hook", kept=True, bold=False, pool="screenplay", score=9.1)
    base.update(over)
    return SlateLine(**base)


class TestSlate:
    def test_needs_a_hook_and_a_threat_or_stakes(self):
        LineSlate(lines=[line(), line(function="threat", text="There is death in one")],
                  iconicity="full")
        with pytest.raises(ValidationError):
            LineSlate(lines=[line(), line(text="No data yet", function="button")],
                      iconicity="full")

    def test_music_only_is_the_empty_slate(self):
        slate = LineSlate(lines=[], iconicity="thin", music_only=True)
        assert slate.spoken() == []

    def test_a_line_without_a_speaker_is_a_card(self):
        assert line(speaker=None).card
        assert not line().card

    def test_the_ceiling_is_a_dialogue_led_cue_at_the_pinned_length(self):
        """12 lines per 100 s is the top of the dialogue-led norm; the cue is
        pinned at 108 s.  Run 10's ceiling of 4 sat under the story spine's
        own floor of 5 per 100 s, so the floor could never be met."""
        assert MAX_LINES == math.ceil(SPEECH_CEILING_PER_100S * PINNED_DURATION / 100) == 13
        full = [line()] * (MAX_LINES - 1) + [line(function="threat")]
        LineSlate(lines=full, iconicity="full")
        with pytest.raises(ValidationError):
            LineSlate(lines=full + [line(function="threat")], iconicity="full")

    def test_the_pool_survives_a_round_trip_and_is_not_spoken(self):
        slate = LineSlate(lines=[line(), line(function="threat", text="There is death in one")],
                          iconicity="full", pool=[line(text="Come along.", function="button")])
        again = LineSlate.model_validate_json(slate.model_dump_json())
        assert [l.text for l in again.pool] == ["Come along."]
        assert len(again.spoken()) == 2


class TestQC:
    def test_floor_is_derived_from_the_measurements(self):
        report = QCReport(cuts=40, cuts_on_beat=0.9, cuts_on_downbeat=0.5, cuts_on_L0=1.0,
                          on_cap_fraction=0.0, title_on_downbeat=True,
                          integrated_lufs=-14.2, true_peak=-1.1, unbound_shots=0,
                          cue_cut=cue_report().cue_cut)
        assert report.floor_pass and report.flags == []

    def test_targets_missed_become_flags_not_failures(self):
        report = QCReport(cuts=35, cuts_on_beat=0.34, cuts_on_downbeat=0.11, cuts_on_L0=0.75,
                          on_cap_fraction=0.23, title_on_downbeat=False,
                          integrated_lufs=-14.0, true_peak=-1.2, unbound_shots=0,
                          music_only_fraction=0.92, peak_position=0.53,
                          act3_over_act2_lu=-2.0)
        assert report.floor_pass
        assert "on_cap_fraction" not in report.flags  # the walk's grader, retired with it
        assert {"cuts_on_downbeat", "cuts_on_L0", "title_on_downbeat",
                "music_only_fraction", "peak_position", "act3_over_act2_lu"} <= set(report.flags)

    def test_the_whole_trailer_beat_lock_is_not_a_target_any_more(self):
        """0.80 on-beat across the whole trailer is what made a music video:
        76% of run 10's cuts were on the beat and the viewer starts counting
        within four shots.  The per-act pair replaces it, pulling opposite
        ways -- loose in act 1, locked in act 3."""
        report = QCReport(cuts=35, cuts_on_beat=0.34, cuts_on_downbeat=0.5, cuts_on_L0=1.0,
                          on_cap_fraction=0.0, title_on_downbeat=True,
                          integrated_lufs=-14.0, true_peak=-1.2, unbound_shots=0,
                          cuts_on_beat_by_act=[0.2, 0.4, 0.9], cue_cut=cue_report().cue_cut)
        assert report.flags == []
        loose = report.model_copy(update={"cuts_on_beat_by_act": [0.9, 0.4, 0.3]})
        assert loose.flags == ["cuts_on_beat_act3"]  # act 1 is the cue's to loosen now

    def test_an_unmeasured_cue_cut_is_flagged_and_never_passed(self):
        """A master QC has not measured against its cue is not known to be
        cut to it; the report says so instead of assuming a pass."""
        report = QCReport(cuts=40, cuts_on_beat=0.9, cuts_on_downbeat=0.5, cuts_on_L0=1.0,
                          on_cap_fraction=0.0, title_on_downbeat=True,
                          integrated_lufs=-14.2, true_peak=-1.1, unbound_shots=0)
        assert report.cue_cut is None and "cue_cut" in report.flags

    def test_a_section_change_the_picture_missed_fails_the_floor(self):
        """Run 10's section boundary at 43.0 s sat inside shot B17."""
        report = cue_report(section_changes_cut=0.8)
        assert not report.floor_pass and "section_changes_cut" in report.flags

    def test_a_cut_inside_a_sustain_fails_the_floor(self):
        report = cue_report(cuts_inside_sustain=1)
        assert not report.floor_pass and "cuts_inside_sustain" in report.flags

    def test_a_long_shot_off_a_sustain_and_a_line_out_of_its_trough_fail_the_floor(self):
        assert not cue_report(long_shots_on_sustains=0.5).floor_pass
        assert not cue_report(lines_in_troughs=0.0).floor_pass

    def test_cuts_off_the_events_are_a_flag_not_a_failure(self):
        report = cue_report(cuts_on_events=0.6)
        assert report.floor_pass and report.flags == ["cuts_on_events"]

    def test_a_cut_made_to_its_cue_passes_clean(self):
        report = cue_report()
        assert report.floor_pass and report.flags == []
        assert report.cue_cut.frames_played_fraction == 0.5

    def test_a_clipped_line_is_damage_and_fails_the_floor(self):
        """Run 10 levelled its only line +11.8 dB with no ceiling anywhere in
        the chain and every gate passed the result."""
        report = QCReport(cuts=40, cuts_on_beat=0.9, cuts_on_downbeat=0.5, cuts_on_L0=1.0,
                          on_cap_fraction=0.0, title_on_downbeat=True,
                          integrated_lufs=-14.2, true_peak=-1.1, unbound_shots=0,
                          line_tp=[0.0], line_flat_factor=[24.2])
        assert not report.floor_pass and not report.lines_are_clean

    def test_a_bed_that_faded_into_the_card_fails_the_floor(self):
        report = QCReport(cuts=40, cuts_on_beat=0.9, cuts_on_downbeat=0.5, cuts_on_L0=1.0,
                          on_cap_fraction=0.0, title_on_downbeat=True,
                          integrated_lufs=-14.2, true_peak=-1.1, unbound_shots=0,
                          hard_out=False)
        assert not report.floor_pass

    def test_loudness_outside_the_floor_fails(self):
        report = QCReport(cuts=40, cuts_on_beat=0.9, cuts_on_downbeat=0.5, cuts_on_L0=1.0,
                          on_cap_fraction=0.0, title_on_downbeat=True,
                          integrated_lufs=-18.0, true_peak=-1.1, unbound_shots=0)
        assert not report.floor_pass

    def test_a_repeated_take_fails_the_floor(self):
        """The owner's rule, measured on the delivered master: run 10 played
        25 takes over 51 shots and no gate said a word."""
        report = QCReport(cuts=40, cuts_on_beat=0.9, cuts_on_downbeat=0.5, cuts_on_L0=1.0,
                          on_cap_fraction=0.0, title_on_downbeat=True,
                          integrated_lufs=-14.2, true_peak=-1.1, unbound_shots=0,
                          reused_shots=26)
        assert not report.floor_pass and "reused_shots" in report.flags

    def test_a_shot_cut_from_a_stale_clip_fails_the_floor(self):
        """24% of run 10's picture came from clips of earlier plans."""
        report = QCReport(cuts=40, cuts_on_beat=0.9, cuts_on_downbeat=0.5, cuts_on_L0=1.0,
                          on_cap_fraction=0.0, title_on_downbeat=True,
                          integrated_lufs=-14.2, true_peak=-1.1, unbound_shots=0,
                          stale_shots=12)
        assert not report.floor_pass and "stale_shots" in report.flags


class TestWindows:
    def test_a_slot_is_found_unless_made(self):
        """A trough the cue has is found; a phrase the mix ducks is made."""
        assert Slot(start=1.0, end=4.0).made is False
        assert Slot(start=1.0, end=4.0, made=True).made is True

    def test_a_slate_line_carries_the_window_it_was_chosen_for(self):
        line = SlateLine(text="No data yet.", speaker="sherlock_holmes", function="button",
                         pool="screenplay", score=1.0)
        assert line.window is None
        placed = line.model_copy(update={"window": Slot(start=30.0, end=38.0, made=True)})
        assert placed.window.start == 30.0
        assert SlateLine.model_validate_json(placed.model_dump_json()).window == placed.window

def cue_report(**cue) -> QCReport:
    """A report whose every other measurement passes, so one cue field decides."""
    fields = dict(cuts_on_events=0.95, section_changes_cut=1.0, cuts_inside_sustain=0,
                  long_shots_on_sustains=1.0, lines_in_troughs=1.0, accents_cut=0.9,
                  movement_medians_s=[3.2, 1.9, 1.1], frames_rendered=2000, frames_played=1000)
    fields.update(cue)
    return QCReport(cuts=40, cuts_on_beat=0.9, cuts_on_downbeat=0.5, cuts_on_L0=1.0,
                    on_cap_fraction=0.0, title_on_downbeat=True, integrated_lufs=-14.2,
                    true_peak=-1.1, unbound_shots=0, cue_cut=CueCut(**fields))
