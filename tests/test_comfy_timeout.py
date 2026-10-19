"""A text call never outlives its row, and a timed-out one interrupts the engine."""
from __future__ import annotations

import pytest

from studio import comfy


def wired(monkeypatch, wait):
    monkeypatch.setattr(comfy, "load_workflow", lambda name: ({"2": {"inputs": {"text": ""}}},
                                                              {"prompt": {"node": "2", "field": "text"}}))
    monkeypatch.setattr(comfy, "submit", lambda wf: "job-1")
    monkeypatch.setattr(comfy, "wait_record", wait)
    sent = []
    monkeypatch.setattr(comfy, "interrupt", lambda: sent.append("interrupt"))
    return sent


def test_text_call_times_out_at_row_remaining_and_interrupts(monkeypatch, real_comfy):
    seen = {}

    def wait(prompt_id, timeout):
        seen["timeout"] = timeout
        raise comfy.StillRunning(prompt_id, timeout)
    sent = wired(monkeypatch, wait)
    monkeypatch.setattr(comfy.time, "time", lambda: 1000.0)
    with comfy.row_deadline(1100.0):                       # 100 s left -> 160 s allowed
        with pytest.raises(comfy.StillRunning):
            comfy.run_text("w", {"prompt": "p"}, timeout=600.0)
    assert seen["timeout"] == 160.0 and sent == ["interrupt"]


def test_the_calls_own_timeout_wins_when_shorter(monkeypatch, real_comfy):
    seen = {}
    wired(monkeypatch, lambda prompt_id, timeout: seen.setdefault("t", timeout) and {"outputs": {}})
    monkeypatch.setattr(comfy.time, "time", lambda: 1000.0)
    with comfy.row_deadline(5000.0):
        comfy.run_text("w", {"prompt": "p"}, timeout=90.0)
    assert seen["t"] == 90.0


def test_no_row_deadline_leaves_the_timeout_alone(monkeypatch, real_comfy):
    seen = {}
    wired(monkeypatch, lambda prompt_id, timeout: seen.setdefault("t", timeout) and {"outputs": {}})
    comfy.run_text("w", {"prompt": "p"}, timeout=600.0)
    assert seen["t"] == 600.0 and comfy.ROW_DEADLINE is None


def test_a_render_is_never_capped_by_the_row(monkeypatch):
    with comfy.row_deadline(1.0):
        assert comfy.text_timeout(3600.0, applies=False) == 3600.0
