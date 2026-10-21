"""Five-iterations build B15.2 (2026-10-20): the 13 s VLM read has a named
mechanism (decode of a 174-token pretty-printed reply, 28 % GPU) but no
measure of setup against decode, and B15's -10 min is the plan's softest
number.  Every engine read now appends one row to vlm_calls.jsonl --
workflow, wall seconds, the engine's own execution seconds, reply chars and
an estimated token count -- so ep02's ~230 reads fit seconds = a + b * tokens.
The conftest turns the log off; this test points it at tmp.  No server."""
from __future__ import annotations

import json

from studio import comfy

RECORD = {"outputs": {"3": {"text": ['{"faults": [], "people": 2}']}},
          "status": {"completed": True, "status_str": "success",
                     "messages": [["execution_start", {"prompt_id": "p", "timestamp": 1_000_000}],
                                  ["execution_cached", {"prompt_id": "p", "timestamp": 1_000_010}],
                                  ["execution_success", {"prompt_id": "p", "timestamp": 1_012_400}]]}}


def test_the_row_carries_seconds_engine_seconds_and_reply_size():
    row = comfy.call_row("take_content_qwen3vl", 13.456, RECORD["outputs"]["3"]["text"][0], RECORD)
    assert row["workflow"] == "take_content_qwen3vl" and row["seconds"] == 13.46
    assert row["node_s"] == 12.4
    assert row["answer_chars"] == 27 and row["answer_tokens"] == 7


def test_a_record_without_stamps_has_no_engine_seconds():
    assert comfy.call_row("w", 1.0, "", {"status": {}})["node_s"] is None


def test_run_text_appends_one_row_per_engine_read(monkeypatch, real_comfy, tmp_path):
    log = tmp_path / "vlm_calls.jsonl"
    monkeypatch.setattr(comfy, "VLM_CALLS", log)
    monkeypatch.setattr(comfy, "load_workflow",
                        lambda name: ({"2": {"inputs": {"text": ""}}}, {"prompt": {"node": "2", "field": "text"}}))
    monkeypatch.setattr(comfy, "submit", lambda wf: "job-1")
    monkeypatch.setattr(comfy, "wait_record", lambda prompt_id, timeout: RECORD)
    comfy.run_text("take_content_qwen3vl", {"prompt": "list"})
    comfy.run_text("take_content_qwen3vl", {"prompt": "list"})
    rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 2 and rows[0]["node_s"] == 12.4 and "ts" in rows[0]


def test_the_default_test_run_logs_nothing():
    assert comfy.VLM_CALLS is None
    comfy.log_call({"workflow": "w"})          # a no-op, never a write under library/
