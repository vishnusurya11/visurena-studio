"""Owner, 2026-10-14 (Jekyll ep01 at 6 % GPU while the CPU measured the takes):
"it shouldn't wait, the GPU needs running, and the DQ checks should be done
after all videos are done, or in parallel if the GPU is not needed."

studio/take_schedule.py is the policy of the two lanes step 09 now runs: the
GPU queue (first renders, then retakes, then the batched GPU checks) and the
CPU check lane beside it.  Pure: no process, no GPU, no file."""
from __future__ import annotations

import pytest

from studio import take_schedule as ts
from studio.take_schedule import CHECKS, FIRST, RETAKE, Costs, Job, Rounds


# ---- the GPU queue ------------------------------------------------------------------

def test_a_retake_queues_behind_every_first_render_still_waiting():
    queue = [Job(FIRST, (0, 1, 2))]
    queue = ts.enqueue(queue, Job(RETAKE, (7,)))
    assert [j.kind for j in queue] == [FIRST, RETAKE]


def test_a_retake_goes_first_when_only_retakes_and_checks_remain():
    queue = [Job(CHECKS, (0, 1))]
    queue = ts.enqueue(queue, Job(RETAKE, (7,)))
    assert queue[0] == Job(RETAKE, (7,))


def test_retakes_ordered_while_one_waits_join_the_waiting_job():
    queue = ts.enqueue([Job(FIRST, (0,)), Job(RETAKE, (3,))], Job(RETAKE, (1, 3)))
    assert queue == [Job(FIRST, (0,)), Job(RETAKE, (1, 3))]


def test_a_render_is_next_whatever_the_cpu_lane_is_doing():
    queue = [Job(RETAKE, (4,)), Job(CHECKS, (0,))]
    assert ts.next_job(queue, cpu_busy=True) == Job(RETAKE, (4,))


def test_the_gpu_checks_never_preempt_and_wait_for_the_cpu_lane():
    """A CPU check still running may order a retake; a retake after the VL batch
    pays the video weights' cold load, which costs more than any one check."""
    queue = [Job(CHECKS, (0, 1))]
    assert ts.next_job(queue, cpu_busy=True) is None
    assert ts.next_job(queue, cpu_busy=False) == Job(CHECKS, (0, 1))
    assert ts.next_job([], cpu_busy=False) is None


# ---- the projection ---------------------------------------------------------------

COSTS = Costs(dq_s=30.0, dq_retake_s=60.0, content_s=20.0, vl_load_s=60.0, eye_s=50.0)


def rounds(**kw) -> Rounds:
    base = dict(first=((0, 100.0), (1, 100.0), (2, 100.0)), round1=(), round2=(), early=frozenset())
    return Rounds(**(base | kw))


def test_the_serial_clock_is_render_then_every_check_in_turn():
    got = ts.serial(rounds(), COSTS)
    assert got.wall_s == pytest.approx(300 + 3 * 30 + 60 + 3 * 20 + 50)
    assert got.gpu_s == pytest.approx(300 + 60 + 3 * 20)


def test_overlap_hides_every_cpu_check_but_the_last_behind_the_renders():
    got = ts.overlapped(rounds(), COSTS)
    assert got.wall_s == pytest.approx(300 + 30 + 60 + 3 * 20 + 50)
    assert got.wall_s < ts.serial(rounds(), COSTS).wall_s


def test_an_early_retake_renders_right_behind_the_first_renders():
    """Take 0's dq lands at 130 s, long before the firsts end at 300 s: its
    retake starts at 300 s, with no checks window between."""
    r = rounds(round1=((0, 100.0),), early=frozenset({0}))
    got = ts.overlapped(r, COSTS)
    # firsts 300, retake 100 -> GPU 400; its dq 60 -> CPU 460; one VL batch over 4 takes
    assert got.wall_s == pytest.approx(460 + 60 + 4 * 20 + 50)
    assert got.wall_s < ts.serial(r, COSTS).wall_s


def test_late_retakes_and_round_two_ride_one_render_job_after_the_checks():
    r = rounds(round1=((1, 100.0),), round2=((1, 100.0),))
    got = ts.overlapped(r, COSTS)
    first = 300 + 30 + 60 + 3 * 20 + 50
    late = 200 + 60 + 60 + 2 * 20 + 50          # both renders, the last dq, one VL batch, the eye
    assert got.wall_s == pytest.approx(first + late)


def test_overlap_only_keeps_todays_cycles_and_still_saves():
    r = rounds(round1=((1, 100.0),))
    assert ts.overlap_only(r, COSTS).wall_s < ts.serial(r, COSTS).wall_s
    assert ts.overlapped(r, COSTS).wall_s <= ts.overlap_only(r, COSTS).wall_s


def test_the_gpu_waits_for_a_late_dq_only_when_nothing_else_can_run():
    """One first render and a slow check: the early retake cannot start before
    its own check ends, and the GPU's idle share says so."""
    slow = Costs(dq_s=500.0, dq_retake_s=60.0, content_s=20.0, vl_load_s=60.0, eye_s=50.0)
    r = Rounds(first=((0, 100.0),), round1=((0, 100.0),), round2=(), early=frozenset({0}))
    got = ts.overlapped(r, slow)
    assert got.wall_s == pytest.approx(600 + 100 + 60 + 60 + 2 * 20 + 50)
    assert got.idle_s == pytest.approx(got.wall_s - got.gpu_s)
