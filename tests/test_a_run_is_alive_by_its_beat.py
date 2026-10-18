"""A run with an honest clock is alive by its beat, not by folder mtimes (page experts
2026-10-18, backend #8): Jekyll ep01's drive exited (series paused) while files in its folder
kept moving, and the live card read 'stalled' -- alive -- for up to 45 min.  When the run has a
clock.open.json, its beat decides; a run from before the clock keeps the mtime rule."""
from __future__ import annotations

from studio.command_center import progress_view as pv

NOW = 10_000.0


def test_a_live_drive_process_is_alive():
    assert pv.run_alive(True, None, False, NOW)


def test_a_fresh_beat_is_alive_and_an_old_one_is_not_whatever_the_files_say():
    assert pv.run_alive(False, NOW - 50, False, NOW)
    assert not pv.run_alive(False, NOW - 1100, True, NOW)


def test_a_run_without_a_clock_falls_back_to_its_files():
    assert pv.run_alive(False, None, True, NOW) and not pv.run_alive(False, None, False, NOW)
