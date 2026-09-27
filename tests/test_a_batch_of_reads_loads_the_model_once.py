"""A batch of vision reads loads the model once and always frees it after.

MEASURED 2026-09-27 (speed plan #6): each read reloaded the 16 GB VL model
(~9.7 s of a ~27.5 s read) because the workflow says keep_model_loaded:
false.  Inside `model_kept()` every text job keeps it; the batch always ends
with /free, because VL left beside MiniMax-H3 once took 6:52 to load
(studio/describe.py:208)."""
import pytest

from studio import comfy

TEMPLATE = ({"1": {"inputs": {"keep_model_loaded": False, "prompt": ""}}, "2": {"inputs": {}}},
            {"prompt": {"node": "1", "field": "prompt"}})


def engine(monkeypatch):
    sent, freed = [], []
    monkeypatch.setattr(comfy, "load_workflow", lambda name: TEMPLATE)
    monkeypatch.setattr(comfy, "submit", lambda prompt: sent.append(prompt) or "id")
    monkeypatch.setattr(comfy, "wait_record", lambda pid, timeout=600.0: {"outputs": {}})
    monkeypatch.setattr(comfy, "free_models", lambda: freed.append(1))
    return sent, freed


def test_inside_a_batch_the_model_is_kept_and_freed_at_the_end(monkeypatch, real_comfy):
    sent, freed = engine(monkeypatch)
    with comfy.model_kept():
        comfy.run_text("caption", {"prompt": "a"})
        comfy.run_text("caption", {"prompt": "b"})
    assert [p["1"]["inputs"]["keep_model_loaded"] for p in sent] == [True, True]
    assert freed == [1]


def test_outside_a_batch_the_workflow_is_as_written(monkeypatch, real_comfy):
    sent, freed = engine(monkeypatch)
    comfy.run_text("caption", {"prompt": "a"})
    assert sent[0]["1"]["inputs"]["keep_model_loaded"] is False and freed == []


def test_a_batch_that_fails_still_frees_the_model(monkeypatch):
    _, freed = engine(monkeypatch)
    with pytest.raises(RuntimeError):
        with comfy.model_kept():
            raise RuntimeError("reader died")
    assert freed == [1]
