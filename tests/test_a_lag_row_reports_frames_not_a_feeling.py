"""The lag row says how many FRAMES the mouth is late or early against the
voice, with its peak correlation, and what the wall was fitted on -- never
"looks off".  The arrays are a recorded fixture (an aperture track and the
voice envelope at 24 fps); the take_dq rows fixture is the shape the ladder
reads.  Nothing here decodes video or opens a model.
"""
import json
from pathlib import Path

import numpy as np

from studio import av_sync
from studio.measure import mouth

FIX = Path(__file__).resolve().parent / "fixtures" / "flow"


def arrays() -> dict:
    return json.loads((FIX / "lag_arrays.json").read_text(encoding="utf-8"))


def test_the_recorded_lag_reads_in_frames_through_av_sync():
    a = arrays()
    ap, voice = np.array(a["aperture"]), np.array(a["voice"])
    got = mouth.lag(ap, voice, fps=a["fps"])
    assert got["lag_frames"] == a["lag_frames"] and got["measured"] is True
    assert got["lag_s"] == round(a["lag_frames"] / a["fps"], 3)
    assert got["lag_frames"] == int(round(av_sync.lag_seconds(mouth.fill(ap), voice, 1, 1.0)))


def test_the_row_names_frames_seconds_and_correlation():
    a = arrays()
    row = mouth.row(mouth.lag(np.array(a["aperture"]), np.array(a["voice"]), fps=a["fps"]))
    assert row.name == "lag" and row.value == a["lag_frames"] and not row.hard
    assert f"{a['lag_frames']:+d}f" in row.note and "corr" in row.note and "s)" in row.note
    assert row.ok is (abs(a["lag_frames"]) <= mouth.LAG_TOL_FRAMES)


def test_a_lag_inside_two_frames_is_ok_and_beyond_is_advisory():
    inside = mouth.row({"measured": True, "lag_frames": 2, "lag_s": 0.083, "corr": 0.8, "readable": 1.0})
    beyond = mouth.row({"measured": True, "lag_frames": -4, "lag_s": -0.167, "corr": 0.8, "readable": 1.0})
    assert inside.ok and inside.penalty == 0.0
    assert not beyond.ok and not beyond.hard and beyond.penalty > 0 and "-4f" in beyond.note


def test_the_take_dq_rows_fixture_carries_the_new_rows_with_their_calibration():
    rows = json.loads((FIX / "take_dq_rows.json").read_text(encoding="utf-8"))
    names = [g["name"] for g in rows["gates"]]
    for name in ("pass-through", "rotation", "leak", "last-vs-panel", "cut-vote", "lag"):
        assert name in names
    lag = next(g for g in rows["gates"] if g["name"] == "lag")
    assert isinstance(lag["value"], int) and "f (" in lag["note"] and lag["hard"] is False
    for key in ("pass_through", "rotation", "leak", "cut_vote", "lag"):
        assert "fitted_on" in rows["measures"][key], key


def take_dq():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "take_dq", Path(__file__).resolve().parents[1] / "scripts" / "episode" / "take_dq.py")
    dq = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dq)
    return dq


def test_the_dq_rows_are_what_the_code_produces_today():
    """The fixture is derived from the contract: the same inputs give the same rows."""
    rows = json.loads((FIX / "take_dq_rows.json").read_text(encoding="utf-8"))
    rec = {"lane": "dialogue", "motion": rows["motion"], "motions": [rows["motion"]]}
    got = [g.__dict__ for g in take_dq().judge_rows(rows["measures"], rec)]
    assert got == rows["gates"]


def fake_verdict(jump: float = 0.9, hard_cut: float = 4.0, cells=True):
    from studio import take_verdict as tv

    v = tv.TakeVerdict(3, 0, "T03.mp4", 1.0, "dialogue", [tv.Gate("jump", jump, True, True, "")], [])
    v.coherence, v.zoom = {"hard_cut": hard_cut, "cells": cells}, {"cum_theta": 0.3, "measured": True}
    v.score, v.passed = 100.0, True
    return v


