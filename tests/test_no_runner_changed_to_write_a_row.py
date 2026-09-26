"""The ruling (decision 2026-09-25, "events vs rows"): the work-order row is
upserted inside db.add_event -- one place, zero runner edits.  No runner, step
runner or stage context names a work_order row or its writer; the only writer is
db.add_event -> db.project_event.  `work_orders` as a WORD (C6's orders/holds
module) is not a row write and is not what this guards."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNNERS = ("episode.py", "refs.py", "analysis.py", "screenplay.py", "trailer.py",
           "studio/step_runner.py", "studio/stage_run.py", "studio/episode_run.py")
ROW_WRITE = re.compile(r"\bwork_order\b|upsert_work_order|project_event"
                       r"|INTO work_orders|UPDATE work_orders", re.IGNORECASE)


@pytest.mark.parametrize("name", RUNNERS)
def test_no_runner_names_a_work_order_row(name):
    source = (ROOT / name).read_text(encoding="utf-8")
    hits = [line for line in source.splitlines() if ROW_WRITE.search(line)]
    assert hits == [], f"{name} writes or reads a work-order row: {hits}"


def test_the_only_writer_is_add_event_through_project_event():
    source = (ROOT / "studio" / "db.py").read_text(encoding="utf-8")
    body = source[source.index("def add_event("):source.index("def unit_status(")]
    assert "project_event(" in body and "UPDATE events SET order_id" in body
