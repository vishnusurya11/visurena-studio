"""The step-09 first-render wall is the episode's, not the process's.

Jekyll Kawajiri ep01 (2026-10-18): `began` was a per-process `time.time()`, so every relaunch of the
takes step started its 120-minute wall again.  The seconds now ride in attempts.json `takes.first`."""
from __future__ import annotations

from scripts.episode import takes_r2v as tr

WALL = 120 * 60


def test_relaunch_does_not_reset_the_first_render_wall():
    assert tr.first_wall_spent(0.0, 30 * 60, [], prior_s=100 * 60) is True
    assert tr.first_wall_spent(0.0, 30 * 60, [], prior_s=0.0) is False


def test_the_prior_seconds_are_booked_on_exit_and_read_back(tmp_path):
    assert tr.prior_first_seconds(tmp_path) == 0.0
    tr.book_first_seconds(tmp_path, 1000.0, 1000.0 + 70 * 60, [])
    assert tr.prior_first_seconds(tmp_path) == 70 * 60
    tr.book_first_seconds(tmp_path, 5000.0, 5000.0 + 60 * 60, [])
    assert tr.prior_first_seconds(tmp_path) == 130 * 60
    assert tr.first_wall_spent(9000.0, 9000.0 + 1, [], prior_s=tr.prior_first_seconds(tmp_path))


def test_a_retake_pass_books_nothing(tmp_path):
    tr.book_first_seconds(tmp_path, 0.0, 600.0, [3])
    assert tr.prior_first_seconds(tmp_path) == 0.0
