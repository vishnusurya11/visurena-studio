"""The storyboard panel is the shot's FIRST FRAME, not a hint beside it.

OWNER 2026-09-20 chose this for episode 6, after ep05 shipped with T14's horse
cropped to a head even though the panel showed the whole animal in its cab.

WHY IT IS SAFE, which I had wrong. I staged the panel as a `weak_reference`
because ep03 T02 froze -- similarity 1.000 to its cell, 0.12 frame-to-frame
change. But the freeze was not the pin. `episode_ref_official` says so beside
the code: 22 of 22 prompts asked for a preserved VIEWPOINT in a block whose own
camera sentence pushes the camera through it, and told to hold the viewpoint
and to change it, the render held. The fix was to drop `viewpoint`. The pin
stayed, and Scarlet pinned every cell this way for fourteen episodes.

So the relation is the one Scarlet uses, word for word:

    <Picture N> ([Shot k] first frame): fully_preserved - subject placement,
    wardrobe and light.

Placement, wardrobe and light. Never viewpoint, never framing: the camera
sentence owns those. And never a LAST frame -- `NO_ENDS` stands, because a
last-frame pin has no good setting; the model races to the end picture and
holds it there.
"""
import pytest


def test_the_pin_is_scarlets_own_words():
    from studio.take_refs import panel_pin
    said = panel_pin(4, shot=1)
    assert "([Shot 1] first frame)" in said
    assert "fully_preserved" in said
    assert "subject placement, wardrobe and light" in said


def test_the_pin_never_claims_the_viewpoint():
    """The one clause that froze ep03 T02."""
    from studio.take_refs import panel_pin
    said = panel_pin(4, shot=1).lower()
    assert "viewpoint" not in said
    assert "framing" not in said


def test_the_pin_is_never_a_last_frame():
    from studio.take_refs import panel_pin
    assert "last frame" not in panel_pin(2, shot=1).lower()


def test_a_panel_is_anchored_at_its_shots_start():
    """`cell_anchors` pins each cell ONCE at its own start frame; a take of one
    shot pins at frame 0."""
    from studio.take_refs import panel_anchor
    assert panel_anchor("shot_14.png", t_start=0.0, take_start=0.0, fps=24) == ("shot_14.png", 0)


def test_an_anchor_lands_on_a_token_start():
    """A pin inside a token smears over its four frames, so it snaps FORWARD to
    a token start -- 17 frames per 5 tokens. Delegated to `episode_takes`,
    never re-derived here."""
    from studio.episode_takes import grid_frame
    from studio.take_refs import panel_anchor
    _, frame = panel_anchor("shot_09.png", t_start=2.05, take_start=0.0, fps=24)
    assert frame == grid_frame(round(2.05 * 24))


def test_the_pin_and_the_retention_are_not_both_used():
    """One relation per picture. `panel_retention` is the weak_reference form
    ep05 shipped with; `panel_pin` replaces it, and using both would mark one
    picture twice."""
    from studio.take_refs import panel_pin, panel_retention
    assert panel_pin(3, shot=1) != panel_retention(3)
