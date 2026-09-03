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
    """How many shots each setup gets.  Deliberately UNEVEN.

    Uniform reuse is its own tell -- both shipped plans gave every setup exactly
    three shots, and `is_uniform` refuses that for shot LENGTHS while nothing
    checked it for setup USE.  Real trailers lean on a few images and spend the
    rest once, which reads as emphasis; equal shares read as rationing.
    """
    uses = {setup: 1 for setup in setups}
    remaining = count - len(setups)
    index = 0
    while remaining > 0:
        setup = setups[index % len(setups)]
        cap = 4 if index % len(setups) < hero else 2
        if uses[setup] < cap:
            uses[setup] += 1
            remaining -= 1
        index += 1
        if index > count * 4:
            break
    return uses


def interleave(setups: list[str], count: int, hero: int = 3) -> list[str]:
    """Order `count` shots so no pass repeats the last and reuse is uneven.

    A setup's uses are spread across the trailer and its neighbours differ on
    every return, so a recurring image reads as a return rather than as the
    tape starting again.
    """
    if not setups:
        return []
    uses = allocate(setups, count, hero)
    pool = {setup: uses[setup] for setup in setups}
    order: list[str] = []
    passes = 0
    while len(order) < count and any(pool.values()):
        rotated = setups[passes % len(setups):] + setups[:passes % len(setups)]
        if passes % 2:
            rotated = list(reversed(rotated))
        for setup in rotated:
            if pool[setup] > 0 and len(order) < count:
                if order and order[-1] == setup:
                    continue
                order.append(setup)
                pool[setup] -= 1
        passes += 1
    return order[:count]
