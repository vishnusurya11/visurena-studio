"""The real first-pass face refine's seven decisions are the code's decisions (2026-10-21_ep02_proof
gpu/FACE.md).

On 2026-10-21 the first pass ran on the real engine over ep01 T06 T13 T18 T26 at HEAD 33a4274.  Six of
its seven faces agree with ep01's recorded refine.json; the seventh, T18 Enfield, is CODE DRIFT
(feb2732: the YOLO tracker moved his windows and denoise_for gave 0.482, so H3 drew another crop) and
not nondeterminism (five matching crops rendered to the same mp4 bytes) nor a harness fault.  The drift
is the intended change; the decision it flipped is the turn wall's, and 4.53 deg lies in the band no
face of TURN_MAX's calibration has a label in (kept by eye up to 2.84, refused by eye from 5.55).  So no
wall moves here: these tests pin what the code decides on the real measures, so the next change to a
wall, the tracker or the denoise that flips one of them is seen."""
from __future__ import annotations

import json
from dataclasses import fields
from pathlib import Path

import pytest

from studio import face_refine

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "proof" / "face_first_pass_decisions.json"
FACES = json.loads(FIXTURE.read_text(encoding="utf-8"))["faces"]
KEPT_BY_EYE_MAX, REFUSED_BY_EYE_MIN = 2.84, 5.55
"""TURN_MAX's calibration (studio/face_refine.py): the ep01 replay's turns of faces kept and refused by eye."""


def measures(face: dict) -> face_refine.Measures:
    names = {f.name for f in fields(face_refine.Measures)}
    return face_refine.Measures(**{k: v for k, v in face["measures"].items() if k in names})


@pytest.mark.parametrize("face", FACES, ids=lambda f: f"{f['take']}-{f['who']}")
def test_the_code_decides_each_real_first_pass_face_as_the_real_run_did(face):
    kept, why = face_refine.decide(measures(face))
    assert kept is face["kept"] and why == face["why"]


def test_the_one_disagreement_with_ep01_is_the_turn_wall_inside_its_unlabelled_band():
    moved = [f for f in FACES if f["kept"] != f["recorded_kept"]]
    assert [(f["take"], f["who"]) for f in moved] == [("T18", "richard_enfield")]
    turn = moved[0]["measures"]["turn"]
    assert turn > face_refine.TURN_MAX and KEPT_BY_EYE_MAX < turn < REFUSED_BY_EYE_MIN


@pytest.mark.parametrize("face", FACES, ids=lambda f: f"{f['take']}-{f['who']}")
def test_the_denoise_the_drift_brought_is_the_one_the_real_run_used(face):
    """feb2732's denoise_for over the real run's own face sizes (T18 Enfield 0.482, where 6475f79 fixed 0.45)."""
    assert face_refine.denoise_for(face["face_px"]) == face["denoise"]
