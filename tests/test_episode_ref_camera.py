"""The camera and framing vocabulary of a take prompt (spec §1.4 D2-D5).

base-en §4.3: camera motion "should be written as a natural English action
within the shot, rather than stacked as separate labels", and "medium amplitude
and normal speed are usually omitted"."""
import pytest

from studio import episode_ref_official as ro


def test_a_frame_heading_becomes_a_noun_phrase_the_grammar_can_use():
    """ref-en §5.3 reads `the shot begins from <Picture 1>: ...`; the plan writes
    the frame as a shot-size heading, which is ungrammatical after a colon."""
    assert ro.noun_phrase("Close on Watson turned from the counter.") == \
        "a close shot of Watson turned from the counter"
    assert ro.noun_phrase("Medium close-up of Watson stopped on the pavement.") == \
        "a medium close-up of Watson stopped on the pavement"
    assert ro.noun_phrase("Medium two-shot side on along the railings.") == \
        "a medium two-shot side on along the railings"
    assert ro.noun_phrase("Insert at the brass foot-rail.") == "an insert at the brass foot-rail"
    assert ro.noun_phrase("Extreme close-up of the vessel.") == "an extreme close-up of the vessel"
    assert ro.noun_phrase("Wide exterior, a wet cobbled street.") == "a wide exterior, a wet cobbled street"
    assert ro.noun_phrase("Full shot from behind them.") == "a full shot from behind them"


def test_the_framing_splits_from_its_contents_so_the_picture_can_sit_between():
    """D2b: `... the shot cuts to {framing}, beginning from <Picture 4>: {contents}.`"""
    assert ro.split_frame("an insert at the brass foot-rail, the same place: the hand on the knob") == \
        ("an insert at the brass foot-rail, the same place", "the hand on the knob")
    assert ro.split_frame("a close shot of Watson walking, the bowler on, the railings behind") == \
        ("a close shot of Watson walking", "the bowler on, the railings behind")


def test_every_camera_head_the_plan_writes_has_a_third_person_verb():
    assert ro.camera_verb("Tracking beside them at a normal walking pace") == \
        "tracks beside them at a normal walking pace"
    assert ro.camera_verb("Push in through the doorway toward the slab") == \
        "pushes in through the doorway toward the slab"
    assert ro.camera_verb("Tilt down from the cravat to the stick") == "tilts down from the cravat to the stick"


def test_a_static_head_is_the_guides_own_sentence_and_names_no_amplitude():
    out = ro.camera_sentence("Static shot; he lifts the glass and drinks; he sets it down", 0, 4)
    assert out == "The camera holds a static shot as he lifts the glass and drinks, from 00:00 to 00:02."
    for banned in ("remain still throughout", "slowly", "with small amplitude",
                   "in one continuous motion in one direction"):
        assert banned not in out


def test_a_segment_with_one_clause_gives_the_camera_the_whole_range():
    assert ro.camera_sentence("Static shot; he lifts the glass", 0, 4) == \
        "The camera holds a static shot as he lifts the glass, from 00:00 to 00:04."
    assert ro.beat_sentences("Static shot; he lifts the glass", 0, 4) == []


def test_the_last_beat_of_a_segment_runs_on_to_the_last_frame():
    """Measured: 6 of 8 dialogue segments froze at the second their line ended, and the
    untimed 'Then ...' tails are where the holds sat."""
    out = ro.beat_sentences("Static shot; he lifts the glass; he walks to the door", 0, 4)
    assert out == ["At 00:02 he walks to the door, and the walk continues to the last frame of the shot."]
    assert ro.motion_noun("he leans his weight onto it") == "the lean"
    assert ro.motion_noun("the thumb turns the stick a quarter round") == "the turn"
    assert ro.motion_noun("the light changes on the wall") == "the movement"


def test_the_cells_are_the_keyframes_and_no_strip_is_cited():
    from studio.episode_spec import Line, Shot
    shots = [Shot(index=3, section="friction", setup="corridor", size="medium", faces=[],
                  frame="Medium shot from behind them down the corridor.",
                  motion="Static shot; they walk on toward the passage; the barred light crosses them")]
    placed = [{"index": 3, "t_start": 24.0, "seconds": 10.75}]
    lines = [Line(index=5, kind="narration", speaker="john_watson", text="I had come home.", shot=3)]
    text = ro.build(shots, placed, lines, {5: (24.25, 5.0)}, 260, [], {}, "A stone corridor.",
                    "john_watson", check_lint=False)
    # Owner 2026-09-11: the strip is gone.  On a one-segment take it was the cell again,
    # pixel for pixel, and its only unique content was shot order, which each cell states.
    assert "storyboard reference" not in text and "weak_reference" not in text
    assert "<Picture 2> is the first frame of [Shot 1]" in text
    assert "[reference generation + keyframe completion + audio reuse] One 10.83-second take" in text


def test_the_pace_of_a_spoken_line_is_gone_from_every_narration_take():
    """It was in all 14 narration takes; narration is not in <Audio 1> at all."""
    from studio.episode_spec import Line, Shot
    shots = [Shot(index=3, section="friction", setup="corridor", size="medium", faces=["john_watson"],
                  frame="Medium shot from behind Watson down the corridor.",
                  motion="Static shot; he lifts the stick and plants it; he walks on")]
    text = ro.build(shots, [{"index": 3, "t_start": 24.0, "seconds": 10.75}],
                    [Line(index=5, kind="narration", speaker="john_watson", text="I had come home.", shot=3)],
                    {5: (24.25, 5.0)}, 260, ["john_watson"], {"john_watson": "A man in his late twenties."},
                    "A stone corridor.", "john_watson", check_lint=False)
    assert "at the pace of a spoken line" not in text
    assert "<Subject 1>'s mouth is closed from 00:00 to 00:05" in text


def test_a_plan_that_says_slow_is_refused_rather_than_repaired():
    with pytest.raises(ValueError, match="slow"):
        ro.limp_clause("Watson limps and walks slowly on his stick")
