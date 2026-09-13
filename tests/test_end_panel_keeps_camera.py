"""An END panel may not re-specify the camera it was told to keep.

`end_text` asserts "the same camera position, the same lens ... as panel j" and
then prints the plan's own `end` prose, which the authors wrote as a complete
fresh picture -- and a complete fresh picture renames the framing: "from a
stride nearer", "his head has grown to half the frame's height".  The model
resolves the contradiction in favour of the prose EVERY time.

MEASURED, episode 2: "END keeps the same camera position" was obeyed 4 times in
12 (0.33), the worst rate of any instruction in the sheet prompt except the dead
landmark ladder.  Sofa 1->2, sofa 4->5 and stair 8->9 all moved the camera.
These cells are the takes' END references, so a violated "same camera" becomes a
jump inside one shot that survives to the master.

OpenAI's own image-editing guidance names the fix: say "change only X" and list
what to preserve.  So the re-framing phrases come out of the END prose, and the
preservation list stays.
"""
import pytest

from studio.episode_seq_board import keeps_camera


@pytest.mark.parametrize("said", [
    "The same hearth from a stride nearer: the pencil stands clear of the paper.",
    "Closer now on the pencilled sheet, the fourth heading written.",
    "A tighter framing on his face, the chin lifted an inch.",
    "The camera has moved in and his head has grown to half the frame's height.",
    "Pulled back a pace, the whole chair in frame.",
    "From a lower angle, the flame at the sheet's corner.",
])
def test_a_reframing_phrase_is_removed(said):
    assert keeps_camera(said) != said
    kept = keeps_camera(said).lower()
    for word in ("nearer", "closer", "tighter", "grown to", "pulled back", "lower angle"):
        assert word not in kept


def test_the_picture_itself_survives():
    said = ("The same hearth from a stride nearer: the pencil stands clear of the paper and "
            "the fourth heading is written.")
    kept = keeps_camera(said)
    assert "the pencil stands clear of the paper" in kept
    assert "the fourth heading is written" in kept


def test_a_clean_end_is_left_alone():
    said = ("Insert on the topmost sheet at the CENTRE of frame: four grey graphite headings "
            "stand in a column down the white paper.")
    assert keeps_camera(said) == said


def test_a_frame_edge_assertion_is_kept():
    """Frame edges are the instruction this model obeys best, at 0.83 -- they say
    WHERE a thing is, not how the camera moved to see it."""
    said = "The blue envelope has crossed to the RIGHT edge, still a palm wide."
    assert keeps_camera(said) == said


def test_an_empty_string_is_safe():
    assert keeps_camera("") == ""
