"""Before `rehearse.py all`, the fake workers' memos are FILLED by the real workers and STAGED, with
the recordings index, into every sandbox (2026-10-21_ep02_proof AUDIT A3).

Without them a fake detector answers every take `{"dets": {}}`, a fake ear hears silence, and the
fake ComfyUI, whose manifest names no recordings index, answers every graph canned.  So:
  rehearse.py memos        fills <proof>/memos from the recordings index's takes, crops and lines
                           (the real workers on the CPU, ComfyUI idle: scripts/proof/fill_memos.py)
  rehearse.py checkpoints  then S0a; each real-book sandbox gets a copy of the memos, and its
  rehearse.py all          manifest names the memos and the recordings index
A scenario whose memos or index are not on disk is `absent:`, never run on canned answers."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.proof import rehearse


def index_doc() -> dict:
    return {"entries": [
        {"kind": "take", "path": "book/episodes/ep01/takes/r2v/T00.mp4"},
        {"kind": "refine_crop", "path": "book/episodes/ep01/takes/r2v/refine/T06_p0.mp4"},
        {"kind": "tts_line", "path": "book/episodes/ep01/audio/lines/l00.wav"},
        {"kind": "vl_text", "path": "book/.vlm_cache/x.txt"}, {"kind": "take", "path": None}]}


def test_the_memo_inputs_are_every_recorded_take_crop_and_line(tmp_path):
    got = rehearse.memo_inputs(index_doc(), tmp_path)
    assert got["detect"] == [tmp_path / "book/episodes/ep01/takes/r2v/T00.mp4",
                             tmp_path / "book/episodes/ep01/takes/r2v/refine/T06_p0.mp4"]
    assert got["whisper"] == [tmp_path / "book/episodes/ep01/audio/lines/l00.wav"]


def test_the_memos_step_fills_the_proof_memo_folder_from_the_index(tmp_path):
    index = tmp_path / "rec.json"
    index.write_text(json.dumps(index_doc()), encoding="utf-8")
    asked = {}
    got = rehearse.fill_step(index, tmp_path / "memos", tmp_path, fill=lambda out, **kw: asked.update(out=out, **kw) or {})
    assert asked["out"] == tmp_path / "memos" and len(asked["detect"]) == 2 and len(asked["whisper"]) == 1
    assert got == {}


def test_each_real_book_sandbox_gets_the_memos_and_the_recordings_index(tmp_path, monkeypatch):
    memos, index = tmp_path / "memos", tmp_path / "rec.json"
    memos.mkdir()
    for kind in ("detect", "whisper"):
        (memos / f"{kind}.json").write_text(json.dumps({"k": kind}), encoding="utf-8")
    index.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(rehearse, "MEMOS", memos)
    monkeypatch.setattr(rehearse, "RECORDINGS", index)
    box = tmp_path / "box"
    box.mkdir()
    (box / "rehearsal.json").write_text(json.dumps({"run_id": "x"}), encoding="utf-8")
    rehearse.stage_inputs(box)
    manifest = json.loads((box / "rehearsal.json").read_text(encoding="utf-8"))
    assert manifest["memos"] == str(box / "memos") and manifest["recordings"] == str(index)
    assert json.loads((box / "memos" / "detect.json").read_text(encoding="utf-8")) == {"k": "detect"}


def test_a_scenario_whose_memos_or_index_are_absent_is_absent_never_run_on_canned_answers(tmp_path, monkeypatch):
    monkeypatch.setattr(rehearse, "FILES", {**rehearse.FILES, "detect_memo": tmp_path / "none" / "detect.json",
                                            "index": tmp_path / "none.json"})
    missing = rehearse.missing_packages("F1")
    assert str(tmp_path / "none" / "detect.json") in missing and str(tmp_path / "none.json") in missing
    assert rehearse.missing_packages("smoke") == []


def test_the_memos_step_is_a_command_beside_checkpoints_and_all():
    assert "memos" in rehearse.COMMANDS and rehearse.COMMANDS.index("memos") < rehearse.COMMANDS.index("all")
