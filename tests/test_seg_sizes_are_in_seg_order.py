"""The size of a segment has to be looked up in the SEGMENT's order.

`takes_r2v.card` builds two lists from the same shots and they are not in the
same order:

    segs  = [(s.index, k) for s in shots for k in range(len(s.cuts) + 1)]
    sizes = [s.size for s in shots] + [c.size for s in shots for c in s.cuts]

`segs` interleaves each shot with its own cuts; `sizes` puts every shot first
and every cut after.  With one shot per take they agree, which is why nothing
has gone wrong -- episode 4 has no sub-shots at all.  Zip them on a take that
holds two shots and one cut and every pairing after the first is wrong.

`seg_sizes` is the one built in segment order, so `end_cells` can ask whether a
segment is an insert.
"""
from types import SimpleNamespace as NS

from scripts.episode.takes_r2v import seg_sizes


def shot(index, size, *cuts):
    return NS(index=index, size=size, cuts=[NS(size=c) for c in cuts])


def test_one_shot_is_its_own_size():
    assert seg_sizes([shot(0, "wide")]) == ["wide"]


def test_a_shots_cuts_follow_it_immediately():
    assert seg_sizes([shot(0, "wide", "insert", "close")]) == ["wide", "insert", "close"]


def test_two_shots_interleave_with_their_own_cuts():
    """The pairing the flat `sizes` list gets wrong."""
    got = seg_sizes([shot(0, "wide", "insert"), shot(1, "medium", "close")])
    assert got == ["wide", "insert", "medium", "close"]


def test_it_matches_segs_one_for_one():
    shots = [shot(0, "wide", "insert"), shot(1, "medium"), shot(2, "close", "full")]
    segs = [(s.index, k) for s in shots for k in range(len(s.cuts) + 1)]
    assert len(seg_sizes(shots)) == len(segs)


def test_the_flat_list_really_does_disagree():
    """Guard the premise: if these two ever coincide the helper is pointless."""
    shots = [shot(0, "wide", "insert"), shot(1, "medium", "close")]
    flat = [s.size for s in shots] + [c.size for s in shots for c in s.cuts]
    assert flat != seg_sizes(shots)


def test_no_shots_is_no_sizes():
    assert seg_sizes([]) == []
