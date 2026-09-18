"""When no cell is staged, the WORDS carry the picture -- and they say only what
is true about what was staged.

Three rules, each from a source:

1. TASK TYPES NAME WHAT IS STAGED. ref-en 3: "Choose task types according to the
   actual role each reference asset plays", and `keyframe completion` is for "an
   image [that] serves as the target video's first frame, keyframe, last frame,
   ... or another concrete frame anchor". With references only there is no such
   image, so the type is not in play -- and the lint must read the PICTURE
   declaration, not the loose words "last frame", which the arrival clause uses
   about the shot's own end.

2. THE BLOCK IS LONGER. ref-en 5.2 asks 350-500 words of detailed_description and
   says to "make detailed_description as detailed and explicit as possible ...
   establish the current composition, subject appearance and position,
   environment and lighting". With a cell at frame zero the picture carries the
   composition; with none, the words are all there is.

3. A BODY THAT MUST NOT MOVE MAY SAY SO. Stillness words are banned because they
   freeze a segment (0.77 frozen share against 0.47) -- which is exactly what a
   dead man wants. MEASURED on ep14: the corpse's hand flexed and spread across
   T02 because every block is required to carry a body-scale action.
"""
import sys

import pytest

from studio import episode_ref_official as ro

sys.path.insert(0, "tests")


def test_keyframe_completion_is_in_play_only_when_a_picture_is_a_frame():
    staged = "<Picture 3> is the first frame of [Shot 1], a close shot of the tube."
    assert ro.needs_keyframe(staged) is True
    assert ro.needs_keyframe("<Picture 3> is the last frame of [Shot 1], the tube set down.") is True


def test_the_shot_s_own_last_frame_is_not_a_keyframe_claim():
    """The arrival clause says the ACTION continues through the shot's last frame.
    No picture is a frame anchor there, and claiming the task type would be false."""
    said = ("By 00:05 the camera is panning right through the last frame, and the action continues "
            "with it.")
    assert ro.needs_keyframe(said) is False


def test_the_summary_names_only_the_types_in_play():
    assert ro.task_types(cells_staged=False) == "[reference generation + audio reuse]"
    assert ro.task_types(cells_staged=True) == "[reference generation + keyframe completion + audio reuse]"


def test_a_block_with_no_cell_is_given_more_words():
    """The floor rises because the words must do what the cell did."""
    assert ro.block_band(cells_staged=True) == (ro.LOW_BLOCK, ro.HIGH_BLOCK)
    low, high = ro.block_band(cells_staged=False)
    assert low > ro.LOW_BLOCK and high > ro.HIGH_BLOCK
    assert low == 240 and high == 360


def test_the_take_floor_follows_the_band():
    assert ro.take_floor(1, cells_staged=True) == 150
    assert ro.take_floor(3, cells_staged=True) == 350
    assert ro.take_floor(1, cells_staged=False) == 240


def test_a_still_segment_may_use_the_stillness_words():
    """L2 bans them everywhere else; a body at rest is the one place the freeze is
    the point."""
    text = ("detailed_description:\n"
            "[Shot 1] From 00:00 to 00:04. The hand lies still on the stone, the fingers keeping "
            "their places. The camera pans right across the whole shot.")
    assert ro.l2_stillness(text, {"still": {1}}) == []
    assert ro.l2_stillness(text, {"still": set()}) != []


def test_a_still_segment_needs_no_body_scale_action():
    text = ("detailed_description:\n"
            "[Shot 1] From 00:00 to 00:04. The camera pans right while the grey dawn brightens on "
            "the stone flags.")
    assert ro.l4_action(text, {"still": {1}}) == []
    assert ro.l4_action(text, {"still": set()}) != []
