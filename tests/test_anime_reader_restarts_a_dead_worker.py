"""The anime identity reader starts a dead worker afresh once before it gives up (face-blur round 2,
BENCH_R2 recommendation 2).  The worker exits after 120 s idle; on the bench's A2 run the first gate
after a 136 s render (ep01 T13) wrote its request into a worker still shutting down, read "the worker
died", set `broken`, and 6 of 15 faces were gated on facenet alone.  One fresh start costs one 12.8 s
load; a second failure in a row is a real fault and the terms stay unread, as before."""
from __future__ import annotations

import contextlib

import numpy as np

from studio import anime_id as aid


class Worker:
    """A fake worker: `dies` asks fail as an idle-exited process does, the rest answer."""

    def __init__(self, dies: bool):
        self.dies, self.closed, self.asked = dies, False, 0

    def __call__(self, paths):
        self.asked += 1
        if self.dies:
            raise RuntimeError("the worker died")
        n = len(paths)
        return np.zeros((n, n)), np.ones((n, n))

    def exited(self):
        return False

    def close(self):
        self.closed = True


def reader(deaths: list[bool]):
    """A reader whose k-th started worker dies when deaths[k] says so."""
    started = []

    def start(device):
        started.append(Worker(deaths[len(started)] if len(started) < len(deaths) else False))
        return started[-1]
    read = aid.Reader(route=lambda job, gb: "cpu", start=start, busy=lambda: False,
                      claim=lambda job: contextlib.nullcontext())
    return read, started


CROP = np.zeros((8, 8, 3), np.uint8)


def test_a_worker_that_died_idle_is_started_afresh_and_the_terms_are_read():
    read, started = reader([True, False])
    got = read(CROP, [CROP], [CROP])
    assert got == {"ccip_src": 0.0, "ccip_ref": 0.0, "clip_src": 1.0, "clip_ref": 1.0}
    assert len(started) == 2 and started[0].closed and not read.broken


def test_the_restarted_worker_serves_every_later_face():
    read, started = reader([True, False])
    read(CROP, [CROP], [CROP])
    assert read(CROP, [CROP], [CROP]) is not None and len(started) == 2 and started[1].asked == 2


def test_each_idle_gap_gets_its_own_fresh_start():
    """A worker that idles out again later is started afresh again: one restart per failed ask."""
    read, started = reader([True, False, False])
    read(CROP, [CROP], [CROP])
    started[1].dies = True
    assert read(CROP, [CROP], [CROP]) is not None and len(started) == 3 and not read.broken


def test_a_fresh_worker_that_fails_too_leaves_the_terms_unread_for_good():
    read, started = reader([True, True])
    assert read(CROP, [CROP], [CROP]) is None and read.broken
    assert read(CROP, [CROP], [CROP]) is None and len(started) == 2
    assert all(w.closed for w in started)
