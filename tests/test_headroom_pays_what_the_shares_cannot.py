"""ep16 (2026-10-01): the cure round wanted 1095 s, the 09 share and the pool
were empty, the episode clock sat at 4.6 of 5 h -- and can_afford DEFERRED
with "run again to resume".  Idling clocks nothing, so every resume met the
same state: an unresolvable deferral, spinning the drive forever.  The brick:
shares are an ALLOCATION of the ceiling, so remaining episode headroom pays
what the shares cannot; only true exhaustion is left, and that is terminal.
The deferral is gone -- it could only ever name money that cannot appear."""
from __future__ import annotations

from studio.run_budget import Budget


def ticking(start: float = 0.0):
    t = [start]
    return t, (lambda: t[0])


def test_headroom_is_what_the_ceiling_has_left():
    t, clock = ticking()
    b = Budget(ceiling_seconds=18000.0, shares={"09": 0.05}, clock=clock)
    t[0] = 16000.0
    assert b.headroom() == 2000.0
    t[0] = 18500.0
    assert b.headroom() == 0.0


def test_an_empty_share_with_headroom_is_not_a_dead_state():
    t, clock = ticking()
    b = Budget(ceiling_seconds=18000.0, shares={"09": 0.05}, clock=clock)
    b.start("09")
    t[0] = 1000.0                                  # the 900 s share is overdrawn...
    assert b.can_afford("09", 1095.0) is False
    assert b.pool_left() <= 0.0                    # ...no ladders share exists...
    assert b.headroom() >= 1095.0                  # ...and the ceiling can still pay
    assert b.ceiling_spent() is False
