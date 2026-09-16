"""A gate that is recalibrated has to be re-runnable on work already paid for.

MEASURED, episode 9. `episode_gutter.FLAT` was loosened from a London number to
one calibrated on the desert, and every cell on disk went clean. The MASTER
passed, edit integrity passed, 28 of 28 takes passed -- and `qc` still failed the
episode, because it reads `seq_<setup>.dq.json`, and that file records what was
measured AT DRAW TIME, under the old threshold.

Redrawing to refresh a verdict costs $0.13 a sheet and throws away pictures that
were never wrong. The report is DERIVED from the cells, so it is re-derivable:
`--remeasure` re-runs the cell checks against the cells already on disk and
rewrites the verdict, spending nothing.

This is the same shape as `cast_bust.forget_read_back` two hours earlier -- a
stored measurement outliving the world it measured -- but the remedy is the
opposite one. There the picture changed and the reading had to die; here the
RULE changed and the reading has to be taken again.
"""
import json
import sys

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, "scripts/episode")


SIDE = 256
"""Big enough that the 8 % window (20 rows) is wider than a test strip.
At 64 px the window is 5 rows and a 10-row strip fills it, which reads as
picture by the rule above -- a fixture too small to express the case."""


def cell(path, value, noise=0.0, seed=0):
    rng = np.random.default_rng(seed)
    a = np.full((SIDE, SIDE), float(value)) + rng.normal(0, noise, (SIDE, SIDE))
    Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert("RGB").save(path)
    return path


@pytest.fixture
def boards(tmp_path):
    room = tmp_path / "boards"
    (room / "cells").mkdir(parents=True)
    (room / "sheets").mkdir(parents=True)
    for name in ("Q00_0.png", "Q01_0.png"):
        cell(room / "cells" / name, 60, noise=20.0)
    (room / "sheets" / "seq_valley_rim.dq.json").write_text(json.dumps({
        "setup": "valley_rim", "cells": 2, "route_cells": 2, "passed": False,
        "white_lines_in": ["Q00_0.png", "Q01_0.png"], "dropped_ends": [], "regressions": [],
        "sheets": [{"sheet": "seq_valley_rim_0.png", "route": [1, 2],
                    "cells": ["Q00_0.png", "Q01_0.png"], "gutters_ok": True,
                    "white_lines_in": ["Q00_0.png", "Q01_0.png"], "door_heights": [None, None],
                    "regressions": [], "duplicates": [], "strict": False}],
    }), encoding="utf-8")
    return room


def test_a_stale_verdict_is_retaken_from_the_cells_on_disk(boards):
    import seq_boards as sb

    changed = sb.remeasure(boards)
    assert changed == ["valley_rim"]
    got = json.loads((boards / "sheets" / "seq_valley_rim.dq.json").read_text(encoding="utf-8"))
    assert got["white_lines_in"] == []
    assert got["sheets"][0]["white_lines_in"] == []
    assert got["passed"] is True


def test_a_cell_that_is_still_dirty_still_fails(boards):
    """Re-measuring is not forgiving: it reads the cells again, whatever it finds."""
    import seq_boards as sb

    a = np.full((SIDE, SIDE), 60.0)
    a[:10] = 250.0                                   # real paper over a dark picture
    Image.fromarray(a.astype(np.uint8)).convert("RGB").save(boards / "cells" / "Q00_0.png")
    sb.remeasure(boards)
    got = json.loads((boards / "sheets" / "seq_valley_rim.dq.json").read_text(encoding="utf-8"))
    assert got["white_lines_in"] == ["Q00_0.png"]
    assert got["passed"] is False


def test_it_spends_nothing_and_draws_nothing(boards, monkeypatch):
    """The drawer is loaded on demand by `storyboard()`; re-measuring never asks
    for it, so making the loader itself explode is the strongest statement of
    "this costs nothing"."""
    import seq_boards as sb

    def refuse(*a, **k):
        raise AssertionError("re-measuring must never reach the drawer")
    monkeypatch.setattr(sb, "storyboard", refuse)
    sb.remeasure(boards)


def test_a_report_with_no_cells_on_disk_is_left_alone(boards):
    """Say nothing rather than call a missing picture clean: an empty
    measurement that reads as a pass is this repo's most-found fault."""
    import seq_boards as sb

    for c in (boards / "cells").glob("*.png"):
        c.unlink()
    assert sb.remeasure(boards) == []
    got = json.loads((boards / "sheets" / "seq_valley_rim.dq.json").read_text(encoding="utf-8"))
    assert got["passed"] is False
