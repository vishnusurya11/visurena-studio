r"""The drop reason said "still a copy" seven times in episode 6, and was wrong seven times.

`duplicates()` flags an END pair when `end_pair_verdict(...) != "ok"` -- which is
COPY **or** RE-STAGED, two opposite faults. `drop_end_copies` then wrote one
hardcoded string for both:

    f"still a copy of {other} after strict"

MEASURED on episode 6's seven retired END cells, similarity to their own start:

    Q08_0E 0.330 · Q09_0E 0.253 · Q10_0E 0.321 · Q15_0E 0.315
    Q17_0E 0.407 · Q19_0E 0.176 · Q23_0E -0.007

Every one is BELOW `END_FLOOR = 0.45`. Not one is near `END_CEILING = 0.80`.
They are all re-stagings -- the drawer answering a camera delta by moving the
camera to a new setup -- and the ledger recorded the exact opposite seven times.

THE COST WAS NOT THE STRING. The false fact propagated: into the skill's
mechanism ("with a dominant reference image it copies"), into this session's
own brief to a reviewer, and into a report to the owner. A ledger that states
the opposite of what was measured is worse than one that says nothing, because
it is quoted.

The fault is the same one the repo keeps finding, one step along: a computation
whose two opposite outcomes are recorded as the same outcome.
"""
from studio.episode_seq_board import END_CEILING, END_FLOOR, drop_reason


def test_a_copy_is_named_a_copy():
    assert "copy" in drop_reason("Q00_0E", "Q00_0", 0.991)


def test_a_restaging_is_named_a_restaging():
    said = drop_reason("Q08_0E", "Q08_0", 0.330)
    assert "re-staged" in said and "copy" not in said


def test_every_episode_six_drop_is_a_restaging():
    for sim in (0.330, 0.253, 0.321, 0.315, 0.407, 0.176, -0.007):
        assert "copy" not in drop_reason("Q08_0E", "Q08_0", sim), sim


def test_the_reason_carries_the_number():
    assert "0.33" in drop_reason("Q08_0E", "Q08_0", 0.330)


def test_the_reason_names_the_cell_it_was_compared_to():
    assert "Q08_0" in drop_reason("Q08_0E", "Q08_0", 0.330)


def test_the_band_is_the_documented_one():
    assert (END_FLOOR, END_CEILING) == (0.45, 0.80)


def test_a_score_inside_the_band_is_neither():
    """It should not have been dropped at all, and the reason says so rather
    than inventing a fault -- ep05's Q20_0E measured 0.565 and was retired."""
    said = drop_reason("Q20_0E", "Q20_0", 0.565)
    assert "in band" in said
