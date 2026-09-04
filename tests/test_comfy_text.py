"""ComfyUI text outputs: a PreviewAny node reports `{"text": [...]}` in the
history record, not a file, so `outputs_of` never sees it."""
from __future__ import annotations

from studio import comfy

RECORD = {"outputs": {"3": {"text": ["a pale man in a bowler hat"]},
                      "4": {"images": [{"filename": "x.png", "type": "output"}]}},
          "status": {"completed": True, "status_str": "success"}}


def test_texts_of_collects_every_text_output_in_node_order():
    record = {"outputs": {"5": {"text": ["second"]}, "3": {"text": ["first", "also"]},
                          "4": {"images": [{"filename": "x.png"}]}}}
    assert comfy.texts_of(record) == ["first", "also", "second"]


def test_texts_of_ignores_non_strings_and_empty_records():
    assert comfy.texts_of({"outputs": {"3": {"text": [None, 4]}}}) == []
    assert comfy.texts_of({}) == []


def test_run_text_returns_the_joined_text_of_the_finished_job(monkeypatch):
    seen = {}
    monkeypatch.setattr(comfy, "load_workflow",
                        lambda name: ({"2": {"inputs": {"text": ""}}}, {"prompt": {"node": "2", "field": "text"}}))
    monkeypatch.setattr(comfy, "submit", lambda wf: seen.setdefault("workflow", wf) and "job-1")
    monkeypatch.setattr(comfy, "wait_record", lambda prompt_id, timeout: RECORD)
    assert comfy.run_text("image_qwen3vl_caption", {"prompt": "describe"}) == "a pale man in a bowler hat"
    assert seen["workflow"]["2"]["inputs"]["text"] == "describe"


def test_wait_record_returns_the_whole_record_on_completion(monkeypatch):
    monkeypatch.setattr(comfy, "history", lambda prompt_id: RECORD)
    assert comfy.wait_record("job-1", timeout=1.0) is RECORD
    assert comfy.wait("job-1", timeout=1.0) == comfy.outputs_of(RECORD)
