"""ep16 (2026-10-02): every grid staging a four-pose turnaround sheet drew the
character up to four times -- wide shots, then medium ones; a prompt line
saying 'exactly once' changed nothing.  Words do not beat a staged picture,
so the grid is shown ONE figure: the sheet's first figure, found as the first
run of non-background columns on its flat backdrop.  $0: numpy on a fake."""
from __future__ import annotations

import numpy as np
from PIL import Image

from studio.sheet_front import first_figure_box, front_of


def fake_sheet(tmp_path):
    rng = np.random.default_rng(7)
    a = np.full((200, 600, 3), 128, np.uint8)          # flat grey backdrop
    for x0 in (40, 180, 320):                          # three textured figures
        a[20:190, x0:x0 + 80] = rng.integers(20, 230, (170, 80, 3), dtype=np.uint8)
    p = tmp_path / "sheet.png"
    Image.fromarray(a).save(p)
    return p


def test_the_first_figure_is_found(tmp_path):
    box = first_figure_box(np.asarray(Image.open(fake_sheet(tmp_path)).convert("RGB")))
    left, right = box
    assert 25 <= left <= 40 and 120 <= right <= 140      # figure 1 plus a margin
    assert right < 180                                   # never reaches figure 2


def test_front_of_writes_and_reuses_a_crop(tmp_path):
    sheet = fake_sheet(tmp_path)
    out = front_of(sheet)
    assert out.name == "sheet_front.png" and out.exists()
    w, h = Image.open(out).size
    assert h == 200 and w < 200
    assert front_of(sheet) == out                        # cached beside the sheet


def test_a_dip_inside_one_figure_is_bridged():
    from studio.sheet_front import runs
    filled = np.array([0] * 5 + [1] * 30 + [0] * 3 + [1] * 30 + [0] * 40 + [1] * 30)
    assert runs(filled.astype(bool), gap=10)[0] == (5, 68)      # 3-col dip bridged


def test_overlapping_poses_give_no_crop(tmp_path):
    rng = np.random.default_rng(3)
    a = np.full((200, 600, 3), 128, np.uint8)
    a[20:190, 20:400] = rng.integers(20, 230, (170, 380, 3), dtype=np.uint8)   # one wide blob
    p = tmp_path / "sheet.png"
    Image.fromarray(a).save(p)
    assert front_of(p) is None
