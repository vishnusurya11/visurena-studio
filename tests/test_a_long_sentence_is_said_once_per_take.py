"""ep21, 2026-10-08 07:30Z: step 06 refused four packed takes on L19 CROWD --
a 23-28 word setup sentence (and an identical camera sentence) sat in both
blocks of one take.  The plan was signed and its battery clean; the repeat was
the builder's.  A long sentence is said once per take: a later block drops
what an earlier block of the same take already carries; short repeats stay."""
from __future__ import annotations

from studio import episode_ref_official as ro

LONG = ("The grey slate shelf crosses the CENTRE behind the two men at waist height, "
        "a cold grey band from the LEFT edge to the RIGHT edge of the picture.")
SHORT = "Grey daylight falls from the LEFT."
DD = (f"[Shot 1] From 00:00 to 00:04. The camera holds a locked-off frame. {LONG} {SHORT}\n"
      f"[Shot 2] From 00:04 to 00:08. The camera pushes in toward the curate. {LONG} {SHORT}")


def test_the_long_sentence_leaves_the_second_block_and_the_short_one_stays():
    out = ro.once_per_take(DD)
    blocks = ro.blocks("detailed_description:\n" + out)
    assert len(blocks) == 2
    assert LONG in blocks[0][3] and LONG not in blocks[1][3]
    assert SHORT in blocks[0][3] and SHORT in blocks[1][3]
    assert "The camera pushes in toward the curate." in blocks[1][3]


def test_the_lint_is_satisfied_afterwards():
    text = ro.six_sections("x", "y", "z", ro.once_per_take(DD), "s")
    assert not [f for f in ro.l19_crowd(text, {}) if "sits in" in f]
    before = ro.six_sections("x", "y", "z", DD, "s")
    assert [f for f in ro.l19_crowd(before, {}) if "sits in" in f]


def test_a_single_block_is_untouched():
    one = f"[Shot 1] From 00:00 to 00:04. {LONG} {SHORT}"
    assert ro.once_per_take(one) == one
