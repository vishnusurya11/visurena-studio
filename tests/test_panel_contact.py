"""The panel contact sheet: every panel on one grid, numbered by shot."""
from __future__ import annotations

import pytest
from PIL import Image

from studio import panel_contact as pc


def _panels(folder, n=4, size=(32, 24)):
    folder.mkdir(parents=True, exist_ok=True)
    out = []
    for i in range(1, n + 1):
        p = folder / f"shot_{i:02d}.png"
        Image.new("RGB", size, (i * 40, 0, 0)).save(p)
        out.append(p)
    return out


def test_shot_number_reads_the_panel_name(tmp_path):
    assert pc.shot_number(tmp_path / "shot_07.png") == 7
    assert pc.shot_number(tmp_path / "contact.png") == 0


def test_fitted_keeps_aspect_inside_the_cell():
    image = pc.fitted(Image.new("RGB", (40, 20)), 10)
    assert image.size == (10, 5)


def test_a_two_by_two_of_tiny_pngs_is_one_png_of_the_right_size(tmp_path):
    panels = _panels(tmp_path / "storyboard")
    out = pc.write(panels, tmp_path / "storyboard" / "contact.png", cols=2, cell=16)
    with Image.open(out) as sheet:
        assert sheet.size == (32, 32)


def test_a_ragged_last_row_still_fits(tmp_path):
    panels = _panels(tmp_path / "storyboard", n=5)
    with Image.open(pc.write(panels, tmp_path / "c.png", cols=2, cell=16)) as sheet:
        assert sheet.size == (32, 48)


def test_no_panels_is_a_refusal(tmp_path):
    with pytest.raises(SystemExit, match="no panels"):
        pc.write([], tmp_path / "c.png")
