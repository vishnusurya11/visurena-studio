"""ep14 (2026-09-30): the terminal held shots 5 and 13 on their panels; assemble
cut the panel push in, and the edit gate compared those segments against the
TAKE files it did not know were replaced -- every frame off, QC failed a correct
cut twice.  A still segment is checked against its panel's picture (the push
starts at zoom 1.0, so the master's first frame is the panel); a cut beside a
still is a change of picture on the master itself."""
import numpy as np

from studio import edit_gate as gate


def picture(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.integers(0, 255, size=(gate.GREY_H, gate.GREY_W), dtype=np.uint8).astype(np.float64)


def test_a_still_segment_matches_its_panel_and_a_wrong_picture_fails():
    panel = picture(1)
    master = np.stack([panel] * 10)
    row = gate.still_match(master, 0, 10, panel)
    assert row["ok"] and row["still"] and row["mean"] <= gate.STILL_FIRST
    other = gate.still_match(np.stack([picture(2)] * 10), 0, 10, panel)
    assert not other["ok"]


def test_a_hard_cut_inside_a_still_segment_fails():
    panel = picture(1)
    frames = [panel] * 5 + [picture(3)] * 5
    row = gate.still_match(np.stack(frames), 0, 10, panel)
    assert not row["ok"]


def test_a_cut_beside_a_still_is_a_change_of_picture_on_the_master():
    a, b = picture(1), picture(2)
    master = np.stack([a] * 8 + [b] * 8)
    assert gate.cut_beside_still(master, 8)
    assert not gate.cut_beside_still(np.stack([a] * 16), 8)
