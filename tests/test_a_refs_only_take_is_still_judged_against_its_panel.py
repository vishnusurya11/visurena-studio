"""A take rendered from the sheets and the plate alone has no pinned CELL, so
`last-vs-cell` printed `not measured (no cell)` -- while its storyboard panel
(`storyboard/shot_NN.png`) sat on disk the whole time.  The panel is the
board for a refs-only take: the last frame is read against it the same way.
"""
import numpy as np
from PIL import Image

from studio import take_coherence as tc
from synth_frames import hold, picture


def board(home, shots: dict[int, np.ndarray]):
    (home / "storyboard").mkdir(parents=True)
    for k, pic in shots.items():
        Image.fromarray(pic).save(tc.panel_path(home, k))


def test_the_panel_path_is_the_storyboard_shot(tmp_path):
    assert tc.panel_path(tmp_path, 7) == tmp_path / "storyboard" / "shot_07.png"


def test_a_take_that_ends_on_its_panel_reads_high_and_one_that_does_not_reads_low(tmp_path):
    a, b = picture(41), picture(42)
    board(tmp_path, {3: a})
    on = tc.refs_only(hold(a, 20), tmp_path, [3])
    assert on["last_vs_cell"] > 0.9 and on["last_cell"] == "shot_03.png" and on["cells"] == "panel"
    assert on["offboard_share"] == 0.0
    off = tc.refs_only(hold(b, 20), tmp_path, [3])
    assert off["last_vs_cell"] < 0.3 and off["offboard_share"] > 0.5


def test_a_two_shot_take_is_read_against_its_last_panel(tmp_path):
    a, b = picture(43), picture(44)
    board(tmp_path, {3: a, 4: b})
    frames = np.concatenate([hold(a, 10), hold(b, 10)])
    m = tc.refs_only(frames, tmp_path, [3, 4])
    assert m["last_cell"] == "shot_04.png" and m["last_vs_cell"] > 0.9
    assert tc.refs_only(hold(a, 20), tmp_path, [3, 4])["last_vs_cell"] < 0.3


def test_no_panel_on_disk_is_not_measured(tmp_path):
    assert tc.refs_only(hold(picture(45), 10), tmp_path, [3]) is None
    assert tc.panels(tmp_path, [3]) == {}


def test_the_rows_of_a_refs_only_take_carry_a_value(tmp_path):
    a = picture(46)
    board(tmp_path, {3: a})
    rows = {g.name: g for g in tc.rows(tc.refs_only(hold(a, 20), tmp_path, [3]))}
    assert rows["last-vs-cell"].value is not None and rows["last-vs-cell"].ok
    assert rows["coherence off-board"].value == 0.0
