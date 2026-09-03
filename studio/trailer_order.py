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


def shortest_return(order: list[str]) -> int:
    """The fewest other shots between any image and its own next use.

    `is_cyclic` asked whether the sequence LOOKED like a repeated list, which a
    ragged opening defeats.  This asks the thing the viewer actually notices:
    how soon does a picture come back.  B00 at 0, 2 and 4 returns after one
    other shot, and that is what "the same shot in the first five seconds"
    means, measured.
    """
    last: dict[str, int] = {}
    gaps = []
    for index, setup in enumerate(order):
        if setup in last:
            gaps.append(index - last[setup] - 1)
        last[setup] = index
    return min(gaps) if gaps else len(order)


def longest_repeat(order: list[str]) -> int:
    """The longest run that appears verbatim more than once.

    A trailer may return to an image; it may not replay a SEQUENCE.  The
    shipped order contained B00..B08 twice end to end and no gate saw it.
    """
    best = 0
    for start in range(len(order)):
        for length in range(best + 1, len(order) - start + 1):
            window = order[start:start + length]
            if any(order[later:later + length] == window
                   for later in range(start + 1, len(order) - length + 1)):
                best = length
            else:
                break
    return best


def refuse_repetitive(order: list[str], min_gap: int = 5,
                      max_repeat: int = 4) -> None:
    """Refuse an order that will read as a loop rather than as a trailer."""
    gap = shortest_return(order)
    if gap < min_gap:
        raise ValueError(
            f"a shot returns after only {gap} other shot(s); a picture needs "
            f"at least {min_gap} between uses to read as a return")
    run = longest_repeat(order)
    if run > max_repeat:
        raise ValueError(
            f"a run of {run} shots repeats verbatim; that is the screenplay "
            f"played twice, not a trailer")


def widest_feasible_gap(setups: list[str], uses: dict[str, int],
                        count: int) -> int:
    """The largest return gap this many images can actually hold.

    Two ceilings.  A gap of g means every window of g+1 shots holds g+1
    distinct setups, so g <= len(setups) - 2 -- at exactly len(setups) - 1 the
    only legal order is round robin, which is the loop we are avoiding.  And
    the most-used setup must fit its uses into the runtime.
    """
    top = max(uses.values()) if uses else 1
    if top < 2:
        return len(setups)
    return max(1, min(len(setups) - 2, (count - 1) // (top - 1) - 1))


def eligible(setups: list[str], pool: dict[str, int], order: list[str],
             gap: int) -> list[str]:
    """Setups that may play next: uses left, cooled off, no repeated pair.

    Banning a repeated PAIR is what stops a long verbatim run before it starts:
    a run of length k contains k-1 adjacent pairs, so forbidding a repeated
    pair forbids a repeated run.  One cheap local rule buys the global
    property that `longest_repeat` measures.
    """
    hot = set(order[-gap:]) if gap else set()
    played = {(a, b) for a, b in zip(order, order[1:])}
    previous = order[-1] if order else None
    ready = [s for s in setups if pool[s] > 0 and s not in hot
             and (previous is None or (previous, s) not in played)]
    return ready or [s for s in setups if pool[s] > 0 and s != previous]


def scatter(setups: list[str], count: int, hero: int = 3,
            seed: int = 0) -> list[str]:
    """Order `count` shots so no image returns before `gap` others have played.

    NOT even spacing.  Even spacing of equal shares is round robin, and round
    robin is precisely the loop that shipped -- B00..B08 three times.  The
    property wanted is irregular but never soon, so the gap is a floor and the
    choice within it is random.
    """
    from random import Random

    uses = allocate(setups, count, hero)
    gap = widest_feasible_gap(setups, uses, count)
    pool, order, rng = dict(uses), [], Random(seed)
    while len(order) < count:
        ready = eligible(setups, pool, order, gap)
        if not ready:
            raise ValueError(
                f"{count} shots need more than {len(setups)} setups to keep "
                f"{gap} shots between returns")
        pick = max(ready, key=lambda s: (pool[s], rng.random()))
        order.append(pick)
        pool[pick] -= 1
    return order


def best_scatter(setups: list[str], count: int, hero: int = 3,
                 tries: int = 64) -> list[str]:
    """The widest-spread scatter over several seeds.

    Greedy-with-randomness can corner itself and fall back to the relaxed rule;
    trying a few seeds and keeping the best costs microseconds.  Seeded, so a
    plan rebuilds identically.
    """
    if not setups:
        return []
    orders = [scatter(setups, count, hero, seed) for seed in range(tries)]
    best = max(orders, key=lambda o: (shortest_return(o), -longest_repeat(o)))
    # Refuse rather than return a loop.  `eligible` relaxes its own rule when
    # it corners itself, which is right for one awkward step and wrong as an
    # outcome: two setups over thirty-one shots can only alternate, and
    # returning that quietly is how a loop reached the screen with green tests.
    if shortest_return(best) < 2:
        raise ValueError(
            f"{count} shots over {len(setups)} setups cannot avoid showing the "
            f"same image every other cut; render more setups or cut shorter")
    return best
