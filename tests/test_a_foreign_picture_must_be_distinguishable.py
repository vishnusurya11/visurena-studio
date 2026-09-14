"""A picture the gate cannot tell apart from the take's own cell is not evidence.

The FOREIGN rule flags a frame whose best OTHER picture beats its own cell by
`FOREIGN_MARGIN` (0.05).  The other set includes every location plate, and that
belongs there: a take drifting onto its empty room is a real fault, and episode
3's T01 pulled in 40 frames of plate_criterion.

It breaks on a shot that IS the empty location.  Episode 4's shot 13 is a wide
of the garden gate of Number 3 with nobody in it; its own cell scores +0.623
against plate_lauriston_gate, because they are the same view.  A frame near
either is near both, and the 0.05 margin is then measuring noise.

MEASURED on episode 4, 2026-09-14, cell vs its own setup's plate:

    Q13_0 +0.623   T13 flagged 85 foreign frames -- FALSE, it is that street
    Q05_0 +0.626   Audley Court wide, same shape
    Q00_0 +0.475   the cab two-shot, two men in it
    Q17_0 +0.230
    Q08_0 -0.057
    Q21_0 -0.051   T21 hit 0.999 on the plate while its own cell read -0.055
                   -- TRUE, the room really did empty

and cell against CROSS-SHEET cell, the same shape one room further out:

    Q13_0 vs Q11_0  +0.585   a night exterior against an indoor close-up
    Q13_0 vs Q15_0E +0.553   the same

So the split is between +0.475 and +0.623, and `DISTINCT = 0.55` sits in it.
Above it the two references are one view and the gate must not accuse; below it
they are distinguishable and the accusation means something.  Six cells is thin
evidence for a constant and this docstring is where that is admitted.
"""
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from studio import cut_landing as cl


def pic(where: Path, name: str, seed: int, blend: float = 0.0, base: int = 0) -> None:
    where.mkdir(parents=True, exist_ok=True)
    a = np.random.RandomState(seed).randint(0, 255, (84, 48)).astype(float)
    if blend:
        b = np.random.RandomState(base).randint(0, 255, (84, 48)).astype(float)
        a = blend * b + (1 - blend) * a
    Image.fromarray(a.astype(np.uint8)).save(where / name)


def a_book(tmp_path: Path, plate_blend: float) -> Path:
    boards = tmp_path / "boards"
    pic(boards / "cells", "Q13_0.png", seed=1)
    pic(boards / "cells", "Q99_0.png", seed=2)
    pic(boards / "plates", "plate_x.png", seed=3, blend=plate_blend, base=1)
    return boards


def test_a_plate_that_is_the_takes_own_view_is_not_foreign(tmp_path):
    boards = a_book(tmp_path, plate_blend=1.0)          # the plate IS the cell
    got = cl.foreign_pictures(boards / "cells", boards / "plates", {"Q13_0.png"})
    assert "plate_x.png" not in got


def test_a_plate_of_a_different_view_stays_foreign(tmp_path):
    boards = a_book(tmp_path, plate_blend=0.0)          # unrelated
    got = cl.foreign_pictures(boards / "cells", boards / "plates", {"Q13_0.png"})
    assert "plate_x.png" in got


def test_another_takes_cell_is_exempted_on_the_same_terms(tmp_path):
    """This started out restricted to plates, on the reasoning that two cells
    which look alike is a sheet fault the TWINS gate owns.  That reasoning is
    wrong: TWINS compares panels WITHIN ONE SHEET, and the pairs that bit here
    are on different sheets, in different setups, so TWINS never saw them.

    MEASURED: T13, a night exterior, was flagged against Q11_0 and Q15_0E --
    close-ups of Rance in a lit indoor parlour.  Q13_0 scores +0.585 and +0.553
    against them, because a 48x84 grey thumbnail reads both as a dark frame with
    one bright window.  The frames are not remotely alike to a reader.

    The law is about the matcher, not the kind of picture: the gate may not
    accuse using a reference it cannot tell apart from the defendant."""
    boards = tmp_path / "boards"
    pic(boards / "cells", "Q13_0.png", seed=1)
    pic(boards / "cells", "Q99_0.png", seed=3, blend=1.0, base=1)   # identical to Q13_0
    (boards / "plates").mkdir(parents=True)
    got = cl.foreign_pictures(boards / "cells", boards / "plates", {"Q13_0.png"})
    assert "Q99_0.png" not in got


def test_a_cell_of_a_different_picture_stays_foreign(tmp_path):
    boards = tmp_path / "boards"
    pic(boards / "cells", "Q13_0.png", seed=1)
    pic(boards / "cells", "Q99_0.png", seed=7)
    (boards / "plates").mkdir(parents=True)
    got = cl.foreign_pictures(boards / "cells", boards / "plates", {"Q13_0.png"})
    assert "Q99_0.png" in got


def test_the_threshold_is_named_and_sits_between_the_measurements():
    assert 0.475 < cl.DISTINCT < 0.623


def test_a_take_with_no_own_cells_exempts_nothing(tmp_path):
    boards = a_book(tmp_path, plate_blend=1.0)
    got = cl.foreign_pictures(boards / "cells", boards / "plates", set())
    assert "plate_x.png" in got


def test_the_exemption_needs_only_one_matching_own_cell(tmp_path):
    """A take holds up to two segments; resembling either one is enough."""
    boards = a_book(tmp_path, plate_blend=1.0)          # plate matches Q13_0 only
    got = cl.foreign_pictures(boards / "cells", boards / "plates", {"Q13_0.png", "Q99_0.png"})
    assert "plate_x.png" not in got
