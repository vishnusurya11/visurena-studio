"""The engine's partial accept (GPU transcript 2026-10-21, error_invalid_graph.json case A): a broken
graph whose other output still validates is answered HTTP 200 with `node_errors` filled in, queued
without the broken outputs, and ends "success" with no picture.  `submit` must read that answer as a
rejection, and `texts_of` must read the subgraph node ids ("30:20") such a record carries."""
from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from studio import comfy

RECORDED = json.loads((Path(__file__).parent / "fixtures" / "proof" / "comfy_classes" /
                       "error_invalid_graph.json").read_text(encoding="utf-8"))["partial_accept"]


def _engine(monkeypatch, reply: dict) -> list:
    """urlopen answering /prompt with `reply` (HTTP 200) and logging every other request."""
    sent = []

    def fake_urlopen(request, timeout=None):
        sent.append((request.full_url, request.data))
        return io.BytesIO(json.dumps(reply).encode("utf-8") if request.full_url.endswith("/prompt") else b"{}")
    monkeypatch.setattr(comfy, "wait_foreign_claims", lambda: False)
    monkeypatch.setattr(comfy.urllib.request, "urlopen", fake_urlopen)
    return sent


def test_a_partly_accepted_graph_raises_naming_the_broken_node(monkeypatch):
    _engine(monkeypatch, RECORDED["prompt_response"])
    with pytest.raises(RuntimeError, match="30:3") as caught:
        comfy.submit(RECORDED["submitted_graph"])
    assert "required_input_missing" in str(caught.value)


def test_the_remnant_of_a_partly_accepted_graph_is_taken_off_the_queue(monkeypatch):
    sent = _engine(monkeypatch, RECORDED["prompt_response"])
    with pytest.raises(RuntimeError):
        comfy.submit(RECORDED["submitted_graph"])
    deletes = [json.loads(body) for url, body in sent if url.endswith("/queue")]
    assert deletes == [{"delete": [RECORDED["prompt_response"]["prompt_id"]]}]


def test_a_clean_accept_still_returns_its_prompt_id(monkeypatch):
    sent = _engine(monkeypatch, {"prompt_id": "job-7", "number": 3, "node_errors": {}})
    assert comfy.submit(RECORDED["submitted_graph"]) == "job-7"
    assert [url for url, _ in sent if not url.endswith("/prompt")] == []


def test_texts_of_reads_subgraph_node_ids_in_node_order():
    record = {"outputs": {"30:20": {"text": ["sub"]}, "5": {"text": ["top"]}, "30:4": {"text": ["first sub"]}}}
    assert comfy.texts_of(record) == ["top", "first sub", "sub"]


def test_texts_of_reads_the_recorded_partial_accept_record():
    assert comfy.texts_of(RECORDED["history_entry"]) == RECORDED["history_entry"]["outputs"]["30:20"]["text"]
