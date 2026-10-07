"""ep23 (2026-10-07): a setup projected 50.5 s against the 50 s cap, `holds` had
nothing to shave, and the writer was paid rungs for half a second.  G-SETUP's
own advice is 'split it': the setup's last shots move to a copy of it (same
picture, a second name) until the first fits.  $0."""
from __future__ import annotations

from studio import plan_cures


def _doc():
    setups = {"garden": {"described": "A garden", "geometry": "Walls", "cast": ["lead"], "landmark": "the wall"}}
    shots = [{"index": i, "setup": "garden", "section": "setup", "beat_s": 0.0, "coda_s": 0.0} for i in range(6)]
    shots[0]["section"] = "hook"
    lines = [{"index": i, "kind": "narration", "speaker": "n", "shot": i, "text": " ".join(["w"] * 30)} for i in range(6)]
    return {"setups": setups, "shots": shots, "lines": lines}


def test_the_last_shots_of_an_overrun_setup_move_to_a_copy_until_it_fits():
    # 6 shots x (30 words / 2.5 + 0.5 handles) = 6 x 12.5 = 75 s in one setup against 50
    out = plan_cures.split_setup(_doc(), rate=2.5)
    assert "garden" in out["setups"] and "garden_2" in out["setups"]
    assert out["setups"]["garden_2"]["described"] == "A garden"
    first = [s["index"] for s in out["shots"] if s["setup"] == "garden"]
    second = [s["index"] for s in out["shots"] if s["setup"] == "garden_2"]
    assert first == [0, 1, 2, 3] and second == [4, 5]          # 4 x 12.5 = 50.0 fits; the rest move


def test_a_setup_within_its_cap_is_left_alone():
    doc = _doc(); doc["shots"] = doc["shots"][:3]; doc["lines"] = doc["lines"][:3]
    out = plan_cures.split_setup(doc, rate=2.5)
    assert list(out["setups"]) == ["garden"]


def test_the_cure_is_in_the_table():
    assert plan_cures.cure_for("G-SETUP setup roehampton_garden: projected seconds of picture in one setup, measured 50.5 against 50.0") == "split_setup"
