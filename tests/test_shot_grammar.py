"""Duration bounds size; a move without a destination is drift."""
from __future__ import annotations

import math

import pytest

from studio import shot_grammar
from studio.shot_grammar import (ANGLE, BOUND_FLOOR, FRAMING, LADDER, MIN_SECONDS,
                                 ladder_distance, legible_sizes, motivated_move)


class TestDurationBoundsSize:
    def test_a_short_shot_cannot_hold_a_wide(self):
        """A wide at the 85-90% trough is a flash of unread information."""
        assert "wide" not in legible_sizes(1.35)

    def test_a_long_shot_can_hold_anything(self):
        assert set(legible_sizes(7.5)) == set(LADDER)

    def test_the_smallest_sizes_survive_the_shortest_shots(self):
        assert legible_sizes(0.6) == ["insert", "extreme_close"]

    def test_a_bound_shot_never_goes_below_the_face_floor(self):
        """Binding a reference to a 2% head spends a render on no face."""
        for seconds in (0.5, 0.9, 1.35, 3.0):
            sizes = legible_sizes(seconds, bound=True)
            assert all(LADDER.index(s) >= LADDER.index(BOUND_FLOOR) for s in sizes)

    def test_every_size_has_a_minimum_and_a_phrasing(self):
        assert set(MIN_SECONDS) == set(LADDER) == set(FRAMING)


class TestOneFloor:
    def test_the_edit_floor_is_the_shortest_legible_size(self):
        """Run 3 of Scarlet died in step 06 on a 0.417 s shot: the beat walk
        allowed it (MIN_SHOT was 0.4) and the grammar refused it (the shortest
        size needs 0.5).  One number, owned here, read by the walk."""
        from studio.trailer_edit import MIN_SHOT
        assert MIN_SHOT == min(shot_grammar.MIN_SECONDS.values())

    def test_every_length_the_walk_allows_has_a_size(self):
        from studio.trailer_edit import MIN_SHOT
        for seconds in (MIN_SHOT, 0.5, 0.7, 4.0):
            assert shot_grammar.choose_sizes([seconds], [False], [0.0])


class TestLadder:
    def test_adjacent_sizes_are_one_rung_apart(self):
        assert ladder_distance("medium", "medium_close") == 1

    def test_the_worst_cut_is_detectable(self):
        """Too different to be a hold, too similar to be a new fact."""
        assert ladder_distance("medium", "medium_close") < 2

    def test_the_ladder_runs_small_to_large(self):
        assert LADDER.index("close") < LADDER.index("wide")


class TestMotivatedMovement:
    def test_a_move_names_its_destination(self):
        move = motivated_move("pushes in", "small", "slow", "she turns", "the letter")
        assert "toward the letter" in move

    def test_a_move_names_its_cause(self):
        assert motivated_move("pushes in", "small", "slow", "she turns", "x").startswith(
            "As she turns,")

    def test_an_occluder_generates_parallax(self):
        move = motivated_move("pushes in", "small", "slow", "a", "b", "the doorframe")
        assert "doorframe sliding past" in move

    def test_stillness_is_requested_positively(self):
        """H3 drifts by default, and these models have no reliable negation."""
        still = motivated_move("static", "", "", "", "")
        assert "static shot" in still and "no camera" not in still

    def test_amplitude_and_speed_survive(self):
        move = motivated_move("tracking", "large", "fast", "he runs", "the alley")
        assert "large amplitude" in move and "fast speed" in move


class TestAngleStatesConsequence:
    def test_angles_describe_what_is_visible_not_the_rig(self):
        """A caption-trained model has no grip vocabulary."""
        for phrasing in ANGLE.values():
            assert any(w in phrasing for w in
                       ("visible", "fills", "crosses", "breaking", "looks"))

    def test_no_angle_uses_bare_jargon(self):
        assert not [p for p in ANGLE.values() if p.strip().lower().startswith("low angle")]


