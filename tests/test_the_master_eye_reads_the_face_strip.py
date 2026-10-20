"""The master eye reads the QC face strip (retro 2026-10-20 item 4, package D): each crop is shown to
the reader alone with FACE_ASK, and the code turns the answer into one word (clear, soft, warped,
none).  The reads go into the measures and the rubric's `face_strip` block, and the step copies them
into the owner's labels file.  They are LOG ONLY (owner veto list V3): no fault, no rung, no flag,
until owner labels calibrate them.  The reader is a fake (the FakeModel), $0.
"""
from __future__ import annotations

import json

import numpy as np
from PIL import Image

from studio.judges import master_eye as me

SAID = json.dumps({"landform": "flat", "people": 1, "lookalikes": 0, "text": False, "hour": "day",
                   "framing": "medium", "action": "walks"})
PLACED = {"duration_s": 10.0, "shots": [{"index": 1, "t_start": 0.0, "t_end": 10.0, "seconds": 10.0}]}
PLAN = {"shots": [{"index": 1, "setup": "a", "size": "medium"}]}


def frames(master, times):
    return [np.full((16, 16, 3), 30, np.uint8) for _ in times]


def a_strip(tmp_path) -> list[dict]:
    rows = []
    for i, shade in ((1, 10), (6, 200)):
        crop = f"faces_x/tiny_T{i:02d}.png"
        (tmp_path / "review" / "faces_x").mkdir(parents=True, exist_ok=True)
        Image.fromarray(np.full((8, 8, 3), shade, np.uint8)).save(tmp_path / "review" / crop)
        rows.append({"crop": crop, "take": f"T{i:02d}", "index": i, "tier": "tiny", "px": 30.0,
                     "master_px": 60.0, "listed": True, "pasted": False, "at": 1.0, "kind": "face", "box": None})
    return rows


def face_reader(picture):
    return '{"face": "soft"}' if int(np.asarray(picture).mean()) < 100 else "the face is clear"


def measured(tmp_path, reader=face_reader):
    return me.read(tmp_path, tmp_path / "m.mp4", PLAN, PLACED, frames=frames, reader=lambda f: SAID,
                   embed=lambda f: [], count=4, strip=a_strip(tmp_path), face_reader=reader)


def test_the_face_ask_names_the_four_words():
    assert all(f'"{w}"' in me.FACE_ASK for w in me.FACE_WORDS)
    assert me.face_word('{"face": "Warped"}') == "warped" and me.face_word("it looks soft") == "soft"
    assert me.face_word("???") == "unreadable"


def test_each_crop_is_read_alone_and_said_as_one_word(tmp_path):
    _v, m = measured(tmp_path)
    strip = m["face_strip"]
    assert [c["eye"] for c in strip["crops"]] == ["soft", "clear"]
    assert strip["soft"] == ["T01"] and strip["warped"] == [] and strip["read"] == 2


def test_a_soft_face_is_logged_and_never_a_fault(tmp_path):
    """The same master read with and without the strip gives the same faults: two soft crops add none."""
    verdict, m = measured(tmp_path)
    bare, _m = me.read(tmp_path, tmp_path / "m.mp4", PLAN, PLACED, frames=frames, reader=lambda f: SAID,
                       embed=lambda f: [], count=4)
    assert m["face_strip"]["soft"] and verdict.faults == bare.faults and verdict.passed == bare.passed
    assert "face_strip" not in me.FIELDS and "log only" in m["face_strip"]["note"]


def test_the_rubric_carries_the_strip_reads(tmp_path):
    verdict, m = measured(tmp_path)
    doc = me.rubric(verdict, "abcd1234", measures=m)
    assert doc["face_strip"]["soft"] == ["T01"]
    json.dumps(doc)                                    # the block is plain JSON, no arrays


def test_no_strip_or_no_face_reader_reads_nothing(tmp_path):
    _v, m = me.read(tmp_path, tmp_path / "m.mp4", PLAN, PLACED, frames=frames, reader=lambda f: SAID,
                    embed=lambda f: [], count=4)
    assert m["face_strip"]["crops"] == [] and m["face_strip"]["read"] == 0
    _v, m = measured(tmp_path, reader=None)
    assert {c["eye"] for c in m["face_strip"]["crops"]} == {""}
