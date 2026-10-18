"""A run whose clock still beats is not 'the runner may be gone' (page experts 2026-10-18, B1,
board half): the lease (900 s) renews only on a step event, so the LLM plan step lapsed it at
20:35Z while clock.open.json beat every 60 s; the head said '~ stale lease' beside LIVE.  The
board now reads the run's own beat; the runner half (the beat renews the lease) follows."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from studio.command_center import unit_view as uv

NOW = datetime(2026, 10, 18, 20, 50, tzinfo=timezone.utc)
ROW = {"state": "running", "lease_until": "2026-10-18T20:35:00Z", "run_id": "R2"}


def test_a_lapsed_lease_with_a_fresh_beat_is_alive():
    got = uv.lease(ROW, NOW, beat=NOW.timestamp() - 40)
    assert got["state"] == "beating"


def test_a_lapsed_lease_with_an_old_beat_is_stale():
    assert uv.lease(ROW, NOW, beat=NOW.timestamp() - 900)["state"] == "stale"
    assert uv.lease(ROW, NOW)["state"] == "stale"


def test_the_beat_is_this_runs_only(tmp_path):
    (tmp_path / "clock.open.json").write_text(json.dumps({"run_id": "R2", "last_beat": 123.0}), encoding="utf-8")
    assert uv.run_beat(tmp_path, ROW) == 123.0
    assert uv.run_beat(tmp_path, {**ROW, "run_id": "R1"}) is None and uv.run_beat(None, ROW) is None
