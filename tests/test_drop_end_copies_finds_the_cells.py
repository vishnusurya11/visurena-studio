"""A guard that checks `.exists()` before acting does nothing when it is looking
in the wrong room, and says nothing either.

`drop_end_copies` retires an END cell that is still a copy of its own start
panel after the strict retry.  It built the path as `boards / f"{end}.png"`.
Cells moved to `boards/cells/` in the layout change (commit af91c0a), so the
path stopped resolving -- and because the function asks `if ... .exists()`
first, it skipped every cell in silence.

MEASURED on episode 4, 2026-09-14: seven END cells scored over END_CEILING
against their own start panel, `clean()` refused every one of those sheets, the
strict retry ran, `drop_end_copies` was reached -- and all seven are still on
disk.  The report said `dropped_ends: []` and looked like good news.

It also no longer DELETES.  `sq.reaches` already refuses a copy as a take's
destination, so the unlink was belt-and-braces over a picture that cost money to
draw.  The cell is moved to `boards/superseded/` instead: retired from the
pipeline, still on disk.
"""
from pathlib import Path

import pytest
from PIL import Image

from scripts.episode.seq_boards import drop_end_copies


def cells(tmp_path: Path, *names: str) -> Path:
    boards = tmp_path / "boards"
    (boards / "cells").mkdir(parents=True)
    for n in names:
        Image.new("RGB", (8, 8), (7, 7, 7)).save(boards / "cells" / n)
    return boards


ENTRY = {"duplicates": [("Q08_0", "Q08_0E")]}


def test_a_copied_end_cell_is_retired(tmp_path):
    boards = cells(tmp_path, "Q08_0.png", "Q08_0E.png")
    dropped = drop_end_copies(boards, ENTRY)
    assert [d["dropped_end"] for d in dropped] == ["Q08_0E"]
    assert not (boards / "cells" / "Q08_0E.png").exists()


def test_it_is_moved_and_not_destroyed(tmp_path):
    """A drawn cell cost money; retiring it is not the same as losing it."""
    boards = cells(tmp_path, "Q08_0.png", "Q08_0E.png")
    drop_end_copies(boards, ENTRY)
    assert (boards / "superseded" / "Q08_0E.png").exists()


def test_the_start_panel_is_left_alone(tmp_path):
    boards = cells(tmp_path, "Q08_0.png", "Q08_0E.png")
    drop_end_copies(boards, ENTRY)
    assert (boards / "cells" / "Q08_0.png").exists()


def test_the_pair_may_be_given_in_either_order(tmp_path):
    boards = cells(tmp_path, "Q08_0.png", "Q08_0E.png")
    assert drop_end_copies(boards, {"duplicates": [("Q08_0E", "Q08_0")]})


def test_a_pair_of_two_start_panels_retires_neither(tmp_path):
    """Two ordinary panels that are one picture is a different fault, and not
    one you answer by deleting a cell the take needs."""
    boards = cells(tmp_path, "Q08_0.png", "Q09_0.png")
    assert drop_end_copies(boards, {"duplicates": [("Q08_0", "Q09_0")]}) == []
    assert (boards / "cells" / "Q09_0.png").exists()


def test_nothing_to_drop_is_no_drops(tmp_path):
    assert drop_end_copies(cells(tmp_path, "Q08_0.png"), {"duplicates": []}) == []


def test_a_cell_that_is_not_on_disk_is_not_reported_as_dropped(tmp_path):
    """The old bug's signature: an empty list that means 'looked in the wrong
    room', not 'nothing was wrong'."""
    boards = cells(tmp_path, "Q08_0.png")
    assert drop_end_copies(boards, ENTRY) == []


def test_it_does_not_look_in_the_boards_root(tmp_path):
    """A cell sitting in the OLD location is not found, and must not be."""
    boards = cells(tmp_path, "Q08_0.png", "Q08_0E.png")
    Image.new("RGB", (8, 8), (1, 1, 1)).save(boards / "Q08_0E.png")
    drop_end_copies(boards, ENTRY)
    assert (boards / "Q08_0E.png").exists()
