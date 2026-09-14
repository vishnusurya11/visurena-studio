"""A waiter that gives up on a job the GPU then finishes has spent the time and
kept nothing.

`bed()` called `run(..., timeout=900)`.  YuE2's olmpack graph runs three seeded
stages -- ABC score, semantic, sampler -- and on this machine it takes longer
than fifteen minutes.  MEASURED on episode 4, 2026-09-14: the waiter raised
`StillRunning` at 900 s, the assemble died with no master, and ComfyUI's history
then reported that same prompt id as `status: success` with its audio on disk.
The bed was made.  It was discarded by the clock.

BED_TIMEOUT is set from the slowest bed engine, not the fastest, because the
cost of waiting too long is minutes and the cost of not waiting long enough is
the whole job.
"""
import inspect

from scripts.episode import assemble


def test_the_bed_waits_longer_than_a_yue2_run():
    """The olmpack graph measured over 900 s; 900 was the old value."""
    assert assemble.BED_TIMEOUT >= 1800


def test_the_bed_uses_it():
    assert "BED_TIMEOUT" in inspect.getsource(assemble.bed)


def test_no_bare_nine_hundred_is_left_in_the_call():
    assert "timeout=900" not in inspect.getsource(assemble.bed)