class TestSelectionIsNotMeasuringLength:
    """The concreteness COUNT was measured at 1.10x lift once length is
    controlled -- it was ranking by word count, and it buried RACHE at 165/268."""

    def test_the_image_gate_is_boolean_not_a_count(self):
        from studio.trailer_story import IMAGE_GATE
        short = "The flame reveals RACHE, scrawled in red across the plaster."
        assert IMAGE_GATE.search(short)

    def test_the_gate_admits_words_a_handwritten_list_missed(self):
        from studio.trailer_story import IMAGE_GATE
        for word in ("flame", "match", "lens", "axe", "phial", "corpse"):
            assert IMAGE_GATE.search(f"He lifts the {word}."), word

    def test_a_line_with_no_thing_in_it_is_gated_out(self):
        from studio.trailer_story import IMAGE_GATE
        assert not IMAGE_GATE.search("Holmes considers the problem at length.")

    def test_distinctiveness_prefers_the_unusual(self):
        from studio.trailer_story import distinctiveness
        counts = {"door": 40, "rache": 1, "plaster": 1, "walks": 30}
        common = distinctiveness("He walks through the door.", counts, 100)
        rare = distinctiveness("RACHE scrawled across the plaster.", counts, 100)
        assert rare > common


class TestBothChannels:
    def test_dialogue_is_reachable_as_a_shot_candidate(self):
        """"You have been in Afghanistan" is dialogue, and the image channel
        filtered on kind == "action", so it could never be selected."""
        from studio.trailer_story import quotable_elements
        scenes = [{"number": 1, "slug": {"location_id": "x"}, "cast": ["h"],
                   "elements": [{"kind": "dialogue", "character": "h",
                                 "text": "You have been in Afghanistan, I perceive."}]}]
        assert len(quotable_elements(scenes)) == 1

    def test_near_duplicates_across_scenes_are_dropped(self):
        from studio.trailer_story import deduplicate
        same = "Measured heaps of white salt wait on glass saucers."
        elements = [{"scene": 28, "text": same}, {"scene": 32, "text": same}]
        assert len(deduplicate(elements)) == 1

    def test_distinct_lines_survive(self):
        from studio.trailer_story import deduplicate
        elements = [{"scene": 1, "text": "The door has no sign."},
                    {"scene": 2, "text": "Fog presses against the cab windows."}]
        assert len(deduplicate(elements)) == 2


class TestDynamicRangeIsNotPeak:
    """max-min looked like range and was peak, because the floor is constant."""

    def test_the_floor_does_not_decide_the_score(self):
        import numpy as np
        from studio.beatmap import dynamic_range
        body = np.concatenate([np.full(400, -40.0), np.full(400, -12.0)])
        quiet_floor = np.concatenate([body, np.full(10, -120.0)])
        loud_floor = np.concatenate([body, np.full(10, -55.0)])
        assert abs(dynamic_range(quiet_floor) - dynamic_range(loud_floor)) < 1.0

    def test_max_minus_min_would_have_been_fooled(self):
        import numpy as np
        body = np.concatenate([np.full(400, -40.0), np.full(400, -12.0)])
        quiet = np.concatenate([body, np.full(10, -120.0)])
        loud = np.concatenate([body, np.full(10, -55.0)])
        assert (quiet.max() - quiet.min()) - (loud.max() - loud.min()) > 60

    def test_a_flat_cue_scores_low(self):
        import numpy as np
        from studio.beatmap import dynamic_range
        assert dynamic_range(np.full(800, -14.0)) < 1.0

    def test_a_dynamic_cue_scores_high(self):
        import numpy as np
        from studio.beatmap import dynamic_range
        varied = np.concatenate([np.full(400, -45.0), np.full(400, -10.0)])
        assert dynamic_range(varied) > 30.0


