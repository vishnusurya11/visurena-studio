"""Refresh fix (lead brief 2026-10-06, A1): every change the sections render
reaches a fingerprint -- DB writes (events, work orders, orders, holds, flags)
AND pure clock flips.  views.LAPSED_SQL turns a running row stale the moment
its lease passes NOW with no write at all, so each section's fingerprint must
carry a cheap lapsed count, and a lease expiry must change the fingerprint
within one poll.  The age bucket's granularity must match the unit the views
actually print.  All on a temp DB, at a fixed `now`, deterministic."""
from __future__ import annotations

import time
from datetime import datetime, timezone

import pytest

from command_center_fixtures import CODEX, make_db, make_library
from studio import db
from studio.command_center import app as cc_app
from studio.command_center import pulse, views

UNIT_KEY = f"unit:episode/{CODEX}/ep04"
ALL_KEYS = ("floor", "attention", "orders", "lanes", "dept:episode", "dept:refs",
            f"book:{CODEX}", UNIT_KEY)
PAST, FUTURE = "2000-01-01T00:00:00Z", "2099-01-01T00:00:00Z"


@pytest.fixture()
def board_db(tmp_path, monkeypatch):
    """The seeded tmp DB's path; ep04 runs on the GPU with a live lease."""
    library = make_library(tmp_path, monkeypatch)
    path = make_db(tmp_path, library)
    conn = db.get_connection(path)
    conn.execute("UPDATE work_orders SET lease_until = ? WHERE unit = 'ep04'", (FUTURE,))
    conn.commit()
    conn.close()
    return path


def reader(path):
    return cc_app.readonly_factory(path)()


def writer(path, sql, args=()):
    conn = db.get_connection(path)
    conn.execute(sql, args)
    conn.commit()
    conn.close()


# --- the mutation table: (how, must change, must not change) ---


def an_event(path):
    conn = db.get_connection(path)
    db.add_event(conn, CODEX, "episode", "09", "completed", run_id="r4", unit="ep04")
    conn.close()


def a_work_order_write(path):
    conn = db.get_connection(path)
    db.upsert_work_order(conn, CODEX, "episode", "ep04", progress="19/25")
    conn.close()


def an_order(path):
    writer(path, "INSERT INTO orders (ts, kind, scope, codex_id, stage, unit)"
                 " VALUES ('2026-10-06T00:00:00Z', 'redo', 'unit', ?, 'episode', 'ep04')", (CODEX,))


def a_hold(path):
    writer(path, "INSERT INTO holds (scope, reason, held_at)"
                 " VALUES ('studio', 'night', '2026-10-06T00:00:00Z')")


def flags_raised(path):
    conn = db.get_connection(path)
    db.upsert_work_order(conn, CODEX, "episode", "ep03", flags=3)
    conn.close()


def a_lease_expiry(path):
    """The clock flip: no row written, the lease just passes NOW (LAPSED_SQL)."""
    writer(path, "UPDATE work_orders SET lease_until = ? WHERE unit = 'ep04'", (PAST,))


MUTATIONS = [
    (an_event, {"floor", "lanes", "dept:episode", f"book:{CODEX}", UNIT_KEY},
     {"orders", "dept:refs"}),
    (a_work_order_write, {"floor", "lanes", "dept:episode", f"book:{CODEX}", UNIT_KEY},
     {"orders", "dept:refs"}),
    (an_order, {"orders", "attention", UNIT_KEY},
     {"floor", "lanes", "dept:episode", "dept:refs", f"book:{CODEX}"}),
    (a_hold, {"floor", "dept:episode", "dept:refs", f"book:{CODEX}", UNIT_KEY},
     {"orders", "lanes", "attention"}),
    (flags_raised, {"attention", "floor", "lanes", "dept:episode", f"book:{CODEX}"},
     {"orders", "dept:refs"}),
    # Referee D1 (2026-10-06): a dead run's unit must land in Needs you, so the
    # attention fp flips on the clock too -- reversing the first pass's exclusion.
    (a_lease_expiry, {"floor", "lanes", "attention", "dept:episode", f"book:{CODEX}", UNIT_KEY},
     {"orders", "dept:refs"}),
]


