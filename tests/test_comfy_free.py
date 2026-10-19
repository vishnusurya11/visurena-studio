"""K10: the engine is freed at a model-family boundary, not per call, and never raises."""
from __future__ import annotations

from studio import comfy


def counted(monkeypatch):
    calls = []
    monkeypatch.setattr(comfy, "free_models", lambda: calls.append(1))
    monkeypatch.setattr(comfy, "LAST_FAMILY", None)
    return calls


def test_free_called_on_family_change_only(monkeypatch):
    calls = counted(monkeypatch)
    assert comfy.free_on_family("krea") is True       # first family seen: another process may have staged models
    assert comfy.free_on_family("vl") is True
    assert comfy.free_on_family("vl") is False
    assert comfy.free_on_family("vl") is False
    assert len(calls) == 2                           # krea (first) and krea -> vl; the repeats free nothing


def test_free_on_family_never_raises(monkeypatch):
    monkeypatch.setattr(comfy, "LAST_FAMILY", "h3")

    def boom():
        raise RuntimeError("engine gone")
    monkeypatch.setattr(comfy, "free_models", boom)
    assert comfy.free_on_family("vl") is False
    assert comfy.LAST_FAMILY == "vl"


def test_a_blank_family_changes_nothing(monkeypatch):
    calls = counted(monkeypatch)
    assert comfy.free_on_family("") is False and calls == []


def test_queue_counts_strict_raises_when_the_engine_is_down():
    def fetch(path):
        raise ConnectionError("refused")
    import pytest
    with pytest.raises(ConnectionError):
        comfy.queue_counts_strict(fetch=fetch)
    assert comfy.queue_counts(fetch=fetch) == (0, 0)
