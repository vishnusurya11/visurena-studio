"""The contracts the ten trailer steps hand each other.

The pydantic model IS the spec: a step's output that does not validate is a
failed step, and a gate the blueprint names is a validator here when it is a
property of the artifact alone.
"""
import pytest
from pydantic import ValidationError

from studio.trailer_stage_spec import (
    LineSlate, Metre, QCReport, SlateLine, Slot, StorySpec, syllables)


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

    def test_at_most_four_lines(self):
        with pytest.raises(ValidationError):
            LineSlate(lines=[line()] * 4 + [line(function="threat")], iconicity="full")


class TestQC:
    def test_floor_is_derived_from_the_measurements(self):
        report = QCReport(cuts=40, cuts_on_beat=0.9, cuts_on_downbeat=0.5, cuts_on_L0=1.0,
                          on_cap_fraction=0.0, title_on_downbeat=True,
                          integrated_lufs=-14.2, true_peak=-1.1, unbound_shots=0)
        assert report.floor_pass and report.flags == []

    def test_targets_missed_become_flags_not_failures(self):
        report = QCReport(cuts=35, cuts_on_beat=0.34, cuts_on_downbeat=0.11, cuts_on_L0=0.75,
                          on_cap_fraction=0.23, title_on_downbeat=False,
                          integrated_lufs=-14.0, true_peak=-1.2, unbound_shots=0)
        assert report.floor_pass
        assert {"cuts_on_beat", "cuts_on_downbeat", "cuts_on_L0", "on_cap_fraction",
                "title_on_downbeat"} <= set(report.flags)

    def test_loudness_outside_the_floor_fails(self):
        report = QCReport(cuts=40, cuts_on_beat=0.9, cuts_on_downbeat=0.5, cuts_on_L0=1.0,
                          on_cap_fraction=0.0, title_on_downbeat=True,
                          integrated_lufs=-18.0, true_peak=-1.1, unbound_shots=0)
        assert not report.floor_pass
