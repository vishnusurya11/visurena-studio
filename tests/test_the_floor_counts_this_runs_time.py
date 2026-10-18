"""The floor and Home count a running unit's time from THIS run (page experts 2026-10-18, D2):
'ep01 running 148h39' counted from the work order's first start on Oct 12, not from the
26-minute-old run.  The run id ends in its UTC start (tracking.make_run_id)."""
from __future__ import annotations

from studio.command_center import views

CODEX = "20260827135504"


def test_the_run_starts_at_its_ids_stamp():
    row = {"started_at": "2026-10-12T15:57:00Z", "run_id": f"{CODEX}__episode__20261018202034"}
    assert views.run_start(row) == "2026-10-18T20:20:34Z"


def test_a_row_without_a_stamped_run_falls_back_to_its_start():
    assert views.run_start({"started_at": "2026-10-12T15:57:00Z", "run_id": "r5"}) == "2026-10-12T15:57:00Z"
    assert views.run_start({"started_at": None, "run_id": None}) is None
