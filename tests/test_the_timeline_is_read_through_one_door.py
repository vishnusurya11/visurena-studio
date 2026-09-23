"""The timeline is fresh to the plan AND to the voice, and is read through one
checked door.

Audit item 11, 2026-09-22: the freshness check was called only by plan_check,
while takes_r2v, assemble, qc and take_dq read placed.json directly. Its
fingerprint covered the plan's words and holds but not the MEASURED line
lengths, so re-voicing a line -- the lines' lengths change, the plan does not
-- left a stale timeline reading fresh.
"""
import json

import pytest

from studio import episode_home
from studio.timeline_fresh import fingerprint, stale


class Line:
    def __init__(self, index, shot, text):
        self.index, self.shot, self.text = index, shot, text


class Shot:
    def __init__(self, index):
        self.index, self.beat_s, self.coda_s = index, 1.0, 1.0


class Ep:
    shots = [Shot(0)]
    lines = [Line(0, 0, "a line")]


def test_the_same_voice_fingerprints_the_same():
    assert fingerprint(Ep(), [{"index": 0, "seconds": 2.5}]) == fingerprint(Ep(), [{"index": 0, "seconds": 2.5}])


def test_a_revoiced_line_changes_the_fingerprint():
    assert fingerprint(Ep(), [{"index": 0, "seconds": 2.5}]) != fingerprint(Ep(), [{"index": 0, "seconds": 3.1}])


def test_a_timeline_built_before_a_revoice_is_stale():
    placed = {"plan": fingerprint(Ep(), [{"index": 0, "seconds": 2.5}])}
    assert stale(Ep(), placed, [{"index": 0, "seconds": 3.1}])


def home(tmp_path, measured_seconds, stamped_seconds):
    root = tmp_path / "episodes" / "ep09"
    (root / "audio" / "lines").mkdir(parents=True)
    (root / "audio" / "lines" / "lines.json").write_text(
        json.dumps([{"index": 0, "seconds": measured_seconds}]))
    (root / "placed.json").write_text(json.dumps(
        {"plan": fingerprint(Ep(), [{"index": 0, "seconds": stamped_seconds}]), "shots": [], "lines": []}))
    return tmp_path


def test_the_checked_door_returns_a_fresh_timeline(tmp_path, monkeypatch):
    book = home(tmp_path, 2.5, 2.5)
    assert episode_home.load_placed(book, 9, Ep())["shots"] == []


def test_the_checked_door_refuses_a_stale_one(tmp_path):
    book = home(tmp_path, 3.1, 2.5)
    with pytest.raises(SystemExit, match="timeline"):
        episode_home.load_placed(book, 9, Ep())
