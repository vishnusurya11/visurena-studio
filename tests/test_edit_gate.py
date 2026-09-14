"""G5.1-5.6 -- the master IS the takes, frame for frame, at the frames the plan
names.  Synthetic frame stacks; the one clip that is written is 0.5 s of
ffmpeg's own testsrc.  No take on disk, no GPU, no money.
"""
from __future__ import annotations

import subprocess

import numpy as np

from studio import edit_gate as gate


def moving(n: int, seed: int = 0) -> np.ndarray:
    """n distinct frames: a bright bar walking across a noisy field."""
    base = np.random.default_rng(seed).integers(40, 80, (gate.GREY_H, gate.GREY_W), dtype=np.uint8)
    out = []
    for i in range(n):
        f = base.copy()
        f[:, (i * 7) % gate.GREY_W:(i * 7) % gate.GREY_W + 6] = 220
        out.append(f)
    return np.stack(out)


def test_the_thresholds_sit_between_encoder_noise_and_another_picture():
    """MEASURED 2026-09-11 on ep01 master_iter11 against shots_r2v: two crf-17
    encodes of one frame differ by 0.16-0.59 (mean |grey| at 128x224); neighbouring
    frames of the slowest take by 1.4-9.7; frames of different shots by 32-63."""
    assert gate.SAME_FRAME == 4.0 and gate.SEGMENT_MEAN == 1.0
    assert gate.DUP == 0.6 and gate.HOLD_FRAMES == 3


def test_a_segment_that_is_the_take_matches_at_offset_zero():
    take = moving(20)
    master = np.concatenate([moving(5, seed=3), take[:12]])
    row = gate.segment_match(master, take, start=5, n=12)
    assert row["ok"] and row["offset"] == 0 and row["frames_off"] == [] and row["held"] == []


def test_a_segment_placed_one_frame_late_is_reported():
    take = moving(20)
    master = np.concatenate([moving(6, seed=3), take[:12]])   # the plan says frame 5, the file has it at 6
    row = gate.segment_match(master, take, start=5, n=12)
    assert not row["ok"] and row["offset"] == -1


def test_a_hold_the_edit_added_is_found_and_the_takes_own_hold_is_not():
    take = moving(20)
    held = np.concatenate([take[:6], np.repeat(take[5:6], 4, axis=0), take[6:10]])
    assert gate.segment_match(held, take, 0, 14)["held"] == [[5, 6, 7, 8]]
    assert gate.segment_match(held, held, 0, 14)["held"] == []     # the take itself holds: not the edit's doing


def test_a_cut_lands_on_the_frame_the_plan_names():
    a, b = moving(10, seed=1), moving(10, seed=2)
    master = np.concatenate([a[:8], b[:8]])
    assert gate.cut_exact(master, 8, a[7], b[0])
    assert not gate.cut_exact(master, 9, a[7], b[0])


def test_a_timestamp_hole_and_a_late_first_frame_are_found():
    """Iteration 11 measured holes of 0.1667 s at frame 3596 and 0.125 s at 3702,
    and the picture starting 0.041 s late."""
    step = 1 / 24
    assert gate.timestamp_holes([i * step for i in range(10)]) == []
    late = [0.041 + i * step for i in range(4)]
    assert gate.timestamp_holes(late)[0][0] == 0
    hole = [0, step, 2 * step, 6 * step, 7 * step]
    assert gate.timestamp_holes(hole) == [(2, round(4 * step, 4))]


def test_the_tail_is_the_card_then_black_and_nothing_else():
    """The chip count comes from `gate.END_CHIP_FRAMES`, never from a literal.

    This test used to hard-code 48 and so PASSED against a gate that demanded a
    tail the cutter has not produced since 2026-09-11 -- which is exactly why the
    42-frame mismatch survived three episodes. A test that restates a constant
    cannot notice the constant moving. See `test_tail_black_count.py`."""
    picture, card = moving(10), moving(6, seed=9)
    black = np.zeros((gate.END_CHIP_FRAMES, gate.GREY_H, gate.GREY_W), dtype=np.uint8)
    good = np.concatenate([picture, card, black])
    assert gate.tail_check(good, 10, card)["ok"]
    short = np.concatenate([picture[:-4], card, black])           # mix -shortest ate four picture frames
    assert not gate.tail_check(short, 10, card)["ok"]


def test_the_plan_names_each_runs_start_frame_and_length():
    placed = {"shots": [{"index": 0, "t_start": 0.0, "seconds": 2.0}, {"index": 1, "t_start": 2.0, "seconds": 1.0},
                        {"index": 2, "t_start": 3.0, "seconds": 0.5}]}
    records = [{"index": 0, "shots": [0, 1], "rel_path": "a.mp4"}, {"index": 2, "rel_path": "b.mp4"}]
    plan = gate.segment_plan(placed, records)
    assert [(r["take"], r["start"], r["n"]) for r in plan] == [(0, 0, 72), (2, 72, 12)]


def test_provenance_names_a_take_that_changed_under_the_cut(tmp_path):
    """G5.6: shots.json named T18.mp4 after the file had been replaced under
    master_iter11.  A manifest built from the files on disk NOW and compared to the
    files on disk NOW is always empty -- provenance means something only against the
    `work/cut.json` that assemble.py writes when the cut is made."""
    take = tmp_path / "shots"
    take.mkdir()
    (take / "T18.mp4").write_bytes(b"abcd")
    plan = [{"take": 18, "rel_path": "shots/T18.mp4", "n": 12}]
    assert gate.provenance(plan, tmp_path, None) == {"measured": False, "stale_takes": []}
    written = gate.cut_manifest(plan, tmp_path)
    assert written["T18.mp4"] == {"rel_path": "shots/T18.mp4", "frames": 12, "bytes": 4}
    assert gate.provenance(plan, tmp_path, written) == {"measured": True, "stale_takes": []}
    (take / "T18.mp4").write_bytes(b"replaced under the cut")
    assert gate.provenance(plan, tmp_path, written)["stale_takes"] == ["T18.mp4"]
    (take / "T18.mp4").unlink()
    assert gate.provenance(plan, tmp_path, written)["stale_takes"] == ["T18.mp4"]


def test_every_frame_of_a_clip_is_timed(tmp_path):
    clip = tmp_path / "clip.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=64x112:rate=24:duration=0.5",
                    "-c:v", "libx264", "-preset", "ultrafast", str(clip)], check=True)
    times = gate.frame_times(clip)
    assert len(times) == 12 == len(gate.grey_frames(clip))
    assert gate.timestamp_holes(times) == []
