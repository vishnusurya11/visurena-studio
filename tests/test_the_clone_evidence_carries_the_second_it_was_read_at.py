"""C4 (a): take_eye's clone evidence carries `t`, the second of the frame it read, so the ladder's
early_clones/head_cut can fire.  ep01 T08 clones (frames 0,1,2,4 of 8) are spread, not early."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from studio import take_ladder as tl
from studio.judges import take_eye
from studio.judges.verdict import Fault
from studio.measure import faces

FIX = Path(__file__).parent / "fixtures" / "ep01_replay" / "P08" / "eye_b368ae93.json"


def test_the_second_of_a_sample_follows_its_share_of_the_take():
    assert abs(faces.sample_second(0, 5.0, 8) - 0.1) < 1e-9
    assert abs(faces.sample_second(7, 5.0, 8) - 0.98 * 5.0) < 1e-9


def test_clones_by_stamps_t_on_every_pair(monkeypatch):
    from studio import identity_gate
    fs = [identity_gate.Face(k=0, h=.3, scores={}, vec=np.ones(2)), identity_gate.Face(k=3, h=.3, scores={}, vec=np.ones(2))]
    monkeypatch.setattr(identity_gate, "observe", lambda *a, **k: fs)
    monkeypatch.setattr(faces, "clone_pairs", lambda f: [{"i": 0, "j": 1, "cosine": .9, "by": "facenet"}])
    rows = take_eye.clones_by(None, detect=lambda x: [], seconds=lambda t: 4.0)(Path("T08.mp4"))
    assert [round(r["t"], 3) for r in rows] == [0.08, round(faces.sample_second(3, 4.0, 8), 3)]


def test_a_clone_fault_keeps_the_t_of_its_row():
    f = take_eye.clone_faults(8, [{"i": 0, "j": 1, "frame": 0, "t": 0.1}])[0]
    assert f.evidence["t"] == 0.1 and tl.early_clones([f])


def test_ep01_t08_clones_are_not_early_so_they_keep_the_seed_cure():
    doc = json.loads(FIX.read_text(encoding="utf-8"))
    rows = [f["evidence"] | {"t": faces.sample_second(f["evidence"]["frame"], 5.0, 8)}
            for f in doc["faults"] if f["kind"] == "clones"]
    faults = take_eye.clone_faults(8, rows)
    assert not tl.early_clones(faults) and tl.cure_of(faults) != "head_cut"
    opening = take_eye.clone_faults(8, [r for r in rows if r["frame"] == 0])
    assert tl.cure_of(opening) == "head_cut"
