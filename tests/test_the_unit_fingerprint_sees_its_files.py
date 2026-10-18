"""A unit's fingerprint sees the files its bands draw (page experts 2026-10-18, D4 / backend #4):
it digested only DB columns, so a verdict or a learning written mid-step (09 renders for hours
with no event) reached the page up to a minute late, on the minute bucket.  Four stats -- the
folder, learnings.jsonl, the newest run log, clock.open.json -- now move it."""
from __future__ import annotations

import os
import time

from command_center_fixtures import CODEX, make_library
from studio.command_center import pulse


def test_a_new_learning_moves_the_units_file_stamps(tmp_path, monkeypatch):
    library = make_library(tmp_path, monkeypatch)
    before = pulse.unit_files(library, "episode", CODEX, "ep04")
    home = next(library.glob(f"{CODEX}_*")) / "episodes" / "ep04"
    with (home / "learnings.jsonl").open("a", encoding="utf-8") as f:
        f.write('{"gate": "PLAN"}\n')
    os.utime(home / "learnings.jsonl", (time.time() + 5, time.time() + 5))
    assert pulse.unit_files(library, "episode", CODEX, "ep04") != before


def test_a_unit_without_a_folder_or_another_stage_has_no_stamps(tmp_path, monkeypatch):
    library = make_library(tmp_path, monkeypatch)
    assert pulse.unit_files(library, "episode", CODEX, "ep99") == ()
    assert pulse.unit_files(library, "screenplay", CODEX, "book") == ()
    assert pulse.unit_files(None, "episode", CODEX, "ep04") == ()


def test_the_pulse_map_and_the_one_key_agree_with_the_library(tmp_path, monkeypatch):
    # the 204 check (app._unchanged) and data-v (viz.fp) must read the same stamps as the pulse
    from command_center_fixtures import make_db
    from studio import db
    library = make_library(tmp_path, monkeypatch)
    conn = db.get_connection(make_db(tmp_path, library))
    key, now = f"unit:episode/{CODEX}/ep04", time.time()
    assert pulse.fingerprints(conn, now, library).get(key, pulse.fingerprint(conn, key, now, library)) == \
        pulse.fingerprint(conn, key, now, library)
    assert pulse.fingerprint(conn, key, now, library) != pulse.fingerprint(conn, key, now, None)


def test_the_stamps_are_in_the_digest():
    row, now = ("running", "09", None, 0, "2026-10-18T20:00:00Z", None, 7, 0), 1e9
    assert pulse.unit_fp(row, (1, None), (0, 0, None), now, (1, 2)) != pulse.unit_fp(row, (1, None), (0, 0, None), now, (1, 3))
