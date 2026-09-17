"""F2 (ep10 synthesis): whether the engine has work, read off /queue.

The 20:20 collision: a take_dq's seven Whisper jobs were in the queue when the
r4 takes were submitted; T02 rendered at 598 s (warm 266) and the DQ ran five
times its uncontended time and was re-run. Nothing asked the queue first.
"""
from studio import comfy


def fetch_of(running: int, pending: int):
    queue = {"queue_running": [[i, f"run-{i}", {}] for i in range(running)],
             "queue_pending": [[i, f"wait-{i}", {}] for i in range(pending)]}
    return lambda path: queue


def test_an_empty_queue_is_not_busy():
    assert comfy.busy(fetch=fetch_of(0, 0)) is False


def test_a_running_job_is_busy():
    assert comfy.busy(fetch=fetch_of(1, 0)) is True


def test_a_pending_job_alone_is_busy():
    assert comfy.busy(fetch=fetch_of(0, 3)) is True


def test_the_counts_are_running_and_pending():
    assert comfy.queue_counts(fetch=fetch_of(1, 6)) == (1, 6)


def test_an_engine_that_cannot_be_reached_holds_no_queue():
    """A restart empties the queue; the stage itself will meet the restart."""
    def refused(path):
        raise comfy.urllib.error.URLError("[WinError 10061] actively refused")
    assert comfy.busy(fetch=refused) is False


def test_an_engines_error_answer_is_not_its_absence():
    import io
    import pytest

    def broken(path):
        raise comfy.urllib.error.HTTPError("http://x/queue", 500, "boom", {}, io.BytesIO(b""))
    with pytest.raises(comfy.urllib.error.HTTPError):
        comfy.busy(fetch=broken)
