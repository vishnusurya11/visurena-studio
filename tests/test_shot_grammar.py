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
        """Run 3 of Scarlet died in step 06 on a 0.417 s shot: the edit floor
        allowed it (MIN_SHOT was 0.4) and the grammar refused it (the shortest
        size needs 0.5).  One number, owned here, read by the cue plan."""
        from studio.trailer_edit import MIN_SHOT
        assert MIN_SHOT == min(shot_grammar.MIN_SECONDS.values())

    def test_every_length_the_floor_allows_has_a_size(self):
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


# --- the grammar per span kind -------------------------------------------------
#
# The cue's measured spans ARE the shot list (docs/analysis/research/
# trailer-music-first.md section 5).  Each kind fills its span in one way, and
# the ShotGrammar contract refuses the fill that breaks its rule.

from pydantic import ValidationError

from studio.cue_plan import CueSpan
from studio.shot_grammar import (FINAL_SECOND, STATIC, ShotGrammar, grammar_for, one_move,
                                 size_for, speaker_mode_for, timed_actions, widest)
from studio.trailer_spec import ShotSpec, TimedAction

BAR = 2.0
TEXT = "Holmes stoops over the body and lifts a small glass phial."
MOVE = motivated_move("tracks in", "moderate", "slow", "Holmes stoops over the body",
                      "a small glass phial")


def span(start, end, kind, movement="M1", index=0) -> CueSpan:
    return CueSpan(index=index, start=start, end=end, kind=kind, section=0,
                   movement=movement, bars=(end - start) / BAR)


def action(at, phase="open"):
    return TimedAction(at=at, phase=phase, text="the frame settles")


class TestSectionGrammar:
    def test_the_reveal_arrives_on_the_downbeat(self):
        """The section's opening cut is the movement's door; the reveal lands
        on the span's own start, which the cue placed on a downbeat."""
        found = grammar_for(span(12.0, 14.0, "section"), MOVE, TEXT, cast=["holmes"])
        assert found.kind == "section"
        assert found.reveal_at == found.start == 12.0
        assert found.actions[0].at == 12.0

    def test_a_section_takes_the_widest_legible_frame(self):
        alone = grammar_for(span(12.0, 14.0, "section"), MOVE, TEXT, cast=[])
        bound = grammar_for(span(12.0, 14.0, "section"), MOVE, TEXT, cast=["holmes"])
        assert alone.size == "full" and bound.size == BOUND_FLOOR

    def test_a_reveal_off_its_downbeat_is_refused(self):
        with pytest.raises(ValidationError, match="downbeat"):
            ShotGrammar(kind="section", start=12.0, end=14.0, size="full", move=None,
                        actions=[action(12.0)], reveal_at=12.5)


class TestSustainGrammar:
    def test_a_sustain_carries_one_move_and_three_actions(self):
        found = grammar_for(span(0.0, 8.0, "sustain"), MOVE, TEXT, cast=["holmes"])
        assert found.move == MOVE
        assert [a.phase for a in found.actions] == ["open", "middle", "final"]
        times = [a.at for a in found.actions]
        assert times == sorted(times) and all(0.0 <= t < 8.0 for t in times)
        assert times[-1] == 8.0 - FINAL_SECOND

    def test_a_static_beat_in_a_sustain_is_given_one_move(self):
        found = grammar_for(span(0.0, 8.0, "sustain"), STATIC, TEXT, cast=["holmes"])
        assert found.move != STATIC and "toward a small glass phial" in found.move

    def test_a_sustain_missing_an_action_is_refused(self):
        with pytest.raises(ValidationError, match="three"):
            ShotGrammar(kind="sustain", start=0.0, end=8.0, size="medium", move=MOVE,
                        actions=[action(0.0), action(4.0, "middle")])

    def test_a_sustain_without_a_move_is_refused(self):
        with pytest.raises(ValidationError, match="one move"):
            ShotGrammar(kind="sustain", start=0.0, end=8.0, size="medium", move=None,
                        actions=[action(0.0), action(4.0, "middle"), action(7.0, "final")])

    def test_an_action_outside_its_span_is_refused(self):
        with pytest.raises(ValidationError, match="inside"):
            ShotGrammar(kind="sustain", start=0.0, end=8.0, size="medium", move=MOVE,
                        actions=[action(0.0), action(4.0, "middle"), action(9.0, "final")])

    def test_a_spoken_sustain_names_its_speaker_mode(self):
        quiet = grammar_for(span(0.0, 8.0, "sustain"), MOVE, TEXT, cast=["holmes"])
        spoken = grammar_for(span(0.0, 8.0, "sustain"), MOVE, TEXT, cast=["holmes"],
                             spoken=True, speaker="holmes")
        assert quiet.speaker_mode is None and spoken.speaker_mode == "look_up"


