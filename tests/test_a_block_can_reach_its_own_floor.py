r"""A block filled exactly to its budget measures under the floor it is filled for.

`segment_text` fills a `[Shot k]` block with `detail(seg, budget(core))`, where

    budget(core) = min(LOW_BLOCK + MARGIN, HIGH_BLOCK) - core     # 165 - core

and `core` is counted with `words()`, which SCRUBS -- it strips `<Picture N>`,
`<Subject N>` and the timestamps before counting. But `detail`'s `trim` cuts the
camera and at-rest sentences by RAW word count. So the allowance is spent in raw
words and the result is judged in scrubbed ones, and the two differ by a lot: on
episode 7's shot 0 the block runs 209 raw words and `words()` calls it 146.

L14 then refuses it, because the gate is 150-240 scrubbed.

MEASURED on that shot, which is why this test exists: I added a longer `frame`,
a longer `camera`, a longer `at_rest` and TWO more motion clauses -- about fifty
words of authored prose -- and the measured block stayed at exactly 146 through
every one of them. Every word added to `core` takes a word out of `want`, and
every word added to the detail fields is trimmed back to `want`. The block is
pinned below its own floor and no amount of writing moves it.

Episodes 4 to 6 never hit this because their blocks carry dialogue lines and
more beats, so `core` alone clears 150 and the fill is never the binding
constraint. A LEAN block -- a silent insert, one short line -- is the case that
cannot pass, and those are exactly the shots the rhythm work asks for.

So the fill aims at the measure the gate uses.
"""
from studio.episode_ref_official import HIGH_BLOCK, LOW_BLOCK, budget, words


def test_a_lean_block_is_allowed_to_reach_the_floor():
    """A block whose scrubbed core is 84 must be able to reach 150 scrubbed."""
    assert budget(84) >= LOW_BLOCK - 84


def test_the_allowance_covers_what_the_scrub_removes():
    """209 raw words scrubbed to 146 is a ratio near 0.70; an allowance that does
    not account for it is spent before the floor is reached."""
    assert budget(84) > 165 - 84


def test_a_full_block_is_given_nothing_more():
    """A block already at the ceiling asks for no fill."""
    assert budget(HIGH_BLOCK) == 0
    assert budget(HIGH_BLOCK + 40) == 0


def test_the_ceiling_still_holds():
    """OWNER 5.17: a take is long because it has more shots, never because one
    shot is padded. The fill may not push a block past HIGH_BLOCK."""
    for core in range(0, HIGH_BLOCK, 10):
        assert core + budget(core) <= HIGH_BLOCK


def test_a_block_at_the_floor_asks_for_little():
    assert budget(LOW_BLOCK) < budget(LOW_BLOCK - 40)


def test_the_scrub_is_what_makes_the_two_counts_differ():
    said = "[Shot 1] From 00:00 to 00:06. <Subject 1> lifts <Picture 2> at 00:04."
    assert words(said) < len(said.split())