@pytest.mark.parametrize("mutate,changed,same", MUTATIONS, ids=lambda m: getattr(m, "__name__", ""))
def test_each_change_moves_its_fingerprints_and_no_other(board_db, mutate, changed, same):
    now = time.time()
    before = pulse.fingerprints(reader(board_db), now)
    mutate(board_db)
    after = pulse.fingerprints(reader(board_db), now)
    for key in changed:
        assert after[key] != before[key], f"{key} must change on {mutate.__name__}"
    for key in same:
        assert after[key] == before[key], f"{key} must hold on {mutate.__name__}"


def test_a_quiet_studio_at_one_instant_answers_identical_fingerprints(board_db):
    now = time.time()
    first = pulse.fingerprints(reader(board_db), now)
    second = pulse.fingerprints(reader(board_db), now)
    assert first == second
    for key in ALL_KEYS:
        assert key in first, key


# --- the clock flip in each aggregate ---


def test_totals_count_the_lapsed_leases(board_db):
    assert pulse.totals(reader(board_db))["lapsed"] == (0,)
    a_lease_expiry(board_db)
    assert pulse.totals(reader(board_db))["lapsed"] == (1,)


def test_group_marks_carry_a_lapsed_count_per_group(board_db):
    a_lease_expiry(board_db)
    marks = pulse.group_marks(reader(board_db), "stage")
    assert marks["episode"][3] == 1 and marks["refs"][3] == 0
    assert all(len(m) == 5 for m in marks.values())


def test_the_unit_row_says_whether_its_lease_lapsed(board_db):
    assert pulse.unit_row(reader(board_db), "episode", CODEX, "ep04")[-1] == 0
    a_lease_expiry(board_db)
    assert pulse.unit_row(reader(board_db), "episode", CODEX, "ep04")[-1] == 1


def test_a_lease_expiry_moves_the_shell_off_the_lapsed_run(board_db):
    progress = lambda codex, unit: None
    before = pulse.shell_block(reader(board_db), progress)
    a_lease_expiry(board_db)
    after = pulse.shell_block(reader(board_db), progress)
    assert pulse.shell_fp(after) != pulse.shell_fp(before)
    assert after["pins"] == [] and after["gpu"] is None
    assert after["dept_dots"]["episode"]["stale"] == 1


def test_a_single_key_fingerprint_still_matches_the_map_after_a_lapse(board_db):
    a_lease_expiry(board_db)
    now = time.time()
    conn = reader(board_db)
    fps = pulse.fingerprints(conn, now)
    for key in ("floor", "lanes", "dept:episode", f"book:{CODEX}", UNIT_KEY):
        assert pulse.fingerprint(conn, key, now) == fps[key], key
    assert pulse.fingerprint(conn, "dept:ghost", now)


# --- the age bucket against what the views print ---


def test_the_bucket_granularity_is_the_printed_age_unit():
    now_dt = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    now = now_dt.timestamp()
    for seconds in (0, 59, 61, 3599, 3600, 7200, 86399, 86400, 10 * 86400):
        printed = views.age(now_dt, pulse.iso(now - seconds))
        unit = "m" if printed == "now" else printed.split()[-1]
        assert pulse.bucket(now, now - seconds)[0] == unit, f"{seconds}s prints '{printed}'"


def test_each_bucket_ticks_at_its_own_granularity():
    now = 100 * 86400.0
    assert pulse.bucket(now, now - 61) != pulse.bucket(now + 60, now - 61)
    assert pulse.bucket(now, now - 7200) != pulse.bucket(now + 3600, now - 7200)
    assert pulse.bucket(now, now - 2 * 86400) != pulse.bucket(now + 86400, now - 2 * 86400)
    assert pulse.bucket(now, now - 2 * 86400, running=True) != pulse.bucket(now + 60, now - 2 * 86400, running=True)
