"""The trailer contract's two promises: identity is bound, music owns time."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from studio.trailer_spec import MusicBed, RefSheet, ShotSpec, TrailerBeat, TrailerPlan


def shot(**kw) -> ShotSpec:
    base = dict(beat_id="b1", index=0, start=0.0, seconds=2.0)
    return ShotSpec(**{**base, **kw})


class TestRefSheet:
    def test_character_ref_id_must_be_prefixed(self):
        with pytest.raises(ValidationError, match="must start with 'char-'"):
            RefSheet(ref_id="holmes", kind="character", name="Holmes", prompt="p")

    def test_location_ref_id_must_be_prefixed(self):
        with pytest.raises(ValidationError, match="must start with 'loc-'"):
            RefSheet(ref_id="char-lab", kind="location", name="Lab", prompt="p")

    def test_well_formed_ref_survives(self):
        r = RefSheet(ref_id="char-holmes", kind="character", name="Holmes", prompt="p")
        assert r.rel_path is None


class TestIdentityBinding:
    """The bug that made the first trailer: cast on screen, no ref carried."""

    def test_shot_with_uncarried_cast_is_not_bound(self):
        s = shot(cast=["holmes", "watson"], char_refs={"holmes": "char-holmes"})
        assert not s.bound()
        assert s.unbound_cast() == ["watson"]

    def test_shot_carrying_every_character_is_bound(self):
        s = shot(cast=["holmes"], char_refs={"holmes": "char-holmes"})
        assert s.bound()
        assert s.unbound_cast() == []

    def test_empty_cast_is_trivially_bound(self):
        assert shot(cast=[]).bound()

    def test_refs_for_absent_characters_do_not_bind_present_ones(self):
        """A ref count that happens to match is not evidence of binding."""
        s = shot(cast=["holmes"], char_refs={"watson": "char-watson"})
        assert not s.bound()
        assert s.unbound_cast() == ["holmes"]

    def test_ref_slots_put_characters_before_place(self):
        s = shot(cast=["holmes"], char_refs={"holmes": "char-holmes"}, loc_ref="loc-lab")
        assert s.ref_slots() == ["char-holmes", "loc-lab"]

    def test_plan_reports_every_unbound_shot(self):
        p = TrailerPlan(
            trailer_id="t", book_id="b", title="T",
            shots=[shot(index=0, cast=["holmes"]),
                   shot(index=1, beat_id="b2", cast=["watson"], char_refs={"watson": "char-watson"})],
        )
        assert [s.index for s in p.unbound_shots()] == [0]


class TestMusicOwnsTime:
    def test_cuts_must_increase(self):
        with pytest.raises(ValidationError, match="strictly increase"):
            MusicBed(rel_path="m.flac", seconds=60.0, sections=6, cuts=[1.0, 3.0, 2.0])

    def test_cut_past_the_end_is_rejected(self):
        with pytest.raises(ValidationError, match="past bed end"):
            MusicBed(rel_path="m.flac", seconds=10.0, sections=2, cuts=[4.0, 11.0])

    def test_a_bed_with_no_cuts_is_legal(self):
        assert MusicBed(rel_path="m.flac", seconds=10.0, sections=2).cuts == []


class TestBeatSubjects:
    def test_a_beat_carries_who_its_shot_names_apart_from_who_it_is_bound_to(self):
        beat = TrailerBeat(beat_id="b", scene_number=13, arc="hit", location_id="utah",
                           cast=["john_ferrier"], subjects=["john_ferrier", "lucy_ferrier"],
                           image_prompt="p", motion="m")
        assert beat.subjects == ["john_ferrier", "lucy_ferrier"]
        assert TrailerBeat(beat_id="b", scene_number=1, arc="hit", location_id="l",
                           image_prompt="p", motion="m").subjects == []


class TestBeatTraceability:
    def test_a_line_without_a_speaker_is_rejected(self):
        with pytest.raises(ValidationError, match="a line needs a speaker"):
            TrailerBeat(beat_id="b", scene_number=1, arc="hit", location_id="l",
                        image_prompt="p", motion="m", line="You have been in Afghanistan.")

    def test_speaker_must_be_in_cast(self):
        with pytest.raises(ValidationError, match="not in cast"):
            TrailerBeat(beat_id="b", scene_number=1, arc="hit", location_id="l",
                        cast=["watson"], image_prompt="p", motion="m",
                        line="Quite so.", speaker="holmes")

    def test_beat_points_back_into_the_screenplay(self):
        with pytest.raises(ValidationError):
            TrailerBeat(beat_id="b", scene_number=0, arc="quiet", location_id="l",
                        image_prompt="p", motion="m")


class TestOneAspectRatio:
    def test_dimensions_off_the_canvas_grid_are_rejected(self):
        with pytest.raises(ValidationError, match="would render 1280x768"):
            TrailerPlan(trailer_id="t", book_id="b", title="T", width=1288, height=768)

    def test_default_plan_is_native_canvas(self):
        p = TrailerPlan(trailer_id="t", book_id="b", title="T")
        assert p.width % 32 == 0 and p.height % 32 == 0
        assert (p.width, p.height) == (1344, 768)


class TestOneTakeOneShot:
    """Run 10 played every one of its 25 takes twice and B00 three times.
    The owner's rule -- a rendered take is never seen twice -- is a property
    of the plan alone, so the plan cannot be built that way."""

    def test_a_beat_used_twice_is_refused(self):
        with pytest.raises(ValidationError, match="one take, one shot"):
            TrailerPlan(trailer_id="t", book_id="b", title="T",
                        shots=[shot(index=0), shot(index=1, start=2.0)])

    def test_a_shot_each_is_accepted(self):
        p = TrailerPlan(trailer_id="t", book_id="b", title="T",
                        shots=[shot(index=0), shot(index=1, beat_id="b2", start=2.0)])
        assert len(p.shots) == 2
