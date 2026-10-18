"""Every episode step has a round cap and a wall (owner 2026-10-18: "implement it now", the caps
of docs/audit/2026-10-18_step_caps/STEP_CAPS.md).

The cap table is DATA (stages.yaml `episode.caps`, read by studio/step_caps), never constants
scattered over the ladders.  A per-episode count is persisted in episodes/epNN/attempts.json
(studio/step_attempts), so a drive run, a relaunch or an autopilot cure reads the same count.
"""
from __future__ import annotations

import pytest

from studio import registry, step_attempts, step_caps


def test_the_table_is_read_from_the_registry_and_names_every_episode_step():
    rows = step_caps.table()
    steps = {s["id"] for s in registry.steps("episode")}
    assert {c.step for c in rows.values()} == steps
    assert all(c.rounds >= 1 and c.wall_s > 0 for c in rows.values())


def test_the_owner_approved_numbers():
    t = step_caps.table()
    assert (t["plan"].rounds, t["plan"].wall_s, t["plan"].climbs) == (3, 30 * 60, 2)
    assert (t["regrid"].rounds, t["regrid"].per, t["regrid"].wall_s) == (2, "episode", 20 * 60)
    assert (t["retakes"].rounds, t["retakes"].per, t["retakes"].wall_s) == (2, "episode", 45 * 60)
    assert (t["master_eye"].rounds, t["master_eye"].wall_s) == (1, 30 * 60)
    assert (t["voice"].rounds, t["places"].rounds, t["face_refine"].rounds) == (2, 3, 1)
    assert t["bind"].wall_s == 120 and t["takes"].wall_s == 120 * 60


def test_a_steps_wall_is_the_sum_of_its_rows_and_a_climb_counts_per_climb():
    assert step_caps.step_wall_s("01") == 2 * 60
    assert step_caps.step_wall_s("02") == 30 * 60 * 2
    assert step_caps.step_wall_s("08") == (30 + 20) * 60
    assert step_caps.step_wall_s("99") == 0


def test_a_gate_finds_its_row():
    assert step_caps.for_gate("EYE_TAKES").name == "retakes"
    assert step_caps.for_gate("MASTER").name == "master_eye"
    assert step_caps.for_gate("LAYOUT") is None


def test_a_count_survives_a_fresh_read(tmp_path):
    assert step_attempts.count(tmp_path, "retakes") == 0
    step_attempts.spend(tmp_path, "retakes", seconds=90.0)
    step_attempts.spend(tmp_path, "retakes", seconds=30.0)
    assert step_attempts.count(tmp_path, "retakes") == 2
    assert step_attempts.seconds(tmp_path, "retakes") == pytest.approx(120.0)
    assert (tmp_path / step_attempts.FILE).exists()


def test_a_per_episode_row_is_spent_by_rounds_or_by_seconds(tmp_path):
    cap = step_caps.table()["retakes"]
    assert not step_attempts.spent(tmp_path, cap)
    step_attempts.spend(tmp_path, "retakes", seconds=cap.wall_s)
    assert step_attempts.spent(tmp_path, cap)            # the wall, one round in
    other = tmp_path / "b"
    step_attempts.spend(other, "retakes")
    step_attempts.spend(other, "retakes")
    assert step_attempts.spent(other, cap)                # the rounds


def test_the_cap_line_says_rounds_time_and_what_was_kept():
    line = step_caps.cap_line("retakes", 2, 2, 754.0, 3)
    assert line == "CAP retakes: 2/2 rounds, 12:34, kept best (3 advisories)"
