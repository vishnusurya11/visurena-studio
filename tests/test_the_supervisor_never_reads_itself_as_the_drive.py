"""2026-10-07 14:06 UTC: ep19 read RUNNING / "drive alive" with no drive.py on the
machine.  The process table's find_drive had grown a fallback that answers the
book-wide autopilot when no drive matches, and the supervisor, asking whether
ITS episode's drive is alive, was handed its own pid: the loop waited on itself
and ep19 never launched.  The supervisor's liveness question is its own:
a drive.py line naming the codex and the number, never a line the kill guard
protects (NEVER_KILL)."""
from __future__ import annotations

from studio import engine_ops
from studio.command_center.procs import ProcInfo

CODEX = "20260827135508"
PILOT = ProcInfo(54656, 1.0, "python.exe scripts/episode/autopilot.py run --book 20260827135508_the-war-of-the-worlds")
DRIVE = ProcInfo(70001, 2.0, 'python.exe scripts/episode/drive.py 20260827135508 19 --label "ep19"')
STEP = ProcInfo(70002, 3.0, "python.exe scripts/episode/takes_r2v.py 20260827135508 19")
OTHER = ProcInfo(70003, 4.0, "python.exe scripts/episode/drive.py 20260827135508 23")


def test_the_supervisor_alone_is_not_a_live_drive():
    assert engine_ops.drive_alive([PILOT], CODEX, 19) is False


def test_a_drive_for_this_episode_is_alive_whatever_else_runs():
    assert engine_ops.drive_alive([PILOT, DRIVE, STEP], CODEX, 19) is True


def test_a_step_without_its_drive_is_not_the_drive():
    # a stray takes script after the drive died: the lock's stale read owns that case
    assert engine_ops.drive_alive([PILOT, STEP], CODEX, 19) is False


def test_another_episodes_drive_does_not_count():
    assert engine_ops.drive_alive([PILOT, OTHER], CODEX, 19) is False
