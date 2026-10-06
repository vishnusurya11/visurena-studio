"""A transient ComfyUI execution failure (HostBuffer.read_file_slice) or a
restarting engine is worth exactly ONE resubmission of the same filled graph;
a second failure, or any other error, is a real fault and propagates."""
from __future__ import annotations

import pytest

from studio import comfy


@pytest.fixture()
def engine(real_comfy, monkeypatch):
    """The conftest trap blocks comfy.run for every test; `real_comfy` gives
    it back here, with the server mocked underneath (submit, wait)."""
    calls = {"submitted": [], "waits": []}
    monkeypatch.setattr(comfy, "load_workflow", lambda name: ({}, {}))
    monkeypatch.setattr(comfy, "submit", lambda graph: calls["submitted"].append(graph) or "pid")

    def wait(pid, timeout=3600.0):
        answer = calls["waits"].pop(0)
        if isinstance(answer, BaseException):
            raise answer
        return answer
    monkeypatch.setattr(comfy, "wait", wait)
    return calls


def test_a_transient_failure_is_resubmitted_once_and_succeeds(engine):
    engine["waits"] = [RuntimeError("pid failed: LoadVideo: HostBuffer.read_file_slice error"), ["out.mp4"]]
    assert comfy.run("wf", {}) == ["out.mp4"]
    assert len(engine["submitted"]) == 2


def test_a_non_transient_failure_propagates_after_one_submit(engine):
    engine["waits"] = [RuntimeError("pid failed: OOM allocating tensor")]
    with pytest.raises(RuntimeError, match="OOM"):
        comfy.run("wf", {})
    assert len(engine["submitted"]) == 1


def test_a_lost_engine_is_retried_once_then_propagates(engine):
    engine["waits"] = [comfy.EngineLost("pid vanished: the engine restarted"),
                      comfy.EngineLost("pid vanished: the engine restarted")]
    with pytest.raises(comfy.EngineLost):
        comfy.run("wf", {})
    assert len(engine["submitted"]) == 2


def test_two_transient_failures_stay_a_fault_not_a_loop(engine):
    engine["waits"] = [RuntimeError("HostBuffer.read_file_slice"), RuntimeError("HostBuffer.read_file_slice")]
    with pytest.raises(RuntimeError, match="HostBuffer"):
        comfy.run("wf", {})
    assert len(engine["submitted"]) == 2


def test_the_transient_class_is_narrow():
    assert comfy.transient("LoadVideo: HostBuffer.read_file_slice failed")
    assert comfy.transient("worker read_file_slice timed out")
    assert not comfy.transient("ComfyUI rejected the workflow: bad node")
    assert not comfy.transient("")
