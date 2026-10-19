"""model_kept is re-entrant: only the outermost batch frees, on enter and on exit."""
from __future__ import annotations

from studio import comfy


def test_nested_model_kept_frees_once(monkeypatch):
    calls = []
    monkeypatch.setattr(comfy, "free_models", lambda: calls.append(comfy.KEEP_LOADED))
    with comfy.model_kept():
        with comfy.model_kept():
            assert comfy.KEEP_LOADED is True
        assert comfy.KEEP_LOADED is True            # the inner exit did not drop the keep
    assert comfy.KEEP_LOADED is False
    assert len(calls) == 2                          # one on enter, one on exit, none for the inner


def test_a_failure_inside_still_resets_depth(monkeypatch):
    monkeypatch.setattr(comfy, "free_models", lambda: None)
    try:
        with comfy.model_kept():
            raise ValueError("x")
    except ValueError:
        pass
    assert comfy.KEEP_DEPTH == 0 and comfy.KEEP_LOADED is False
