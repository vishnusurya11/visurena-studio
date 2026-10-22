"""Fleet C A4 (2026-10-22): a face refine is priced by the fit measured on the 4090.

COSTS.md (2026-10-21_ep02_proof/gpu) measured the H3 face refine at 11.0 s + 0.558 s per frame
per face (73 frames: 54.6 / 57.2 s, 141: 82.2-86.7 s, 209: 136.0 s), and found the cost follows
frames, not face size.  The old price, 110 s per face per 192 frames, had no intercept: 41.8 s at
73 frames against 55-57 s measured, so the reserve under-held short refines."""
from __future__ import annotations

import pytest

from studio import face_refine as fr


def test_one_face_over_73_frames_is_priced_at_the_fit():
    assert fr.price(1, 73) == pytest.approx(51.7, abs=0.05)


def test_the_price_is_within_ten_percent_of_every_measured_length():
    measured = {73: (54.6 + 57.2) / 2, 141: (82.2 + 83.9 + 86.7) / 3, 209: 136.0}
    assert all(abs(fr.price(1, f) - s) <= 0.10 * s for f, s in measured.items())


def test_each_face_pays_the_intercept_again():
    assert fr.price(2, 141) == pytest.approx(2 * fr.price(1, 141))


def test_no_frames_or_no_faces_cost_nothing():
    assert fr.price(0, 141) == 0.0 and fr.price(2, 0) == 0.0


def test_a_warm_grid_render_is_the_70_s_measured():
    """COSTS.md: a warm Qwen-Image 2x2 grid is 69.7 s (102 s held part of a load).  A rung is priced at
    RUNG_SECONDS, the redraw plus its rebuild and reads, never at one render."""
    from studio import panel_ladder
    assert panel_ladder.GRID_SECONDS == 70.0 and panel_ladder.RUNG_SECONDS > panel_ladder.GRID_SECONDS
