"""The take identity row is measured again, with the take's own cast sheets (owner ruling 2026-10-14).

4c5f14c (2026-09-25) held the sheets back -- on 34 face takes of WotW ep10-12 the
armed gate failed 3 correct takes and caught nothing -- and nobody turned it back on:
every take since read "identity: not measured" (Jekyll HEL ep01: 0/23 measured).
The row now always gets the sheets; it is HARD only while `TAKE_IDENTITY_HARD` holds
(a replay with no false refusals), else its STRANGER / DRIFT findings ride as an
ADVISORY row that the master eye reads and flags.
"""
from __future__ import annotations

import json
from pathlib import Path


from studio import identity_gate as g, take_verdict as tv
from studio.judges import master_eye


def test_the_take_hands_the_sheets_in_and_names_the_rule(monkeypatch, tmp_path):
    seen = {}

    def fake(video, segments, expected, refs, sheets=None, armed=True, **kw):
        seen.update(sheets=sheets, armed=armed)
        return dict(g.NOT_MEASURED)
    monkeypatch.setattr(g, "identity_dq", fake)
    record = {"faces": ["hyde"], "refs": ["refs/characters/hyde/sheet_front.png", "episodes/ep01/storyboard/h3/shot_03.png"]}
    tv.identity_report(tmp_path / "t.mp4", [0], record, tmp_path)
    assert seen["sheets"] == {"hyde": tmp_path / "refs/characters/hyde/sheet_front.png"}
    assert seen["armed"] is tv.TAKE_IDENTITY_HARD


def test_disarmed_findings_are_advisory_not_lost(monkeypatch):
    face = g.Face(k=2, h=0.4, scores={"hyde": 0.30}, vec=None)
    monkeypatch.setattr(g, "enabled", lambda: True)
    monkeypatch.setattr(g, "observe", lambda *a, **k: [face])
    report = g.identity_dq("t.mp4", [0], ["hyde"], [], sheets={"hyde": "s.png"}, armed=False)
    assert report["ok"] and report["hard"] == []
    assert report["advisory"] and report["advisory"][0].startswith("STRANGER")
    row = tv.identity_gate_row(report)
    assert row.ok and not row.hard and row.value == 1 and "advisory" in row.note and "STRANGER" in row.note


def test_armed_findings_still_refuse(monkeypatch):
    face = g.Face(k=2, h=0.4, scores={"hyde": 0.30}, vec=None)
    monkeypatch.setattr(g, "enabled", lambda: True)
    monkeypatch.setattr(g, "observe", lambda *a, **k: [face])
    row = tv.identity_gate_row(g.identity_dq("t.mp4", [0], ["hyde"], [], sheets={"hyde": "s.png"}, armed=True))
    assert not row.ok and row.hard


def dq(tmp_path: Path, index: int, note: str, value) -> None:
    room = tmp_path / "takes" / "r2v"
    room.mkdir(parents=True, exist_ok=True)
    row = {"name": "identity", "value": value, "ok": True, "hard": False, "note": note, "penalty": 0.0}
    (room / f"T{index:02d}.dq.json").write_text(json.dumps({"take": index, "gates": [row]}), encoding="utf-8")


def test_the_master_eye_reads_the_take_identity_rows(tmp_path):
    dq(tmp_path, 3, "advisory: STRANGER frame 2: best hyde 0.30 < 0.45", 1)
    dq(tmp_path, 4, "1 cast on screen", 0)
    dq(tmp_path, 5, "not measured", None)
    reads = master_eye.take_identity(tmp_path)
    assert reads == {"T03": {"findings": 1, "note": "advisory: STRANGER frame 2: best hyde 0.30 < 0.45"},
                     "T04": {"findings": 0, "note": "1 cast on screen"},
                     "T05": {"findings": None, "note": "not measured"}}
    faults = master_eye.take_identity_faults(reads)
    assert [(f.kind, f.where, f.severity) for f in faults] == [("take_identity", "T03", "low")]
    assert "take_identity" not in master_eye.MEASURED


def test_no_takes_no_reads(tmp_path):
    assert master_eye.take_identity(tmp_path) == {}
    assert master_eye.take_identity_faults({}) == []


def test_the_measuring_code_covers_stillness_and_identity():
    from scripts.episode import take_dq
    assert "studio/stillness.py" in take_dq.MEASURES and "studio/identity_gate.py" in take_dq.MEASURES

