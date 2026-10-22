"""The same rendered file, measured twice, gives the same face numbers (FastH3 bench, 2026-10-21).

docs/audit/2026-10-21_fasth3_faces/REPEATABILITY.md: T06 A seed 2 read Enfield's eye at 118.3 and
then 69.9.  The YOLO worker idles out after IDLE_S; a take asked of it while it was shutting down got
EOF ("the worker died") and the Finder handed that take AND every later one to MTCNN, a photo detector
that reads cel art differently (Hyde's 10 px face became a 200 px street patch).  So a worker is never
asked a take once it has sat near its idle line, a death is answered by one fresh worker before MTCNN,
and the Finder says which reader read each take.  The model and the process are fakes here."""
from __future__ import annotations

import contextlib
from pathlib import Path

import numpy as np

from studio import face_detect as fd
from studio import face_detect_worker as worker

FRAMES = [np.zeros((8, 8, 3), np.uint8)] * 7
YOLO = {0: [{"box": [1, 1, 9, 9], "score": 0.9}]}
MTCNN = [{"box": [2, 2, 40, 40], "score": 0.99}]


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class DyingWorker:
    """A YOLO worker that dies on the ask numbers in `deaths` (counted across every worker started)."""

    def __init__(self, asks: list, deaths: set):
        self.asks, self.deaths, self.closed, self.mine = asks, deaths, False, 0

    def __call__(self, take):
        self.asks.append(take)
        self.mine += 1
        if len(self.asks) in self.deaths:
            raise RuntimeError("the worker died")
        return dict(YOLO)

    def exited(self):
        return False

    def close(self):
        self.closed = True


def finder(deaths=(), clock=None):
    asks, started = [], []

    def start(device):
        started.append(DyingWorker(asks, set(deaths)))
        return started[-1]
    find = fd.Finder(lambda rgb: list(MTCNN), route=lambda job, gb: "cpu", start=start, busy=lambda: False,
                     claim=lambda job: contextlib.nullcontext(), clock=clock or Clock())
    return find, started


def test_one_file_measured_twice_reads_the_same_boxes():
    """A then B then A again, the worker dying once on B: A's two readings are identical."""
    find, _ = finder(deaths={2})
    first = find(Path("A.mp4"), FRAMES)
    find(Path("B.mp4"), FRAMES)
    assert find(Path("A.mp4"), FRAMES) == first


def test_a_worker_that_dies_once_is_replaced_and_the_take_read_again_by_yolo():
    find, started = finder(deaths={1})
    assert find(Path("A.mp4"), FRAMES) == YOLO
    assert len(started) == 2 and started[0].closed
    assert find.reader_of["A.mp4"] == "yolo"


def test_a_take_after_one_death_is_still_read_by_yolo():
    find, _ = finder(deaths={1})
    find(Path("A.mp4"), FRAMES)
    assert find(Path("B.mp4"), FRAMES) == YOLO and find.reader_of["B.mp4"] == "yolo"


def test_a_worker_that_dies_twice_in_a_row_hands_the_take_to_mtcnn_and_says_so():
    find, started = finder(deaths={1, 2})
    assert find(Path("A.mp4"), FRAMES) == {t: MTCNN for t in range(0, 7, fd.EVERY)}
    assert find.reader_of["A.mp4"] == "mtcnn" and len(started) == 2


def test_a_worker_near_its_idle_line_is_replaced_before_it_is_asked():
    """The race: a worker past IDLE_S less the margin may be shutting down; it is never asked."""
    clock = Clock()
    find, started = finder(clock=clock)
    find(Path("A.mp4"), FRAMES)
    clock.now = worker.IDLE_S - fd.IDLE_MARGIN_S + 0.1
    find(Path("B.mp4"), FRAMES)
    assert len(started) == 2 and started[0].closed and (started[0].mine, started[1].mine) == (1, 1)


def test_a_worker_asked_inside_its_idle_line_serves_the_next_take():
    clock = Clock()
    find, started = finder(clock=clock)
    find(Path("A.mp4"), FRAMES)
    clock.now = worker.IDLE_S - fd.IDLE_MARGIN_S - 1.0
    find(Path("B.mp4"), FRAMES)
    assert len(started) == 1
