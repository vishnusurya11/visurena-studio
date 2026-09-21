"""The storyboard panel can be PINNED as a take's first frame, on request.

OWNER 2026-09-20, option 2, after ep05 shipped with T14's horse cropped to a
head while its panel showed the whole animal in its cab. A weak_reference
informs and has no authority over framing -- which is exactly what we tell it
-- so the panel could not fix the framing. A first-frame pin has that
authority.

The freeze that ep03 T02 suffered came from a preserved VIEWPOINT in a block
whose own camera sentence pushes the camera through it, not from the pin; see
studio/take_refs.panel_pin. So the pin preserves subject placement, wardrobe
and light, and never viewpoint.
"""
from __future__ import annotations

import pytest

from studio import take_refs


def test_the_pin_preserves_placement_wardrobe_and_light():
    said = take_refs.panel_pin(5, shot=3)
    assert "fully_preserved" in said
    assert "subject placement" in said and "wardrobe" in said and "light" in said


def test_the_pin_never_preserves_the_viewpoint():
    """The one word that froze ep03 T02 at similarity 1.000."""
    assert "viewpoint" not in take_refs.panel_pin(5, shot=3).lower()


def test_the_pin_names_the_slot_and_the_shot():
    said = take_refs.panel_pin(6, shot=2)
    assert "<Picture 6>" in said and "Shot 2" in said


def test_the_pin_says_it_is_the_first_frame():
    assert "first frame" in take_refs.panel_pin(4, shot=1)


def test_the_pin_carries_no_negation():
    from studio.episode_ref_official import negations
    assert not negations(take_refs.panel_pin(4, shot=1))


@pytest.mark.parametrize("pinned,expect", [(True, "fully_preserved"),
                                           (False, "weak_reference")])
def test_the_builder_chooses_the_relation_the_caller_asked_for(pinned, expect):
    said = (take_refs.panel_pin(4, shot=1) if pinned
            else take_refs.panel_retention(4))
    assert expect in said


def test_the_relation_pins_by_default():
    assert "fully_preserved" in take_refs.panel_relation(4)


def test_the_relation_can_still_only_consult():
    assert "weak_reference" in take_refs.panel_relation(4, pin=False)
