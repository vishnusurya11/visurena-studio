"""`heads.json` was a hand-written file: somebody watched the strip, counted
the frames of the wrong picture, and typed the seconds.  Now the measured leak
writes it, through the ONE reader the cut and the edit gate already share
(`edit_gate.heads_in`), only when the take still covers its shot.
"""
import json

from studio import edit_gate, take_leak as lk


def test_a_measured_leak_lands_in_heads_json_and_the_edit_gate_reads_it(tmp_path):
    got = {"frames": 8, "seconds": round(8 / 24, 3), "covers": True}
    path = lk.write_head(tmp_path, 7, got)
    assert path == tmp_path / "heads.json"
    assert edit_gate.heads_in(tmp_path) == {7: round(8 / 24, 3)}


def test_other_takes_heads_are_kept_and_a_zero_leak_clears_its_own(tmp_path):
    (tmp_path / "heads.json").write_text('{"13": 0.67, "7": 0.5}', encoding="utf-8")
    lk.write_head(tmp_path, 7, {"frames": 0, "seconds": 0.0, "covers": True})
    assert edit_gate.heads_in(tmp_path) == {13: 0.67}
    lk.write_head(tmp_path, 2, {"frames": 3, "seconds": 0.125, "covers": True})
    assert json.loads((tmp_path / "heads.json").read_text(encoding="utf-8")) == {"13": 0.67, "2": 0.125}


def test_a_head_that_does_not_cover_the_shot_is_not_written(tmp_path):
    assert lk.write_head(tmp_path, 7, {"frames": 12, "seconds": 0.5, "covers": False}) is None
    assert not (tmp_path / "heads.json").exists()
    assert lk.write_head(tmp_path, 7, None) is None


def test_the_head_is_the_frame_count_over_the_frame_rate():
    assert lk.head_seconds(12) == 0.5 and lk.head_seconds(0) == 0.0 and lk.head_seconds(8) == round(8 / 24, 3)
