"""scripts/audit/who_fixture.py writes the calibration set G-WHO replays (retro B): each case's real read, its
cast's staged markers and the eye's answer, in the shape the replay test reads.  The reader is faked here."""
from __future__ import annotations

import json

from scripts.audit import who_fixture as wf


def test_a_case_is_recorded_with_its_read_its_cast_and_the_eyes_answer(tmp_path, monkeypatch):
    from scripts.episode import panel_content_check as pcc
    figures = [{"hair": "grey", "facial_hair": "none", "coat": "black", "headwear": "bowler"}]
    monkeypatch.setattr(pcc, "read_who", lambda path, seed=19: figures)
    monkeypatch.setattr(wf.episode_home, "load_plan", lambda book, n: type("P", (), {"setups": {}})())
    monkeypatch.setattr(wf, "markers_of", lambda book, faces, setup: [(f, {"headwear": "bowler"}, "black coat") for f in faces])
    monkeypatch.setattr(wf.episode_home, "book_dir", lambda book_id: tmp_path)
    cases = tmp_path / "cases.json"
    cases.write_text(json.dumps([{"case": "panel_25_v1", "image": "x.png", "faces": ["utterson", "poole"],
                                  "setup": "doorstep", "double_by_eye": True}]))
    wf.main("book", 6, cases, tmp_path / "out.json")
    row = json.loads((tmp_path / "out.json").read_text())["takes"][0]
    assert row["take"] == "panel_25_v1" and row["double_by_eye"] is True and row["frames"] == [figures]
    assert row["cast"]["poole"] == {"markers": {"headwear": "bowler"}, "top": "black coat"}
