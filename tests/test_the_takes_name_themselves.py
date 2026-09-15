"""A take is named by the file that made it, never by counting shots.

Episode 7 has 26 shots and 25 takes: `episode_takes.groups` packed two shots
into one take, so take index 5 does not exist.  `take_dq.py` was then called
with `seq 0 25` -- 26 indices, the shot count -- and died on

    rec = records[index]
    KeyError: 5

after writing 5 of the 25 reports.  The caller had guessed a set that the
records file already knew exactly, and the guess was right for episodes 1 to 6
because nothing had packed yet.

This is the fault class again: a constant calibrated on a world that has since
changed.  The cure is not a better guess -- it is to stop guessing.  `wanted`
reads the indices off the records, and an index nobody rendered is named in one
message rather than discovered one report at a time.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location("take_dq", ROOT / "scripts/episode/take_dq.py")
take_dq = importlib.util.module_from_spec(spec)
sys.modules["take_dq"] = take_dq
spec.loader.exec_module(take_dq)

PACKED = {i: {"index": i} for i in [0, 1, 2, 3, 4, 6, 7, 8]}


def test_no_indices_means_every_take_that_exists():
    assert take_dq.wanted(PACKED, []) == [0, 1, 2, 3, 4, 6, 7, 8]


def test_the_order_is_the_take_order_not_the_argument_order():
    assert take_dq.wanted(PACKED, [7, 0, 3]) == [0, 3, 7]


def test_an_index_nobody_rendered_is_named_before_any_work_is_done():
    with pytest.raises(SystemExit) as exit:
        take_dq.wanted(PACKED, [4, 5, 9])
    said = str(exit.value)
    assert "5" in said and "9" in said, said
    assert "4" not in said.split(":")[-1], f"a take that exists was blamed: {said}"


def test_a_shot_that_was_packed_away_is_not_a_take():
    """`seq 0 25` on episode 7's 26 shots -- the call that crashed."""
    with pytest.raises(SystemExit):
        take_dq.wanted(PACKED, list(range(9)))
