"""NO SLOW SHOTS -- the owner's strict rule, 2026-09-12.

`episode_ref_official` already refused 'slow' in the TAKE prompt, which is one
stage too late: the word is written in the plan, copied onto the storyboard
sheet, drawn, and only then refused -- after the paid sheet.  And the sheet's
own prose is never linted for pace at all, so a panel could say "slowly" and
gpt-image would draw the drag into the cell for H3 to inherit as position.

The rule is enforced where the word is written: the plan.
"""
import pytest
from pydantic import ValidationError

from studio.episode_spec import Setup, Shot


def a_shot(**over) -> dict:
    base = dict(index=0, section="hook", setup="room", size="medium", faces=[],
                frame="Medium on a man at a table, his hand flat on the cloth.",
                motion="The hand slides a thumb's width across the cloth.")
    return base | over


def a_setup(**over) -> dict:
    base = dict(described="A plain room with one window and a table under it.")
    return base | over


def test_a_plain_shot_still_passes():
    assert Shot(**a_shot()).index == 0


@pytest.mark.parametrize("said", [
    "The hand slides slowly across the cloth.",
    "The hand makes a slow move across the cloth.",
    "The camera gradually pushes in on his face.",
    "His gaze is a lingering one across the table.",
    "The arm lifts in a languid arc.",
    "A leisurely turn of the head toward the door.",
    "The whole shot plays in slow-motion.",
])
def test_every_pace_word_is_refused_in_the_motion(said):
    with pytest.raises(ValidationError):
        Shot(**a_shot(motion=said))


def test_the_frame_is_refused_too():
    with pytest.raises(ValidationError):
        Shot(**a_shot(frame="Medium on a man in a slow drift toward the window."))


def test_a_sub_shot_is_refused_on_the_same_rule():
    with pytest.raises(ValidationError):
        Shot(**a_shot(cuts=[dict(at_s=3.0, size="insert",
                                 frame="Insert on a hand on a rail.",
                                 motion="The hand slides slowly up the rail.")]))


def test_a_setups_own_description_is_refused_too():
    with pytest.raises(ValidationError):
        Setup(**a_setup(described="A plain room where dust drifts slowly through the window light."))


def test_a_word_that_merely_contains_slow_is_left_alone():
    """'Slower' is the comparative and still names a drag; 'slowworm' is a
    lizard.  The boundary is a whole word, so a legitimate noun passes."""
    assert Shot(**a_shot(motion="A slowworm lies on the warm tile.")).index == 0
