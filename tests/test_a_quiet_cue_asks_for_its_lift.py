"""ep15 (2026-10-01): QC heard 19 of 22 planned sounds and refused the master
on the three quiet ones (field guns 4.6 dB, two shot-3 cues at ~2 dB against
EVENT_DB 6.0) -- and the pipeline had NO cure: the only knob was gain_db inside
the signed plan, so the refusal was forever.  The cure is a sidecar,
audio/cue_lifts.json: each unheard cue's measured deficit plus a margin,
accumulated across recuts and clamped, applied on top of the plan's gain at
render time.  The plan stays untouched and signed.  $0: pure arithmetic."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from studio import episode_sound as es


def rows():
    return [
        {"shot": 0, "sound": "distant field guns firing", "at": 0.8, "db": 4.6, "ok": False},
        {"shot": 1, "sound": "a church bell", "at": 9.0, "db": 8.2, "ok": True},
        {"shot": 3, "sound": "ammunition explosion", "at": 27.5, "db": 2.1, "ok": False},
    ]


def test_an_unheard_cue_lifts_by_its_deficit_plus_margin():
    lifts = es.lift_cures(rows(), {})
    assert lifts == {"0|distant field guns firing": 2.4,       # (6.0-4.6)+1.0
                     "3|ammunition explosion": 4.9}            # (6.0-2.1)+1.0
    assert "1|a church bell" not in lifts                      # heard cues untouched


def test_a_lift_accumulates_over_recuts_and_clamps():
    once = es.lift_cures(rows(), {})
    again = es.lift_cures(rows(), once)                        # still quiet after recut
    assert again["0|distant field guns firing"] == 4.8         # 2.4 + 2.4
    walled = es.lift_cures([{"shot": 9, "sound": "x", "db": -30.0, "ok": False}],
                           {"9|x": 11.0})
    assert walled["9|x"] == es.MAX_LIFT_DB                     # never past the schema wall


def test_cues_of_applies_the_lift_on_top_of_the_plans_gain():
    shot = SimpleNamespace(index=0, sounds=[SimpleNamespace(
        sound="distant field guns firing", at=0.8, seconds=2.0, gain_db=3.0)])
    episode = SimpleNamespace(shots=[shot], omit=[])
    cue = es.cues_of(episode, {"0|distant field guns firing": 2.4})[0]
    assert cue.gain_db == 5.4
    assert es.cues_of(episode)[0].gain_db == 3.0               # no lifts = the plan


def test_cure_from_qc_reads_the_last_measure_and_writes_the_sidecar(tmp_path):
    home = tmp_path
    (home / "qc_r2v.json").write_text(json.dumps({"sound": rows()}), encoding="utf-8")
    lifts = es.cure_from_qc(home, "r2v")
    on_disk = json.loads((home / "audio" / "cue_lifts.json").read_text(encoding="utf-8"))
    assert on_disk == lifts and lifts["3|ammunition explosion"] == 4.9
    assert es.lifts_of(home) == on_disk
    assert es.cure_from_qc(tmp_path / "virgin", "r2v") == {}   # no qc yet = no lifts
