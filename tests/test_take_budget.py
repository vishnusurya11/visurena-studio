"""A take is short, because a long one dies.

MEASURED over all 24 of episode 3's take records, by rendered frame count:

    frames  seconds   n  pass   mean score
       141     5.88   2     2         95.2
       158     6.58   5     4         82.1
       175     7.29   7     5         78.8
       192     8.00   5     4         87.9
       209     8.71   1     1         73.2
       294    12.25   2     0          3.75

Takes of 5.9-8.7 s pass 16 of 20 at a mean of 82.9.  The two takes at 12.25 s
pass 0 of 2 at a mean of 3.75, and they are the two worst in the episode -- T02
(3.7), which drew the owner's "blurred man at 17 seconds", and T22 (3.8).

THIS IS A SEPARATE AXIS FROM `SEGMENT_CAP`.  T22 carries only TWO segments and
still scores 3.8, so capping the panel count does not reach it.  What the long
takes share is the distance the model has to hold a composition on its own: every
passing 2-segment take puts its cut at 68-94 frames (2.8-3.9 s), while T22's sits
at 175 (7.3 s).  Nothing in `groups()` bounded that; `BUDGET` is the only lever
that does, and 8.0 s is just above the largest passing take (7.67 s placed).
"""
from studio.episode_takes import BUDGET, groups

SHOT = lambda i, secs, cuts=(), setup="hall": {
    "index": i, "seconds": secs, "setup": setup, "cuts": list(cuts)}


def test_the_budget_is_eight_seconds():
    assert BUDGET == 8.0


def test_the_twelve_second_take_that_scored_four_cannot_be_built():
    """T22's shape: two plain shots totalling 12.25 s, two segments, score 3.8."""
    runs = groups([SHOT(22, 6.1), SHOT(23, 6.15)])
    assert runs == [[22], [23]]


def test_two_shots_that_fit_still_travel_together():
    """The passing band is not broken: 3.9 + 3.9 is well inside it."""
    assert groups([SHOT(0, 3.9), SHOT(1, 3.9)]) == [[0, 1]]


def test_a_pair_at_the_old_budget_is_now_split():
    """8.1 s was legal at BUDGET 12.0 and sits in the band that passes 0 of 2."""
    assert groups([SHOT(0, 4.05), SHOT(1, 4.05)]) == [[0], [1]]


def test_a_single_shot_longer_than_the_budget_still_gets_its_own_take():
    """The cap cannot split a shot; a long shot is the plan's fault, not the
    packer's, and it must not be dropped or loop."""
    assert groups([SHOT(9, 11.0)]) == [[9]]


def test_the_segment_cap_still_applies_inside_the_budget():
    """Both caps bind: 3 segments in 6 s is still two takes."""
    runs = groups([SHOT(2, 3.0, [1.5]), SHOT(3, 3.0)])
    assert runs == [[2], [3]]


def test_every_shot_still_appears_once_and_in_order():
    rows = [SHOT(i, 4.5) for i in range(5)]
    assert [i for run in groups(rows) for i in run] == [0, 1, 2, 3, 4]
