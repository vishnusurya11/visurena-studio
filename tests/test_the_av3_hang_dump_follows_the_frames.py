"""The av3 worker's hang dump follows the frames (GPU costs pass 2026-10-21, COSTS.md): the worker
armed `faulthandler.dump_traceback_later(STALL_S)` once at start and never again, so every pass
longer than 60 s printed a false `Timeout (0:01:00)!` stack on stderr at 62.7 s while frames were
still moving.  The pump's watchdog now re-arms it on every poll while frames move, so the dump
comes only STALL_S after the last frame: a real hang still leaves its stack, a long pass does not."""
from __future__ import annotations

import time

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
