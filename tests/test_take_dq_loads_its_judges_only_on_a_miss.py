"""A take_dq pass whose every take is a cache hit loaded yolo, FaceMesh, the embedder and the warp
detector for nothing (Jekyll Kawajiri ep01: the serial cached passes took 32.4, 33.4 and 15.0 s for
23-28 takes that were not measured).  The judges now load on the first take that misses."""
from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))
import take_dq  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "ep01_replay" / "C3-take-content-and-dq-pace" / "timing.jsonl"


def fake_loaders(monkeypatch, calls: list[str]) -> None:
    monkeypatch.setattr(take_dq, "cap_threads", lambda n: calls.append("threads"))
    monkeypatch.setattr(take_dq, "judge_embedder", lambda cpu: (calls.append("embed"), ("e", "i", ["leak"]))[1])
    monkeypatch.setattr(take_dq, "landmarker", lambda: calls.append("mesh") or "mesh")
    monkeypatch.setattr(take_dq, "load_vision_judges", lambda: calls.append("vision") or ("yolo", "face"))


def test_building_the_judges_loads_nothing(monkeypatch):
    calls: list[str] = []
    fake_loaders(monkeypatch, calls)
    take_dq.Judges(Path("home"), cpu_only=True)
    assert calls == []


def test_the_first_miss_loads_all_once(monkeypatch):
    calls: list[str] = []
    fake_loaders(monkeypatch, calls)
    judges = take_dq.Judges(Path("home"), cpu_only=True)
    first, second = judges.get(), judges.get()
    assert first is second and sorted(calls) == ["embed", "mesh", "threads", "vision"]
    assert first[0] == {"home": Path("home"), "embed": "e", "inputs": "i", "landmarker": "mesh",
                        "person": "yolo", "face": "face"}
    assert first[1] == ["leak"]


def test_main_no_longer_loads_judges_before_the_cache_check():
    src = inspect.getsource(take_dq.main)
    assert "judge_embedder(" not in src and "landmarker()" not in src and "Judges(" in src


def test_ep01_cached_passes_are_the_priced_floor():
    """The ep01 serial passes that measured nothing (empty or --ceiling-spent note): the time the lazy load
    can give back is at most this, and the 15.0 s one is the loaded-models floor."""
    rows = [json.loads(l) for l in FIXTURE.read_text(encoding="utf-8").splitlines()]
    cached = [r["seconds"] for r in rows if r["stage"] == "take_dq" and r.get("note", "x") in ("", "--ceiling-spent")]
    assert cached == [32.4, 33.4, 15.0] and round(sum(cached), 1) == 80.8
