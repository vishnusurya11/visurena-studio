"""The edit gate compares a segment against the take from the frame the CUT
started on, not from frame 0.

MEASURED on episode 12 (2026-09-17): T13 was cut from 0.67 s in (`heads.json`,
after an invented jump at frame 15), and QC reported all 191 of its frames off
against frames 0..190 of the take, failing an edit that was exactly the take.
"""
import numpy as np

from studio import edit_gate


def frames(n, seed=0):
    rng = np.random.default_rng(seed)
    return rng.integers(0, 255, size=(n, 8, 8)).astype(np.float32)


def test_no_head_leaves_the_take_whole():
    take = frames(40)
    assert len(edit_gate.headed(take, 0.0)) == 40


def test_a_head_drops_its_frames_at_the_episode_rate():
    take = frames(40)
    got = edit_gate.headed(take, 16 / 24)
    assert len(got) == 24 and np.array_equal(got[0], take[16])


def test_a_segment_cut_from_the_head_matches_the_headed_take():
    take = frames(60, seed=3)
    master = np.concatenate([frames(10, seed=9), take[16:46]])
    row = edit_gate.segment_match(master, edit_gate.headed(take, 16 / 24), start=10, n=30)
    assert row["ok"] and row["offset"] == 0


def test_the_heads_file_is_read_by_take_index(tmp_path):
    assert edit_gate.heads_in(tmp_path) == {}
    (tmp_path / "heads.json").write_text('{"13": 0.67}', encoding="utf-8")
    assert edit_gate.heads_in(tmp_path) == {13: 0.67}
