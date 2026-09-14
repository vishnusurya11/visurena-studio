"""A gate that finds no cells has not measured the take; it has not run.

`take_verdict.measure(video, record, cells, ...)` builds its own-cell signatures
with `cell_signatures(cells, names)`, which quietly skips any name not on disk:

    return {n: ... for n in names if (cells / n).exists()}

`take_dq.main` passed `boards` where `cells` was wanted.  Cells moved to
`boards/cells/` in the layout change (af91c0a) and nothing complained: `own`
came back EMPTY, `per_frame` became `[]` by its own `if own else []`, and every
picture gate downstream read an empty list as nothing-wrong.
`cl.foreign_names(cells, cells.parent / "plates", ...)` went looking in
`ep04/plates` for the same reason, so foreign-picture detection was dead too.

MEASURED 2026-09-14: episode 4's whole DQ run produced verdicts off zero
frames of comparison.  The ONLY reason it surfaced is that the report image is
drawn last and raised FileNotFoundError on the same bad path.  Had the strip
been drawn from `work/` alone, 24 takes would have been reported judged.

So the rule is not "pass the right directory" -- that is the bug, not the
lesson.  It is that an empty measurement must be loud.  If a take names cells
and none of them are found, `measure` raises.  A gate is allowed to say a take
is bad, and allowed to say it could not read something; it is not allowed to
say nothing and be read as a pass.
"""
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from studio import take_verdict as tv


def a_cell(where: Path, name: str) -> None:
    where.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.random.RandomState(0).randint(0, 255, (84, 48), dtype=np.uint8)).save(where / name)


def test_named_cells_that_are_all_missing_raise(tmp_path):
    boards = tmp_path / "boards"
    a_cell(boards / "cells", "Q00_0.png")
    with pytest.raises(FileNotFoundError, match="Q00_0.png"):
        tv.cell_signatures(boards, ["Q00_0.png"])          # the WRONG room


def test_the_complaint_names_the_room_it_looked_in(tmp_path):
    boards = tmp_path / "boards"
    a_cell(boards / "cells", "Q00_0.png")
    with pytest.raises(FileNotFoundError) as e:
        tv.cell_signatures(boards, ["Q00_0.png"])
    assert str(boards) in str(e.value)


def test_cells_that_are_there_are_measured(tmp_path):
    cells = tmp_path / "boards" / "cells"
    a_cell(cells, "Q00_0.png")
    got = tv.cell_signatures(cells, ["Q00_0.png"])
    assert set(got) == {"Q00_0.png"} and got["Q00_0.png"].ndim == 1


def test_asking_for_no_cells_at_all_is_not_a_failure(tmp_path):
    """`foreign_names` legitimately returns an empty list; that is an answer."""
    assert tv.cell_signatures(tmp_path, []) == {}


def test_a_partial_miss_still_raises(tmp_path):
    """Half the cells found is not half a measurement."""
    cells = tmp_path / "cells"
    a_cell(cells, "Q00_0.png")
    with pytest.raises(FileNotFoundError, match="Q01_0.png"):
        tv.cell_signatures(cells, ["Q00_0.png", "Q01_0.png"])


def test_take_dq_hands_measure_the_cells_room():
    """The call site the bug was in."""
    import inspect

    from scripts.episode import take_dq
    src = inspect.getsource(take_dq.main) + inspect.getsource(take_dq.measure_attempt)
    assert "boards_dir" in src
    assert "cells_in(" in src or "cells=" in src
    assert "tv.measure(video, rec, boards," not in src


# ---- the same shape, one room further out -----------------------------------

def a_plate(where: Path, name: str) -> None:
    where.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.random.RandomState(1).randint(0, 255, (84, 48), dtype=np.uint8)).save(where / name)


def test_a_foreign_plate_is_resolved_in_the_plates_room(tmp_path):
    """`foreign_names` returns cell names AND plate names, and both call sites
    resolved every one of them against `cells / n`.  Plates live in
    `boards/plates/`, so their signatures were never loaded -- skipped by the
    same `if exists()`.  The plate set is the one that caught T01 drifting onto
    plate_criterion for 40 frames, so it was worth having."""
    from studio import cut_landing as cl
    boards = tmp_path / "boards"
    a_cell(boards / "cells", "Q00_0.png")
    a_cell(boards / "cells", "Q05_0.png")
    a_plate(boards / "plates", "plate_cab.png")
    got = cl.foreign_pictures(boards / "cells", boards / "plates", {"Q00_0.png"})
    assert set(got) == {"Q05_0.png", "plate_cab.png"}
    assert got["plate_cab.png"].parent.name == "plates"
    assert got["Q05_0.png"].parent.name == "cells"


def test_every_foreign_picture_resolves_to_a_file_that_exists(tmp_path):
    from studio import cut_landing as cl
    boards = tmp_path / "boards"
    a_cell(boards / "cells", "Q00_0.png")
    a_plate(boards / "plates", "plate_cab.png")
    got = cl.foreign_pictures(boards / "cells", boards / "plates", set())
    assert got and all(p.exists() for p in got.values())
