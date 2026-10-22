"""Every model load is one row in the changeover ledger: the model, why it loaded, and its seconds (craft ruling A27).

The GPU grouping rule (each model loads once, its jobs batched) had no measure: `free_on_family` frees the engine
when the family changes and nothing recorded what the change cost.  Checked first: five-iterations B15.2 logs each
VLM text read (library/vlm_calls.jsonl) and RETRO item 15 timed the step-03 vision reads; neither records a load.
Now the free opens a changeover and the first job that completes on the new family closes it with one row in
library/changeovers.jsonl: {model, why, seconds (free to first job done), node_s (the engine's own window)}."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from studio import comfy

RECORD = {"status": {"completed": True, "messages": [["execution_start", {"timestamp": 1000_000}],
                                                     ["execution_success", {"timestamp": 1042_500}]]}}


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    path = tmp_path / "changeovers.jsonl"
    monkeypatch.setattr(comfy, "CHANGEOVERS", path)
    monkeypatch.setattr(comfy, "LAST_FAMILY", "krea")
    return path


def rows(path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def test_a_fake_load_writes_one_row_with_seconds(ledger):
    assert comfy.free_on_family("h3")
    comfy.changed_over(RECORD)
    comfy.changed_over(RECORD)                      # the second job on the family is no load
    [row] = rows(ledger)
    assert row["model"] == "h3" and row["why"] == "krea -> h3"
    assert row["seconds"] >= 0 and row["node_s"] == 42.5


def test_the_same_family_loads_nothing(ledger):
    assert not comfy.free_on_family("krea")
    comfy.changed_over(RECORD)
    assert rows(ledger) == []


def test_a_ledger_that_cannot_be_written_never_fails_the_job(ledger, monkeypatch):
    monkeypatch.setattr(comfy, "CHANGEOVERS", ledger.parent / "no" / "such" / "dir" / "x.jsonl")
    comfy.free_on_family("h3")
    comfy.changed_over(RECORD)


def test_no_ledger_in_a_test_writes_nothing(monkeypatch):
    assert comfy.CHANGEOVERS is None


CHILD = """
import json, sys
from pathlib import Path
from studio import comfy
comfy.CHANGEOVERS = Path(sys.argv[1])
comfy.changed_over(json.loads(sys.argv[2]))
"""


def test_the_job_in_the_steps_own_process_closes_the_drives_free(ledger):
    """Wave-3 review: the drive frees (step_runner._free_family) and the step's script, a child process
    (stage_run.launch), waits on the job; an open changeover held in one process's memory wrote no row in
    production.  The open changeover is on disk, and the first job done in any process closes it."""
    comfy.free_on_family("h3")
    root = Path(comfy.__file__).resolve().parents[1]
    subprocess.run([sys.executable, "-c", CHILD, str(ledger), json.dumps(RECORD)], cwd=root, check=True)
    [row] = rows(ledger)                            # written by the child, the job that ran after the free
    comfy.changed_over(RECORD)                      # the drive's own later job is no load
    assert rows(ledger) == [row]
    assert row["model"] == "h3" and row["why"] == "krea -> h3" and row["node_s"] == 42.5
