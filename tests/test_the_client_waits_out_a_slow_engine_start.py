"""Fleet C A6 (2026-10-22): the client's patience covers a measured engine start.

CRASH.md (2026-10-21) measured a ComfyUI start at 333, 386 and 775 s to answer /system_stats
(custom-node imports on the D: HDD).  `comfy._open` gave up at 600 s, so a drive step met a
refused connection while the engine was still importing and failed a step it could have
waited out.  The supervisor (engine_ops.restart) re-waits on its next tick and kills only past
about two READY_SECONDS, so the client waits that long too."""
from __future__ import annotations

from studio import comfy, engine_ops


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def _engine_up_at(monkeypatch, up_at: float) -> Clock:
    clock = Clock()
    monkeypatch.setattr(comfy.time, "time", clock.time)
    monkeypatch.setattr(comfy.time, "sleep", clock.sleep)

    def urlopen(request, timeout=None):
        if clock.now < up_at:
            raise comfy.urllib.error.URLError("[WinError 10061] actively refused")
        return "answered"
    monkeypatch.setattr(comfy.urllib.request, "urlopen", urlopen)
    return clock


def test_a_775_second_start_is_waited_out(monkeypatch):
    clock = _engine_up_at(monkeypatch, 775.0)
    assert comfy._open("http://x/queue") == "answered"
    assert clock.now >= 775.0


def test_the_client_waits_as_long_as_the_supervisor_before_its_kill():
    """restart() waits READY_SECONDS on the starting engine, then the next tick waits again."""
    assert comfy.RESTART_SECONDS >= 2 * engine_ops.READY_SECONDS
