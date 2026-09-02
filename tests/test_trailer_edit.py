"""The cut: variety, shape, and landing on the music."""
from __future__ import annotations

from studio.beatmap import IMPACT_DB, STOPDOWN_DB
from studio.trailer_assemble import segment_start
from studio.trailer_cut import FINAL_HOLD, is_uniform, target_length
from studio.trailer_edit import MIN_SHOT, cut_points, lengths_of, snap

GRID = [1.0, 2.5, 4.0, 6.2, 9.9, 14.0, 20.5, 28.0, 35.0, 44.0, 55.0, 61.0, 70.0, 78.0]


class TestSnapping:
    def test_a_cut_moves_onto_a_near_onset(self):
        assert snap(2.4, GRID) == 2.5

    def test_a_cut_far_from_any_onset_stays_put(self):
        assert snap(50.0, GRID) == 50.0

    def test_an_empty_grid_leaves_every_cut_alone(self):
        assert snap(3.7, []) == 3.7


class TestTheArc:
    def test_the_opening_shot_is_the_longest_of_the_opening(self):
        assert target_length(0.02) > target_length(0.12)

    def test_there_is_a_breath_a_third_of_the_way_in(self):
        assert target_length(0.32) > target_length(0.22)

    def test_the_climax_is_the_fastest_cutting(self):
        assert target_length(0.87) == min(target_length(p / 100) for p in range(100))

    def test_the_cut_decelerates_into_the_title(self):
        assert target_length(0.97) > target_length(0.87)


class TestCutPoints:
    def test_shot_lengths_are_never_uniform(self):
        lengths = lengths_of(cut_points(80.0, GRID))
        assert not is_uniform(lengths)

    def test_no_shot_is_a_flash_frame(self):
        assert all(x >= MIN_SHOT for x in lengths_of(cut_points(80.0, GRID)))

    def test_the_cut_covers_exactly_the_span_asked_for(self):
        points = cut_points(80.0, GRID)
        assert points[0] == 0.0 and points[-1] == 80.0

    def test_a_longer_stretch_yields_fewer_shots(self):
        few = cut_points(80.0, GRID, stretch=3.0)
        many = cut_points(80.0, GRID, stretch=1.0)
        assert len(few) < len(many)

    def test_boundaries_strictly_increase(self):
        points = cut_points(80.0, GRID)
        assert all(b > a for a, b in zip(points, points[1:]))


class TestReuseShowsDifferentMoments:
    def test_three_uses_of_one_take_start_in_three_places(self):
        starts = [segment_start(u, 3, 2.5, 10.1) for u in range(3)]
        assert len(set(starts)) == 3

    def test_a_single_use_takes_from_the_middle_of_the_take(self):
        """Not the head -- the head is the animated reference sheet."""
        from studio.trailer_assemble import HEAD_TRIM
        start = segment_start(0, 1, 2.5, 10.1)
        assert HEAD_TRIM <= start <= 10.1 - 2.5

    def test_a_take_with_no_room_does_not_seek_past_its_end(self):
        assert segment_start(2, 3, 10.0, 10.0) == 0.0


class TestDetectionThresholds:
    def test_a_stopdown_is_a_bigger_move_than_an_impact(self):
        """Asymmetric on purpose: a hit is a spike, a stopdown is a floor."""
        assert STOPDOWN_DB > IMPACT_DB

    def test_the_final_hold_outlasts_every_arc_target(self):
        assert FINAL_HOLD > max(target_length(p / 100) for p in range(100))


class TestSheetLanguageNeverReachesAShot:
    """A shot prompt describes a person in a place, not a photograph of them."""

    def test_a_sheet_prompt_is_rejected(self):
        from studio.trailer_refs import character_prompt
        from studio.trailer_shot import is_scene_safe
        sheet = character_prompt("A tall lean man, hawk-nosed.", "Muted London grey.")
        assert not is_scene_safe(sheet)

    def test_a_plain_physical_description_passes(self):
        from studio.trailer_shot import is_scene_safe
        assert is_scene_safe("A tall lean man of about thirty, thin hawk-like nose.")

    def test_the_shot_prompt_built_from_a_sheet_prompt_is_caught(self):
        """The exact bug: the sheet prompt reaching shot_prompt unnoticed."""
        from studio.trailer_refs import character_prompt
        from studio.trailer_shot import is_scene_safe, shot_prompt
        sheet = character_prompt("A small wiry man.", "Fog and gaslight.")
        built = shot_prompt("Style.", [sheet], "a lane", "He turns.", "hit", 2.0)
        assert not is_scene_safe(built)


class TestHeadTrim:
    """H3 r2v opens on the reference sheet; no shot may come from there."""

    def test_no_use_starts_inside_the_reference_leak(self):
        from studio.trailer_assemble import HEAD_TRIM, segment_start
        starts = [segment_start(u, 3, 2.5, 10.12) for u in range(3)]
        assert all(s >= HEAD_TRIM for s in starts)

    def test_a_single_use_also_clears_the_leak(self):
        from studio.trailer_assemble import HEAD_TRIM, segment_start
        assert segment_start(0, 1, 2.5, 10.12) >= HEAD_TRIM

    def test_uses_still_show_different_moments(self):
        from studio.trailer_assemble import segment_start
        assert len({segment_start(u, 3, 2.0, 10.12) for u in range(3)}) == 3

    def test_a_take_too_short_to_trim_does_not_seek_past_its_end(self):
        from studio.trailer_assemble import segment_start
        assert segment_start(0, 1, 3.0, 3.0) == 0.0
