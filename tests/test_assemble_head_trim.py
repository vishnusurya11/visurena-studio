"""A take may start its cut a few frames in, on a narration shot only.

MEASURED on episode 12's turn (2026-09-17): T13 opens on its storyboard cell and
jumps at frame 15 to a wider picture of the same moment (frame diff 28.1, every
other frame under 5).  The render is 209 frames against a 7.96 s shot, so the
cut can start after the jump without re-rendering.  A DIALOGUE shot may not:
its wav is anchored 0.25 s into the take, and starting the picture later would
put the mouth ahead of the sound.
"""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ep_assemble_heads", ROOT / "scripts" / "episode" / "assemble.py")
assemble = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assemble)

PLACED = {"shots": [{"index": 12, "seconds": 7.0}, {"index": 13, "seconds": 7.96}],
          "lines": [{"index": 11, "kind": "dialogue", "shot": 12}, {"index": 12, "kind": "narration", "shot": 13}]}


def test_no_heads_file_trims_nothing(tmp_path):
    assert assemble.heads_of(tmp_path) == {}


def test_a_heads_file_is_read_by_take_index(tmp_path):
    (tmp_path / "heads.json").write_text('{"13": 0.67}', encoding="utf-8")
    assert assemble.heads_of(tmp_path) == {13: 0.67}


def test_a_head_on_a_dialogue_shot_is_refused():
    with pytest.raises(SystemExit, match="T12"):
        assemble.refuse_dialogue_heads({12: 0.5}, PLACED)


def test_a_head_on_a_narration_shot_is_allowed():
    assemble.refuse_dialogue_heads({13: 0.67}, PLACED)


def test_the_head_counts_against_the_take_length():
    short = assemble.short_takes([(13, 7.96)], lambda i: 8.70 - {13: 0.67}.get(i, 0.0))
    assert short == []
    short = assemble.short_takes([(13, 7.96)], lambda i: 8.40 - {13: 0.67}.get(i, 0.0))
    assert short and short[0][0] == 13
