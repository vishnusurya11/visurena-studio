"""P2 (retro 2026-10-19, P06): a setup that is day, read as night, is logged on
the panel row -- never a fault (the reader cannot see the sky indoors, and the
wall for the hour is the night direction only).  `landmarks_seen` is logged
beside it so a later gate has data; no prompt changed."""
from __future__ import annotations

from studio import panel_content as pc
from studio.panel_content import Seen


def test_a_day_setup_read_as_night_is_an_advisory():
    got = pc.hour_advisory(Seen(hour="night", landform="flat"), "a Sunday afternoon street, low sun")
    assert got and "advisory" in got and "night" in got


def test_a_day_read_on_a_day_setup_is_quiet():
    assert pc.hour_advisory(Seen(hour="day"), "a Sunday afternoon street") is None


def test_a_night_setup_is_not_this_advisory():
    assert pc.hour_advisory(Seen(hour="night"), "a street at night under the gas lamp") is None


def test_an_interior_has_no_hour_to_read():
    assert pc.hour_advisory(Seen(hour="night", landform="indoors"), "a quiet room by day") is None


def test_landmarks_are_the_listed_nouns_among_the_subjects():
    seen = Seen(subjects=["man", "gas lamp", "stone steps", "dog", "door"])
    assert pc.landmarks_seen(seen) == ["gas lamp", "stone steps", "door"]


def test_the_panel_row_carries_the_advisory_the_landmarks_and_the_shape_keys(monkeypatch, tmp_path):
    from pathlib import Path
    from types import SimpleNamespace
    from scripts.episode import panel_content_check as pcc
    seen = Seen(people=1, hour="night", subjects=["man", "door"], body="fading")
    monkeypatch.setattr(pcc, "read", lambda path, seed=11: seen)
    shot = SimpleNamespace(index=2, frame="Close on the man.", at_rest="", size="close", faces=[], extras=1,
                           model_fields_set={"frame", "faces", "extras"})
    setup = SimpleNamespace(crowd="", described="a Sunday afternoon street", location="")
    monkeypatch.setattr(pcc, "twin_check", lambda shot, seen, path: ([], {}))
    row = pcc.row_for(tmp_path, shot, setup, Path("shot_02.png"))
    assert any("day setup" in n for n in row["look_advisory"]) and row["passed"] is True
    assert row["landmarks_seen"] == ["door"] and row["body"] == "fading" and row["shape_advisory"]
