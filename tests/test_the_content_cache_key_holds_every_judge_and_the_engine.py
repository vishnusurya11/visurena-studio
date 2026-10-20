"""take_content's verdict cache keys on every module that judges and on the engine that reads.

Skeptic on 92eacc1 (package H, retro 2026-10-20), major: a cached content verdict is served from
the bytes, so whatever made it must be in the key or in the pin.
  - The judging code: JUDGES named take_content_check, take_content and panel_content, but the
    verdict also runs studio/look_table.py (lt.family, lt.seen_hair), studio/panel_dq.py
    (back_view, at_night) and studio/people_count.py.  JUDGES is now the import closure of the
    judges, plus frames.py (which frames are read), so an edit to any of them reds the pin test.
  - The engine: the key named the workflow only.  The old path re-read through comfy.text_key,
    which holds the workflow JSON, its inject map and comfy.TEXT_CACHE_VERSION; the verdict key
    now holds the same, so a swapped VL model or node is a miss.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))
import take_content_check as tcc  # noqa: E402

TEMPLATE = ({"1": {"class_type": "Qwen3VL", "inputs": {"model": "qwen3-vl-8b"}}}, {"prompt": ["1", "text"]})


def engine(monkeypatch, template=TEMPLATE) -> None:
    monkeypatch.setattr(tcc.comfy, "load_workflow", lambda name: template)


def key(tmp_path: Path) -> dict:
    take = tmp_path / "T00.mp4"
    take.write_bytes(b"ep01 T00 bytes")
    return tcc.verdict_key(take, {"planned": 1, "size": "medium"}, 4.0)


def test_the_judges_hold_every_module_the_verdict_runs():
    for rel in ("studio/look_table.py", "studio/panel_dq.py", "studio/people_count.py", "studio/frames.py",
                "studio/take_content.py", "studio/panel_content.py", "scripts/episode/take_content_check.py"):
        assert rel in tcc.JUDGES, rel


def test_the_judges_are_the_import_closure_of_the_judging_modules():
    from studio import code_closure
    assert set(code_closure.closure(tcc.ROOT, ("studio/take_content.py",))) <= set(tcc.JUDGES)
    assert "studio/comfy.py" not in tcc.JUDGES and "studio/episode_home.py" not in tcc.JUDGES


def test_a_swapped_vl_workflow_is_a_miss(tmp_path, monkeypatch):
    engine(monkeypatch)
    before = key(tmp_path)
    engine(monkeypatch, ({"1": {"class_type": "Qwen3VL", "inputs": {"model": "qwen3-vl-32b"}}}, TEMPLATE[1]))
    assert key(tmp_path)["judged_sha8"] != before["judged_sha8"]


def test_a_bumped_text_cache_version_is_a_miss(tmp_path, monkeypatch):
    engine(monkeypatch)
    before = key(tmp_path)
    monkeypatch.setattr(tcc.comfy, "TEXT_CACHE_VERSION", tcc.comfy.TEXT_CACHE_VERSION + ".1")
    assert key(tmp_path)["judged_sha8"] != before["judged_sha8"]


def test_an_unchanged_engine_is_the_same_key(tmp_path, monkeypatch):
    engine(monkeypatch)
    assert key(tmp_path) == key(tmp_path)


def test_a_missing_workflow_keys_as_absent_and_never_raises(tmp_path, monkeypatch):
    def missing(name):
        raise FileNotFoundError(name)
    monkeypatch.setattr(tcc.comfy, "load_workflow", missing)
    assert tcc.engine_sha8() == "absent"
    engine(monkeypatch)
    assert tcc.engine_sha8() not in ("absent", "")
