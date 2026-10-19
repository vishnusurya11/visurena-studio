"""C4 (b): production wires the best-draw runner to what take_dq already measured and recorded for
every draw (T<nn>.dq.json `attempts`: file bytes, gates, the warp note's Se) -- no GPU, no re-measure.
A draw the record cannot name is never the winner."""
from __future__ import annotations

import json

from studio import take_ladder as tl


def gate(name, ok, hard, note=""):
    return {"name": name, "ok": ok, "hard": hard, "note": note}


def room_of(tmp_path):
    room = tmp_path / "takes" / "r2v"
    (room / "attempts").mkdir(parents=True)
    (room / "T21.mp4").write_bytes(b"last")
    (room / "attempts" / "T21_fail1.mp4").write_bytes(b"firstdraw")
    rec = {"bytes": 4, "gates": [gate("warp", False, True, "fail: S 0.10 Se 3.55 over 100% tracked")],
           "attempts": [
               {"bytes": 4, "gates": [gate("warp", False, True, "fail: S 0.10 Se 3.55 over 100% tracked")]},
               {"bytes": 9, "gates": [gate("warp", False, True, "fail: S 0.10 Se 2.10 over 100% tracked")]}]}
    (room / "T21.dq.json").write_text(json.dumps(rec), encoding="utf-8")
    return room


def test_a_draw_is_read_from_the_record_by_its_bytes(tmp_path):
    room = room_of(tmp_path)
    assert tl.recorded_draw(room / "attempts" / "T21_fail1.mp4") == {"hard": 1, "Se": 2.10}
    assert tl.recorded_draw(room / "T21.mp4") == {"hard": 1, "Se": 3.55}


def test_a_draw_the_record_does_not_name_cannot_win(tmp_path):
    room = room_of(tmp_path)
    (room / "attempts" / "T21_fail2.mp4").write_bytes(b"unknown")
    assert tl.recorded_draw(room / "attempts" / "T21_fail2.mp4")["hard"] >= 999


def test_the_terminal_restores_the_lower_se_draw_from_the_record(tmp_path):
    room = room_of(tmp_path)
    said = tl.best_draw(room, 21, tl.recorded_draw)
    assert (room / "T21.mp4").read_bytes() == b"firstdraw" and "T21" in said


def test_production_wires_the_recorded_runner(monkeypatch):
    from scripts.episode import step_09_shoot as s9
    seen = {}
    monkeypatch.setattr(s9.take_ladder, "terminal_for", lambda ctx, plan, draws=None: seen.setdefault("draws", draws))
    monkeypatch.setattr(s9.judged_gate, "clear", lambda ctx, gate, **kw: kw["terminal"])
    monkeypatch.setattr(s9, "signed_for", lambda ctx, room: None)
    monkeypatch.setattr(s9.episode_home, "load_plan", lambda *a: None)
    monkeypatch.setattr(s9.take_ladder, "rungs", lambda *a: None)
    ctx = type("C", (), {"home": __import__("pathlib").Path("."), "book_dir": None, "number": 1})()
    s9.judge_takes(ctx, "")
    assert seen["draws"] is tl.recorded_draw
