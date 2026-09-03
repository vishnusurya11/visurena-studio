"""Assigning shots to the cut grid without producing a loop.

Both shipped plans put their beats in the order B00..B10 and then repeated that
whole sequence three times.  Not three uses of each setup scattered through the
cut -- the same SEQUENCE, three times over, each pass faster than the last.
That is the screenplay played three times, and it is why the trailers read as
loops rather than as trailers.

Interleaving fixes it: a setup's uses are spread across the trailer and its
neighbours differ on every pass, so a returning image reads as a return rather
than as the tape starting again.
"""
from __future__ import annotations


def is_cyclic(order: list[str]) -> bool:
    """True when a shot order simply repeats its own beat sequence.

    The check the pipeline lacked.  Every gate passed a cut whose picture order
    was its beat order three times through, because nothing compared a shot
    sequence against itself.
    """
    unique = list(dict.fromkeys(order))
    if len(unique) < 3 or len(order) < 2 * len(unique):
        return False
    return order[:len(unique)] == unique and order[len(unique):2 * len(unique)] == unique


def allocate(setups: list[str], count: int, hero: int = 3) -> dict[str, int]:
    """How many shots each setup gets.  Deliberately UNEVEN, and it MEETS count.

    Uniform reuse is its own tell -- both shipped plans gave every setup exactly
    three shots, and `is_uniform` refuses that for shot LENGTHS while nothing
    checked it for setup USE.  Real trailers lean on a few images and spend the
    rest once, which reads as emphasis; equal shares read as rationing.

    The caps used to be fixed at 4 and 2, which made nine setups hold 24 shots
    and no more.  Asked for 31 this returned 24 without complaint, the caller
    zipped the two lists, and seven cuts -- 18.6 seconds -- vanished into a
    static title card.  The caps now scale to the demand, so the SHAPE of the
    unevenness is preserved while the total is whatever was asked for.
    """
    if not setups:
        return {}
    tall, short = 4, 2
    while tall * min(hero, len(setups)) + short * max(len(setups) - hero, 0) < count:
        tall += 2
        short += 1
    uses = {setup: 1 for setup in setups}
    remaining = count - len(setups)
    index = 0
    while remaining > 0:
        setup = setups[index % len(setups)]
        cap = tall if index % len(setups) < hero else short
        if uses[setup] < cap:
            uses[setup] += 1
            remaining -= 1
        index += 1
    return uses


def interleave(setups: list[str], count: int, hero: int = 3) -> list[str]:
    """Order `count` shots so no pass repeats the last and reuse is uneven.

    A setup's uses are spread across the trailer and its neighbours differ on
    every return, so a recurring image reads as a return rather than as the
    tape starting again.
    """
    if not setups:
        return []
    if len(setups) == 1 and count > 1:
        raise ValueError("cannot avoid a repeat with one setup and many shots")
    uses = allocate(setups, count, hero)
    pool = {setup: uses[setup] for setup in setups}
    order: list[str] = []
    # Always spend the setup with the most left, never the one just used.  The
    # previous version walked the setup list in rotated passes and SKIPPED any
    # setup that would repeat -- so a setup with uses left could be skipped on
    # every pass and never placed, which is how a request for 31 came back with
    # 24.  Taking the fullest remaining setup cannot strand one: the setup with
    # the most uses is only ever blocked by itself, and then only for one step.
    while len(order) < count:
        options = [s for s in setups
                   if pool[s] > 0 and (not order or order[-1] != s)]
        if not options:
            raise ValueError(
                f"{count} shots cannot be ordered from {len(setups)} setups "
                f"without a repeat; one setup would have to follow itself")
        pick = max(options, key=lambda s: (pool[s], -setups.index(s)))
        order.append(pick)
        pool[pick] -= 1
    return order
