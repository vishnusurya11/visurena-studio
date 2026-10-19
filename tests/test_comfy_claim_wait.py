"""comfy.submit waits for a FOREIGN live GPU claim, only briefly, never for its own pid."""
from __future__ import annotations

import os

from studio import comfy


def clock():
    state = {"now": 0.0, "slept": 0.0}
    return state, (lambda: state["now"]), (lambda s: state.update(now=state["now"] + s, slept=state["slept"] + s))


def test_submit_never_waits_on_its_own_claim():
    state, now, sleep = clock()
    seen = []
    def claims(own_pid):
        seen.append(own_pid)
        return []                                   # compute_device already drops own pid
    assert comfy.wait_foreign_claims(cap_s=30.0, claims=claims, sleep=sleep, now=now) is False
    assert seen == [os.getpid()] and state["slept"] == 0.0


def test_a_foreign_claim_is_waited_for_up_to_the_cap():
    state, now, sleep = clock()
    held = [{"job": "av3 master", "pid": 9}]
    assert comfy.wait_foreign_claims(cap_s=30.0, claims=lambda p: held, sleep=sleep, now=now) is True
    assert 30.0 <= state["slept"] < 40.0


def test_a_claim_that_clears_ends_the_wait():
    state, now, sleep = clock()
    rows = iter([[{"pid": 9}], [{"pid": 9}], []])
    assert comfy.wait_foreign_claims(cap_s=30.0, claims=lambda p: next(rows), sleep=sleep, now=now) is False
    assert state["slept"] == 2 * comfy.CLAIM_POLL_S
