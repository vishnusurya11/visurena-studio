"""take_content serves a verdict on the take's bytes + the rows it judges against + the gate version.

Never on bytes alone: a take content verdict is a judgement of what the VL read AGAINST the
plan's words (the shot's faces, size and extras, the setup's crowd and stage, the banned list,
the look markers, the panel's people, and the asks themselves).  A changed judged row is a miss.
Jekyll ep01 repair run 16 (drive_run04.log): 1,434 s, owed, because the ask itself moved (v2).
The fixture is a copy of ep01's takes/r2v/T00.content.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))
import take_content_check as tcc  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "ep01_gate_version" / "T00.content.json"


def plan_rows(monkeypatch) -> None:
    """The book-reading rows answered from the test, so judged_row reads no library."""
    monkeypatch.setattr(tcc.pc, "flat_place", lambda book, loc: False)
    monkeypatch.setattr(tcc.pc, "banned_subjects", lambda book: ["car"])
    monkeypatch.setattr(tcc.pc, "crowd_declared", lambda shot, setup: False)
    monkeypatch.setattr(tcc.pc, "stage_text", lambda shot, setup: setup.described)
    monkeypatch.setattr(tcc, "pc_row", lambda book, who: f"{who} is tall")
    monkeypatch.setattr(tcc, "look_markers", lambda book, faces, setup: ["top hat"])
    monkeypatch.setattr(tcc.comfy, "load_workflow", lambda name: ({"1": {"class_type": "Qwen3VL"}}, {}))


SHOT = SimpleNamespace(faces=["richard_enfield"], size="medium", extras=0)
SETUP = SimpleNamespace(location="by_street", described="a by-street in London, day")


def key(tmp_path: Path, shot=SHOT, setup=SETUP, seconds: float = 4.0, people: int | None = 1) -> dict:
    take = tmp_path / "T00.mp4"
    if not take.exists():
        take.write_bytes(b"ep01 T00 bytes")
    return tcc.verdict_key(take, tcc.judged_row(tmp_path, shot, setup, people), seconds)


def stored(tmp_path: Path, k: dict) -> Path:
    path = tmp_path / "T00.content.json"
    row = json.loads(FIXTURE.read_text(encoding="utf-8"))
    path.write_text(json.dumps(tcc.keyed(row, k)), encoding="utf-8", newline="\n")
    return path


def test_unchanged_bytes_rows_and_gate_are_a_hit(tmp_path, monkeypatch):
    plan_rows(monkeypatch)
    path = stored(tmp_path, key(tmp_path))
    hit = tcc.cached(path, key(tmp_path))
    assert hit is not None and hit["passed"] is True and hit["panel_people"] == 1


def test_a_changed_judged_row_is_a_miss(tmp_path, monkeypatch):
    plan_rows(monkeypatch)
    path = stored(tmp_path, key(tmp_path))
    crowd = SimpleNamespace(faces=["richard_enfield", "edward_hyde"], size="medium", extras=0)
    assert tcc.cached(path, key(tmp_path, shot=crowd)) is None
    assert tcc.cached(path, key(tmp_path, setup=SimpleNamespace(location="by_street", described="night"))) is None
    assert tcc.cached(path, key(tmp_path, people=2)) is None


def test_a_changed_ask_is_a_miss(tmp_path, monkeypatch):
    plan_rows(monkeypatch)
    path = stored(tmp_path, key(tmp_path))
    monkeypatch.setattr(tcc.pc, "ASK", tcc.pc.ASK + " (ask v3)")
    assert tcc.cached(path, key(tmp_path)) is None


def test_changed_bytes_or_gate_are_a_miss(tmp_path, monkeypatch):
    plan_rows(monkeypatch)
    path = stored(tmp_path, key(tmp_path))
    monkeypatch.setattr(tcc, "GATE_VERSION", "0")
    assert tcc.cached(path, key(tmp_path)) is None
    monkeypatch.undo()
    plan_rows(monkeypatch)
    (tmp_path / "T00.mp4").write_bytes(b"a retaken T00")
    assert tcc.cached(path, key(tmp_path)) is None


def test_ep01s_unkeyed_record_is_judged_once(tmp_path, monkeypatch):
    plan_rows(monkeypatch)
    path = tmp_path / "T00.content.json"
    path.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    assert tcc.cached(path, key(tmp_path)) is None


def test_an_unread_verdict_is_never_kept(tmp_path, monkeypatch):
    plan_rows(monkeypatch)
    unread = {"passed": False, "faults": ["unread: the engine said nothing"]}
    assert tcc.keyed(unread, key(tmp_path)) == unread


def test_the_verdict_judges_the_same_rows_the_key_holds(monkeypatch, tmp_path):
    plan_rows(monkeypatch)
    seen = {}
    monkeypatch.setattr(tcc.tc, "take_faults", lambda reads, **rows: seen.update(rows) or [])
    monkeypatch.setattr(tcc.tc, "busiest", lambda reads: SimpleNamespace(people=1, lookalikes=0, hour="day", text=False))
    monkeypatch.setattr(tcc.tc, "look_log", lambda reads, markers: [])
    monkeypatch.setattr(tcc.pc, "shape_read", lambda reads: (None, []))
    tcc.verdict_for(tmp_path, SHOT, SETUP, [], 1)
    assert seen == tcc.judged_row(tmp_path, SHOT, SETUP, 1)


def test_a_pass_of_hits_never_asks_the_engine(tmp_path, monkeypatch):
    plan_rows(monkeypatch)
    k = key(tmp_path)
    stored(tmp_path, k)
    monkeypatch.setattr(tcc, "take_key", lambda book, ep, record, take_dir: k)
    monkeypatch.setattr(tcc, "judge_take", lambda *a: (_ for _ in ()).throw(AssertionError("judged")))
    monkeypatch.setattr(tcc.comfy, "model_kept", lambda: (_ for _ in ()).throw(AssertionError("engine")))
    failed = tcc.judge_all(tmp_path, None, [{"index": 0}], tmp_path, tmp_path / "work")
    assert failed == [] and json.loads((tmp_path / "T00.content.json").read_text(encoding="utf-8"))["passed"]
