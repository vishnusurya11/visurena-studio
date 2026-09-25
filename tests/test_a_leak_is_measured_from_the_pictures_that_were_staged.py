"""A head leak is the take opening on another STAGED picture -- a sheet, a
plate -- before it lands on its panel.  It is measured against exactly the
pictures the take's own graph loaded (`take_currency.staged_images`), never
against a picture the render was not shown.  The embedder is injected: a
thumbnail stands in for the patch model, and no test reaches ComfyUI.
"""
import json

import numpy as np
import pytest

from studio import take_leak as lk
from synth_frames import hold, picture, thumb_embed

PANEL, SHEET, PLATE = picture(31), picture(32), picture(33)


def staged() -> dict[str, np.ndarray]:
    return {"Q03_0_1a2b3c4d.png": PANEL, "hero_5e6f7a8b.png": SHEET, "plate_road_9c0d1e2f.png": PLATE}


def leaking(head: int) -> np.ndarray:
    return np.concatenate([hold(SHEET, head), hold(PANEL, 30)])


def test_a_head_of_sheet_frames_is_measured_in_frames():
    got = lk.leak(leaking(5), staged(), thumb_embed)
    assert got["frames"] == 5 and got["seconds"] == round(5 / 24, 3) and got["covers"] is True
    assert got["best"][:5] == ["hero_5e6f7a8b.png"] * 5 and got["best"][5] == "Q03_0_1a2b3c4d.png"


def test_a_take_that_opens_on_its_panel_has_no_leak():
    got = lk.leak(hold(PANEL, 20), staged(), thumb_embed)
    assert got["frames"] == 0 and got["covers"] is True


def test_a_head_that_never_lands_does_not_cover_the_shot():
    got = lk.leak(hold(PLATE, 20), staged(), thumb_embed)
    assert got["frames"] == lk.HEAD_FRAMES and got["covers"] is False


def test_only_the_staged_pictures_are_consulted():
    got = lk.leak(leaking(5), staged(), thumb_embed)
    assert got["against"] == sorted(staged())
    without_sheet = {k: v for k, v in staged().items() if not k.startswith("hero")}
    assert lk.leak(leaking(5), without_sheet, thumb_embed)["frames"] == 0   # the sheet was never staged


def test_the_staged_names_come_from_the_takes_own_graph(tmp_path):
    graph = {"1": {"class_type": "LoadImage", "inputs": {"image": "Q03_0_1a2b3c4d.png"}},
             "2": {"class_type": "LoadImage", "inputs": {"image": "hero_5e6f7a8b.png"}},
             "3": {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": {"prompt": "x"}}}
    (tmp_path / "T03.graph.json").write_text(json.dumps(graph), encoding="utf-8")
    inputs = tmp_path / "input"
    inputs.mkdir()
    from PIL import Image
    for name, pic in staged().items():
        Image.fromarray(pic).save(inputs / name)
    pics = lk.staged_pictures(tmp_path / "T03.mp4", inputs)
    assert sorted(pics) == ["Q03_0_1a2b3c4d.png", "hero_5e6f7a8b.png"]        # the plate was not in the graph
    assert pics["hero_5e6f7a8b.png"].shape[:2] == SHEET.shape and pics["hero_5e6f7a8b.png"].ndim == 3


def test_pictures_are_sorted_into_panel_sheet_and_plate_by_name():
    assert lk.kinds(list(staged())) == {"Q03_0_1a2b3c4d.png": "panel", "hero_5e6f7a8b.png": "sheet",
                                        "plate_road_9c0d1e2f.png": "plate"}
    assert lk.kinds(["shot_07_ab12cd34.png"]) == {"shot_07_ab12cd34.png": "panel"}


def test_no_panel_among_the_staged_pictures_is_not_measured():
    assert lk.leak(leaking(5), {"hero_5e6f7a8b.png": SHEET}, thumb_embed) is None
    row = lk.row(None)
    assert row.ok and row.value is None and row.note == "not measured"


def test_the_row_is_an_advisory_that_names_the_head_and_its_calibration():
    row = lk.row(lk.leak(leaking(5), staged(), thumb_embed))
    assert not row.ok and not row.hard and row.value == 5 and "5 frames" in row.note and row.penalty > 0
    assert lk.row(lk.leak(hold(PANEL, 20), staged(), thumb_embed)).ok
    assert "advisory" in lk.FITTED_ON


def test_the_default_embedder_is_never_reached_by_a_test():
    with pytest.raises(RuntimeError, match="reached ComfyUI"):
        lk.dino_embed(PANEL)
