"""A-ledger asks for a timing row per step that RAN (2026-10-21_ep02_proof DESIGN 3.1).

The first real window's S0a failed A-ledger with "step 01 has no timing row": the drive log said
`--- step 01 (bind) skipped: output exists`, and steps_since read every `--- step NN` line as a step
that ran.  A skipped step writes no timing row by design; only the started form
`--- step NN (name) | <label> ---` is a step that ran."""
from __future__ import annotations

from scripts.proof import rehearse

LOG = ("=== EPISODE start | 9999 episode/ep01 | run r ===\n"
       "--- step 01 (bind) skipped: output exists\n"
       "--- step 02 (plan) | 9999 episode/ep01 ---\n"
       "STEP 02 start 17:43:49 (plan, wall 60:00)\n")


def test_a_skipped_step_is_not_counted_as_a_step_that_ran(tmp_path):
    (tmp_path / "drive_run01.log").write_text(LOG, encoding="utf-8")
    assert rehearse.steps_since(tmp_path, 0.0) == ["02"]


def test_a_log_older_than_the_point_counts_nothing(tmp_path):
    (tmp_path / "drive_run01.log").write_text(LOG, encoding="utf-8")
    assert rehearse.steps_since(tmp_path, 4.0e9) == []
