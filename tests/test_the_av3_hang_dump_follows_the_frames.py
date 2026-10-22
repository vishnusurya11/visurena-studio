"""The av3 worker's hang dump follows the frames (GPU costs pass 2026-10-21, COSTS.md): the worker
armed `faulthandler.dump_traceback_later(STALL_S)` once at start and never again, so every pass
longer than 60 s printed a false `Timeout (0:01:00)!` stack on stderr at 62.7 s while frames were
still moving.  The pump's watchdog now re-arms it on every poll while frames move, so the dump
comes only STALL_S after the last frame: a real hang still leaves its stack, a long pass does not."""
from __future__ import annotations

import threading
import time

import pytest

from studio import master_av3 as av
from tests.test_the_av3_master_never_hangs import SIDE, parts, within


def test_the_watchdog_beats_while_frames_move_and_stops_beating_once_they_stop():
    beats, fired = [], []
    dog = av.Watchdog(0.3, lambda: fired.append(1), poll=0.05, beat=lambda: beats.append(time.monotonic()))
    dog.start()
    for _ in range(6):
        dog.tick()
        time.sleep(0.1)
    alive = len(beats)
    time.sleep(0.8)
    dog.stop()
    assert alive >= 5 and fired == [1]
    assert len(beats) - alive <= 7, "a pump that stopped is not beaten alive"


def test_a_streamed_pass_rearms_the_hang_dump_as_its_watchdog_beat(tmp_path, monkeypatch):
    armed = []
    monkeypatch.setattr(av, "dump_on_hang", lambda seconds=av.STALL_S: armed.append(seconds))
    listing = parts(tmp_path, (2,))

    def slow(frame):
        time.sleep(0.02)
        return frame
    state, got = within(60, lambda: av.streamed(listing, tmp_path / "o.mp4", SIDE, SIDE, 1, 24, slow, [],
                                                stall_s=0.4))
    assert (state, got) == ("ok", 48)
    assert armed and set(armed) == {0.4}


# -- a pass that has ended leaves no dump armed (suite keeper 2026-10-21) -----------------------
# The beat arms the process's ONE faulthandler timer; nothing cancelled it when the pass ended, so it
# fired `stall_s` later in whatever ran next.  In the test process that was the next test: the reversed
# suite died with "Windows fatal exception: access violation" in test_a_clean_multi_shot_pass_counts_every_frame,
# 1.5 s after test_a_pump_that_moves_nothing_is_killed_and_called_stalled had armed it.

def timer_calls(monkeypatch) -> list[str]:
    """The faulthandler timer's arms and cancels, in order; nothing is armed for real."""
    calls = []
    monkeypatch.setattr(av.faulthandler, "dump_traceback_later", lambda *a, **k: calls.append("arm"))
    monkeypatch.setattr(av.faulthandler, "cancel_dump_traceback_later", lambda: calls.append("cancel"))
    return calls


def slow(frame):
    time.sleep(0.02)
    return frame


def test_a_finished_pass_cancels_the_hang_dump_it_armed(tmp_path, monkeypatch):
    calls = timer_calls(monkeypatch)
    listing = parts(tmp_path, (2,))
    state, got = within(60, lambda: av.streamed(listing, tmp_path / "o.mp4", SIDE, SIDE, 1, 24, slow, [],
                                                stall_s=0.4))
    assert (state, got) == ("ok", 48)
    assert "arm" in calls and calls[-1] == "cancel", calls


def test_a_failed_pass_cancels_the_hang_dump_too(tmp_path, monkeypatch):
    calls = timer_calls(monkeypatch)
    listing = parts(tmp_path, (2,))

    def dies(frame, seen=[]):
        seen.append(1)
        if len(seen) == 30:
            raise RuntimeError("CUDA error: the card went away")
        return slow(frame)
    state, got = within(60, lambda: av.streamed(listing, tmp_path / "o.mp4", SIDE, SIDE, 1, 24, dies, [],
                                                stall_s=0.4))
    assert state == "error" and "card went away" in str(got)
    assert "arm" in calls and calls[-1] == "cancel", calls


def test_a_stopped_watchdog_beats_no_more():
    """stop() waits out a beat in flight: one landing after the pass's cancel would re-arm the dump."""
    beats, inside = [], threading.Event()

    def beat():
        inside.set()
        time.sleep(0.1)
        beats.append(1)
    dog = av.Watchdog(5.0, lambda: None, poll=0.001, beat=beat).start()
    assert inside.wait(5)
    dog.stop()
    after = len(beats)
    time.sleep(0.2)
    assert after == 1 and len(beats) == after and not dog.thread.is_alive()


def ends_with(outcome):
    """A stand-in worker run that returns a frame count, or raises the exception it is given."""
    def run(job, hard_exit=None):
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome
    return run


@pytest.mark.parametrize("outcome", [7, av.Stalled("no frame"), av.mu.ShortPass("3 of 9")],
                         ids=["done", "stalled", "short"])
def test_the_worker_cancels_its_start_dump_however_it_ends(outcome, monkeypatch, capsys):
    """main arms the dump before the model loads; its own end cancels it, so a caller in the same
    process (test_a_stall_exits_the_worker_with_its_own_code) is not left a live 60 s timer."""
    calls = timer_calls(monkeypatch)
    monkeypatch.setattr(av.Path, "read_text", lambda self, encoding=None: "{}")
    monkeypatch.setattr(av, "run", ends_with(outcome))
    try:
        av.main(["master_av3.py", "job.json"])
    except SystemExit:
        pass
    assert calls[0] == "arm" and calls[-1] == "cancel", calls