class TestQuantisation:
    """Shots are planned in seconds and rendered in frames; they must agree."""

    def test_a_zero_timestamp_stays_zero(self):
        from studio.trailer_edit import quantise
        assert quantise(0.0) == 0.0

    def test_every_boundary_lands_on_a_frame(self):
        from studio.trailer_edit import cut_points
        grid = [1.0, 2.5, 4.0, 6.2, 9.9, 14.0, 20.5, 28.0, 35.0, 44.0]
        for point in cut_points(48.0, grid):
            assert abs(point * 24 - round(point * 24)) < 1e-9

    def test_the_planned_length_is_what_ffmpeg_will_render(self):
        """-t truncates to whole frames; 33 truncations drifted 1.28s."""
        from studio.trailer_edit import cut_points, lengths_of
        grid = [1.0, 2.5, 4.0, 6.2, 9.9, 14.0, 20.5, 28.0, 35.0, 44.0]
        for length in lengths_of(cut_points(48.0, grid)):
            frames = length * 24
            assert abs(frames - round(frames)) < 1e-6, length


def rendered_frames(arg: str, fps: int = 24) -> int:
    """What ffmpeg actually renders for `-t arg`.

    MEASURED, not assumed: `-t` keeps frames whose timestamp is below t, so
    the count is ceil(t * fps).  Verified against ffmpeg at 2.208 -> 53,
    2.2083 -> 53, 2.2292 -> 54, 1.3750 -> 33, 1.3958 -> 34.
    """
    return math.ceil(float(arg) * fps)


class TestFrameArgument:
    """`-t` rounds the picture UP to a whole frame.  Ask for the exact one."""

    def test_every_frame_count_survives_the_round_trip(self):
        from studio.trailer_assemble import frames_arg
        for n in range(1, 400):
            assert rendered_frames(frames_arg(n / 24, 24)) == n

    def test_a_fractional_length_renders_the_frames_it_rounds_to(self):
        """2.21s is 53.04 frames.  The plan must know it will get 53."""
        from studio.trailer_assemble import frames_arg
        assert rendered_frames(frames_arg(2.21, 24)) == 53

    def test_zero_stays_zero(self):
        from studio.trailer_assemble import frames_arg
        assert float(frames_arg(0.0, 24)) == 0.0


class TestSegmentStart:
    """A seek that lands mid-frame costs a frame, every time."""

    def test_the_start_is_always_on_a_frame(self):
        from studio.trailer_assemble import segment_start
        for usage in range(4):
            for need in (0.5, 1.7083, 2.2083, 3.5417):
                start = segment_start(usage, 4, need, 10.125)
                assert abs(start * 24 - round(start * 24)) < 1e-6, (usage, need, start)

    def test_the_shot_never_runs_past_the_end_of_the_take(self):
        """The last use sits flush with the end; rounding it UP truncated it."""
        from studio.trailer_assemble import segment_start
        for need in (0.5, 2.2083, 3.5417):
            assert segment_start(3, 4, need, 10.125) + need <= 10.125 + 1e-9

    def test_a_take_with_no_room_still_returns_a_usable_start(self):
        from studio.trailer_assemble import segment_start
        assert segment_start(0, 1, 10.0, 10.125) >= 0.0

    def test_uses_are_still_spread_across_the_take(self):
        from studio.trailer_assemble import segment_start
        starts = [segment_start(u, 3, 2.0, 10.125) for u in range(3)]
        assert starts[0] < starts[1] < starts[2]


class TestSeekArgument:
    """`-ss` decides which frame is FIRST, so it rounds like `-t` does."""

    def test_a_seek_never_lands_past_the_frame_it_names(self):
        from studio.trailer_assemble import frames_arg
        for n in (0, 1, 62, 187, 243):
            assert float(frames_arg(n / 24, 24)) <= n / 24 + 1e-9

    def test_the_frame_that_cost_three_shots_a_frame_each(self):
        """187/24 is 7.791666s.  Written '.3f' it becomes 7.792 -- past the
        frame -- so ffmpeg began at 188 while -t still counted from 7.792."""
        from studio.trailer_assemble import frames_arg
        assert float(frames_arg(187 / 24, 24)) <= 187 / 24
