"""The live card's liveness must not need process visibility (2026-10-07: ep23's
run, launched by another session, was invisible to the API and the card said
"dead" while takes rendered).  vitals.files_alive reads the unit folder's own
mtimes; the card counts a run alive when the pid answers OR the files move."""
from __future__ import annotations

import os
import time
from pathlib import Path

from studio.command_center import vitals

SRC = (Path(__file__).parent.parent / "studio" / "command_center" / "progress_view.py").read_text(encoding="utf-8")


def _home(tmp_path, old_s):
    home = tmp_path / "ep"
    (home / "takes").mkdir(parents=True)
    stamp = time.time() - old_s
    for p in (home, home / "takes"):
        os.utime(p, (stamp, stamp))
    return home


def test_moving_files_read_alive_and_still_files_do_not(tmp_path):
    assert vitals.files_alive(_home(tmp_path / "a", 60), time.time()) is True
    assert vitals.files_alive(_home(tmp_path / "b", 3 * 86400), time.time()) is False


def test_a_missing_folder_is_not_alive(tmp_path):
    assert vitals.files_alive(tmp_path / "nowhere", time.time()) is False


def test_the_card_counts_files_beside_the_pid():
    assert "files_alive" in SRC and "pid_alive" in SRC
