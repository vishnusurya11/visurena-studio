r"""A cell left over from an older numbering is a picture of a different shot.

Cells are named by SHOT INDEX -- `Q19_0E.png` is shot 19's END panel -- and a
plan may be renumbered. Episode 8 was: five shots were spliced in to get one
line per shot, and every shot from the fifth onward moved up. The sheets were
redrawn and wrote the new cells beside the old ones, which nothing removed.

MEASURED. Four cells survived the renumbering -- Q09_0E, Q16_0E, Q19_0E and
Q23_0E -- and they are pictures of shots that no longer carry those numbers. Old
shot 19 was the scouts climbing the bluff; new shot 19 is Ferrier and the child
asleep against the boulder. `takes_r2v` attached the old picture as the new
shot's destination, and `drift` then failed the take for not arriving at a
photograph of some horsemen.

    T16  drift  0.24 HARD   aimed at the stale Q16_0E
    T19  drift -0.01 HARD   aimed at the stale Q19_0E
    T22  drift -0.10 HARD   aimed at the stale Q23_0E

Three of episode 8's five failures, and all three looked exactly like a
renderer that could not reach its mark.

THE SHEET REPORT IS THE TRUTH. `seq_<setup>.dq.json` lists the cells each sheet
actually cut, so a cell on disk that no sheet in this episode claims was drawn
for a plan that no longer exists. That is checkable for nothing, and it has to
be checked before the GPU, because the cost of being wrong is a whole episode of
takes aimed at other episodes' pictures.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio import episode_seq_board as sq

BOOK = ROOT / "library/20260822113400_a-study-in-scarlet"


def boards(tmp_path, made: dict[str, list[str]], on_disk: list[str]) -> Path:
    """A boards directory: sheet reports claiming `made`, cells `on_disk`."""
    sheets, cells = sq.sheets_in(tmp_path), sq.cells_in(tmp_path)
    sheets.mkdir(parents=True, exist_ok=True)
    cells.mkdir(parents=True, exist_ok=True)
    for setup, names in made.items():
        (sheets / f"seq_{setup}.dq.json").write_text(
            json.dumps({"sheets": [{"sheet": f"seq_{setup}_0.png", "cells": names}]}),
            encoding="utf-8")
    for name in on_disk:
        (cells / name).write_bytes(b"\x89PNG\r\n\x1a\n")
    return tmp_path


def test_a_cell_no_sheet_claims_is_named(tmp_path):
    made = {"crag": ["Q15_0.png", "Q15_0E.png"]}
    where = boards(tmp_path, made, ["Q15_0.png", "Q15_0E.png", "Q19_0E.png"])
    assert sq.stale_cells(where) == ["Q19_0E.png"]


def test_a_boards_room_that_agrees_with_itself_is_silent(tmp_path):
    made = {"crag": ["Q15_0.png", "Q15_0E.png"]}
    where = boards(tmp_path, made, ["Q15_0.png", "Q15_0E.png"])
    assert sq.stale_cells(where) == []


def test_every_setup_is_read_not_just_the_first(tmp_path):
    made = {"crag": ["Q15_0.png"], "bluff": ["Q24_0.png"]}
    where = boards(tmp_path, made, ["Q15_0.png", "Q24_0.png", "Q99_0.png"])
    assert sq.stale_cells(where) == ["Q99_0.png"]


def test_an_earlier_attempt_of_the_same_sheet_still_counts(tmp_path):
    """A strict retry rewrites the same cells; the first attempt's list is not
    stale, it is the same names."""
    sheets, cells = sq.sheets_in(tmp_path), sq.cells_in(tmp_path)
    sheets.mkdir(parents=True, exist_ok=True)
    cells.mkdir(parents=True, exist_ok=True)
    (sheets / "seq_crag.dq.json").write_text(json.dumps({"sheets": [
        {"sheet": "seq_crag_0.png", "cells": ["Q15_0.png"]},
        {"sheet": "seq_crag_0_strict.png", "cells": ["Q15_0.png"]}]}), encoding="utf-8")
    (cells / "Q15_0.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    assert sq.stale_cells(tmp_path) == []


def test_no_sheet_report_at_all_means_nothing_is_judged(tmp_path):
    """An episode whose boards have not been drawn yet has no truth to check
    against, and must not be told every cell is stale."""
    where = boards(tmp_path, {}, ["Q15_0.png"])
    assert sq.stale_cells(where) == []


def test_episode_8_is_clean_now():
    """The four that were found: Q09_0E, Q16_0E, Q19_0E, Q23_0E."""
    import pytest

    boards_dir = BOOK / "episodes/ep08/boards"
    if not boards_dir.exists():
        pytest.skip("episode 8's boards are not on this disk")
    assert sq.stale_cells(boards_dir) == []
