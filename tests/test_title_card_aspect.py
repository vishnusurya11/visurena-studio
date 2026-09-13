"""A title card drawn for another shape is refused, not silently cropped.

MEASURED 2026-09-13, episode 3: `library/<book>/title/ep03.mp4` had never been
made, so `assemble.py` fell back to the book's generic `title/title.mp4` --
768x1344, drawn for a 9:16 episode. `conform_card` scales with
`force_original_aspect_ratio=increase` and then crops to the episode canvas, so
a 9:16 card in a 1:1 episode is blown up and has its TOP AND BOTTOM CUT OFF,
lettering included. The owner saw it immediately; nothing in the pipeline did.
QC even reported `title_card: true`, because a card was present.

The fallback itself is not the bug -- a book-wide card is a reasonable default.
Using one of the WRONG SHAPE without saying so is.
"""
import pytest

import importlib.util, sys
spec = importlib.util.spec_from_file_location("ep_assemble", "scripts/episode/assemble.py")
asm = importlib.util.module_from_spec(spec)
sys.modules["ep_assemble"] = asm
spec.loader.exec_module(asm)


def test_a_card_of_the_episodes_own_shape_is_accepted():
    assert asm.card_fits((768, 768), 768, 768)
    assert asm.card_fits((1024, 1024), 768, 768)      # same ratio, bigger
    assert asm.card_fits((768, 1344), 768, 1344)


def test_a_nine_by_sixteen_card_is_refused_by_a_square_episode():
    """The episode 3 fault, exactly."""
    assert not asm.card_fits((768, 1344), 768, 768)


def test_a_square_card_is_refused_by_a_vertical_episode():
    assert not asm.card_fits((768, 768), 768, 1344)


def test_a_hair_of_rounding_is_tolerated():
    """2048/3 = 682.67; a cell or card can land a pixel off its exact ratio."""
    assert asm.card_fits((767, 768), 768, 768)
    assert asm.card_fits((768, 769), 768, 768)


def test_a_card_that_cannot_be_measured_is_refused():
    assert not asm.card_fits(None, 768, 768)
    assert not asm.card_fits((0, 0), 768, 768)


def test_the_refusal_names_the_command_that_fixes_it(tmp_path):
    """A refusal that does not say what to run is a wall, not a gate."""
    with pytest.raises(SystemExit, match="title.py"):
        asm.check_card((768, 1344), 768, 768, "title.mp4", 3)
