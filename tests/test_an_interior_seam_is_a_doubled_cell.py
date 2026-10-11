"""R2_verdict §0.5/§2.1 (2026-10-10): 18 WotW panels in 9 episodes carry a
full-length paper-white line INSIDE the picture -- a cell drawn as two pictures
(ep19 shot 17 the pit twice, ep27 shot 10 the desk twice).  `episode_gutter`
searches only the outer 8 % and the by-thirds `stacked` score missed them, so
the panel gate now looks at every row and column: a line at >= 250 luma over
>= 95 % of its length is a SEAM, a hard panel fault whose cure is a grid
redraw on a bumped seed (the panel ladder's first rung)."""
import numpy as np

from studio import panel_dq, panel_ladder
from studio.judges import panel_eye, registry


def picture(size: int = 768) -> np.ndarray:
    rng = np.random.default_rng(0)
    return rng.integers(30, 200, (size, size, 3), dtype=np.uint8)


def test_a_clean_picture_has_no_seam():
    assert panel_dq.seams(picture()) == []


def test_an_interior_white_column_is_a_seam():
    a = picture()
    a[:, 520] = 255
    assert panel_dq.seams(a) == [("col", 520)]


def test_an_interior_white_row_is_a_seam_even_where_a_figure_crosses_it():
    a = picture()
    a[384, :] = 252
    a[384, :30] = 90                      # under 5 % of the row broken by a figure
    assert panel_dq.seams(a) == [("row", 384)]


def test_a_bright_textured_line_is_no_seam():
    a = picture()
    a[:, 300] = 255
    a[::8, 300] = 120                     # 12.5 % dark: a lit pole, not paper
    assert panel_dq.seams(a) == []


def test_a_band_of_adjacent_lines_is_one_seam():
    a = picture()
    a[381:387, :] = 255
    assert panel_dq.seams(a) == [("row", 381)]


def test_a_seam_fails_the_panel():
    row = panel_dq.verdict(faces=[], planned=0, sharp=1.0, ink=0.0, tiled=0.0, seam=True)
    assert not row["passed"] and row["flags"] == ["seam"]


def test_the_eye_refuses_a_seam_and_the_ladder_cures_it_as_one_picture():
    assert "seam" in panel_eye.CALIBRATED
    # the seam rung (2026-10-11): seam and stacked isolate once, never a reprose phrase
    assert {"seam", "stacked"} == set(panel_ladder.SEAMED) and not set(panel_ladder.SEAMED) & set(panel_ladder.CURES)
    assert registry.PANEL_CLASS["seam"] == "stacked_pictures"


def test_the_stored_seam_flag_is_kept_by_the_registry_judge():
    from types import SimpleNamespace
    row = SimpleNamespace(machine={"panel_dq": {"flags": ["seam"], "sharp": 1.0, "ink": 0.0, "tiled": 0.0}})
    assert registry.panel_dq_judge(row)["classes"] == ["stacked_pictures"]


def test_the_gate_reads_the_seam_on_the_panel_h3_is_staged(tmp_path):
    from PIL import Image
    from scripts.episode import panel_check
    (tmp_path / "h3").mkdir()
    staged = picture()
    staged[:, 400] = 255
    Image.fromarray(staged).save(tmp_path / "h3" / "shot_03.png")
    assert panel_check.seam_of(tmp_path, 3, picture(1024))
    assert not panel_check.seam_of(tmp_path, 4, picture(1024))   # no h3 panel: the cell itself
