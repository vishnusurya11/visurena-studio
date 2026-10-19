"""2026-10-18 22:30-22:46: ComfyUI was slow to answer while it read the D: HDD, the
supervisor called it down and `restart()` launched another; each new engine loaded the
same custom nodes off the same disk and slowed the first, so three main.py ran at
once.  A restart while an engine process lives waits for THAT engine; only an engine
that never answers is killed and replaced, by exactly one launch."""
from __future__ import annotations

from pathlib import Path

from studio import engine_ops as eo
from studio.command_center.procs import ProcInfo

STARTING = [ProcInfo(16360, 1.0, "python.exe -s ComfyUI/main.py --windows-standalone-build")]


def test_a_live_engine_process_is_waited_on_never_launched_twice():
    launched, killed = [], []
    assert eo.restart(launch=lambda cmd, cwd: launched.append(cmd), wait=lambda: True,
                      root=Path("E:/p"), rows=lambda: STARTING, kill=killed.append)
    assert launched == [] and killed == []


def test_an_engine_that_never_answers_is_killed_and_replaced_once():
    launched, killed, answers = [], [], iter([False, True])
    assert eo.restart(launch=lambda cmd, cwd: launched.append(cmd), wait=lambda: next(answers),
                      root=Path("E:/p"), rows=lambda: STARTING, kill=killed.append)
    assert killed == [16360] and len(launched) == 1


def test_no_engine_process_means_one_launch():
    launched = []
    assert eo.restart(launch=lambda cmd, cwd: launched.append(cmd), wait=lambda: True,
                      root=Path("E:/p"), rows=lambda: [], kill=lambda pid: None)
    assert len(launched) == 1
