"""A4 (fleet E, 2026-10-22): a timed-out /prompt adopts only the job it posted.

`submit` asked the queue for a job writing the same `filename_prefix`.  Constant prefixes
(`trailer_say` for every spoken line, `ep_bed`, `ep_title`) and an index-only take prefix
(`ep_take_05` in any episode) let a timed-out line adopt another line's prompt id: a silent
wrong take.  The job's identity is now a client prompt id (ComfyUI takes one in the POST body,
0.41.2 server.py), asked of the queue and the history before one more POST."""
from __future__ import annotations

import json
import uuid

import pytest

from studio import comfy

SAY = {"9": {"class_type": "SaveAudio", "inputs": {"filename_prefix": "trailer_say"}}}


class Reply:
    def __init__(self, body: dict):
        self.body = json.dumps(body).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self.body


@pytest.fixture
def engine(monkeypatch):
    """A POST that times out once; `seen` holds the ids posted, `queue`/`history` what the engine says."""
    state = {"seen": [], "queue": {"queue_running": [], "queue_pending": []}, "history": {}, "timeouts": 1}

    def urlopen(request, timeout=None):
        sent = json.loads(request.data)
        state["seen"].append(sent.get("prompt_id"))
        if state["timeouts"]:
            state["timeouts"] -= 1
            raise TimeoutError("the engine answered slowly")
        return Reply({"prompt_id": sent.get("prompt_id") or "minted", "number": 1, "node_errors": {}})

    def get(path):
        return state["queue"] if path == "/queue" else state["history"]
    monkeypatch.setattr(comfy, "wait_foreign_claims", lambda: False)
    monkeypatch.setattr(comfy.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(comfy, "_get", get)
    return state


def test_a_line_never_adopts_another_lines_job_with_the_same_prefix(engine):
    engine["queue"]["queue_pending"] = [[1, "other-line", SAY]]
    got = comfy.submit(SAY)
    assert got != "other-line" and len(engine["seen"]) == 2 and got == engine["seen"][-1]


def test_a_job_the_slow_engine_already_queued_is_adopted_without_a_second_post(engine, monkeypatch):
    own = str(uuid.uuid4())
    monkeypatch.setattr(comfy.uuid, "uuid4", lambda: uuid.UUID(own))
    engine["queue"]["queue_running"] = [[1, own, SAY]]
    assert comfy.submit(SAY) == own and engine["seen"] == [own]


def test_a_job_that_already_finished_is_adopted_from_the_history(engine, monkeypatch):
    own = str(uuid.uuid4())
    monkeypatch.setattr(comfy.uuid, "uuid4", lambda: uuid.UUID(own))
    engine["history"] = {own: {"outputs": {}}}
    assert comfy.submit(SAY) == own and engine["seen"] == [own]


def test_the_post_carries_a_canonical_client_id(engine):
    engine["timeouts"] = 0
    got = comfy.submit(SAY)
    assert got == engine["seen"][0] and str(uuid.UUID(got)) == got