def test_the_judged_rows_extend_the_verdict_and_re_sum_its_score():
    dq = take_dq()
    rows = json.loads((FIX / "take_dq_rows.json").read_text(encoding="utf-8"))
    v = dq.extend_verdict(fake_verdict(), rows["measures"], {"lane": "dialogue", "motion": rows["motion"]})
    assert [g.name for g in v.gates][-6:] == ["pass-through", "rotation", "leak", "last-vs-panel", "cut-vote", "lag"]
    assert v.passed is False and v.score < 100.0
    assert dq.gate_value(v, "jump") == 0.9 and dq.gate_value(v, "nothing") is None


def test_the_picture_measures_come_off_the_frames_alone():
    from synth_frames import hold, picture, rgb

    dq = take_dq()
    frames = [rgb(f) for f in np.concatenate([hold(picture(61), 12), hold(picture(62), 12)])]
    m = dq.picture_measures(frames, fake_verdict(jump=0.1, hard_cut=40.0), {"anchors": []})
    assert m["pass_through"] is None                                     # no face
    assert m["rotation"] == {"cum_theta": 0.3, "measured": True, "fitted_on": m["rotation"]["fitted_on"]}
    assert m["cut_vote"]["count"] == 3 and m["cut_vote"]["scene_cuts"] == [12]
    pinned = dq.cut_vote(fake_verdict(jump=0.1, hard_cut=40.0), frames, [("Q00_0.png", 0), ("Q01_0.png", 12)])
    assert pinned["votes"]["scene"] is False and pinned["scene_cuts"] == []


def test_the_staged_measures_read_the_panel_for_a_refs_only_take_and_skip_the_leak_without_an_embedder(tmp_path, monkeypatch):
    from PIL import Image

    from studio import take_coherence as tc
    from synth_frames import hold, picture

    dq = take_dq()
    (tmp_path / "storyboard").mkdir()
    Image.fromarray(picture(63)).save(tc.panel_path(tmp_path, 3))
    monkeypatch.setattr(tc, "frames", lambda video, seconds=None: hold(picture(63), 10))
    m = dq.staged_measures(tmp_path / "T03.mp4", {"index": 3, "shots": [3]}, fake_verdict(cells=False), tmp_path, 1.0)
    assert m["leak"] is None and m["board"]["last_vs_cell"] > 0.9 and m["board"]["cells"] == "panel"
    with_cells = dq.staged_measures(tmp_path / "T03.mp4", {"index": 3}, fake_verdict(cells=True), tmp_path, 1.0)
    assert with_cells == {"leak": None, "board": None}


def test_the_voice_measure_runs_only_on_a_dialogue_take_with_a_landmarker():
    dq = take_dq()
    a = arrays()
    frames = [np.zeros((4, 4, 3), np.uint8)] * len(a["aperture"])
    pts = iter(a["aperture"])

    def landmarker(_frame):
        p = np.zeros((478, 2))
        p[mouth.LEFT_EYE], p[mouth.RIGHT_EYE] = (0.3, 0.4), (0.7, 0.4)
        p[mouth.UPPER], p[mouth.LOWER] = (0.5, 0.6), (0.5, 0.6 + next(pts) * 0.4)
        return p

    got = dq.voice_measure(frames, {"lane": "dialogue"}, landmarker, np.array(a["voice"]))
    assert got["lag"]["lag_frames"] == a["lag_frames"]
    assert dq.voice_measure(frames, {"lane": "narration"}, landmarker, np.array(a["voice"])) == {"lag": None}
    assert dq.voice_measure(frames, {"lane": "dialogue"}, None, None) == {"lag": None}


def test_the_production_readers_are_none_when_their_models_are_absent(tmp_path, monkeypatch):
    from studio import comfy

    dq = take_dq()

    def no_workflow(name):
        raise FileNotFoundError(name)

    def no_model(model=None):
        raise FileNotFoundError(model)

    monkeypatch.setattr(comfy, "load_workflow", no_workflow)
    assert dq.embedder() == (None, None)
    monkeypatch.setattr(mouth, "facemesh", no_model)
    assert dq.landmarker() is None
    assert dq.voice_of(tmp_path / "voice_03.wav", True) is None and dq.voice_of(tmp_path / "x.wav", False) is None