class TestPhraseAccentTrough:
    def test_a_phrase_states_one_fact(self):
        found = grammar_for(span(8.0, 10.0, "phrase"), MOVE, TEXT, cast=["holmes"])
        assert len(found.actions) == 1 and found.actions[0].at == 8.0
        assert found.move == MOVE

    def test_a_phrase_with_two_facts_is_refused(self):
        with pytest.raises(ValidationError, match="one fact"):
            ShotGrammar(kind="phrase", start=8.0, end=10.0, size="medium", move=MOVE,
                        actions=[action(8.0), action(9.0, "middle")])

    def test_an_accent_never_carries_a_bound_face(self):
        found = grammar_for(span(16.0, 16.5, "accent"), MOVE, TEXT, cast=["holmes"])
        assert found.binds_face is False and found.size == "insert" and found.move is None
        with pytest.raises(ValidationError, match="accent"):
            ShotGrammar(kind="accent", start=16.0, end=16.5, size="insert", move=None,
                        actions=[action(16.0)], binds_face=True)
        with pytest.raises(ValidationError, match="accent"):
            ShotSpec(beat_id="b1", index=0, start=16.0, seconds=0.5, cast=["holmes"],
                     char_refs={"holmes": "char-holmes"}, size="extreme_close",
                     span_kind="accent")

    def test_a_trough_is_a_static_answer(self):
        found = grammar_for(span(29.0, 32.0, "trough"), MOVE, TEXT, cast=["holmes"],
                            spoken=True, speaker=None)
        assert found.move is None and found.speaker_mode == "listening"
        with pytest.raises(ValidationError, match="still"):
            ShotGrammar(kind="trough", start=29.0, end=32.0, size="medium", move=MOVE,
                        actions=[action(29.0)])

    def test_the_tail_belongs_to_the_card_and_has_no_grammar(self):
        with pytest.raises(ValueError, match="tail"):
            grammar_for(span(32.0, 38.0, "tail"), MOVE, TEXT, cast=[])


class TestGrammarPieces:
    def test_widest_is_the_largest_legible_size_capped_for_a_face(self):
        assert widest(8.0, bound=False) == "extreme_wide"
        assert widest(8.0, bound=True) == BOUND_FLOOR
        assert widest(0.5, bound=True) == "extreme_close"

    def test_size_for_reads_the_kind(self):
        assert size_for("accent", 0.5, bound=False) == "insert"
        assert size_for("section", 3.0, bound=False) == "extreme_wide"
        assert size_for("phrase", 2.0, bound=False) == "medium_close"
        assert size_for("trough", 3.0, bound=True) == BOUND_FLOOR
        assert MIN_SECONDS[size_for("phrase", 0.5, bound=True)] <= 0.5

    def test_timed_actions_open_middle_and_final_second(self):
        found = timed_actions(10.0, 16.0, TEXT)
        assert [a.at for a in found] == [10.0, 13.0, 16.0 - FINAL_SECOND]
        assert "Holmes stoops over the body" in found[0].text
        assert "a small glass phial" in found[1].text

    def test_one_move_keeps_a_motivated_move_and_replaces_a_static_one(self):
        assert one_move(MOVE, TEXT) == MOVE
        assert one_move(STATIC, TEXT).startswith("As Holmes stoops over the body")

    def test_speaker_mode_follows_who_is_in_frame(self):
        assert speaker_mode_for(["holmes"], "holmes", spoken=False) is None
        assert speaker_mode_for(["holmes"], None, spoken=True) == "listening"
        assert speaker_mode_for(["holmes", "watson"], "holmes", spoken=True) == "two_shot"
        assert speaker_mode_for(["holmes"], "holmes", spoken=True) == "look_up"
        assert speaker_mode_for(["watson"], "holmes", spoken=True) == "ots"

    def test_insert_text_is_written_once(self):
        from studio.shot_grammar import INSERT, insert_text
        once = insert_text(TEXT)
        assert once.startswith(INSERT) and "a small glass phial" in once
        assert insert_text(once) == once

    def test_the_grammars_model_text_is_affirmative(self):
        from studio.affirm import negations
        from studio.shot_grammar import INSERT, LOOK_UP
        for text in (INSERT, LOOK_UP, *(a.text for a in timed_actions(0.0, 8.0, TEXT))):
            assert negations(text) == []
