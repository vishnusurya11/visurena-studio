"""Every VL reply a rehearsal serves names the gate that consumed it (DESIGN 2.3, 2.4, R3;
2026-10-21_ep02_proof P4).

A wrapper AROUND (never instead of) comfy.run_text / cached_text appends one row per outermost
read to <sandbox>/vl_consumers.jsonl: the engine's prompt id (None on a cache hit), the ask's
workflow name and the qualname of the studio function that asked.  P5 joins it to the fake
engine's engine_log.jsonl, so a gate that passed on a canned reply is named."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio import comfy
from studio.rehearsal import fakes


@pytest.fixture
def box(tmp_path, monkeypatch):
    submitted = iter(["pid-1", "pid-2", "pid-3"])
    monkeypatch.setattr(comfy, "submit", lambda workflow, timeout=180.0: next(submitted))
    monkeypatch.setattr(comfy, "run_text", lambda name, values, timeout=600.0: f"{comfy.submit({})}:{name}")
    monkeypatch.setattr(comfy, "text_key", lambda name, values: "ab" * 32)
    fakes.install({}, tmp_path)
    yield tmp_path
    fakes.uninstall()


def rows(box: Path) -> list[dict]:
    return [json.loads(x) for x in (box / "vl_consumers.jsonl").read_text(encoding="utf-8").splitlines()]


def panel_gate(box: Path) -> str:
    return comfy.cached_text("vl_panel_faces", {"image": "x.png"}, lambda t: False, root=box / "cache")


def eye_gate() -> str:
    return comfy.run_text("vl_master_eye", {"video": "m.mp4"})


def test_a_read_names_its_prompt_its_ask_and_the_gate_that_asked(box):
    assert eye_gate() == "pid-1:vl_master_eye"
    row = rows(box)[-1]
    assert (row["prompt_id"], row["ask"], row["via"]) == ("pid-1", "vl_master_eye", "run_text")
    assert row["caller"] == f"{__name__}.eye_gate"


def test_a_cached_read_is_one_row_with_its_inner_prompt(box):
    panel_gate(box)
    assert len(rows(box)) == 1
    row = rows(box)[0]
    assert (row["prompt_id"], row["via"], row["cache"]) == ("pid-1", "cached_text", "miss")
    assert row["caller"] == f"{__name__}.panel_gate"


def test_a_cache_hit_has_no_prompt(box):
    cache = box / "cache" / "ab" / f"{'ab' * 32}.txt"
    cache.parent.mkdir(parents=True)
    cache.write_text("kept answer", encoding="utf-8")
    assert panel_gate(box) == "kept answer"
    assert (rows(box)[-1]["prompt_id"], rows(box)[-1]["cache"]) == (None, "hit")


def test_a_read_that_raises_is_still_named(box, monkeypatch):
    fakes.uninstall()
    monkeypatch.setattr(comfy, "run_text", lambda *a, **k: (_ for _ in ()).throw(TimeoutError("hung")))
    fakes.install({}, box)
    with pytest.raises(TimeoutError):
        eye_gate()
    assert rows(box)[-1]["error"] == "TimeoutError"


def test_the_wrapper_is_undone(box):
    fakes.uninstall()
    assert comfy.run_text.__name__ == "<lambda>"
